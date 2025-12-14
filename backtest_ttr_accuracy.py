#!/usr/bin/env python3
"""
Backtest TTR Accuracy v8.4
Teste la précision du TTR observé sur 20-50 événements historiques
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import duckdb
import numpy as np
from typing import List, Dict
import json

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    'event_families': ['CPI', 'NFP', 'Jobless_Claims', 'GDP', 'Retail_Sales'],
    'date_range': {
        'start': '2023-01-01',
        'end': '2024-12-31'
    },
    'min_importance': 2,
    'max_events': 50,
    'retracement_thresholds': [0.15, 0.20, 0.25, 0.30],  # Tester différents seuils
    'max_lookback_minutes': 60
}


# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def fetch_historical_events(db_path: str, families: List[str], date_start: str, date_end: str) -> pd.DataFrame:
    """Récupère les événements historiques avec surprise significative"""
    
    conn = duckdb.connect(db_path, read_only=True)
    
    # D'abord, vérifier quelles dates sont disponibles
    check_query = """
    SELECT MIN(DATE(ts_utc)) as min_date, MAX(DATE(ts_utc)) as max_date, COUNT(*) as total
    FROM events
    WHERE actual IS NOT NULL
    """
    
    date_info = conn.execute(check_query).fetchone()
    print(f"   📅 Dates disponibles dans la DB : {date_info[0]} → {date_info[1]} ({date_info[2]} événements)")
    
    # Patterns pour les familles (plus larges)
    family_patterns = {
        'CPI': '%cpi%',
        'NFP': '%nfp%',
        'Jobless_Claims': '%jobless%',
        'GDP': '%gdp%',
        'Retail_Sales': '%retail%'
    }
    
    conditions = []
    for family in families:
        if family in family_patterns:
            conditions.append(f"LOWER(event_key) LIKE '{family_patterns[family]}'")
    
    where_clause = " OR ".join(conditions) if conditions else "1=1"
    
    # Query plus permissive
    query = f"""
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        previous,
        estimate,
        forecast,
        (actual - COALESCE(estimate, previous, 0)) as surprise
    FROM events
    WHERE DATE(ts_utc) >= '{date_start}'
      AND DATE(ts_utc) <= '{date_end}'
      AND ({where_clause})
      AND country IN ('US', 'EU', 'DE', 'FR', 'GB')
      AND actual IS NOT NULL
    ORDER BY ts_utc DESC
    LIMIT {CONFIG['max_events'] * 3}
    """
    
    print(f"\n   🔍 Query SQL :")
    print(f"      WHERE DATE(ts_utc) >= '{date_start}' AND DATE(ts_utc) <= '{date_end}'")
    print(f"      AND ({where_clause})")
    
    events = conn.execute(query).fetchdf()
    
    print(f"   📊 Événements bruts trouvés : {len(events)}")
    
    if len(events) > 0:
        print(f"   📋 Exemples d'événements :")
        for _, evt in events.head(5).iterrows():
            print(f"      {evt['ts_utc']:%Y-%m-%d %H:%M} - {evt['event_key']} ({evt['country']}) - Surprise: {evt['surprise']:.2f}")
    
    conn.close()
    
    # Filtrer surprises significatives (> 0.01 en valeur absolue)
    if len(events) > 0:
        events = events[events['surprise'].abs() > 0.01]
        print(f"   ✅ Après filtrage surprise > 0.01 : {len(events)} événements")
    
    # Limiter au nombre max
    events = events.head(CONFIG['max_events'])
    
    return events


def fetch_prices_for_event(db_path: str, event_time: datetime, duration_minutes: int = 60) -> pd.DataFrame:
    """Récupère les prix pour un événement donné"""
    
    conn = duckdb.connect(db_path, read_only=True)
    
    # Normaliser timestamp
    if isinstance(event_time, pd.Timestamp):
        event_time = event_time.to_pydatetime()
    if hasattr(event_time, 'tz') and event_time.tz is not None:
        event_time = event_time.tz_convert('UTC').tz_localize(None)
    
    start_epoch = int(event_time.timestamp())
    end_epoch = start_epoch + (duration_minutes * 60)
    
    query = f"""
    SELECT timestamp, close as price
    FROM prices_1m
    WHERE timestamp >= {start_epoch} AND timestamp <= {end_epoch}
    ORDER BY timestamp ASC
    """
    
    try:
        prices = conn.execute(query).fetchall()
        conn.close()
        
        if len(prices) > 0:
            times = [datetime.fromtimestamp(r[0]) for r in prices]
            values = [r[1] for r in prices]
            return pd.DataFrame({'time': times, 'price': values})
        return None
    except Exception as e:
        conn.close()
        return None


def calculate_ttr_observed(prices_df: pd.DataFrame, direction: str, 
                          retracement_threshold: float = 0.30) -> Dict:
    """
    Calcule le TTR observé depuis les prix réels
    Reproduction de calculate_real_ttr_for_phase()
    """
    
    if prices_df is None or len(prices_df) == 0:
        return {'ttr': None, 'reason': 'no_prices'}
    
    # Prix de référence
    ref_price = prices_df.iloc[0]['price']
    
    # Trouver le peak
    if direction == 'DOWN':
        peak_idx = prices_df['price'].idxmin()
    else:
        peak_idx = prices_df['price'].idxmax()
    
    peak_price = prices_df.loc[peak_idx, 'price']
    peak_minutes = prices_df.index.get_loc(peak_idx)
    
    movement_pips = abs((peak_price - ref_price) * 10000)
    
    # Si mouvement trop faible (< 3 pips), ignorer
    if movement_pips < 3.0:
        return {'ttr': None, 'reason': 'movement_too_small', 'movement_pips': movement_pips}
    
    # Chercher le retracement après le peak
    if peak_minutes < len(prices_df) - 1:
        for i in range(peak_minutes + 1, len(prices_df)):
            current_price = prices_df.iloc[i]['price']
            
            # Calculer retracement
            if direction == 'DOWN':
                retracement_pips = (current_price - peak_price) * 10000
            else:
                retracement_pips = (peak_price - current_price) * 10000
            
            # Vérifier si retracement significatif
            if retracement_pips > movement_pips * retracement_threshold:
                return {
                    'ttr': i,
                    'peak_minutes': peak_minutes,
                    'movement_pips': movement_pips,
                    'retracement_pct': (retracement_pips / movement_pips * 100) if movement_pips > 0 else 0,
                    'reason': 'success'
                }
    
    # Pas de retracement trouvé
    return {
        'ttr': None,
        'peak_minutes': peak_minutes,
        'movement_pips': movement_pips,
        'reason': 'no_retracement'
    }


def calculate_ttr_theoretical(surprise: float, base_ttr: float = 30) -> float:
    """
    Calcule le TTR théorique basé sur la surprise
    Formule empirique simplifiée
    """
    
    # Ajustement selon la surprise
    surprise_factor = min(abs(surprise) / 50.0, 2.0)
    ttr_theoretical = base_ttr * (0.5 + 0.5 * surprise_factor)
    
    return ttr_theoretical


def determine_direction(event_key: str, surprise: float) -> str:
    """Détermine la direction attendue selon la famille"""
    
    # Familles inversées (surprise positive = EUR/USD UP)
    inverted_families = ['jobless', 'unemployment', 'inflation', 'cpi']
    
    event_lower = event_key.lower()
    is_inverted = any(fam in event_lower for fam in inverted_families)
    
    if is_inverted:
        return 'UP' if surprise > 0 else 'DOWN'
    else:
        return 'DOWN' if surprise > 0 else 'UP'


# ═══════════════════════════════════════════════════════════════
# BACKTEST PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def run_backtest() -> Dict:
    """Exécute le backtest complet"""
    
    print("=" * 80)
    print("🧪 BACKTEST TTR ACCURACY v8.4")
    print("=" * 80)
    
    db_path = get_db_path()
    
    # 1. Charger événements historiques
    print("\n📥 Chargement des événements historiques...")
    events = fetch_historical_events(
        db_path,
        CONFIG['event_families'],
        CONFIG['date_range']['start'],
        CONFIG['date_range']['end']
    )
    
    print(f"✅ {len(events)} événements trouvés")
    print(f"   Période : {events['ts_utc'].min()} → {events['ts_utc'].max()}")
    
    # 2. Tester chaque seuil
    results_by_threshold = {}
    
    for threshold in CONFIG['retracement_thresholds']:
        print(f"\n{'─' * 80}")
        print(f"🔬 TEST AVEC SEUIL {threshold * 100:.0f}%")
        print(f"{'─' * 80}")
        
        results = []
        
        for idx, event in events.iterrows():
            event_time = pd.to_datetime(event['ts_utc'])
            
            # Récupérer prix
            prices_df = fetch_prices_for_event(db_path, event_time, duration_minutes=60)
            
            if prices_df is None:
                continue
            
            # Déterminer direction
            direction = determine_direction(event['event_key'], event['surprise'])
            
            # Calculer TTR observé
            ttr_obs = calculate_ttr_observed(prices_df, direction, retracement_threshold=threshold)
            
            # Calculer TTR théorique
            ttr_theo = calculate_ttr_theoretical(event['surprise'])
            
            # Enregistrer résultat
            result = {
                'date': event_time.strftime('%Y-%m-%d %H:%M'),
                'event_key': event['event_key'],
                'country': event['country'],
                'surprise': event['surprise'],
                'direction': direction,
                'ttr_theoretical': ttr_theo,
                'ttr_observed': ttr_obs.get('ttr'),
                'peak_minutes': ttr_obs.get('peak_minutes'),
                'movement_pips': ttr_obs.get('movement_pips'),
                'reason': ttr_obs.get('reason'),
                'error': None
            }
            
            # Calculer erreur si TTR observé disponible
            if result['ttr_observed'] is not None:
                result['error'] = abs(result['ttr_observed'] - result['ttr_theoretical'])
            
            results.append(result)
        
        results_by_threshold[threshold] = results
        
        # Statistiques pour ce seuil
        valid_results = [r for r in results if r['ttr_observed'] is not None]
        
        if len(valid_results) > 0:
            errors = [r['error'] for r in valid_results]
            
            print(f"\n📊 STATISTIQUES (seuil {threshold * 100:.0f}%) :")
            print(f"   Événements testés : {len(results)}")
            print(f"   TTR observés calculés : {len(valid_results)} ({len(valid_results)/len(results)*100:.1f}%)")
            print(f"   MAE : {np.mean(errors):.1f} min")
            print(f"   RMSE : {np.sqrt(np.mean(np.array(errors)**2)):.1f} min")
            print(f"   Médiane : {np.median(errors):.1f} min")
            print(f"   Min : {np.min(errors):.1f} min")
            print(f"   Max : {np.max(errors):.1f} min")
            
            # Distribution des raisons d'échec
            reasons = {}
            for r in results:
                reason = r['reason']
                reasons[reason] = reasons.get(reason, 0) + 1
            
            print(f"\n   Raisons :")
            for reason, count in reasons.items():
                print(f"      {reason}: {count} ({count/len(results)*100:.1f}%)")
    
    # 3. Trouver le meilleur seuil
    print("\n" + "=" * 80)
    print("🎯 COMPARAISON DES SEUILS")
    print("=" * 80)
    
    best_threshold = None
    best_mae = float('inf')
    
    comparison = []
    
    for threshold, results in results_by_threshold.items():
        valid_results = [r for r in results if r['ttr_observed'] is not None]
        
        if len(valid_results) > 0:
            errors = [r['error'] for r in valid_results]
            mae = np.mean(errors)
            rmse = np.sqrt(np.mean(np.array(errors)**2))
            coverage = len(valid_results) / len(results) * 100
            
            comparison.append({
                'threshold': threshold,
                'coverage': coverage,
                'mae': mae,
                'rmse': rmse,
                'n_valid': len(valid_results)
            })
            
            if mae < best_mae:
                best_mae = mae
                best_threshold = threshold
    
    # Afficher tableau comparatif
    print(f"\n{'Seuil':<10} {'Couverture':<15} {'MAE':<10} {'RMSE':<10} {'N':<10}")
    print("─" * 60)
    for c in comparison:
        marker = "✅" if c['threshold'] == best_threshold else "  "
        print(f"{c['threshold']*100:.0f}%{marker:<6} {c['coverage']:.1f}%{'':<10} {c['mae']:.1f} min{'':<3} {c['rmse']:.1f} min{'':<3} {c['n_valid']}")
    
    print(f"\n🏆 MEILLEUR SEUIL : {best_threshold * 100:.0f}% (MAE = {best_mae:.1f} min)")
    
    # 4. Sauvegarder résultats
    output_file = "backtest_results_v84.json"
    output_data = {
        'config': CONFIG,
        'results_by_threshold': {
            str(k): v for k, v in results_by_threshold.items()
        },
        'comparison': comparison,
        'best_threshold': best_threshold,
        'best_mae': best_mae,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"\n💾 Résultats sauvegardés : {output_file}")
    
    # 5. Top 10 meilleurs et pires cas
    print("\n" + "=" * 80)
    print("🏆 TOP 10 MEILLEURES PRÉDICTIONS")
    print("=" * 80)
    
    best_results = results_by_threshold[best_threshold]
    valid_best = [r for r in best_results if r['ttr_observed'] is not None]
    valid_best.sort(key=lambda x: x['error'])
    
    print(f"\n{'Date':<18} {'Événement':<30} {'TTR obs':<10} {'TTR theo':<10} {'Erreur':<10}")
    print("─" * 80)
    for r in valid_best[:10]:
        print(f"{r['date']:<18} {r['event_key'][:28]:<30} {r['ttr_observed']:<10} {r['ttr_theoretical']:<10.1f} {r['error']:.1f} min")
    
    print("\n" + "=" * 80)
    print("⚠️ TOP 10 PIRES PRÉDICTIONS")
    print("=" * 80)
    
    print(f"\n{'Date':<18} {'Événement':<30} {'TTR obs':<10} {'TTR theo':<10} {'Erreur':<10}")
    print("─" * 80)
    for r in valid_best[-10:]:
        print(f"{r['date']:<18} {r['event_key'][:28]:<30} {r['ttr_observed']:<10} {r['ttr_theoretical']:<10.1f} {r['error']:.1f} min")
    
    print("\n" + "=" * 80)
    print("✅ BACKTEST TERMINÉ")
    print("=" * 80)
    
    return output_data


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    results = run_backtest()
