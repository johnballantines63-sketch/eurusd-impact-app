#!/usr/bin/env python3
"""
Script de fusion automatique pour créer 4_Planificateur-Multi-Evenements.py v8.3
Fusionne les 2 parties des artifacts en un seul fichier

Usage:
    python3 merge_planificateur_v8.3.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Configurations
PROJECT_ROOT = Path("/Users/andrevalentin/Projects/eurusd_news_impact_calculator")
TARGET_FILE = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
BACKUP_FILE = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.bak"

# Contenu des 2 parties (à copier depuis les artifacts)
PART1_CONTENT = """import sys
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Télécharger la base de données si nécessaire (une seule fois)
try:
    from download_database import download_database
    download_database()
except Exception as e:
    pass  # Déjà téléchargée ou erreur gérée ailleurs


# [COPIER LE RESTE DE LA PARTIE 1 ICI]
# Voir artifact "planificateur_v83_part1"
"""

PART2_CONTENT = """
# [COPIER LA PARTIE 2 ICI]
# Voir artifact "planificateur_v83_part2"
"""


def create_backup():
    """Crée une sauvegarde du fichier actuel"""
    if TARGET_FILE.exists():
        # Ajouter timestamp au backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_with_time = BACKUP_FILE.parent / f"{BACKUP_FILE.stem}_{timestamp}.py"
        
        print(f"📦 Création backup: {backup_with_time.name}")
        
        with open(TARGET_FILE, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        with open(backup_with_time, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        print(f"✅ Backup créé: {len(original_content)} caractères")
        return backup_with_time
    else:
        print("ℹ️ Aucun fichier existant à sauvegarder")
        return None


def merge_and_write():
    """Fusionne les 2 parties et écrit le fichier final"""
    
    print("=" * 70)
    print("🔧 FUSION AUTOMATIQUE v8.3")
    print("=" * 70)
    print()
    
    # Vérifier que le projet existe
    if not PROJECT_ROOT.exists():
        print(f"❌ ERREUR: Dossier projet introuvable: {PROJECT_ROOT}")
        print("💡 Modifiez PROJECT_ROOT dans le script")
        sys.exit(1)
    
    print(f"📁 Projet: {PROJECT_ROOT}")
    print(f"📄 Fichier cible: {TARGET_FILE.name}")
    print()
    
    # Créer backup
    backup_file = create_backup()
    print()
    
    # ATTENTION : Ce script contient des placeholders
    # Vous devez remplacer PART1_CONTENT et PART2_CONTENT
    # par le contenu réel des artifacts
    
    if "COPIER" in PART1_CONTENT or "COPIER" in PART2_CONTENT:
        print("⚠️" + "=" * 68)
        print("⚠️ ATTENTION : Ce script contient des PLACEHOLDERS")
        print("⚠️" + "=" * 68)
        print()
        print("📋 INSTRUCTIONS:")
        print()
        print("1. Ouvrir ce script dans un éditeur")
        print("2. Remplacer PART1_CONTENT par le contenu de l'artifact 'planificateur_v83_part1'")
        print("3. Remplacer PART2_CONTENT par le contenu de l'artifact 'planificateur_v83_part2'")
        print("4. Relancer le script")
        print()
        print("💡 OU utilisez la méthode manuelle (copier-coller direct)")
        print()
        sys.exit(1)
    
    # Fusionner les contenus
    print("🔄 Fusion des parties...")
    full_content = PART1_CONTENT + "\n" + PART2_CONTENT
    
    # Statistiques
    lines = full_content.split('\n')
    n_lines = len(lines)
    n_chars = len(full_content)
    
    print(f"📊 Statistiques du fichier fusionné:")
    print(f"   Lignes: {n_lines}")
    print(f"   Caractères: {n_chars:,}")
    print()
    
    # Écrire le fichier
    print(f"💾 Écriture: {TARGET_FILE}")
    
    # Créer dossiers si nécessaire
    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print("✅ Fichier créé avec succès!")
    print()
    
    # Vérification
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        written_content = f.read()
    
    if len(written_content) == len(full_content):
        print("✅ Vérification: Taille correcte")
    else:
        print("⚠️ Attention: Taille différente après écriture")
    
    print()
    print("=" * 70)
    print("✨ FUSION TERMINÉE")
    print("=" * 70)
    print()
    
    if backup_file:
        print(f"💾 Backup: {backup_file.name}")
    
    print(f"📄 Nouveau fichier: {TARGET_FILE.name}")
    print(f"📏 Taille: {n_lines} lignes, {n_chars:,} caractères")
    print()
    print("🧪 PROCHAINES ÉTAPES:")
    print()
    print("1. Vérifier le fichier:")
    print(f"   open -a 'Visual Studio Code' {TARGET_FILE}")
    print()
    print("2. Tester l'application:")
    print("   streamlit run fx_impact_app/streamlit_app/Home.py")
    print()
    print("3. Si erreur, restaurer backup:")
    if backup_file:
        print(f"   cp {backup_file} {TARGET_FILE}")
    print()


def show_manual_method():
    """Affiche la méthode manuelle si le script ne peut pas être utilisé"""
    print()
    print("=" * 70)
    print("📋 MÉTHODE MANUELLE (Alternative)")
    print("=" * 70)
    print()
    print("Si ce script ne fonctionne pas, utilisez la méthode manuelle:")
    print()
    print("1️⃣ Créer un nouveau fichier vide")
    print("2️⃣ Copier PARTIE 1 (artifact 'planificateur_v83_part1')")
    print("3️⃣ Copier PARTIE 2 (artifact 'planificateur_v83_part2') À LA SUITE")
    print("4️⃣ Sauvegarder comme '4_Planificateur-Multi-Evenements.py'")
    print()


if __name__ == "__main__":
    try:
        merge_and_write()
    except KeyboardInterrupt:
        print("\n\n⚠️ Fusion annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        print()
        show_manual_method()
        sys.exit(1)
