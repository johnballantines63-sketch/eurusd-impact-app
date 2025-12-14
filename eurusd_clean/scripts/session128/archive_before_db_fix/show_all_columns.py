#!/usr/bin/env python3
"""Afficher TOUTES les colonnes pour 1 événement 11 septembre"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

# Prendre 1 événement et afficher TOUTES colonnes
query = """
SELECT *
FROM economic_events
WHERE DATE(datetime_utc) = '2025-09-11'
  AND country = 'US'
  AND event_name = 'inflation_rate'
  AND importance = 'HIGH'
LIMIT 1
"""

df = conn.execute(query).df()
conn.close()

print("TOUTES LES COLONNES (1 événement inflation_rate) :")
print("="*80)

if len(df) > 0:
    for col in df.columns:
        value = df[col].iloc[0]
        print(f"{col:30} : {value}")
else:
    print("Aucun événement trouvé")
