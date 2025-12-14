"""
EXTRACTION MÉTRIQUES RÉELLES SINGLE WAVE FORT - DÉTECTION INDÉPENDANTE
Session 137 - Recalibration Formules V1.2

Mission:
- Détecter indépendamment les mouvements SINGLE_WAVE_FORT depuis les prix réels
- Calculer toutes les métriques: impact, latence, durée pic, pullback, stabilisation
- Ne pas se baser sur le CSV existant qui peut contenir des erreurs

Auteur: André Valentin avec Claude
Date: 2025-01-XX
"""

import pandas as pd
import numpy as np
import duckdb
from pathlib import Path
from datetime import timedelta
from typing import Dict, Optional, Tuple, List

# =============================================================================
# CHEMINS
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
OUTPUT_CSV = Path(__file__).parent / "singlewave_real_metrics_independent.csv"

# =============================================================================
# PARAMÈTRES DÉTECTION
# =============================================================================

MIN_IMPACT_PIPS = 40.0  # Minimum pour Single Wave Fort
MAX_PULLBACK_RATIO = 0.30  # Pullback max 30% pour Single Wave Fort
WINDOW_MINUTES = 120  # Fenêtre d'observation après événement
LATENCY_THRESHOLD_PIPS = 3.0  # Seuil pour détecter début mouvement

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def pips_diff(price1: float, price2: float) -> float:
    """Calcule différence en pips entre deux prix"""
    return abs(price1 - price2) * 10000


def find_local_extrema(
    df_prices: pd.DataFrame,
    window: int = 5
) -> Tuple[List[Tuple], List[Tuple]]:
    """
    Trouve les extrema locaux (peaks et troughs) dans les prix.
    
    Returns:
        (peaks, troughs) où chaque élément est (datetime, price, pips_from_baseline)
    """
    peaks = []
    troughs = []
    
    if len(df_prices) < window * 2:
        return peaks, troughs
    
    for i in range(window, len(df_prices) - window):
        high = df_prices.iloc[i]['high']
        low = df_prices.iloc[i]['low']
        dt = df_prices.iloc[i]['datetime']
        
        # Vérifier si c'est un peak local
        is_peak = True
        for j in range(i - window, i + window + 1):
            if j != i and df_prices.iloc[j]['high'] >= high:
                is_peak = False
                break
        
        if is_peak:
            peaks.append((dt, high, 0.0))  # pips calculé plus tard
        
        # Vérifier si c'est un trough local
        is_trough = True
        for j in range(i - window, i + window + 1):
            if j != i and df_prices.iloc[j]['low'] <= low:
                is_trough = False
                break
        
        if is_trough:
            troughs.append((dt, low, 0.0))
    
    return peaks, troughs


