#!/usr/bin/env python3
"""
Script de Diagnostic Complet - EUR/USD News Impact Calculator
Vérifie l'état du système SANS MODIFIER aucun fichier

USAGE: python3 1_diagnostic_complet.py
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Détecter le répertoire racine du projet
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator MPC")
PLANIFICATEUR = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
DB_PATH = PROJECT_ROOT / "fx_impact_app/data/warehouse.duckdb"
BACKTEST_CLI = PROJECT_ROOT / "backtest_multi_events_phases_FIXED.py"

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def print_header(title):
    """Affiche un titre formaté"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_section(title):
    """Affiche un sous-titre"""
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")

def check_file(path, name):
    """Vérifie l'existence d'un fichier et retourne ses infos"""
    if path.exists():
        size = path.stat().st_size
        return True, f"✅ {name:30s} : {size:>12,} bytes"
    else:
        return False, f"❌ {name:30s} : MANQUANT"

def read_file_safe(path):
    """Lit un fichier en toute sécurité"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None

# ═══════════════════════════════════════════════════════════════
# DIAGNOSTIC FICHIERS
# ═══════════════════════════════════════════════════════════════

def diagnose_files():
    """Diagnostic des fichiers critiques"""
    print_section("📂 FICHIERS CRITIQUES")
    
    files = [
        (PLANIFICATEUR, "Planificateur Multi-Événements"),
        (BACKTEST_CLI, "Backtest CLI (FIXED)"),
        (PROJECT_ROOT / "fx_impact_app/src/sequence_multi_event_timeline.py", "Timeline Séquentielle v8.4"),
        (PROJECT_ROOT / "fx_impact_app/src/latency_analyzer.py", "Latency Analyzer"),
        (PROJECT_ROOT / "fx_impact_app/src/scoring_engine.py", "Scoring Engine"),
        (PROJECT_ROOT / "fx_impact_app/src/forecaster_mvp.py", "Forecaster MVP"),
        (PROJECT_ROOT / "fx_impact_app/src/event_families.py", "Event Families"),
        (DB_PATH, "Base de données DuckDB"),
    ]
    
    all_ok = True
    for path, name in files:
        ok, msg = check_file(path, name)
        print(f"  {msg}")
        if not ok:
            all_ok = False
    
    return all_ok

# ═══════════════════════════════════════════════════════════════
# DIAGNOSTIC PLANIFICATEUR
# ═══════════════════════════════════════════════════════════════

def diagnose_planificateur():
    """Analyse détaillée du fichier Planificateur"""
    print_section("📊 ANALYSE PLANIFICATEUR")
    
    if not PLANIFICATEUR.exists():
        print("  ❌ Fichier Planificateur introuvable")
        return False
    
    content = read_file_safe(PLANIFICATEUR)
    if content is None:
        print("  ❌ Erreur lecture fichier")
        return False
    
    lines = content.split('\n')
    
    print(f"  Lignes totales     : {len(lines):>6,}")
    print(f"  Caractères         : {len(content):>6,}")
    print(f"  Taille             : {PLANIFICATEUR.stat().st_size:>6,} bytes")
    
    # Détection bugs
    print("\n  🔍 Recherche de bugs connus...")
    
    bugs = []
    
    # Bug #1 : Impact = 0
    pattern_impact_bug = r"impact\s*=\s*\w+\s*\*\s*\((?:surprise|abs\(surprise\))\s*/\s*10(?:\.0)?\)"
    if re.search(pattern_impact_bug, content):
        bugs.append({
            'id': 1,
            'severity': '🔴',
            'name': 'Impact = 0.0 pips',
            'description': 'Formule incorrecte dans predict_impact()',
            'pattern': 'impact = mfe * (surprise / 10)',
            'fixable': True
        })
    
    # Bug #2 : Conversion surprise manquante
    if "surprise_pct = abs(surprise) * 100" not in content:
        bugs.append({
            'id': 2,
            'severity': '🟠',
            'name': 'Conversion surprise en %',
            'description': 'Conversion manquante ou incorrecte',
            'pattern': 'surprise_pct sans * 100',
            'fixable': True
        })
    
    if bugs:
        print(f"\n  ⚠️  {len(bugs)} bug(s) détecté(s) :\n")
        for bug in bugs:
            print(f"    {bug['severity']} Bug #{bug['id']} : {bug['name']}")
            print(f"       Description : {bug['description']}")
            print(f"       Pattern     : {bug['pattern']}")
            print(f"       Corrigeable : {'✅ Oui' if bug['fixable'] else '❌ Non'}")
            print()
        return bugs
    else:
        print("\n  ✅ Aucun bug évident détecté")
        return []

# ═══════════════════════════════════════════════════════════════
# DIAGNOSTIC BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════

def diagnose_database():
    """Diagnostic de la base de données"""
    print_section("💾 BASE DE DONNÉES")
    
    if not DB_PATH.exists():
        print("  ❌ Base de données introuvable")
        return False
    
    try:
        import duckdb
        
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Compter éléments
        events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        prices = conn.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
        families = conn.execute("SELECT COUNT(DISTINCT family_name) FROM event_families").fetchone()[0]
        
        conn.close()
        
        print(f"  Événements         : {events:>12,}")
        print(f"  Prix 1 minute      : {prices:>12,}")
        print(f"  Familles           : {families:>12}")
        
        if prices < 1000000:
            print("  ⚠️  Attention : Moins de 1M prix")
        else:
            print("  ✅ Données suffisantes")
        
        return True
        
    except ImportError:
        print("  ⚠️  Module duckdb non installé")
        return False
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        return False

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Script principal de diagnostic"""
    
    print_header("🔍 DIAGNOSTIC COMPLET - EUR/USD News Impact Calculator")
    print(f"\n  Exécuté le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Répertoire : {PROJECT_ROOT}")
    
    # Phase 1 : Fichiers
    files_ok = diagnose_files()
    
    # Phase 2 : Planificateur
    bugs = diagnose_planificateur()
    
    # Phase 3 : Base de données
    db_ok = diagnose_database()
    
    # Résumé final
    print_header("📊 RÉSUMÉ DIAGNOSTIC")
    
    print(f"\n  Fichiers critiques   : {'✅ OK' if files_ok else '❌ MANQUANT'}")
    print(f"  Base de données      : {'✅ OK' if db_ok else '❌ PROBLÈME'}")
    print(f"  Bugs détectés        : {len(bugs) if bugs else '✅ Aucun'}")
    
    if bugs:
        fixable = len([b for b in bugs if b['fixable']])
        print(f"  Bugs corrigeables    : {fixable}/{len(bugs)}")
        print("\n  📝 Prochaine étape :")
        print("     python3 2_correction_automatique.py")
    
    print("\n" + "="*70 + "\n")
    
    sys.exit(1 if bugs else 0)

if __name__ == "__main__":
    main()
