#!/usr/bin/env python3
"""
Backtest Multi-Événements v8.4 - VERSION CORRIGÉE
✅ Calcul d'impact corrigé (en % au lieu d'absolu)
✅ Détection correcte des retracements
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

# Importer les fonctions de séquençage
try:
    from sequence_multi_event_timeline import sequence_multi_event_timeline, calculate_ttr_accuracy_stats
    SEQUENCE_AVAILABLE = True
except ImportError:
    SEQUENCE_AVAILABLE = False
    print("⚠️ sequence_multi_event_timeline non disponible - mode simplifié")


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    'date_range': {
        'start': '2024-01-01',
        'end': '2024-06-30'
    },
    'countries': ['US', 'EU', 'DE'],
    'time_gap_minutes': 5,
    'retracement_threshold': 0.30,
    'min_events_per_session': 2,
    'max_sessions': 100
}


# ═══════════════════════════════════════════════════════════════
# FONCTIONS DE DÉTECTION DES SESSIONS
# ═══════════════════════════════════════════════════════════════

def find_multi_event_sessions(db_path: str, date_start: str, date_end: str) -> List[Dict]:
    """Trouve les sessions avec plusieurs événements rapprochés (< 5 min)"""
    
    conn = duckdb.connect(db_path, read_only=True)
    
    query = f"""
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        previous,
        estimate
    FROM events
    WHERE DATE(ts_utc) >= '{date_start}'
      AND DATE(ts_utc) <= '{date_end}'
      AND country IN ('US', 'EU', 'DE', 'FR', 'GB')
      AND importance_n >= 1
      AND actual IS NOT NULL
      AND estimate IS NOT NULL
    ORDER BY ts_utc
    """
    
    events = conn.execute(query).fetchdf()
    conn.close()
    
    if len(events) == 0:
        return []
    
    # Grouper par sessions (événements < 5 min d'écart)
    sessions = []
    current_session = []
    last_time = None
    
    for idx, event in events.iterrows():
        event_time = pd.to_datetime(event['ts_utc'])
        
        if last_time is None or (event_time - last_time).total_seconds() / 60 <= CONFIG['time_gap_minutes']:
            current_session.append(event.to_dict())
            last_time = event_time
        else:
            if len(current_session) >= CONFIG['min_events_per_session']:
                sessions.append({
                    'start_time': pd.to_datetime(current_session[0]['ts_utc']),
                    'events': current_session
                })
            
            current_session = [event.to_dict()]
            last_time = event_time
    
    if len(current_session) >= CONFIG['min_events_per_session']:
        sessions.append({
            'start_time': pd.to_datetime(current_session[0]['ts_utc']),
            'events': current_session
        })
    
    print(f"\n✅ {len(sessions)} sessions multi-événements trouvées")
    
    return sessions[:CONFIG['max_sessions']]


def identify_family(event_key: str) -> str:
    """Identifie la famille d'un événement"""
    
    families = {
        'CPI': ['cpi', 'inflation'],
        'Jobless': ['jobless', 'unemployment'],
        'NFP': ['nfp', 'payroll'],
        'GDP': ['gdp'],
        'Retail': ['retail'],
        'Interest_Rate': ['interest rate', 'rate decision'],
        'PMI': ['pmi'],
        'Trade': ['trade balance', 'current account']
    }
    
    event_lower = event_key.lower()
    
    for family, patterns in families.items():
        if any(p in event_lower for p in patterns):
            return family
    
    return 'Other'


def predict_impact_simple_FIXED(event: Dict) -> Dict:
    """
    ✅ VERSION CORRIGÉE - Calcul d'impact en % de la valeur de référence
    
    Changements :
    - Calcul de surprise en % au lieu d'absolu
    - Base impact augmentée de 30 à 50 pips
    - Multiplicateur max augmenté de 2.0 à 3.0
    """
    
    actual = event.get('actual')
    estimate = event.get('estimate')
    
    if actual is None or estimate is None or estimate == 0:
        return None
    
    # ✅ CORRECTION : Calcul en pourcentage
    surprise_pct = abs((actual - estimate) / estimate) * 100
    
    if surprise_pct < 0.1:  # Moins de 0.1% de surprise
        return None
    
    # ✅ CORRECTION : Impact basé sur le % de surprise
    base_impact = 50.0  # pips (au lieu de 30)
    impact_pips = base_impact * min(surprise_pct / 10.0, 3.0)  # Max 150 pips
    
    # Direction (inversion pour CPI et Jobless)
    family = identify_family(event['event_key'])
    inverted = family in ['CPI', 'Jobless']
    
    surprise = actual - estimate
    
    if inverted:
        direction = 1 if surprise > 0 else -1
    else:
        direction = -1 if surprise > 0 else 1
    
    return {
        'predicted_pips': impact_pips,
        'direction': direction,
        'latency_median': 5.0,
        'ttr_median': 30.0,
        'surprise': surprise,
        'surprise_pct': surprise_pct,  # ✅ Nouveau : pour analyse
        'family': family
    }


