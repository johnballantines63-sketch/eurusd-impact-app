#!/usr/bin/env python3
"""
DEBUG : TOUS les événements 11 septembre 2025
"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("TOUS ÉVÉNEMENTS 11 SEPTEMBRE 2025 - USD")
print("=" * 80)
print()

# Tous les événements USD (pas juste HIGH)
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
      AND country = 'usd'
    ORDER BY datetime_utc, importance DESC, event_name
""").df()

print(f"Total événements USD : {len(result)}")
print()
print(result.to_string())
print()

# Comptage par importance
print("=" * 80)
print("COMPTAGE PAR IMPORTANCE")
print("=" * 80)
result_count = conn.execute("""
    SELECT 
        importance,
        COUNT(*) as count
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND country = 'usd'
    GROUP BY importance
    ORDER BY importance DESC
""").df()
print(result_count)
print()

# Événements HIGH détaillés
print("=" * 80)
print("ÉVÉNEMENTS HIGH UNIQUEMENT")
print("=" * 80)
result_high = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND country = 'usd'
      AND importance = 'HIGH'
    ORDER BY datetime_utc, event_name
""").df()
print(result_high.to_string())
print()

conn.close()
