# fx_impact_app/src/config.py
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Dict

# ------------------------------------------------------------
# Chargement .env (optionnel : python-dotenv). Fallback manuel.
# ------------------------------------------------------------
def _manual_dotenv_load(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        # Ne pas écraser si déjà défini par l'environnement
        if k and (os.environ.get(k) is None):
            os.environ[k] = v

def load_env() -> None:
    """Charge un .env s'il existe (à la racine du projet)."""
    root = Path(__file__).resolve().parents[2]  # .../eurusd_news_impact_app_v5_full
    dotenv_path = root / ".env"
    try:
        from dotenv import load_dotenv  # type: ignore
        # override=False pour ne pas écraser l'env courant
        load_dotenv(dotenv_path=dotenv_path, override=False)
    except Exception:
        _manual_dotenv_load(dotenv_path)

# Charger une fois au premier import
load_env()

# ------------------------------------------------------------
# Helpers clés & DB
# ------------------------------------------------------------
def get_db_path() -> str:
    """
    Retourne le chemin DuckDB (par défaut: fx_impact_app/data/warehouse.duckdb).
    Peut être surchargé par la variable d'environnement DUCKDB_PATH.
    """
    env = os.environ.get("DUCKDB_PATH")
    if env and env.strip():
        return Path(env).expanduser().resolve().as_posix()
    root = Path(__file__).resolve().parents[1]  # .../fx_impact_app
    return (root / "data" / "warehouse.duckdb").as_posix()

def get_eod_key(default: Optional[str] = None) -> Optional[str]:
    """Renvoie la clé EODHD sous forme de chaîne (ou None si absente)."""
    v = os.environ.get("EODHD_API_KEY")
    if v is None or not str(v).strip() or str(v).strip().lower() in ("true", "false"):
        return default
    return str(v).strip()

def get_te_key(default: Optional[str] = None) -> Optional[str]:
    """Renvoie la clé TradingEconomics sous forme de chaîne (ou None si absente)."""
    v = os.environ.get("TE_API_KEY")
    if v is None or not str(v).strip() or str(v).strip().lower() in ("true", "false"):
        return default
    return str(v).strip()

def env_status() -> Dict[str, bool]:
    """
    Pour les pages de statut : True/False si une clé *valide* est apparemment présente.
    (Évite de compter 'True'/'False' comme clé.)
    """
    eod = get_eod_key()
    te = get_te_key()
    return {
        "EODHD_API_KEY": bool(eod),
        "TE_API_KEY": bool(te),
    }
