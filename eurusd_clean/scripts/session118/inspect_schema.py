"""
Script pour inspecter le schéma de la table events
"""
import duckdb
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
warehouse_path = project_root / 'data' / 'warehouse.duckdb'

conn = duckdb.connect(str(warehouse_path), read_only=True)

print("=" * 80)
print("INSPECTION SCHÉMA TABLE EVENTS")
print("=" * 80)

# Lister toutes les tables
print("\n📋 Tables disponibles:")
tables = conn.execute("SHOW TABLES").df()
print(tables)

# Schéma de la table events
print("\n📋 Colonnes table 'events':")
try:
    schema = conn.execute("DESCRIBE events").df()
    print(schema)
except Exception as e:
    print(f"❌ Erreur: {e}")

# Quelques exemples de lignes
print("\n📋 Exemple de lignes (5 premières):")
try:
    sample = conn.execute("SELECT * FROM events LIMIT 5").df()
    print(sample.columns.tolist())
    print(sample.head())
except Exception as e:
    print(f"❌ Erreur: {e}")

conn.close()
