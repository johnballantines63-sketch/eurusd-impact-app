#!/usr/bin/env python3
"""Vérifier si les 10 événements US 12:30 sont dans la DB"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

query = """
SELECT 
    event_name,
    actual,
    forecast,
    previous
FROM economic_events
WHERE datetime_utc >= '2025-09-11 12:30:00'
  AND datetime_utc < '2025-09-11 12:31:00'
  AND country = 'US'
ORDER BY event_name
"""

df = conn.execute(query).df()
conn.close()

print("="*80)
print("ÉVÉNEMENTS US 12:30 DANS LA DB (après import corrigé)")
print("="*80)
print()
print(df.to_string(index=False))
print()
print(f"Total : {len(df)} événements")
print()

expected = [
    'inflation_rate_yoy',
    'cpi_s.a',
    'cpi',
    'real_earnings_mom',
    'continuing_jobless_claims',
    'core_inflation_rate_mom',
    'jobless_claims_4_week_average',
    'core_inflation_rate_yoy',
    'initial_jobless_claims',
    'inflation_rate_mom'
]

print("VÉRIFICATION :")
print("-"*80)
for event in expected:
    present = event in df['event_name'].values
    status = "✅" if present else "❌"
    print(f"{status} {event}")

print()

if len(df) == 10:
    print("✅ Tous les événements présents !")
else:
    print(f"❌ Manque {10 - len(df)} événements")
