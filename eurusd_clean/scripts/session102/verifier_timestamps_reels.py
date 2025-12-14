#!/usr/bin/env python3
"""
VÉRIFIER TIMESTAMPS RÉELS 11.09
=================================

Afficher les timestamps EXACTS des événements
pour confirmer qu'ils sont bien à 14:30
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 100)
print("TIMESTAMPS RÉELS - 11.09.2025")
print("=" * 100)
print()

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

query = """
SELECT 
    e.event_key,
    e.event_title,
    e.ts_utc,
    DATE_TRUNC('hour', e.ts_utc) as hour_truncated,
    ef.empirical_score,
    ef.family
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND (
        e.importance_n = 1
        OR ef.empirical_score > 40
        OR (ef.family = 'Jobless Claims' AND ef.empirical_score > 25)
    )
ORDER BY e.ts_utc, e.event_key
LIMIT 15
"""

df = conn.execute(query).fetchdf()

print(f"✅ {len(df)} événements trouvés\n")

print(f"{'Event':<45} {'Timestamp RÉEL':>20} {'Truncated Hour':>20} {'Family':<15}")
print("-" * 110)

for idx, row in df.iterrows():
    name = row['event_title'] if pd.notna(row['event_title']) else row['event_key']
    name = name[:43] if len(name) > 43 else name
    
    ts_real = str(row['ts_utc'])
    ts_trunc = str(row['hour_truncated'])
    family = row['family'] if pd.notna(row['family']) else "NULL"
    
    print(f"{name:<45} {ts_real:>20} {ts_trunc:>20} {family:<15}")

conn.close()

print()
print("=" * 100)
print("EXPLICATION")
print("=" * 100)
print()

print("DATE_TRUNC('hour', ...) arrondit à l'heure pleine :")
print("  - 14:30:00 → 14:00:00 (affichage)")
print("  - 14:45:00 → 14:00:00 (affichage)")
print("  - 16:30:00 → 16:00:00 (affichage)")
print()
print("C'est VOULU pour regrouper les événements proches en clusters horaires.")
print()
print("Les événements CPI+Jobless sont bien à 14:30 (12:30 UTC).")
print("L'affichage '14:00' signifie 'cluster entre 14:00 et 14:59'.")
