#!/usr/bin/env python3
"""
Script de diagnostic pour comprendre pourquoi le scanner ne trouve rien

Analyse sur quelques événements connus pour voir ce qui est détecté
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

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

db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
tz_bern = pytz.timezone('Europe/Zurich')

# Tester sur cas connus
test_cases = [
    {'date': '2025-09-11', 'time': '14:30:00', 'name': 'US CPI (cas référence)'},
    {'date': '2025-08-01', 'time': '14:30:00', 'name': 'US NFP'},
    {'date': '2025-07-01', 'time': '14:30:00', 'name': 'US NFP'},
    {'date': '2024-06-12', 'time': '14:30:00', 'name': 'US CPI (référence S117)'},
]

print("="*80)
print("DIAGNOSTIC SCANNER SINGLE WAVE")
print("="*80)

for test_case in test_cases:
    date_str = test_case['date']
    time_str = test_case['time']
    name = test_case['name']
    
    print(f"\n{'='*80}")
    print(f"CAS TEST: {date_str} {time_str} - {name}")
    print(f"{'='*80}\n")
    
    event_dt = pd.to_datetime(f"{date_str} {time_str}").tz_localize(tz_bern)
    
    # Fenêtre
    start_window = event_dt - timedelta(minutes=30)
    end_window = event_dt + timedelta(hours=2)
    
    # Charger OHLC
    try:
        df_ohlc = load_ohlc_1m_duckdb(db_path, 'prices_bern', tz_bern, start_window, end_window)
    except Exception as e:
        print(f"❌ Erreur chargement OHLC: {e}")
        continue
    
    if df_ohlc is None or len(df_ohlc) < 10:
        print(f"❌ Données OHLC insuffisantes: {len(df_ohlc) if df_ohlc is not None else 0} bars")
        continue
    
    print(f"✅ OHLC chargé: {len(df_ohlc)} bars")
    
    # Calculer ATR
    df_ohlc['ATR'] = atr1m(df_ohlc)
    atr_median = df_ohlc['ATR'].median()
    print(f"   ATR médian: {atr_median*10000:.2f} pips")
    
    # Baseline
    before_event = df_ohlc[df_ohlc.index < event_dt]
    if len(before_event) == 0:
        print(f"❌ Pas de données avant event")
        continue
    
    baseline = before_event['close'].iloc[-1]
    print(f"   Baseline: {baseline:.5f} @ {before_event.index[-1].strftime('%H:%M:%S')}")
    
    # Extrema post-event
    df_after = df_ohlc[df_ohlc.index > event_dt].copy()
    print(f"   Bars après event: {len(df_after)}")
    
    if len(df_after) < 5:
        print(f"❌ Pas assez de données après event")
        continue
    
    # Détecter extrema bruts (sans filtre ATR)
    peaks_brut = []
    troughs_brut = []
    
    highs = df_after['high'].values
    lows = df_after['low'].values
    times = df_after.index
    
    width = 2
    for i in range(width, len(df_after) - width):
        if is_local_peak(pd.Series(highs), i, width):
            peak_price = highs[i]
            impact_pips = to_pips(abs(peak_price - baseline))
            peaks_brut.append((times[i], peak_price, impact_pips))
        
        if is_local_trough(pd.Series(lows), i, width):
            trough_price = lows[i]
            impact_pips = to_pips(abs(trough_price - baseline))
            troughs_brut.append((times[i], trough_price, impact_pips))
    
    print(f"\n   EXTREMA BRUTS (sans filtre ATR):")
    print(f"   Peaks détectés: {len(peaks_brut)}")
    if len(peaks_brut) > 0:
        for i, (t, p, pips) in enumerate(peaks_brut[:5]):  # Top 5
            print(f"      Peak {i+1}: {t.strftime('%H:%M:%S')} - {pips:.1f} pips")
    
    print(f"   Troughs détectés: {len(troughs_brut)}")
    if len(troughs_brut) > 0:
        for i, (t, p, pips) in enumerate(troughs_brut[:5]):  # Top 5
            print(f"      Trough {i+1}: {t.strftime('%H:%M:%S')} - {pips:.1f} pips")
    
    # Filtrer avec seuil ATR
    min_variation = max(atr_median * 0.5, 5.0 / 10000)
    print(f"\n   SEUIL ATR: {to_pips(min_variation):.2f} pips")
    
    peaks_filtered = [(t, p, pips) for t, p, pips in peaks_brut if abs(p - baseline) >= min_variation]
    troughs_filtered = [(t, p, pips) for t, p, pips in troughs_brut if abs(p - baseline) >= min_variation]
    
    print(f"\n   EXTREMA FILTRÉS (avec seuil ATR):")
    print(f"   Peaks significatifs: {len(peaks_filtered)}")
    if len(peaks_filtered) > 0:
        for i, (t, p, pips) in enumerate(peaks_filtered[:5]):
            print(f"      Peak {i+1}: {t.strftime('%H:%M:%S')} - {pips:.1f} pips")
    
    print(f"   Troughs significatifs: {len(troughs_filtered)}")
    
    # Analyser domination peak
    if len(peaks_filtered) > 0:
        max_peak = max(peaks_filtered, key=lambda x: x[2])
        total_amplitude = sum([pips for _, _, pips in peaks_filtered])
        dominance = (max_peak[2] / total_amplitude * 100) if total_amplitude > 0 else 0
        
        print(f"\n   DOMINANCE PEAK:")
        print(f"   Peak max: {max_peak[2]:.1f} pips @ {max_peak[0].strftime('%H:%M:%S')}")
        print(f"   Total amplitude: {total_amplitude:.1f} pips")
        print(f"   Dominance: {dominance:.1f}%")
        
        # Critère Single Wave : dominance > 50%
        if dominance > 50:
            print(f"   ✅ CRITÈRE DOMINANCE: OK ({dominance:.1f}% > 50%)")
            
            # Analyser pullback
            troughs_after_peak = [t for t in troughs_filtered if t[0] > max_peak[0]]
            if len(troughs_after_peak) > 0:
                deepest_trough = min(troughs_after_peak, key=lambda x: abs(x[1] - baseline))
                pullback_amp = abs(max_peak[1] - deepest_trough[1])
                total_amp = abs(max_peak[1] - baseline)
                pullback_ratio = (pullback_amp / total_amp * 100) if total_amp > 0 else 0
                
                print(f"\n   PULLBACK:")
                print(f"   Trough après peak: {deepest_trough[2]:.1f} pips @ {deepest_trough[0].strftime('%H:%M:%S')}")
                print(f"   Pullback ratio: {pullback_ratio:.1f}%")
                
                # Classification
                if max_peak[2] >= 40 and pullback_ratio < 20:
                    print(f"   ✅ SINGLE WAVE FORT (impact {max_peak[2]:.1f} pips, pullback {pullback_ratio:.1f}%)")
                elif 20 <= max_peak[2] < 40 and pullback_ratio < 30:
                    print(f"   ✅ SINGLE WAVE INTERMEDIATE (impact {max_peak[2]:.1f} pips, pullback {pullback_ratio:.1f}%)")
                else:
                    print(f"   ❌ NE CORRESPOND PAS AUX CRITÈRES SINGLE WAVE")
                    print(f"      Raison: impact {max_peak[2]:.1f} pips, pullback {pullback_ratio:.1f}%")
            else:
                print(f"   ⚠️  Pas de trough après peak (pas de pullback détecté)")
        else:
            print(f"   ❌ CRITÈRE DOMINANCE: NON ({dominance:.1f}% < 50%)")
            print(f"      Pattern multi-peaks (Double Wave ou ZigZag probable)")
    else:
        print(f"\n   ❌ Aucun peak significatif détecté après filtrage ATR")

print(f"\n{'='*80}")
print("DIAGNOSTIC TERMINÉ")
print("="*80)
