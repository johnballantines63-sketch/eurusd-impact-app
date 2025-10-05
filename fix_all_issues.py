#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script maître de correction pour FX Impact Calculator
Résout TOUS les problèmes identifiés dans l'audit complet
"""
from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()
SRC_DIR = ROOT / "fx_impact_app" / "src"
PAGES_DIR = ROOT / "fx_impact_app" / "streamlit_app" / "pages"

def backup_file(path: Path):
    """Crée un backup timestampé avant modification"""
    if path.exists():
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = path.with_suffix(f".{timestamp}.backup")
        shutil.copy2(path, backup)
        print(f"  ✓ Backup: {backup.name}")

# ============================================================
# 1. REGEX_PRESETS.PY - VERSION UNIFIÉE DÉFINITIVE
# ============================================================
REGEX_PRESETS_UNIFIED = '''# fx_impact_app/src/regex_presets.py
"""
Presets regex pour filtrage d'événements macro-économiques.
Version unifiée compatible avec toutes les pages.
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional

# ============================================================
# PRESETS REGEX (structure simple, dict plat)
# ============================================================
REGEX_PRESETS: Dict[str, str] = {
    # US — Emploi
    "NFP (US)": r"(?i)(nonfarm|non-farm|nfp|payrolls|employment)",
    "ADP (US)": r"(?i)\\badp\\b",
    "Unemployment rate (US)": r"(?i)\\bunemployment\\b|\\bjobless\\b",
    "Average Hourly Earnings (US)": r"(?i)average hourly earnings|ahe",
    
    # US — Inflation
    "CPI (US)": r"(?i)\\bcpi\\b|consumer price",
    "Core CPI (US)": r"(?i)core cpi|core consumer price",
    "PCE / Core PCE (US)": r"(?i)\\bpce\\b|core pce|personal consumption",
    
    # US — Activité
    "Retail Sales (US)": r"(?i)retail sales",
    "ISM Manufacturing (US)": r"(?i)\\bism\\b.*manufacturing|manufacturing pmi",
    "ISM Services (US)": r"(?i)\\bism\\b.*services|services pmi",
    "GDP (US)": r"(?i)\\bgdp\\b|gross domestic product",
    "Initial Jobless Claims (US)": r"(?i)initial (jobless|unemployment) claims",
    "Housing (US)": r"(?i)(housing starts|building permits|existing home sales|new home sales)",
    
    # US — Banque centrale
    "FOMC (Fed, US)": r"(?i)fomc|fed funds|rate decision|interest rate|dot plot|press conference|powell",
    
    # Eurozone
    "CPI (EA/EU)": r"(?i)(hicp|cpi).*(ea|euro|eurozone|euro area)",
    "ECB (EA/EU)": r"(?i)ecb|main refinancing|deposit facility|marginal lending",
    "PMI (EA/EU)": r"(?i)pmi|s&p global",
    "GDP (EA/EU)": r"(?i)\\bgdp\\b|gross domestic product",
    
    # Allemagne
    "ZEW (DE)": r"(?i)\\bzew\\b",
    "IFO (DE)": r"(?i)\\bifo\\b",
    "CPI (DE)": r"(?i)(hicp|cpi).*(germany|deutschland|\\bde\\b)",
    
    # France
    "CPI (FR)": r"(?i)(hicp|cpi).*(france|\\bfr\\b)",
    
    # UK
    "BoE / Rate Decision (UK)": r"(?i)bank of england|boe|rate decision|bank rate",
    
    # Génériques
    "Any Rate Decision": r"(?i)rate decision|monetary policy decision|policy rate",
    "Press conference (CB)": r"(?i)press conference|statement|minutes",
}

# ============================================================
# MAPPING FAMILLE -> PRESET PAR DÉFAUT
# ============================================================
_FAMILY_DEFAULT: Dict[str, str] = {
    "NFP": "NFP (US)",
    "CPI": "CPI (US)",
    "FOMC": "FOMC (Fed, US)",
}

