#!/usr/bin/env python3
"""
Correction FINALE : Retirer le filtre par selected_impacts (lignes 314-322)
"""

from pathlib import Path
from datetime import datetime

def remove_impact_filter():
    file_path = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé : {file_path}")
        return False
    
    # Backup
    backup_path = file_path.parent / "backups" / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
    backup_path.parent.mkdir(exist_ok=True)
    
    lines = file_path.read_text(encoding='utf-8').split('\n')
    backup_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ Backup créé : {backup_path}")
    
    # ═══════════════════════════════════════════════════════════
    # Trouver et COMMENTER le bloc lignes 314-324
    # ═══════════════════════════════════════════════════════════
    
    print("\n🔧 Recherche du bloc de filtrage par impact...")
    
    new_lines = []
    in_filter_block = False
    block_start = None
    lines_commented = 0
    
    for i, line in enumerate(lines):
        # Détecter le début du bloc
        if 'if selected_impacts:' in line and not in_filter_block:
            in_filter_block = True
            block_start = i
            indent = len(line) - len(line.lstrip())
            
            # Commenter cette ligne
            new_lines.append(' ' * indent + '# ' + line.lstrip() + '  # ❌ Filtre désactivé')
            lines_commented += 1
            print(f"   🔍 Bloc trouvé ligne {i+1}")
            continue
        
        # Si dans le bloc, commenter jusqu'à la fin
        if in_filter_block:
            current_indent = len(line) - len(line.lstrip())
            
            # Fin du bloc si retour à l'indentation initiale OU ligne vide suivie d'indentation normale
            if line.strip() and current_indent <= indent:
                in_filter_block = False
                print(f"   ✅ Fin du bloc ligne {i}, {lines_commented} lignes commentées")
                new_lines.append(line)
                continue
            
            # Commenter la ligne
            if line.strip():
                new_lines.append(' ' * current_indent + '# ' + line.lstrip())
                lines_commented += 1
            else:
                new_lines.append(line)
            continue
        
        new_lines.append(line)
    
    # ═══════════════════════════════════════════════════════════
    # ÉCRITURE
    # ═══════════════════════════════════════════════════════════
    
    if lines_commented > 0:
        file_path.write_text('\n'.join(new_lines), encoding='utf-8')
        
        print("\n" + "="*70)
        print("✅ FICHIER CORRIGÉ")
        print("="*70)
        
        print(f"\n   ✅ {lines_commented} lignes commentées (lignes ~314-322)")
        
        print(f"\n📄 Fichier : {file_path}")
        print(f"💾 Backup : {backup_path}")
        
        print("\n" + "="*70)
        print("📊 FLUX AVANT/APRÈS")
        print("="*70)
        
        print("\n❌ AVANT :")
        print("""
    92 enriched_events
        ↓
    filtered_events = enriched_events
        ↓
    SI selected_impacts:
        filtered_events = [e if impact in selected_impacts]
        → Tous ont impact='Unknown' → 0 passent ! ❌
        ↓
    0 événements affichés
        """)
        
        print("\n✅ APRÈS :")
        print("""
    92 enriched_events
        ↓
    filtered_events = enriched_events
        ↓
    # SI selected_impacts: (DÉSACTIVÉ)
        ↓
    92 événements affichés ! 🎉
        """)
        
        print("\n🎯 Résultat attendu :")
        print("   📅 92 événements trouvés")
        print("   📊 92 événements affichés")
        print("   ✅ Comme le Planificateur !")
        
        print("\n🚀 Relancez : streamlit run fx_impact_app/streamlit_app/Home.py")
        
        return True
    else:
        print("\n⚠️  Bloc non trouvé ou déjà commenté")
        return False

if __name__ == "__main__":
    print("🔧 CORRECTION FINALE : RETIRER FILTRE IMPACT")
    print("="*70)
    
    if not remove_impact_filter():
        print("\n❌ Échec - Modification manuelle nécessaire")
        
        print("\n📋 À faire manuellement :")
        print("\n   Ligne ~314-322 : Commenter tout le bloc")
        print("""
    # if selected_impacts:
    #     if use_empirical:
    #         filtered_events = [e for e in filtered_events 
    #                           if e.get('impact_empirical', 'Unknown') in selected_impacts]
    #     else:
    #         filtered_events = [e for e in filtered_events 
    #                           if e.get('impact_calendar', 'Unknown') in selected_impacts]
        """)
