#!/usr/bin/env python3
"""
BACKUP DATABASE - Avant migration timezone
==========================================

Crée une copie de sécurité de warehouse.duckdb avant toute modification.

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 1
"""

from pathlib import Path
import shutil
from datetime import datetime

print("="*80)
print("💾 BACKUP DATABASE")
print("="*80)

# Chemins
db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")
backup_dir = db_path.parent / "backups"

# Créer dossier backups
backup_dir.mkdir(exist_ok=True)

# Nom backup avec timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_name = f"warehouse_backup_{timestamp}_before_timezone_fix.duckdb"
backup_path = backup_dir / backup_name

print(f"\n📁 Source: {db_path}")
print(f"📁 Destination: {backup_path}")

if not db_path.exists():
    print(f"\n❌ ERREUR: Base de données introuvable !")
    print(f"   Chemin: {db_path}")
    exit(1)

# Taille DB
db_size_mb = db_path.stat().st_size / (1024 * 1024)
print(f"\n📊 Taille DB: {db_size_mb:.2f} MB")

# Copier
print(f"\n🔄 Copie en cours...")
try:
    shutil.copy2(db_path, backup_path)
    
    # Vérifier
    if backup_path.exists():
        backup_size_mb = backup_path.stat().st_size / (1024 * 1024)
        
        if backup_size_mb == db_size_mb:
            print(f"✅ BACKUP RÉUSSI !")
            print(f"   Taille backup: {backup_size_mb:.2f} MB")
            print(f"   Emplacement: {backup_path}")
            
            print(f"\n💡 Pour restaurer en cas de problème:")
            print(f"   cp '{backup_path}' '{db_path}'")
        else:
            print(f"⚠️ ATTENTION: Tailles différentes !")
            print(f"   Original: {db_size_mb:.2f} MB")
            print(f"   Backup: {backup_size_mb:.2f} MB")
    else:
        print(f"❌ ÉCHEC: Backup non créé")
        
except Exception as e:
    print(f"❌ ERREUR: {e}")
    exit(1)

print("\n" + "="*80)
print("✅ BACKUP TERMINÉ - Prêt pour migration timezone")
print("="*80)
