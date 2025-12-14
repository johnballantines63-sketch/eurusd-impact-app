#!/usr/bin/env python3
"""
VÉRIFIER IMPORTANCE DES JOBLESS CLAIMS
=======================================

Chercher les événements de chômage du 11.09.2025
et voir leur importance_n réelle
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
print("VÉRIFICATION IMPORTANCE - JOBLESS CLAIMS 11.09.2025")
print("=" * 100)
print()

TEST_DATE = '2025-09-11'

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# CHERCHER TOUS LES ÉVÉNEMENTS US (SANS FILTRE IMPORTANCE)
# ============================================================================

query = """
SELECT 
    e.event_key,
    e.event_title,
    e.actual,
    e.estimate,
    e.ts_utc,
    e.importance_n,
    ef.empirical_score,
    ef.family
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
ORDER BY e.importance_n DESC, e.ts_utc, e.event_key
"""

df = conn.execute(query, [TEST_DATE]).fetchdf()

print(f"✅ {len(df)} événements US trouvés (toutes importances)\n")

# ============================================================================
# AFFICHER PAR NIVEAU D'IMPORTANCE
# ============================================================================

print("=" * 100)
print("ÉVÉNEMENTS PAR IMPORTANCE")
print("=" * 100)
print()

for importance_n in [1, 2, 3]:
    label = {1: "HIGH", 2: "MEDIUM", 3: "LOW"}.get(importance_n, "UNKNOWN")
    df_imp = df[df['importance_n'] == importance_n]
    
    print(f"\n{'='*100}")
    print(f"IMPORTANCE {importance_n} ({label}) : {len(df_imp)} événements")
    print(f"{'='*100}\n")
    
    if len(df_imp) == 0:
        print("  (aucun événement)\n")
        continue
    
    for idx, event in df_imp.iterrows():
        name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
        score = f"{event['empirical_score']:.1f}" if pd.notna(event['empirical_score']) else "NULL"
        family = event['family'] if pd.notna(event['family']) else "NULL"
        
        actual = f"{event['actual']:.2f}" if pd.notna(event['actual']) else "NaN"
        estimate = f"{event['estimate']:.2f}" if pd.notna(event['estimate']) else "NaN"
        
        # Marquer si c'est jobless claims
        is_jobless = "jobless" in event['event_key'].lower() or "claims" in event['event_key'].lower()
        marker = "🎯" if is_jobless else "  "
        
        print(f"{marker} {name:45s} | Imp={importance_n} | Score={score:>6s} | "
              f"Family={family:15s}")

# ============================================================================
# CHERCHER SPÉCIFIQUEMENT JOBLESS CLAIMS
# ============================================================================

print(f"\n{'='*100}")
print("RECHERCHE SPÉCIFIQUE : JOBLESS CLAIMS")
print(f"{'='*100}\n")

jobless_events = df[
    df['event_key'].str.contains('jobless|claims|unemployment', case=False, na=False)
]

print(f"Trouvé {len(jobless_events)} événements contenant 'jobless', 'claims' ou 'unemployment'\n")

if len(jobless_events) > 0:
    for idx, event in jobless_events.iterrows():
        name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
        imp_label = {1: "HIGH", 2: "MEDIUM", 3: "LOW"}.get(event['importance_n'], "UNKNOWN")
        score = f"{event['empirical_score']:.1f}" if pd.notna(event['empirical_score']) else "NULL"
        
        print(f"  📌 {name:45s}")
        print(f"     event_key      : {event['event_key']}")
        print(f"     importance_n   : {event['importance_n']} ({imp_label})")
        print(f"     empirical_score: {score}")
        print(f"     actual         : {event['actual']}")
        print(f"     estimate       : {event['estimate']}")
        print()
else:
    print("❌ AUCUN événement jobless/claims trouvé !")
    print()
    print("HYPOTHÈSES :")
    print("  1. Événements pas dans la DB pour cette date")
    print("  2. Noms différents dans DB vs MyFxBook")
    print("  3. Filtre pays incorrect")

conn.close()

print()
print("=" * 100)
print("CONCLUSION")
print("=" * 100)
print()

print("Si jobless claims trouvés MAIS importance_n != 1 :")
print("  → Le filtre `importance_n = 1` les exclut à tort")
print("  → MyFxBook les considère HIGH mais eodhd non")
print("  → SOLUTION : Utiliser `empirical_score > 40` comme filtre principal")
print()

print("Si jobless claims PAS trouvés du tout :")
print("  → Données manquantes dans DB pour cette date")
print("  → Import incomplet depuis eodhd")
