#!/usr/bin/env python3
"""
Extraction prix toutes les 30 minutes pour 2025-09-11
"""

import duckdb
from pathlib import Path
from datetime import datetime, timedelta

# Chemins
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR.parent / "fx_impact_app" / "data" / "warehouse.duckdb"

print("="*80)
print("EXTRACTION PRIX 24H - INTERVALLE 30 MINUTES")
print("="*80)
print(f"\nDB : {DB_PATH}")
print(f"Existe : {DB_PATH.exists()}")

# Connexion DB
conn = duckdb.connect(str(DB_PATH), read_only=True)

# Période exacte
start_ts = "2025-09-10 12:30:00+02:00"
end_ts = "2025-09-11 12:30:00+02:00"

print(f"\nPériode analysée :")
print(f"  Début : {start_ts} (10 sept 14:30 Bern)")
print(f"  Fin   : {end_ts} (11 sept 14:30 Bern)")

# Requête tous les prix
query = """
SELECT 
    ts_utc,
    close
FROM eurusd_prices
WHERE ts_utc >= ?::TIMESTAMP
  AND ts_utc <= ?::TIMESTAMP
ORDER BY ts_utc
"""

df_all = conn.execute(query, [start_ts, end_ts]).fetchdf()
print(f"\n✅ Chargé {len(df_all)} lignes prix total")

# Extraire toutes les 30 minutes
start_dt = datetime.fromisoformat(start_ts.replace('+02:00', ''))
end_dt = datetime.fromisoformat(end_ts.replace('+02:00', ''))

print("\n" + "="*80)
print("PRIX TOUTES LES 30 MINUTES")
print("="*80)
print(f"\n{'Timestamp':<25} {'Bern Time':<15} {'Close':<10}")
print("-"*80)

current_dt = start_dt
interval_count = 0
prices_list = []

while current_dt <= end_dt:
    # Chercher le prix le plus proche de current_dt
    target_ts = current_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Filtrer dans le dataframe
    df_filtered = df_all[df_all['ts_utc'].astype(str).str.startswith(target_ts[:16])]
    
    if len(df_filtered) > 0:
        row = df_filtered.iloc[0]
        bern_time = f"{current_dt.strftime('%d/%m %H:%M')}"
        print(f"{row['ts_utc']!s:<25} {bern_time:<15} {row['close']:<10.5f}")
        prices_list.append(row['close'])
        interval_count += 1
    
    # Avancer de 30 minutes
    current_dt += timedelta(minutes=30)

print("-"*80)
print(f"\nTotal intervalles : {interval_count}")

# Trouver HIGH et LOW de la période
max_price = df_all['close'].max()
min_price = df_all['close'].min()
max_time = df_all[df_all['close'] == max_price].iloc[0]['ts_utc']
min_time = df_all[df_all['close'] == min_price].iloc[0]['ts_utc']

print("\n" + "="*80)
print("EXTREMES PÉRIODE 24H")
print("="*80)
print(f"\nHIGH absolu : {max_price:.5f}")
print(f"  Timestamp : {max_time}")
print(f"\nLOW absolu  : {min_price:.5f}")
print(f"  Timestamp : {min_time}")

# Distance depuis chaque extrême
event_price = df_all.iloc[-1]['close']
print(f"\nPrix event (12:30:00+02:00) : {event_price:.5f}")
print(f"\nDistance depuis HIGH : {(event_price - max_price) * 10000:.1f} pips")
print(f"Distance depuis LOW  : {(event_price - min_price) * 10000:.1f} pips")

# Analyser tendance
if len(prices_list) >= 2:
    print("\n" + "="*80)
    print("ANALYSE TENDANCE")
    print("="*80)
    
    # Variation totale
    variation_total = ((prices_list[-1] - prices_list[0]) / prices_list[0]) * 100
    print(f"\nVariation totale 24h : {variation_total:+.2f}%")
    print(f"                       {(prices_list[-1] - prices_list[0]) * 10000:+.1f} pips")
    
    # Trouver quel extrême est le plus proche temporellement
    idx_max = df_all[df_all['close'] == max_price].index[0]
    idx_min = df_all[df_all['close'] == min_price].index[0]
    idx_event = len(df_all) - 1
    
    distance_to_high = idx_event - idx_max
    distance_to_low = idx_event - idx_min
    
    print(f"\nDistance au HIGH : {distance_to_high} minutes")
    print(f"Distance au LOW  : {distance_to_low} minutes")
    
    if distance_to_low < distance_to_high:
        print(f"\n→ Dernier pic = LOW (plus proche)")
        print(f"   Prix monte depuis low pendant {distance_to_low/60:.1f}h")
    else:
        print(f"\n→ Dernier pic = HIGH (plus proche)")
        print(f"   Prix descend depuis high pendant {distance_to_high/60:.1f}h")

conn.close()
