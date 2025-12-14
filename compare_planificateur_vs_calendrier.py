#!/usr/bin/env python3
"""
Compare EXACTEMENT comment le Planificateur et le Calendrier chargent les événements
"""

from pathlib import Path
import re

def extract_function_logic(file_path, start_marker, end_marker):
    """Extrait une section de code entre deux marqueurs"""
    lines = file_path.read_text(encoding='utf-8').split('\n')
    
    extracting = False
    extracted = []
    
    for i, line in enumerate(lines, 1):
        if start_marker in line:
            extracting = True
            extracted.append((i, line))
        elif extracting:
            extracted.append((i, line))
            if end_marker in line:
                break
    
    return extracted

def compare():
    print("🔍 COMPARAISON PLANIFICATEUR VS CALENDRIER")
    print("="*70)
    
    plani = Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
    cal = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    
    # ═══════════════════════════════════════════════════════════
    # 1. COMPARER get_future_events()
    # ═══════════════════════════════════════════════════════════
    
    print("\n📊 1. FONCTION get_future_events()")
    print("-"*70)
    
    # Extraire les signatures
    plani_lines = plani.read_text().split('\n')
    cal_lines = cal.read_text().split('\n')
    
    plani_sig = [l for l in plani_lines if 'def get_future_events(' in l]
    cal_sig = [l for l in cal_lines if 'def get_future_events(' in l]
    
    if plani_sig:
        print(f"\n✅ Planificateur : {plani_sig[0].strip()}")
    else:
        print("\n❌ Planificateur : Fonction non trouvée")
    
    if cal_sig:
        print(f"✅ Calendrier    : {cal_sig[0].strip()}")
    else:
        print("❌ Calendrier    : Fonction non trouvée")
    
    # Comparer les WHERE clauses
    print("\n📋 Clauses WHERE dans les queries :")
    
    plani_where = [l.strip() for l in plani_lines if 'AND e.importance_n' in l or 'WHERE e.ts_utc' in l]
    cal_where = [l.strip() for l in cal_lines if 'AND e.importance_n' in l or 'WHERE e.ts_utc' in l]
    
    print(f"\nPlanificateur ({len(plani_where)} filtres) :")
    for w in plani_where[:5]:
        print(f"   {w}")
    
    print(f"\nCalendrier ({len(cal_where)} filtres) :")
    for w in cal_where[:5]:
        print(f"   {w}")
    
    # ═══════════════════════════════════════════════════════════
    # 2. COMPARER L'USAGE (comment la fonction est appelée)
    # ═══════════════════════════════════════════════════════════
    
    print("\n" + "="*70)
    print("📊 2. COMMENT LA FONCTION EST APPELÉE")
    print("-"*70)
    
    # Planificateur
    plani_calls = []
    for i, line in enumerate(plani_lines, 1):
        if 'get_future_events(' in line and 'def get_future_events' not in line:
            plani_calls.append((i, line.strip()))
    
    print(f"\nPlanificateur ({len(plani_calls)} appels) :")
    for line_num, line in plani_calls[:3]:
        print(f"   Ligne {line_num}: {line[:80]}")
    
    # Calendrier
    cal_calls = []
    for i, line in enumerate(cal_lines, 1):
        if 'get_future_events(' in line and 'def get_future_events' not in line:
            cal_calls.append((i, line.strip()))
    
    print(f"\nCalendrier ({len(cal_calls)} appels) :")
    for line_num, line in cal_calls[:3]:
        print(f"   Ligne {line_num}: {line[:80]}")
    
    # ═══════════════════════════════════════════════════════════
    # 3. COMPARER LE FLUX APRÈS CHARGEMENT
    # ═══════════════════════════════════════════════════════════
    
    print("\n" + "="*70)
    print("📊 3. FLUX APRÈS CHARGEMENT DES ÉVÉNEMENTS")
    print("-"*70)
    
    # Chercher les filtres appliqués APRÈS get_future_events()
    print("\nPlanificateur - Que fait-il après get_future_events() ?")
    
    for i, line in enumerate(plani_lines):
        if 'events = get_future_events(' in line:
            print(f"\n   Ligne {i+1}: {line.strip()}")
            # Afficher les 15 lignes suivantes
            for j in range(i+1, min(i+16, len(plani_lines))):
                if plani_lines[j].strip():
                    print(f"   Ligne {j+1}: {plani_lines[j].strip()[:70]}")
            break
    
    print("\nCalendrier - Que fait-il après get_future_events() ?")
    
    for i, line in enumerate(cal_lines):
        if 'future_events = get_future_events(' in line:
            print(f"\n   Ligne {i+1}: {line.strip()}")
            # Afficher les 15 lignes suivantes
            for j in range(i+1, min(i+16, len(cal_lines))):
                if cal_lines[j].strip():
                    print(f"   Ligne {j+1}: {cal_lines[j].strip()[:70]}")
            break
    
    # ═══════════════════════════════════════════════════════════
    # 4. IDENTIFIER LES DIFFÉRENCES CRITIQUES
    # ═══════════════════════════════════════════════════════════
    
    print("\n" + "="*70)
    print("🔍 4. DIFFÉRENCES CRITIQUES IDENTIFIÉES")
    print("="*70)
    
    differences = []
    
    # Check 1 : min_importance dans signature
    plani_has_min_imp = any('min_importance' in l for l in plani_sig)
    cal_has_min_imp = any('min_importance' in l for l in cal_sig)
    
    if plani_has_min_imp != cal_has_min_imp:
        differences.append(
            f"❌ Paramètre min_importance : "
            f"Planificateur={'OUI' if plani_has_min_imp else 'NON'}, "
            f"Calendrier={'OUI' if cal_has_min_imp else 'NON'}"
        )
    
    # Check 2 : Filtre importance dans query
    plani_filters_imp = any('importance_n' in l for l in plani_where)
    cal_filters_imp = any('importance_n' in l for l in cal_where)
    
    if plani_filters_imp != cal_filters_imp:
        differences.append(
            f"❌ Filtre importance_n dans query : "
            f"Planificateur={'OUI' if plani_filters_imp else 'NON'}, "
            f"Calendrier={'OUI' if cal_filters_imp else 'NON'}"
        )
    
    # Check 3 : Filtres post-chargement
    plani_has_score_filter = any('score' in l and '>=' in l for l in plani_lines)
    cal_has_score_filter = any('score' in l and '>=' in l and 'min_score' in l for l in cal_lines)
    
    if cal_has_score_filter and not plani_has_score_filter:
        differences.append(
            f"❌ Filtre par score : "
            f"Planificateur=NON, Calendrier=OUI (filtre par min_score)"
        )
    
    # Check 4 : Besoin de famille
    plani_needs_family = any('family' in l and 'notna()' in l for l in plani_lines[300:400])
    cal_needs_family = any('family in family_scores' in l for l in cal_lines)
    
    if plani_needs_family != cal_needs_family:
        differences.append(
            f"❌ Requiert famille pour affichage : "
            f"Planificateur={'OUI' if plani_needs_family else 'NON'}, "
            f"Calendrier={'OUI' if cal_needs_family else 'NON'}"
        )
    
    # Afficher les différences
    if differences:
        print("\n🔴 DIFFÉRENCES TROUVÉES :\n")
        for i, diff in enumerate(differences, 1):
            print(f"{i}. {diff}\n")
    else:
        print("\n✅ Aucune différence majeure détectée")
    
    # ═══════════════════════════════════════════════════════════
    # 5. RECOMMANDATION
    # ═══════════════════════════════════════════════════════════
    
    print("="*70)
    print("💡 RECOMMANDATION")
    print("="*70)
    
    print("\n🎯 Pour que le Calendrier fonctionne comme le Planificateur :")
    print("\n1. Retirer ou désactiver le filtre par min_score")
    print("   → Permet d'afficher TOUS les événements trouvés")
    print("\n2. Retirer le filtre 'family in family_scores'")
    print("   → Permet d'afficher les événements même sans scores")
    print("\n3. Copier la logique d'affichage du Planificateur")
    print("   → Afficher événements + calculer scores à la demande")
    
    print("\n📋 Ou plus simple : Utiliser la checkbox 'show_all=True'")

if __name__ == "__main__":
    compare()
