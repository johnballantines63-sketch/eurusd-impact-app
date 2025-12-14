#!/usr/bin/env python3
"""
Diagnostic: Pourquoi les stats ne sont pas enregistrées ?
"""

import sys
from pathlib import Path
import duckdb

project_root = Path(__file__).parent
src_path = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path

DB_PATH = get_db_path()

print("=" * 80)
print("DIAGNOSTIC STRUCTURE TABLE event_families")
print("=" * 80)
print()

conn = duckdb.connect(DB_PATH, read_only=True)

# 1. Structure table
print("📋 Structure de la table :")
print("-" * 80)
schema = conn.execute("DESCRIBE event_families").fetchall()
for col in schema:
    print(f"  {col[0]:<30} {col[1]}")

print()

# 2. Échantillon de données
print("📊 Échantillon de données (5 premières lignes) :")
print("-" * 80)
query = """
SELECT family, event_key, country, latency_median, mfe_p80
FROM event_families
LIMIT 5
"""
sample = conn.execute(query).fetchall()
for row in sample:
    print(f"  family={row[0]}, event_key={row[1]}, country={row[2]}, lat={row[3]}, mfe={row[4]}")

print()

# 3. Compter familles distinctes
print("📈 Familles distinctes dans la table :")
print("-" * 80)
query = "SELECT COUNT(DISTINCT family) as n FROM event_families"
count = conn.execute(query).fetchone()[0]
print(f"  Total familles distinctes : {count}")

print()

# 4. Vérifier si UPDATE a fonctionné
print("🔍 Familles avec latency_median NOT NULL :")
print("-" * 80)
query = """
SELECT family, COUNT(*) as n_rows, 
       MIN(latency_median) as min_lat, 
       MAX(latency_median) as max_lat
FROM event_families
WHERE latency_median IS NOT NULL
GROUP BY family
"""
results = conn.execute(query).fetchall()

if results:
    for row in results:
        print(f"  ✅ {row[0]}: {row[1]} lignes, lat={row[2]:.1f}-{row[3]:.1f}min")
else:
    print("  ❌ Aucune famille avec latency_median !")
    print()
    print("  🔍 PROBLÈME IDENTIFIÉ :")
    print("     Le UPDATE ne fonctionne pas correctement")

print()

# 5. Vérifier clé primaire
print("🔑 Clé(s) de la table :")
print("-" * 80)
query = """
SELECT column_name 
FROM information_schema.key_column_usage 
WHERE table_name = 'event_families'
"""
try:
    keys = conn.execute(query).fetchall()
    if keys:
        for key in keys:
            print(f"  Clé : {key[0]}")
    else:
        print("  Pas de clé primaire définie")
except:
    print("  Impossible de déterminer (requête non supportée)")

print()

# 6. Exemple de famille pour debug
print("🔬 Exemple détaillé : famille 'CPI' :")
print("-" * 80)
query = """
SELECT family, event_key, country, latency_median, ttr_median, mfe_p80, n_events_latency
FROM event_families
WHERE family = 'CPI'
LIMIT 3
"""
cpi = conn.execute(query).fetchall()
for row in cpi:
    print(f"  family={row[0]}, event_key={row[1]}, country={row[2]}")
    print(f"    lat={row[3]}, ttr={row[4]}, mfe={row[5]}, n={row[6]}")

conn.close()

print()
print("=" * 80)
print("ANALYSE")
print("=" * 80)
print()
print("La table event_families semble avoir une structure :")
print("  - family (nom famille)")
print("  - event_key (événement spécifique)")
print("  - country (pays)")
print()
print("⚠️  HYPOTHÈSE : Il y a PLUSIEURS lignes par famille (une par event_key)")
print("     Le UPDATE sur 'WHERE family = X' met à jour TOUTES ces lignes")
print()
print("💡 SOLUTION : Vérifier que l'UPDATE fonctionne en mode READ-WRITE")
print()
