#!/usr/bin/env python3
"""
Diagnostic : Pourquoi 88 trouvés mais seulement 30 affichés ?
"""

from pathlib import Path

def diagnose():
    file_path = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé")
        return
    
    lines = file_path.read_text(encoding='utf-8').split('\n')
    
    print("🔍 DIAGNOSTIC : 88 TROUVÉS → 30 AFFICHÉS")
    print("="*70)
    
    issues = []
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 1 : show_all activé par défaut ?
    # ═══════════════════════════════════════════════════════════
    
    print("\n📋 CHECK 1 : Checkbox show_all...")
    
    for i, line in enumerate(lines, 1):
        if 'show_all = st.sidebar.checkbox' in line:
            print(f"   Ligne {i}: {line.strip()}")
            
            if 'value=True' in line:
                print("   ✅ show_all activé par défaut")
            elif 'value=False' in line:
                print("   ❌ show_all DÉSACTIVÉ par défaut !")
                issues.append("show_all=False")
            else:
                print("   ⚠️  Pas de value= spécifié (défaut=False)")
                issues.append("show_all pas défini")
            break
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 2 : Filtre par min_score ?
    # ═══════════════════════════════════════════════════════════
    
    print("\n📋 CHECK 2 : Filtre par score minimum...")
    
    score_filters = []
    for i, line in enumerate(lines, 1):
        if 'filtered_events' in line and 'min_score' in line:
            score_filters.append((i, line.strip()))
    
    if score_filters:
        print(f"   ⚠️  {len(score_filters)} filtre(s) par score trouvé(s) :")
        for line_num, line in score_filters:
            print(f"   Ligne {line_num}: {line[:70]}")
            if "e['score'] >= min_score" in line:
                issues.append(f"Filtre score ligne {line_num}")
    else:
        print("   ✅ Pas de filtre par min_score")
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 3 : Filtre par impact sélectionné ?
    # ═══════════════════════════════════════════════════════════
    
    print("\n📋 CHECK 3 : Filtre par impact...")
    
    impact_filters = []
    for i, line in enumerate(lines, 1):
        if 'selected_impacts' in line and 'filter' in line.lower():
            impact_filters.append((i, line.strip()))
    
    if impact_filters:
        print(f"   ⚠️  {len(impact_filters)} filtre(s) par impact trouvé(s) :")
        for line_num, line in impact_filters[:3]:
            print(f"   Ligne {line_num}: {line[:70]}")
    else:
        print("   ✅ Pas de filtre par impact")
    
    # ═══════════════════════════════════════════════════════════
    # CHECK 4 : Combien d'événements passent le filtre ?
    # ═══════════════════════════════════════════════════════════
    
    print("\n📋 CHECK 4 : Analyse du flux de filtrage...")
    
    for i, line in enumerate(lines, 1):
        if 'for _, event in future_events.iterrows():' in line:
            print(f"\n   🔍 Boucle d'enrichissement ligne {i}")
            print(f"   Input: future_events (88 événements)")
            
            # Chercher les conditions
            conditions = []
            for j in range(i, min(i+30, len(lines))):
                if 'if family and family in family_scores:' in lines[j]:
                    conditions.append(f"Ligne {j+1}: if family in family_scores → Affiche avec scores")
                elif 'elif show_all:' in lines[j]:
                    conditions.append(f"Ligne {j+1}: elif show_all → Affiche sans scores")
            
            print(f"\n   Conditions trouvées :")
            for cond in conditions:
                print(f"   - {cond}")
            
            break
    
    # ═══════════════════════════════════════════════════════════
    # RÉSUMÉ
    # ═══════════════════════════════════════════════════════════
    
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES PROBLÈMES")
    print("="*70)
    
    if issues:
        print(f"\n❌ {len(issues)} problème(s) trouvé(s) :\n")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        
        print("\n💡 SOLUTIONS RECOMMANDÉES :")
        
        if 'show_all=False' in issues or 'show_all pas défini' in issues:
            print("\n1️⃣  Activer show_all par défaut :")
            print("   show_all = st.sidebar.checkbox(..., value=True)")
        
        if any('Filtre score' in issue for issue in issues):
            print("\n2️⃣  Retirer le filtre par min_score :")
            print("   Commenter : filtered_events = [e for e in ... if e['score'] >= min_score]")
    else:
        print("\n✅ Aucun problème évident détecté dans le code")
        print("\n💡 Vérifier manuellement :")
        print("   1. La checkbox 'Afficher tous' est-elle cochée dans l'interface ?")
        print("   2. Y a-t-il des filtres Impact/Pays qui réduisent les résultats ?")
    
    print("\n" + "="*70)
    print("🎯 EXPLICATION DU FLUX")
    print("="*70)
    
    print("""
88 événements trouvés par get_future_events()
    ↓
Pour chaque événement :
    ├─ Si famille ET dans family_scores → enriched_events (avec scores)
    ├─ Sinon si show_all=True → enriched_events (score=0)
    └─ Sinon → IGNORÉ
    ↓
enriched_events = X événements
    ↓
SI filtre score : filtered_events = [e for e if score >= 40]
    ↓
SI filtre impact : filtered_events = [e for e if impact in selected]
    ↓
Événements totaux affichés = 30
    """)

if __name__ == "__main__":
    diagnose()
