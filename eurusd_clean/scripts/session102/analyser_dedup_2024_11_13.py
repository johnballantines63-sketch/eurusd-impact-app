#!/usr/bin/env python3
"""
ANALYSER RÉSULTAT DÉDUPLICATION 2024-11-13
===========================================

Afficher les 7 événements restants pour comprendre
pourquoi il en reste 7 au lieu de 6 (selon MyFxBook)
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
print("ANALYSE DÉDUPLICATION 2024-11-13")
print("=" * 100)
print()

# ============================================================================
# CHARGER ET DÉDUPLIQUER
# ============================================================================

TEST_DATE = '2024-11-13'

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

query = """
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
ORDER BY e.ts_utc
"""

df_events = conn.execute(query, [TEST_DATE]).fetchdf()

print(f"✅ Chargé {len(df_events)} événements AVANT déduplication\n")

# Déduplication (même logique que step1)
df_events['dedup_key'] = (
    df_events['family'].astype(str) + '_' +
    df_events['actual'].astype(str) + '_' +
    df_events['estimate'].astype(str) + '_' +
    df_events['ts_utc'].astype(str)
)

unique_events = []

for key, group in df_events.groupby('dedup_key'):
    if len(group) == 1:
        unique_events.append(group.iloc[0])
    else:
        with_title = group[group['event_title'].notna()]
        if len(with_title) > 0:
            unique_events.append(with_title.iloc[0])
        else:
            unique_events.append(group.iloc[0])

df_deduplicated = pd.DataFrame(unique_events)

print(f"✅ Reste {len(df_deduplicated)} événements APRÈS déduplication\n")

# ============================================================================
# AFFICHER ÉVÉNEMENTS RESTANTS
# ============================================================================

print("=" * 100)
print("ÉVÉNEMENTS APRÈS DÉDUPLICATION")
print("=" * 100)
print()

for idx, event in df_deduplicated.iterrows():
    event_name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
    actual = f"{event['actual']:.2f}" if pd.notna(event['actual']) else "NaN"
    estimate = f"{event['estimate']:.2f}" if pd.notna(event['estimate']) else "NaN"
    
    print(f"{idx+1}. {event_name:30s} | Family: {event['family']:15s} | "
          f"Actual: {actual:>8s} | Estimate: {estimate:>8s}")

print()

# ============================================================================
# COMPARAISON MYFXBOOK
# ============================================================================

print("=" * 100)
print("COMPARAISON AVEC MYFXBOOK (6 ÉVÉNEMENTS)")
print("=" * 100)
print()

MYFXBOOK_EVENTS = [
    "IPC de",
    "IPC finale", 
    "Taux d'inflation (mensuel)",
    "Taux D'Inflation De Base (Mensuel)",
    "Taux D'Inflation De Base (Annuel)",
    "Taux D'Inflation (Annuel)"
]

print("MyFxBook liste :")
for i, name in enumerate(MYFXBOOK_EVENTS, 1):
    print(f"  {i}. {name}")

print()
print(f"DB dédupliquée : {len(df_deduplicated)} événements")
print(f"MyFxBook       : {len(MYFXBOOK_EVENTS)} événements")
print()

if len(df_deduplicated) > len(MYFXBOOK_EVENTS):
    print(f"❌ Il reste {len(df_deduplicated) - len(MYFXBOOK_EVENTS)} événement(s) en trop !")
    print()
    print("Hypothèses :")
    print("  1. MyFxBook ne liste pas tous les événements HIGH")
    print("  2. DB contient des variantes supplémentaires (MoM vs YoY)")
    print("  3. Logique déduplication insuffisante")
elif len(df_deduplicated) < len(MYFXBOOK_EVENTS):
    print(f"⚠️  Il manque {len(MYFXBOOK_EVENTS) - len(df_deduplicated)} événement(s) !")
else:
    print("✅ Nombre correct !")

conn.close()

print()
print("=" * 100)
