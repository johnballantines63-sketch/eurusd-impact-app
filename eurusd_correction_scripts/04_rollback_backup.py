#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROLLBACK BACKUP - EUR/USD Trading App
Restaure un fichier depuis un backup
"""

import os
import sys
import shutil
import glob
from datetime import datetime

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def lister_backups():
    """Liste tous les backups disponibles"""
    pattern = "fx_impact_app/*_backup_*.py"
    backups = glob.glob(pattern)
    
    if not backups:
        return []
    
    # Trier par date (plus récent en premier)
    backups_info = []
    for backup in backups:
        try:
            # Extraire timestamp du nom
            parts = os.path.basename(backup).split('_backup_')
            if len(parts) == 2:
                timestamp_str = parts[1].replace('.py', '')
                # Format: YYYYMMDD_HHMMSS
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                # Fichier original
                fichier_original = parts[0] + '.py'
                
                taille = os.path.getsize(backup)
                
                backups_info.append({
                    'path': backup,
                    'timestamp': timestamp,
                    'fichier_original': fichier_original,
                    'taille': taille
                })
        except:
            continue
    
    # Trier par date décroissante
    backups_info.sort(key=lambda x: x['timestamp'], reverse=True)
    return backups_info

def restaurer_backup(backup_path, fichier_cible):
    """Restaure un backup"""
    try:
        # Créer un backup du fichier actuel avant restauration
        if os.path.exists(fichier_cible):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup = f"{os.path.splitext(fichier_cible)[0]}_safety_{timestamp}.py"
            shutil.copy2(fichier_cible, safety_backup)
            print_info(f"Safety backup créé: {os.path.basename(safety_backup)}")
        
        # Restaurer
        shutil.copy2(backup_path, fichier_cible)
        return True, f"Fichier restauré: {os.path.basename(fichier_cible)}"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def main():
    print_header("🔄 ROLLBACK BACKUP - EUR/USD TRADING APP")
    
    # Lister backups
    print_info("Recherche de backups...")
    backups = lister_backups()
    
    if not backups:
        print_error("Aucun backup trouvé")
        print_info("Les backups sont créés automatiquement par le script de correction")
        return 1
    
    print_success(f"{len(backups)} backup(s) trouvé(s)\n")
    
    # Afficher la liste
    print_header("📋 BACKUPS DISPONIBLES")
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {os.path.basename(backup['path'])}")
        print(f"   📅 Date: {backup['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📄 Original: {backup['fichier_original']}")
        print(f"   💾 Taille: {backup['taille']:,} bytes\n")
    
    # Sélection
    try:
        choix = input(f"Sélectionnez un backup (1-{len(backups)}) ou 'q' pour quitter: ").strip()
        
        if choix.lower() == 'q':
            print_info("Annulé")
            return 0
        
        index = int(choix) - 1
        if index < 0 or index >= len(backups):
            print_error("Sélection invalide")
            return 1
        
        backup_selectionne = backups[index]
        
        # Confirmation
        print_header("⚠️  CONFIRMATION")
        print(f"Backup: {os.path.basename(backup_selectionne['path'])}")
        print(f"Date: {backup_selectionne['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Restaurer vers: {backup_selectionne['fichier_original']}")
        
        confirmation = input("\nConfirmer la restauration ? (o/n): ").strip().lower()
        if confirmation != 'o':
            print_info("Restauration annulée")
            return 0
        
        # Restaurer
        fichier_cible = f"fx_impact_app/{backup_selectionne['fichier_original']}"
        success, message = restaurer_backup(backup_selectionne['path'], fichier_cible)
        
        if success:
            print_success(message)
            print("\n💡 Le fichier a été restauré avec succès")
            print("   Un safety backup du fichier actuel a été créé")
            return 0
        else:
            print_error(message)
            return 1
            
    except ValueError:
        print_error("Entrée invalide")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Annulé")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        sys.exit(1)
