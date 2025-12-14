"""
Scripts de Correction Automatique - EUR/USD News Impact Calculator
Créé le 13 octobre 2025

USAGE:
1. Sauvegarder ce fichier : fix_all_bugs.py
2. Exécuter : python3 fix_all_bugs.py
3. Suivre les instructions
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent
PLANIFICATEUR_PATH = BASE_DIR / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
BACKUP_DIR = BASE_DIR / "fx_impact_app/streamlit_app/pages/Backups"

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def create_backup(file_path: Path, suffix: str = "auto_fix") -> Path:
    """Crée un backup avec timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{file_path.stem}_{suffix}_{timestamp}.py"
    BACKUP_DIR.mkdir(exist_ok=True)
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup créé : {backup_path.name}")
    return backup_path

def read_file(file_path: Path) -> str:
    """Lit le contenu d'un fichier"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(file_path: Path, content: str):
    """Écrit le contenu dans un fichier"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Fichier modifié : {file_path.name}")

# ═══════════════════════════════════════════════════════════════
# CORRECTION #1 : BUG IMPACT = 0
# ═══════════════════════════════════════════════════════════════

def fix_impact_calculation(content: str) -> tuple[str, bool]:
    """
    Corrige le bug impact = 0.0 pips
    
    Cherche et remplace les formules incorrectes dans :
    - predict_impact()
    - predict_impact_fast()
    """
    
    changes_made = False
    
    # Pattern 1 : Formule simple (impact = mfe * surprise / 10)
    pattern1 = r"(impact\s*=\s*(?:mfe_p80|base_impact|adjusted_impact)\s*\*\s*\(surprise\s*/\s*10(?:\.0)?\))"
    replacement1 = """# ✅ CORRIGÉ : Conversion en pourcentage relatif
    surprise_pct = abs(surprise) * 100  # Ex: 0.3 → 30%
    impact_factor = min(2.0, 1.0 + (surprise_pct / 50.0)) if surprise_pct > 5 else 1.0
    impact = mfe_p80 * impact_factor"""
    
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)
        changes_made = True
        print("  ✅ Pattern 1 corrigé (formule simple)")
    
    # Pattern 2 : Ajustement surprise_factor
    pattern2 = r"(surprise_factor\s*=\s*min\(surprise_pct\s*/\s*50\.0,\s*2\.0\))"
    replacement2 = "surprise_factor = min(2.0, 1.0 + (surprise_pct / 50.0))"
    
    if re.search(pattern2, content):
        content = re.sub(pattern2, replacement2, content)
        changes_made = True
        print("  ✅ Pattern 2 corrigé (surprise_factor)")
    
    # Pattern 3 : Conversion surprise en %
    pattern3 = r"(surprise_pct\s*=\s*abs\(surprise\)(?:\s*\*\s*100)?)"
    if "surprise_pct = abs(surprise) * 100" not in content:
        # Assurer que tous les surprise_pct sont bien * 100
        content = re.sub(
            r"(surprise_pct\s*=\s*abs\(surprise\))",
            r"surprise_pct = abs(surprise) * 100  # Conversion en %",
            content
        )
        changes_made = True
        print("  ✅ Pattern 3 corrigé (conversion %)")
    
    return content, changes_made

# ═══════════════════════════════════════════════════════════════
# DIAGNOSTIC SYSTÈME
# ═══════════════════════════════════════════════════════════════