def detect_single_wave_fort(
    df_prices: pd.DataFrame,
    event_time: pd.Timestamp,
    baseline_price: float
) -> Optional[Dict]:
    """
    Détecte un mouvement Single Wave Fort depuis les prix réels.
    
    Critères:
    - Impact > 40 pips
    - Un pic dominant (pas de deuxième pic significatif)
    - Pullback < 30% si présent
    
    Returns:
        Dict avec métriques ou None si pas de Single Wave Fort
    """
    # Filtrer prix après événement
    df_after = df_prices[df_prices['datetime'] >= event_time].copy()
    
    if len(df_after) < 10:
        return None
    
    # Trouver le pic maximum (high ou low selon direction)
    max_high = df_after['high'].max()
    min_low = df_after['low'].min()
    
    high_idx = df_after['high'].idxmax()
    low_idx = df_after['low'].idxmin()
    
    high_time = df_after.loc[high_idx, 'datetime']
    low_time = df_after.loc[low_idx, 'datetime']
    
    # Déterminer direction
    impact_up = (max_high - baseline_price) * 10000
    impact_down = (baseline_price - min_low) * 10000
    
    if impact_up > impact_down and impact_up >= MIN_IMPACT_PIPS:
        direction = 'UP'
        peak_time = high_time
        peak_price = max_high
        impact_pips = impact_up
    elif impact_down >= MIN_IMPACT_PIPS:
        direction = 'DOWN'
        peak_time = low_time
        peak_price = min_low
        impact_pips = impact_down
    else:
        return None  # Impact insuffisant
    
    # Latence: première bougie avec mouvement > seuil
    latency_minutes = None
    movement_start_time = None
    
    for idx, row in df_after.iterrows():
        if direction == 'UP':
            if row['high'] > baseline_price + (LATENCY_THRESHOLD_PIPS / 10000):
                latency_minutes = (row['datetime'] - event_time).total_seconds() / 60
                movement_start_time = row['datetime']
                break
        else:  # DOWN
            if row['low'] < baseline_price - (LATENCY_THRESHOLD_PIPS / 10000):
                latency_minutes = (row['datetime'] - event_time).total_seconds() / 60
                movement_start_time = row['datetime']
                break
    
    if latency_minutes is None:
        return None
    
    # Durée jusqu'au pic
    peak_minutes_from_start = (peak_time - movement_start_time).total_seconds() / 60
    
    # Vérifier pullback (dans les 60 min après pic)
    pullback_window = df_after[df_after['datetime'] > peak_time].copy()
    pullback_window = pullback_window[
        (pullback_window['datetime'] - peak_time).dt.total_seconds() / 60 <= 60
    ]
    
    has_pullback = False
    pullback_info = {}
    
    if len(pullback_window) > 0:
        if direction == 'UP':
            pullback_price = pullback_window['low'].min()
            pullback_idx = pullback_window['low'].idxmin()
        else:  # DOWN
            pullback_price = pullback_window['high'].max()
            pullback_idx = pullback_window['high'].idxmax()
        
        pullback_time = pullback_window.loc[pullback_idx, 'datetime']
        pullback_pips = pips_diff(peak_price, pullback_price)
        pullback_ratio = pullback_pips / impact_pips if impact_pips > 0 else 0.0
        
        if pullback_ratio > 0.10:  # Pullback significatif > 10%
            has_pullback = True
            pullback_info = {
                'pullback_time': pullback_time,
                'pullback_price': pullback_price,
                'pullback_pips': pullback_pips,
                'pullback_ratio': pullback_ratio,
                'pullback_minutes_from_peak': (pullback_time - peak_time).total_seconds() / 60
            }
            
            # Vérifier critère Single Wave Fort: pullback < 30%
            if pullback_ratio > MAX_PULLBACK_RATIO:
                return None  # Trop de pullback, pas un Single Wave Fort
    
    # Vérifier qu'il n'y a pas de deuxième pic significatif
    # (critère: pas de deuxième pic > 50% du premier dans les 120 min)
    if has_pullback:
        # Chercher deuxième pic après pullback
        search_after = pullback_info['pullback_time']
        search_window = df_after[df_after['datetime'] > search_after].copy()
        search_window = search_window[
            (search_window['datetime'] - search_after).dt.total_seconds() / 60 <= 60
        ]
        
        if len(search_window) > 0:
            if direction == 'UP':
                second_peak_price = search_window['high'].max()
                second_peak_impact = (second_peak_price - pullback_info['pullback_price']) * 10000
            else:  # DOWN
                second_peak_price = search_window['low'].min()
                second_peak_impact = (pullback_info['pullback_price'] - second_peak_price) * 10000
            
            # Si deuxième pic > 50% du premier, c'est un Double Wave, pas Single
            if second_peak_impact > impact_pips * 0.5:
                return None
    
    # Construire résultat
    result = {
        'baseline_price': baseline_price,
        'latency_minutes': latency_minutes,
        'movement_start_time': movement_start_time,
        'peak_time': peak_time,
        'peak_price': peak_price,
        'peak_minutes_from_start': peak_minutes_from_start,
        'impact_pips': impact_pips,
        'direction': direction,
        'has_pullback': has_pullback,
    }
    
    if has_pullback:
        result.update(pullback_info)
    else:
        result.update({
            'pullback_time': None,
            'pullback_price': None,
            'pullback_pips': None,
            'pullback_ratio': None,
            'pullback_minutes_from_peak': None
        })
    
    return result


# =============================================================================
# FONCTION PRINCIPALE D'EXTRACTION
# =============================================================================

