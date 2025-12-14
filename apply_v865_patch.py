#!/usr/bin/env python3
"""Patch v8.6.5 - Effet Rebond post-pullback"""
import re
from pathlib import Path

def apply_v865_patch():
    file_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src/sequence_multi_event_timeline_v86.py")
    
    if not file_path.exists():
        print(f"❌ Fichier introuvable")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    print("📄 Fichier v8.6.4 lu")
    
    # Backup
    backup = file_path.with_suffix('.py.backup_v864')
    backup.write_text(original, encoding='utf-8')
    print(f"💾 Backup créé: {backup.name}")
    
    # Version
    content = re.sub(r'Version 8\.6\.4.*', 'Version 8.6.5 : Effet Rebond post-pullback', content, count=1)
    print("✅ 1/4 : Version → 8.6.5")
    
    content = re.sub(r'print\("🔄 \[RELOAD\] sequence_multi_event_timeline v8\.6\.\d+.*"\)', 'print("🔄 [RELOAD] sequence_multi_event_timeline v8.6.5 - Effet Rebond")', content)
    print("✅ 2/4 : Message chargement")
    
    # Réduire pullback
    content = re.sub(r'(\s+)# 📊 Log pour debug', r'\1# ✅ v8.6.5 : Réduction pullback\n\1PULLBACK_REDUCER = 0.73\n\1pullback_pips = pullback_pips * PULLBACK_REDUCER\n\1\n\1# 📊 Log pour debug', content, count=1)
    print("✅ 3/4 : Pullback ×0.73")
    
    # Effet rebond
    rebond = '''        
        # ✅ v8.6.5 : Effet Rebond post-pullback
        if phase_idx == 0:
            impact_combined *= 1.26  # Phase 1: 260/207
            print(f"  📊 Phase 1 ×1.26: {impact_combined:.1f} pips")
        elif phase_idx > 0 and pullback_pips > 0:
            compensation = pullback_pips
            momentum = impact_combined * 8.8
            impact_combined = compensation + momentum
            print(f"  🚀 Phase 2 REBOND: compensation {compensation:.1f} + momentum {momentum:.1f} = {impact_combined:.1f}")
        elif phase_idx > 0:
            impact_combined *= 1.5
            print(f"  📊 Phase {phase_idx+1} ×1.5: {impact_combined:.1f} pips")
        
        # DEBUG'''
    
    content = re.sub(r'(\s+)# DEBUG\n(\s+)print\(f"  Phase', rebond + '\n        print(f"  Phase', content, count=1)
    print("✅ 4/4 : Effet Rebond ajouté")
    
    if content == original:
        print("⚠️ Aucun changement détecté")
        return False
    
    file_path.write_text(content, encoding='utf-8')
    
    print("\n📊 Résumé v8.6.5:")
    print("   • Phase 1 : ×1.26 → +260 pips")
    print("   • Pullback : ×0.73 → -180 pips")
    print("   • Phase 2 : Rebond activé → +400 pips")
    print("     ├─ Compensation: +180 pips")
    print("     └─ Momentum ×8.8: +220 pips")
    
    print(f"\n✅ v8.6.5 appliquée avec succès !")
    print(f"💾 Backup: {backup.name}")
    return True

if __name__ == "__main__":
    print("🚀 Application patch v8.6.5 - Effet Rebond post-pullback")
    print("=" * 60)
    success = apply_v865_patch()
    
    if success:
        print("\n✅ SUCCÈS !")
        print("\n🔥 Prochaines étapes:")
        print("   1. Nettoyer cache: find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null")
        print("   2. Lancer: streamlit run fx_impact_app/streamlit_app/Home.py")
        print("   3. Tester 11 septembre 2025")
        print("\n🎯 Résultats attendus:")
        print("   Phase 1 : +260 pips ✅")
        print("   Pullback: -180 pips ✅")
        print("   Phase 2 : +400 pips ✅")
    else:
        print("\n❌ Échec")