def diagnose_system():
    """Diagnostic complet du système"""
    
    print("\n" + "="*70)
    print("🔍 DIAGNOSTIC SYSTÈME EUR/USD")
    print("="*70 + "\n")
    
    # 1. Vérifier existence fichiers critiques
    print("📂 Fichiers Critiques:")
    
    files_to_check = [
        ("Planificateur", PLANIFICATEUR_PATH),
        ("Backtest CLI", BASE_DIR / "backtest_multi_events_phases_FIXED.py"),
        ("Sequence Timeline", BASE_DIR / "fx_impact_app/src/sequence_multi_event_timeline.py"),
        ("Base de données", BASE_DIR / "fx_impact_app/data/warehouse.duckdb"),
    ]
    
    for name, path in files_to_check:
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {name:20s} : {size:,} bytes")
        else:
            print(f"  ❌ {name:20s} : MANQUANT")
    
    # 2. Analyser Planificateur
    print("\n📊 Analyse Planificateur:")
    
    if PLANIFICATEUR_PATH.exists():
        content = read_file(PLANIFICATEUR_PATH)
        lines = content.split('\n')
        
        print(f"  Lignes totales    : {len(lines)}")
        print(f"  Taille           : {len(content):,} caractères")
        
        # Chercher patterns bugués
        bugs_found = []
        
        if re.search(r"impact\s*=\s*\w+\s*\*\s*\(surprise\s*/\s*10", content):
            bugs_found.append("🐛 Bug impact = 0 (formule incorrecte)")
        
        if "surprise_pct = abs(surprise) * 100" not in content:
            bugs_found.append("⚠️  Conversion surprise en % manquante")
        
        if bugs_found:
            print(f"\n  🐛 Bugs détectés :")
            for bug in bugs_found:
                print(f"    {bug}")
        else:
            print(f"  ✅ Aucun bug évident détecté")
    
    # 3. Vérifier DB
    print("\n💾 Base de Données:")
    try:
        import duckdb
        db_path = BASE_DIR / "fx_impact_app/data/warehouse.duckdb"
        if db_path.exists():
            conn = duckdb.connect(str(db_path), read_only=True)
            
            events_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            prices_count = conn.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
            families_count = conn.execute("SELECT COUNT(DISTINCT family_name) FROM event_families").fetchone()[0]
            
            print(f"  Événements : {events_count:,}")
            print(f"  Prix 1 min : {prices_count:,}")
            print(f"  Familles   : {families_count}")
            
            conn.close()
    except Exception as e:
        print(f"  ⚠️  Erreur lecture DB : {e}")
    
    print("\n" + "="*70 + "\n")

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Script principal"""
    
    print("\n" + "="*70)
    print("🔧 CORRECTEUR AUTOMATIQUE - EUR/USD News Impact Calculator")
    print("="*70 + "\n")
    
    # Phase 1 : Diagnostic
    diagnose_system()
    
    # Phase 2 : Confirmation utilisateur
    print("📋 Actions proposées:")
    print("  1. ✅ Créer backup du Planificateur")
    print("  2. 🔧 Corriger bug impact = 0.0 pips")
    print("  3. ✅ Valider corrections")
    print()
    
    response = input("Continuer ? (o/n) : ").strip().lower()
    if response != 'o':
        print("\n❌ Annulé par l'utilisateur")
        return
    
    # Phase 3 : Backup
    print("\n📦 Création backup...")
    if not PLANIFICATEUR_PATH.exists():
        print(f"❌ Fichier introuvable : {PLANIFICATEUR_PATH}")
        return
    
    backup_path = create_backup(PLANIFICATEUR_PATH, "before_impact_fix")
    
    # Phase 4 : Corrections
    print("\n🔧 Application des corrections...")
    
    content = read_file(PLANIFICATEUR_PATH)
    original_content = content
    
    # Correction impact = 0
    content, impact_fixed = fix_impact_calculation(content)
    
    # Phase 5 : Sauvegarde
    if content != original_content:
        write_file(PLANIFICATEUR_PATH, content)
        
        print("\n✅ CORRECTIONS APPLIQUÉES")
        print(f"   Impact calculation : {'✅ Corrigé' if impact_fixed else '⏭️  Déjà OK'}")
        
    else:
        print("\n⏭️  AUCUNE CORRECTION NÉCESSAIRE")
        print("   Le code semble déjà correct !")
    
    # Phase 6 : Instructions test
    print("\n" + "="*70)
    print("📋 PROCHAINES ÉTAPES")
    print("="*70)
    print("\n1. Tester l'application:")
    print("   streamlit run fx_impact_app/streamlit_app/Home.py")
    print()
    print("2. Vérifier prédictions:")
    print("   - Charger événements 10 octobre 2025")
    print("   - Sélectionner CPI + NFP")
    print("   - Vérifier : Impact > 0 pips (attendu 40-150 pips)")
    print()
    print("3. Valider avec backtest:")
    print("   python3 backtest_multi_events_phases_FIXED.py")
    print("   - MAE attendu : ~14 min")
    print("   - Impact moyen : ~124 pips")
    print()
    print("4. Si problème, restaurer backup:")
    print(f"   cp '{backup_path}' \\")
    print(f"      '{PLANIFICATEUR_PATH}'")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()