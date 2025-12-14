#!/usr/bin/env python3
"""
Scanner Single Wave V3 - APPROCHE MATHÉMATIQUE PURE

MÉTHODOLOGIE CRITIQUE (Session 121 - Correction majeure) :
===========================================================
APPROCHE CORRECTE : PRIX → PATTERNS → ÉVÉNEMENTS

1. SCANNER PRIX (approche mathématique pure)
   - Parcourir timeline chronologiquement
   - Détecter spikes significatifs (> 30 pips en 1-2 bars)
   - Lancer détection séquentielle Rev12

2. CLASSIFIER PATTERNS
   - Single Wave Fort/Intermediate
   - Single Wave Extended
   - Double Wave (rejeté ici)

3. ASSOCIER ÉVÉNEMENTS (après détection)
   - Chercher événements HIGH dans fenêtre ±15 min
   - Constituer CLUSTER d'événements causaux

DIFFÉRENCE FONDAMENTALE vs V2 :
- V2 : Parcourait ÉVÉNEMENTS → détectait mouvements (FAUX - doublons)
- V3 : Parcourt PRIX → détecte mouvements → associe événements (CORRECT)

Cette approche garantit :
- 1 mouvement réel = 1 détection unique
- Clusters multi-événements correctement associés
- Cohérence avec stratégie bottom-up empirique
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


def detect_single_wave_sequential(
    df_ohlc: pd.DataFrame,
    spike_time: pd.Timestamp,
    baseline: float,
    max_idle_bars: int = 20,
    min_bars_before_pullback: int = 3
) -> dict:
    """
    Détection Single Wave avec approche séquentielle Rev12
    (Identique à V2, mais appelé depuis détection spike)
    """
    # Slice après spike (horizon 90 min comme Rev12)
    end_time = spike_time + timedelta(minutes=90)
    df_after = df_ohlc[(df_ohlc.index >= spike_time) & (df_ohlc.index <= end_time)].copy()
    
    if len(df_after) < 10:
        return None
    
    # Vérifier ATR existe
    if 'ATR' not in df_after.columns:
        return None
    
    # Statistiques ATR (seuils adaptatifs)
    day_atr_median = df_after['ATR'].median()
    atr0 = df_after['ATR'].iloc[0]
    
    # Seuils adaptatifs (même formule Rev12)
    atr_k = max(0.40, min(0.60, 0.5 * (day_atr_median / max(1e-12, atr0))))
    min_w1_pullback = 0.25 + 0.05 * (atr0 / max(1e-12, day_atr_median))
    
    # Direction (probe initial comme Rev12)
    direction = 'bullish' if (df_after['high'].iloc[:6].max() - baseline) >= (baseline - df_after['low'].iloc[:6].min()) else 'bearish'
    
    highs = df_after['high'].values
    lows = df_after['low'].values
    times = df_after.index
    
    # ====================
    # PHASE 1 : WAVE 1
    # ====================
    peak1_price = baseline
    peak1_time = spike_time
    pullback1_price = None
    pullback1_time = None
    
    idle = 0
    for i in range(len(df_after)):
        ts = times[i]
        atr_i = df_after['ATR'].iloc[i]
        
        if direction == 'bullish':
            if highs[i] > peak1_price:
                peak1_price = highs[i]
                peak1_time = ts
                idle = 0
            else:
                idle += 1
            
            minutes_since_peak = (ts - peak1_time).total_seconds() / 60.0
            if minutes_since_peak >= min_bars_before_pullback:
                amp = peak1_price - baseline
                if amp > 0:
                    dd = (peak1_price - lows[i]) / amp
                    dd_filter = (peak1_price - lows[i]) >= atr_k * atr_i
                    
                    if dd >= min_w1_pullback and dd_filter and i >= 2 and i < len(df_after) - 2:
                        if is_local_trough(pd.Series(lows), i, width=2):
                            pullback1_price = lows[i]
                            pullback1_time = ts
                            break
        else:  # bearish
            if lows[i] < peak1_price:
                peak1_price = lows[i]
                peak1_time = ts
                idle = 0
            else:
                idle += 1
            
            minutes_since_peak = (ts - peak1_time).total_seconds() / 60.0
            if minutes_since_peak >= min_bars_before_pullback:
                amp = baseline - peak1_price
                if amp > 0:
                    dd = (highs[i] - peak1_price) / amp
                    dd_filter = (highs[i] - peak1_price) >= atr_k * atr_i
                    
                    if dd >= min_w1_pullback and dd_filter and i >= 2 and i < len(df_after) - 2:
                        if is_local_peak(pd.Series(highs), i, width=2):
                            pullback1_price = highs[i]
                            pullback1_time = ts
                            break
        
        if idle >= max_idle_bars:
            # Pas de pullback, mais mouvement significatif → Extended
            wave1_impact = to_pips(abs(peak1_price - baseline))
            if wave1_impact >= 40:
                return {
                    'pattern_type': 'extended',
                    'direction': direction,
                    'spike_time': spike_time,
                    'peak_time': peak1_time,
                    'peak_price': peak1_price,
                    'pullback_price': None,
                    'baseline': baseline,
                    'impact_pips': round(wave1_impact, 1),
                    'pullback_ratio': 0.0,
                    'methodology': 'sequential_rev12_extended'
                }
            return None
    
    if pullback1_time is None:
        return None
    
    # Calcul Wave1
    wave1_impact = to_pips(abs(peak1_price - baseline))
    pullback1_ratio = abs(peak1_price - pullback1_price) / abs(peak1_price - baseline)
    
    # ====================
    # PHASE 2 : CHERCHER WAVE 2
    # ====================
    start_i = df_after.index.get_loc(pullback1_time) + 1
    if start_i >= len(df_after):
        return classify_single_wave(
            spike_time, peak1_time, peak1_price, pullback1_price, 
            baseline, wave1_impact, pullback1_ratio, direction
        )
    
    peak2_price = peak1_price
    peak2_time = peak1_time
    has_significant_wave2 = False
    idle = 0
    
    for i in range(start_i, len(df_after)):
        ts = times[i]
        
        if direction == 'bullish':
            if highs[i] > peak2_price:
                peak2_price = highs[i]
                peak2_time = ts
                idle = 0
                
                wave2_vs_baseline = to_pips(peak2_price - baseline)
                break_condition = to_pips(peak2_price - peak1_price) >= 1.0
                extension_condition = wave2_vs_baseline >= 1.2 * wave1_impact
                
                if break_condition or extension_condition:
                    has_significant_wave2 = True
                    break
            else:
                idle += 1
        else:  # bearish
            if lows[i] < peak2_price:
                peak2_price = lows[i]
                peak2_time = ts
                idle = 0
                
                wave2_vs_baseline = to_pips(baseline - peak2_price)
                break_condition = to_pips(peak1_price - peak2_price) >= 1.0
                extension_condition = wave2_vs_baseline >= 1.2 * wave1_impact
                
                if break_condition or extension_condition:
                    has_significant_wave2 = True
                    break
            else:
                idle += 1
        
        if idle >= max_idle_bars:
            break
    
    if has_significant_wave2:
        return None  # Double Wave
    
    return classify_single_wave(
        spike_time, peak1_time, peak1_price, pullback1_price,
        baseline, wave1_impact, pullback1_ratio, direction
    )


def classify_single_wave(
    spike_time, peak_time, peak_price, pullback_price,
    baseline, impact_pips, pullback_ratio, direction
) -> dict:
    """Classifier Single Wave selon impact + pullback"""
    single_wave_type = None
    
    if impact_pips >= 40 and pullback_ratio < 0.30:
        single_wave_type = 'fort'
    elif 20 <= impact_pips < 40 and pullback_ratio < 0.40:
        single_wave_type = 'intermediate'
    
    if single_wave_type is None:
        return None
    
    return {
        'pattern_type': single_wave_type,
        'direction': direction,
        'spike_time': spike_time,
        'peak_time': peak_time,
        'peak_price': peak_price,
        'pullback_price': pullback_price,
        'baseline': baseline,
        'impact_pips': round(impact_pips, 1),
        'pullback_ratio': round(pullback_ratio * 100, 1),
        'methodology': 'sequential_rev12'
    }


def find_events_in_window(
    db_path: str,
    spike_time: pd.Timestamp,
    window_minutes: int = 15
) -> list:
    """
    Chercher événements HIGH dans fenêtre ±window_minutes autour du spike
    Retourne liste événements formant le CLUSTER causal
    """
    tz_bern = pytz.timezone('Europe/Zurich')
    
    start_window = spike_time - timedelta(minutes=window_minutes)
    end_window = spike_time + timedelta(minutes=window_minutes)
    
    # Convertir en UTC pour requête DB
    start_utc = start_window.astimezone(pytz.utc)
    end_utc = end_window.astimezone(pytz.utc)
    
    conn = duckdb.connect(db_path, read_only=True)
    
    query = """
    SELECT 
        ts_utc,
        country,
        event_title,
        actual,
        estimate,
        forecast
    FROM events
    WHERE importance_n = 3
      AND ts_utc >= ?
      AND ts_utc <= ?
    ORDER BY ts_utc
    """
    
    df = conn.execute(query, [start_utc.isoformat(), end_utc.isoformat()]).df()
    conn.close()
    
    events = []
    for _, row in df.iterrows():
        event_time_utc = pd.to_datetime(row['ts_utc'])
        event_time_bern = event_time_utc.tz_convert(tz_bern)
        
        events.append({
            'time': event_time_bern.strftime('%H:%M:%S'),
            'country': row['country'] if row['country'] else 'Unknown',
            'title': row['event_title'] if row['event_title'] else 'Unknown Event',
            'actual': row['actual'],
            'estimate': row['estimate'],
            'forecast': row['forecast']
        })
    
    return events


def scan_price_movements(
    db_path: str,
    start_date: str = '2024-01-01',
    end_date: str = '2025-12-31',
    spike_threshold_pips: float = 30.0,
    output_file: str = None
) -> list:
    """
    Scanner V3 - APPROCHE MATHÉMATIQUE PURE
    
    1. Parcourir prix chronologiquement
    2. Détecter spikes (> spike_threshold_pips en 1-2 bars)
    3. Lancer détection séquentielle Rev12
    4. Associer événements du cluster
    """
    print(f"\n{'='*80}")
    print(f"SCANNER SINGLE WAVE V3 - APPROCHE MATHÉMATIQUE PURE")
    print(f"{'='*80}\n")
    print(f"Période: {start_date} → {end_date}")
    print(f"Méthodologie: Prix → Patterns → Événements")
    print(f"Seuil spike: {spike_threshold_pips} pips")
    print(f"Database: {db_path}")
    print(f"Output: {output_file if output_file else 'Aucun'}\n")
    
    tz_bern = pytz.timezone('Europe/Zurich')
    
    # Charger TOUTES les données prix période
    print("Chargement données prix...")
    start_dt = pd.to_datetime(start_date).tz_localize(tz_bern)
    end_dt = pd.to_datetime(end_date).tz_localize(tz_bern)
    
    df_ohlc = load_ohlc_1m_duckdb(db_path, 'prices_bern', tz_bern, start_dt, end_dt)
    print(f"✅ {len(df_ohlc)} bars chargées\n")
    
    # Calculer ATR
    print("Calcul ATR...")
    df_ohlc['ATR'] = atr1m(df_ohlc)
    print(f"✅ ATR calculé\n")
    
    # Détecter spikes significatifs
    print(f"Détection spikes (> {spike_threshold_pips} pips)...")
    spike_threshold = spike_threshold_pips / 10000
    
    spikes = []
    for i in range(1, len(df_ohlc)):
        prev_close = df_ohlc['close'].iloc[i-1]
        curr_high = df_ohlc['high'].iloc[i]
        curr_low = df_ohlc['low'].iloc[i]
        
        # Spike haussier
        if (curr_high - prev_close) >= spike_threshold:
            spikes.append({
                'time': df_ohlc.index[i],
                'direction': 'bullish',
                'amplitude': to_pips(curr_high - prev_close),
                'baseline': prev_close
            })
        
        # Spike baissier
        if (prev_close - curr_low) >= spike_threshold:
            spikes.append({
                'time': df_ohlc.index[i],
                'direction': 'bearish',
                'amplitude': to_pips(prev_close - curr_low),
                'baseline': prev_close
            })
    
    print(f"✅ {len(spikes)} spikes détectés\n")
    
    # Analyser chaque spike
    print("Analyse patterns séquentiels (Rev12)...\n")
    
    candidates = []
    fort_count = 0
    intermediate_count = 0
    extended_count = 0
    
    for spike in spikes:
        spike_time = spike['time']
        baseline = spike['baseline']
        
        # Fenêtre analyse : spike - 30min → spike + 2h
        start_window = spike_time - timedelta(minutes=30)
        end_window = spike_time + timedelta(hours=2)
        
        df_window = df_ohlc[(df_ohlc.index >= start_window) & (df_ohlc.index <= end_window)].copy()
        
        if len(df_window) < 10:
            continue
        
        # Détection séquentielle
        detection = detect_single_wave_sequential(df_window, spike_time, baseline)
        
        if detection is not None:
            pattern_type = detection['pattern_type']
            
            # Chercher événements cluster
            events_cluster = find_events_in_window(db_path, spike_time, window_minutes=15)
            
            candidate = {
                'date': spike_time.strftime('%Y-%m-%d'),
                'time': spike_time.strftime('%H:%M:%S'),
                'pattern_type': pattern_type,
                'impact_pips': detection['impact_pips'],
                'peak_time': detection['peak_time'].strftime('%H:%M:%S'),
                'pullback_ratio': detection['pullback_ratio'],
                'direction': detection['direction'],
                'events_cluster': events_cluster,
                'num_events': len(events_cluster),
                'methodology': 'price_first_v3'
            }
            
            candidates.append(candidate)
            
            if pattern_type == 'fort':
                fort_count += 1
                emoji = "🟢"
            elif pattern_type == 'intermediate':
                intermediate_count += 1
                emoji = "🟡"
            else:  # extended
                extended_count += 1
                emoji = "🔵"
            
            pullback_str = f"Pullback {candidate['pullback_ratio']:4.1f}%" if candidate['pullback_ratio'] > 0 else "No pullback"
            events_str = f"{len(events_cluster)} event(s)" if len(events_cluster) > 0 else "No events"
            
            print(f"{emoji} {candidate['date']} {candidate['time']} | "
                  f"{pattern_type.upper():12s} | {candidate['impact_pips']:5.1f} pips | "
                  f"{pullback_str:18s} | {events_str}")
    
    print(f"\n{'='*80}")
    print(f"RÉSULTATS SCAN (APPROCHE MATHÉMATIQUE V3)")
    print(f"{'='*80}")
    print(f"Mouvements détectés: {len(candidates)}")
    print(f"  - Single Fort:        {fort_count}")
    print(f"  - Single Intermediate: {intermediate_count}")
    print(f"  - Extended:           {extended_count}")
    print(f"\nObjectif Session 121:")
    print(f"  - Single Fort:        {'✅' if fort_count >= 3 else '❌'} {fort_count}/3+ requis")
    print(f"  - Single Intermediate: {'✅' if intermediate_count >= 2 else '❌'} {intermediate_count}/2+ requis")
    print(f"  - Extended:            🔍 {extended_count} à classifier")
    print(f"{'='*80}\n")
    
    # Sauvegarder
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            'scan_date': datetime.now(tz_bern).isoformat(),
            'methodology': 'price_first_sequential_v3',
            'spike_threshold_pips': spike_threshold_pips,
            'period': {'start': start_date, 'end': end_date},
            'summary': {
                'total_movements': len(candidates),
                'fort_count': fort_count,
                'intermediate_count': intermediate_count,
                'extended_count': extended_count
            },
            'candidates': candidates
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Résultats sauvegardés: {output_file}\n")
    
    return candidates


if __name__ == '__main__':
    db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
    output_file = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121/single_wave_candidates_v3.json'
    
    candidates = scan_price_movements(
        db_path=db_path,
        start_date='2024-01-01',
        end_date='2025-12-31',
        spike_threshold_pips=30.0,
        output_file=output_file
    )
    
    print("✅ Scanner V3 terminé avec succès!")
