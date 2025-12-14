#!/usr/bin/env python3
"""
Liste les tables disponibles dans warehouse.duckdb
"""
import duckdb
from pathlib import Path

db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

con = duckdb.connect(str(db_path), read_only=True)

print("="*80)
print("📊 TABLES DISPONIBLES DANS warehouse.duckdb")
print("="*80)

# Lister toutes les tables
tables = con.execute("SHOW TABLES").df()

print(f"\n✅ {len(tables)} table(s) trouvée(s):\n")

for i, row in tables.iterrows():
    table_name = row['name']
    
    # Compter lignes
    try:
        count = con.execute(f"SELECT COUNT(*) as cnt FROM {table_name}").fetchone()[0]
        print(f"{i+1}. {table_name:<30} ({count:,} lignes)")
        
        # Si table contient "price" ou "ohlc" ou "dukascopy", afficher structure
        if any(keyword in table_name.lower() for keyword in ['price', 'ohlc', 'duka', 'candle']):
            print(f"   📋 Structure:")
            cols = con.execute(f"DESCRIBE {table_name}").df()
            for _, col in cols.iterrows():
                print(f"      - {col['column_name']:<20} {col['column_type']}")
            print()
    except Exception as e:
        print(f"{i+1}. {table_name:<30} (erreur: {e})")

con.close()

print("="*80)
