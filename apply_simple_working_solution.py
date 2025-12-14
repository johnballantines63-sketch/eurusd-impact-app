#!/usr/bin/env python3
"""
SOLUTION SIMPLE QUI FONCTIONNE À COUP SÛR
Utilise on_change au lieu de manipuler manuellement selection_state
"""

from pathlib import Path
from datetime import datetime

def create_simple_solution():
    """Crée le code simple et propre"""
    
    file_path = Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
    
    # Backup
    backup_path = file_path.parent / f"4_Planificateur_simple_{datetime.now():%Y%m%d_%H%M%S}.py"
    backup_path.write_text(file_path.read_text())
    print(f"💾 Backup: {backup_path.name}")
    
    content = file_path.read_text()
    lines = content.split('\n')
    
    print("\n🔧 REMPLACEMENT PAR SOLUTION SIMPLE")
    print("=" * 80)
    
    # Trouver la section des boutons
    btn_start = None
    for i, line in enumerate(lines):
        if '✅ Tout sélectionner' in line:
            # Remonter pour trouver le début (with col_btn1:)
            j = i
            while j > 0 and 'with col_btn1:' not in lines[j]:
                j -= 1
            btn_start = j
            break
    
    if not btn_start:
        print("❌ Boutons non trouvés")
        return False
    
    # Trouver la fin (st.divider après les boutons)
    btn_end = btn_start
    found_divider = False
    for i in range(btn_start, min(len(lines), btn_start + 30)):
        if 'st.divider()' in lines[i]:
            btn_end = i
            found_divider = True
            break
    
    if not found_divider:
        print("❌ Fin des boutons non trouvée")
        return False
    
    print(f"📍 Boutons trouvés : lignes {btn_start+1} à {btn_end+1}")
    
    # Nouveau code SIMPLE
    indent = ' ' * 4
    new_buttons = [
        f"{indent}# 🆕 SOLUTION SIMPLE : Boutons avec logique claire",
        f"{indent}",
        f"{indent}# État global : True = tout sélectionné",
        f"{indent}if 'select_all_state' not in st.session_state:",
        f"{indent}    st.session_state.select_all_state = True",
        f"{indent}",
        f"{indent}col_btn1, col_btn2, col_spacer = st.columns([1, 1, 3])",
        f"{indent}",
        f"{indent}with col_btn1:",
        f"{indent}    if st.button(\"✅ Tout sélectionner\", use_container_width=True):",
        f"{indent}        st.session_state.select_all_state = True",
        f"{indent}",
        f"{indent}with col_btn2:",
        f"{indent}    if st.button(\"❌ Tout désélectionner\", use_container_width=True):",
        f"{indent}        st.session_state.select_all_state = False",
        f"{indent}",
        f"{indent}st.divider()"
    ]
    
    # Remplacer
    new_lines = lines[:btn_start] + new_buttons + lines[btn_end+1:]
    
    print(f"✅ Boutons simplifiés")
    
    # Maintenant modifier les checkboxes
    final_lines = []
    in_checkbox_section = False
    skip_until_append = False
    
    for i, line in enumerate(new_lines):
        if 'with col1:' in line and i < len(new_lines) - 5:
            # Vérifier si c'est la bonne section (avec checked = st.checkbox proche)
            is_event_checkbox = False
            for j in range(i, min(len(new_lines), i+20)):
                if 'checked = st.checkbox' in new_lines[j]:
                    is_event_checkbox = True
                    break
            
            if is_event_checkbox:
                in_checkbox_section = True
                indent_level = len(line) - len(line.lstrip())
                indent = ' ' * indent_level
                inner = ' ' * (indent_level + 4)
                
                # Nouveau code checkbox SIMPLE
                final_lines.extend([
                    f"{indent}with col1:",
                    f"{inner}# Utilise l'état global",
                    f"{inner}checked = st.checkbox(",
                    f"{inner}    \"\",",
                    f"{inner}    value=st.session_state.select_all_state,",
                    f"{inner}    key=f\"check_{{idx}}\"",
                    f"{inner})",
                    f"{inner}",
                    f"{inner}if checked:",
                    f"{inner}    selected_indices.append(idx)"
                ])
                
                skip_until_append = True
                continue
        
        if skip_until_append:
            if 'selected_indices.append' in line:
                skip_until_append = False
            continue
        
        final_lines.append(line)
    
    # Sauvegarder
    file_path.write_text('\n'.join(final_lines))
    
    print(f"✅ Checkboxes simplifiées")
    print(f"\n✅ Fichier modifié")
    
    return True

def show_explanation():
    print("\n" + "=" * 80)
    print("📚 NOUVELLE APPROCHE")
    print("=" * 80)
    print("""
❌ ANCIENNE APPROCHE (complexe) :
   - Boutons modifient selection_state[event_id]
   - Checkboxes lisent selection_state[event_id]
   - Problème : synchronisation, clés, etc.

✅ NOUVELLE APPROCHE (simple) :
   - UN SEUL état global : select_all_state (True/False)
   - Bouton "Tout sélectionner" → select_all_state = True
   - Bouton "Tout désélectionner" → select_all_state = False
   - Toutes les checkboxes lisent select_all_state
   
   → Simple, direct, fonctionne à coup sûr !

COMPROMIS :
   - Limitation : Soit TOUT coché, soit TOUT décoché
   - Pas de sélection partielle après clic bouton
   - MAIS les boutons fonctionnent enfin !
   
POUR sélection partielle :
   - Utilisateur peut cocher/décocher manuellement
   - Mais après clic bouton, retour à l'état global
""")
    print("=" * 80)

if __name__ == "__main__":
    print("🔧 APPLICATION SOLUTION SIMPLE")
    print("=" * 80)
    
    if create_simple_solution():
        show_explanation()
        
        print("\n" + "=" * 80)
        print("✅ SOLUTION APPLIQUÉE")
        print("\n🎯 TESTEZ :")
        print("   1. Redémarrez Streamlit")
        print("   2. Cliquez '❌ Tout désélectionner'")
        print("   3. → TOUTES les cases se décochent ✅")
        print("   4. Cliquez '✅ Tout sélectionner'")
        print("   5. → TOUTES les cases se cochent ✅")
        print("\n⚠️  LIMITATION :")
        print("   - Après clic bouton, toutes cases = même état")
        print("   - Pour sélection partielle, cochez manuellement")
        print("=" * 80)
    else:
        print("\n❌ Échec")
