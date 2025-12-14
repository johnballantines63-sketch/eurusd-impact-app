#!/usr/bin/env python3
"""
Debug détaillé scanner Rev12 sur 1er août 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import timedelta
import pytz

session119_dir = Path(__file__).parent.parent / 'session119'
sys.path.insert(0, str(session119_dir))

from double_wave_detector_rev10 import (
    load_ohlc_1m_duckdb, atr1m, to_pips, 
    is_local_peak, is_local_trough
)

db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
tz_bern = pytz.timezone('Europe/Zurich')

event_dt = pd.to_datetime('2025-08-01 14:30:00').tz_localize(tz_bern)

print("="*80)
print("DEBUG DÉTAILLÉ - APPROCHE SÉQUENTIELLE REV12")
print("="*80 + "\n")

# Charger OHLC
start_window = event_dt - timedelta(minutes=30)
end_window = event_dt + timedelta(hours=2)

df_ohlc = load_ohlc_1m_duckdb(db_path, 'prices_bern', tz_bern, start_window, end_window)
df_ohlc['ATR'] = atr1m(df_ohlc)

baseline = df_ohlc[df_ohlc.index < event_dt]['close'].iloc[-1]
print(f"Event time: {event_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"Baseline: {baseline:.5f} @ {df_ohlc[df_ohlc.index < event_dt].index[-1].strftime('%H:%M:%S')}\n")

# Afficher prix autour de l'event pour vérifier timezone
print("PRIX AUTOUR DE L'EVENT (vérification timezone):")
print("="*80)
event_window = df_ohlc[(df_ohlc.index >= event_dt - timedelta(minutes=5)) & 
                        (df_ohlc.index <= event_dt + timedelta(minutes=30))]
for idx, row in event_window.iterrows():
    marker = " ◀─ EVENT" if idx == event_dt else ""
    impact_from_baseline = to_pips(row['high'] - baseline)
    print(f"{idx.strftime('%H:%M:%S')} | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f} | "
          f"Impact: {impact_from_baseline:6.1f} pips{marker}")
print("="*80 + "\n")

# Slice après event (90 min)
end_time = event_dt + timedelta(minutes=90)
df_after = df_ohlc[(df_ohlc.index >= event_dt) & (df_ohlc.index <= end_time)].copy()
print(f"Bars après event (90 min): {len(df_after)}\n")

# Seuils adaptatifs
day_atr_median = df_after['ATR'].median()
atr0 = df_after['ATR'].iloc[0]
atr_k = max(0.40, min(0.60, 0.5 * (day_atr_median / max(1e-12, atr0))))
min_w1_pullback = 0.25 + 0.05 * (atr0 / max(1e-12, day_atr_median))

print(f"Paramètres adaptatifs:")
print(f"  ATR médian: {day_atr_median*10000:.2f} pips")
print(f"  ATR initial: {atr0*10000:.2f} pips")
print(f"  ATR_K: {atr_k:.3f}")
print(f"  Min pullback ratio: {min_w1_pullback:.3f} ({min_w1_pullback*100:.1f}%)\n")

# Direction
direction = 'bullish' if (df_after['high'].iloc[:6].max() - baseline) >= (baseline - df_after['low'].iloc[:6].min()) else 'bearish'
print(f"Direction: {direction}\n")

highs = df_after['high'].values
lows = df_after['low'].values
times = df_after.index

print("="*80)
print("PHASE 1 : DÉTECTION WAVE 1")
print("="*80 + "\n")

peak1_price = baseline
peak1_time = event_dt
pullback1_price = None
pullback1_time = None

min_bars_before_pullback = 3
max_idle_bars = 20
idle = 0

print(f"Recherche peak progressif + pullback (garde {min_bars_before_pullback} bars)...\n")

for i in range(len(df_after)):
    ts = times[i]
    atr_i = df_after['ATR'].iloc[i]
    
    # Chercher peak progressif
    if direction == 'bullish':
        if highs[i] > peak1_price:
            old_peak = peak1_price
            peak1_price = highs[i]
            peak1_time = ts
            impact = to_pips(peak1_price - baseline)
            print(f"  {ts.strftime('%H:%M:%S')} - Nouveau peak: {impact:.1f} pips")
            idle = 0
        else:
            idle += 1
        
        # Chercher pullback avec garde temporelle
        minutes_since_peak = (ts - peak1_time).total_seconds() / 60.0
        if minutes_since_peak >= min_bars_before_pullback:
            amp = peak1_price - baseline
            if amp > 0:
                dd = (peak1_price - lows[i]) / amp
                dd_filter = (peak1_price - lows[i]) >= atr_k * atr_i
                
                # Vérifier extremum local
                if dd >= min_w1_pullback and dd_filter and i >= 2 and i < len(df_after) - 2:
                    if is_local_trough(pd.Series(lows), i, width=2):
                        pullback1_price = lows[i]
                        pullback1_time = ts
                        print(f"\n✅ PULLBACK DÉTECTÉ:")
                        print(f"   Time: {pullback1_time.strftime('%H:%M:%S')}")
                        print(f"   Price: {pullback1_price:.5f}")
                        print(f"   Pullback ratio: {dd*100:.1f}%")
                        print(f"   Minutes depuis peak: {minutes_since_peak:.1f} min")
                        break
    
    if idle >= max_idle_bars:
        print(f"\n❌ Idle {max_idle_bars} bars atteint sans pullback")
        break

if pullback1_time is None:
    print(f"\n❌ WAVE 1 : Pas de pullback validé")
    print(f"   Peak final: {to_pips(peak1_price - baseline):.1f} pips @ {peak1_time.strftime('%H:%M:%S')}")
    sys.exit(0)

wave1_impact = to_pips(abs(peak1_price - baseline))
pullback1_ratio = abs(peak1_price - pullback1_price) / abs(peak1_price - baseline)

print(f"\n✅ WAVE 1 COMPLÈTE:")
print(f"   Impact: {wave1_impact:.1f} pips")
print(f"   Peak: {peak1_time.strftime('%H:%M:%S')} @ {peak1_price:.5f}")
print(f"   Pullback: {pullback1_time.strftime('%H:%M:%S')} @ {pullback1_price:.5f}")
print(f"   Pullback ratio: {pullback1_ratio*100:.1f}%")

print(f"\n{'='*80}")
print("PHASE 2 : CHERCHER WAVE 2")
print("="*80 + "\n")

start_i = df_after.index.get_loc(pullback1_time) + 1
if start_i >= len(df_after):
    print("✅ Pas assez de données après pullback → SINGLE WAVE")
    sys.exit(0)

print(f"Recherche nouveau peak après pullback1 (bars restantes: {len(df_after) - start_i})...\n")
print(f"Critères Wave2:")
print(f"  - Break: peak > {peak1_price:.5f} + 1 pip")
print(f"  - Extension: impact > {wave1_impact * 1.2:.1f} pips (1.2x Wave1)")
print(f"  - Idle max: {max_idle_bars} bars\n")

peak2_price = peak1_price
peak2_time = peak1_time
has_significant_wave2 = False
idle = 0

for i in range(start_i, len(df_after)):
    ts = times[i]
    
    if direction == 'bullish':
        if highs[i] > peak2_price:
            old_peak2 = peak2_price
            peak2_price = highs[i]
            peak2_time = ts
            idle = 0
            
            wave2_vs_baseline = to_pips(peak2_price - baseline)
            break_condition = to_pips(peak2_price - peak1_price) >= 1.0
            extension_condition = wave2_vs_baseline >= 1.2 * wave1_impact
            
            print(f"  {ts.strftime('%H:%M:%S')} - Peak: {wave2_vs_baseline:.1f} pips | "
                  f"vs Wave1: {to_pips(peak2_price - peak1_price):.1f} pips | "
                  f"Break: {break_condition} | Extension: {extension_condition}")
            
            if break_condition or extension_condition:
                has_significant_wave2 = True
                print(f"\n✅ WAVE 2 SIGNIFICATIVE DÉTECTÉE → DOUBLE WAVE (rejeté pour Single)")
                print(f"   Wave2 impact: {wave2_vs_baseline:.1f} pips")
                print(f"   Ratio Wave2/Wave1: {wave2_vs_baseline/wave1_impact:.2f}x")
                break
        else:
            idle += 1
            if idle == max_idle_bars:
                print(f"\n✅ Idle {max_idle_bars} bars → Pas de Wave2 significative → SINGLE WAVE")
    
    if idle >= max_idle_bars:
        break

print(f"\n{'='*80}")
print("RÉSULTAT FINAL")
print("="*80 + "\n")

if has_significant_wave2:
    print("❌ DOUBLE WAVE détecté → Rejeté pour Single Wave")
    print(f"   Wave1: {wave1_impact:.1f} pips")
    print(f"   Wave2: {to_pips(peak2_price - baseline):.1f} pips")
else:
    print("✅ SINGLE WAVE confirmé")
    print(f"   Impact: {wave1_impact:.1f} pips")
    print(f"   Pullback: {pullback1_ratio*100:.1f}%")
    
    # Classification
    if wave1_impact >= 40 and pullback1_ratio < 0.30:
        print(f"   Type: FORT (impact >= 40 pips, pullback < 30%)")
    elif 20 <= wave1_impact < 40 and pullback1_ratio < 0.40:
        print(f"   Type: INTERMEDIATE (impact 20-40 pips, pullback < 40%)")
    else:
        print(f"   ❌ Ne correspond pas aux critères:")
        print(f"      Impact {wave1_impact:.1f} pips (besoin >= 20)")
        print(f"      Pullback {pullback1_ratio*100:.1f}% (Fort: <30%, Inter: <40%)")

print("\n" + "="*80)
