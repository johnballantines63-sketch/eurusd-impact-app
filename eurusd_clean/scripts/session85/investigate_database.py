"""
INVESTIGATION DATABASE - SESSION 85

Objectif : Identifier TOUTES les tables de prix dans warehouse.duckdb
et trouver la source correcte contenant les vraies données MT5/Dukascopy

Date : 26 octobre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

def list_all_tables():
    """Liste toutes les tables de la base de données"""
    print("=" * 80)
    print("ÉTAPE 1 : LISTE DE TOUTES LES TABLES")
    print("=" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Lister toutes les tables
    tables = conn.execute("SHOW TABLES").fetchdf()
    print("\n📊 Tables disponibles :")
    print(tables.to_string(index=False))
    print(f"\nTotal : {len(tables)} tables\n")
    
    conn.close()
    return tables

def inspect_table_schema(table_name: str):
    """Inspecte le schéma d'une table"""
    print(f"\n{'=' * 80}")
    print(f"SCHÉMA TABLE : {table_name}")
    print(f"{'=' * 80}")
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Schéma
        schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()
        print("\nColonnes :")
        print(schema.to_string(index=False))
        
        # Statistiques
        count = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchdf().iloc[0]['count']
        print(f"\nNombre de lignes : {count:,}")
        
        # Échantillon
        if count > 0:
            sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchdf()
            print("\nÉchantillon (5 premières lignes) :")
            print(sample.to_string(index=False))
            
            # Si c'est une table de prix avec datetime
            if 'datetime' in sample.columns or 'ts_utc' in sample.columns:
                dt_col = 'datetime' if 'datetime' in sample.columns else 'ts_utc'
                period = conn.execute(f"""
                    SELECT 
                        MIN({dt_col}) as min_date,
                        MAX({dt_col}) as max_date
                    FROM {table_name}
                """).fetchdf()
                print(f"\nPériode couverte :")
                print(period.to_string(index=False))
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
    
    finally:
        conn.close()

def check_specific_date(table_name: str, date_str: str = "2025-08-01", time_str: str = "14:30:00"):
    """Vérifie les données pour une date/heure spécifique"""
    print(f"\n{'=' * 80}")
    print(f"VÉRIFICATION DATE SPÉCIFIQUE : {table_name}")
    print(f"Date : {date_str} {time_str}")
    print(f"{'=' * 80}")
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Essayer datetime d'abord
        result = conn.execute(f"""
            SELECT * FROM {table_name}
            WHERE datetime >= TIMESTAMP '{date_str} {time_str}' - INTERVAL '5 minutes'
              AND datetime <= TIMESTAMP '{date_str} {time_str}' + INTERVAL '20 minutes'
            ORDER BY datetime
        """).fetchdf()
        
        if len(result) > 0:
            print(f"\n✅ Trouvé {len(result)} lignes avec colonne 'datetime'")
            print(result.to_string(index=False))
            
            # Calculer range
            if 'close' in result.columns or 'c' in result.columns:
                price_col = 'close' if 'close' in result.columns else 'c'
                high_val = result[price_col].max()
                low_val = result[price_col].min()
                range_pips = (high_val - low_val) * 10000
                print(f"\n📊 Range observé : {range_pips:.1f} pips")
                print(f"   High : {high_val:.5f}")
                print(f"   Low  : {low_val:.5f}")
        else:
            print("❌ Aucune donnée trouvée avec 'datetime'")
            
    except Exception as e1:
        print(f"⚠️  Erreur avec 'datetime' : {e1}")
        
        # Essayer ts_utc
        try:
            result = conn.execute(f"""
                SELECT * FROM {table_name}
                WHERE ts_utc >= TIMESTAMP '{date_str} {time_str}' - INTERVAL '5 minutes'
                  AND ts_utc <= TIMESTAMP '{date_str} {time_str}' + INTERVAL '20 minutes'
                ORDER BY ts_utc
            """).fetchdf()
            
            if len(result) > 0:
                print(f"\n✅ Trouvé {len(result)} lignes avec colonne 'ts_utc'")
                print(result.to_string(index=False))
                
                # Calculer range
                if 'close' in result.columns:
                    high_val = result['close'].max()
                    low_val = result['close'].min()
                    range_pips = (high_val - low_val) * 10000
                    print(f"\n📊 Range observé : {range_pips:.1f} pips")
                    print(f"   High : {high_val:.5f}")
                    print(f"   Low  : {low_val:.5f}")
            else:
                print("❌ Aucune donnée trouvée avec 'ts_utc'")
        
        except Exception as e2:
            print(f"❌ Erreur avec 'ts_utc' : {e2}")
    
    finally:
        conn.close()

def main():
    """Investigation complète"""
    print("\n" + "=" * 80)
    print("INVESTIGATION DATABASE WAREHOUSE.DUCKDB")
    print("SESSION 85 - Recherche données MT5/Dukascopy")
    print("=" * 80)
    
    # Étape 1 : Lister toutes les tables
    tables = list_all_tables()
    
    # Étape 2 : Identifier tables contenant prix
    price_tables = []
    for table in tables['name']:
        table_lower = str(table).lower()
        if any(keyword in table_lower for keyword in ['price', 'ohlc', 'market', 'candle', '1m', 'tick']):
            price_tables.append(table)
    
    if price_tables:
        print(f"\n🎯 Tables potentielles de prix identifiées : {price_tables}")
    else:
        print("\n⚠️  Aucune table de prix identifiée par nom, inspection de toutes les tables...")
        price_tables = tables['name'].tolist()
    
    # Étape 3 : Inspecter chaque table de prix
    for table in price_tables:
        inspect_table_schema(table)
        
        # Test spécifique 01.08.2025 14:30 si table contient datetime/ts_utc
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        try:
            cols = conn.execute(f"DESCRIBE {table}").fetchdf()['column_name'].tolist()
            if 'datetime' in cols or 'ts_utc' in cols:
                check_specific_date(table, "2025-08-01", "14:30:00")
        except:
            pass
        finally:
            conn.close()
    
    print("\n" + "=" * 80)
    print("INVESTIGATION TERMINÉE")
    print("=" * 80)

if __name__ == "__main__":
    main()
