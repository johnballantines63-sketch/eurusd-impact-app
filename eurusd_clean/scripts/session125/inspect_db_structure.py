#!/usr/bin/env python3
"""
Inspecter structure DB warehouse.duckdb
"""
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("INSPECTION STRUCTURE DATABASE")
print("="*80)
print()

# Lister toutes les tables
print("📋 Tables disponibles :")
tables = conn.execute("SHOW TABLES").df()
print(tables)
print()

# Inspecter table economic_events
print("="*80)
print("STRUCTURE TABLE: economic_events")
print("="*80)
print()

try:
    schema = conn.execute("DESCRIBE economic_events").df()
    print(schema)
    print()
    
    # Compter lignes
    count = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"📊 Nombre de lignes : {count:,}")
    print()
    
    # Échantillon
    print("📊 Échantillon (5 premières lignes) :")
    sample = conn.execute("SELECT * FROM economic_events LIMIT 5").df()
    print(sample)
    print()
    
except Exception as e:
    print(f"❌ Table economic_events n'existe pas : {e}")
    print()

# Chercher tables avec "event" dans le nom
print("="*80)
print("TABLES CONTENANT 'event' :")
print("="*80)
print()

all_tables = conn.execute("SHOW TABLES").df()
event_tables = all_tables[all_tables['name'].str.contains('event', case=False, na=False)]
print(event_tables)
print()

# Inspecter chaque table event
for table_name in event_tables['name']:
    print(f"="*80)
    print(f"TABLE: {table_name}")
    print(f"="*80)
    
    try:
        schema = conn.execute(f"DESCRIBE {table_name}").df()
        print(schema)
        
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"📊 Lignes : {count:,}")
        print()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        print()

conn.close()
