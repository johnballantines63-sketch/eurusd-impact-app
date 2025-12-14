#!/usr/bin/env python3
"""
DEBUG : Vérifier période economic_events et 11 septembre
"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("TABLE ECONOMIC_EVENTS - ANALYSE COMPLÈTE")
print("=" * 80)
print()

# Période
result = conn.execute("""
    SELECT 
        MIN(datetime_utc) as min_date, 
        MAX(datetime_utc) as max_date,
        COUNT(*) as total
    FROM economic_events
""").df()
print(f"Période : {result['min_date'].iloc[0]} → {result['max_date'].iloc[0]}")
print(f"Total   : {result['total'].iloc[0]:,} événements")
print()

# Événements US HIGH
result = conn.execute("""
    SELECT COUNT(*) as count
    FROM economic_events
    WHERE country = 'US' AND importance = 'HIGH'
""").df()
print(f"Événements US HIGH : {result['count'].iloc[0]:,}")
print()

# Septembre 2025
print("=" * 80)
print("SEPTEMBRE 2025 - US HIGH")
print("=" * 80)
result = conn.execute("""
    SELECT 
        DATE(datetime_utc) as date,
        COUNT(*) as count
    FROM economic_events
    WHERE country = 'US' 
      AND importance = 'HIGH'
      AND datetime_utc >= '2025-09-01'
      AND datetime_utc < '2025-10-01'
    GROUP BY DATE(datetime_utc)
    ORDER BY date
""").df()
print(result)
print()

# 11 septembre 2025 détail
print("=" * 80)
print("11 SEPTEMBRE 2025 - DÉTAIL")
print("=" * 80)
result = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND country = 'US'
      AND importance = 'HIGH'
    ORDER BY datetime_utc
""").df()
print(result)
print()

conn.close()
