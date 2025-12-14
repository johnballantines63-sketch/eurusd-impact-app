"""
Orchestration workflow complet - Double source

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Double source

WORKFLOW:
1. Télécharger JBlanked 2020-2025
2. Télécharger EODHD 2020-2025
3. Merger sources → Master
4. Import DB
5. Validation
"""

import subprocess
import sys
from pathlib import Path
import time

def run_script(script_name: str, description: str):
    """Exécuter script Python"""
    
    print("=" * 80)
    print(f"▶️  {description}")
    print("=" * 80)
    print()
    
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ Script non trouvé: {script_name}")
        return False
    
    start = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            check=True
        )
        
        elapsed = time.time() - start
        print()
        print(f"✅ Terminé en {elapsed:.1f}s")
        print()
        return True
    
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start
        print()
        print(f"❌ Erreur après {elapsed:.1f}s")
        print(f"   Code: {e.returncode}")
        return False
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Orchestration complète"""
    
    print("=" * 80)
    print("WORKFLOW COMPLET - DOUBLE SOURCE JBLANKED + EODHD")
    print("=" * 80)
    print()
    print("Étapes:")
    print("   1. Téléchargement JBlanked 2020-2025")
    print("   2. Téléchargement EODHD 2020-2025")
    print("   3. Merge sources → Master")
    print("   4. Import DB (à faire manuellement)")
    print()
    
    input("Appuyez sur ENTRÉE pour démarrer...")
    print()
    
    start_total = time.time()
    
    # ÉTAPE 1 : JBlanked
    success = run_script(
        'download_jblanked_2020_2025.py',
        'ÉTAPE 1/3 : Téléchargement JBlanked 2020-2025'
    )
    
    if not success:
        print("❌ Workflow arrêté - Erreur JBlanked")
        return
    
    # ÉTAPE 2 : EODHD
    success = run_script(
        'download_eodhd_2020_2025.py',
        'ÉTAPE 2/3 : Téléchargement EODHD 2020-2025'
    )
    
    if not success:
        print("❌ Workflow arrêté - Erreur EODHD")
        return
    
    # ÉTAPE 3 : Merge
    success = run_script(
        'merge_sources.py',
        'ÉTAPE 3/3 : Merge sources → Master'
    )
    
    if not success:
        print("❌ Workflow arrêté - Erreur Merge")
        return
    
    # Fin
    elapsed_total = time.time() - start_total
    
    print("=" * 80)
    print("✅ WORKFLOW TERMINÉ")
    print("=" * 80)
    print()
    print(f"⏱️  Durée totale: {elapsed_total/60:.1f} minutes")
    print()
    print("📊 Fichiers créés:")
    print("   • data/jblanked_2020_2025/jblanked_all_2020_2025.json")
    print("   • data/eodhd_2020_2025/eodhd_all_2020_2025.json")
    print("   • data/master/events_master_2020_2025.json")
    print()
    print("🎯 PROCHAINES ÉTAPES:")
    print("   1. Vérifier data/master/events_master_2020_2025.json")
    print("   2. Import DB avec script import_master_to_db.py")
    print("   3. Validation système")
    print()


if __name__ == '__main__':
    main()
