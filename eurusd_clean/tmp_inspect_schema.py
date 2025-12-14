#!/usr/bin/env python3
"""
Script temporaire d'inspection du schéma DB
===========================================

Inspecte les tables/vues utilisées dans le notebook de validation.
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

TABLES_TO_INSPECT = [
    "events_with_ts_local_v1",
    "economic_events",
    "prices_finnhub_m5",
    "daily_risk_signal_v3_2_1",
]

DATES_TO_TEST = ["2025-08-01", "2025-09-11"]


def inspect_table_schema(conn, table_name):
    """Inspecte le schéma d'une table/vue."""
    print("=" * 80)
    print(f"TABLE/VUE: {table_name}")
    print("=" * 80)
    
    # Vérifier existence
    try:
        count_df = conn.execute(f"SELECT COUNT(*) as n FROM {table_name}").df()
        n_rows = count_df.iloc[0]["n"]
        print(f"Nombre de lignes: {n_rows:,}")
    except Exception as e:
        print(f"❌ Erreur COUNT(*): {e}")
        print("  (table/vue peut-être inexistante)")
        return False
    
    # Colonnes
    try:
        # PRAGMA table_info pour DuckDB
        info_df = conn.execute(f"PRAGMA table_info('{table_name}')").df()
        if not info_df.empty:
            print("\nColonnes:")
            for _, row in info_df.iterrows():
                col_name = row.get("name", "?")
                col_type = row.get("type", "?")
                not_null = row.get("notnull", 0)
                null_str = "NOT NULL" if not_null else "NULL"
                print(f"  - {col_name:40s} {col_type:30s} ({null_str})")
        else:
            # Fallback: DESCRIBE
            desc_df = conn.execute(f"DESCRIBE {table_name}").df()
            print("\nColonnes (via DESCRIBE):")
            for _, row in desc_df.iterrows():
                col_name = row.get("column_name", "?")
                col_type = row.get("column_type", "?")
                print(f"  - {col_name:40s} {col_type}")
    except Exception as e:
        print(f"⚠️  Erreur PRAGMA table_info: {e}")
        # Essayer DESCRIBE
        try:
            desc_df = conn.execute(f"DESCRIBE {table_name}").df()
            print("\nColonnes (via DESCRIBE):")
            for _, row in desc_df.iterrows():
                print(f"  - {row.get('column_name', '?')}: {row.get('column_type', '?')}")
        except Exception as e2:
            print(f"❌ Erreur DESCRIBE: {e2}")
    
    print()
    return True


def safe_select_columns(conn, table_name, date_col, date_value, columns_to_select, limit=10):
    """
    Sélectionne des colonnes en gérant celles qui n'existent pas.
    """
    # D'abord, vérifier quelles colonnes existent
    try:
        all_cols_df = conn.execute(f"DESCRIBE {table_name}").df()
        available_cols = set(all_cols_df["column_name"].str.lower())
    except:
        try:
            all_cols_df = conn.execute(f"PRAGMA table_info('{table_name}')").df()
            available_cols = set(all_cols_df["name"].str.lower())
        except:
            print(f"  ⚠️  Impossible de lister les colonnes de {table_name}")
            return None
    
    # Filtrer les colonnes qui existent
    cols_to_use = []
    for col in columns_to_select:
        if col.lower() in available_cols:
            cols_to_use.append(col)
        else:
            print(f"  ⚠️  Colonne '{col}' absente dans {table_name}")
    
    if not cols_to_use:
        print(f"  ❌ Aucune colonne disponible parmi {columns_to_select}")
        return None
    
    # Construire la requête
    try:
        if date_col.lower() in available_cols:
            query = f"""
                SELECT {', '.join(cols_to_use)}
                FROM {table_name}
                WHERE DATE({date_col}) = CAST(? AS DATE)
                LIMIT {limit}
            """
            df = conn.execute(query, [date_value]).df()
        else:
            print(f"  ⚠️  Colonne date '{date_col}' absente, tentative sans filtre date")
            query = f"""
                SELECT {', '.join(cols_to_use)}
                FROM {table_name}
                LIMIT {limit}
            """
            df = conn.execute(query).df()
        
        return df
    except Exception as e:
        print(f"  ❌ Erreur SELECT: {e}")
        return None


def inspect_sample_data(conn, table_name, date_col, date_value, columns_to_select, description):
    """Inspecte un échantillon de données."""
    print(f"📊 {description}")
    print(f"   Table: {table_name}, Date: {date_value}")
    
    df = safe_select_columns(conn, table_name, date_col, date_value, columns_to_select, limit=10)
    
    if df is None or df.empty:
        print(f"   ⚠️  Aucune donnée trouvée")
    else:
        print(f"   ✅ {len(df)} ligne(s) trouvée(s)")
        print()
        print(df.to_string(index=False))
    print()


def main():
    print("=" * 80)
    print("INSPECTION SCHÉMA DB — Validation Notebook")
    print("=" * 80)
    print(f"DB: {DB_PATH}")
    print()
    
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # 1. Inspection schéma des tables/vues
        print("\n" + "=" * 80)
        print("PARTIE 1 : SCHÉMA DES TABLES/VUES")
        print("=" * 80)
        print()
        
        for table_name in TABLES_TO_INSPECT:
            inspect_table_schema(conn, table_name)
        
        # 2. Inspection données d'échantillon
        print("\n" + "=" * 80)
        print("PARTIE 2 : ÉCHANTILLONS DE DONNÉES")
        print("=" * 80)
        print()
        
        for date_str in DATES_TO_TEST:
            print("\n" + "-" * 80)
            print(f"DATE: {date_str}")
            print("-" * 80)
            print()
            
            # 2a) events_with_ts_local_v1
            inspect_sample_data(
                conn,
                "events_with_ts_local_v1",
                "ts_local",
                date_str,
                ["ts_utc", "ts_local", "country", "event_key", "event_title", 
                 "importance_n", "actual", "forecast", "previous", "estimate", "prev"],
                "Événements (events_with_ts_local_v1)"
            )
            
            # 2b) economic_events
            inspect_sample_data(
                conn,
                "economic_events",
                "ts_utc",
                date_str,
                ["ts_utc", "country", "event", "estimate", "prev", "actual"],
                "Consensus (economic_events)"
            )
            
            # 2c) prices_finnhub_m5 (fenêtre autour 14:30 UTC)
            print(f"📊 Prix EURUSD (prices_finnhub_m5)")
            print(f"   Fenêtre: {date_str} 13:00:00 UTC → {date_str} 18:00:00 UTC")
            try:
                prices_df = conn.execute("""
                    SELECT ts_utc, close
                    FROM prices_finnhub_m5
                    WHERE ts_utc >= CAST(? AS TIMESTAMP)
                      AND ts_utc <= CAST(? AS TIMESTAMP)
                    ORDER BY ts_utc
                    LIMIT 10
                """, [f"{date_str} 13:00:00", f"{date_str} 18:00:00"]).df()
                
                if prices_df.empty:
                    print(f"   ⚠️  Aucune donnée trouvée dans la fenêtre")
                else:
                    print(f"   ✅ {len(prices_df)} ligne(s) trouvée(s)")
                    print()
                    print(prices_df.to_string(index=False))
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
            print()
        
        print("=" * 80)
        print("✅ Inspection terminée")
        print("=" * 80)
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

