"""
SCRIPT D'INSPECTION BASE DE DONNÉES
====================================

Liste toutes les tables et leurs colonnes dans warehouse.duckdb

Usage: python inspect_database.py
"""

import duckdb
from pathlib import Path

# Chemin vers la DB
# Depuis: eurusd_clean/scripts/session111/
# Vers:   eurusd_clean/app/data/warehouse.duckdb
script_dir = Path(__file__).parent  # session111
db_path = script_dir.parent.parent / 'app' / 'data' / 'warehouse.duckdb'

print("="*70)
print("📊 INSPECTION BASE DE DONNÉES - warehouse.duckdb")
print("="*70)

if not db_path.exists():
    print(f"\n❌ ERREUR: {db_path} n'existe pas!")
    exit(1)

print(f"\n✅ Base de données trouvée: {db_path}")

# Connexion
con = duckdb.connect(str(db_path), read_only=True)

# Lister toutes les tables
print("\n" + "="*70)
print("📋 LISTE DES TABLES")
print("="*70)

tables_query = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'main'
ORDER BY table_name
"""

tables = con.execute(tables_query).fetchall()

for table in tables:
    table_name = table[0]
    print(f"\n🔹 Table: {table_name}")
    
    # Obtenir les colonnes de cette table
    columns_query = f"""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'main' AND table_name = '{table_name}'
    ORDER BY ordinal_position
    """
    
    columns = con.execute(columns_query).fetchall()
    
    print("   Colonnes:")
    for col_name, col_type in columns:
        print(f"      - {col_name:30s} ({col_type})")
    
    # Compter les lignes
    try:
        count_query = f"SELECT COUNT(*) FROM {table_name}"
        count = con.execute(count_query).fetchone()[0]
        print(f"   Nombre de lignes: {count:,}")
    except:
        print(f"   Nombre de lignes: (erreur de comptage)")

# Exemples de données pour tables principales
print("\n" + "="*70)
print("📊 EXEMPLES DE DONNÉES (5 premières lignes)")
print("="*70)

important_tables = ['events', 'event_families', 'prices_1m']

for table_name in important_tables:
    if any(t[0] == table_name for t in tables):
        print(f"\n🔹 Table: {table_name}")
        try:
            sample_query = f"SELECT * FROM {table_name} LIMIT 5"
            df = con.execute(sample_query).df()
            print(df.to_string())
        except Exception as e:
            print(f"   Erreur: {e}")

con.close()

print("\n" + "="*70)
print("✅ INSPECTION TERMINÉE")
print("="*70)
