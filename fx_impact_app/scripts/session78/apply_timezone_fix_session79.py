#!/usr/bin/env python3
"""
TIMEZONE FIX DÉFINITIF - SESSION 79
===================================

Applique la solution timezone définitive aux scripts Session 78.

ÉTAPES :
1. Backup automatique avec timestamp
2. Mise à jour imports
3. Remplacement logique timezone
4. Vérification

Date : 25 octobre 2025
Session : 79
"""

import shutil
from pathlib import Path
from datetime import datetime
import re

SCRIPT_DIR = Path(__file__).parent
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

print("\n" + "="*70)
print("TIMEZONE FIX DÉFINITIF - SESSION 79")
print("="*70 + "\n")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : BACKUPS
# ════════════════════════════════════════════════════════════════

print("🔒 ÉTAPE 1 : Création backups")
print("-"*70)

files_to_fix = [
    '2_optimize_window_session78_CORRECTED.py',
    '3_validation_finale_session78_CORRECTED.py'
]

backups_created = []

for filename in files_to_fix:
    source = SCRIPT_DIR / filename
    
    if not source.exists():
        print(f"❌ Fichier introuvable : {filename}")
        continue
    
    backup_name = f"{filename}.backup_session79_timezone_fix_{timestamp}"
    backup_path = SCRIPT_DIR / backup_name
    
    shutil.copy2(source, backup_path)
    
    if backup_path.exists():
        size_kb = backup_path.stat().st_size / 1024
        print(f"✅ Backup : {backup_name} ({size_kb:.1f} KB)")
        backups_created.append((filename, backup_path))
    else:
        print(f"❌ ERREUR backup : {filename}")
        exit(1)

print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : MISE À JOUR SCRIPTS
# ════════════════════════════════════════════════════════════════

print("🔧 ÉTAPE 2 : Application timezone fix")
print("-"*70)

for filename, backup_path in backups_created:
    print(f"\n📝 Modification : {filename}")
    
    source_path = SCRIPT_DIR / filename
    
    # Lire contenu
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_lines = len(content.split('\n'))
    
    # ════════════════════════════════════════════════════════════
    # MODIFICATION 1 : Ajouter import timezone_utils
    # ════════════════════════════════════════════════════════════
    
    if 'from src.utils.timezone_utils import' not in content:
        # Trouver ligne après "from src.formulas_validated import"
        import_pattern = r'(from src\.formulas_validated import[^\n]+\n)'
        new_import = r'\1from src.utils.timezone_utils import get_event_window_utc\n'
        content = re.sub(import_pattern, new_import, content)
        print("   ✅ Import timezone_utils ajouté")
    else:
        print("   ℹ️  Import timezone_utils déjà présent")
    
    # ════════════════════════════════════════════════════════════
    # MODIFICATION 2 : Remplacer logique timezone
    # ════════════════════════════════════════════════════════════
    
    # Pattern à remplacer (ancienne méthode)
    old_pattern = r'''# Parser datetime avec timezone Berne
        dt_dataset = dateutil\.parser\.parse\(row\['datetime'\]\)
        tz_berne = pytz\.timezone\('Europe/Zurich'\)
        dt_berne = dt_dataset\.astimezone\(tz_berne\)
        
        # Fenêtre temporelle
        start_time = dt_berne - timedelta\(minutes=window\)
        end_time = dt_berne \+ timedelta\(minutes=window\)'''
    
    # Nouvelle méthode (simple et correcte)
    new_pattern = '''# Utiliser timezone_utils pour conversion correcte
        start_time, end_time = get_event_window_utc(row['datetime'], window)'''
    
    if re.search(old_pattern.replace('\n', ''), content.replace('\n', '')):
        content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)
        print("   ✅ Logique timezone remplacée")
    else:
        # Essayer pattern alternatif (dans boucle for)
        old_pattern2 = r'''dt_dataset = dateutil\.parser\.parse\(row\['datetime'\]\)
        tz_berne = pytz\.timezone\('Europe/Zurich'\)
        dt_berne = dt_dataset\.astimezone\(tz_berne\)
        
        # Fenêtre temporelle
        start_time = dt_berne - timedelta\(minutes=window\)
        end_time = dt_berne \+ timedelta\(minutes=window\)'''
        
        new_pattern2 = '''# Utiliser timezone_utils pour conversion correcte
        start_time, end_time = get_event_window_utc(row['datetime'], window)'''
        
        if re.search(old_pattern2.replace('\n', ''), content.replace('\n', '')):
            content = re.sub(old_pattern2, new_pattern2, content, flags=re.MULTILINE)
            print("   ✅ Logique timezone remplacée (pattern 2)")
        else:
            print("   ⚠️  Pattern timezone non trouvé (peut-être déjà modifié)")
    
    # ════════════════════════════════════════════════════════════
    # MODIFICATION 3 : Ajuster query SQL (utiliser strings directement)
    # ════════════════════════════════════════════════════════════
    
    # Remplacer .strftime() par usage direct des strings
    old_sql_pattern = r"WHERE e\.ts_utc >= '\{start_time\.strftime\('%Y-%m-%d %H:%M:%S'\)\}'"
    new_sql_pattern = "WHERE e.ts_utc >= '{start_time}'"
    
    if old_sql_pattern in content:
        content = content.replace(
            "WHERE e.ts_utc >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'",
            "WHERE e.ts_utc >= '{start_time}'"
        )
        content = content.replace(
            "AND e.ts_utc <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'",
            "AND e.ts_utc <= '{end_time}'"
        )
        print("   ✅ Query SQL ajustée")
    else:
        print("   ℹ️  Query SQL déjà correcte")
    
    # Écrire fichier modifié
    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    modified_lines = len(content.split('\n'))
    print(f"   📊 Lignes : {original_lines} → {modified_lines}")

print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : VÉRIFICATION
# ════════════════════════════════════════════════════════════════

print("✅ ÉTAPE 3 : Vérification")
print("-"*70)

for filename, _ in backups_created:
    source_path = SCRIPT_DIR / filename
    
    with open(source_path, 'r') as f:
        content = f.read()
    
    checks = [
        ('from src.utils.timezone_utils import', 'Import timezone_utils'),
        ('get_event_window_utc', 'Fonction get_event_window_utc'),
    ]
    
    all_ok = True
    for pattern, description in checks:
        if pattern in content:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} manquant")
            all_ok = False
    
    if not all_ok:
        print(f"\n❌ Vérification échouée pour {filename}")
        print("   Restaurer backup si nécessaire")

print()

# ════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ════════════════════════════════════════════════════════════════

print("="*70)
print("✅ TIMEZONE FIX APPLIQUÉ")
print("="*70)
print()
print("📋 Backups créés :")
for filename, backup_path in backups_created:
    print(f"   {backup_path.name}")
print()
print("📝 Fichiers modifiés :")
for filename, _ in backups_created:
    print(f"   {filename}")
print()
print("🧪 Test recommandé :")
print("   python3 src/utils/timezone_utils.py")
print()
print("🚀 Exécution pipeline :")
print("   ./run_pipeline_corrected.sh")
print()
