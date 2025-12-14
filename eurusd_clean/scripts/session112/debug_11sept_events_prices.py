#!/usr/bin/env python3
"""
DEBUG - Inspection événements et prix 11 septembre 2025
"""
import duckdb
from pathlib import Path
import pandas as pd

db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

con = duckdb.connect(str(db_path), read_only=True)

print("="*80)
print("🔍 DEBUG - 11 SEPTEMBRE 2025 à 14:30")
print("="*80)

# ══════════════════════════════════════════════════════════════════════
# 1. ÉVÉNEMENTS DU 11 SEPTEMBRE
# ══════════════════════════════════════════════════════════════════════

print("\n📅 ÉVÉNEMENTS DU 11 SEPTEMBRE 2025:")
print("-"*80)

events = con.execute("""
SELECT 
    ts_utc,
    event_title,
    actual,
    estimate,
    forecast,
    previous
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND country = 'US'
ORDER BY ts_utc
""").df()

print(f"\n✅ {len(events)} événements trouvés\n")

for i, row in events.iterrows():
    print(f"{i+1}. {row['ts_utc']} - {row['event_title']}")
    print(f"   Actual: {row['actual']}, Estimate: {row['estimate']}, Previous: {row['previous']}")
    print()

# ══════════════════════════════════════════════════════════════════════
# 2. FOCUS SUR 14:30
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 ÉVÉNEMENTS À 14:30 (CPI cluster)")
print("="*80)

events_1430 = con.execute("""
SELECT 
    ts_utc,
    event_title,
    event_key,
    actual,
    estimate
FROM events
WHERE ts_utc >= '2025-09-11 14:30:00+02:00'
    AND ts_utc < '2025-09-11 14:31:00+02:00'
    AND country = 'US'
ORDER BY event_title
""").df()

print(f"\n✅ {len(events_1430)} événements à 14:30+02:00\n")

for i, row in events_1430.iterrows():
    print(f"{i+1}. {row['event_title']} ({row['event_key']})")
    print(f"   Actual: {row['actual']}, Estimate: {row['estimate']}")

# ══════════════════════════════════════════════════════════════════════
# 3. PRIX AUTOUR DE 14:30
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💹 PRIX DE 14:25 À 14:35 (Méthode Session 86)")
print("="*80)

prices = con.execute("""
SELECT 
    datetime,
    open,
    high,
    low,
    close,
    (high - low) * 10000 as range_pips
FROM prices_1m
WHERE datetime >= '2025-09-11 14:25:00+02:00'
    AND datetime <= '2025-09-11 14:35:00+02:00'
ORDER BY datetime
""").df()

print(f"\n✅ {len(prices)} bougies\n")
print(f"{'Time':<25} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Range':<8}")
print("-"*80)

for i, row in prices.iterrows():
    time_str = str(row['datetime'])
    marker = " ← ÉVÉNEMENT" if '14:30:00' in time_str else ""
    print(f"{time_str:<25} {row['open']:<10.5f} {row['high']:<10.5f} {row['low']:<10.5f} {row['close']:<10.5f} {row['range_pips']:<8.1f}{marker}")

# ══════════════════════════════════════════════════════════════════════
# 4. PREMIÈRE BOUGIE ÉVÉNEMENT
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🎯 PREMIÈRE BOUGIE ÉVÉNEMENT (14:30)")
print("="*80)

first_candle = prices[prices['datetime'] == '2025-09-11 14:30:00+02:00']

if len(first_candle) > 0:
    candle = first_candle.iloc[0]
    print(f"\nTimestamp: {candle['datetime']}")
    print(f"OPEN:  {candle['open']:.5f} ← Prix référence")
    print(f"HIGH:  {candle['high']:.5f}")
    print(f"LOW:   {candle['low']:.5f}")
    print(f"CLOSE: {candle['close']:.5f}")
    print(f"Range: {candle['range_pips']:.1f} pips")
    
    print(f"\n📊 Impact si on mesure depuis OPEN:")
    print(f"   HIGH - OPEN = {(candle['high'] - candle['open']) * 10000:.1f} pips")
    print(f"   OPEN - LOW  = {(candle['open'] - candle['low']) * 10000:.1f} pips")

# ══════════════════════════════════════════════════════════════════════
# 5. PEAK DANS LES 120 MINUTES
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🚀 RECHERCHE PEAK (14:30 à 16:30)")
print("="*80)

prices_120min = con.execute("""
SELECT 
    datetime,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime >= '2025-09-11 14:30:00+02:00'
    AND datetime <= '2025-09-11 16:30:00+02:00'
ORDER BY datetime
""").df()

start_price = first_candle.iloc[0]['open'] if len(first_candle) > 0 else None

if start_price:
    prices_120min['pips_high'] = (prices_120min['high'] - start_price) * 10000
    prices_120min['pips_low'] = (start_price - prices_120min['low']) * 10000
    
    max_high_idx = prices_120min['pips_high'].idxmax()
    max_low_idx = prices_120min['pips_low'].idxmax()
    
    max_high_row = prices_120min.loc[max_high_idx]
    max_low_row = prices_120min.loc[max_low_idx]
    
    print(f"\nPrix départ (OPEN 14:30): {start_price:.5f}")
    print(f"\n🔺 Peak HIGH:")
    print(f"   Temps: {max_high_row['datetime']}")
    print(f"   Prix: {max_high_row['high']:.5f}")
    print(f"   Impact: {max_high_row['pips_high']:.1f} pips")
    
    print(f"\n🔻 Peak LOW:")
    print(f"   Temps: {max_low_row['datetime']}")
    print(f"   Prix: {max_low_row['low']:.5f}")
    print(f"   Impact: {max_low_row['pips_low']:.1f} pips")
    
    if max_high_row['pips_high'] > max_low_row['pips_low']:
        print(f"\n✅ Direction dominante: UP ⬆️")
        print(f"   Impact mesuré: {max_high_row['pips_high']:.1f} pips")
    else:
        print(f"\n✅ Direction dominante: DOWN ⬇️")
        print(f"   Impact mesuré: {max_low_row['pips_low']:.1f} pips")

con.close()

print("\n" + "="*80)
print("FIN DEBUG")
print("="*80)
