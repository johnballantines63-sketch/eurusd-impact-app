#!/usr/bin/env python3
"""
DÉFINIR CAS DE RÉFÉRENCE - SESSION 130 ÉTAPE 3
===============================================

Sélectionne UN cas de référence par pattern pour calibration.

CRITÈRES SÉLECTION (ordre de priorité) :
1. Données prix complètes (pas de gaps)
2. Events causaux clairement identifiés (n_events >= 2)
3. Impact significatif mais pas outlier extrême (percentile 50-75)
4. Pattern "pur" (pas hybride ou edge case)
5. Validation antérieure si possible (ex: 11 sept)

Output : reference_cases.json avec UN cas par pattern

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import statistics

# Chemins
INPUT_FILE = Path(__file__).parent / "patterns_classified.json"
OUTPUT_FILE = Path(__file__).parent / "reference_cases.json"

# Cas validés sessions antérieures
VALIDATED_CASES = {
    "DoubleWave_Overlap": {
        "date": "2025-09-11",
        "reason": "Validé Session 115 (MAE 0.29 pips)",
        "priority": 1  # Priorité absolue
    }
}

# Patterns cibles
TARGET_PATTERNS = [
    "DoubleWave_Overlap",
    "DoubleWave_Cascade",
    "SingleWave_Fort",
    "SingleWave_Intermediate",
    "ZigZag"
]


def select_reference_case(pattern: str, validable_cases: List[Dict]) -> Optional[Dict]:
    """
    Sélectionne LE meilleur cas de référence pour un pattern.
    
    Stratégie :
    1. Si cas validé antérieurement → prendre celui-ci
    2. Sinon filtrer :
       - n_events >= 2 (événements clairs)
       - Impact dans percentile 50-75 (significatif mais pas outlier)
    3. Trier par critère qualité (n_events desc, impact)
    4. Prendre le meilleur
    
    Returns:
        Dict cas sélectionné ou None si aucun candidat
    """
    if not validable_cases:
        return None
    
    # ÉTAPE 1 : Cas validé antérieurement ?
    if pattern in VALIDATED_CASES:
        validated = VALIDATED_CASES[pattern]
        # Chercher dans validable_cases
        for case in validable_cases:
            if case["date"] == validated["date"]:
                print(f"   ✅ Cas validé antérieurement trouvé : {validated['date']}")
                print(f"      Raison : {validated['reason']}")
                return case
    
    # ÉTAPE 2 : Filtrage candidats
    # Filtre : n_events >= 2
    candidates = [c for c in validable_cases if c["n_events"] >= 2]
    
    if not candidates:
        # Fallback : au moins 1 event
        candidates = [c for c in validable_cases if c["n_events"] >= 1]
    
    if not candidates:
        return None
    
    print(f"   Candidats après filtrage : {len(candidates)}/{len(validable_cases)}")
    
    # ÉTAPE 3 : Sélection impact médian (éviter outliers)
    impacts = [c["impact_pips"] for c in candidates]
    
    if len(impacts) >= 4:
        # Calculer percentiles
        p25 = statistics.quantiles(impacts, n=4)[0]  # 25th
        p50 = statistics.quantiles(impacts, n=2)[0]  # 50th (median)
        p75 = statistics.quantiles(impacts, n=4)[2]  # 75th
        
        # Préférer percentile 50-75
        preferred = [c for c in candidates 
                    if p50 <= c["impact_pips"] <= p75]
        
        if preferred:
            candidates = preferred
            print(f"   Après filtre percentile 50-75 : {len(candidates)}")
    
    # ÉTAPE 4 : Trier par qualité
    # Critères : n_events (desc), impact (asc pour éviter outliers)
    candidates_sorted = sorted(candidates, 
                               key=lambda c: (-c["n_events"], c["impact_pips"]))
    
    # Prendre le meilleur
    selected = candidates_sorted[0]
    
    print(f"   ✅ Sélectionné : {selected['date']}")
    print(f"      Impact : {selected['impact_pips']:.1f} pips")
    print(f"      Events : {selected['n_events']}")
    
    return selected


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("DÉFINIR CAS DE RÉFÉRENCE - ÉTAPE 3")
    print("=" * 80)
    
    # Charger classifications
    print(f"\n📂 Chargement : {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        print(f"❌ Fichier introuvable : {INPUT_FILE}")
        print("   Lancez d'abord classify_patterns.py")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    validable = data["validable_cases"]
    statistics_data = data["statistics"]
    
    print(f"✅ Classifications chargées")
    
    # Sélection cas référence
    print(f"\n" + "=" * 80)
    print("SÉLECTION CAS DE RÉFÉRENCE")
    print("=" * 80)
    
    reference_cases = {}
    
    for pattern in TARGET_PATTERNS:
        print(f"\n🔍 Pattern : {pattern}")
        
        if pattern not in validable:
            print(f"   ❌ Aucun cas validable")
            continue
        
        cases = validable[pattern]
        print(f"   Cas validables : {len(cases)}")
        
        if not cases:
            print(f"   ❌ Aucun cas avec événements")
            continue
        
        # Sélectionner référence
        selected = select_reference_case(pattern, cases)
        
        if selected:
            reference_cases[pattern] = {
                "date": selected["date"],
                "impact_real": selected["impact_pips"],
                "baseline_time": selected["baseline_time"],
                "peak_time": selected["peak_time"],
                "direction": selected["direction"],
                "wave1_pips": selected.get("wave1_pips", 0),
                "pullback_ratio": selected.get("pullback_ratio", 0),
                "wave2_pips": selected.get("wave2_pips", 0),
                "events": selected["events"],
                "n_events": selected["n_events"],
                "status": "validated" if pattern in VALIDATED_CASES 
                         and selected["date"] == VALIDATED_CASES[pattern]["date"]
                         else "to_validate"
            }
        else:
            print(f"   ⚠️ Aucun cas sélectionnable")
    
    # Résumé sélection
    print(f"\n" + "=" * 80)
    print("RÉSUMÉ CAS DE RÉFÉRENCE")
    print("=" * 80)
    
    print(f"\n📋 Cas sélectionnés : {len(reference_cases)}/{len(TARGET_PATTERNS)}")
    print()
    
    for pattern, ref_case in reference_cases.items():
        status_icon = "✅" if ref_case["status"] == "validated" else "⏳"
        print(f"{status_icon} {pattern:<30s}")
        print(f"   Date : {ref_case['date']}")
        print(f"   Impact : {ref_case['impact_real']:.1f} pips")
        print(f"   Events : {ref_case['n_events']}")
        print(f"   Statut : {ref_case['status']}")
        
        if ref_case["status"] == "validated":
            validated_info = VALIDATED_CASES.get(pattern, {})
            print(f"   Validation : {validated_info.get('reason', 'N/A')}")
    
    # Table référence
    print(f"\n" + "=" * 80)
    print("TABLE RÉFÉRENCE (format markdown)")
    print("=" * 80)
    print()
    print("| Pattern | Date Réf | Impact (pips) | N Events | Statut |")
    print("|---------|----------|---------------|----------|---------|")
    
    for pattern in TARGET_PATTERNS:
        if pattern in reference_cases:
            ref = reference_cases[pattern]
            status = "✅ Validé" if ref["status"] == "validated" else "⏳ À valider"
            print(f"| {pattern:<20s} | {ref['date']} | {ref['impact_real']:>6.1f} | "
                  f"{ref['n_events']:>8d} | {status} |")
        else:
            print(f"| {pattern:<20s} | - | - | - | ❌ Manquant |")
    
    # Sauvegarde
    print(f"\n" + "=" * 80)
    print("SAUVEGARDE RÉSULTATS")
    print("=" * 80)
    
    output = {
        "metadata": {
            "source_file": str(INPUT_FILE),
            "selection_criteria": {
                "min_events": 2,
                "impact_percentile": "50-75",
                "priority_validated": True
            },
            "target_patterns": TARGET_PATTERNS
        },
        "reference_cases": reference_cases,
        "validated_cases": VALIDATED_CASES
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Cas référence sauvegardés : {OUTPUT_FILE}")
    print(f"   Taille : {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    
    # Validation critique
    print(f"\n" + "=" * 80)
    print("VALIDATION CRITIQUE")
    print("=" * 80)
    
    # Vérifier 11 septembre présent
    if "DoubleWave_Overlap" in reference_cases:
        ref_11sept = reference_cases["DoubleWave_Overlap"]
        if ref_11sept["date"] == "2025-09-11":
            print(f"\n✅ 11 septembre PRÉSENT comme référence DoubleWave_Overlap")
            print(f"   Impact : {ref_11sept['impact_real']:.1f} pips")
            print(f"   Events : {ref_11sept['n_events']}")
            print(f"   Statut : {ref_11sept['status']}")
        else:
            print(f"\n⚠️ 11 septembre NON sélectionné comme référence")
            print(f"   Date sélectionnée : {ref_11sept['date']}")
    else:
        print(f"\n❌ Aucune référence DoubleWave_Overlap")
    
    # Minimum requis
    min_required = 2  # Au moins 2 patterns avec référence
    if len(reference_cases) >= min_required:
        print(f"\n✅ Minimum requis atteint : {len(reference_cases)} >= {min_required}")
    else:
        print(f"\n⚠️ Minimum requis NON atteint : {len(reference_cases)} < {min_required}")
        print(f"   Il faudra plus de données ou ajuster critères sélection")
    
    print("\n" + "=" * 80)
    print("✅ ÉTAPE 3 TERMINÉE")
    print("=" * 80)
    
    print(f"\n🎯 PROCHAINE ÉTAPE : Calculer amplifications idéales (Étape 4)")
    print(f"   Script : calculate_ideal_amplifications.py")
    print(f"   Input : reference_cases.json")
    print(f"   Output : reference_cases_with_amplifications.json")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
