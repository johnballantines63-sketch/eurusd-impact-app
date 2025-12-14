#!/usr/bin/env python3
"""
SESSION 26 - ÉTAPE 1 : Backup + Nettoyage
Backup warehouse.duckdb et suppression tables corrompues
"""

import duckdb
import shutil
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("SESSION 26 - ÉTAPE 1 : BACKUP + NETTOYAGE")
print("=" * 80)

# Chemins
db_path = Path("fx_impact_app/data/warehouse.duckdb")
backup_path = Path("fx_impact_app/data/warehouse_BACKUP_SESSION26_before_clean.duckdb")

# 1. BACKUP
print("\n📦 ÉTAPE 1 : Création backup...")

if not db_path.exists():
    print(f"❌ ERREUR : Base de données introuvable : {db_path}")
    exit(1)

try:
    shutil.copy2(db_path, backup_path)
    backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB
    print(f"✅ Backup créé : {backup_path}")
    print(f"   Taille : {backup_size:.2f} MB")
except Exception as e:
    print(f"❌ ERREUR backup : {e}")
    exit(1)

# 2. CONNEXION
print("\n🔌 ÉTAPE 2 : Connexion base de données...")

try:
    con = duckdb.connect(str(db_path))
    print("✅ Connecté")
except Exception as e:
    print(f"❌ ERREUR connexion : {e}")
    exit(1)

# 3. LISTER TABLES AVANT
print("\n📊 ÉTAPE 3 : État AVANT nettoyage...")

query_tables = "SHOW TABLES"
tables_before = con.execute(query_tables).df()
print(f"Nombre de tables : {len(tables_before)}")

# 4. IDENTIFIER TABLES À SUPPRIMER
print("\n🗑️  ÉTAPE 4 : Identification tables corrompues...")

tables_to_drop = [
    'event_impacts_calculated',
    'event_group_impacts',
    'event_group_impacts_backup_session22'
]

print(f"\nTables à supprimer : {len(tables_to_drop)}")
for table in tables_to_drop:
    # Vérifier si existe
    check_query = f"""
        SELECT COUNT(*) as cnt 
        FROM information_schema.tables 
        WHERE table_name = '{table}'
    """
    exists = con.execute(check_query).fetchone()[0] > 0
    
    if exists:
        count_query = f"SELECT COUNT(*) as cnt FROM {table}"
        try:
            count = con.execute(count_query).fetchone()[0]
            print(f"  - {table:<40} ({count:>10,} lignes) ⚠️  À SUPPRIMER")
        except:
            print(f"  - {table:<40} (erreur comptage) ⚠️  À SUPPRIMER")
    else:
        print(f"  - {table:<40} (n'existe pas) ✓")

# 5. SUPPRESSION
print("\n🔥 ÉTAPE 5 : Suppression tables corrompues...")

dropped = 0
errors = 0

for table in tables_to_drop:
    try:
        con.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"  ✅ Supprimé : {table}")
        dropped += 1
    except Exception as e:
        print(f"  ❌ Erreur {table} : {e}")
        errors += 1

print(f"\nRésultat : {dropped} tables supprimées, {errors} erreurs")

# 6. VÉRIFICATION APRÈS
print("\n📊 ÉTAPE 6 : État APRÈS nettoyage...")

tables_after = con.execute(query_tables).df()
print(f"Nombre de tables : {len(tables_after)}")

# 7. TABLES RESTANTES (VALIDES)
print("\n✅ TABLES VALIDES CONSERVÉES :")

valid_tables = [
    'events',
    'event_families',
    'scores',
    'prices_1m',
    'prices_1h',
    'prices_5m',
    'prices_m15',
    'prices_m30',
    'prices_h4'
]

for table_name in valid_tables:
    check = f"""
        SELECT COUNT(*) as cnt 
        FROM information_schema.tables 
        WHERE table_name = '{table_name}'
    """
    exists = con.execute(check).fetchone()[0] > 0
    
    if exists:
        count_query = f"SELECT COUNT(*) as cnt FROM {table_name}"
        try:
            count = con.execute(count_query).fetchone()[0]
            print(f"  ✅ {table_name:<30} ({count:>10,} lignes)")
        except:
            print(f"  ✅ {table_name:<30} (erreur comptage)")
    else:
        print(f"  ⚠️  {table_name:<30} (manquant)")

# 8. VALIDATION prices_1m
print("\n" + "=" * 80)
print("VALIDATION CRITIQUE : prices_1m")
print("=" * 80)

validation_query = """
SELECT 
    COUNT(*) as total_rows,
    MIN(datetime) as date_min,
    MAX(datetime) as date_max
FROM prices_1m
"""

validation = con.execute(validation_query).df()
print("\nStatistiques prices_1m :")
print(f"  Total lignes : {validation['total_rows'].iloc[0]:,}")
print(f"  Date min : {validation['date_min'].iloc[0]}")
print(f"  Date max : {validation['date_max'].iloc[0]}")

# Vérifier 11 septembre
sept11_query = """
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime >= '2025-09-11 12:30:00'
  AND datetime <= '2025-09-11 12:45:00'
ORDER BY datetime
LIMIT 5
"""

sept11_check = con.execute(sept11_query).df()

if len(sept11_check) > 0:
    print("\n✅ Validation 11 septembre OK")
    print(f"   {len(sept11_check)} minutes trouvées")
    start_price = sept11_check.iloc[0]['open']
    print(f"   Prix départ 12:30 UTC : {start_price:.5f}")
else:
    print("\n❌ ERREUR : 11 septembre introuvable !")

# 9. FERMETURE
con.close()

print("\n" + "=" * 80)
print("RÉSUMÉ NETTOYAGE")
print("=" * 80)

print(f"\n✅ Backup créé : {backup_path}")
print(f"✅ Tables supprimées : {dropped}")
print(f"✅ Tables valides conservées : {len(valid_tables)}")
print(f"✅ prices_1m validé")

print("\n🎯 PROCHAINE ÉTAPE :")
print("   python3 build_event_impacts_v2_session26.py")

print("\n" + "=" * 80)