def fetch_prices_batch(db_path: str, start_time: datetime, duration_minutes: int = 120) -> pd.DataFrame:
    """Récupère les prix pour une session"""
    
    conn = duckdb.connect(db_path, read_only=True)
    
    if isinstance(start_time, pd.Timestamp):
        start_time = start_time.to_pydatetime()
    if hasattr(start_time, 'tz') and start_time.tz is not None:
        start_time = start_time.tz_convert('UTC').tz_localize(None)
    
    start_epoch = int(start_time.timestamp())
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


# ═══════════════════════════════════════════════════════════════
# BACKTEST PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def run_multi_event_backtest() -> Dict:
    """Exécute le backtest sur les sessions multi-événements"""
    
    print("=" * 80)
    print("🧪 BACKTEST MULTI-ÉVÉNEMENTS v8.4 - VERSION CORRIGÉE")
    print("=" * 80)
    print("\n✅ Calcul d'impact corrigé (en % au lieu d'absolu)")
    
    if not SEQUENCE_AVAILABLE:
        print("\n❌ sequence_multi_event_timeline non disponible")
        return {}
    
    db_path = get_db_path()
    
    # 1. Trouver les sessions
    print("\n📥 Recherche des sessions multi-événements...")
    print(f"   Période : {CONFIG['date_range']['start']} → {CONFIG['date_range']['end']}")
    
    sessions = find_multi_event_sessions(
        db_path,
        CONFIG['date_range']['start'],
        CONFIG['date_range']['end']
    )
    
    if len(sessions) == 0:
        print("\n❌ Aucune session trouvée")
        return {}
    
    print("\n📋 Exemples de sessions :")
    for i, session in enumerate(sessions[:5]):
        print(f"\n   Session {i+1} : {session['start_time'].strftime('%Y-%m-%d %H:%M')}")
        for evt in session['events']:
            print(f"      - {evt['event_key']} ({evt['country']})")
    
    # 2. Tester chaque session
    print("\n" + "=" * 80)
    print("🔬 TEST DES SESSIONS")
    print("=" * 80)
    
    results = []
    
    for session_idx, session in enumerate(sessions):
        print(f"\n{'─' * 80}")
        print(f"Session {session_idx + 1}/{len(sessions)} : {session['start_time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   {len(session['events'])} événements")
        
        # Préparer prédictions
        predictions = []
        
        for evt in session['events']:
            pred = predict_impact_simple_FIXED(evt)  # ✅ VERSION CORRIGÉE
            
            if pred is None:
                continue
            
            predictions.append({
                'event': {
                    'ts_utc': pd.to_datetime(evt['ts_utc']),
                    'family': pred['family'],
                    'event_key': evt['event_key'],
                    'country': evt['country']
                },
                'predicted_pips': pred['predicted_pips'],
                'direction': pred['direction'],
                'latency_median': pred['latency_median'],
                'ttr_median': pred['ttr_median'],
                'surprise': pred['surprise'],
                'surprise_pct': pred['surprise_pct']  # ✅ Nouveau
            })
        
        if len(predictions) == 0:
            print("   ⚠️ Aucune prédiction valide")
            continue
        
        # Afficher impacts calculés
        total_impact = sum(abs(p['predicted_pips']) for p in predictions)
        print(f"   💥 Impact total prédit : {total_impact:.1f} pips")
        
        # Récupérer prix réels
        start_fetch = session['start_time'] - timedelta(minutes=30)
        real_prices_df = fetch_prices_batch(db_path, start_fetch, duration_minutes=120)
        
        if real_prices_df is None:
            print("   ⚠️ Prix introuvables")
            continue
        
        print(f"   ✅ {len(real_prices_df)} minutes de prix")
        
        # Calculer phases
        try:
            phases = sequence_multi_event_timeline(
                predictions,
                real_prices_df=real_prices_df,
                time_gap_minutes=CONFIG['time_gap_minutes']
            )
            
            print(f"   📊 {len(phases)} phases détectées")
            
            # Analyser chaque phase
            for phase_idx, phase in enumerate(phases):
                ttr_obs = phase.get('ttr_real')
                ttr_theo = phase.get('ttr_theoretical')
                ttr_source = phase.get('ttr_source')
                impact = phase.get('impact_combined', 0)
                
                if ttr_obs and ttr_theo:
                    error = abs(ttr_obs - ttr_theo)
                    
                    result = {
                        'session_date': session['start_time'].strftime('%Y-%m-%d %H:%M'),
                        'n_events': len(phase.get('events', [])),
                        'phase_idx': phase_idx,
                        'impact_pips': impact,  # ✅ Devrait être > 0 maintenant
                        'direction': phase.get('direction', 'UP'),
                        'ttr_theoretical': ttr_theo,
                        'ttr_observed': ttr_obs,
                        'ttr_source': ttr_source,
                        'error': error,
                        'duration_minutes': phase.get('duration_minutes', 0)
                    }
                    
                    results.append(result)
                    
                    status = "✅" if error < 10 else "⚠️" if error < 20 else "❌"
                    print(f"      Phase {phase_idx + 1}: {status} Impact={impact:.1f} pips, TTR obs={ttr_obs:.0f} min, theo={ttr_theo:.0f} min, err={error:.0f} min")
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            continue
    
    # 3. Statistiques globales
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES GLOBALES")
    print("=" * 80)
    
    if len(results) == 0:
        print("\n❌ Aucun résultat valide")
        return {}
    
    errors = [r['error'] for r in results]
    impacts = [r['impact_pips'] for r in results]
    observed_sources = [r['ttr_source'] for r in results]
    
    n_observed = observed_sources.count('observed')
    n_theoretical = observed_sources.count('theoretical')
    
    print(f"\n   Sessions testées : {len(sessions)}")
    print(f"   Phases analysées : {len(results)}")
    print(f"   TTR observé : {n_observed} ({n_observed/len(results)*100:.1f}%)")
    print(f"   TTR théorique : {n_theoretical} ({n_theoretical/len(results)*100:.1f}%)")
    
    # ✅ Vérifier si impacts sont > 0
    n_zero_impact = sum(1 for i in impacts if i == 0)
    print(f"\n   💥 Impacts :")
    print(f"      Avec impact > 0 : {len(results) - n_zero_impact} ({(len(results) - n_zero_impact)/len(results)*100:.1f}%)")
    print(f"      Avec impact = 0 : {n_zero_impact} ({n_zero_impact/len(results)*100:.1f}%)")
    print(f"      Impact moyen : {np.mean(impacts):.1f} pips")
    
    print(f"\n   📊 Précision TTR :")
    print(f"      MAE : {np.mean(errors):.1f} min")
    print(f"      RMSE : {np.sqrt(np.mean(np.array(errors)**2)):.1f} min")
    print(f"      Médiane : {np.median(errors):.1f} min")
    print(f"      Min : {np.min(errors):.1f} min")
    print(f"      Max : {np.max(errors):.1f} min")
    
    # Distribution des erreurs
    bins = [0, 5, 10, 15, 20, 30, 100]
    labels = ['< 5 min', '5-10 min', '10-15 min', '15-20 min', '20-30 min', '> 30 min']
    
    print(f"\n   📊 Distribution des erreurs :")
    for i, label in enumerate(labels):
        count = sum(1 for e in errors if bins[i] <= e < bins[i+1])
        pct = count / len(errors) * 100
        bar = "█" * int(pct / 2)
        print(f"      {label:<12} : {count:3} ({pct:5.1f}%) {bar}")
    
    # 4. Sauvegarder
    output_file = "backtest_multi_events_results_FIXED.json"
    output_data = {
        'config': CONFIG,
        'results': results,
        'stats': {
            'n_sessions': len(sessions),
            'n_phases': len(results),
            'mae': float(np.mean(errors)),
            'rmse': float(np.sqrt(np.mean(np.array(errors)**2))),
            'median': float(np.median(errors)),
            'mean_impact': float(np.mean(impacts)),
            'n_zero_impact': int(n_zero_impact)
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"\n💾 Résultats sauvegardés : {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ BACKTEST TERMINÉ")
    print("=" * 80)
    
    return output_data


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    results = run_multi_event_backtest()
