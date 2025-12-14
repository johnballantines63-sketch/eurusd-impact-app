"""
Configuration centralisée de l'application EUR/USD Impact Calculator.

Ce module gère :
- Chemins vers la base de données
- Variables d'environnement (API keys)
- Paramètres métier (fenêtres temporelles, seuils)
- Constantes système

Usage:
    from app.config import config
    
    db_path = config.get_db_path()
    window = config.DEFAULT_WINDOW_MINUTES
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Dict


# ============================================================================
# CHARGEMENT VARIABLES D'ENVIRONNEMENT
# ============================================================================

def _manual_dotenv_load(dotenv_path: Path) -> None:
    """
    Charge un fichier .env manuellement si python-dotenv n'est pas disponible.
    
    Args:
        dotenv_path: Chemin vers le fichier .env
    """
    if not dotenv_path.exists():
        return
    
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        
        # Ignorer commentaires et lignes vides
        if not line or line.startswith("#"):
            continue
            
        if "=" not in line:
            continue
            
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        
        # Ne pas écraser variables d'environnement existantes
        if key and (os.environ.get(key) is None):
            os.environ[key] = value


def load_env() -> None:
    """
    Charge les variables d'environnement depuis .env (si présent).
    
    Essaie d'abord python-dotenv, puis fallback sur chargement manuel.
    Ne charge que si .env existe à la racine du projet.
    """
    # Remonter de 2 niveaux : app/config.py -> app/ -> eurusd_clean/
    root = Path(__file__).resolve().parents[1]
    dotenv_path = root / ".env"
    
    try:
        from dotenv import load_dotenv
        # override=False : ne pas écraser variables existantes
        load_dotenv(dotenv_path=dotenv_path, override=False)
    except ImportError:
        # Fallback : chargement manuel
        _manual_dotenv_load(dotenv_path)


# Charger automatiquement au premier import
load_env()


# ============================================================================
# CLASSE CONFIGURATION
# ============================================================================

class Config:
    """
    Configuration centralisée de l'application.
    
    Tous les paramètres système sont définis ici pour faciliter
    la maintenance et les tests.
    """
    
    # ========================================================================
    # CHEMINS & BASE DE DONNÉES
    # ========================================================================
    
    def get_db_path(self) -> str:
        """
        Retourne le chemin vers warehouse.duckdb.
        
        Peut être surchargé par variable d'environnement DUCKDB_PATH.
        
        Returns:
            Chemin absolu vers warehouse.duckdb
            
        Examples:
            >>> config = Config()
            >>> db_path = config.get_db_path()
            >>> "warehouse.duckdb" in db_path
            True
        """
        # Priorité 1 : Variable d'environnement
        env_path = os.environ.get("DUCKDB_PATH")
        if env_path and env_path.strip():
            return Path(env_path).expanduser().resolve().as_posix()
        
        # Priorité 2 : Chemin par défaut
        # eurusd_clean/app/config.py -> eurusd_clean/app/data/warehouse.duckdb
        app_root = Path(__file__).resolve().parent
        return (app_root / "data" / "warehouse.duckdb").as_posix()
    
    def get_legacy_db_path(self) -> str:
        """
        Retourne le chemin vers l'ancienne base de données (legacy).
        
        Utilisé uniquement pendant la migration.
        
        Returns:
            Chemin absolu vers fx_impact_app/data/warehouse.duckdb
        """
        # Remonter de eurusd_clean/app/ à la racine projet
        project_root = Path(__file__).resolve().parents[2]
        return (project_root / "fx_impact_app" / "data" / "warehouse.duckdb").as_posix()
    
    # ========================================================================
    # API KEYS
    # ========================================================================
    
    def get_eod_key(self, default: Optional[str] = None) -> Optional[str]:
        """
        Retourne la clé API EODHD.
        
        Args:
            default: Valeur par défaut si clé absente
            
        Returns:
            Clé API ou None si absente/invalide
            
        Examples:
            >>> config = Config()
            >>> key = config.get_eod_key()
            >>> key is None or isinstance(key, str)
            True
        """
        value = os.environ.get("EODHD_API_KEY")
        
        # Filtrer valeurs invalides
        if value is None or not str(value).strip():
            return default
            
        # Filtrer booléens mal formatés
        if str(value).strip().lower() in ("true", "false"):
            return default
            
        return str(value).strip()
    
    def get_te_key(self, default: Optional[str] = None) -> Optional[str]:
        """
        Retourne la clé API TradingEconomics.
        
        Args:
            default: Valeur par défaut si clé absente
            
        Returns:
            Clé API ou None si absente/invalide
        """
        value = os.environ.get("TE_API_KEY")
        
        if value is None or not str(value).strip():
            return default
            
        if str(value).strip().lower() in ("true", "false"):
            return default
            
        return str(value).strip()
    
    def env_status(self) -> Dict[str, bool]:
        """
        Retourne le statut des clés API (présentes ou non).
        
        Utilisé pour afficher le statut dans l'interface.
        
        Returns:
            Dictionnaire {nom_clé: présente}
            
        Examples:
            >>> config = Config()
            >>> status = config.env_status()
            >>> isinstance(status, dict)
            True
            >>> "EODHD_API_KEY" in status
            True
        """
        return {
            "EODHD_API_KEY": bool(self.get_eod_key()),
            "TE_API_KEY": bool(self.get_te_key()),
        }
    
    # ========================================================================
    # PARAMÈTRES MÉTIER
    # ========================================================================
    
    # Fenêtres temporelles
    DEFAULT_WINDOW_MINUTES: int = 30
    """Fenêtre par défaut pour grouper événements simultanés (minutes)"""
    
    PHASE1_WINDOW_MINUTES: int = 60
    """Fenêtre Phase 1 : première réaction marché après événement (minutes)"""
    
    LATENCY_MAX_MINUTES: int = 30
    """Latence maximale acceptable entre événement et première réaction (minutes)"""
    
    TTR_MAX_MINUTES: int = 120
    """Time-to-Revert maximal acceptable (minutes)"""
    
    # Seuils impact
    MIN_IMPACT_PIPS: float = 1.0
    """Impact minimum en pips pour être considéré comme significatif"""
    
    HIGH_IMPACT_PIPS: float = 10.0
    """Seuil d'impact élevé en pips"""
    
    VERY_HIGH_IMPACT_PIPS: float = 20.0
    """Seuil d'impact très élevé en pips"""
    
    # Seuils surprise
    MIN_SURPRISE_PCT: float = 0.5
    """Surprise minimale en % pour être considérée comme significative"""
    
    HIGH_SURPRISE_PCT: float = 2.0
    """Seuil de surprise élevée en %"""
    
    # Score composite
    MIN_TRADABILITY_SCORE: int = 50
    """Score minimum pour événement "tradable" (0-100)"""
    
    # Facteur correction multi-événements
    VECTORIAL_SUM_FACTOR: float = 0.758
    """
    Facteur de correction pour somme vectorielle multi-événements.
    
    Validé empiriquement (Session 27) :
    - Sans correction : R² = 0.264
    - Avec 0.758 : R² = 0.292 (meilleur)
    """
    
    # ========================================================================
    # PAYS & DEVISES
    # ========================================================================
    
    SUPPORTED_COUNTRIES: list[str] = ["US", "EU", "GB"]
    """Pays supportés pour événements économiques"""
    
    BASE_CURRENCY: str = "EUR"
    """Devise de base pour paires forex"""
    
    QUOTE_CURRENCY: str = "USD"
    """Devise de cotation pour paires forex"""
    
    # ========================================================================
    # TIMEFRAMES
    # ========================================================================
    
    SUPPORTED_TIMEFRAMES: list[str] = ["1m", "5m", "15m", "1h"]
    """Timeframes supportés pour données de prix"""
    
    DEFAULT_TIMEFRAME: str = "1m"
    """Timeframe par défaut"""
    
    # ========================================================================
    # FORMULES & VERSIONS
    # ========================================================================
    
    ACTIVE_FORMULA: str = "v9-clean"
    """Formule active pour calcul impacts"""
    
    AVAILABLE_FORMULAS: list[str] = [
        "v8.7",       # Ancienne version (production)
        "v9-clean",   # Version actuelle (somme vectorielle)
        "v4",         # Version future (prédiction ML)
    ]
    """Formules disponibles pour calcul impacts"""
    
    # ========================================================================
    # CACHE & PERFORMANCE
    # ========================================================================
    
    ENABLE_CACHE: bool = True
    """Activer cache pour requêtes DB fréquentes"""
    
    CACHE_TTL_SECONDS: int = 300
    """Durée de vie du cache (secondes)"""
    
    MAX_CACHE_SIZE_MB: int = 100
    """Taille maximale du cache (MB)"""
    
    # ========================================================================
    # DEBUG & LOGGING
    # ========================================================================
    
    DEBUG_MODE: bool = False
    """Mode debug (logs verbeux)"""
    
    LOG_LEVEL: str = "INFO"
    """Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)"""
    
    LOG_TO_FILE: bool = True
    """Écrire logs dans fichier"""
    
    LOG_FILE_PATH: Optional[str] = None
    """Chemin vers fichier de logs (None = auto)"""


