#!/usr/bin/env python3
"""Vérifier calcul surprises événements 11 septembre"""
import duckdb
from pathlib import Path
import json
import pandas as pd

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

query = """
SELECT 
    datetime_utc,
    event_name,
    actual,
    previous,
    raw_data
FROM economic_events
WHERE datetime_utc >= '2025-09-11 12:30:00'
  AND datetime_utc < '2025-09-11 12:31:00'
  AND country = 'US'
ORDER BY event_name
"""

df = conn.execute(query).df()
conn.close()

print("SURPRISES CALCULÉES - 11 SEPTEMBRE 12:30 (US):")
print("="*100)

for idx, row in df.iterrows():
    # Extraire estimate
    try:
        data = json.loads(row['raw_data'])
        estimate = data.get('estimate', None)
    except:
        estimate = None
    
    # Calculer surprise
    if estimate and row['actual']:
        # Est-ce un taux/inflation ?
        is_rate = any(kw in row['event_name'].lower() for kw in ['rate', 'inflation', 'cpi'])
        
        if is_rate:
            surprise_pct = ((row['actual'] - estimate) / estimate) * 100 if estimate != 0 else 0
            surprise_pts = row['actual'] - estimate
        else:
            surprise_pct = ((row['actual'] - estimate) / estimate) * 100 if estimate != 0 else 0
            surprise_pts = None
    else:
        surprise_pct = None
        surprise_pts = None
    
    print(f"\n{row['event_name']:<30}")
    print(f"  Actual   : {row['actual']}")
    print(f"  Estimate : {estimate}")
    print(f"  Previous : {row['previous']}")
    if surprise_pct is not None:
        print(f"  Surprise : {surprise_pct:.2f}%", end="")
        if surprise_pts is not None:
            print(f" ({surprise_pts:+.2f} pts)")
        else:
            print()
    else:
        print(f"  Surprise : N/A")

print("\n" + "="*100)
print("\nREMARQUE : Session 115 parlait de surprise CPI 33% !")
print("Vérifier si le calcul de surprise dans calculate_cluster_impact() est correct.")
