#!/usr/bin/env python3
"""
ORCHESTRATEUR PHASE 3 - SESSION 130
====================================

Lance séquentiellement ÉTAPES 6-7 du workflow :
6. Trouver clusters similaires
7. Calculer R² pour clusters

Usage : python run_phase3.py

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_script(script_name: str, description: str) -> bool:
    """
    Lance un script Python et capture résultat.
    
    Returns:
        True si succès, False sinon
    """
    print("\n" + "=" * 80)
    print(f"🚀 {description}")
    print("=" * 80)
    print(f"Script : {script_name}")
    print(f"Début : {datetime.now().strftime('%H:%M:%S')}\n")
    
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ Script introuvable : {script_path}")
        return False
    
    try:
        # Lancer script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=3600  # 1h max par script (scan peut être long)
        )
        
        # Afficher stdout
        if result.stdout:
            print(result.stdout)
        
        # Afficher stderr si erreur
        if result.returncode != 0:
            print(f"\n❌ ERREUR (code {result.returncode})")
            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr)
            return False
        
        print(f"\n✅ {description} - TERMINÉ")
        print(f"Fin : {datetime.now().strftime('%H:%M:%S')}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print(f"\n❌ TIMEOUT (> 1h)")
        return False
    except Exception as e:
        print(f"\n❌ EXCEPTION : {e}")
        return False


def main():
    """Lance PHASE 3 complète"""
    
    print("=" * 80)
    print("ORCHESTRATEUR PHASE 3 - WORKFLOW 10 ÉTAPES")
    print("=" * 80)
    print(f"Début : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Étapes prévues :")
    print("   6. Trouver clusters similaires (~30-45 min)")
    print("   7. Calculer R² clusters (~15-30 min)")
    print()
    print("⏱️  Durée estimée totale : ~1h")
    print()
    print("⚠️  NOTE : Étape 6 peut être longue (scan 3 ans)")
    print()
    
    input("Appuyez sur ENTRÉE pour démarrer...")
    
    # ÉTAPE 6 : Clusters similaires
    success6 = run_script(
        "find_similar_clusters.py",
        "ÉTAPE 6 : Trouver clusters similaires"
    )
    
    if not success6:
        print("\n❌ PHASE 3 INTERROMPUE - Échec Étape 6")
        return 1
    
    # ÉTAPE 7 : R² clusters
    success7 = run_script(
        "calculate_r2_clusters.py",
        "ÉTAPE 7 : Calculer R² clusters"
    )
    
    if not success7:
        print("\n❌ PHASE 3 INTERROMPUE - Échec Étape 7")
        return 1
    
    # Succès complet
    print("\n" + "=" * 80)
    print("✅✅✅ PHASE 3 TERMINÉE AVEC SUCCÈS ✅✅✅")
    print("=" * 80)
    print(f"Fin : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📂 Fichiers créés :")
    print("   ✅ reference_cases_with_similar_clusters.json")
    print("   ✅ reference_cases_with_r2_clusters.json")
    print()
    print("🎯 PROCHAINE ÉTAPE : PHASE 4 (Modélisation)")
    print("   Ou : Arrêter et documenter Session 130")
    print()
    print("📊 PHASES COMPLÉTÉES :")
    print("   ✅ PHASE 1 : Scanner 100 mouvements")
    print("   ✅ PHASE 2 : Amplifications idéales 5 patterns")
    print("   ✅ PHASE 3 : Clusters similaires + R²")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ INTERRUPTION UTILISATEUR")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR FATALE : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
