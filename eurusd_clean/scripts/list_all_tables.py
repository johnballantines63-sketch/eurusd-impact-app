#!/usr/bin/env python3
"""Lister TOUTES les tables dans warehouse.duckdb"""

import duckdb

db_path = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb"
conn = duckdb.connect(db_path, read_only=True)

print("=" * 70)
print("TOUTES LES TABLES DANS warehouse.duckdb")
print("=" * 70)

# Liste des tables
tables = conn.execute("SHOW TABLES").fetchdf()
print(f"\nNombre de tables : {len(tables)}")
print(tables)

# Pour chaque table, afficher le count
print("\n" + "=" * 70)
print("NOMBRE DE LIGNES PAR TABLE")
print("=" * 70)

for table_name in tables['name']:
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"{table_name:40} {count:>12,} lignes")
        
        # Si la table contient "event" ou "calendar" ou "score", montrer aperçu
        if any(keyword in table_name.lower() for keyword in ['event', 'calendar', 'score', 'family']):
            print(f"  → Colonnes: {conn.execute(f'DESCRIBE {table_name}').fetchdf()['column_name'].tolist()}")
    except Exception as e:
        print(f"{table_name:40} ❌ Erreur: {e}")

conn.close()
