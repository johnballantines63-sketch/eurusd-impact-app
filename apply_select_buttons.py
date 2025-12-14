#!/usr/bin/env python3
"""
Script pour ajouter boutons Sélectionner/Désélectionner tout
au Planificateur Multi-Événements
"""

import re
from pathlib import Path
from datetime import datetime

def add_selection_buttons():
    """Ajoute les boutons de sélection globale"""
    
    file_path = Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé: {file_path}")
        return False
    
    # Backup
    backup_path = file_path.parent / f"4_Planificateur_select_buttons_backup_{datetime.now():%Y%m%d_%H%M%S}.py"
    backup_path.write_text(file_path.read_text())
    print(f"💾 Backup: {backup_path.name}")
    
    content = file_path.read_text()
    
    # ═══════════════════════════════════════════════════════════
    # MODIFICATION 1 : Ajouter boutons après le header
    # ═══════════════════════════════════════════════════════════
    
    pattern1 = r'(st\.header\("📋 Sélection des Événements"\)\s*\n\s*selected_indices = \[\])'
    
    replacement1 = '''st.header("📋 Sélection des Événements")
    
    # ═══════════════════════════════════════════════════════════
    # 🆕 BOUTONS SÉLECTION/DÉSÉLECTION GLOBALE
    # ═══════════════════════════════════════════════════════════
    
    # Initialiser état sélection si absent
    if 'selection_state' not in st.session_state:
        st.session_state.selection_state = {}
    
    # Boutons en ligne
    col_btn1, col_btn2, col_spacer = st.columns([1, 1, 3])
    
    with col_btn1:
        if st.button("✅ Tout sélectionner", use_container_width=True):
            # Marquer tous les événements comme sélectionnés
            for idx in df.index:
                st.session_state.selection_state[idx] = True
            st.rerun()
    
    with col_btn2:
        if st.button("❌ Tout désélectionner", use_container_width=True):
            # Marquer tous les événements comme désélectionnés
            for idx in df.index:
                st.session_state.selection_state[idx] = False
            st.rerun()
    
    st.divider()
    
    selected_indices = []'''
    
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)
        print("✅ Boutons ajoutés après header")
    else:
        print("⚠️  Pattern 1 non trouvé - Cherche variante...")
        # Essayer sans selected_indices
        pattern1_alt = r'st\.header\("📋 Sélection des Événements"\)'
        if pattern1_alt in content:
            content = content.replace(
                pattern1_alt,
                pattern1_alt + '\n\n' + replacement1.split('\n', 1)[1]
            )
            print("✅ Boutons ajoutés (variante)")
    
    # ═══════════════════════════════════════════════════════════
    # MODIFICATION 2 : Modifier checkbox pour utiliser session_state
    # ═══════════════════════════════════════════════════════════
    
    pattern2 = r'''with col1:
                checked = st\.checkbox\(
                    "",
                    value=True,  # ✅ Coché par défaut
                    key=f"check_\{idx\}"
                \)
                if checked:
                    selected_indices\.append\(idx\)'''
    
    replacement2 = '''with col1:
                # Déterminer état par défaut
                if idx not in st.session_state.selection_state:
                    # Premier chargement : tout coché par défaut
                    default_value = True
                    st.session_state.selection_state[idx] = True
                else:
                    # Utiliser état stocké
                    default_value = st.session_state.selection_state[idx]
                
                checked = st.checkbox(
                    "",
                    value=default_value,
                    key=f"check_{idx}"
                )
                
                # Mettre à jour état
                st.session_state.selection_state[idx] = checked
                
                if checked:
                    selected_indices.append(idx)'''
    
    if re.search(pattern2, content, re.MULTILINE):
        content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
        print("✅ Checkbox modifiée pour session_state")
    else:
        print("⚠️  Pattern 2 non trouvé - Modification manuelle requise")
    
    # Sauvegarder
    file_path.write_text(content)
    print(f"\n✅ Fichier modifié: {file_path}")
    
    return True

def verify_modifications():
    """Vérifie que les modifications sont présentes"""
    
    file_path = Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
    content = file_path.read_text()
    
    print("\n🔍 VÉRIFICATION:")
    print("=" * 80)
    
    checks = [
        ("✅ Tout sélectionner", "✅ Tout sélectionner"),
        ("❌ Tout désélectionner", "❌ Tout désélectionner"),
        ("selection_state", "'selection_state' not in st.session_state"),
        ("st.rerun()", "st.rerun()")
    ]
    
    all_ok = True
    for name, pattern in checks:
        if pattern in content:
            print(f"✅ {name} présent")
        else:
            print(f"❌ {name} manquant")
            all_ok = False
    
    return all_ok

if __name__ == "__main__":
    print("🔧 AJOUT BOUTONS SÉLECTION/DÉSÉLECTION")
    print("=" * 80)
    
    if add_selection_buttons():
        if verify_modifications():
            print("\n" + "=" * 80)
            print("✅ MODIFICATIONS APPLIQUÉES AVEC SUCCÈS")
            print("\n🎯 PROCHAINES ÉTAPES:")
            print("   1. Recharger Streamlit (Ctrl+R ou F5)")
            print("   2. Aller dans Planificateur Multi-Événements")
            print("   3. Tester les boutons ✅ et ❌")
            print("=" * 80)
        else:
            print("\n⚠️  Vérification partielle - Testez manuellement")
    else:
        print("\n❌ ÉCHEC - Modification manuelle requise")
