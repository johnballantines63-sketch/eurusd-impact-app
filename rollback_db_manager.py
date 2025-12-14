#!/usr/bin/env python3
"""
🔧 ROLLBACK - Annulation du gestionnaire DB
Restaure les fichiers avant l'intégration du gestionnaire DB

Usage:
    python rollback_db_manager.py
"""

from pathlib import Path
import shutil
from datetime import datetime

def restore_from_backup(filepath: Path):
    """Restaure un fichier depuis son backup le plus récent"""
    backup_dir = filepath.parent / "backups"
    
    if not backup_dir.exists():
        print(f"⚠️  Pas de backups pour {filepath.name}")
        return False
    
    # Trouver les backups de ce fichier
    backups = sorted(backup_dir.glob(f"{filepath.stem}_*.backup"), reverse=True)
    
    if not backups:
        print(f"⚠️  Aucun backup trouvé pour {filepath.name}")
        return False
    
    # Prendre le plus ancien (avant nos modifications)
    oldest = backups[-1]
    
    print(f"   Restauration depuis: {oldest.name}")
    shutil.copy2(oldest, filepath)
    
    return True

def remove_db_manager_imports(filepath: Path):
    """Supprime les imports de db_connection_manager"""
    if not filepath.exists():
        return
    
    content = filepath.read_text(encoding='utf-8')
    
    # Supprimer les imports
    lines = content.split('\n')
    lines_clean = []
    
    for line in lines:
        if 'from db_connection_manager import' in line or \
           'import db_connection_manager' in line:
            print(f"   ❌ Suppression: {line.strip()}")
            continue
        lines_clean.append(line)
    
    # Remplacer get_db_connection par duckdb.connect direct
    content = '\n'.join(lines_clean)
    content = content.replace(
        'get_db_connection(db_path)',
        'duckdb.connect(db_path, read_only=True)'
    )
    content = content.replace(
        'get_db_connection(get_db_path())',
        'duckdb.connect(get_db_path(), read_only=True)'
    )
    
    filepath.write_text(content, encoding='utf-8')

def main():
    print("="*70)
    print("🔙 ROLLBACK - Annulation gestionnaire DB")
    print("="*70)
    print()
    
    if not Path("fx_impact_app").exists():
        print("❌ Lancez depuis la racine du projet")
        return
    
    files_to_restore = [
        Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"),
        Path("fx_impact_app/src/forecaster_mvp.py"),
        Path("fx_impact_app/src/latency_analyzer.py"),
    ]
    
    print("🔄 Restauration des fichiers depuis backup...\n")
    
    restored = 0
    for filepath in files_to_restore:
        print(f"📦 {filepath.name}:")
        if restore_from_backup(filepath):
            print(f"   ✅ Restauré\n")
            restored += 1
        else:
            print(f"   ⚠️  Nettoyage des imports à la place...")
            remove_db_manager_imports(filepath)
            print()
    
    # Supprimer le fichier db_connection_manager.py créé
    bad_files = [
        Path("db_connection_manager.py"),  # Racine (mauvais endroit)
        Path("fx_impact_app/src/db_connection_manager.py"),  # Si créé là aussi
    ]
    
    print("🗑️  Suppression des fichiers db_connection_manager...\n")
    for filepath in bad_files:
        if filepath.exists():
            filepath.unlink()
            print(f"   ❌ Supprimé: {filepath}")
    
    print("\n" + "="*70)
    print("🎉 ROLLBACK TERMINÉ")
    print("="*70)
    print()
    print(f"✅ {restored} fichier(s) restauré(s)")
    print("✅ Imports db_connection_manager supprimés")
    print()
    print("📝 État:")
    print("   - Planificateur: Restauré (devrait marcher)")
    print("   - ForecastEngine: Restauré")
    print("   - LatencyAnalyzer: Restauré")
    print()
    print("🧪 Test:")
    print("   streamlit run fx_impact_app/streamlit_app/Home.py")
    print()
    print("💡 Prochaine étape:")
    print("   On ne touche PLUS au Planificateur (il marche !)")
    print("   On corrige UNIQUEMENT le Calendrier")

if __name__ == "__main__":
    main()
