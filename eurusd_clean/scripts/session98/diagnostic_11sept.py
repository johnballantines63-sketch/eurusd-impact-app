#!/usr/bin/env python3
"""
Diagnostic 11 septembre - Vérifier données DB
Session 98
"""

import duckdb
from pathlib import Path
import sys

# Path DB
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'fx_impact_app' / 'src'))

from config import get_db_path

db_path = get_db_path()
conn = duckdb.connect(db_path, read_only=True)

print("=" * 80)
print("DIAGNOSTIC 11 SEPTEMBRE 2025 - DONNÉES DB")
print("=" * 80)

# Query EXACTE V2.4
query = """
SELECT 
    e.event_key,
    e.event_title as label,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.forecast,
    e.previous,
    ef.family,
    ef.empirical_score,
    ef.latency_median
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
    AND ef.empirical_score > 40
ORDER BY e.ts_utc, e.event_title
"""

df = conn.execute(query).fetchdf()
conn.close()

print(f"\n✅ {len(df)} événements HIGH trouvés\n")

for idx, row in df.iterrows():
    print(f"{idx+1}. {row['label']}")
    print(f"   Time: {row['ts_utc']}")
    print(f"   Score: {row['empirical_score']}")
    print(f"   Actual: {row['actual']}")
    print(f"   Estimate: {row['estimate']}")
    print(f"   Forecast: {row['forecast']}")
    print(f"   Previous: {row['previous']}")
    
    # Calcul surprise
    if row['actual'] is not None and row['estimate'] is not None and row['estimate'] != 0:
        surprise = abs((row['actual'] - row['estimate']) / row['estimate']) * 100
        print(f"   ➜ Surprise: {surprise:.1f}%")
    else:
        print(f"   ➜ Surprise: 0% (actual={row['actual']}, estimate={row['estimate']})")
    print()

print("=" * 80)
print("ANALYSE")
print("=" * 80)

# Compter événements avec surprise
events_with_surprise = 0
events_no_surprise = 0

for idx, row in df.iterrows():
    if row['actual'] is not None and row['estimate'] is not None and row['estimate'] != 0:
        events_with_surprise += 1
    else:
        events_no_surprise += 1

print(f"\nÉvénements AVEC surprise valide: {events_with_surprise}")
print(f"Événements SANS surprise (NULL/0): {events_no_surprise}")

if events_no_surprise > 0:
    print("\n⚠️ PROBLÈME IDENTIFIÉ:")
    print("   Des événements n'ont pas de valeurs actual/estimate valides")
    print("   → Surprise calculée à 0%")
    print("   → Impact sous-estimé")
