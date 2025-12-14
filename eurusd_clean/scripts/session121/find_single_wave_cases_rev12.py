#!/usr/bin/env python3
"""
Scanner Single Wave V2 - APPROCHE SÉQUENTIELLE REV12

MÉTHODOLOGIE CRITIQUE (Session 121) :
=====================================
Ce scanner utilise la MÊME logique mathématique que Rev12 (validé MAE 4.5 pips).

POURQUOI CETTE APPROCHE ?
- Rev12 validé empiriquement (convergence Session 118)
- Approche séquentielle PURE (pas de fenêtres temporelles fixes)
- Suit mouvement progressif du marché (pas d'analyse globale post-facto)
- Cohérence méthodologique tout le projet

LOGIQUE SÉQUENTIELLE :
1. Détecter Wave1 : Peak progressif + Pullback (MIN_BARS=3)
2. Chercher Wave2 : Nouveau peak > Wave1 (MAX_IDLE=20 bars)
3. Classification :
   - Pas de Wave2 significative → Single Wave ✅
   - Wave2 existe → Double Wave (rejeté ici)

DIFFÉRENCE vs APPROCHE PRÉCÉDENTE :
- AVANT : Fenêtre 2h fixe → détecter TOUS peaks → calculer dominance
- MAINTENANT : Séquentiel → suivre mouvement réel → arrêt naturel
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import json

# Imports fonctions utilitaires rev10 (mathématiques pures)
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
    event_time: pd.Timestamp,
    baseline: float,
    max_idle_bars: int = 20,
    min_bars_before_pullback: int = 3
) -> dict:
    """
    Détection Single Wave avec approche séquentielle Rev12
    
    ALGORITHME (identique Rev12 Wave1) :
    1. Wave1 : Chercher peak progressif + pullback significatif
       - Peak monte progressivement
       - Garde temporelle MIN_BARS_BEFORE_PULLBACK = 3
       - Pullback validé avec seuils ATR adaptatifs
    
    2. Wave2 : Chercher nouveau peak significatif
       - Peak > 1.2x Wave1 OU break Wave1 + 1 pip
       - Si trouve → Double Wave (rejeter pour Single)
       - Si idle MAX_IDLE_BARS → pas de Wave2 → Single Wave ✅
    
    3. Classification Single Wave :
       - Fort : impact > 40 pips, pullback < 30%
       - Intermediate : impact 20-40 pips, pullback < 40%
    
    Args:
        df_ohlc: DataFrame OHLC 1-min avec ATR
        event_time: Timestamp event
        baseline: Prix baseline
        max_idle_bars: Bars max sans nouveau peak avant arrêt
        min_bars_before_pullback: Garde temporelle pullback
    
    Returns:
        Dict pattern détecté ou None
    """
    # Slice après event (horizon 90 min comme Rev12)
    end_time = event_time + timedelta(minutes=90)
    df_after = df_ohlc[(df_ohlc.index >= event_time) & (df_ohlc.index <= end_time)].copy()
    
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
    peak1_time = event_time
    pullback1_price = None
    pullback1_time = None
    
    idle = 0
    for i in range(len(df_after)):
        ts = times[i]
        atr_i = df_after['ATR'].iloc[i]
        
        if direction == 'bullish':
            # Chercher peak progressif
            if highs[i] > peak1_price:
                peak1_price = highs[i]
                peak1_time = ts
                idle = 0
            else:
                idle += 1
            
            # Chercher pullback (GARDE TEMPORELLE)
            minutes_since_peak = (ts - peak1_time).total_seconds() / 60.0
            if minutes_since_peak >= min_bars_before_pullback:
                amp = peak1_price - baseline
                if amp > 0:
                    dd = (peak1_price - lows[i]) / amp
                    dd_filter = (peak1_price - lows[i]) >= atr_k * atr_i
                    
                    # Validation pullback (extremum local)
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
            # Pas de pullback dans le délai, MAIS si mouvement significatif → capturer
            wave1_impact = to_pips(abs(peak1_price - baseline))
            if wave1_impact >= 40:  # Mouvement significatif
                return {
                    'pattern_type': 'unclassified_extended',
                    'type': 'extended',  # Provisoire
                    'direction': direction,
                    'peak_time': peak1_time,
                    'peak_price': peak1_price,
                    'pullback_price': None,
                    'baseline': baseline,
                    'impact_pips': round(wave1_impact, 1),
                    'pullback_ratio': 0.0,  # Pas de pullback détecté
                    'methodology': 'sequential_rev12_extended',
                    'note': 'Mouvement continu sans pullback significatif'
                }
            return None  # Mouvement trop petit
    
    if pullback1_time is None:
        return None  # Pas de pullback Wave1
    
    # Calcul Wave1
    wave1_impact = to_pips(abs(peak1_price - baseline))
    pullback1_ratio = abs(peak1_price - pullback1_price) / abs(peak1_price - baseline)
    
    # ====================
    # PHASE 2 : CHERCHER WAVE 2
    # ====================
    start_i = df_after.index.get_loc(pullback1_time) + 1
    if start_i >= len(df_after):
        # Pas assez de données après pullback1 → Single Wave
        return classify_single_wave(
            peak1_time, peak1_price, pullback1_price, 
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
                
                # Vérifier si Wave2 significative (> 1.2x Wave1 OU break + 1 pip)
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
            break  # Pas de Wave2 significative
    
    # ====================
    # CLASSIFICATION
    # ====================
    if has_significant_wave2:
        return None  # C'est un Double Wave, pas Single Wave
    
    # Single Wave confirmé ✅
    return classify_single_wave(
        peak1_time, peak1_price, pullback1_price,
        baseline, wave1_impact, pullback1_ratio, direction
    )


def classify_single_wave(
    peak_time, peak_price, pullback_price,
    baseline, impact_pips, pullback_ratio, direction
) -> dict:
    """
    Classifier Single Wave selon impact + pullback
    
    CRITÈRES (assouplis Session 121) :
    - Fort : impact >= 40 pips, pullback < 30%
    - Intermediate : impact 20-40 pips, pullback < 40%
    """
    single_wave_type = None
    
    if impact_pips >= 40 and pullback_ratio < 0.30:
        single_wave_type = 'fort'
    elif 20 <= impact_pips < 40 and pullback_ratio < 0.40:
        single_wave_type = 'intermediate'
    
    if single_wave_type is None:
        return None  # Ne correspond pas aux critères
    
    return {
        'pattern_type': f'single_wave_{single_wave_type}',
        'type': single_wave_type,
        'direction': direction,
        'peak_time': peak_time,
        'peak_price': peak_price,
        'pullback_price': pullback_price,
        'baseline': baseline,
        'impact_pips': round(impact_pips, 1),
        'pullback_ratio': round(pullback_ratio * 100, 1),
        'methodology': 'sequential_rev12'
    }


def load_high_events(db_path: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Charge événements HIGH importance période donnée
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


def scan_single_wave_cases(
    db_path: str,
    start_date: str = '2024-01-01',
    end_date: str = '2025-12-31',
    output_file: str = None
) -> list:
    """
    Scanner DB avec approche séquentielle Rev12
    """
    print(f"\n{'='*80}")
    print(f"SCANNER SINGLE WAVE V2 - APPROCHE SÉQUENTIELLE REV12")
    print(f"{'='*80}\n")
    print(f"Période: {start_date} → {end_date}")
    print(f"Méthodologie: Séquentielle (validée Rev12 MAE 4.5 pips)")
    print(f"Database: {db_path}")
    print(f"Output: {output_file if output_file else 'Aucun (affichage uniquement)'}\n")
    
    # Charger events HIGH
    print("Chargement événements HIGH importance...")
    df_events = load_high_events(db_path, start_date, end_date)
    print(f"  → {len(df_events)} événements trouvés\n")
    
    if len(df_events) == 0:
        print("Aucun événement HIGH trouvé dans la période.")
        return []
    
    tz_bern = pytz.timezone('Europe/Zurich')
    
    candidates = []
    fort_count = 0
    intermediate_count = 0
    extended_count = 0
    
    print("Analyse événements (approche séquentielle)...\n")
    
    for idx, event in df_events.iterrows():
        event_dt_utc = pd.to_datetime(event['ts_utc'])
        event_dt = event_dt_utc.tz_convert(tz_bern)
        event_name = event['event_title'] if event['event_title'] is not None else 'Unknown Event'
        currency = event.get('country', 'UNKNOWN')
        
        # Fenêtre: event - 30min → event + 2h (chargement données)
        start_window = event_dt - timedelta(minutes=30)
        end_window = event_dt + timedelta(hours=2)
        
        # Charger OHLC 1-min
        try:
            df_ohlc = load_ohlc_1m_duckdb(db_path, 'prices_bern', tz_bern, start_window, end_window)
        except Exception as e:
            continue
        
        if df_ohlc is None or len(df_ohlc) < 10:
            continue
        
        # Calculer ATR
        df_ohlc['ATR'] = atr1m(df_ohlc)
        
        if 'ATR' not in df_ohlc.columns or df_ohlc['ATR'].isna().all():
            continue
        
        # Baseline
        before_event = df_ohlc[df_ohlc.index < event_dt]
        if len(before_event) == 0:
            continue
        baseline = before_event['close'].iloc[-1]
        
        # DÉTECTION SÉQUENTIELLE
        detection = detect_single_wave_sequential(df_ohlc, event_dt, baseline)
        
        if detection is not None:
            pattern_type = detection['type']
            
            candidate = {
                'date': event_dt.strftime('%Y-%m-%d'),
                'time': event_dt.strftime('%H:%M:%S'),
                'event_name': event_name,
                'country': currency,
                'pattern_type': pattern_type,
                'impact_pips': detection['impact_pips'],
                'peak_time': detection['peak_time'].strftime('%H:%M:%S'),
                'pullback_ratio': detection['pullback_ratio'],
                'direction': detection['direction'],
                'methodology': 'sequential_rev12'
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
                emoji = "🔵"  # Bleu pour "non classifié"
            
            pullback_str = f"Pullback {candidate['pullback_ratio']:4.1f}%" if candidate.get('pullback_ratio', 0) > 0 else "No pullback"
            print(f"{emoji} {candidate['date']} {candidate['time']} - {event_name[:40]:40s} | "
                  f"{pattern_type.upper():12s} | {candidate['impact_pips']:5.1f} pips | "
                  f"{pullback_str}")
    
    print(f"\n{'='*80}")
    print(f"RÉSULTATS SCAN (APPROCHE SÉQUENTIELLE REV12)")
    print(f"{'='*80}")
    print(f"Candidats trouvés: {len(candidates)}")
    print(f"  - Single Fort (> 40 pips):        {fort_count}")
    print(f"  - Single Intermediate (20-40):    {intermediate_count}")
    print(f"  - Extended (mouvement continu):   {extended_count}")
    print(f"\nObjectif Session 121:")
    print(f"  - Single Fort:        {'✅' if fort_count >= 3 else '❌'} {fort_count}/3+ requis")
    print(f"  - Single Intermediate: {'✅' if intermediate_count >= 2 else '❌'} {intermediate_count}/2+ requis")
    print(f"  - Extended:            🔍 {extended_count} à classifier après analyse")
    print(f"{'='*80}\n")
    
    # Sauvegarder JSON
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            'scan_date': datetime.now(tz_bern).isoformat(),
            'methodology': 'sequential_rev12',
            'period': {'start': start_date, 'end': end_date},
            'summary': {
                'total_candidates': len(candidates),
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
    output_file = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121/single_wave_candidates_rev12.json'
    
    candidates = scan_single_wave_cases(
        db_path=db_path,
        start_date='2024-01-01',
        end_date='2025-12-31',
        output_file=output_file
    )
    
    print("✅ Scanner terminé avec succès!")
