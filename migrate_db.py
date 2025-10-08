"""Migration DB : Ajoute colonnes latency si manquantes"""
import duckdb
from pathlib import Path

def get_db_path():
    """Trouve le chemin de la DB"""
    possible_paths = [
        Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb",
        Path("fx_impact_app/data/warehouse.duckdb"),
        Path("/mount/src/eurusd-news-impact-calculator/fx_impact_app/data/warehouse.duckdb")
    ]
    for p in possible_paths:
        if p.exists():
            return str(p)
    return "fx_impact_app/data/warehouse.duckdb"

def migrate_database():
    """Ajoute colonnes latency si nécessaire"""
    try:
        db_path = get_db_path()
        conn = duckdb.connect(db_path)
        
        schema = conn.execute("DESCRIBE event_families").fetchall()
        existing_cols = [col[0] for col in schema]
        
        if 'latency_median' not in existing_cols:
            print("🔧 Migration DB : Ajout colonnes...")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_median DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_p20 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_p80 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_median DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_p20 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_p80 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS mfe_p80 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS n_events_latency INTEGER")
            print("✅ Migration OK")
        
        conn.close()
    except Exception as e:
        print(f"⚠️ Migration: {e}")

if __name__ == "__main__":
    migrate_database()
