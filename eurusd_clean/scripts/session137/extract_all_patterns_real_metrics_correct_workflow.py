"""
EXTRACTION MÉTRIQUES RÉELLES TOUS PATTERNS - WORKFLOW CORRECT
Session 137 - Recalibration Formules V1.2

WORKFLOW CORRECT:
1. Scanner les PRIX pour trouver mouvements forts (indépendamment des événements)
2. Détecter le pattern (Double Wave, Single Wave Fort, ZigZag, etc.)
3. ENSUITE chercher les événements correspondants

Patterns détectés:
- DOUBLE_WAVE_UP / DOUBLE_WAVE_DOWN
- SINGLE_WAVE_FORT_UP / SINGLE_WAVE_FORT_DOWN
- ZIGZAG_BULLISH / ZIGZAG_BEARISH

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
OUTPUT_CSV = Path(__file__).parent / "all_patterns_real_metrics_correct_workflow.csv"

# =============================================================================
# PARAMÈTRES DÉTECTION
# =============================================================================

MIN_MOVEMENT_PIPS = 35.0  # Minimum pour considérer un mouvement fort
WINDOW_SCAN_MINUTES = 120  # Fenêtre d'analyse après détection mouvement

# Double Wave
MIN_PHASE1_PIPS_DW = 20.0
MIN_PHASE2_PIPS_DW = 15.0
MIN_PULLBACK_RATIO_DW = 0.25
MAX_PULLBACK_RATIO_DW = 0.70
PHASE2_MIN_RATIO_DW = 0.5

# Single Wave Fort
MIN_IMPACT_SW = 40.0
MAX_PULLBACK_RATIO_SW = 0.30

# ZigZag
MIN_PEAKS_ZZ = 3
MIN_PULLBACK_RATIO_ZZ = 0.10
MAX_PULLBACK_RATIO_ZZ = 0.60

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def pips_diff(price1: float, price2: float) -> float:
    """Calcule différence en pips entre deux prix"""
    return abs(price1 - price2) * 10000


def detect_movement_start(
    df_prices: pd.DataFrame,
    baseline_idx: int,
    threshold_pips: float = 5.0
) -> Optional[Tuple[int, str, float]]:
    """
    Détecte le début réel d'un mouvement UP ou DOWN.
    
    Args:
        df_prices: DataFrame avec prix
        baseline_idx: Index de la baseline (prix de référence)
        threshold_pips: Seuil minimum en pips pour considérer un mouvement
    
    Returns:
        (index_début, direction, baseline_price) ou None
    """
    if baseline_idx >= len(df_prices) - 10:
        return None
    
    baseline_price = df_prices.iloc[baseline_idx]['close']
    baseline_time = df_prices.iloc[baseline_idx]['datetime']
    
    # Scanner les bougies après la baseline
    for i in range(baseline_idx + 1, len(df_prices)):
        row = df_prices.iloc[i]
        
        # Vérifier mouvement UP
        if row['high'] > baseline_price + (threshold_pips / 10000):
            return (i, 'UP', baseline_price)
        
        # Vérifier mouvement DOWN
        if row['low'] < baseline_price - (threshold_pips / 10000):
            return (i, 'DOWN', baseline_price)
    
    return None


def find_movement_peak(
    df_prices: pd.DataFrame,
    start_idx: int,
    baseline_price: float,
    direction: str,
    max_window_minutes: int = 120
) -> Optional[Tuple[int, float, float]]:
    """
    Trouve le pic/trough réel d'un mouvement.
    
    Args:
        baseline_price: Prix baseline (doit être passé explicitement)
    
    Returns:
        (index_peak, peak_price, impact_pips) ou None
    """
    start_time = df_prices.iloc[start_idx]['datetime']
    
    end_time = start_time + timedelta(minutes=max_window_minutes)
    df_window = df_prices[
        (df_prices['datetime'] >= start_time) & 
        (df_prices['datetime'] <= end_time)
    ].copy()
    
    if len(df_window) == 0:
        return None
    
    if direction == 'UP':
        peak_idx = df_window['high'].idxmax()
        peak_price = df_window.loc[peak_idx, 'high']
        impact_pips = (peak_price - baseline_price) * 10000
    else:  # DOWN
        peak_idx = df_window['low'].idxmin()
        peak_price = df_window.loc[peak_idx, 'low']
        impact_pips = (baseline_price - peak_price) * 10000
    
    # Trouver l'index dans df_prices original
    peak_time = df_prices.loc[peak_idx, 'datetime']
    peak_idx_original = df_prices[df_prices['datetime'] == peak_time].index[0]
    
    return (peak_idx_original, peak_price, impact_pips)


def scan_strong_movements(
    conn: duckdb.DuckDBPyConnection,
    start_date: str = '2023-01-01',
    end_date: str = '2026-01-01'
) -> List[Dict]:
    """
    Scanne les prix pour trouver des mouvements forts réels (indépendamment des événements).
    Détecte précisément le début de chaque mouvement.
    
    Returns:
        Liste de dict avec mouvement_id, movement_datetime, baseline_price, direction, impact_pips
    """
    print(f"\n📊 Scan des prix pour mouvements forts réels >= {MIN_MOVEMENT_PIPS} pips...")
    
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
    processed_times = set()  # Éviter doublons
    
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
        
        if df_prices['datetime'].dtype == 'object':
            df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        
        # Scanner minute par minute pour détecter TOUS les mouvements
        # Pour chaque minute, vérifier si un mouvement commence (dépassement seuil depuis minute précédente)
        i = 10
        movement_windows = []  # Stocker les fenêtres de mouvements détectés
        
        while i < len(df_prices) - 60:
            # Utiliser une baseline plus large (low/high minimum sur 0-90 min avant)
            # Nécessite au moins 90 minutes de données avant
            if i < 90:
                i += 1
                continue
            
            current_idx = i
            current_row = df_prices.iloc[current_idx]
            current_time = current_row['datetime']
            
            # Chercher le low/high minimum dans une fenêtre plus large (0-90 min avant)
            # Pour capturer les mouvements progressifs qui commencent plus tôt
            window_start_idx = max(0, i - 90)
            window_end_idx = i - 1
            df_baseline_window = df_prices.iloc[window_start_idx:window_end_idx+1]
            
            if len(df_baseline_window) == 0:
                i += 1
                continue
            
            # Pour mouvement UP: utiliser le low minimum de la fenêtre
            # Pour mouvement DOWN: utiliser le high maximum de la fenêtre
            baseline_low = df_baseline_window['low'].min()
            baseline_high = df_baseline_window['high'].max()
            baseline_close = df_prices.iloc[i - 1]['close']  # Close de la minute précédente pour détection
            baseline_time = df_prices.iloc[i - 1]['datetime']  # Temps de référence
            
            # Ne plus bloquer les mouvements qui se chevauchent
            # On détectera tous les mouvements qui commencent, et le filtre too_close gérera les doublons
            
            # Vérifier si un mouvement commence à cette minute
            # DÉTECTION DOUBLE: début progressif (>= 5 pips depuis baseline large) ET mouvement explosif (>= 15 pips en 1 min)
            movement_found = False
            direction = None
            movement_type = None  # 'progressive' ou 'explosive'
            
            # Calculer impact depuis baseline large (low/high sur 30-60 min)
            high_diff_from_baseline_low = (current_row['high'] - baseline_low) * 10000
            low_diff_from_baseline_high = (baseline_high - current_row['low']) * 10000
            
            # Calculer variation depuis minute précédente (pour détecter mouvement explosif)
            if current_idx > 1:
                prev_row = df_prices.iloc[current_idx - 1]
                prev_baseline_close = df_prices.iloc[current_idx - 2]['close'] if current_idx > 1 else baseline_close
                high_diff_explosive = (current_row['high'] - prev_baseline_close) * 10000
                low_diff_explosive = (prev_baseline_close - current_row['low']) * 10000
            else:
                high_diff_explosive = 0
                low_diff_explosive = 0
            
            # Vérifier mouvement UP
            # Option 1: Mouvement explosif (>= 15 pips en 1 min depuis close précédent)
            if high_diff_explosive >= 15.0:
                movement_found = True
                direction = 'UP'
                movement_type = 'explosive'
            # Option 2: Début progressif (>= 3 pips depuis baseline low large) ET pas encore détecté
            # Seuil abaissé à 3 pips pour capturer les débuts progressifs
            elif high_diff_from_baseline_low >= 3.0:
                # Vérifier qu'on n'a pas déjà détecté ce mouvement progressif
                # (éviter de détecter plusieurs fois le même mouvement)
                movement_found = True
                direction = 'UP'
                movement_type = 'progressive'
            
            # Vérifier mouvement DOWN
            elif low_diff_explosive >= 15.0:
                movement_found = True
                direction = 'DOWN'
                movement_type = 'explosive'
            elif low_diff_from_baseline_high >= 3.0:
                movement_found = True
                direction = 'DOWN'
                movement_type = 'progressive'
            
            if not movement_found:
                i += 1
                continue
            
            # Un mouvement commence à cette minute !
            movement_start_time = current_time
            
            # Vérifier qu'on n'a pas déjà traité ce mouvement
            if movement_start_time in processed_times:
                i += 1
                continue
            
            # Déterminer baseline pour calcul impact (low pour UP, high pour DOWN)
            # Toujours utiliser baseline large pour impact précis
            if direction == 'UP':
                baseline_for_impact = baseline_low
            else:
                baseline_for_impact = baseline_high
            
            # Pour mouvement progressif, ajuster le start_time au moment où l'impact atteint 3 pips
            # Mais chercher dans une fenêtre plus restreinte (20-30 min avant) pour éviter de remonter trop loin
            if movement_type == 'progressive':
                # Trouver le premier moment où l'impact atteint 3 pips depuis baseline large
                # Chercher dans les 30 dernières minutes pour trouver le vrai début progressif
                movement_start_time = current_time
                search_start = max(0, i - 30)  # Limiter à 30 min avant
                
                for j in range(search_start, i + 1):
                    check_row = df_prices.iloc[j]
                    if direction == 'UP':
                        check_impact = (check_row['high'] - baseline_low) * 10000
                    else:
                        check_impact = (baseline_high - check_row['low']) * 10000
                    
                    if check_impact >= 3.0:
                        movement_start_time = check_row['datetime']
                        current_idx = j
                        current_row = check_row
                        break
            else:
                movement_start_time = current_time
            
            # Trouver le pic/trough réel depuis ce point
            peak_info = find_movement_peak(df_prices, current_idx, baseline_for_impact, direction, max_window_minutes=120)
            
            if peak_info is None:
                i += 1
                continue
            
            peak_idx, peak_price, impact_pips = peak_info
            
            # Recalculer impact avec la bonne baseline (baseline large)
            if direction == 'UP':
                impact_pips = (peak_price - baseline_low) * 10000
            else:
                impact_pips = (baseline_high - peak_price) * 10000
            
            # Vérifier que l'impact est suffisant
            if impact_pips < MIN_MOVEMENT_PIPS:
                i += 1
                continue
            
            # Éviter les mouvements qui se chevauchent trop
            # MAIS permettre si les baselines sont différentes (mouvements indépendants)
            too_close = False
            for prev_mov in movements[-20:]:
                time_diff = abs((movement_start_time - prev_mov['movement_datetime']).total_seconds() / 60)
                if time_diff < 15:
                    # Vérifier si les baselines sont différentes (mouvements indépendants)
                    prev_baseline = prev_mov.get('baseline_time', prev_mov['movement_datetime'])
                    baseline_diff = abs((baseline_time - pd.to_datetime(prev_baseline)).total_seconds() / 60)
                    
                    # Si les baselines sont différentes de plus de 5 min, c'est un mouvement indépendant
                    if baseline_diff < 5:
                        too_close = True
                        break
            
            if too_close:
                i += 1
                continue
            
            # Marquer les temps traités
            processed_times.add(movement_start_time)
            
            # Enregistrer la fenêtre du mouvement
            movement_windows.append({
                'start_idx': current_idx,
                'peak_idx': peak_idx,
                'end_idx': peak_idx + 30,
                'movement_start': movement_start_time
            })
            
            movement_id += 1
            peak_time = df_prices.iloc[peak_idx]['datetime']
            
            # Enregistrer baseline_price comme close pour référence, mais impact calculé depuis low/high large
            movements.append({
                'movement_id': movement_id,
                'movement_datetime': movement_start_time,  # Début progressif ou explosif selon type
                'movement_type': movement_type,  # 'progressive' ou 'explosive'
                'baseline_price': baseline_close,  # Close pour référence
                'baseline_low': baseline_low,  # Low minimum sur 30-60 min (pour calcul impact UP)
                'baseline_high': baseline_high,  # High maximum sur 30-60 min (pour calcul impact DOWN)
                'baseline_time': baseline_time,
                'direction': direction,
                'impact_pips': impact_pips,  # Impact calculé depuis baseline large
                'peak_time': peak_time,
                'peak_price': peak_price
            })
            
            # Avancer après le pic pour éviter de détecter le même mouvement
            i = peak_idx + 1
    
    print(f"   ✅ {len(movements)} mouvements forts réels détectés")
    return movements


# =============================================================================
# DÉTECTION PATTERNS
# =============================================================================

def detect_double_wave(
    df_prices: pd.DataFrame,
    movement_start: pd.Timestamp,
    baseline_price: float,
    direction: str,
    baseline_low: float = None,
    baseline_high: float = None
) -> Optional[Dict]:
    """Détecte pattern Double Wave"""
    df_after = df_prices[df_prices['datetime'] >= movement_start].copy()
    df_after = df_after[df_after['datetime'] <= movement_start + timedelta(minutes=WINDOW_SCAN_MINUTES)]
    
    if len(df_after) < 20:
        return None
    
    if direction == 'UP':
        # Phase 1: Chercher le PREMIER pic local significatif (dans les 20 premières minutes)
        df_phase1_search = df_after[df_after['datetime'] <= movement_start + timedelta(minutes=20)].copy()
        if len(df_phase1_search) < 5:
            return None
        
        # Trouver TOUS les pics locaux significatifs, puis prendre le plus élevé
        local_peaks = []
        
        for i in range(2, len(df_phase1_search) - 2):
            window = df_phase1_search.iloc[i-2:i+3]
            local_max = window['high'].max()
            local_max_idx = window['high'].idxmax()
            
            # Vérifier si c'est un pic local (plus haut que les 2 minutes avant et après)
            if local_max_idx == df_phase1_search.index[i]:
                candidate_price = df_phase1_search.iloc[i]['high']
                candidate_pips = (candidate_price - baseline_price) * 10000
                
                # Enregistrer tous les pics significatifs (>= 20 pips)
                if candidate_pips >= MIN_PHASE1_PIPS_DW:
                    local_peaks.append({
                        'idx': df_phase1_search.index[i],
                        'time': df_phase1_search.iloc[i]['datetime'],
                        'price': candidate_price,
                        'pips': candidate_pips
                    })
        
        # Prendre le pic le plus élevé parmi les pics locaux
        if len(local_peaks) > 0:
            best_peak = max(local_peaks, key=lambda x: x['pips'])
            phase1_idx = best_peak['idx']
            phase1_time = best_peak['time']
            phase1_price = best_peak['price']
        else:
            # Si pas de pic local trouvé, prendre le maximum dans les 20 premières minutes
            phase1_idx = df_phase1_search['high'].idxmax()
            phase1_time = df_phase1_search.loc[phase1_idx, 'datetime']
            phase1_price = df_phase1_search.loc[phase1_idx, 'high']
        
        # Utiliser baseline_low pour calcul impact UP (plus précis)
        baseline_for_calc = baseline_low if baseline_low is not None else baseline_price
        phase1_pips = (phase1_price - baseline_for_calc) * 10000
        
        if phase1_pips < MIN_PHASE1_PIPS_DW:
            return None
        
        # Pullback: Trouver low minimum après Phase 1 (dans les 20 min)
        df_pullback = df_after[(df_after['datetime'] > phase1_time) & 
                               (df_after['datetime'] <= phase1_time + timedelta(minutes=20))]
        if len(df_pullback) == 0:
            return None
        
        pullback_idx = df_pullback['low'].idxmin()
        pullback_time = df_pullback.loc[pullback_idx, 'datetime']
        pullback_price = df_pullback.loc[pullback_idx, 'low']
        pullback_pips = (phase1_price - pullback_price) * 10000
        pullback_ratio = pullback_pips / phase1_pips if phase1_pips > 0 else 0.0
        
        # Accepter pullback jusqu'à 85% pour capturer cas comme 11.09 (84%)
        if pullback_ratio < MIN_PULLBACK_RATIO_DW or pullback_ratio > 0.85:
            return None
        
        # Phase 2: Trouver high maximum après pullback (dans les 40 min)
        df_phase2 = df_after[(df_after['datetime'] > pullback_time) & 
                            (df_after['datetime'] <= pullback_time + timedelta(minutes=40))]
        if len(df_phase2) == 0:
            return None
        
        phase2_idx = df_phase2['high'].idxmax()
        phase2_time = df_phase2.loc[phase2_idx, 'datetime']
        phase2_price = df_phase2.loc[phase2_idx, 'high']
        phase2_pips = (phase2_price - pullback_price) * 10000
        
        if phase2_pips < MIN_PHASE2_PIPS_DW or phase2_pips < phase1_pips * PHASE2_MIN_RATIO_DW:
            return None
        
        # Impact total depuis baseline appropriée
        baseline_for_calc = baseline_low if baseline_low is not None else baseline_price
        impact_pips = (phase2_price - baseline_for_calc) * 10000
        
    else:  # DOWN
        # Phase 1: Chercher le PREMIER trough local significatif
        df_phase1_search = df_after[df_after['datetime'] <= movement_start + timedelta(minutes=20)].copy()
        if len(df_phase1_search) < 5:
            return None
        
        # Trouver le premier trough local
        phase1_price = None
        phase1_time = None
        phase1_idx = None
        
        for i in range(2, len(df_phase1_search) - 2):
            window = df_phase1_search.iloc[i-2:i+3]
            local_min = window['low'].min()
            local_min_idx = window['low'].idxmin()
            
            if local_min_idx == df_phase1_search.index[i]:
                candidate_price = df_phase1_search.iloc[i]['low']
                candidate_pips = (baseline_price - candidate_price) * 10000
                
                if candidate_pips >= MIN_PHASE1_PIPS_DW:
                    phase1_price = candidate_price
                    phase1_time = df_phase1_search.iloc[i]['datetime']
                    phase1_idx = df_phase1_search.index[i]
                    break
        
        if phase1_price is None:
            phase1_idx = df_phase1_search['low'].idxmin()
            phase1_time = df_phase1_search.loc[phase1_idx, 'datetime']
            phase1_price = df_phase1_search.loc[phase1_idx, 'low']
        
        # Utiliser baseline_high pour calcul impact DOWN (plus précis)
        baseline_for_calc = baseline_high if baseline_high is not None else baseline_price
        phase1_pips = (baseline_for_calc - phase1_price) * 10000
        
        if phase1_pips < MIN_PHASE1_PIPS_DW:
            return None
        
        # Pullback: Trouver high maximum après Phase 1 (dans les 20 min)
        df_pullback = df_after[(df_after['datetime'] > phase1_time) & 
                               (df_after['datetime'] <= phase1_time + timedelta(minutes=20))]
        if len(df_pullback) == 0:
            return None
        
        pullback_idx = df_pullback['high'].idxmax()
        pullback_time = df_pullback.loc[pullback_idx, 'datetime']
        pullback_price = df_pullback.loc[pullback_idx, 'high']
        pullback_pips = (pullback_price - phase1_price) * 10000
        pullback_ratio = pullback_pips / phase1_pips if phase1_pips > 0 else 0.0
        
        if pullback_ratio < MIN_PULLBACK_RATIO_DW or pullback_ratio > 0.85:
            return None
        
        # Phase 2: Trouver low minimum après pullback (dans les 40 min)
        df_phase2 = df_after[(df_after['datetime'] > pullback_time) & 
                            (df_after['datetime'] <= pullback_time + timedelta(minutes=40))]
        if len(df_phase2) == 0:
            return None
        
        phase2_idx = df_phase2['low'].idxmin()
        phase2_time = df_phase2.loc[phase2_idx, 'datetime']
        phase2_price = df_phase2.loc[phase2_idx, 'low']
        phase2_pips = (pullback_price - phase2_price) * 10000
        
        if phase2_pips < MIN_PHASE2_PIPS_DW or phase2_pips < phase1_pips * PHASE2_MIN_RATIO_DW:
            return None
        
        # Impact total depuis baseline appropriée
        baseline_for_calc = baseline_high if baseline_high is not None else baseline_price
        impact_pips = (baseline_for_calc - phase2_price) * 10000
    
    phase1_minutes = (phase1_time - movement_start).total_seconds() / 60
    pullback_minutes = (pullback_time - phase1_time).total_seconds() / 60
    phase2_minutes = (phase2_time - pullback_time).total_seconds() / 60
    
    return {
        'pattern_type': f'DOUBLE_WAVE_{direction}',
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


def detect_single_wave_fort(
    df_prices: pd.DataFrame,
    movement_start: pd.Timestamp,
    baseline_price: float,
    direction: str,
    baseline_low: float = None,
    baseline_high: float = None
) -> Optional[Dict]:
    """Détecte pattern Single Wave Fort"""
    df_after = df_prices[df_prices['datetime'] >= movement_start].copy()
    df_after = df_after[df_after['datetime'] <= movement_start + timedelta(minutes=WINDOW_SCAN_MINUTES)]
    
    if len(df_after) < 10:
        return None
    
    if direction == 'UP':
        # Pic maximum
        peak_idx = df_after['high'].idxmax()
        peak_time = df_after.loc[peak_idx, 'datetime']
        peak_price = df_after.loc[peak_idx, 'high']
        # Utiliser baseline_low pour calcul impact UP (plus précis)
        baseline_for_calc = baseline_low if baseline_low is not None else baseline_price
        impact_pips = (peak_price - baseline_for_calc) * 10000
        
        if impact_pips < MIN_IMPACT_SW:
            return None
        
        # Vérifier qu'il n'y a pas de deuxième pic significatif (sinon c'est Double Wave)
        # Chercher pullback dans les 60 min après pic
        df_pullback = df_after[(df_after['datetime'] > peak_time) & 
                               (df_after['datetime'] <= peak_time + timedelta(minutes=60))]
        
        if len(df_pullback) > 0:
            pullback_price = df_pullback['low'].min()
            pullback_pips = (peak_price - pullback_price) * 10000
            pullback_ratio = pullback_pips / impact_pips if impact_pips > 0 else 0.0
            
            # Si pullback > 30%, ce n'est pas un Single Wave Fort
            if pullback_ratio > MAX_PULLBACK_RATIO_SW:
                return None
            
            # Vérifier qu'il n'y a pas de Phase 2 significative après pullback
            df_phase2 = df_after[(df_after['datetime'] > df_pullback[df_pullback['low'] == pullback_price]['datetime'].iloc[0]) & 
                                (df_after['datetime'] <= peak_time + timedelta(minutes=120))]
            
            if len(df_phase2) > 0:
                phase2_peak = df_phase2['high'].max()
                phase2_pips = (phase2_peak - pullback_price) * 10000
                
                # Si Phase 2 > 50% de Phase 1, c'est un Double Wave
                if phase2_pips > impact_pips * 0.5:
                    return None
        
        peak_minutes = (peak_time - movement_start).total_seconds() / 60
        
    else:  # DOWN
        # Trough minimum
        trough_idx = df_after['low'].idxmin()
        trough_time = df_after.loc[trough_idx, 'datetime']
        trough_price = df_after.loc[trough_idx, 'low']
        # Utiliser baseline_high pour calcul impact DOWN (plus précis)
        baseline_for_calc = baseline_high if baseline_high is not None else baseline_price
        impact_pips = (baseline_for_calc - trough_price) * 10000
        
        if impact_pips < MIN_IMPACT_SW:
            return None
        
        # Vérifier pullback
        df_pullback = df_after[(df_after['datetime'] > trough_time) & 
                              (df_after['datetime'] <= trough_time + timedelta(minutes=60))]
        
        if len(df_pullback) > 0:
            pullback_price = df_pullback['high'].max()
            pullback_pips = (pullback_price - trough_price) * 10000
            pullback_ratio = pullback_pips / impact_pips if impact_pips > 0 else 0.0
            
            if pullback_ratio > MAX_PULLBACK_RATIO_SW:
                return None
            
            df_phase2 = df_after[(df_after['datetime'] > df_pullback[df_pullback['high'] == pullback_price]['datetime'].iloc[0]) & 
                               (df_after['datetime'] <= trough_time + timedelta(minutes=120))]
            
            if len(df_phase2) > 0:
                phase2_trough = df_phase2['low'].min()
                phase2_pips = (pullback_price - phase2_trough) * 10000
                
                if phase2_pips > impact_pips * 0.5:
                    return None
        
        peak_time = trough_time
        peak_price = trough_price
        peak_minutes = (trough_time - movement_start).total_seconds() / 60
    
    return {
        'pattern_type': f'SINGLE_WAVE_FORT_{direction}',
        'peak_time': peak_time,
        'peak_price': peak_price,
        'peak_minutes_from_start': peak_minutes,
        'impact_pips': impact_pips,
    }


def detect_zigzag(
    df_prices: pd.DataFrame,
    movement_start: pd.Timestamp,
    baseline_price: float,
    direction: str
) -> Optional[Dict]:
    """Détecte pattern ZigZag (3+ pics successifs)"""
    df_after = df_prices[df_prices['datetime'] >= movement_start].copy()
    df_after = df_after[df_after['datetime'] <= movement_start + timedelta(minutes=WINDOW_SCAN_MINUTES)]
    
    if len(df_after) < 30:
        return None
    
    # Trouver extrema locaux (fenêtre 5 min)
    peaks = []
    troughs = []
    window = 5
    
    for i in range(window, len(df_after) - window):
        if direction == 'UP':
            # Chercher peaks
            high = df_after.iloc[i]['high']
            is_peak = True
            for j in range(i - window, i + window + 1):
                if j != i and df_after.iloc[j]['high'] >= high:
                    is_peak = False
                    break
            if is_peak:
                peaks.append((df_after.iloc[i]['datetime'], high))
        else:  # DOWN
            # Chercher troughs
            low = df_after.iloc[i]['low']
            is_trough = True
            for j in range(i - window, i + window + 1):
                if j != i and df_after.iloc[j]['low'] <= low:
                    is_trough = False
                    break
            if is_trough:
                troughs.append((df_after.iloc[i]['datetime'], low))
    
    # Pour ZigZag, on a besoin d'au moins 3 pics/troughs
    if direction == 'UP':
        if len(peaks) < MIN_PEAKS_ZZ:
            return None
        
        # Vérifier pullbacks entre pics
        total_amplitude = 0
        for i in range(len(peaks) - 1):
            peak1_price = peaks[i][1]
            peak2_price = peaks[i+1][1]
            
            # Trouver trough entre les deux pics
            trough_between = [t for t in troughs if peaks[i][0] < t[0] < peaks[i+1][0]]
            if len(trough_between) == 0:
                return None
            
            trough_price = min([t[1] for t in trough_between])
            pullback_pips = (peak1_price - trough_price) * 10000
            segment_pips = abs(peak2_price - peak1_price) * 10000
            
            if segment_pips > 0:
                pullback_ratio = pullback_pips / segment_pips
                if pullback_ratio < MIN_PULLBACK_RATIO_ZZ or pullback_ratio > MAX_PULLBACK_RATIO_ZZ:
                    return None
            
            total_amplitude += abs(peak2_price - peak1_price) * 10000
        
        impact_pips = (peaks[-1][1] - baseline_price) * 10000
        num_peaks = len(peaks)
        
    else:  # DOWN
        if len(troughs) < MIN_PEAKS_ZZ:
            return None
        
        # Vérifier pullbacks entre troughs
        for i in range(len(troughs) - 1):
            trough1_price = troughs[i][1]
            trough2_price = troughs[i+1][1]
            
            peak_between = [p for p in peaks if troughs[i][0] < p[0] < troughs[i+1][0]]
            if len(peak_between) == 0:
                return None
            
            peak_price = max([p[1] for p in peak_between])
            pullback_pips = (peak_price - trough1_price) * 10000
            segment_pips = abs(trough2_price - trough1_price) * 10000
            
            if segment_pips > 0:
                pullback_ratio = pullback_pips / segment_pips
                if pullback_ratio < MIN_PULLBACK_RATIO_ZZ or pullback_ratio > MAX_PULLBACK_RATIO_ZZ:
                    return None
        
        impact_pips = (baseline_price - troughs[-1][1]) * 10000
        num_peaks = len(troughs)
    
    return {
        'pattern_type': f'ZIGZAG_{"BULLISH" if direction == "UP" else "BEARISH"}',
        'num_peaks': num_peaks,
        'impact_pips': impact_pips,
    }


def detect_pattern(
    df_prices: pd.DataFrame,
    movement_start: pd.Timestamp,
    baseline_price: float,
    direction: str,
    baseline_low: float = None,
    baseline_high: float = None
) -> Optional[Dict]:
    """
    Détecte le pattern d'un mouvement (Double Wave, Single Wave Fort, ZigZag).
    Essaie dans l'ordre : Double Wave → Single Wave Fort → ZigZag
    """
    # Essayer Double Wave d'abord (critères les plus stricts)
    pattern = detect_double_wave(df_prices, movement_start, baseline_price, direction, baseline_low, baseline_high)
    if pattern:
        return pattern
    
    # Essayer Single Wave Fort
    pattern = detect_single_wave_fort(df_prices, movement_start, baseline_price, direction, baseline_low, baseline_high)
    if pattern:
        return pattern
    
    # Essayer ZigZag
    pattern = detect_zigzag(df_prices, movement_start, baseline_price, direction)
    if pattern:
        return pattern
    
    return None


def find_events_for_movement(
    conn: duckdb.DuckDBPyConnection,
    movement_datetime: pd.Timestamp,
    window_minutes: int = 30
) -> List[Dict]:
    """Trouve les événements autour d'un mouvement détecté"""
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
        })
    
    return events


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("EXTRACTION TOUS PATTERNS - WORKFLOW CORRECT (Prix → Mouvement → Pattern)")
    print("=" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ÉTAPE 1: Scanner les PRIX pour trouver mouvements forts
    movements = scan_strong_movements(conn, start_date='2023-01-01', end_date='2026-01-01')
    
    if len(movements) == 0:
        print("\n❌ Aucun mouvement fort détecté")
        conn.close()
        return
    
    # ÉTAPE 2: Pour chaque mouvement, détecter le pattern
    print("\n📈 Détection patterns...")
    results = []
    pattern_counts = {}
    
    for mov in movements:
        movement_id = mov['movement_id']
        movement_datetime = mov['movement_datetime']
        baseline_price = mov['baseline_price']
        baseline_low = mov.get('baseline_low')
        baseline_high = mov.get('baseline_high')
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
        
        # Détecter pattern (avec baseline_low et baseline_high pour calcul impact précis)
        pattern = detect_pattern(df_prices, movement_datetime, baseline_price, direction, baseline_low, baseline_high)
        
        if pattern is None:
            continue  # Aucun pattern détecté
        
        pattern_type = pattern['pattern_type']
        pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
        
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
            main_event = events[0]
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
        
        if len(results) % 100 == 0:
            print(f"   {len(results)} patterns détectés...")
    
    conn.close()
    
    # Sauvegarder
    if len(results) == 0:
        print("\n❌ Aucun pattern détecté")
        return
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n✅ {len(results)} patterns détectés")
    print(f"   Sauvegardé dans: {OUTPUT_CSV}")
    
    # Statistiques par pattern
    print("\n📊 Statistiques par pattern:")
    for pattern_type, count in sorted(pattern_counts.items()):
        df_pattern = df_results[df_results['pattern_type'] == pattern_type]
        print(f"\n   {pattern_type}: {count} cas")
        if len(df_pattern) > 0:
            print(f"      Impact médian: {df_pattern['impact_pips'].median():.1f} pips")
            if 'phase1_pips' in df_pattern.columns:
                print(f"      Phase 1 médiane: {df_pattern['phase1_pips'].median():.1f} pips")
            if 'peak_minutes_from_start' in df_pattern.columns:
                print(f"      Durée pic médiane: {df_pattern['peak_minutes_from_start'].median():.1f} min")


if __name__ == "__main__":
    main()

