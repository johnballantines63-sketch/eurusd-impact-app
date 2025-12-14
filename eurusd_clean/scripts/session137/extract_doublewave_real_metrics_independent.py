"""
EXTRACTION MÉTRIQUES RÉELLES DOUBLE WAVE - DÉTECTION INDÉPENDANTE
Session 137 - Recalibration Formules V1.2

Mission:
- Détecter indépendamment les mouvements DOUBLE_WAVE depuis les prix réels
- Calculer toutes les métriques: impact, latence, phase1, pullback, phase2, stabilisation
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
OUTPUT_CSV = Path(__file__).parent / "doublewave_real_metrics_independent.csv"

# =============================================================================
# PARAMÈTRES DÉTECTION
# =============================================================================

MIN_PHASE1_PIPS = 20.0  # Minimum Phase 1 pour Double Wave
MIN_PHASE2_PIPS = 15.0  # Minimum Phase 2 pour Double Wave
MIN_PULLBACK_RATIO = 0.25  # Pullback minimum 25%
MAX_PULLBACK_RATIO = 0.70  # Pullback maximum 70%
WINDOW_MINUTES = 120  # Fenêtre d'observation après événement
LATENCY_THRESHOLD_PIPS = 3.0  # Seuil pour détecter début mouvement
PHASE2_MIN_RATIO = 0.5  # Phase 2 doit être au moins 50% de Phase 1

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
        (peaks, troughs) où chaque élément est (datetime, price)
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
            peaks.append((dt, high))
        
        # Vérifier si c'est un trough local
        is_trough = True
        for j in range(i - window, i + window + 1):
            if j != i and df_prices.iloc[j]['low'] <= low:
                is_trough = False
                break
        
        if is_trough:
            troughs.append((dt, low))
    
    return peaks, troughs


def detect_double_wave(
    df_prices: pd.DataFrame,
    event_time: pd.Timestamp,
    baseline_price: float
) -> Optional[Dict]:
    """
    Détecte un mouvement Double Wave depuis les prix réels.
    Approche simplifiée : chercher directement les high/low dans les prix.
    
    Critères:
    - Phase 1 > 20 pips
    - Pullback 25-70% de Phase 1
    - Phase 2 > 15 pips et > 50% de Phase 1
    
    Returns:
        Dict avec métriques ou None si pas de Double Wave
    """
    # Filtrer prix après événement
    df_after = df_prices[df_prices['datetime'] >= event_time].copy()
    
    if len(df_after) < 20:
        return None
    
    # Déterminer direction initiale (premier mouvement significatif)
    max_high = df_after['high'].max()
    min_low = df_after['low'].min()
    
    impact_up = (max_high - baseline_price) * 10000
    impact_down = (baseline_price - min_low) * 10000
    
    if impact_up > impact_down:
        direction = 'UP'
    else:
        direction = 'DOWN'
    
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
    
    # Chercher Phase 1, Pullback, Phase 2 dans les prix directement
    if direction == 'UP':
        # Phase 1: Premier high significatif après mouvement start
        df_phase1_window = df_after[df_after['datetime'] >= movement_start_time].copy()
        df_phase1_window = df_phase1_window[df_phase1_window['datetime'] <= movement_start_time + timedelta(minutes=60)]
        
        if len(df_phase1_window) == 0:
            return None
        
        phase1_idx = df_phase1_window['high'].idxmax()
        phase1_time = df_phase1_window.loc[phase1_idx, 'datetime']
        phase1_price = df_phase1_window.loc[phase1_idx, 'high']
        phase1_pips = (phase1_price - baseline_price) * 10000
        
        if phase1_pips < MIN_PHASE1_PIPS:
            return None
        
        # Pullback: Trouver low minimum après Phase 1 (dans les 30 min)
        df_pullback_window = df_after[df_after['datetime'] > phase1_time].copy()
        df_pullback_window = df_pullback_window[df_pullback_window['datetime'] <= phase1_time + timedelta(minutes=30)]
        
        if len(df_pullback_window) == 0:
            return None
        
        pullback_idx = df_pullback_window['low'].idxmin()
        pullback_time = df_pullback_window.loc[pullback_idx, 'datetime']
        pullback_price = df_pullback_window.loc[pullback_idx, 'low']
        pullback_pips = (phase1_price - pullback_price) * 10000
        pullback_ratio = pullback_pips / phase1_pips if phase1_pips > 0 else 0.0
        
        # Vérifier critère pullback
        if pullback_ratio < MIN_PULLBACK_RATIO or pullback_ratio > MAX_PULLBACK_RATIO:
            return None
        
        # Phase 2: Trouver high maximum après pullback (dans les 60 min)
        df_phase2_window = df_after[df_after['datetime'] > pullback_time].copy()
        df_phase2_window = df_phase2_window[df_phase2_window['datetime'] <= pullback_time + timedelta(minutes=60)]
        
        if len(df_phase2_window) == 0:
            return None
        
        phase2_idx = df_phase2_window['high'].idxmax()
        phase2_time = df_phase2_window.loc[phase2_idx, 'datetime']
        phase2_price = df_phase2_window.loc[phase2_idx, 'high']
        phase2_pips = (phase2_price - pullback_price) * 10000
        
        if phase2_pips < MIN_PHASE2_PIPS:
            return None
        
        # Vérifier que Phase 2 > 50% de Phase 1
        if phase2_pips < phase1_pips * PHASE2_MIN_RATIO:
            return None
        
        # Impact total = Phase 2 depuis baseline
        impact_pips = (phase2_price - baseline_price) * 10000
        
    else:  # DOWN
        # Phase 1: Premier low significatif après mouvement start
        df_phase1_window = df_after[df_after['datetime'] >= movement_start_time].copy()
        df_phase1_window = df_phase1_window[df_phase1_window['datetime'] <= movement_start_time + timedelta(minutes=60)]
        
        if len(df_phase1_window) == 0:
            return None
        
        phase1_idx = df_phase1_window['low'].idxmin()
        phase1_time = df_phase1_window.loc[phase1_idx, 'datetime']
        phase1_price = df_phase1_window.loc[phase1_idx, 'low']
        phase1_pips = (baseline_price - phase1_price) * 10000
        
        if phase1_pips < MIN_PHASE1_PIPS:
            return None
        
        # Pullback: Trouver high maximum après Phase 1 (dans les 30 min)
        df_pullback_window = df_after[df_after['datetime'] > phase1_time].copy()
        df_pullback_window = df_pullback_window[df_pullback_window['datetime'] <= phase1_time + timedelta(minutes=30)]
        
        if len(df_pullback_window) == 0:
            return None
        
        pullback_idx = df_pullback_window['high'].idxmax()
        pullback_time = df_pullback_window.loc[pullback_idx, 'datetime']
        pullback_price = df_pullback_window.loc[pullback_idx, 'high']
        pullback_pips = (pullback_price - phase1_price) * 10000
        pullback_ratio = pullback_pips / phase1_pips if phase1_pips > 0 else 0.0
        
        # Vérifier critère pullback
        if pullback_ratio < MIN_PULLBACK_RATIO or pullback_ratio > MAX_PULLBACK_RATIO:
            return None
        
        # Phase 2: Trouver low minimum après pullback (dans les 60 min)
        df_phase2_window = df_after[df_after['datetime'] > pullback_time].copy()
        df_phase2_window = df_phase2_window[df_phase2_window['datetime'] <= pullback_time + timedelta(minutes=60)]
        
        if len(df_phase2_window) == 0:
            return None
        
        phase2_idx = df_phase2_window['low'].idxmin()
        phase2_time = df_phase2_window.loc[phase2_idx, 'datetime']
        phase2_price = df_phase2_window.loc[phase2_idx, 'low']
        phase2_pips = (pullback_price - phase2_price) * 10000
        
        if phase2_pips < MIN_PHASE2_PIPS:
            return None
        
        # Vérifier que Phase 2 > 50% de Phase 1
        if phase2_pips < phase1_pips * PHASE2_MIN_RATIO:
            return None
        
        # Impact total = Phase 2 depuis baseline
        impact_pips = (baseline_price - phase2_price) * 10000
    
    # Calculer durées
    phase1_minutes = (phase1_time - movement_start_time).total_seconds() / 60
    pullback_minutes = (pullback_time - phase1_time).total_seconds() / 60
    phase2_minutes = (phase2_time - pullback_time).total_seconds() / 60
    
    # Construire résultat
    result = {
        'baseline_price': baseline_price,
        'latency_minutes': latency_minutes,
        'movement_start_time': movement_start_time,
        'direction': direction,
        'phase1_time': phase1_time,
        'phase1_price': phase1_price,
        'phase1_pips': phase1_pips,
        'phase1_minutes_from_start': phase1_minutes,
        'pullback_time': pullback_time,
        'pullback_price': pullback_price,
        'pullback_pips': pullback_pips,
        'pullback_ratio': pullback_ratio,
        'pullback_minutes_from_phase1': pullback_minutes,
        'phase2_time': phase2_time,
        'phase2_price': phase2_price,
        'phase2_pips': phase2_pips,
        'phase2_minutes_from_pullback': phase2_minutes,
        'impact_pips': impact_pips,
    }
    
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
    
    # Détecter Double Wave
    result = detect_double_wave(df_prices, event_time, baseline_price)
    
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
    print("EXTRACTION MÉTRIQUES RÉELLES DOUBLE WAVE - DÉTECTION INDÉPENDANTE")
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
    print("\n📈 Détection Double Wave et extraction métriques...")
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
    
    print(f"\n✅ {len(results)} mouvements Double Wave détectés")
    print(f"   Sauvegardé dans: {OUTPUT_CSV}")
    
    # Statistiques
    print("\n📊 Statistiques:")
    if len(df_results) > 0:
        print(f"   Impact médian (UP)   : {df_results[df_results['direction']=='UP']['impact_pips'].median():.1f} pips")
        print(f"   Impact médian (DOWN) : {df_results[df_results['direction']=='DOWN']['impact_pips'].median():.1f} pips")
        print(f"   Latence médiane      : {df_results['latency_minutes'].median():.2f} min")
        print(f"   Phase 1 médiane      : {df_results['phase1_pips'].median():.1f} pips en {df_results['phase1_minutes_from_start'].median():.1f} min")
        print(f"   Pullback médian      : {df_results['pullback_ratio'].median():.3f} ({df_results['pullback_minutes_from_phase1'].median():.1f} min)")
        print(f"   Phase 2 médiane      : {df_results['phase2_pips'].median():.1f} pips en {df_results['phase2_minutes_from_pullback'].median():.1f} min")


if __name__ == "__main__":
    main()

