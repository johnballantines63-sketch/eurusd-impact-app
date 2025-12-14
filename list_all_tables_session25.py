#!/usr/bin/env python3
"""
Liste toutes les tables de la DB - Session 25
"""

import duckdb
from pathlib import Path

def main():
    print("=" * 80)
    print("🔍 EXPLORATION BASE DE DONNÉES")
    print("=" * 80)
    
    db_path = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
    con = duckdb.connect(str(db_path))
    
    # Lister toutes les tables
    print("\n📋 TABLES DISPONIBLES:")
    tables = con.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).df()
    
    for idx, row in tables.iterrows():
        table_name = row['table_name']
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"\n{idx+1}. {table_name}")
        print(f"   Lignes: {count:,}")
        
        # Structure
        schema = con.execute(f"DESCRIBE {table_name}").df()
        print(f"   Colonnes ({len(schema)}):")
        for col in schema['column_name'][:10]:  # Max 10 colonnes
            print(f"      - {col}")
        if len(schema) > 10:
            print(f"      ... et {len(schema)-10} autres")
    
    # Chercher tables avec datetime
    print("\n" + "=" * 80)
    print("🔍 TABLES AVEC COLONNE 'DATETIME':")
    print("=" * 80)
    
    for idx, row in tables.iterrows():
        table_name = row['table_name']
        schema = con.execute(f"DESCRIBE {table_name}").df()
        
        if 'datetime' in schema['column_name'].str.lower().values:
            print(f"\n✅ {table_name}")
            
            # Échantillon
            sample = con.execute(f"""
                SELECT * FROM {table_name}
                LIMIT 3
            """).df()
            
            print(f"   Échantillon:")
            print(sample.head(3).to_string(index=False))
    
    con.close()
    
    print("\n" + "=" * 80)
    print("Fin exploration")
    print("=" * 80)

if __name__ == "__main__":
    main()
