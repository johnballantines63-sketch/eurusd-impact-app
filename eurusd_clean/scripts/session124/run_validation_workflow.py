"""
Workflow Complet Session 124
=============================

Script orchestrateur qui exécute toutes les étapes de la validation multi-dates.

ÉTAPES:
1. Test setup environnement
2. Scanner 2024-2025 avec Rev12
3. Validation formules S115
4. Analyse résultats
5. Génération rapport final

USAGE:
    python run_validation_workflow.py [--skip-scan]
    
OPTIONS:
    --skip-scan : Sauter le scan (utiliser résultats existants)
"""

import sys
import subprocess
from pathlib import Path
import argparse


# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPTS_DIR = Path(__file__).parent

SCRIPTS = {
    'test': SCRIPTS_DIR / 'test_scan_setup.py',
    'scan': SCRIPTS_DIR / 'scan_with_rev12.py',
    'validate': SCRIPTS_DIR / 'validate_formulas_multidates.py',
    'analyze': SCRIPTS_DIR / 'analyze_results.py'
}


# ============================================================================
# EXÉCUTION ÉTAPES
# ============================================================================

def run_step(step_name: str, script_path: Path, args: list = None) -> bool:
    """
    Exécuter une étape du workflow.
    
    Args:
        step_name: Nom étape (pour affichage)
        script_path: Path vers script Python
        args: Arguments supplémentaires (optionnel)
    
    Returns:
        True si succès, False sinon
    """
    print("\n" + "="*80)
    print(f"ÉTAPE: {step_name}")
    print("="*80)
    
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ {step_name} - SUCCÈS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {step_name} - ÉCHEC (code {e.returncode})")
        return False


def check_files():
    """Vérifier que tous les scripts nécessaires existent"""
    missing = []
    
    for name, path in SCRIPTS.items():
        if not path.exists():
            missing.append(f"{name}: {path}")
    
    if missing:
        print("❌ Scripts manquants:")
        for m in missing:
            print(f"   - {m}")
        return False
    
    return True


# ============================================================================
# WORKFLOW
# ============================================================================

def run_workflow(skip_scan: bool = False):
    """
    Exécuter workflow complet.
    
    Args:
        skip_scan: Si True, sauter l'étape scan (utiliser résultats existants)
    
    Returns:
        True si workflow complet, False si erreur
    """
    print("\n" + "="*80)
    print("WORKFLOW VALIDATION MULTI-DATES - SESSION 124")
    print("="*80)
    
    # Vérifier scripts
    if not check_files():
        return False
    
    # ÉTAPE 1: Test environnement
    if not run_step("Test Setup", SCRIPTS['test']):
        print("\n⚠️  Tests environnement échoués. Corriger avant continuer.")
        return False
    
    # ÉTAPE 2: Scanner 2024-2025 (optionnel si skip_scan)
    if skip_scan:
        print("\n⏭️  Scan ignoré (--skip-scan)")
        
        # Vérifier que fichier résultats existe
        patterns_file = SCRIPTS_DIR / 'double_waves_rev12.json'
        if not patterns_file.exists():
            print(f"❌ Fichier patterns non trouvé: {patterns_file}")
            print("   Impossible de sauter scan sans résultats existants")
            return False
    else:
        if not run_step("Scanner 2024-2025", SCRIPTS['scan']):
            print("\n⚠️  Scan échoué. Vérifier logs.")
            return False
    
    # ÉTAPE 3: Validation formules
    if not run_step("Validation Formules S115", SCRIPTS['validate']):
        print("\n⚠️  Validation échouée. Vérifier logs.")
        return False
    
    # ÉTAPE 4: Analyse résultats
    if not run_step("Analyse Résultats", SCRIPTS['analyze']):
        print("\n⚠️  Analyse échouée. Vérifier logs.")
        return False
    
    # Succès complet
    print("\n" + "="*80)
    print("✅ WORKFLOW COMPLET - SUCCÈS")
    print("="*80)
    
    # Résumé fichiers générés
    print("\n📁 Fichiers générés:")
    
    files = [
        ('Patterns détectés', SCRIPTS_DIR / 'double_waves_rev12.json'),
        ('Résultats CSV', SCRIPTS_DIR / 'double_waves_summary.csv'),
        ('Résultats validation', SCRIPTS_DIR / 'validation_results.json'),
        ('Rapport final', SCRIPTS_DIR / 'VALIDATION_REPORT.md')
    ]
    
    for name, path in files:
        if path.exists():
            size = path.stat().st_size
            if size > 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size} bytes"
            print(f"   ✅ {name}: {path.name} ({size_str})")
        else:
            print(f"   ❌ {name}: {path.name} (non trouvé)")
    
    print("\n🎯 PROCHAINES ÉTAPES:")
    print("   1. Lire VALIDATION_REPORT.md")
    print("   2. Vérifier critères succès atteints")
    print("   3. Si succès: Session 125 (Planificateur V2.9)")
    print("   4. Si échec: Ajuster paramètres et re-valider")
    
    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Point d'entrée"""
    parser = argparse.ArgumentParser(
        description='Workflow complet validation multi-dates Session 124'
    )
    parser.add_argument(
        '--skip-scan',
        action='store_true',
        help='Sauter étape scan (utiliser résultats existants)'
    )
    
    args = parser.parse_args()
    
    success = run_workflow(skip_scan=args.skip_scan)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
