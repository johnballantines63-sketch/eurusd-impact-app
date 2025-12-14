#!/usr/bin/env python3
"""Afficher TOUS les événements 11 septembre avec TOUTES les colonnes"""
import duckdb
from pathlib import Path
import pandas as pd

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

print("="*100)
print("TOUS LES ÉVÉNEMENTS 11 SEPTEMBRE 2025 - TOUTES COLONNES")
print("="*100)
print()

query = """
SELECT *
FROM economic_events
WHERE DATE(datetime_utc) = '2025-09-11'
  AND country IN ('US', 'EU', 'DE')
  AND importance IN ('HIGH', 'MEDIUM')
ORDER BY datetime_utc, event_name
"""

df = conn.execute(query).df()
conn.close()

print(f"TOTAL : {len(df)} événements\n")

# Afficher colonnes importantes
for idx, row in df.iterrows():
    print(f"{'='*100}")
    print(f"ÉVÉNEMENT #{idx+1}")
    print(f"{'='*100}")
    print(f"  datetime_utc  : {row['datetime_utc']}")
    print(f"  event_name    : {row['event_name']}")
    print(f"  country       : {row['country']}")
    print(f"  importance    : {row['importance']}")
    print(f"  actual        : {row['actual']}")
    print(f"  forecast      : {row['forecast']}")
    print(f"  previous      : {row['previous']}")
    print()

# Résumé par cluster temporel
print("="*100)
print("RÉSUMÉ PAR HEURE")
print("="*100)

df['heure'] = pd.to_datetime(df['datetime_utc']).dt.strftime('%H:%M')
summary = df.groupby(['heure', 'country']).agg({
    'event_name': 'count'
}).reset_index()
summary.columns = ['Heure', 'Pays', 'Nombre_événements']

print(summary.to_string(index=False))
