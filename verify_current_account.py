#!/usr/bin/env python3
"""
Vérification rapide : Comment Current Account est stocké dans la DB ?
"""

import sys
from pathlib import Path
import duckdb

# Setup path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

from config import get_db_path

db_path = get_db_path()
print("="*70)
print("🔍 RECHERCHE CURRENT ACCOUNT DANS LA DB")
print("="*70)
print(f"\n📁 DB: {db_path}\n")

conn = duckdb.connect(db_path, read_only=True)

# Chercher toutes les variantes possibles
print("1️⃣ RECHERCHE AVEC LIKE '%current%account%'")
print("-"*70)
query = """
SELECT DISTINCT family, latency_median, ttr_median, mfe_p80, n_events_latency
FROM event_families
WHERE LOWER(family) LIKE '%current%account%' OR LOWER(family) LIKE '%account%current%'
"""
results = conn.execute(query).fetchall()

if results:
    print(f"✅ Trouvé {len(results)} résultat(s) :\n")
    for family, lat, ttr, mfe, n_events in results:
        status = "✅ PRÉ-CALCULÉ" if lat is not None else "❌ PAS PRÉ-CALCULÉ"
        print(f"  {status}")
        print(f"  Nom exact : '{family}'")
        print(f"  - latency_median: {lat}")
        print(f"  - ttr_median: {ttr}")
        print(f"  - mfe_p80: {mfe}")
        print(f"  - n_events: {n_events}")
        print()
else:
    print("❌ AUCUN résultat trouvé\n")

print("\n2️⃣ RECHERCHE EXACTE DES VARIANTES")
print("-"*70)
variants = ['Current Account', 'Current_Account', 'CURRENT_ACCOUNT', 'current_account']
for variant in variants:
    query = f"SELECT COUNT(*) FROM event_families WHERE family = '{variant}'"
    count = conn.execute(query).fetchone()[0]
    if count > 0:
        print(f"  ✅ '{variant}' : {count} ligne(s)")
    else:
        print(f"  ❌ '{variant}' : 0 ligne")

print("\n\n3️⃣ TOUTES LES FAMILLES DANS LA DB")
print("-"*70)
query = "SELECT DISTINCT family FROM event_families ORDER BY family"
all_families = conn.execute(query).fetchall()
print(f"Total: {len(all_families)} familles distinctes\n")

# Chercher celles qui contiennent un espace
families_with_space = [f[0] for f in all_families if ' ' in f[0]]
families_with_underscore = [f[0] for f in all_families if '_' in f[0]]

print(f"📊 Familles avec ESPACE     : {len(families_with_space)}")
if families_with_space:
    for f in families_with_space[:5]:
        print(f"     - '{f}'")
    if len(families_with_space) > 5:
        print(f"     ... et {len(families_with_space) - 5} autres")

print(f"\n📊 Familles avec UNDERSCORE : {len(families_with_underscore)}")
if families_with_underscore:
    for f in families_with_underscore[:5]:
        print(f"     - '{f}'")
    if len(families_with_underscore) > 5:
        print(f"     ... et {len(families_with_underscore) - 5} autres")

conn.close()

print("\n" + "="*70)
print("✅ VÉRIFICATION TERMINÉE")
print("="*70)
