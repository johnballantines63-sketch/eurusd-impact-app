#!/usr/bin/env python3
"""Chercher tables avec scores empiriques"""
import duckdb

DB_PATH = "data/warehouse.duckdb"

conn = duckdb.connect(DB_PATH, read_only=True)

print("=" * 80)
print("RECHERCHE TABLES SCORES")
print("=" * 80)

# Lister toutes les tables
print("\n📋 Tables disponibles :")
tables = conn.execute("SHOW TABLES").fetchall()
for table in tables:
    table_name = table[0]
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"   {table_name:<30s} : {count:>10,} lignes")

print("\n🔍 Tables potentielles pour scores :")
potential_tables = []
for table in tables:
    table_name = table[0]
    if any(keyword in table_name.lower() for keyword in ['score', 'event', 'family', 'empirical']):
        potential_tables.append(table_name)
        print(f"   ✅ {table_name}")
        
        # Afficher structure
        columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        print(f"      Colonnes :")
        for col in columns:
            print(f"         - {col[1]} ({col[2]})")

conn.close()
