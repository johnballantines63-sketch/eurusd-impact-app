#!/usr/bin/env python3
"""
URGENCE : Restauration du backup
=================================

On a perdu 95% des données (33,277 → 1,750)
Restaurons le backup immédiatement !
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
import duckdb

PROJECT_ROOT = Path(__file__).parent
DB_PATH = PROJECT_ROOT / "fx_impact_app" / "data" / "warehouse.duckdb"
BACKUP_DIR = PROJECT_ROOT / "backups_session19"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

print(f"\n{Colors.RED}{Colors.BOLD}{'='*80}{Colors.END}")
print(f"{Colors.RED}{Colors.BOLD}RESTAURATION D'URGENCE DU BACKUP{Colors.END}")
print(f"{Colors.RED}{Colors.BOLD}{'='*80}{Colors.END}")

# Trouver le dernier backup
backups = sorted(BACKUP_DIR.glob("warehouse_*.duckdb"), key=lambda p: p.stat().st_mtime, reverse=True)

if not backups:
    print(f"{Colors.RED}❌ Aucun backup trouvé !{Colors.END}")
    sys.exit(1)

# Afficher les backups disponibles
print(f"\n{Colors.YELLOW}Backups disponibles :{Colors.END}")
for i, backup in enumerate(backups[:5], 1):
    size_mb = backup.stat().st_size / 1024 / 1024
    mtime = datetime.fromtimestamp(backup.stat().st_mtime)
    print(f"   {i}. {backup.name} ({size_mb:.1f} MB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

# Sélectionner le dernier backup FULL_IMPORT (avant le nettoyage)
full_import_backup = None
for backup in backups:
    if "FULL_IMPORT" in backup.name:
        full_import_backup = backup
        break

if not full_import_backup:
    print(f"\n{Colors.YELLOW}⚠️  Backup FULL_IMPORT introuvable, utilisation du plus récent{Colors.END}")
    full_import_backup = backups[0]

print(f"\n{Colors.BOLD}Backup sélectionné :{Colors.END}")
print(f"   {full_import_backup.name}")

# Vérifier le backup
print(f"\n{Colors.BOLD}Vérification du backup...{Colors.END}")
try:
    conn = duckdb.connect(str(full_import_backup))
    count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    conn.close()
    print(f"   ✅ Backup valide : {count:,} événements")
except Exception as e:
    print(f"   {Colors.RED}❌ Erreur : {e}{Colors.END}")
    sys.exit(1)

# Confirmation
print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  ATTENTION ⚠️{Colors.END}")
print(f"La DB actuelle (1,750 événements) sera ÉCRASÉE")
print(f"par le backup ({count:,} événements)")

response = input(f"\n{Colors.BOLD}Continuer ? (oui/non) : {Colors.END}")
if response.lower() not in ['oui', 'o', 'yes', 'y']:
    print("Restauration annulée.")
    sys.exit(0)

# Sauvegarder la DB actuelle (au cas où)
print(f"\n{Colors.BOLD}Sauvegarde DB actuelle...{Colors.END}")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
current_backup = BACKUP_DIR / f"warehouse_current_{timestamp}.duckdb"
shutil.copy2(DB_PATH, current_backup)
print(f"   ✅ Sauvegardée : {current_backup.name}")

# Restauration
print(f"\n{Colors.BOLD}Restauration du backup...{Colors.END}")
try:
    shutil.copy2(full_import_backup, DB_PATH)
    print(f"   ✅ DB restaurée")
except Exception as e:
    print(f"   {Colors.RED}❌ Erreur : {e}{Colors.END}")
    sys.exit(1)

# Vérification
print(f"\n{Colors.BOLD}Vérification...{Colors.END}")
conn = duckdb.connect(str(DB_PATH))
restored_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
conn.close()

print(f"   Total événements : {restored_count:,}")

if restored_count > 30000:
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ RESTAURATION RÉUSSIE !{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}")
else:
    print(f"\n{Colors.RED}⚠️  Nombre d'événements anormalement bas{Colors.END}")

print(f"\n{Colors.YELLOW}Note :{Colors.END} Le code modifié (avec les 5 nouveaux champs) est toujours en place.")
print("Mais le schéma DB a les anciennes colonnes (sans comparison, period, etc.)")
print("\nIl faut maintenant :")
print("1. Corriger le script d'import pour gérer tous les événements")
print("2. Re-faire l'import proprement")
