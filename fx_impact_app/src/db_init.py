# fx_impact_app/src/db_init.py
"""Initialisation des structures DuckDB nécessaires."""
from __future__ import annotations
import duckdb
from pathlib import Path

def create_price_views(con: duckdb.DuckDBPyConnection) -> None:
    """
    Crée les vues de prix normalisées pour tous les timeframes.
    À appeler après ingestion des prix.
    """
    views_mapping = {
        "prices_1m_v": "prices_1m",
        "prices_5m_v": "prices_5m", 
        "prices_m15_v": "prices_15m",
        "prices_m30_v": "prices_30m",
        "prices_1h_v": "prices_1h",
        "prices_h4_v": "prices_4h",
    }
    
    for view_name, table_name in views_mapping.items():
        try:
            # Vérifie si la table source existe
            exists = con.execute(f"""
                SELECT 1 FROM information_schema.tables 
                WHERE lower(table_name) = lower('{table_name}')
                LIMIT 1
            """).fetchone()
            
            if not exists:
                print(f"  ⚠ Table {table_name} absente, vue {view_name} non créée")
                continue
                
            con.execute(f"""
                CREATE OR REPLACE VIEW {view_name} AS
                SELECT 
                    CAST(datetime AS TIMESTAMP) AS ts_utc,
                    open, high, low, close, volume
                FROM {table_name}
                WHERE datetime IS NOT NULL
                ORDER BY datetime
            """)
            print(f"  ✓ Vue créée: {view_name}")
            
        except Exception as e:
            print(f"  ⚠ Erreur création {view_name}: {e}")

def ensure_events_table(con: duckdb.DuckDBPyConnection) -> None:
    """Crée la table events si elle n'existe pas."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS events (
            ts_utc TIMESTAMP WITH TIME ZONE,
            country VARCHAR,
            event_title VARCHAR,
            event_key VARCHAR,
            label VARCHAR,
            type VARCHAR,
            estimate DOUBLE,
            forecast DOUBLE,
            previous DOUBLE,
            actual DOUBLE,
            unit VARCHAR,
            importance_n BIGINT
        )
    """)
    print("  ✓ Table events vérifiée")

def init_database(db_path: str) -> None:
    """
    Initialise toutes les structures nécessaires.
    Usage: python -m fx_impact_app.src.db_init
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Initialisation de {db_path}")
    with duckdb.connect(db_path) as con:
        ensure_events_table(con)
        create_price_views(con)
    print(f"✅ Base initialisée: {db_path}")

if __name__ == "__main__":
    from fx_impact_app.src.config import get_db_path
    init_database(get_db_path())
