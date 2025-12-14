#!/usr/bin/env python3
"""
SESSION 128 - SCRIPT DE LANCEMENT : TESTS NON-RÉGRESSION COMPLETS
==================================================================
Exécute les 3 tests de validation système en séquence

Tests :
1. Mapping variantes (20 cas + comparaison baseline)
2. Pipeline calibration (fonction universelle + imports)
3. Cas référence 11 septembre 2025

Génère rapport consolidé avec synthèse globale

Auteur : André Valentin
Date : 12 novembre 2025
"""
import sys
from pathlib import Path
import subprocess
from datetime import datetime


def run_test(test_script: str, test_name: str) -> dict:
    """
    Exécute un test et capture résultats
    
    Returns:
        dict avec success, output, return_code
    """
    print("=" * 80)
    print(f"EXÉCUTION : {test_name}")
    print("=" * 80)
    print()
    
    script_path = Path(__file__).parent / test_script
    
    if not script_path.exists():
        print(f"❌ Script introuvable : {script_path}")
        return {
            'success': False,
            'output': f"Script introuvable: {script_path}",
            'return_code': 1,
            'test_name': test_name
        }
    
    try:
        # Exécuter script Python
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max par test
        )
        
        # Afficher output
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        success = result.returncode == 0
        
        return {
            'success': success,
            'output': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode,
            'test_name': test_name
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT : Test dépasse 5 minutes")
        return {
            'success': False,
            'output': "Timeout après 5 minutes",
            'return_code': 124,
            'test_name': test_name
        }
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return {
            'success': False,
            'output': str(e),
            'return_code': 1,
            'test_name': test_name
        }


def generate_consolidated_report(results: list, output_path: Path):
    """Génère rapport consolidé Markdown"""
    
    report = []
    report.append("# SESSION 128 - RAPPORT TESTS NON-RÉGRESSION")
    report.append("")
    report.append(f"**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Synthèse globale
    report.append("## 📊 SYNTHÈSE GLOBALE")
    report.append("")
    
    total_tests = len(results)
    success_count = sum(1 for r in results if r['success'])
    
    report.append(f"Tests exécutés : **{total_tests}**")
    report.append(f"Tests réussis  : **{success_count}/{total_tests}** ({success_count/total_tests*100:.0f}%)")
    report.append("")
    
    # Détails par test
    report.append("## 📝 DÉTAILS PAR TEST")
    report.append("")
    
    for idx, result in enumerate(results, 1):
        status = "✅ SUCCÈS" if result['success'] else "❌ ÉCHEC"
        report.append(f"### Test {idx} : {result['test_name']}")
        report.append(f"**Statut :** {status}")
        report.append(f"**Return code :** {result['return_code']}")
        report.append("")
        
        # Extraire métriques clés de l'output (si disponible)
        if result['success']:
            # Parser output pour métriques
            lines = result['output'].split('\n')
            for line in lines:
                if 'SUCCÈS' in line or 'Critère' in line or 'amélioration' in line.lower():
                    report.append(f"  - {line.strip()}")
        else:
            report.append(f"**Erreur :** Voir détails ci-dessous")
        
        report.append("")
    
    # Verdict final
    report.append("## 🎯 VERDICT FINAL")
    report.append("")
    
    if success_count == total_tests:
        report.append("✅✅✅ **TOUS TESTS RÉUSSIS**")
        report.append("")
        report.append("**Session 127 validée :**")
        report.append("- Mapping variantes opérationnel")
        report.append("- Pipeline calibration intact")
        report.append("- Cas référence validé")
        report.append("")
        report.append("**Prêt pour ÉTAPE 2 : Intégration Planificateur V2.5**")
    elif success_count >= total_tests * 0.66:
        report.append("⚠️ **SUCCÈS PARTIEL**")
        report.append("")
        report.append(f"{total_tests - success_count} test(s) échoué(s)")
        report.append("")
        report.append("**ACTION REQUISE :**")
        report.append("- Analyser tests échoués")
        report.append("- Corriger si nécessaire")
        report.append("- Relancer validation")
    else:
        report.append("❌ **ÉCHEC GLOBAL**")
        report.append("")
        report.append(f"{total_tests - success_count} test(s) échoué(s)")
        report.append("")
        report.append("**ACTION URGENTE :**")
        report.append("- Vérifier Session 127 (mapping variantes)")
        report.append("- Vérifier imports et dépendances")
        report.append("- Relancer tests après corrections")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("**Auteur :** André Valentin avec Claude")
    report.append(f"**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Écrire rapport
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n✅ Rapport consolidé : {output_path}")


def main():
    print("=" * 80)
    print("SESSION 128 - LANCEMENT TESTS NON-RÉGRESSION COMPLETS")
    print("=" * 80)
    print()
    print("3 tests seront exécutés en séquence :")
    print("  1. Test mapping variantes (20 cas)")
    print("  2. Test pipeline calibration")
    print("  3. Test cas référence 11 septembre")
    print()
    print("Durée estimée : 5-10 minutes")
    print()
    input("Appuyez sur ENTRÉE pour démarrer...")
    print()
    
    # ========================================================================
    # DÉFINITION TESTS
    # ========================================================================
    
    tests = [
        ('test_1_mapping_variants_non_regression.py', 'Mapping Variantes (20 cas)'),
        ('test_2_pipeline_calibration_non_regression.py', 'Pipeline Calibration'),
        ('test_3_reference_case_11_sept.py', 'Cas Référence 11 Septembre'),
    ]
    
    # ========================================================================
    # EXÉCUTION TESTS
    # ========================================================================
    
    results = []
    
    for test_script, test_name in tests:
        result = run_test(test_script, test_name)
        results.append(result)
        
        print()
        
        if not result['success']:
            print(f"⚠️  Test échoué : {test_name}")
            print("   Continuer avec tests suivants ? (o/n)")
            choice = input().lower()
            if choice != 'o':
                print("Arrêt prématuré.")
                break
        
        print()
    
    # ========================================================================
    # SYNTHÈSE GLOBALE
    # ========================================================================
    
    print("=" * 80)
    print("SYNTHÈSE GLOBALE TESTS NON-RÉGRESSION")
    print("=" * 80)
    print()
    
    success_count = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Tests exécutés : {total}")
    print(f"Tests réussis  : {success_count}/{total} ({success_count/total*100:.0f}%)")
    print()
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test_name']}")
    
    print()
    
    # ========================================================================
    # GÉNÉRATION RAPPORT
    # ========================================================================
    
    output_path = Path(__file__).parent / "RAPPORT_TESTS_NON_REGRESSION.md"
    generate_consolidated_report(results, output_path)
    
    print()
    
    # ========================================================================
    # VERDICT FINAL
    # ========================================================================
    
    print("=" * 80)
    print("VERDICT FINAL")
    print("=" * 80)
    print()
    
    if success_count == total:
        print("✅✅✅ TOUS TESTS RÉUSSIS")
        print()
        print("Session 127 validée :")
        print("  - Mapping variantes opérationnel")
        print("  - Pipeline calibration intact")
        print("  - Cas référence validé")
        print()
        print("🚀 PRÊT POUR ÉTAPE 2 : Intégration Planificateur V2.5")
        return_code = 0
    elif success_count >= total * 0.66:
        print("⚠️  SUCCÈS PARTIEL")
        print()
        print(f"{total - success_count} test(s) échoué(s)")
        print()
        print("ACTION REQUISE :")
        print("  - Analyser rapport : RAPPORT_TESTS_NON_REGRESSION.md")
        print("  - Corriger tests échoués")
        print("  - Relancer validation")
        return_code = 0
    else:
        print("❌ ÉCHEC GLOBAL")
        print()
        print(f"{total - success_count} test(s) échoué(s)")
        print()
        print("ACTION URGENTE :")
        print("  - Vérifier rapport : RAPPORT_TESTS_NON_REGRESSION.md")
        print("  - Corriger problèmes critiques")
        print("  - Relancer validation complète")
        return_code = 1
    
    print()
    print(f"📄 Rapport complet : {output_path}")
    print()
    print("=" * 80)
    print("FIN TESTS NON-RÉGRESSION")
    print("=" * 80)
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())
