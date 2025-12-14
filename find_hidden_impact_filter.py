#!/usr/bin/env python3
"""
Trouve LE filtre Impact caché qui empêche l'affichage
"""

from pathlib import Path

def find_impact_filter():
    cal_file = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    plani_file = Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
    
    print("🔍 RECHERCHE DU FILTRE IMPACT CACHÉ")
    print("="*70)
    
    # Lire les fichiers
    cal_lines = cal_file.read_text(encoding='utf-8').split('\n')
    plani_lines = plani_file.read_text(encoding='utf-8').split('\n')
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 1 : Chercher TOUS les filtres possibles dans Calendrier
    # ═══════════════════════════════════════════════════════════
    
    print("\n📋 TOUS LES FILTRES DANS LE CALENDRIER :")
    print("-"*70)
    
    filter_keywords = ['filter', 'selected_impacts', 'impact', 'if.*in.*selected']
    
    cal_filters = []
    for i, line in enumerate(cal_lines, 1):
        for keyword in filter_keywords:
            if keyword in line.lower() and ('=' in line or 'if' in line or 'for' in line):
                cal_filters.append((i, line.strip()))
                break
    
    # Afficher tous les filtres trouvés
    seen = set()
    for line_num, line in cal_filters:
        if line not in seen and len(line) > 10:
            print(f"   Ligne {line_num:4d}: {line[:80]}")
            seen.add(line)
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 2 : Chercher filtres dans Planificateur (pour comparer)
    # ═══════════════════════════════════════════════════════════
    
    print("\n📋 FILTRES DANS LE PLANIFICATEUR (comparaison) :")
    print("-"*70)
    
    plani_filters = []
    for i, line in enumerate(plani_lines, 1):
        for keyword in filter_keywords:
            if keyword in line.lower() and ('=' in line or 'if' in line):
                plani_filters.append((i, line.strip()))
                break
    
    seen = set()
    for line_num, line in plani_filters:
        if line not in seen and len(line) > 10:
            print(f"   Ligne {line_num:4d}: {line[:80]}")
            seen.add(line)
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 3 : Chercher où filtered_events est utilisé
    # ═══════════════════════════════════════════════════════════
    
    print("\n📋 UTILISATION DE filtered_events DANS CALENDRIER :")
    print("-"*70)
    
    for i, line in enumerate(cal_lines, 1):
        if 'filtered_events' in line and 'for' in line:
            print(f"   Ligne {i:4d}: {line.strip()[:80]}")
            # Afficher les 5 lignes suivantes
            for j in range(i, min(i+5, len(cal_lines))):
                if cal_lines[j].strip():
                    print(f"        {j+1:4d}: {cal_lines[j].strip()[:70]}")
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 4 : Chercher après "Calendrier des Événements"
    # ═══════════════════════════════════════════════════════════
    
    print("\n📋 CODE APRÈS 'Calendrier des Événements' :")
    print("-"*70)
    
    found_calendar_section = False
    for i, line in enumerate(cal_lines, 1):
        if 'Calendrier des Événements' in line or 'st.subheader("📋' in line:
            found_calendar_section = True
            print(f"   🔍 Section trouvée ligne {i}")
            
        if found_calendar_section and i > 0:
            # Afficher les 30 lignes suivantes
            for j in range(i, min(i+30, len(cal_lines))):
                if cal_lines[j].strip():
                    print(f"   {j+1:4d}: {cal_lines[j].strip()[:80]}")
            break
    
    # ═══════════════════════════════════════════════════════════
    # DIAGNOSTIC
    # ═══════════════════════════════════════════════════════════
    
    print("\n" + "="*70)
    print("🔍 DIAGNOSTIC")
    print("="*70)
    
    # Chercher spécifiquement un filtre par impact dans la boucle d'affichage
    has_impact_filter_in_display = False
    for i, line in enumerate(cal_lines):
        if 'for' in line and 'filtered_events' in line:
            # Chercher dans les 20 lignes suivantes
            for j in range(i, min(i+20, len(cal_lines))):
                if 'impact' in cal_lines[j].lower() and ('==' in cal_lines[j] or 'in' in cal_lines[j]):
                    if 'if' in cal_lines[j]:
                        print(f"\n⚠️  FILTRE TROUVÉ ligne {j+1} :")
                        print(f"   {cal_lines[j].strip()}")
                        has_impact_filter_in_display = True
    
    if not has_impact_filter_in_display:
        print("\n✅ Aucun filtre impact trouvé dans la boucle d'affichage")
        print("\n💡 Le problème est probablement AVANT l'affichage :")
        print("   → Vérifier si filtered_events est vide")
        print("   → Vérifier si le filtre selected_impacts s'applique ailleurs")

if __name__ == "__main__":
    find_impact_filter()