def extract_metrics_for_event(
    event_time: pd.Timestamp,
    conn: duckdb.DuckDBPyConnection
) -> Optional[Dict]:
    """
    Extrait métriques pour un événement donné.
    
    Returns:
        Dict avec métriques ou None
    """
    # Fenêtre: -30 min avant → +120 min après
    start_time = event_time - timedelta(minutes=30)
    end_time = event_time + timedelta(minutes=WINDOW_MINUTES)
    
    # Charger prix
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime <= ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query, [start_time, end_time]).df()
    
    if len(df_prices) == 0:
        return None
    
    # Convertir datetime
    if df_prices['datetime'].dtype == 'object':
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    # Baseline (dernier close avant événement)
    prices_before = df_prices[df_prices['datetime'] < event_time]
    if len(prices_before) == 0:
        return None
    
    baseline_price = prices_before['close'].iloc[-1]
    
    if baseline_price is None or pd.isna(baseline_price):
        return None
    
    # Détecter Single Wave Fort
    result = detect_single_wave_fort(df_prices, event_time, baseline_price)
    
    if result is None:
        return None
    
    # Ajouter métadonnées
    result['event_time'] = event_time
    result['baseline_price'] = baseline_price
    
    return result


# =============================================================================
# MAIN - SCAN ÉVÉNEMENTS HIGH IMPACT
# =============================================================================

def main():
    print("=" * 80)
    print("EXTRACTION MÉTRIQUES RÉELLES SINGLE WAVE FORT - DÉTECTION INDÉPENDANTE")
    print("=" * 80)
    
    # Connexion DB
    print("\n🔌 Connexion DB...")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Charger événements HIGH IMPACT (importance_n = 3 ou empirical_score > 40)
    print("\n📊 Chargement événements HIGH IMPACT...")
    query_events = """
    SELECT DISTINCT
        e.ts_utc,
        e.ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich' as ts_bern,
        e.event_title,
        e.country,
        e.importance_n,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE (e.importance_n = 3 OR ef.empirical_score > 40)
      AND e.ts_utc >= '2023-01-01'
      AND e.ts_utc < '2026-01-01'
      AND e.country IN ('US', 'EU', 'DE', 'FR', 'IT', 'ES', 'UK')
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query_events).df()
    print(f"   ✅ {len(df_events)} événements HIGH IMPACT trouvés")
    
    # Convertir ts_bern en datetime
    df_events['ts_bern'] = pd.to_datetime(df_events['ts_bern'])
    
    # Extraire métriques pour chaque événement
    print("\n📈 Détection Single Wave Fort et extraction métriques...")
    results = []
    
    for idx, row in df_events.iterrows():
        if idx % 50 == 0:
            print(f"   Traitement {idx+1}/{len(df_events)}...")
        
        event_time = row['ts_bern']
        
        try:
            metrics = extract_metrics_for_event(event_time, conn)
            
            if metrics:
                # Ajouter infos événement
                metrics['event_title'] = row['event_title']
                metrics['country'] = row['country']
                metrics['importance_n'] = row['importance_n']
                metrics['empirical_score'] = row.get('empirical_score', None)
                results.append(metrics)
        except Exception as e:
            if idx < 5:  # Debug pour les 5 premiers
                print(f"   ⚠️  Erreur événement {idx}: {e}")
            continue
    
    conn.close()
    
    # Sauvegarder résultats
    if len(results) == 0:
        print("\n❌ Aucune métrique extraite")
        return
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n✅ {len(results)} mouvements Single Wave Fort détectés")
    print(f"   Sauvegardé dans: {OUTPUT_CSV}")
    
    # Statistiques
    print("\n📊 Statistiques:")
    if len(df_results) > 0:
        print(f"   Impact médian (UP)   : {df_results[df_results['direction']=='UP']['impact_pips'].median():.1f} pips")
        print(f"   Impact médian (DOWN) : {df_results[df_results['direction']=='DOWN']['impact_pips'].median():.1f} pips")
        print(f"   Latence médiane      : {df_results['latency_minutes'].median():.2f} min")
        print(f"   Durée pic médiane    : {df_results['peak_minutes_from_start'].median():.1f} min")
        print(f"   Pullback présent     : {df_results['has_pullback'].sum()}/{len(df_results)} ({100.0*df_results['has_pullback'].sum()/len(df_results):.1f}%)")


if __name__ == "__main__":
    main()

