#!/usr/bin/env python3
"""
DEBUG : Vérifier format colonne importance
"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("VALEURS DISTINCTES COLONNE IMPORTANCE")
print("=" * 80)
result = conn.execute("""
    SELECT 
        importance,
        COUNT(*) as count
    FROM economic_events
    GROUP BY importance
    ORDER BY count DESC
""").df()
print(result)
print()

print("=" * 80)
print("PAYS DISPONIBLES")
print("=" * 80)
result = conn.execute("""
    SELECT 
        country,
        COUNT(*) as count
    FROM economic_events
    GROUP BY country
    ORDER BY count DESC
    LIMIT 10
""").df()
print(result)
print()

print("=" * 80)
print("EXEMPLE ÉVÉNEMENTS SEPTEMBRE 2025 (tous)")
print("=" * 80)
result = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
    ORDER BY datetime_utc
    LIMIT 20
""").df()
print(result)
print()

conn.close()
