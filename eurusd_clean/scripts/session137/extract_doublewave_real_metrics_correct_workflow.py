"""
EXTRACTION MÉTRIQUES RÉELLES DOUBLE WAVE - WORKFLOW CORRECT
Session 137 - Recalibration Formules V1.2

WORKFLOW CORRECT:
1. Scanner les PRIX pour trouver mouvements forts (indépendamment des événements)
2. Détecter le pattern (Double Wave, Single Wave, etc.)
3. ENSUITE chercher les événements correspondants

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
OUTPUT_CSV = Path(__file__).parent / "doublewave_real_metrics_correct_workflow.csv"

# =============================================================================
# PARAMÈTRES DÉTECTION
# =============================================================================

MIN_MOVEMENT_PIPS = 35.0  # Minimum pour considérer un mouvement fort
MIN_PHASE1_PIPS = 20.0
MIN_PHASE2_PIPS = 15.0
MIN_PULLBACK_RATIO = 0.25
MAX_PULLBACK_RATIO = 0.70
PHASE2_MIN_RATIO = 0.5
WINDOW_SCAN_MINUTES = 120  # Fenêtre d'analyse après détection mouvement

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def pips_diff(price1: float, price2: float) -> float:
    """Calcule différence en pips entre deux prix"""
    return abs(price1 - price2) * 10000


def scan_strong_movements(
    conn: duckdb.DuckDBPyConnection,
    start_date: str = '2023-01-01',
    end_date: str = '2026-01-01'
) -> List[Dict]:
    """
    Scanne les prix pour trouver des mouvements forts (indépendamment des événements).
    
    Returns:
        Liste de dict avec mouvement_id, movement_datetime, baseline_price, direction, impact_pips
    """
    print(f"\n📊 Scan des prix pour mouvements forts >= {MIN_MOVEMENT_PIPS} pips...")
    
    # Charger prix par jour et scanner
    query = """
    SELECT 
        DATE(datetime) as date,
        MIN(datetime) as first_time,
        MAX(datetime) as last_time
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime < ?
    GROUP BY DATE(datetime)
    ORDER BY date
    """
    
    df_dates = conn.execute(query, [start_date, end_date]).df()
    
    movements = []
    movement_id = 0
    
    for idx, row in df_dates.iterrows():
        date = row['date']
        
        # Charger prix pour ce jour
        query_prices = """
        SELECT datetime, open, high, low, close
        FROM prices_bern
        WHERE DATE(datetime) = ?
        ORDER BY datetime
        """
        
        df_prices = conn.execute(query_prices, [date]).df()
        
        if len(df_prices) < 60:  # Au moins 1h de données
            continue
        
        # Scanner par fenêtre glissante de 2h
        window_minutes = 120
        step_minutes = 30
        
        for i in range(0, len(df_prices) - window_minutes, step_minutes):
            window = df_prices.iloc[i:i+window_minutes].copy()
            
            if len(window) < 60:
                continue
            
            baseline = window['close'].iloc[0]
            max_high = window['high'].max()
            min_low = window['low'].min()
            
            impact_up = (max_high - baseline) * 10000
            impact_down = (baseline - min_low) * 10000
            
            if impact_up >= MIN_MOVEMENT_PIPS:
                movement_id += 1
                movement_start = window['datetime'].iloc[0]
                peak_time = window[window['high'] == max_high]['datetime'].iloc[0]
                
                movements.append({
                    'movement_id': movement_id,
                    'movement_datetime': movement_start,
                    'baseline_price': baseline,
                    'direction': 'UP',
                    'impact_pips': impact_up,
                    'peak_time': peak_time,
                    'peak_price': max_high
                })
            
            elif impact_down >= MIN_MOVEMENT_PIPS:
                movement_id += 1
                movement_start = window['datetime'].iloc[0]
                trough_time = window[window['low'] == min_low]['datetime'].iloc[0]
                
                movements.append({
                    'movement_id': movement_id,
                    'movement_datetime': movement_start,
                    'baseline_price': baseline,
                    'direction': 'DOWN',
                    'impact_pips': impact_down,
                    'peak_time': trough_time,
                    'peak_price': min_low
                })
    
    print(f"   ✅ {len(movements)} mouvements forts détectés")
    return movements


def detect_double_wave_pattern(
    df_prices: pd.DataFrame,
    movement_start: pd.Timestamp,
    baseline_price: float,
    direction: str
) -> Optional[Dict]:
    """
    Détecte pattern Double Wave dans les prix après un mouvement fort détecté.
    
    Returns:
        Dict avec métriques Double Wave ou None
    """
    # Fenêtre après mouvement start
    df_after = df_prices[df_prices['datetime'] >= movement_start].copy()
    df_after = df_after[df_after['datetime'] <= movement_start + timedelta(minutes=WINDOW_SCAN_MINUTES)]
    
    if len(df_after) < 20:
        return None
    
    if direction == 'UP':
        # Phase 1: Premier high significatif (dans les 60 premières minutes)
        df_phase1_window = df_after[df_after['datetime'] <= movement_start + timedelta(minutes=60)]
        
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
        # Phase 1: Premier low significatif
        df_phase1_window = df_after[df_after['datetime'] <= movement_start + timedelta(minutes=60)]
        
        if len(df_phase1_window) == 0:
            return None
        
        phase1_idx = df_phase1_window['low'].idxmin()
        phase1_time = df_phase1_window.loc[phase1_idx, 'datetime']
        phase1_price = df_phase1_window.loc[phase1_idx, 'low']
        phase1_pips = (baseline_price - phase1_price) * 10000
        
        if phase1_pips < MIN_PHASE1_PIPS:
            return None
        
        # Pullback: Trouver high maximum après Phase 1
        df_pullback_window = df_after[df_after['datetime'] > phase1_time].copy()
        df_pullback_window = df_pullback_window[df_pullback_window['datetime'] <= phase1_time + timedelta(minutes=30)]
        
        if len(df_pullback_window) == 0:
            return None
        
        pullback_idx = df_pullback_window['high'].idxmax()
        pullback_time = df_pullback_window.loc[pullback_idx, 'datetime']
        pullback_price = df_pullback_window.loc[pullback_idx, 'high']
        pullback_pips = (pullback_price - phase1_price) * 10000
        pullback_ratio = pullback_pips / phase1_pips if phase1_pips > 0 else 0.0
        
        if pullback_ratio < MIN_PULLBACK_RATIO or pullback_ratio > MAX_PULLBACK_RATIO:
            return None
        
        # Phase 2: Trouver low minimum après pullback
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
        
        if phase2_pips < phase1_pips * PHASE2_MIN_RATIO:
            return None
        
        impact_pips = (baseline_price - phase2_price) * 10000
    
    # Calculer durées
    phase1_minutes = (phase1_time - movement_start).total_seconds() / 60
    pullback_minutes = (pullback_time - phase1_time).total_seconds() / 60
    phase2_minutes = (phase2_time - pullback_time).total_seconds() / 60
    
    return {
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


def find_events_for_movement(
    conn: duckdb.DuckDBPyConnection,
    movement_datetime: pd.Timestamp,
    window_minutes: int = 30
) -> List[Dict]:
    """
    Trouve les événements autour d'un mouvement détecté.
    
    Returns:
        Liste d'événements avec leurs scores
    """
    start_time = movement_datetime - timedelta(minutes=window_minutes)
    end_time = movement_datetime + timedelta(minutes=window_minutes)
    
    query = """
    SELECT DISTINCT
        e.ts_utc,
        e.ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich' as ts_bern,
        e.event_title,
        e.country,
        e.importance_n,
        e.actual,
        e.estimate,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc >= ?
      AND e.ts_utc <= ?
      AND e.country IN ('US', 'EU', 'DE', 'FR', 'IT', 'ES', 'UK')
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query, [start_time, end_time]).df()
    
    events = []
    for idx, row in df_events.iterrows():
        events.append({
            'event_time': row['ts_bern'],
            'event_title': row['event_title'],
            'country': row['country'],
            'importance_n': row['importance_n'],
            'empirical_score': row.get('empirical_score', None),
            'actual': row.get('actual', None),
            'estimate': row.get('estimate', None)
        })
    
    return events


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("EXTRACTION DOUBLE WAVE - WORKFLOW CORRECT (Prix → Mouvement → Pattern)")
    print("=" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ÉTAPE 1: Scanner les PRIX pour trouver mouvements forts
    movements = scan_strong_movements(conn, start_date='2023-01-01', end_date='2026-01-01')
    
    if len(movements) == 0:
        print("\n❌ Aucun mouvement fort détecté")
        conn.close()
        return
    
    # ÉTAPE 2: Pour chaque mouvement, détecter le pattern
    print("\n📈 Détection patterns Double Wave...")
    results = []
    
    for mov in movements:
        movement_id = mov['movement_id']
        movement_datetime = mov['movement_datetime']
        baseline_price = mov['baseline_price']
        direction = mov['direction']
        
        # Charger prix autour du mouvement
        start_time = movement_datetime - timedelta(minutes=30)
        end_time = movement_datetime + timedelta(minutes=WINDOW_SCAN_MINUTES)
        
        query = """
        SELECT datetime, open, high, low, close
        FROM prices_bern
        WHERE datetime >= ?
          AND datetime <= ?
        ORDER BY datetime
        """
        
        df_prices = conn.execute(query, [start_time, end_time]).df()
        
        if len(df_prices) == 0:
            continue
        
        if df_prices['datetime'].dtype == 'object':
            df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        
        # Détecter pattern Double Wave
        pattern = detect_double_wave_pattern(df_prices, movement_datetime, baseline_price, direction)
        
        if pattern is None:
            continue  # Pas un Double Wave
        
        # ÉTAPE 3: Trouver événements correspondants
        events = find_events_for_movement(conn, movement_datetime, window_minutes=30)
        
        # Construire résultat
        result = {
            'movement_id': movement_id,
            'movement_datetime': movement_datetime,
            'baseline_price': baseline_price,
            'direction': direction,
            'num_events': len(events),
            **pattern
        }
        
        # Ajouter infos événements (premier événement principal)
        if len(events) > 0:
            main_event = events[0]  # Prendre le premier
            result['event_time'] = main_event['event_time']
            result['event_title'] = main_event['event_title']
            result['country'] = main_event['country']
            result['importance_n'] = main_event['importance_n']
            result['empirical_score'] = main_event.get('empirical_score', None)
        else:
            result['event_time'] = None
            result['event_title'] = None
            result['country'] = None
            result['importance_n'] = None
            result['empirical_score'] = None
        
        results.append(result)
        
        if len(results) % 10 == 0:
            print(f"   {len(results)} Double Wave détectés...")
    
    conn.close()
    
    # Sauvegarder
    if len(results) == 0:
        print("\n❌ Aucun Double Wave détecté")
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
        print(f"   Phase 1 médiane      : {df_results['phase1_pips'].median():.1f} pips en {df_results['phase1_minutes_from_start'].median():.1f} min")
        print(f"   Pullback médian      : {df_results['pullback_ratio'].median():.3f} ({df_results['pullback_minutes_from_phase1'].median():.1f} min)")
        print(f"   Phase 2 médiane      : {df_results['phase2_pips'].median():.1f} pips en {df_results['phase2_minutes_from_pullback'].median():.1f} min")
        print(f"   Avec événements      : {df_results['num_events'].sum()}/{len(df_results)} mouvements ont des événements")


if __name__ == "__main__":
    main()

