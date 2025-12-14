#!/usr/bin/env python3
"""
Affiche le code ACTUEL des boutons et checkboxes
Pour voir ce qui est vraiment dans le fichier
"""

from pathlib import Path

def show_current_code():
    file_path = Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
    content = file_path.read_text()
    lines = content.split('\n')
    
    print("🔍 CODE ACTUEL")
    print("=" * 80)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 1 : Bouton "Tout sélectionner"
    # ═══════════════════════════════════════════════════════════
    print("\n1️⃣ BOUTON 'TOUT SÉLECTIONNER'")
    print("-" * 80)
    
    for i, line in enumerate(lines):
        if '✅ Tout sélectionner' in line:
            # Afficher 10 lignes
            for j in range(i, min(len(lines), i+10)):
                print(f"{j+1:4d} | {lines[j]}")
            break
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 2 : Bouton "Tout désélectionner"
    # ═══════════════════════════════════════════════════════════
    print("\n\n2️⃣ BOUTON 'TOUT DÉSÉLECTIONNER'")
    print("-" * 80)
    
    for i, line in enumerate(lines):
        if '❌ Tout désélectionner' in line:
            # Afficher 10 lignes
            for j in range(i, min(len(lines), i+10)):
                print(f"{j+1:4d} | {lines[j]}")
            break
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 3 : Checkbox
    # ═══════════════════════════════════════════════════════════
    print("\n\n3️⃣ CHECKBOX")
    print("-" * 80)
    
    for i, line in enumerate(lines):
        if 'checked = st.checkbox' in line:
            # Vérifier si c'est la bonne (avec selected_indices.append proche)
            is_event_checkbox = False
            for j in range(i, min(len(lines), i+15)):
                if 'selected_indices.append' in lines[j]:
                    is_event_checkbox = True
                    break
            
            if is_event_checkbox:
                # Afficher contexte
                start = max(0, i-8)
                for j in range(start, min(len(lines), i+12)):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{j+1:4d} | {lines[j]}")
                break
    
    # ═══════════════════════════════════════════════════════════
    # ANALYSE
    # ═══════════════════════════════════════════════════════════
    print("\n\n" + "=" * 80)
    print("📊 ANALYSE")
    print("=" * 80)
    
    # Vérifier si event_id est utilisé
    uses_event_id_btn = 'event_id = f"{event' in content
    uses_event_id_chk = 'event_id not in st.session_state.selection_state' in content
    
    print(f"{'✅' if uses_event_id_btn else '❌'} Boutons utilisent event_id : {uses_event_id_btn}")
    print(f"{'✅' if uses_event_id_chk else '❌'} Checkbox utilise event_id : {uses_event_id_chk}")
    
    if not uses_event_id_btn or not uses_event_id_chk:
        print("\n❌ PROBLÈME : Les modifications n'ont pas été appliquées !")
        print("   Le script regex n'a pas matché le code")
    
    # Compter st.rerun()
    rerun_count = content.count('st.rerun()')
    print(f"\nNombre de st.rerun() : {rerun_count}")
    
    # Vérifier structure
    has_for_idx_df = 'for idx in df.index' in content
    has_for_idx_event = 'for idx, event in df.iterrows()' in content
    
    print(f"\n{'❌' if has_for_idx_df else '✅'} 'for idx in df.index' : {has_for_idx_df} (devrait être False)")
    print(f"{'✅' if has_for_idx_event else '❌'} 'for idx, event in df.iterrows()' : {has_for_idx_event} (devrait être True)")

if __name__ == "__main__":
    show_current_code()
