#!/usr/bin/env python3
"""
AFFICHER LES 8 ÉVÉNEMENTS DU 11.09 (MODE OR)
=============================================

Voir exactement quels événements restent après déduplication
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

TEST_DATE = '2025-09-11'
TEST_HOUR = '2025-09-11 14:00:00'

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# CHARGER ÉVÉNEMENTS (MODE OR)
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
    AND DATE_TRUNC('hour', e.ts_utc) = ?
    AND e.country = 'US'
    AND (
        e.importance_n = 1
        OR ef.empirical_score > 40
    )
ORDER BY e.ts_utc, e.event_key
"""

df = conn.execute(query, [TEST_DATE, pd.Timestamp(TEST_HOUR)]).fetchdf()

print("=" * 100)
print(f"ÉVÉNEMENTS 11.09.2025 AVANT DÉDUP (MODE OR) : {len(df)}")
print("=" * 100)
print()

for idx, event in df.iterrows():
    name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
    score = f"{event['empirical_score']:.1f}" if pd.notna(event['empirical_score']) else "NULL"
    imp = event['importance_n'] if pd.notna(event['importance_n']) else "NULL"
    
    print(f"{idx+1:2d}. {name:45s} | Imp={imp} | Score={score:>6s} | Family={event['family']}")

# ============================================================================
# DÉDUPLICATION
# ============================================================================

df['dedup_key'] = (
    df['family'].astype(str) + '_' +
    df['actual'].astype(str) + '_' +
    df['estimate'].astype(str) + '_' +
    df['ts_utc'].astype(str)
)

unique_events = []

for key, group in df.groupby('dedup_key'):
    if len(group) == 1:
        unique_events.append(group.iloc[0])
    else:
        with_title = group[group['event_title'].notna()]
        if len(with_title) > 0:
            unique_events.append(with_title.iloc[0])
        else:
            unique_events.append(group.iloc[0])

df_dedup = pd.DataFrame(unique_events)

print()
print("=" * 100)
print(f"ÉVÉNEMENTS 11.09.2025 APRÈS DÉDUP : {len(df_dedup)}")
print("=" * 100)
print()

for idx, event in df_dedup.iterrows():
    name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
    score = f"{event['empirical_score']:.1f}" if pd.notna(event['empirical_score']) else "NULL"
    
    actual = f"{event['actual']:.2f}" if pd.notna(event['actual']) else "NaN"
    estimate = f"{event['estimate']:.2f}" if pd.notna(event['estimate']) else "NaN"
    
    print(f"{idx+1}. {name:45s} | Family={event['family']:15s}")
    print(f"   Actual={actual:>8s}, Estimate={estimate:>8s}, Score={score}")
    print()

# ============================================================================
# COMPARER AVEC MYFXBOOK
# ============================================================================

print("=" * 100)
print("COMPARAISON MYFXBOOK")
print("=" * 100)
print()

MYFXBOOK = [
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

print(f"MyFxBook : {len(MYFXBOOK)} événements")
print(f"DB dédup : {len(df_dedup)} événements")
print()

if len(df_dedup) < len(MYFXBOOK):
    print(f"❌ Il manque {len(MYFXBOOK) - len(df_dedup)} événement(s)")
    print()
    print("Événements MyFxBook manquants possibles :")
    print("  - Réclamations Continues ? (continuing jobless claims)")
    print("  - Revendications initiales ? (initial jobless claims)")
    print("  - Moyenne 4 semaines ? (4-week average)")

conn.close()
