#!/usr/bin/env python3
"""
SESSION 127 - QUICK CHECK DB
Vérification rapide : exemples événements réels DB

Auteur : André Valentin
Date : 11 novembre 2025
"""
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / 'data' / 'warehouse.duckdb'

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("=" * 80)
print("QUICK CHECK DB - EXEMPLES ÉVÉNEMENTS RÉELS")
print("=" * 80)
print()

# Prendre 5 événements inflation_rate en 2024
query_inflation = """
SELECT 
    date,
    event_key,
    country,
    actual,
    forecast,
    previous,
    importance_n
FROM events
WHERE country = 'US'
  AND LOWER(event_key) LIKE '%inflation%rate%'
  AND date >= '2024-01-01'
ORDER BY date DESC
LIMIT 10
"""

print("[1] ÉVÉNEMENTS INFLATION 2024 (US)")
print("-" * 80)

result = conn.execute(query_inflation).df()

for _, row in result.iterrows():
    imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
    print(f"{row['date']} | event_key: '{row['event_key']:<40}' | [{imp}]")
    print(f"           actual={row['actual']}, forecast={row['forecast']}, previous={row['previous']}")
    print()

print()

# GDP events
query_gdp = """
SELECT 
    date,
    event_key,
    country,
    actual,
    forecast,
    importance_n
FROM events
WHERE country = 'US'
  AND LOWER(event_key) LIKE '%gdp%'
  AND date >= '2024-01-01'
ORDER BY date DESC
LIMIT 10
"""

print("[2] ÉVÉNEMENTS GDP 2024 (US)")
print("-" * 80)

result = conn.execute(query_gdp).df()

for _, row in result.iterrows():
    imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
    print(f"{row['date']} | event_key: '{row['event_key']:<40}' | [{imp}]")
    print(f"           actual={row['actual']}, forecast={row['forecast']}")
    print()

print()

# Retail sales
query_retail = """
SELECT 
    date,
    event_key,
    country,
    actual,
    importance_n
FROM events
WHERE country = 'US'
  AND LOWER(event_key) LIKE '%retail%sales%'
  AND date >= '2024-01-01'
ORDER BY date DESC
LIMIT 10
"""

print("[3] ÉVÉNEMENTS RETAIL SALES 2024 (US)")
print("-" * 80)

result = conn.execute(query_retail).df()

for _, row in result.iterrows():
    imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
    print(f"{row['date']} | event_key: '{row['event_key']:<40}' | [{imp}]")
    print(f"           actual={row['actual']}")
    print()

conn.close()

print("=" * 80)
print("✅ QUICK CHECK TERMINÉ")
print("=" * 80)
