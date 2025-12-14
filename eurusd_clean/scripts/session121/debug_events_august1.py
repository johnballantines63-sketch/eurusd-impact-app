#!/usr/bin/env python3
"""
Debug : Vérifier événements HIGH autour du 1er août 14:30
"""

import duckdb
import pandas as pd
import pytz

db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
tz_bern = pytz.timezone('Europe/Zurich')

spike_time = pd.to_datetime('2025-08-01 14:30:00').tz_localize(tz_bern)

print("="*80)
print("DEBUG ÉVÉNEMENTS - 1er août 2025")
print("="*80 + "\n")

print(f"Spike détecté : {spike_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"Spike en UTC  : {spike_time.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")

# Chercher événements ±30 min (large)
start_window = spike_time - pd.Timedelta(minutes=30)
end_window = spike_time + pd.Timedelta(minutes=30)

start_utc = start_window.astimezone(pytz.utc)
end_utc = end_window.astimezone(pytz.utc)

print(f"Fenêtre recherche (Bern) : {start_window.strftime('%H:%M')} → {end_window.strftime('%H:%M')}")
print(f"Fenêtre recherche (UTC)  : {start_utc.strftime('%H:%M')} → {end_utc.strftime('%H:%M')}\n")

conn = duckdb.connect(db_path, read_only=True)

# TOUS les événements du 1er août (tous pays)
query = """
SELECT 
    ts_utc,
    country,
    event_title,
    importance_n,
    actual,
    forecast
FROM events
WHERE ts_utc >= '2025-08-01 00:00:00'
  AND ts_utc < '2025-08-02 00:00:00'
ORDER BY ts_utc
"""

df = conn.execute(query).df()

print(f"TOUS les événements du 1er août : {len(df)}\n")

if len(df) > 0:
    print("LISTE COMPLÈTE (tripar heure UTC) :")
    print("="*100)
    for _, row in df.iterrows():
        event_utc = pd.to_datetime(row['ts_utc'])
        event_bern = event_utc.tz_convert(tz_bern)
        importance = "HIGH" if row['importance_n'] == 3 else ("MEDIUM" if row['importance_n'] == 2 else "LOW")
        
        title = row['event_title'] if row['event_title'] else "Unknown Event"
        actual = f"A:{row['actual']}" if row['actual'] is not None else "A:-"
        forecast = f"F:{row['forecast']}" if row['forecast'] is not None else "F:-"
        
        print(f"{event_bern.strftime('%H:%M:%S')} CEST | {event_utc.strftime('%H:%M:%S')} UTC | "
              f"{importance:6s} | {row['country']:3s} | {title[:40]:40s} | {actual:12s} | {forecast:12s}")
else:
    print("❌ Aucun événement trouvé dans cette période")
    print("\nVérifions si des événements existent le 1er août...")
    
    query_day = "SELECT COUNT(*) as count FROM events WHERE DATE(ts_utc) = '2025-08-01'"
    count = conn.execute(query_day).fetchone()[0]
    print(f"Total événements 1er août : {count}")

conn.close()

print("\n" + "="*80)
