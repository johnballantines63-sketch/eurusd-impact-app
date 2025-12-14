"""
Workflow optimisé - Double source avec EODHD mensuel

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Maximisation complétude
"""

import subprocess
import sys
from pathlib import Path
import time
import shutil

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


def copy_monthly_to_main():
    """Copier données mensuelles vers dossier principal"""
    
    print("=" * 80)
    print("🔄 COPIE DONNÉES MENSUELLES")
    print("=" * 80)
    print()
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    monthly_dir = data_dir / 'eodhd_2020_2025_monthly'
    main_dir = data_dir / 'eodhd_2020_2025'
    
    monthly_file = monthly_dir / 'eodhd_all_2020_2025_monthly.json'
    main_file = main_dir / 'eodhd_all_2020_2025.json'
    
    if not monthly_file.exists():
        print(f"❌ Fichier mensuel non trouvé: {monthly_file}")
        return False
    
    # Backup ancien fichier
    if main_file.exists():
        backup_file = main_dir / 'eodhd_all_2020_2025_backup.json'
        shutil.copy2(main_file, backup_file)
        print(f"💾 Backup créé: {backup_file.name}")
    
    # Copier nouveau fichier
    shutil.copy2(monthly_file, main_file)
    print(f"✅ Copié: {monthly_file.name} → {main_file.name}")
    print()
    
    return True


def main():
    """Workflow complet optimisé"""
    
    print("=" * 80)
    print("WORKFLOW OPTIMISÉ - DOUBLE SOURCE + EODHD MENSUEL")
    print("=" * 80)
    print()
    print("Étapes:")
    print("   1. Téléchargement JBlanked 2020-2025 (si pas déjà fait)")
    print("   2. Téléchargement EODHD mensuel 2020-2025 (12-15 min)")
    print("   3. Copie données mensuelles")
    print("   4. Merge sources → Master")
    print("   5. Import DB")
    print()
    print("⏱️  Durée totale estimée: 15-20 minutes")
    print()
    
    input("Appuyez sur ENTRÉE pour démarrer...")
    print()
    
    start_total = time.time()
    
    # Vérifier si JBlanked déjà téléchargé
    data_dir = Path(__file__).parent.parent.parent / 'data'
    jblanked_file = data_dir / 'jblanked_2020_2025' / 'jblanked_all_2020_2025.json'
    
    if jblanked_file.exists():
        print("✅ JBlanked déjà téléchargé (étape 1 ignorée)")
        print()
    else:
        # ÉTAPE 1 : JBlanked
        success = run_script(
            'download_jblanked_2020_2025.py',
            'ÉTAPE 1/5 : Téléchargement JBlanked 2020-2025'
        )
        
        if not success:
            print("❌ Workflow arrêté - Erreur JBlanked")
            return
    
    # ÉTAPE 2 : EODHD Mensuel
    success = run_script(
        'download_eodhd_monthly.py',
        'ÉTAPE 2/5 : Téléchargement EODHD mensuel 2020-2025'
    )
    
    if not success:
        print("❌ Workflow arrêté - Erreur EODHD mensuel")
        return
    
    # ÉTAPE 3 : Copie
    print("=" * 80)
    print("▶️  ÉTAPE 3/5 : Copie données mensuelles")
    print("=" * 80)
    print()
    
    success = copy_monthly_to_main()
    
    if not success:
        print("❌ Workflow arrêté - Erreur copie")
        return
    
    # ÉTAPE 4 : Merge
    success = run_script(
        'merge_sources.py',
        'ÉTAPE 4/5 : Merge sources → Master'
    )
    
    if not success:
        print("❌ Workflow arrêté - Erreur Merge")
        return
    
    # ÉTAPE 5 : Import DB
    success = run_script(
        'import_master_to_db.py',
        'ÉTAPE 5/5 : Import DB'
    )
    
    if not success:
        print("❌ Workflow arrêté - Erreur Import DB")
        return
    
    # Fin
    elapsed_total = time.time() - start_total
    
    print("=" * 80)
    print("✅ WORKFLOW COMPLET TERMINÉ")
    print("=" * 80)
    print()
    print(f"⏱️  Durée totale: {elapsed_total/60:.1f} minutes")
    print()
    print("📊 Résultats:")
    print("   • JBlanked: ~17,700 événements")
    print("   • EODHD mensuel: ~15,000-20,000 événements (estimation)")
    print("   • Master: ~32,000-37,000 événements (estimation)")
    print("   • DB warehouse.duckdb: IMPORTÉ ✅")
    print()
    print("🎉 SYSTÈME PRÊT !")
    print()


if __name__ == '__main__':
    main()
