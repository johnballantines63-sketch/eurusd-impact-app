"""
DEBUG COMPLET - Pourquoi aucun événement trouvé ?
=================================================
"""
import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("DEBUG ÉVÉNEMENTS - INVESTIGATION COMPLÈTE")
print("="*80)
print()

# TEST 1 : Combien d'événements en général ?
print("TEST 1 : Total événements dans table events")
print("-"*80)
total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
print(f"Total événements : {total:,}")
print()

# TEST 2 : Plage de dates
print("TEST 2 : Plage dates événements")
print("-"*80)
result = conn.execute("""
    SELECT 
        MIN(ts_utc) as min_date,
        MAX(ts_utc) as max_date
    FROM events
""").fetchone()
print(f"Date min : {result[0]}")
print(f"Date max : {result[1]}")
print()

# TEST 3 : Événements US HIGH importance
print("TEST 3 : Événements US importance >= 3")
print("-"*80)
us_high = conn.execute("""
    SELECT COUNT(*)
    FROM events
    WHERE country = 'US'
      AND importance_n >= 3
""").fetchone()[0]
print(f"Événements US HIGH : {us_high:,}")
print()

# TEST 4 : Événements septembre 2025
print("TEST 4 : Événements septembre 2025")
print("-"*80)
sept = conn.execute("""
    SELECT COUNT(*)
    FROM events
    WHERE ts_utc >= '2025-09-01'
      AND ts_utc < '2025-10-01'
""").fetchone()[0]
print(f"Événements septembre 2025 : {sept:,}")
print()

# TEST 5 : Événements 11 septembre 2025 (TOUS)
print("TEST 5 : Événements 11 septembre 2025 (TOUS)")
print("-"*80)
sept11_all = conn.execute("""
    SELECT ts_utc, event_key, country, importance_n
    FROM events
    WHERE ts_utc >= '2025-09-11'
      AND ts_utc < '2025-09-12'
    ORDER BY ts_utc
    LIMIT 20
""").fetchall()

if sept11_all:
    print(f"Trouvés : {len(sept11_all)} événements")
    for ts, key, country, imp in sept11_all[:10]:
        print(f"  {ts} | {country:3} | imp={imp} | {key}")
else:
    print("❌ Aucun événement trouvé")
print()

# TEST 6 : Événements 11 septembre avec Bern time explicit
print("TEST 6 : Événements 11 sept avec timezone +02:00")
print("-"*80)
sept11_bern = conn.execute("""
    SELECT ts_utc, event_key, country
    FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+02:00'
      AND ts_utc < '2025-09-11 14:35:00+02:00'
    ORDER BY ts_utc
""").fetchall()

if sept11_bern:
    print(f"Trouvés : {len(sept11_bern)}")
    for ts, key, country in sept11_bern:
        print(f"  {ts} | {country} | {key}")
else:
    print("❌ Aucun événement trouvé")
print()

# TEST 7 : Format timezone des timestamps
print("TEST 7 : Format timestamp dans DB")
print("-"*80)
sample = conn.execute("""
    SELECT ts_utc, typeof(ts_utc)
    FROM events
    LIMIT 3
""").fetchall()

for ts, type_val in sample:
    print(f"  {ts} | Type: {type_val}")
print()

# TEST 8 : Événements CPI spécifiquement
print("TEST 8 : Événements CPI US")
print("-"*80)
cpi = conn.execute("""
    SELECT ts_utc, event_key
    FROM events
    WHERE country = 'US'
      AND (event_key LIKE '%inflation%' OR event_key LIKE '%cpi%')
      AND ts_utc >= '2025-01-01'
    ORDER BY ts_utc DESC
    LIMIT 10
""").fetchall()

if cpi:
    print(f"Trouvés : {len(cpi)} événements CPI")
    for ts, key in cpi:
        print(f"  {ts} | {key}")
else:
    print("❌ Aucun CPI trouvé")
print()

conn.close()

print("="*80)
print("FIN DEBUG")
print("="*80)
