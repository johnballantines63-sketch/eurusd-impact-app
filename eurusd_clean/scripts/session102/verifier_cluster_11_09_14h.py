#!/usr/bin/env python3
"""
VÉRIFIER CLUSTER 11.09.2025 à 14:00
====================================

Afficher les 11 événements du cluster 14:00
et comparer avec les 9 de MyFxBook
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
print("VÉRIFIER CLUSTER 11.09.2025 à 14:00")
print("=" * 100)
print()

TEST_DATE = '2025-09-11'

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# CHARGER ÉVÉNEMENTS DU CLUSTER 14:00
# ============================================================================

query = """
SELECT 
    e.event_key,
    e.event_title,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.importance_n,
    ef.empirical_score,
    ef.family
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND DATE_TRUNC('hour', e.ts_utc) = TIMESTAMP '2025-09-11 14:00:00'
    AND e.country = 'US'
    AND ef.empirical_score > 40
ORDER BY e.ts_utc, e.event_key
"""

df = conn.execute(query, [TEST_DATE]).fetchdf()

conn.close()

print(f"✅ {len(df)} événements dans cluster 14:00\n")

# ============================================================================
# AFFICHER ÉVÉNEMENTS
# ============================================================================

print("=" * 100)
print("ÉVÉNEMENTS DU CLUSTER 14:00")
print("=" * 100)
print()

for idx, event in df.iterrows():
    name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
    score = f"{event['empirical_score']:.1f}" if pd.notna(event['empirical_score']) else "NULL"
    actual = f"{event['actual']:.2f}" if pd.notna(event['actual']) else "NaN"
    estimate = f"{event['estimate']:.2f}" if pd.notna(event['estimate']) else "NaN"
    
    imp_label = {1: "H", 2: "M", 3: "L"}.get(event['importance_n'], "?")
    
    print(f"{idx+1:2d}. {name:45s} | {event['ts_utc']} | Imp={imp_label} | "
          f"Score={score:>6s} | Family={event['family']:15s}")
    print(f"    Actual={actual:>8s}, Estimate={estimate:>8s}")
    print()

# ============================================================================
# COMPARAISON MYFXBOOK
# ============================================================================

print("=" * 100)
print("COMPARAISON MYFXBOOK (9 événements à 13:30)")
print("=" * 100)
print()

MYFXBOOK_EVENTS = [
    "Réclamations Continues des Sans-Employ",
    "Revendications chômage initiales",
    "Demandes de chômage, moyenne sur 4 semaines",
    "Taux D'Inflation De Base (Mensuel)",
    "IPC de",
    "IPC finale",
    "Taux d'inflation (mensuel)",
    "Taux D'Inflation (Annuel)",
    "Taux D'Inflation De Base (Annuel)"
]

print("MyFxBook liste 9 événements HIGH à 13:30 (= 14:30 heure d'été) :")
for i, name in enumerate(MYFXBOOK_EVENTS, 1):
    print(f"  {i}. {name}")

print()
print(f"DB cluster 14:00 : {len(df)} événements")
print(f"MyFxBook 13:30   : {len(MYFXBOOK_EVENTS)} événements")
print()

if len(df) > len(MYFXBOOK_EVENTS):
    print(f"⚠️  {len(df) - len(MYFXBOOK_EVENTS)} événements en trop dans DB !")
    print()
    print("CAUSES POSSIBLES :")
    print("  1. Doublons (MoM/YoY variants)")
    print("  2. Événements à d'autres minutes (14:00, 14:15, etc.)")
    print("  3. Événements avec score > 40 mais importance != HIGH")
elif len(df) < len(MYFXBOOK_EVENTS):
    print(f"❌ {len(MYFXBOOK_EVENTS) - len(df)} événements manquants !")
else:
    print("✅ Nombre correct !")

print()
print("=" * 100)
