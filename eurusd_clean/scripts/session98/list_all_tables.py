"""
Liste toutes les tables de la base de données
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "app" / "data" / "warehouse.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("=" * 80)
print("TABLES DISPONIBLES")
print("=" * 80)

tables = conn.execute("SHOW TABLES").df()
print(tables.to_string(index=False))

print("\n" + "=" * 80)
print("DÉTAIL CHAQUE TABLE")
print("=" * 80)

for table_name in tables['name']:
    print(f"\n{'='*80}")
    print(f"TABLE: {table_name}")
    print(f"{'='*80}")
    
    # Schéma
    schema = conn.execute(f"DESCRIBE {table_name}").df()
    print(schema.to_string(index=False))
    
    # Nombre de lignes
    count = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()[0]
    print(f"\n📊 Nombre de lignes: {count:,}")

conn.close()
