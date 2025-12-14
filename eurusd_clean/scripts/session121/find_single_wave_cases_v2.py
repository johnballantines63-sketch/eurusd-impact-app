#!/usr/bin/env python3
"""
Scanner DB pour identifier cas Single Wave (2024-2025)

OBJECTIF: Trouver 5+ cas Single Wave pour validation détecteurs V2
- 3+ cas Single Fort (> 40 pips)
- 2+ cas Single Intermediate (20-40 pips)

CRITÈRES:
- 1 pic dominant après event
- Impact 20-80 pips
- Pullback < 20% (Fort) ou < 30% (Intermediate)
- Events HIGH importance

APPROCHE: Approche bottom-up (scanner prix pour détecter patterns réels)
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import json

# Imports fonctions utilitaires rev10
session119_dir = Path(__file__).parent.parent / 'session119'
sys.path.insert(0, str(session119_dir))

from double_wave_detector_rev10 import (
    load_ohlc_1m_duckdb,
    atr1m,
    to_pips,
    is_local_peak,
    is_local_trough
)

# Imports détecteurs V2
session120_dir = Path(__file__).parent.parent / 'session120'
sys.path.insert(0, str(session120_dir))

from base_pattern_detector_v2 import prepare_dataframe


def load_high_events(db_path: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Charge événements HIGH importance période donnée
    
    Args:
        db_path: Chemin warehouse.duckdb
        start_date: Date début 'YYYY-MM-DD'
        end_date: Date fin 'YYYY-MM-DD'
    
    Returns:
        DataFrame events avec colonnes: ts_utc, event_title, importance_n, actual, estimate, forecast, country
    """
    conn = duckdb.connect(db_path, read_only=True)
    
    query = """
    SELECT 
        ts_utc,
        country,
        event_title,
        importance_n,
        actual,
        estimate,
        forecast
    FROM events
    WHERE importance_n = 3
      AND ts_utc >= ?
      AND ts_utc <= ?
    ORDER BY ts_utc
    """
    
    df = conn.execute(query, [start_date, end_date]).df()
    conn.close()
    
    return df


def calculate_baseline(df_ohlc: pd.DataFrame, event_time: pd.Timestamp) -> float:
    """
    Calcule baseline = close(t-1) avant event
    
    BASELINE VALIDÉE (Session 118): close de la dernière barre AVANT event
    """
    before_event = df_ohlc[df_ohlc.index < event_time]
    
    if len(before_event) == 0:
        return None
    
    return before_event['close'].iloc[-1]


def find_local_extrema_adaptive(df_ohlc: pd.DataFrame, after_time: pd.Timestamp, width: int = 2) -> dict:
    """
    Trouve extrema locaux après time donné
    
    Args:
        df_ohlc: DataFrame OHLC avec ATR
        after_time: Chercher extrema après ce timestamp
        width: Largeur fenêtre (2 = validé rev10/rev12)
    
    Returns:
        {
            'peaks': List[(timestamp, price)],
            'troughs': List[(timestamp, price)]
        }
    """
    df_after = df_ohlc[df_ohlc.index > after_time].copy()
    
    if len(df_after) < 2*width + 1:
        return {'peaks': [], 'troughs': []}
    
    peaks = []
    troughs = []
    
    highs = df_after['high'].values
    lows = df_after['low'].values
    times = df_after.index
    
    for i in range(width, len(df_after) - width):
        # Peak
        if is_local_peak(pd.Series(highs), i, width):
            peaks.append((times[i], highs[i]))
        
        # Trough
        if is_local_trough(pd.Series(lows), i, width):
            troughs.append((times[i], lows[i]))
    
    return {'peaks': peaks, 'troughs': troughs}


def filter_significant_extrema(extrema: list, baseline: float, atr_median: float, min_pips: float = 5.0) -> list:
    """
    Filtre extrema significatifs (seuil ATR adaptatif)
    
    SEUIL V2: max(0.5 * ATR, 5 pips)
    """
    min_variation = max(atr_median * 0.5, min_pips / 10000)
    
    significant = []
    for time, price in extrema:
        variation = abs(price - baseline)
        if variation >= min_variation:
            significant.append((time, price, to_pips(variation)))
    
    return significant


