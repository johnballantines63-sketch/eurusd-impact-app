#!/usr/bin/env python3
"""
DEBUG : Vérifier événements 11 septembre 2025 dans DB
"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

# Test 1 : Vérifier structure table events
print("=" * 80)
print("STRUCTURE TABLE EVENTS")
print("=" * 80)
result = conn.execute("DESCRIBE events").df()
print(result)
print()

# Test 2 : Compter événements US HIGH
print("=" * 80)
print("TOTAL ÉVÉNEMENTS US HIGH")
print("=" * 80)
result = conn.execute("""
    SELECT COUNT(*) as total
    FROM events
    WHERE country = 'US' AND importance_n = 3
""").df()
print(f"Total : {result['total'].iloc[0]}")
print()

# Test 3 : Vérifier dates disponibles (septembre 2025)
print("=" * 80)
print("ÉVÉNEMENTS US HIGH SEPTEMBRE 2025")
print("=" * 80)
result = conn.execute("""
    SELECT 
        DATE(ts_utc) as date,
        COUNT(*) as count
    FROM events
    WHERE country = 'US' 
      AND importance_n = 3
      AND ts_utc >= '2025-09-01'
      AND ts_utc < '2025-10-01'
    GROUP BY DATE(ts_utc)
    ORDER BY date
    LIMIT 20
""").df()
print(result)
print()

# Test 4 : Chercher événements autour du 11 septembre
print("=" * 80)
print("ÉVÉNEMENTS US HIGH AUTOUR DU 11 SEPTEMBRE 2025")
print("=" * 80)
result = conn.execute("""
    SELECT 
        ts_utc,
        event_key,
        importance_n,
        actual,
        estimate
    FROM events
    WHERE country = 'US'
      AND ts_utc >= '2025-09-10'
      AND ts_utc <= '2025-09-12'
    ORDER BY ts_utc
    LIMIT 20
""").df()
print(result)
print()

conn.close()
