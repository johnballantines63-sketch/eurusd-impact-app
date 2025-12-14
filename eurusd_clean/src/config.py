"""
Configuration centralisée - eurusd_clean
=========================================

Chemins et paramètres pour toute l'application.

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

import os
from pathlib import Path

# Chemins de base
# config.py est dans src/, donc remonter d'un niveau pour avoir eurusd_clean/
PROJECT_ROOT = Path(__file__).parent.parent

# Charger .env si disponible
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')
except:
    pass
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "warehouse.duckdb"

# Paramètres DB
DB_TABLE_PRICES = "prices_bern"  # ✅ TOUJOURS utiliser prices_bern
DB_TABLE_EVENTS = "events"

# Paramètres mesure impact
DEFAULT_LOOKBACK_MINUTES = 5
DEFAULT_LOOKAHEAD_MINUTES = 120

# Formules validées (Session 51-55)
FORMULAS_VERSION = "2.4"
AMPLIFICATION_BASELINE = 2.5

# Timezone
TIMEZONE_BERN = "Europe/Zurich"

# Validation
REFERENCE_CASE = {
    "date": "2025-09-11",
    "time": "14:30:00",
    "expected_impact": 56.2,  # pips
}

def get_db_path():
    """Retourne le chemin vers la DB principale"""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB introuvable: {DB_PATH}")
    return DB_PATH

def get_finnhub_api_key() -> str:
    """Retourne la clé API Finnhub depuis l'environnement"""
    api_key = os.environ.get('FINNHUB_API_KEY')
    if not api_key:
        raise ValueError("FINNHUB_API_KEY non trouvée dans l'environnement. Vérifiez le fichier .env")
    return api_key

def validate_db():
    """Valide que la DB contient la vue prices_bern"""
    import duckdb
    
    con = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Vérifier vue
        count = con.execute("SELECT COUNT(*) FROM prices_bern").fetchone()[0]
        print(f"✅ Vue prices_bern: {count:,} lignes")
        return True
    except Exception as e:
        print(f"❌ Erreur DB: {e}")
        return False
    finally:
        con.close()

if __name__ == "__main__":
    print("Configuration eurusd_clean")
    print(f"DB: {DB_PATH}")
    validate_db()