def analyze_single_wave_candidate(
    df_ohlc: pd.DataFrame,
    event_time: pd.Timestamp,
    baseline: float,
    peaks: list,
    troughs: list
) -> dict:
    """
    Analyse candidat Single Wave
    
    CRITÈRES ASSOUPLIS (Session 121 - fix bug 1er août) :
    1. Pic dominant : > 2x second pic OU dominance > 60% (seulement pics significatifs > 15 pips)
    2. Impact 20-120 pips (augmenté pour capturer gros mouvements)
    3. Pullback < 30% (Fort) ou < 40% (Intermediate) - assoupli
    
    Returns:
        {
            'is_single_wave': bool,
            'type': 'fort' / 'intermediate' / None,
            'peak_time': Timestamp,
            'peak_price': float,
            'impact_pips': float,
            'pullback_ratio': float,
            'quality_score': float
        }
    """
    if len(peaks) == 0:
        return {'is_single_wave': False}
    
    # Trouver pic maximum (impact depuis baseline)
    max_peak = None
    max_impact = 0
    
    for time, price, pips in peaks:
        impact = abs(price - baseline)
        if impact > max_impact:
            max_impact = impact
            max_peak = (time, price, pips)
    
    if max_peak is None:
        return {'is_single_wave': False}
    
    peak_time, peak_price, impact_pips = max_peak
    
    # CORRECTION BUG #1 : Ne compter que pics significatifs (> 15 pips) pour dominance
    significant_peaks = [p for p in peaks if p[2] >= 15.0]  # Seuil 15 pips
    
    if len(significant_peaks) == 0:
        return {'is_single_wave': False}
    
    # Dominance par rapport aux pics significatifs uniquement
    total_amplitude_significant = sum([pips for _, _, pips in significant_peaks])
    dominance = impact_pips / total_amplitude_significant if total_amplitude_significant > 0 else 0
    
    # ALTERNATIVE : Vérifier si pic principal > 2x second pic
    if len(significant_peaks) >= 2:
        sorted_peaks = sorted(significant_peaks, key=lambda x: x[2], reverse=True)
        second_peak_impact = sorted_peaks[1][2]
        ratio_vs_second = impact_pips / second_peak_impact if second_peak_impact > 0 else 999
    else:
        ratio_vs_second = 999  # Un seul pic significatif
    
    # Critère dominance assoupli : > 60% OU > 2x second pic
    is_dominant = (dominance > 0.60) or (ratio_vs_second > 2.0)
    
    if not is_dominant:
        return {'is_single_wave': False}  # Pas assez dominant
    
    # Calculer pullback (creux après pic)
    troughs_after_peak = [t for t in troughs if t[0] > peak_time]
    
    pullback_ratio = 0.0
    if len(troughs_after_peak) > 0:
        # Trouver creux le plus profond
        deepest_trough = min(troughs_after_peak, key=lambda x: abs(x[1] - baseline))
        trough_price = deepest_trough[1]
        
        # Pullback ratio = (peak - trough) / (peak - baseline)
        pullback_amplitude = abs(peak_price - trough_price)
        total_amplitude_peak = abs(peak_price - baseline)
        
        if total_amplitude_peak > 0:
            pullback_ratio = pullback_amplitude / total_amplitude_peak
    
    # CORRECTION BUG #2 : Critères pullback assouplis
    single_wave_type = None
    if impact_pips >= 40 and pullback_ratio < 0.30:  # Fort : pullback < 30% (assoupli de 20%)
        single_wave_type = 'fort'
    elif 20 <= impact_pips < 40 and pullback_ratio < 0.40:  # Intermediate : pullback < 40% (assoupli de 30%)
        single_wave_type = 'intermediate'
    
    # Quality score (dominance + faible pullback)
    quality_score = dominance * (1 - pullback_ratio)
    
    return {
        'is_single_wave': single_wave_type is not None,
        'type': single_wave_type,
        'peak_time': peak_time,
        'peak_price': peak_price,
        'impact_pips': impact_pips,
        'pullback_ratio': pullback_ratio * 100,  # Pourcentage
        'dominance': dominance * 100,
        'quality_score': quality_score,
        'num_peaks': len(peaks),
        'num_significant_peaks': len(significant_peaks),
        'ratio_vs_second_peak': ratio_vs_second,
        'num_troughs': len(troughs)
    }


