#!/usr/bin/env python3
"""
Debug : Que se passe-t-il exactement le 11 septembre 2025 ?
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.eodhd_client import fetch_calendar_json, calendar_to_events_df

print("\n" + "="*80)
print("DEBUG : 11 septembre 2025")
print("="*80)

# 1. Que dit l'API EODHD ?
print("\n[1] Données brutes de l'API EODHD pour 11 septembre 2025 :")
print("-"*80)

data = fetch_calendar_json('2025-09-11', '2025-09-11', countries=['US'])
print(f"Total événements bruts : {len(data)}")

# Filtrer les événements inflation
inflation_raw = [item for item in data if 'inflation' in str(item.get('event', '')).lower()]
print(f"Événements contenant 'inflation' : {len(inflation_raw)}")

for item in inflation_raw:
    print(f"\n   Event : {item.get('event')}")
    print(f"   Comparison : {item.get('comparison')}")
    print(f"   Actual : {item.get('actual')}")
    print(f"   Estimate : {item.get('estimate')}")
    print(f"   Country : {item.get('country')}")

# 2. Après normalisation
print("\n[2] Après normalisation (calendar_to_events_df) :")
print("-"*80)

df = calendar_to_events_df(data)
inflation_df = df[df['event_key'].str.contains('inflation', case=False, na=False)]

print(f"Événements 'inflation' après normalisation : {len(inflation_df)}")
print("\nDétails :")
print(inflation_df[['event_key', 'actual', 'estimate', 'country']].to_string(index=False))

# 3. Ce qui est en DB
print("\n[3] Ce qui est ACTUELLEMENT dans la DB :")
print("-"*80)

db_path = get_db_path()
conn = duckdb.connect(str(db_path))

result = conn.execute("""
    SELECT 
        event_key,
        actual,
        estimate,
        country,
        strftime(ts_utc, '%Y-%m-%d %H:%M:%S') as ts
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
      AND country = 'US'
      AND event_key LIKE '%inflation%'
    ORDER BY ts_utc, event_key
""").fetchall()

print(f"Événements 'inflation' en DB : {len(result)}")
if result:
    print("\nDétails :")
    for event_key, actual, estimate, country, ts in result:
        print(f"   {ts} | {event_key:<40} | {actual} vs {estimate} | {country}")
else:
    print("   Aucun événement trouvé")

# 4. Tous les événements US du 11 septembre
print("\n[4] TOUS les événements US du 11 septembre en DB :")
print("-"*80)

result_all = conn.execute("""
    SELECT 
        strftime(ts_utc, '%H:%M') as time,
        event_key,
        actual,
        estimate
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
      AND country = 'US'
    ORDER BY ts_utc, event_key
""").fetchall()

print(f"Total événements US : {len(result_all)}")
if result_all:
    for time, event_key, actual, estimate in result_all[:20]:  # Limiter à 20
        actual_str = f"{actual:.2f}" if actual is not None else "N/A"
        estimate_str = f"{estimate:.2f}" if estimate is not None else "N/A"
        print(f"   {time} | {event_key:<45} | {actual_str:>8} vs {estimate_str:>8}")

# 5. Compter les événements avec suffixes
print("\n[5] Statistiques globales sur les suffixes MoM/YoY/QoQ :")
print("-"*80)

stats = conn.execute("""
    SELECT 
        CASE 
            WHEN event_key LIKE '%_mom' THEN 'MoM'
            WHEN event_key LIKE '%_yoy' THEN 'YoY'
            WHEN event_key LIKE '%_qoq' THEN 'QoQ'
            ELSE 'Sans suffixe'
        END as type,
        COUNT(*) as count
    FROM events
    WHERE event_key LIKE '%inflation%'
    GROUP BY type
    ORDER BY count DESC
""").fetchall()

for type_suffix, count in stats:
    print(f"   {type_suffix:<20} : {count:>5} événements")

conn.close()

print("\n" + "="*80)
print("Fin du debug")
print("="*80)
