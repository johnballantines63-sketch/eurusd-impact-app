"""
Liste Tables Backup
===================

Voir quelles tables existent dans le backup pour trouver les events
"""

import duckdb
from pathlib import Path

DB_BACKUP = Path(__file__).parent.parent / 'session123' / 'backups' / 'warehouse_backup_20251109_201627.duckdb'

print("\n" + "="*80)
print("TABLES DISPONIBLES DANS BACKUP")
print("="*80)
print()

conn = duckdb.connect(str(DB_BACKUP), read_only=True)

tables = conn.execute("SHOW TABLES").df()

print(f"Nombre de tables: {len(tables)}")
print()

for _, row in tables.iterrows():
    table_name = row['name']
    
    # Compter rows
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"   {table_name:30s} : {count:,} rows")
    except:
        print(f"   {table_name:30s} : (erreur count)")

print()
print("="*80)
print("RECHERCHE TABLE EVENTS")
print("="*80)
print()

# Chercher tables avec "event" dans le nom
event_tables = [row['name'] for _, row in tables.iterrows() if 'event' in row['name'].lower()]

print(f"Tables contenant 'event': {len(event_tables)}")
for table in event_tables:
    print(f"   - {table}")
    
    # Montrer structure
    try:
        cols = conn.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
        """).df()
        
        print(f"     Colonnes:")
        for _, col in cols.iterrows():
            print(f"        {col['column_name']:20s} : {col['data_type']}")
        
        # Échantillon
        sample = conn.execute(f"SELECT * FROM {table} LIMIT 1").df()
        if len(sample) > 0:
            print(f"     Échantillon colonnes: {sample.columns.tolist()}")
        
        print()
    except Exception as e:
        print(f"     ❌ Erreur: {e}")
        print()

conn.close()
