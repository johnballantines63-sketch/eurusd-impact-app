#!/usr/bin/env python3
"""
ORCHESTRATEUR PHASE 2 - SESSION 130
====================================

Lance séquentiellement ÉTAPES 4-5 du workflow :
4. Calculer amplifications idéales
5. Établir table référence

Usage : python run_phase2.py

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
            timeout=600  # 10 min max par script
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
        print(f"\n❌ TIMEOUT (> 10 min)")
        return False
    except Exception as e:
        print(f"\n❌ EXCEPTION : {e}")
        return False


def main():
    """Lance PHASE 2 complète"""
    
    print("=" * 80)
    print("ORCHESTRATEUR PHASE 2 - WORKFLOW 10 ÉTAPES")
    print("=" * 80)
    print(f"Début : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Étapes prévues :")
    print("   4. Calculer amplifications idéales (~5-10 min)")
    print("   5. Établir table référence (~1 min)")
    print()
    print("⏱️  Durée estimée totale : ~10 min")
    print()
    
    input("Appuyez sur ENTRÉE pour démarrer...")
    
    # ÉTAPE 4 : Amplifications idéales
    success4 = run_script(
        "calculate_ideal_amplifications.py",
        "ÉTAPE 4 : Calculer amplifications idéales"
    )
    
    if not success4:
        print("\n❌ PHASE 2 INTERROMPUE - Échec Étape 4")
        return 1
    
    # ÉTAPE 5 : Table référence
    success5 = run_script(
        "create_reference_table.py",
        "ÉTAPE 5 : Établir table référence"
    )
    
    if not success5:
        print("\n❌ PHASE 2 INTERROMPUE - Échec Étape 5")
        return 1
    
    # Succès complet
    print("\n" + "=" * 80)
    print("✅✅✅ PHASE 2 TERMINÉE AVEC SUCCÈS ✅✅✅")
    print("=" * 80)
    print(f"Fin : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📂 Fichiers créés :")
    print("   ✅ reference_cases_with_amplifications.json")
    print("   ✅ REFERENCE_TABLE.md")
    print()
    print("🎯 PROCHAINE ÉTAPE : PHASE 3 (Recherche similarités)")
    print("   Ou : Arrêter et documenter Session 130")
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
