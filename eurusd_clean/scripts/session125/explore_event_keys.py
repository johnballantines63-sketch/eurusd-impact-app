#!/usr/bin/env python3
"""
SESSION 125 - VALIDATION CROISÉE (event_key)
"""
import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("EXPLORATION : event_key vs event_title")
print("="*80)
print()

# 1. Compter par event_key
query1 = """
SELECT 
    event_key,
    event_title,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND ts_utc >= '2023-01-01'
GROUP BY event_key, event_title
ORDER BY count DESC
LIMIT 30
"""

df = conn.execute(query1).df()

print("📊 TOP 30 event_key HIGH US :")
print()

for idx, row in df.iterrows():
    title = row['event_title'] if pd.notna(row['event_title']) else "(null)"
    print(f"   {row['count']:3d}× {row['event_key']:40s} - {title}")

print()

# 2. Vérifier CPI
query_cpi = """
SELECT DISTINCT 
    event_key,
    event_title,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND event_key LIKE '%CPI%'
  AND ts_utc >= '2023-01-01'
GROUP BY event_key, event_title
ORDER BY count DESC
"""

df_cpi = conn.execute(query_cpi).df()

print("✅ Événements CPI (event_key) :")
print()

for idx, row in df_cpi.iterrows():
    title = row['event_title'] if pd.notna(row['event_title']) else "(null)"
    print(f"   {row['count']:3d}× {row['event_key']:40s} - {title}")

conn.close()

print()
print("="*80)