# ============================================================
# MAPPING PRESET -> PAYS SUGGÉRÉS
# ============================================================
_PRESET_COUNTRIES: Dict[str, List[str]] = {
    "NFP (US)": ["US"],
    "ADP (US)": ["US"],
    "Unemployment rate (US)": ["US"],
    "Average Hourly Earnings (US)": ["US"],
    "CPI (US)": ["US"],
    "Core CPI (US)": ["US"],
    "PCE / Core PCE (US)": ["US"],
    "Retail Sales (US)": ["US"],
    "ISM Manufacturing (US)": ["US"],
    "ISM Services (US)": ["US"],
    "GDP (US)": ["US"],
    "Initial Jobless Claims (US)": ["US"],
    "Housing (US)": ["US"],
    "FOMC (Fed, US)": ["US"],
    "CPI (EA/EU)": ["EA", "EU"],
    "ECB (EA/EU)": ["EA", "EU"],
    "PMI (EA/EU)": ["EA", "EU"],
    "GDP (EA/EU)": ["EA", "EU"],
    "ZEW (DE)": ["DE"],
    "IFO (DE)": ["DE"],
    "CPI (DE)": ["DE"],
    "CPI (FR)": ["FR"],
    "BoE / Rate Decision (UK)": ["GB", "UK"],
    "Any Rate Decision": [],
    "Press conference (CB)": [],
}

# ============================================================
# FONCTIONS D'ACCÈS (API publique)
# ============================================================

def preset_names() -> List[str]:
    """Liste des noms de presets disponibles."""
    return list(REGEX_PRESETS.keys())

def pattern_for(name: str) -> str:
    """Retourne le pattern regex pour un preset donné."""
    return REGEX_PRESETS.get(name, r"(?i).")

def default_preset_for_family(family: Optional[str]) -> str:
    """Retourne le preset par défaut pour une famille donnée."""
    return _FAMILY_DEFAULT.get((family or "").upper(), "NFP (US)")

def get_countries(preset_name: str) -> List[str]:
    """Retourne les pays suggérés pour un preset."""
    return _PRESET_COUNTRIES.get(preset_name, [])

def get_regex(preset_name: str) -> str:
    """Alias de pattern_for() pour compatibilité."""
    return pattern_for(preset_name)

def coalesce_regex(preset_name: str, free_text: str) -> str:
    """Retourne free_text si non-vide, sinon le pattern du preset."""
    ft = (free_text or "").strip()
    return ft if ft else pattern_for(preset_name)

# ============================================================
# COMPOSANT STREAMLIT (optionnel)
# ============================================================

def regex_selectbox(
    label: str = "Filtre regex (preset)",
    default: Optional[str] = None,
    help: Optional[str] = None
) -> Tuple[str, str]:
    """
    Composant Streamlit pour sélectionner un preset.
    Retourne (pattern, preset_name)
    """
    import streamlit as st
    names = preset_names()
    idx = names.index(default) if default in names else 0
    name = st.selectbox(label, names, index=idx, help=help)
    pattern = REGEX_PRESETS[name]
    with st.expander("Voir le regex"):
        st.code(pattern, language="regex")
    return pattern, name

# ============================================================
# COMPATIBILITÉ LEGACY (pour anciennes pages)
# ============================================================

# Alias pour compatibilité avec les anciennes pages qui importent PRESETS
def preset_keys():
    """Alias de preset_names()."""
    return preset_names()

def get_variants(preset_name: str) -> List[str]:
    """Retourne une liste à un élément (compatibilité)."""
    return ["Standard"]

def get_variant_regex(preset_name: str, variant: str) -> str:
    """Retourne le regex du preset (ignore variant)."""
    return pattern_for(preset_name)

def get_family(preset_name: str) -> Optional[str]:
    """Devine la famille depuis le nom du preset."""
    name_upper = preset_name.upper()
    if "NFP" in name_upper or "ADP" in name_upper or "EMPLOYMENT" in name_upper:
        return "NFP"
    if "CPI" in name_upper or "INFLATION" in name_upper or "PCE" in name_upper:
        return "CPI"
    if "FOMC" in name_upper or "FED" in name_upper:
        return "FOMC"
    return None
'''

# ============================================================
# 2. FORECASTER_MVP.PY - AJOUT DES FONCTIONS MANQUANTES
# ============================================================
FORECASTER_ADDITIONS = '''
# Ajout en début de fichier (après les imports)

# Horizons par défaut (minutes)
HORIZONS = [15, 30, 60]

def compute_surprise(actual: float, consensus: float) -> float:
    """
    Calcule la surprise en % : (Actual - Consensus) / |Consensus| * 100
    Retourne 0.0 si consensus est nul pour éviter division par zéro.
    """
    if consensus == 0:
        return 0.0
    return ((actual - consensus) / abs(consensus)) * 100.0
'''

# ============================================================
# 3. TE_CLIENT.PY - CORRECTION IMPORT
# ============================================================
TE_CLIENT_FIXED = '''# fx_impact_app/src/te_client.py
from __future__ import annotations
import requests
import pandas as pd
from typing import Any, Dict, List, Optional
from .config import get_te_key as _get_te_key_config

TE_BASE = "https://api.tradingeconomics.com/calendar"

