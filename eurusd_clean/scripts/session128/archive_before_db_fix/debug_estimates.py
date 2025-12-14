#!/usr/bin/env python3
"""Vérifier colonnes forecast/estimate dans economic_events"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

print("COLONNES economic_events :")
cols = conn.execute("DESCRIBE economic_events").df()
print(cols)
print()

print("ÉCHANTILLON 11 SEPT (toutes colonnes) :")
sample = conn.execute("""
    SELECT *
    FROM economic_events
    WHERE datetime_utc >= '2025-09-11 12:30:00'
      AND datetime_utc < '2025-09-11 12:31:00'
      AND country = 'US'
    LIMIT 3
""").df()
print(sample.T)  # Transposé pour voir toutes colonnes

conn.close()
