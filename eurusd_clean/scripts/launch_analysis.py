#!/usr/bin/env python3
"""
Launcher Script - Session 63 Pattern W Analysis
Simplifie l'exécution des scripts d'analyse
"""

import subprocess
import sys
from pathlib import Path

def print_header(title):
    """Affiche un header formaté"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def run_script(script_path, description):
    """Exécute un script Python et affiche le résultat"""
    print(f"🚀 {description}...\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Warnings:")
            print(result.stderr)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution:\n")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def main():
    """Fonction principale"""
    print_header("SESSION 63 - ANALYSE PATTERN W CPI")
    
    # Déterminer le répertoire du projet
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Chemins des scripts
    test_infra = project_root / "scripts" / "analysis" / "test_infrastructure.py"
    analyze_pattern = project_root / "scripts" / "analysis" / "analyze_cpi_pattern_w.py"
    
    # Menu
    print("Que voulez-vous faire ?\n")
    print("1. Test infrastructure uniquement")
    print("2. Analyse Pattern W complète")
    print("3. Les deux (test + analyse)")
    print("0. Quitter\n")
    
    choice = input("Votre choix (0-3): ").strip()
    
    if choice == "0":
        print("\n👋 Au revoir !")
        return
    
    elif choice == "1":
        print_header("TEST INFRASTRUCTURE")
        if run_script(test_infra, "Test de l'infrastructure"):
            print("\n✅ Test terminé avec succès")
        else:
            print("\n❌ Test échoué")
            sys.exit(1)
    
    elif choice == "2":
        print_header("ANALYSE PATTERN W")
        if run_script(analyze_pattern, "Analyse complète Pattern W"):
            print("\n✅ Analyse terminée avec succès")
            
            # Indiquer où trouver les résultats
            results_path = project_root / "scripts" / "analysis" / "cpi_pattern_analysis_results.csv"
            print(f"\n📁 Résultats sauvegardés dans:")
            print(f"   {results_path}")
        else:
            print("\n❌ Analyse échouée")
            sys.exit(1)
    
    elif choice == "3":
        # Test d'abord
        print_header("ÉTAPE 1/2 : TEST INFRASTRUCTURE")
        if not run_script(test_infra, "Test de l'infrastructure"):
            print("\n❌ Test infrastructure échoué. Abandon de l'analyse.")
            sys.exit(1)
        
        print("\n✅ Test réussi ! Passage à l'analyse...\n")
        input("Appuyez sur Entrée pour continuer...")
        
        # Puis analyse
        print_header("ÉTAPE 2/2 : ANALYSE PATTERN W")
        if run_script(analyze_pattern, "Analyse complète Pattern W"):
            print("\n✅ Analyse terminée avec succès")
            
            results_path = project_root / "scripts" / "analysis" / "cpi_pattern_analysis_results.csv"
            print(f"\n📁 Résultats sauvegardés dans:")
            print(f"   {results_path}")
        else:
            print("\n❌ Analyse échouée")
            sys.exit(1)
    
    else:
        print("\n❌ Choix invalide")
        sys.exit(1)
    
    print_header("SESSION 63 - TERMINÉ")
    print("📊 Prochaines étapes:")
    print("   1. Consulter le fichier CSV généré")
    print("   2. Analyser la fréquence du Pattern W")
    print("   3. Décider de la stratégie de modélisation\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interruption utilisateur. Au revoir !")
        sys.exit(0)