def get_te_key(key_in: Optional[str] = None) -> str:
    """Récupère la clé TE depuis config ou paramètre."""
    if key_in:
        return key_in
    k = _get_te_key_config()
    if not k:
        raise RuntimeError("Missing TE_API_KEY.")
    return k
'''

# ============================================================
# 4. DB_INIT.PY - INITIALISATION VUES DUCKDB
# ============================================================
DB_INIT_CONTENT = '''# fx_impact_app/src/db_init.py
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
'''

# ============================================================
# 5. CHECK_SETUP.PY - SCRIPT DE VÉRIFICATION
# ============================================================
CHECK_SETUP_CONTENT = '''#!/usr/bin/env python3
"""Script de vérification complète de l'installation."""
import sys
from pathlib import Path

def check_structure():
    """Vérifie la structure des dossiers."""
    required = [
        "fx_impact_app/src",
        "fx_impact_app/streamlit_app",
        "fx_impact_app/streamlit_app/pages",
        "fx_impact_app/data",
    ]
    missing = [p for p in required if not Path(p).exists()]
    
    if missing:
        print("❌ Dossiers manquants:")
        for m in missing:
            print(f"   - {m}")
        return False
    print("✓ Structure des dossiers OK")
    return True

def check_imports():
    """Vérifie que tous les imports fonctionnent."""
    errors = []
    
    try:
        from fx_impact_app.src import config
        print("  ✓ config")
    except Exception as e:
        errors.append(f"config: {e}")
    
    try:
        from fx_impact_app.src import regex_presets
        # Vérifie les fonctions critiques
        assert hasattr(regex_presets, 'REGEX_PRESETS'), "REGEX_PRESETS manquant"
        assert hasattr(regex_presets, 'preset_names'), "preset_names() manquante"
        assert hasattr(regex_presets, 'get_countries'), "get_countries() manquante"
        assert hasattr(regex_presets, 'get_regex'), "get_regex() manquante"
        assert hasattr(regex_presets, 'coalesce_regex'), "coalesce_regex() manquante"
        print("  ✓ regex_presets (toutes fonctions présentes)")
    except Exception as e:
        errors.append(f"regex_presets: {e}")
    
    try:
        from fx_impact_app.src import forecaster_mvp
        assert hasattr(forecaster_mvp, 'compute_surprise'), "compute_surprise manquante"
        assert hasattr(forecaster_mvp, 'HORIZONS'), "HORIZONS manquant"
        assert hasattr(forecaster_mvp, 'forecast'), "forecast() manquante"
        print("  ✓ forecaster_mvp (toutes fonctions présentes)")
    except Exception as e:
        errors.append(f"forecaster_mvp: {e}")
    
    try:
        from fx_impact_app.src import eodhd_client
        print("  ✓ eodhd_client")
    except Exception as e:
        errors.append(f"eodhd_client: {e}")
    
    try:
        from fx_impact_app.src import db_init
        print("  ✓ db_init")
    except Exception as e:
        errors.append(f"db_init: {e}")
    
    if errors:
        print("❌ Erreurs d'import:")
        for err in errors:
            print(f"   - {err}")
        return False
    
    print("✓ Tous les imports OK")
    return True

def check_env():
    """Vérifie les variables d'environnement."""
    from fx_impact_app.src.config import get_eod_key, get_te_key
    
    eod = get_eod_key()
    te = get_te_key()
    
    print(f"  EODHD_API_KEY: {'✓ configurée' if eod else '❌ MANQUANTE (requis)'}")
    print(f"  TE_API_KEY: {'✓ configurée' if te else '⚠ absente (optionnel)'}")
    
    return bool(eod)

def check_database():
    """Vérifie l'accès à la base de données."""
    try:
        from fx_impact_app.src.config import get_db_path
        import duckdb
        
        db_path = get_db_path()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with duckdb.connect(db_path) as con:
            con.execute("SELECT 1")
            
            # Vérifie les tables/vues critiques
            has_events = con.execute("""
                SELECT 1 FROM information_schema.tables 
                WHERE lower(table_name) = 'events'
            """).fetchone()
            
            if has_events:
                print(f"  ✓ Table 'events' présente")
            else:
                print(f"  ⚠ Table 'events' absente (normale si première utilisation)")
        
        print(f"✓ DB accessible: {db_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur DB: {e}")
        return False

