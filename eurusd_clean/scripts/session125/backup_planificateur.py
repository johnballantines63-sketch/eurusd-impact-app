#!/usr/bin/env python3
"""
SESSION 125 - BACKUP PLANIFICATEUR V2.4
========================================
Sauvegarde version actuelle avant intégration fonction amplification(R²)
"""
import shutil
from pathlib import Path
from datetime import datetime

print("="*80)
print("SESSION 125 - BACKUP PLANIFICATEUR V2.4")
print("="*80)
print()

# Chemins CORRIGÉS
PROJECT_ROOT = Path(__file__).parents[2]
PLANIFICATEUR = PROJECT_ROOT / "streamlit_app" / "pages" / "2_Planificateur_V2.py"
BACKUP_DIR = Path(__file__).parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print(f"📁 Recherche Planificateur :")
print(f"   {PLANIFICATEUR}")
print()

# Backup Planificateur
if PLANIFICATEUR.exists():
    backup_planif = BACKUP_DIR / f"Planificateur_V2_backup_{timestamp}.py"
    shutil.copy2(PLANIFICATEUR, backup_planif)
    
    file_size = backup_planif.stat().st_size / 1024
    
    print(f"✅ Planificateur sauvegardé :")
    print(f"   {backup_planif.name}")
    print(f"   Taille : {file_size:.1f} KB")
    print()
else:
    print(f"❌ Planificateur introuvable : {PLANIFICATEUR}")
    print()

# Backup formules validées
FORMULAS_FILE = PROJECT_ROOT / "app" / "core" / "formulas_validated.py"

print(f"📁 Recherche Formules validées :")
print(f"   {FORMULAS_FILE}")
print()

if FORMULAS_FILE.exists():
    backup_formulas = BACKUP_DIR / f"formulas_validated_backup_{timestamp}.py"
    shutil.copy2(FORMULAS_FILE, backup_formulas)
    
    file_size = backup_formulas.stat().st_size / 1024
    
    print(f"✅ Formules validées sauvegardées :")
    print(f"   {backup_formulas.name}")
    print(f"   Taille : {file_size:.1f} KB")
    print()
else:
    print(f"⚠️  Formules introuvables : {FORMULAS_FILE}")
    print()

# Lister backups existants
backups = sorted(BACKUP_DIR.glob("*.py"))
print("="*80)
print(f"BACKUPS DISPONIBLES ({len(backups)})")
print("="*80)
print()

if backups:
    for backup in backups:
        size_kb = backup.stat().st_size / 1024
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"   📄 {backup.name}")
        print(f"      Taille : {size_kb:.1f} KB")
        print(f"      Date   : {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
else:
    print("   (aucun backup)")
    print()

print("="*80)
print("BACKUP TERMINÉ ✅")
print("="*80)
print()
print("🎯 Prêt pour intégration fonction amplification(R²)")
