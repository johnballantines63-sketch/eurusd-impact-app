#!/usr/bin/env python3
"""
Script pour restaurer une version propre du fichier 4_Planificateur depuis un backup
"""

from pathlib import Path
import shutil
from datetime import datetime

def restore_clean_version():
    """Restaure une version propre depuis un backup"""
    
    pages_dir = Path(__file__).parent / "fx_impact_app" / "streamlit_app" / "pages"
    
    current_file = pages_dir / "4_Planificateur-Multi-Evenements.py"
    stable_backup = pages_dir / "4_Planificateur_STABLE_0159_PERFECT.py"
    
    if not stable_backup.exists():
        print(f"❌ Backup stable non trouvé: {stable_backup}")
        return False
    
    # Sauvegarder la version corrompue
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    corrupted_backup = pages_dir / f"4_Planificateur-Multi-Evenements.py.corrupted_{timestamp}"
    
    if current_file.exists():
        shutil.copy2(current_file, corrupted_backup)
        print(f"✅ Version corrompue sauvegardée: {corrupted_backup.name}")
    
    # Restaurer la version stable
    shutil.copy2(stable_backup, current_file)
    print(f"✅ Version stable restaurée depuis: {stable_backup.name}")
    
    return True

if __name__ == "__main__":
    print("="*80)
    print("🔄 RESTAURATION VERSION PROPRE")
    print("="*80)
    print()
    
    success = restore_clean_version()
    
    if success:
        print("\n" + "="*80)
        print("✅ SUCCÈS - Version propre restaurée")
        print("="*80)
        print("\n⚠️ ATTENTION :")
        print("  - Les modifications récentes (presets, corrections TTR) sont perdues")
        print("  - Mais le fichier est maintenant syntaxiquement correct")
        print("\n📋 Prochaines étapes :")
        print("1. pkill -f streamlit")
        print("2. streamlit run fx_impact_app/streamlit_app/Home.py")
        print("3. Tester le pullback sur 11 sept 2025")
        print("\n💡 Note :")
        print("  - Les corrections du pullback (v8.6.6) sont dans sequence_multi_event_timeline_v86.py")
        print("  - Ces corrections sont toujours actives !")
        print("  - Le système de presets peut être réintégré plus tard si nécessaire")
    else:
        print("\n❌ Échec restauration")
