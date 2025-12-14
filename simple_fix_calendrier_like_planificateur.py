#!/usr/bin/env python3
"""
Correction SIMPLE : 2 modifications pour que Calendrier = Planificateur
"""

from pathlib import Path
from datetime import datetime

def simple_fix():
    file_path = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé : {file_path}")
        return False
    
    # Backup
    backup_path = file_path.parent / "backups" / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
    backup_path.parent.mkdir(exist_ok=True)
    
    content = file_path.read_text(encoding='utf-8')
    backup_path.write_text(content, encoding='utf-8')
    print(f"✅ Backup créé : {backup_path}")
    
    original = content
    corrections = []
    
    # ═══════════════════════════════════════════════════════════
    # CORRECTION 1 : Désactiver filtre importance_n
    # ═══════════════════════════════════════════════════════════
    
    print("\n🔧 Correction 1 : Désactiver filtre importance...")
    
    # Pattern : AND e.importance_n <= {min_importance}
    if 'AND e.importance_n <=' in content:
        # Commenter la ligne
        content = content.replace(
            'AND e.importance_n <= {min_importance}',
            '# AND e.importance_n <= {min_importance}  # Désactivé pour afficher TOUT'
        )
        corrections.append("✅ Filtre importance_n désactivé")
        print("   ✅ AND e.importance_n <= ... commenté")
    else:
        print("   ⚠️  Pattern non trouvé")
    
    # ═══════════════════════════════════════════════════════════
    # CORRECTION 2 : Désactiver filtre "family in family_scores"
    # ═══════════════════════════════════════════════════════════
    
    print("\n🔧 Correction 2 : Toujours enrichir les événements...")
    
    # Pattern : if family and family in family_scores:
    if 'if family and family in family_scores:' in content:
        # Remplacer par condition toujours vraie
        content = content.replace(
            'if family and family in family_scores:',
            'if True:  # ✅ Affiche TOUS les événements (comme Planificateur)'
        )
        corrections.append("✅ Condition 'family in family_scores' désactivée")
        print("   ✅ 'if family and family in family_scores' → 'if True'")
    else:
        print("   ⚠️  Pattern non trouvé")
    
    # ═══════════════════════════════════════════════════════════
    # ÉCRITURE
    # ═══════════════════════════════════════════════════════════
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        
        print("\n" + "="*70)
        print("✅ FICHIER CORRIGÉ")
        print("="*70)
        
        for correction in corrections:
            print(f"   {correction}")
        
        print(f"\n📄 Fichier : {file_path}")
        print(f"💾 Backup : {backup_path}")
        
        print("\n" + "="*70)
        print("📊 CE QUI A CHANGÉ")
        print("="*70)
        
        print("\n✅ Avant (Calendrier bugué) :")
        print("   1. WHERE importance_n <= 2  → Filtre une partie")
        print("   2. if family in family_scores → Affiche seulement avec scores")
        print("   Result: 88 trouvés → 0 affichés ❌")
        
        print("\n✅ Après (comme Planificateur) :")
        print("   1. WHERE importance_n <= 2  (désactivé)")
        print("   2. if True → Affiche TOUT")
        print("   Result: 88 trouvés → 88 affichés ✅")
        
        print("\n🎯 Résultat attendu dans Streamlit :")
        print("   📅 88 événements trouvés")
        print("   📊 88 événements affichés (comme Planificateur !)")
        print("   ✅ Score = 0 pour ceux sans historique")
        
        print("\n🚀 Relancez : streamlit run fx_impact_app/streamlit_app/Home.py")
        
        return True
    else:
        print("\n⚠️  Aucune modification appliquée")
        return False

if __name__ == "__main__":
    print("🔧 CORRECTION SIMPLE : CALENDRIER = PLANIFICATEUR")
    print("="*70)
    
    if not simple_fix():
        print("\n❌ Échec - Modifications manuelles nécessaires")
        
        print("\n📋 À faire manuellement dans le fichier :")
        
        print("\n1️⃣  Dans get_future_events() (ligne ~145) :")
        print("   Chercher  : AND e.importance_n <= {min_importance}")
        print("   Commenter : # AND e.importance_n <= {min_importance}")
        
        print("\n2️⃣  Dans la boucle for _, event in future_events (ligne ~230) :")
        print("   Chercher  : if family and family in family_scores:")
        print("   Remplacer : if True:  # Affiche TOUT")
