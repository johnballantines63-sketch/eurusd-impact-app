#!/usr/bin/env python3
"""
INVESTIGATION : Schéma base de données
"""
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"

print("="*80)
print("INVESTIGATION : SCHÉMA BASE DE DONNÉES")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Lister TOUTES les tables
print("📋 TABLES DISPONIBLES :")
print()

tables = conn.execute("SHOW TABLES").df()

for idx, row in tables.iterrows():
    table_name = row['name']
    count = conn.execute(f"SELECT COUNT(*) as cnt FROM {table_name}").fetchone()[0]
    print(f"   • {table_name:30s} ({count:,} lignes)")

print()

# 2. Chercher tables avec "event" ou "economic"
print("🔍 TABLES CONTENANT 'EVENT' OU 'ECONOMIC' :")
print()

event_tables = [t for t in tables['name'] if 'event' in t.lower() or 'economic' in t.lower()]

if event_tables:
    for table in event_tables:
        print(f"   ✅ {table}")
        
        # Schéma
        schema = conn.execute(f"DESCRIBE {table}").df()
        print(f"      Colonnes : {', '.join(schema['column_name'].tolist())}")
        
        # Échantillon
        sample = conn.execute(f"SELECT * FROM {table} LIMIT 3").df()
        print(f"      Échantillon : {len(sample)} lignes")
        print()
else:
    print("   (aucune)")

print()

# 3. Chercher table prix
print("📊 TABLES PRIX :")
print()

price_tables = [t for t in tables['name'] if 'price' in t.lower()]

for table in price_tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"   • {table:30s} ({count:,} lignes)")

conn.close()

print()
print("="*80)
