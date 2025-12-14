import duckdb
from pathlib import Path

db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")
conn = duckdb.connect(str(db_path))

print("=" * 80)
print("📊 STRUCTURE BASE DE DONNÉES")
print("=" * 80)

# Lister toutes les tables
print("\n🗂️  TABLES DISPONIBLES :")
print("-" * 80)
tables = conn.execute("SHOW TABLES").fetchall()
for table in tables:
    print(f"  ✅ {table[0]}")

# Pour chaque table, montrer quelques colonnes
print("\n\n📋 STRUCTURE DES TABLES :")
print("-" * 80)

for table in tables:
    table_name = table[0]
    print(f"\n📊 {table_name}")
    print("-" * 40)
    try:
        cols = conn.execute(f"DESCRIBE {table_name}").fetchall()
        for col in cols[:10]:  # Première 10 colonnes
            print(f"   • {col[0]:<30} {col[1]}")
        if len(cols) > 10:
            print(f"   ... et {len(cols) - 10} autres colonnes")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

# Compter les lignes
print("\n\n📈 NOMBRE DE LIGNES PAR TABLE :")
print("-" * 80)
for table in tables:
    table_name = table[0]
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"   {table_name:<30} : {count:>8} lignes")
    except Exception as e:
        print(f"   {table_name:<30} : ❌ Erreur")

conn.close()
print("\n" + "=" * 80)