def main():
    print("="*60)
    print("VÉRIFICATION FX IMPACT CALCULATOR")
    print("="*60)
    print()
    
    tests = [
        ("Structure", check_structure),
        ("Imports Python", check_imports),
        ("Variables d'environnement", check_env),
        ("Base de données", check_database),
    ]
    
    results = []
    for name, func in tests:
        print(f"[{name}]")
        results.append(func())
        print()
    
    print("="*60)
    if all(results):
        print("✅ Tous les tests passent !")
        print()
        print("Commandes pour démarrer:")
        print('  export PYTHONPATH="$(pwd)"')
        print("  streamlit run fx_impact_app/streamlit_app/Home.py")
        return 0
    else:
        print("❌ Certains tests échouent. Corrigez les erreurs ci-dessus.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

# ============================================================
# FONCTION PRINCIPALE D'APPLICATION DES CORRECTIONS
# ============================================================

def apply_all_fixes():
    """Applique toutes les corrections dans l'ordre."""
    
    print("\n" + "="*60)
    print("FX IMPACT CALCULATOR - CORRECTION COMPLÈTE")
    print("="*60 + "\n")
    
    # Vérification préalable
    if not SRC_DIR.exists():
        SRC_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✓ Création de {SRC_DIR}")
    
    # 1. regex_presets.py
    print("[1/5] Correction de regex_presets.py")
    path = SRC_DIR / "regex_presets.py"
    backup_file(path)
    path.write_text(REGEX_PRESETS_UNIFIED, encoding="utf-8")
    print(f"  ✓ Fichier unifié écrit\n")
    
    # 2. forecaster_mvp.py - ajout des fonctions
    print("[2/5] Ajout de compute_surprise() et HORIZONS dans forecaster_mvp.py")
    path = SRC_DIR / "forecaster_mvp.py"
    if path.exists():
        backup_file(path)
        content = path.read_text(encoding="utf-8")
        
        if "def compute_surprise" not in content:
            # Insérer après les imports
            lines = content.split("\n")
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("from fx_impact_app.src.config"):
                    insert_idx = i + 1
                    break
            
            lines.insert(insert_idx, FORECASTER_ADDITIONS)
            path.write_text("\n".join(lines), encoding="utf-8")
            print("  ✓ Fonctions ajoutées")
        else:
            print("  ✓ Fonctions déjà présentes")
    else:
        print("  ⚠ forecaster_mvp.py non trouvé")
    print()
    
    # 3. te_client.py - correction import
    print("[3/5] Correction de te_client.py")
    path = SRC_DIR / "te_client.py"
    if path.exists():
        backup_file(path)
        content = path.read_text(encoding="utf-8")
        
        # Remplace l'import incorrect
        content = content.replace(
            "from .config import load_env_keys",
            "from .config import get_te_key as _get_te_key_config"
        )
        
        # Remplace la fonction get_te_key si nécessaire
        if "def get_te_key(key_in:" in content:
            # Cherche et remplace la fonction
            import re
            pattern = r'def get_te_key\(key_in:.*?\n.*?return k'
            replacement = '''def get_te_key(key_in: Optional[str] = None) -> str:
    if key_in:
        return key_in
    k = _get_te_key_config()
    if not k:
        raise RuntimeError("Missing TE_API_KEY.")
    return k'''
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        path.write_text(content, encoding="utf-8")
        print("  ✓ Import corrigé\n")
    else:
        print("  ⚠ te_client.py non trouvé\n")
    
    # 4. db_init.py
    print("[4/5] Création de db_init.py")
    path = SRC_DIR / "db_init.py"
    path.write_text(DB_INIT_CONTENT, encoding="utf-8")
    print(f"  ✓ Créé: {path.relative_to(ROOT)}\n")
    
    # 5. check_setup.py
    print("[5/5] Création du script de vérification")
    path = ROOT / "check_setup.py"
    path.write_text(CHECK_SETUP_CONTENT, encoding="utf-8")
    path.chmod(0o755)
    print(f"  ✓ Créé: {path.relative_to(ROOT)}\n")
    
    print("="*60)
    print("✅ CORRECTIONS TERMINÉES !")
    print("="*60)
    print()
    print("PROCHAINES ÉTAPES:")
    print()
    print("1. Créez votre fichier .env à la racine:")
    print("   echo 'EODHD_API_KEY=votre_cle_ici' > .env")
    print()
    print("2. Vérifiez l'installation:")
    print("   python3 check_setup.py")
    print()
    print("3. Initialisez la base de données:")
    print("   python3 -m fx_impact_app.src.db_init")
    print()
    print("4. Lancez l'application:")
    print('   export PYTHONPATH="$(pwd)"')
    print("   streamlit run fx_impact_app/streamlit_app/Home.py")
    print()

if __name__ == "__main__":
    try:
        apply_all_fixes()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
