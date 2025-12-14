#!/usr/bin/env python3
"""
Script de Correction Automatique - EUR/USD News Impact Calculator
Corrige automatiquement les bugs avec backup et validation

USAGE: python3 2_correction_automatique.py

SÉCURITÉ:
- Backup automatique avant modification
- Validation syntaxe Python
- Rollback automatique si erreur
"""

import sys
import re
import ast
import shutil
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator MPC")
PLANIFICATEUR = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
BACKUP_DIR = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/Backups"

# ═══════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_section(title):
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_backup(file_path, suffix="auto"):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{suffix}_{timestamp}.py"
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(file_path, backup_path)
    return backup_path

def validate_python_syntax(content):
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Ligne {e.lineno}: {e.msg}"

# ═══════════════════════════════════════════════════════════════
# CORRECTIONS
# ═══════════════════════════════════════════════════════════════

def fix_impact_calculation(content):
    """Corrige le bug Impact = 0.0 pips"""
    
    changes = []
    
    # Pattern : impact = mfe * (surprise / 10)
    pattern = re.compile(
        r'(\s+)(impact\s*=\s*(?:mfe_p80|base_impact|adjusted_impact)\s*\*\s*\((?:abs\()?surprise(?:\))?\s*/\s*10(?:\.0)?\))',
        re.MULTILINE
    )
    
    def replace(match):
        indent = match.group(1)
        changes.append("Formule impact corrigée")
        return f'''{indent}# ✅ CORRIGÉ : Conversion surprise en pourcentage
{indent}surprise_pct = abs(surprise) * 100
{indent}impact_factor = min(2.0, 1.0 + (surprise_pct / 50.0)) if surprise_pct > 5 else 1.0
{indent}impact = mfe_p80 * impact_factor'''
    
    new_content = pattern.sub(replace, content)
    
    # Assurer surprise_pct = abs(surprise) * 100
    pattern2 = re.compile(
        r'(\s+)(surprise_pct\s*=\s*abs\(surprise\))\s*(?!\*\s*100)',
        re.MULTILINE
    )
    
    def replace2(match):
        indent = match.group(1)
        changes.append("Conversion surprise_pct ajoutée")
        return f'{indent}surprise_pct = abs(surprise) * 100'
    
    new_content = pattern2.sub(replace2, new_content)
    
    return new_content, changes

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print_header("🔧 CORRECTION AUTOMATIQUE - EUR/USD News Impact Calculator")
    print(f"\n  Exécuté le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n  ⚠️  Ce script va modifier le fichier Planificateur")
    print("     Un backup automatique sera créé")
    
    response = input("\n  Continuer ? (o/n) : ").strip().lower()
    if response != 'o':
        print("\n  ❌ Annulé")
        sys.exit(1)
    
    # Vérifier fichier
    print_section("📂 VÉRIFICATION")
    
    if not PLANIFICATEUR.exists():
        print(f"  ❌ Fichier introuvable : {PLANIFICATEUR}")
        sys.exit(1)
    
    print(f"  ✅ Fichier trouvé")
    
    # Lire contenu
    try:
        original_content = read_file(PLANIFICATEUR)
        print(f"  ✅ {len(original_content):,} caractères lus")
    except Exception as e:
        print(f"  ❌ Erreur lecture : {e}")
        sys.exit(1)
    
    # Valider syntaxe originale
    is_valid, error = validate_python_syntax(original_content)
    if not is_valid:
        print(f"  ⚠️  Syntaxe invalide : {error}")
    else:
        print("  ✅ Syntaxe valide")
    
    # Backup
    print_section("📦 BACKUP")
    
    try:
        backup_path = create_backup(PLANIFICATEUR, "before_fix")
        print(f"  ✅ Backup : {backup_path.name}")
    except Exception as e:
        print(f"  ❌ Erreur backup : {e}")
        sys.exit(1)
    
    # Corrections
    print_section("🔧 CORRECTIONS")
    
    new_content, changes = fix_impact_calculation(original_content)
    
    if not changes:
        print("  ✅ Aucune correction nécessaire")
        sys.exit(0)
    
    print(f"  📊 {len(changes)} correction(s) :")
    for change in changes:
        print(f"     • {change}")
    
    # Valider nouvelle syntaxe
    is_valid, error = validate_python_syntax(new_content)
    
    if not is_valid:
        print(f"\n  ❌ ERREUR SYNTAXE : {error}")
        print("  🔄 Rollback automatique")
        sys.exit(1)
    
    print(f"\n  ✅ Syntaxe valide après corrections")
    
    # Confirmation
    response = input("\n  Appliquer les modifications ? (o/n) : ").strip().lower()
    if response != 'o':
        print("\n  ❌ Annulé")
        sys.exit(1)
    
    # Sauvegarde
    print_section("💾 SAUVEGARDE")
    
    try:
        write_file(PLANIFICATEUR, new_content)
        print("  ✅ Fichier modifié")
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        shutil.copy2(backup_path, PLANIFICATEUR)
        print("  🔄 Backup restauré")
        sys.exit(1)
    
    print_header("✅ SUCCÈS")
    print("\n  🎉 Corrections appliquées !")
    print("\n  📝 Prochaines étapes :")
    print("     1. python3 3_validation_corrections.py")
    print("     2. streamlit run fx_impact_app/streamlit_app/Home.py")
    print(f"\n  📦 Backup : {backup_path}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
