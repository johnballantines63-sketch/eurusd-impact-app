#!/usr/bin/env python3
"""
Script interactif de fusion v8.3
Vous guide étape par étape pour fusionner les 2 parties

Usage:
    python3 merge_interactive.py
"""

import sys
from pathlib import Path
from datetime import datetime

def print_header():
    print("\n" + "=" * 70)
    print("🔧 ASSISTANT DE FUSION PLANIFICATEUR v8.3")
    print("=" * 70)
    print()

def print_step(num, title):
    print(f"\n{'─' * 70}")
    print(f"📌 ÉTAPE {num}: {title}")
    print('─' * 70)

def wait_for_user():
    input("\n👉 Appuyez sur ENTRÉE pour continuer...")

def main():
    print_header()
    
    # Configuration
    PROJECT_ROOT = Path("/Users/andrevalentin/Projects/eurusd_news_impact_calculator")
    TARGET_DIR = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages"
    TARGET_FILE = TARGET_DIR / "4_Planificateur-Multi-Evenements.py"
    
    print(f"📁 Dossier projet: {PROJECT_ROOT}")
    print(f"📄 Fichier cible: {TARGET_FILE.name}")
    
    # Vérifier que le projet existe
    if not PROJECT_ROOT.exists():
        print(f"\n❌ ERREUR: Dossier projet introuvable!")
        print(f"💡 Le script cherche: {PROJECT_ROOT}")
        print(f"💡 Modifiez PROJECT_ROOT si votre projet est ailleurs")
        sys.exit(1)
    
    print("✅ Dossier projet trouvé")
    
    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 1 : Backup
    # ═══════════════════════════════════════════════════════════
    
    print_step(1, "BACKUP DU FICHIER ACTUEL")
    
    if TARGET_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = TARGET_DIR / f"4_Planificateur-Multi-Evenements.bak_{timestamp}.py"
        
        print(f"\n📦 Fichier existant détecté")
        print(f"💾 Création backup: {backup_file.name}")
        
        try:
            with open(TARGET_FILE, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            original_lines = len(original_content.split('\n'))
            print(f"✅ Backup créé: {original_lines} lignes sauvegardées")
            
        except Exception as e:
            print(f"❌ Erreur backup: {e}")
            response = input("\n⚠️ Continuer sans backup ? (oui/non): ")
            if response.lower() != 'oui':
                print("❌ Fusion annulée")
                sys.exit(1)
    else:
        print("ℹ️ Aucun fichier existant (création nouveau fichier)")
    
    wait_for_user()
    
    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 2 : Créer fichier temporaire
    # ═══════════════════════════════════════════════════════════
    
    print_step(2, "PRÉPARATION DU FICHIER TEMPORAIRE")
    
    temp_file = TARGET_DIR / "temp_planificateur_v8.3.py"
    
    print(f"\n📝 Création fichier temporaire: {temp_file.name}")
    print("💡 Vous allez copier les 2 parties ici")
    
    # Créer fichier temporaire vide
    temp_file.write_text("", encoding='utf-8')
    print("✅ Fichier temporaire créé")
    
    wait_for_user()
    
    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 3 : Ouvrir éditeur
    # ═══════════════════════════════════════════════════════════
    
    print_step(3, "OUVRIR ÉDITEUR")
    
    print("\n📝 Ouverture dans Visual Studio Code...")
    
    import subprocess
    try:
        subprocess.run(['open', '-a', 'Visual Studio Code', str(temp_file)])
        print("✅ Éditeur ouvert")
    except Exception as e:
        print(f"⚠️ Impossible d'ouvrir automatiquement: {e}")
        print(f"💡 Ouvrez manuellement: {temp_file}")
    
    print()
    print("📋 INSTRUCTIONS COPIER-COLLER:")
    print()
    print("1️⃣ Dans Claude, trouver l'artifact 'planificateur_v83_part1'")
    print("   → Sélectionner TOUT le code (Ctrl+A)")
    print("   → Copier (Ctrl+C)")
    print("   → Coller dans le fichier temporaire (Ctrl+V)")
    print()
    print("2️⃣ Dans Claude, trouver l'artifact 'planificateur_v83_part2'")
    print("   → Sélectionner TOUT le code (Ctrl+A)")
    print("   → Copier (Ctrl+C)")
    print("   → Coller À LA SUITE (position curseur après PARTIE 1)")
    print()
    print("3️⃣ Sauvegarder le fichier (Cmd+S)")
    print()
    
    response = input("✅ Avez-vous copié les 2 parties et sauvegardé ? (oui/non): ")
    
    if response.lower() != 'oui':
        print("\n⚠️ Fusion annulée - Fichier temporaire conservé")
        print(f"💡 Fichier: {temp_file}")
        sys.exit(0)
    
    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 4 : Vérification
    # ═══════════════════════════════════════════════════════════
    
    print_step(4, "VÉRIFICATION DU CONTENU")
    
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            merged_content = f.read()
        
        lines = merged_content.split('\n')
        n_lines = len(lines)
        n_chars = len(merged_content)
        
        print(f"\n📊 Statistiques du fichier:")
        print(f"   Lignes: {n_lines}")
        print(f"   Caractères: {n_chars:,}")
        print()
        
        # Vérifications de base
        checks_passed = True
        
        # Check 1: Taille minimale (CORRIGÉ: 1346 lignes attendues)
        if n_lines < 1300:
            print(f"⚠️ Attention: Seulement {n_lines} lignes (attendu ~1346)")
            checks_passed = False
        elif n_lines > 1400:
            print(f"⚠️ Attention: Trop de lignes {n_lines} (attendu ~1346)")
            checks_passed = False
        else:
            print(f"✅ Taille correcte: {n_lines} lignes (attendu ~1346)")
        
        # Check 2: Imports séquençage
        if 'sequence_multi_event_timeline' in merged_content:
            print("✅ Imports séquençage détectés")
        else:
            print("⚠️ Attention: Imports séquençage manquants")
            checks_passed = False
        
        # Check 3: Toggle UI
        if 'use_sequential' in merged_content:
            print("✅ Toggle séquentiel détecté")
        else:
            print("⚠️ Attention: Toggle séquentiel manquant")
            checks_passed = False
        
        # Check 4: Mode classique préservé
        if 'vectorial_impact' in merged_content:
            print("✅ Mode classique préservé")
        else:
            print("⚠️ Attention: Mode classique manquant")
            checks_passed = False
        
        print()
        
        if not checks_passed:
            print("⚠️" + "=" * 68)
            print("⚠️ ATTENTION: Certaines vérifications ont échoué")
            print("⚠️" + "=" * 68)
            response = input("\n❓ Continuer quand même ? (oui/non): ")
            if response.lower() != 'oui':
                print("❌ Fusion annulée")
                sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erreur lecture fichier: {e}")
        sys.exit(1)
    
    wait_for_user()
    
    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 5 : Remplacement final
    # ═══════════════════════════════════════════════════════════
    
    print_step(5, "REMPLACEMENT DU FICHIER FINAL")
    
    print(f"\n🔄 Remplacement:")
    print(f"   Source: {temp_file.name}")
    print(f"   Cible: {TARGET_FILE.name}")
    
    response = input("\n⚠️ CONFIRMER le remplacement ? (oui/non): ")
    
    if response.lower() != 'oui':
        print("\n❌ Fusion annulée")
        print(f"💡 Fichier temporaire conservé: {temp_file}")
        sys.exit(0)
    
    try:
        # Copier temp → final
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(TARGET_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fichier remplacé avec succès!")
        
        # Supprimer temp
        temp_file.unlink()
        print("✅ Fichier temporaire supprimé")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)
    
    # ═══════════════════════════════════════════════════════════
    # SUCCÈS
    # ═══════════════════════════════════════════════════════════
    
    print("\n" + "=" * 70)
    print("✨ FUSION RÉUSSIE !")
    print("=" * 70)
    print()
    print(f"📄 Fichier final: {TARGET_FILE}")
    print(f"📏 Taille: {n_lines} lignes, {n_chars:,} caractères")
    
    if 'backup_file' in locals():
        print(f"💾 Backup: {backup_file}")
    
    print()
    print("🧪 PROCHAINES ÉTAPES:")
    print()
    print("1️⃣ Créer les modules séquençage:")
    print("   • fx_impact_app/src/sequence_multi_event_timeline.py")
    print("   • fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py")
    print()
    print("2️⃣ Tester l'application:")
    print("   streamlit run fx_impact_app/streamlit_app/Home.py")
    print()
    print("3️⃣ Vérifier le toggle séquentiel:")
    print("   • Charger 11/09/2025")
    print("   • Cocher événements")
    print("   • Activer toggle séquentiel")
    print()
    
    if 'backup_file' in locals():
        print("⚠️ Si erreur, restaurer backup:")
        print(f"   cp {backup_file} {TARGET_FILE}")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Fusion annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
