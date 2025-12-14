#!/usr/bin/env python3
"""
Diagnostic complet : Pourquoi les boutons ne fonctionnent pas ?
"""

from pathlib import Path

def diagnose():
    file_path = Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
    content = file_path.read_text()
    lines = content.split('\n')
    
    print("🔍 DIAGNOSTIC BOUTONS SÉLECTION")
    print("=" * 80)
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 1 : Boutons présents et corrects ?
    # ═══════════════════════════════════════════════════════════
    print("\n1️⃣ BOUTONS")
    print("-" * 80)
    
    has_select_all = '✅ Tout sélectionner' in content
    has_deselect_all = '❌ Tout désélectionner' in content
    has_rerun = 'st.rerun()' in content
    
    print(f"{'✅' if has_select_all else '❌'} Bouton 'Tout sélectionner' : {has_select_all}")
    print(f"{'✅' if has_deselect_all else '❌'} Bouton 'Tout désélectionner' : {has_deselect_all}")
    print(f"{'✅' if has_rerun else '❌'} st.rerun() présent : {has_rerun}")
    
    # Afficher code des boutons
    if has_select_all:
        for i, line in enumerate(lines):
            if '✅ Tout sélectionner' in line:
                print(f"\n📍 Bouton 'Tout sélectionner' ligne {i+1}:")
                for j in range(max(0, i-1), min(len(lines), i+6)):
                    print(f"  {j+1:4d} | {lines[j]}")
                break
    
    if has_deselect_all:
        for i, line in enumerate(lines):
            if '❌ Tout désélectionner' in line:
                print(f"\n📍 Bouton 'Tout désélectionner' ligne {i+1}:")
                for j in range(max(0, i-1), min(len(lines), i+6)):
                    print(f"  {j+1:4d} | {lines[j]}")
                break
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 2 : Checkbox lit selection_state ?
    # ═══════════════════════════════════════════════════════════
    print("\n\n2️⃣ CHECKBOXES")
    print("-" * 80)
    
    # Chercher checkbox dans boucle événements
    for i, line in enumerate(lines):
        if 'checked = st.checkbox' in line:
            # Vérifier si c'est la bonne (avec selected_indices.append dans les 10 lignes suivantes)
            is_event_checkbox = False
            for j in range(i, min(len(lines), i+15)):
                if 'selected_indices.append' in lines[j]:
                    is_event_checkbox = True
                    break
            
            if is_event_checkbox:
                print(f"📍 Checkbox événements ligne {i+1}:")
                
                # Afficher contexte
                start = max(0, i-5)
                end = min(len(lines), i+15)
                
                for j in range(start, end):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{j+1:4d} | {lines[j]}")
                
                # Vérifier si lit selection_state
                checkbox_block = '\n'.join(lines[i-5:i+10])
                
                reads_state = 'value=st.session_state.selection_state' in checkbox_block
                updates_state = 'st.session_state.selection_state[idx] = checked' in checkbox_block
                
                print(f"\n{'✅' if reads_state else '❌'} Lit selection_state : {reads_state}")
                print(f"{'✅' if updates_state else '❌'} Met à jour selection_state : {updates_state}")
                
                if not reads_state:
                    print("\n❌ PROBLÈME TROUVÉ : Checkbox ne lit pas selection_state !")
                    print("   → Elle doit avoir : value=st.session_state.selection_state[idx]")
                
                break
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 3 : Ordre d'exécution correct ?
    # ═══════════════════════════════════════════════════════════
    print("\n\n3️⃣ ORDRE D'EXÉCUTION")
    print("-" * 80)
    
    # Trouver positions
    header_line = None
    init_line = None
    buttons_line = None
    loop_line = None
    
    for i, line in enumerate(lines):
        if header_line is None and 'st.header("📋 Sélection des Événements")' in line:
            header_line = i + 1
        if init_line is None and "'selection_state' not in st.session_state" in line:
            init_line = i + 1
        if buttons_line is None and '✅ Tout sélectionner' in line:
            buttons_line = i + 1
        if loop_line is None and 'for date in dates:' in line and i > 1000:  # Après la config
            loop_line = i + 1
    
    print(f"Header     : ligne {header_line if header_line else 'NON TROUVÉ'}")
    print(f"Init state : ligne {init_line if init_line else 'NON TROUVÉ'}")
    print(f"Boutons    : ligne {buttons_line if buttons_line else 'NON TROUVÉ'}")
    print(f"Boucle     : ligne {loop_line if loop_line else 'NON TROUVÉ'}")
    
    order_ok = all([header_line, init_line, buttons_line, loop_line]) and \
               header_line < init_line < buttons_line < loop_line
    
    print(f"\n{'✅' if order_ok else '❌'} Ordre correct : {order_ok}")
    
    if not order_ok:
        print("\n❌ PROBLÈME : Ordre incorrect !")
        print("   Ordre attendu : Header → Init → Boutons → Boucle")
    
    # ═══════════════════════════════════════════════════════════
    # RÉSUMÉ ET RECOMMANDATIONS
    # ═══════════════════════════════════════════════════════════
    print("\n\n" + "=" * 80)
    print("📊 RÉSUMÉ")
    print("=" * 80)
    
    issues = []
    
    if not has_select_all or not has_deselect_all:
        issues.append("❌ Boutons manquants")
    
    if not has_rerun:
        issues.append("❌ st.rerun() manquant")
    
    # Vérifier checkbox (chercher dans le code analysé plus haut)
    if 'value=st.session_state.selection_state' not in content:
        issues.append("❌ Checkbox ne lit pas selection_state")
    
    if not order_ok:
        issues.append("❌ Ordre d'exécution incorrect")
    
    if not issues:
        print("✅ Tout semble correct dans le code")
        print("\n💡 PROBLÈME POSSIBLE :")
        print("   Le cache Streamlit n'est peut-être pas invalidé")
        print("\n🔧 SOLUTION :")
        print("   1. Arrêtez Streamlit (Ctrl+C)")
        print("   2. Supprimez le cache : rm -rf .streamlit/cache")
        print("   3. Relancez : streamlit run fx_impact_app/streamlit_app/Home.py")
    else:
        print("❌ Problèmes détectés :")
        for issue in issues:
            print(f"   {issue}")
    
    print("=" * 80)
    
    return len(issues) == 0

if __name__ == "__main__":
    diagnose()
