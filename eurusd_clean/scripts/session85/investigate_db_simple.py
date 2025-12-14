"""
INVESTIGATION DATABASE SIMPLIFIÉE - SESSION 85
Écrit les résultats dans un fichier texte
"""

import duckdb
import pandas as pd
from pathlib import Path
import sys

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")
OUTPUT_FILE = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session85/investigation_results.txt")

def write_output(text):
    """Écrit dans le fichier et affiche"""
    print(text)
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(text + "\n")

# Effacer fichier de sortie
if OUTPUT_FILE.exists():
    OUTPUT_FILE.unlink()

write_output("=" * 80)
write_output("INVESTIGATION DATABASE WAREHOUSE.DUCKDB")
write_output("SESSION 85 - Recherche données MT5/Dukascopy")
write_output("=" * 80)

try:
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Étape 1 : Liste des tables
    write_output("\n" + "=" * 80)
    write_output("ÉTAPE 1 : LISTE TOUTES LES TABLES")
    write_output("=" * 80)
    
    tables = conn.execute("SHOW TABLES").fetchdf()
    write_output(f"\nTables trouvées : {len(tables)}")
    write_output(tables.to_string(index=False))
    
    # Étape 2 : Inspecter chaque table avec "price" dans le nom
    price_tables = [t for t in tables['name'] if 'price' in str(t).lower()]
    
    write_output(f"\n\n🎯 Tables contenant 'price' : {price_tables}")
    
    for table in price_tables:
        write_output(f"\n\n{'=' * 80}")
        write_output(f"TABLE : {table}")
        write_output("=" * 80)
        
        # Schéma
        schema = conn.execute(f"DESCRIBE {table}").fetchdf()
        write_output("\nSchéma :")
        write_output(schema.to_string(index=False))
        
        # Stats
        count = conn.execute(f"SELECT COUNT(*) as c FROM {table}").fetchone()[0]
        write_output(f"\nNombre de lignes : {count:,}")
        
        # Échantillon
        sample = conn.execute(f"SELECT * FROM {table} LIMIT 3").fetchdf()
        write_output("\nÉchantillon :")
        write_output(sample.to_string(index=False))
        
        # Période
        cols = schema['column_name'].tolist()
        dt_col = 'datetime' if 'datetime' in cols else ('ts_utc' if 'ts_utc' in cols else None)
        
        if dt_col:
            period = conn.execute(f"SELECT MIN({dt_col}) as min_d, MAX({dt_col}) as max_d FROM {table}").fetchdf()
            write_output("\nPériode :")
            write_output(period.to_string(index=False))
            
            # Test 01.08.2025 14:30
            write_output(f"\n{'~' * 60}")
            write_output("TEST 01.08.2025 14:30 (±20 min)")
            write_output("~" * 60)
            
            test = conn.execute(f"""
                SELECT * FROM {table}
                WHERE {dt_col} >= '2025-08-01 14:25:00'
                  AND {dt_col} <= '2025-08-01 14:50:00'
                ORDER BY {dt_col}
            """).fetchdf()
            
            write_output(f"\nLignes trouvées : {len(test)}")
            if len(test) > 0:
                write_output(test.to_string(index=False))
                
                # Calculer range si colonne close existe
                price_cols = [c for c in test.columns if c in ['close', 'c', 'price']]
                if price_cols:
                    pc = price_cols[0]
                    high_v = test[pc].max()
                    low_v = test[pc].min()
                    range_pips = (high_v - low_v) * 10000
                    write_output(f"\n📊 RANGE : {range_pips:.1f} pips")
                    write_output(f"   High : {high_v:.5f}")
                    write_output(f"   Low  : {low_v:.5f}")
            else:
                write_output("❌ Aucune donnée pour cette période")
    
    conn.close()
    
    write_output("\n\n" + "=" * 80)
    write_output("✅ INVESTIGATION TERMINÉE")
    write_output("=" * 80)
    write_output(f"\nRésultats sauvegardés dans : {OUTPUT_FILE}")

except Exception as e:
    write_output(f"\n❌ ERREUR : {str(e)}")
    import traceback
    write_output(traceback.format_exc())
    sys.exit(1)