# ============================================================================
# INSTANCE SINGLETON
# ============================================================================

# Instance unique de configuration (pattern Singleton)
config = Config()


# ============================================================================
# FONCTIONS UTILITAIRES (Rétro-compatibilité)
# ============================================================================

def get_db_path() -> str:
    """
    [DEPRECATED] Utiliser config.get_db_path() à la place.
    
    Conservé pour rétro-compatibilité avec code legacy.
    """
    return config.get_db_path()


def get_eod_key(default: Optional[str] = None) -> Optional[str]:
    """
    [DEPRECATED] Utiliser config.get_eod_key() à la place.
    
    Conservé pour rétro-compatibilité avec code legacy.
    """
    return config.get_eod_key(default)


def get_te_key(default: Optional[str] = None) -> Optional[str]:
    """
    [DEPRECATED] Utiliser config.get_te_key() à la place.
    
    Conservé pour rétro-compatibilité avec code legacy.
    """
    return config.get_te_key(default)


def env_status() -> Dict[str, bool]:
    """
    [DEPRECATED] Utiliser config.env_status() à la place.
    
    Conservé pour rétro-compatibilité avec code legacy.
    """
    return config.env_status()


# ============================================================================
# VALIDATION AU DÉMARRAGE
# ============================================================================

def validate_config() -> tuple[bool, list[str]]:
    """
    Valide la configuration au démarrage de l'application.
    
    Returns:
        (is_valid, errors) : Tuple (validité, liste d'erreurs)
        
    Examples:
        >>> is_valid, errors = validate_config()
        >>> isinstance(is_valid, bool)
        True
    """
    errors = []
    
    # Vérifier DB existe
    db_path = Path(config.get_db_path())
    if not db_path.exists():
        errors.append(f"Base de données introuvable : {db_path}")
    
    # Vérifier taille DB (doit être > 100 MB)
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        if size_mb < 100:
            errors.append(
                f"Base de données trop petite : {size_mb:.1f} MB "
                f"(attendu > 100 MB)"
            )
    
    # Avertir si clés API manquantes (non bloquant)
    if not config.get_eod_key():
        errors.append(
            "AVERTISSEMENT : Clé API EODHD manquante "
            "(import calendrier désactivé)"
        )
    
    is_valid = not any(e for e in errors if not e.startswith("AVERTISSEMENT"))
    return is_valid, errors


if __name__ == "__main__":
    # Test de la configuration
    print("=" * 70)
    print("Configuration EUR/USD Impact Calculator")
    print("=" * 70)
    
    print(f"\n📁 Chemins:")
    print(f"  DB Path : {config.get_db_path()}")
    print(f"  Legacy DB : {config.get_legacy_db_path()}")
    
    print(f"\n🔑 API Keys:")
    status = config.env_status()
    for key, present in status.items():
        status_icon = "✅" if present else "❌"
        print(f"  {status_icon} {key}")
    
    print(f"\n⚙️  Paramètres Métier:")
    print(f"  Fenêtre par défaut : {config.DEFAULT_WINDOW_MINUTES} min")
    print(f"  Phase 1 : {config.PHASE1_WINDOW_MINUTES} min")
    print(f"  Facteur vectoriel : {config.VECTORIAL_SUM_FACTOR}")
    print(f"  Formule active : {config.ACTIVE_FORMULA}")
    
    print(f"\n✓ Validation:")
    is_valid, errors = validate_config()
    if is_valid:
        print("  ✅ Configuration valide")
    else:
        print("  ❌ Erreurs détectées :")
        for error in errors:
            print(f"    - {error}")
    
    print("=" * 70)
