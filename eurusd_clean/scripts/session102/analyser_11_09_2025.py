#!/usr/bin/env python3
"""
ANALYSE DÉDUPLICATION 11.09.2025
=================================

MyFxBook liste 9 événements HIGH :
1. Réclamations Continues des Sans-Employ
2. Revendications chômage initiales
3. Demandes de chômage, moyenne sur 4 semaines
4. Taux D'Inflation De Base (Mensuel)
5. IPC de
6. IPC finale
7. Taux d'inflation (mensuel)
8. Taux D'Inflation (Annuel)
9. Taux D'Inflation De Base (Annuel)

DB après dédup : 7 événements

→ Il MANQUE 2 événements !
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
print("ANALYSE DÉDUPLICATION 11.09.2025")
print("=" * 100)
print()

# ============================================================================
# CHARGER TOUS LES ÉVÉNEMENTS (AVANT FILTRE score > 40)
# ============================================================================

TEST_DATE = '2025-09-11'

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# D'ABORD : Tous les événements US HIGH (sans filtre score)
query_all = """
SELECT 
    e.event_key,
    e.event_title,
    e.actual,
    e.estimate,
    e.ts_utc,
    ef.empirical_score,
    ef.family,
    e.importance_n
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
    AND e.importance_n = 1
ORDER BY e.ts_utc, e.event_key
"""

df_all = conn.execute(query_all, [TEST_DATE]).fetchdf()

print(f"✅ {len(df_all)} événements US HIGH (tous)\n")

# ENSUITE : Avec filtre score > 40
query_filtered = """
SELECT 
    e.event_key,
    e.event_title,
    e.actual,
    e.estimate,
    e.ts_utc,
    ef.empirical_score,
    ef.family
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
    AND ef.empirical_score > 40
ORDER BY e.ts_utc, e.event_key
"""

df_filtered = conn.execute(query_filtered, [TEST_DATE]).fetchdf()

print(f"✅ {len(df_filtered)} événements avec score > 40\n")

# ============================================================================
# AFFICHER TOUS LES ÉVÉNEMENTS HIGH
# ============================================================================

print("=" * 100)
print("TOUS LES ÉVÉNEMENTS US HIGH (11.09.2025)")
print("=" * 100)
print()

for idx, event in df_all.iterrows():
    name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
    score = f"{event['empirical_score']:.1f}" if pd.notna(event['empirical_score']) else "NULL"
    filtered = "✅" if pd.notna(event['empirical_score']) and event['empirical_score'] > 40 else "❌"
    
    actual = f"{event['actual']:.2f}" if pd.notna(event['actual']) else "NaN"
    estimate = f"{event['estimate']:.2f}" if pd.notna(event['estimate']) else "NaN"
    
    print(f"{filtered} {idx+1:2d}. {name:40s} | Score: {score:>6s} | "
          f"Actual: {actual:>8s} | Est: {estimate:>8s}")

print()

# ============================================================================
# DÉDUPLICATION SUR ÉVÉNEMENTS FILTRÉS
# ============================================================================

print("=" * 100)
print("DÉDUPLICATION (score > 40)")
print("=" * 100)
print()

print(f"Avant déduplication : {len(df_filtered)} événements\n")

# Déduplication
df_filtered['dedup_key'] = (
    df_filtered['family'].astype(str) + '_' +
    df_filtered['actual'].astype(str) + '_' +
    df_filtered['estimate'].astype(str) + '_' +
    df_filtered['ts_utc'].astype(str)
)

unique_events = []

for key, group in df_filtered.groupby('dedup_key'):
    if len(group) == 1:
        unique_events.append(group.iloc[0])
    else:
        with_title = group[group['event_title'].notna()]
        if len(with_title) > 0:
            unique_events.append(with_title.iloc[0])
        else:
            unique_events.append(group.iloc[0])

df_deduplicated = pd.DataFrame(unique_events)

print(f"Après déduplication : {len(df_deduplicated)} événements\n")

print("Événements restants :")
for idx, event in df_deduplicated.iterrows():
    name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
    print(f"  {idx+1}. {name:40s} | Family: {event['family']}")

print()

# ============================================================================
# COMPARAISON MYFXBOOK
# ============================================================================

print("=" * 100)
print("COMPARAISON MYFXBOOK")
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

print(f"MyFxBook : {len(MYFXBOOK_EVENTS)} événements")
print(f"DB dédup : {len(df_deduplicated)} événements")
print()

if len(df_deduplicated) < len(MYFXBOOK_EVENTS):
    missing = len(MYFXBOOK_EVENTS) - len(df_deduplicated)
    print(f"❌ Il MANQUE {missing} événements après déduplication !")
    print()
    print("HYPOTHÈSES :")
    print("  1. Certains événements ont score <= 40 (filtrés)")
    print("  2. Déduplication trop agressive (supprime des vrais événements distincts)")
    print("  3. Données manquantes dans event_families")

conn.close()

print()
print("=" * 100)
