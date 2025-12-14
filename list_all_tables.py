#!/usr/bin/env python3
"""Liste toutes les tables disponibles"""

import duckdb

con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("=" * 70)
print("TABLES DISPONIBLES DANS LA BASE")
print("=" * 70)

query = "SHOW TABLES"
tables = con.execute(query).df()

print(f"\nNombre de tables: {len(tables)}")
print("\nListe des tables:")
for idx, row in tables.iterrows():
    table_name = row['name']
    
    # Compter lignes
    count_query = f"SELECT COUNT(*) as cnt FROM {table_name}"
    try:
        count = con.execute(count_query).fetchone()[0]
        print(f"  - {table_name:<30} ({count:>10,} lignes)")
    except:
        print(f"  - {table_name:<30} (erreur comptage)")

print("\n" + "=" * 70)
print("TABLES CONTENANT 'IMPACT' OU 'GROUP'")
print("=" * 70)

impact_tables = [row['name'] for _, row in tables.iterrows() 
                 if 'impact' in row['name'].lower() or 'group' in row['name'].lower()]

for table in impact_tables:
    print(f"\n📊 Table: {table}")
    desc_query = f"DESCRIBE {table}"
    desc = con.execute(desc_query).df()
    print(desc[['column_name', 'column_type']].to_string(index=False))

con.close()
