#!/usr/bin/env python3
"""
Script pour appliquer le patch v8.6.4 à sequence_multi_event_timeline_v86.py
Suppression complète de l'atténuation
"""

import re
from pathlib import Path

def apply_v864_patch():
    """Applique les modifications v8.6.4"""
    
    file_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src/sequence_multi_event_timeline_v86.py")
    
    if not file_path.exists():
        print(f"❌ Fichier introuvable : {file_path}")
        return False
    
    # Lire le fichier
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    print("📄 Fichier lu avec succès")
    
    # Backup
    backup_path = file_path.with_suffix('.py.backup_v862')
    backup_path.write_text(original_content, encoding='utf-8')
    print(f"💾 Backup créé : {backup_path.name}")
    
    # Modification 1 : Header version
    content = re.sub(
        r'Version 8\.6\.\d+.*',
        'Version 8.6.4 : SUPPRESSION COMPLÈTE atténuation',
        content,
        count=1
    )
    print("✅ 1/5 : Header version mis à jour")
    
    # Modification 2 : Print statement
    content = re.sub(
        r'print\("🔄 \[RELOAD\] sequence_multi_event_timeline v8\.6\.\d+.*"\)',
        'print("🔄 [RELOAD] sequence_multi_event_timeline v8.6.4 - ZÉRO atténuation (plein impact)")',
        content
    )
    print("✅ 2/5 : Message de chargement mis à jour")
    
    # Modification 3 : base_factor
    content = re.sub(
        r'base_factor = 0\.85  # .*',
        'base_factor = 1.00  # ↑ 0.85 → 1.00',
        content
    )
    print("✅ 3/5 : base_factor = 1.00")
    
    # Modification 4-5 : Tous les facteurs
    replacements = [
        (r'factor = 1\.05  # ↑ 1\.02', 'factor = 1.10  # ↑ 1.05 → 1.10'),
        (r'factor = 0\.90  # ↑ 0\.80', 'factor = 1.20  # ↑ 0.90 → 1.20'),
        (r'factor = 0\.80  # ↑ 0\.66', 'factor = 1.00  # ↑ 0.80 → 1.00'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    print("✅ 4/5 : Facteurs cohérent, surprise, incohérent mis à jour")
    
    # Modification commentaire standard
    content = re.sub(
        r'# Cas standard : atténuation de base',
        '# Cas standard : aucune atténuation',
        content
    )
    content = re.sub(
        r'factor = base_factor$',
        'factor = 1.00  # ↑ 0.85 → 1.00',
        content,
        flags=re.MULTILINE
    )
    print("✅ 5/5 : Facteur standard mis à jour")
    
    # Vérifier les changements
    if content == original_content:
        print("⚠️  ATTENTION : Aucun changement détecté !")
        print("Le fichier est peut-être déjà en v8.6.4")
        return False
    
    # Écrire le fichier modifié
    file_path.write_text(content, encoding='utf-8')
    print(f"\n✅ Fichier modifié : {file_path}")
    
    # Afficher les lignes modifiées
    print("\n📊 Résumé des modifications :")
    print("   - Version : 8.6.2 → 8.6.4")
    print("   - base_factor : 0.85 → 1.00")
    print("   - Facteur cohérent : 1.05 → 1.10")
    print("   - Facteur surprise : 0.90 → 1.20")
    print("   - Facteur standard : 0.85 → 1.00")
    print("   - Facteur incohérent : 0.80 → 1.00")
    
    print("\n🎯 v8.6.4 appliquée avec succès !")
    print(f"💾 Backup disponible : {backup_path.name}")
    
    return True

if __name__ == "__main__":
    print("🚀 Application du patch v8.6.4")
    print("=" * 60)
    success = apply_v864_patch()
    
    if success:
        print("\n✅ SUCCÈS ! Redémarrez Streamlit pour tester :")
        print("   streamlit run fx_impact_app/streamlit_app/Home.py")
    else:
        print("\n❌ Échec de l'application du patch")
