#!/usr/bin/env python3
"""
BACKUP AUTOMATIQUE - SESSION 79
================================

Crée backups systématiques avant modifications timezone fix.

Date : 25 octobre 2025
Session : 79
"""

import shutil
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent

# Timestamp pour backups
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Fichiers à sauvegarder
files_to_backup = [
    '2_optimize_window_session78_CORRECTED.py',
    '3_validation_finale_session78_CORRECTED.py'
]

print("\n" + "="*70)
print("BACKUP AUTOMATIQUE - SESSION 79")
print("="*70 + "\n")

for filename in files_to_backup:
    source = SCRIPT_DIR / filename
    
    if not source.exists():
        print(f"⚠️  Fichier introuvable : {filename}")
        continue
    
    # Nom backup
    backup_name = f"{filename}.backup_session79_timezone_fix_{timestamp}"
    backup_path = SCRIPT_DIR / backup_name
    
    # Copier
    shutil.copy2(source, backup_path)
    
    # Vérifier
    if backup_path.exists():
        size_kb = backup_path.stat().st_size / 1024
        print(f"✅ Backup créé : {backup_name}")
        print(f"   Taille : {size_kb:.1f} KB")
    else:
        print(f"❌ ERREUR backup : {filename}")

print("\n" + "="*70)
print("✅ BACKUPS TERMINÉS")
print("="*70 + "\n")