def scan_single_wave_cases(
    db_path: str,
    start_date: str = '2024-01-01',
    end_date: str = '2025-12-31',
    output_file: str = None
) -> list:
    """
    Scanner DB pour mouvements Single Wave
    
    ALGORITHME:
    1. Charger events HIGH importance période
    2. Pour chaque date:
       - Charger OHLC 1-min (event - 30min → event + 2h)
       - Calculer baseline = close(t-1)
       - Calculer ATR
       - Détecter extrema post-event (width=2, validé rev10)
       - Filtrer significatifs (seuil ATR adaptatif)
       - Compter peaks > seuil
       - Si 1 pic dominant → Single Wave candidat
       - Analyser pattern (Fort vs Intermediate)
    3. Filtrer candidates par type (Fort / Intermediate)
    4. Sauvegarder JSON
    
    Args:
        db_path: Chemin warehouse.duckdb
        start_date: Date début scan
        end_date: Date fin scan
        output_file: Fichier JSON sortie (optionnel)
    
    Returns:
        List[Dict] cas identifiés
    """
    print(f"\n{'='*80}")
    print(f"SCANNER SINGLE WAVE V2 - Session 121")
    print(f"{'='*80}\n")
    print(f"Période: {start_date} → {end_date}")
    print(f"Database: {db_path}")
    print(f"Output: {output_file if output_file else 'Aucun (affichage uniquement)'}\n")
    
    # Charger events HIGH
    print("Chargement événements HIGH importance...")
    df_events = load_high_events(db_path, start_date, end_date)
    print(f"  → {len(df_events)} événements trouvés\n")
    
    if len(df_events) == 0:
        print("Aucun événement HIGH trouvé dans la période.")
        return []
    
    # Timezone Bern
    tz_bern = pytz.timezone('Europe/Zurich')
    
    candidates = []
    fort_count = 0
    intermediate_count = 0
    
    print("Analyse événements...\n")
    
    for idx, event in df_events.iterrows():
        # ts_utc est déjà en UTC avec timezone
        event_dt_utc = pd.to_datetime(event['ts_utc'])
        # Convertir en timezone Bern pour travailler avec prices_bern
        event_dt = event_dt_utc.tz_convert(tz_bern)
        event_name = event['event_title']
        currency = event.get('country', 'UNKNOWN')
        
        # Fenêtre: event - 30min → event + 2h
        start_window = event_dt - timedelta(minutes=30)
        end_window = event_dt + timedelta(hours=2)
        
        # Charger OHLC 1-min
        try:
            df_ohlc = load_ohlc_1m_duckdb(
                db_path,
                'prices_bern',
                tz_bern,
                start_window,
                end_window
            )
        except Exception as e:
            print(f"  ⚠️  {event_dt.date()} {event_dt.time()} - Erreur chargement OHLC: {e}")
            continue
        
        if df_ohlc is None or len(df_ohlc) < 10:
            continue
        
        # Calculer ATR (atr1m retourne une Series)
        df_ohlc['ATR'] = atr1m(df_ohlc)
        
        if 'ATR' not in df_ohlc.columns or df_ohlc['ATR'].isna().all():
            continue
        
        atr_median = df_ohlc['ATR'].median()
        
        # Baseline
        baseline = calculate_baseline(df_ohlc, event_dt)
        if baseline is None:
            continue
        
        # Détecter extrema post-event
        extrema = find_local_extrema_adaptive(df_ohlc, event_dt, width=2)
        
        # Filtrer significatifs (seuil ATR)
        peaks_sig = filter_significant_extrema(extrema['peaks'], baseline, atr_median)
        troughs_sig = filter_significant_extrema(extrema['troughs'], baseline, atr_median)
        
        if len(peaks_sig) == 0:
            continue
        
        # Analyser pattern Single Wave
        analysis = analyze_single_wave_candidate(
            df_ohlc,
            event_dt,
            baseline,
            peaks_sig,
            troughs_sig
        )
        
        if analysis['is_single_wave']:
            pattern_type = analysis['type']
            
            candidate = {
                'date': event_dt.strftime('%Y-%m-%d'),
                'time': event_dt.strftime('%H:%M:%S'),
                'event_name': event_name,
                'currency': currency,
                'pattern_type': pattern_type,
                'impact_pips': round(analysis['impact_pips'], 1),
                'peak_time': analysis['peak_time'].strftime('%H:%M:%S'),
                'pullback_ratio': round(analysis['pullback_ratio'], 1),
                'dominance': round(analysis['dominance'], 1),
                'quality_score': round(analysis['quality_score'], 3),
                'num_peaks': analysis['num_peaks'],
                'atr_median': round(atr_median * 10000, 2)
            }
            
            candidates.append(candidate)
            
            if pattern_type == 'fort':
                fort_count += 1
                emoji = "🟢"
            else:
                intermediate_count += 1
                emoji = "🟡"
            
            print(f"{emoji} {candidate['date']} {candidate['time']} - {event_name[:40]:40s} | "
                  f"{pattern_type.upper():12s} | {candidate['impact_pips']:5.1f} pips | "
                  f"Pullback {candidate['pullback_ratio']:4.1f}% | "
                  f"Quality {candidate['quality_score']:.3f}")
    
    print(f"\n{'='*80}")
    print(f"RÉSULTATS SCAN")
    print(f"{'='*80}")
    print(f"Candidats Single Wave trouvés: {len(candidates)}")
    print(f"  - Single Fort (> 40 pips):        {fort_count}")
    print(f"  - Single Intermediate (20-40):    {intermediate_count}")
    print(f"\nObjectif Session 121:")
    print(f"  - Single Fort:        {'✅' if fort_count >= 3 else '❌'} {fort_count}/3+ requis")
    print(f"  - Single Intermediate: {'✅' if intermediate_count >= 2 else '❌'} {intermediate_count}/2+ requis")
    print(f"{'='*80}\n")
    
    # Sauvegarder JSON
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            'scan_date': datetime.now(tz_bern).isoformat(),
            'period': {'start': start_date, 'end': end_date},
            'summary': {
                'total_candidates': len(candidates),
                'fort_count': fort_count,
                'intermediate_count': intermediate_count
            },
            'candidates': candidates
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Résultats sauvegardés: {output_file}\n")
    
    return candidates


if __name__ == '__main__':
    # Configuration
    db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
    output_file = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121/single_wave_candidates.json'
    
    # Scanner 2024-2025
    candidates = scan_single_wave_cases(
        db_path=db_path,
        start_date='2024-01-01',
        end_date='2025-12-31',
        output_file=output_file
    )
    
    print("✅ Scanner terminé avec succès!")
