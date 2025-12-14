#!/usr/bin/env python3
"""
ORCHESTRATEUR PHASE 1 - SESSION 130
====================================

Lance séquentiellement ÉTAPES 1-3 du workflow :
1. Scanner mouvements 2023-2025
2. Classifier patterns
3. Définir cas de référence

Usage : python run_phase1.py

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
            timeout=3600  # 1h max par script
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
    """Lance PHASE 1 complète"""
    
    print("=" * 80)
    print("ORCHESTRATEUR PHASE 1 - WORKFLOW 10 ÉTAPES")
    print("=" * 80)
    print(f"Début : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 Étapes prévues :")
    print("   1. Scanner mouvements 2023-2025 (~30-45 min)")
    print("   2. Classifier patterns (~2 min)")
    print("   3. Définir cas référence (~1 min)")
    print()
    print("⏱️  Durée estimée totale : ~45 min")
    print()
    
    input("Appuyez sur ENTRÉE pour démarrer...")
    
    # ÉTAPE 1 : Scanner
    success1 = run_script(
        "scan_by_month.py",
        "ÉTAPE 1 : Scanner mouvements 2023-2025"
    )
    
    if not success1:
        print("\n❌ PHASE 1 INTERROMPUE - Échec Étape 1")
        return 1
    
    # ÉTAPE 2 : Classification
    success2 = run_script(
        "classify_patterns.py",
        "ÉTAPE 2 : Classifier patterns"
    )
    
    if not success2:
        print("\n❌ PHASE 1 INTERROMPUE - Échec Étape 2")
        return 1
    
    # ÉTAPE 3 : Cas référence
    success3 = run_script(
        "define_reference_cases.py",
        "ÉTAPE 3 : Définir cas de référence"
    )
    
    if not success3:
        print("\n❌ PHASE 1 INTERROMPUE - Échec Étape 3")
        return 1
    
    # Succès complet
    print("\n" + "=" * 80)
    print("✅✅✅ PHASE 1 TERMINÉE AVEC SUCCÈS ✅✅✅")
    print("=" * 80)
    print(f"Fin : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📂 Fichiers créés :")
    print("   ✅ movements_2023_2025_complete.json")
    print("   ✅ patterns_classified.json")
    print("   ✅ reference_cases.json")
    print()
    print("🎯 PROCHAINE ÉTAPE : PHASE 2 (Calibration)")
    print("   Script : run_phase2.py (à créer)")
    print("   OU : Lancer manuellement calculate_ideal_amplifications.py")
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
