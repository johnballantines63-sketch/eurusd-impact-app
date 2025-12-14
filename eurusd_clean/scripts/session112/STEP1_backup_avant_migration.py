#!/usr/bin/env python3
"""
BACKUP AVANT MIGRATION TIMEZONE
================================

CRITIQUE: Backup obligatoire avant modification DB

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 1
"""

from pathlib import Path
import shutil
from datetime import datetime

print("="*80)
print("💾 BACKUP DATABASE - AVANT MIGRATION TIMEZONE")
print("="*80)

# Chemins
db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")
backup_dir = db_path.parent / "backups"

# Créer dossier backups
backup_dir.mkdir(exist_ok=True)

# Nom backup avec timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_name = f"warehouse_AVANT_MIGRATION_TIMEZONE_{timestamp}.duckdb"
backup_path = backup_dir / backup_name

print(f"\n📁 Source: {db_path}")
print(f"📁 Backup: {backup_path}")

if not db_path.exists():
    print(f"\n❌ ERREUR: Base de données introuvable !")
    exit(1)

# Taille DB
db_size_mb = db_path.stat().st_size / (1024 * 1024)
print(f"\n📊 Taille DB: {db_size_mb:.2f} MB")

# Copier
print(f"\n🔄 Copie en cours...")
shutil.copy2(db_path, backup_path)

# Vérifier
if backup_path.exists():
    backup_size_mb = backup_path.stat().st_size / (1024 * 1024)
    
    if abs(backup_size_mb - db_size_mb) < 0.01:
        print(f"\n✅ BACKUP RÉUSSI !")
        print(f"   Taille: {backup_size_mb:.2f} MB")
        print(f"   Emplacement: {backup_path}")
        
        print(f"\n💡 Pour restaurer en cas de problème:")
        print(f"   cp '{backup_path}' '{db_path}'")
        
        print(f"\n✅ Prêt pour migration !")
    else:
        print(f"⚠️ ATTENTION: Tailles différentes !")
        exit(1)
else:
    print(f"❌ ÉCHEC backup")
    exit(1)
