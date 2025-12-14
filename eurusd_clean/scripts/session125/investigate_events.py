#!/usr/bin/env python3
"""
INVESTIGATION : Quels événements HIGH disponibles ?
"""
import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"

print("="*80)
print("INVESTIGATION : ÉVÉNEMENTS HIGH DISPONIBLES")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Liste TOUS les événements HIGH US
query = """
SELECT DISTINCT 
    event_name,
    COUNT(*) as occurrences
FROM economic_events
WHERE country = 'US'
  AND importance = 'HIGH'
  AND datetime_utc >= '2023-01-01'
GROUP BY event_name
ORDER BY occurrences DESC
LIMIT 30
"""

df = conn.execute(query).df()

print(f"📊 TOP 30 événements HIGH US (depuis 2023) :")
print()

for idx, row in df.iterrows():
    print(f"   {row['occurrences']:3d}× {row['event_name']}")

print()

# 2. Chercher spécifiquement emploi/payroll
query_employment = """
SELECT DISTINCT event_name
FROM economic_events
WHERE country = 'US'
  AND (
    event_name LIKE '%Employment%'
    OR event_name LIKE '%Payroll%'
    OR event_name LIKE '%Jobs%'
    OR event_name LIKE '%Unemployment%'
  )
ORDER BY event_name
"""

df_emp = conn.execute(query_employment).df()

print("🔍 Événements liés à l'emploi :")
print()

if len(df_emp) > 0:
    for idx, row in df_emp.iterrows():
        print(f"   • {row['event_name']}")
else:
    print("   (aucun)")

print()

# 3. Vérifier CPI pour comparaison
query_cpi = """
SELECT DISTINCT event_name, COUNT(*) as count
FROM economic_events
WHERE country = 'US'
  AND event_name LIKE '%CPI%'
  AND datetime_utc >= '2023-01-01'
GROUP BY event_name
"""

df_cpi = conn.execute(query_cpi).df()

print("✅ Événements CPI (pour comparaison) :")
print()

for idx, row in df_cpi.iterrows():
    print(f"   {row['count']:3d}× {row['event_name']}")

conn.close()

print()
print("="*80)
