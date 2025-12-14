#!/usr/bin/env python3
"""
CHERCHER JOBLESS CLAIMS 11.09.2025
===================================

Chercher TOUS les événements jobless/claims/unemployment
SANS filtre score, pour voir s'ils existent dans DB
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
print("CHERCHER JOBLESS CLAIMS 11.09.2025")
print("=" * 100)
print()

TEST_DATE = '2025-09-11'

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# CHERCHER TOUS LES ÉVÉNEMENTS US (SANS FILTRE)
# ============================================================================

query_all = """
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
    AND e.country = 'US'
ORDER BY e.ts_utc, e.event_key
"""

df_all = conn.execute(query_all, [TEST_DATE]).fetchdf()

print(f"✅ {len(df_all)} événements US trouvés (tous)\n")

# ============================================================================
# FILTRER JOBLESS CLAIMS
# ============================================================================

# Recherche par mots-clés
jobless_keywords = ['jobless', 'claims', 'unemployment', 'initial', 'continuing', 'chômage']

df_jobless = df_all[
    df_all['event_key'].str.contains('|'.join(jobless_keywords), case=False, na=False) |
    df_all['event_title'].str.contains('|'.join(jobless_keywords), case=False, na=False)
]

print("=" * 100)
print(f"ÉVÉNEMENTS JOBLESS/CLAIMS/UNEMPLOYMENT : {len(df_jobless)}")
print("=" * 100)
print()

if len(df_jobless) == 0:
    print("❌ AUCUN événement jobless claims trouvé dans la DB !")
    print()
    print("CONCLUSION :")
    print("  → Les jobless claims ne sont PAS dans la DB pour cette date")
    print("  → Import incomplet depuis eodhd")
    print("  → Données manquantes")
else:
    for idx, event in df_jobless.iterrows():
        name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
        score = f"{event['empirical_score']:.1f}" if pd.notna(event['empirical_score']) else "NULL"
        imp_label = {1: "HIGH", 2: "MEDIUM", 3: "LOW"}.get(event['importance_n'], "NULL")
        
        actual = f"{event['actual']:.2f}" if pd.notna(event['actual']) else "NaN"
        estimate = f"{event['estimate']:.2f}" if pd.notna(event['estimate']) else "NaN"
        
        print(f"📌 {name}")
        print(f"   event_key      : {event['event_key']}")
        print(f"   ts_utc         : {event['ts_utc']}")
        print(f"   importance_n   : {event['importance_n']} ({imp_label})")
        print(f"   empirical_score: {score}")
        print(f"   family         : {event['family']}")
        print(f"   actual         : {actual}")
        print(f"   estimate       : {estimate}")
        print()
        
        # Analyser pourquoi filtré
        if pd.isna(event['empirical_score']):
            print(f"   ❌ FILTRÉ : empirical_score = NULL")
            print(f"      → Pas dans event_families !")
        elif event['empirical_score'] <= 40:
            print(f"   ❌ FILTRÉ : empirical_score = {event['empirical_score']:.1f} <= 40")
            print(f"      → Score trop faible !")
        else:
            print(f"   ✅ DEVRAIT ÊTRE INCLUS (score={event['empirical_score']:.1f} > 40)")
        print()

# ============================================================================
# VÉRIFIER event_families POUR JOBLESS
# ============================================================================

print("=" * 100)
print("VÉRIFICATION event_families")
print("=" * 100)
print()

query_families = """
SELECT 
    event_key,
    country,
    family,
    empirical_score
FROM event_families
WHERE country = 'US'
    AND (
        event_key LIKE '%jobless%' 
        OR event_key LIKE '%claims%' 
        OR event_key LIKE '%unemployment%'
    )
ORDER BY empirical_score DESC
"""

df_families = conn.execute(query_families).fetchdf()

if len(df_families) == 0:
    print("❌ AUCUN jobless claims dans event_families !")
    print()
    print("PROBLÈME CRITIQUE :")
    print("  → Les jobless claims n'ont PAS de empirical_score calculé")
    print("  → Ils ne peuvent donc PAS être sélectionnés avec score > 40")
    print()
    print("SOLUTION :")
    print("  1. Recalculer empirical_score pour jobless claims")
    print("  2. OU utiliser importance_n = 1 (HIGH) comme filtre alternatif")
else:
    print(f"✅ {len(df_families)} familles jobless/claims/unemployment dans event_families :")
    print()
    for idx, row in df_families.iterrows():
        print(f"  {row['event_key']:40s} | Score: {row['empirical_score']:.1f} | Family: {row['family']}")

conn.close()

print()
print("=" * 100)
