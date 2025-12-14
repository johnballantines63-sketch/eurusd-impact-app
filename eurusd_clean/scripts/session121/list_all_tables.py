#!/usr/bin/env python3
"""
Lister TOUTES les tables de la DB et leurs structures
"""

import duckdb

db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'

conn = duckdb.connect(db_path, read_only=True)

print("="*80)
print("TOUTES LES TABLES DANS warehouse.duckdb")
print("="*80 + "\n")

# Lister toutes les tables
query_tables = "SHOW TABLES"
tables = conn.execute(query_tables).df()

print(f"Nombre de tables : {len(tables)}\n")

for _, row in tables.iterrows():
    table_name = row['name']
    
    # Compter rows
    try:
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        count = conn.execute(count_query).fetchone()[0]
    except:
        count = "?"
    
    print(f"📊 {table_name:30s} ({count:>7} rows)")
    
    # Si c'est events ou une table avec "event" dans le nom, montrer structure
    if 'event' in table_name.lower():
        try:
            struct_query = f"DESCRIBE {table_name}"
            struct = conn.execute(struct_query).df()
            print(f"   Colonnes : {', '.join(struct['column_name'].tolist())}")
        except:
            pass
    
    print()

conn.close()

print("="*80)
