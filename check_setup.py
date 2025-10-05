#!/usr/bin/env python3
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
