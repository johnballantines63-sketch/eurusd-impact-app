#!/usr/bin/env python3
"""
CLASSIFICATION PATTERNS - SESSION 130 ÉTAPE 2
==============================================

Charge movements_2023_2025_complete.json et classi

fie patterns en groupes :
- DoubleWave_Overlap
- DoubleWave_Cascade  
- SingleWave_Fort
- SingleWave_Intermediate
- ZigZag
- Other

Output : patterns_classified.json avec groupes structurés

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

# Chemins
INPUT_FILE = Path(__file__).parent / "movements_2023_2025_complete.json"
OUTPUT_FILE = Path(__file__).parent / "patterns_classified.json"


def classify_movements(movements: List[Dict]) -> Dict:
    """
    Classifie mouvements par pattern.
    
    Returns:
        Dict avec clés = pattern types, valeurs = listes mouvements
    """
    classified = defaultdict(list)
    
    for movement in movements:
        pattern = movement["pattern"]
        classified[pattern].append(movement)
    
    return dict(classified)


def compute_statistics(classified: Dict) -> Dict:
    """Calcule statistiques par pattern"""
    
    stats = {}
    
    for pattern, movements in classified.items():
        if not movements:
            continue
        
        impacts = [m["impact_pips"] for m in movements]
        n_events_list = [m["n_events"] for m in movements]
        
        # Stats impact
        avg_impact = sum(impacts) / len(impacts)
        min_impact = min(impacts)
        max_impact = max(impacts)
        
        # Stats events
        avg_events = sum(n_events_list) / len(n_events_list)
        with_events = sum(1 for n in n_events_list if n > 0)
        pct_with_events = 100.0 * with_events / len(movements)
        
        stats[pattern] = {
            "count": len(movements),
            "avg_impact_pips": round(avg_impact, 1),
            "min_impact_pips": round(min_impact, 1),
            "max_impact_pips": round(max_impact, 1),
            "avg_events": round(avg_events, 1),
            "pct_with_events": round(pct_with_events, 1)
        }
    
    return stats


def identify_validable_cases(classified: Dict) -> Dict:
    """
    Identifie cas validables (avec événements causaux).
    
    Un cas est validable si :
    - Au moins 1 événement causal (n_events > 0)
    - Pattern identifié (pas "unknown" ou "insufficient_data")
    """
    validable = {}
    
    target_patterns = [
        "DoubleWave_Overlap",
        "DoubleWave_Cascade",
        "SingleWave_Fort",
        "SingleWave_Intermediate",
        "ZigZag"
    ]
    
    for pattern in target_patterns:
        if pattern not in classified:
            validable[pattern] = []
            continue
        
        # Filtrer mouvements avec events
        with_events = [m for m in classified[pattern] if m["n_events"] > 0]
        validable[pattern] = with_events
    
    return validable


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("CLASSIFICATION PATTERNS - ÉTAPE 2")
    print("=" * 80)
    
    # Charger movements
    print(f"\n📂 Chargement : {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        print(f"❌ Fichier introuvable : {INPUT_FILE}")
        print("   Lancez d'abord scan_by_month.py")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    movements = data["movements"]
    print(f"✅ {len(movements)} mouvements chargés")
    
    # Classification
    print(f"\n🔍 Classification par pattern...")
    classified = classify_movements(movements)
    
    print(f"✅ {len(classified)} types de patterns identifiés")
    
    # Statistiques
    print(f"\n📊 Calcul statistiques...")
    stats = compute_statistics(classified)
    
    # Cas validables
    print(f"\n🎯 Identification cas validables...")
    validable = identify_validable_cases(classified)
    
    # Affichage résultats
    print(f"\n" + "=" * 80)
    print("RÉSULTATS CLASSIFICATION")
    print("=" * 80)
    
    print(f"\n📈 Distribution complète :")
    print(f"\n{'Pattern':<30s} {'Total':>6s} {'Valid':>6s} {'Avg Impact':>12s} {'Events':>8s}")
    print("-" * 80)
    
    for pattern in sorted(classified.keys(), key=lambda x: -len(classified[x])):
        count = len(classified[pattern])
        valid_count = len(validable.get(pattern, []))
        st = stats[pattern]
        
        print(f"{pattern:<30s} {count:>6d} {valid_count:>6d} "
              f"{st['avg_impact_pips']:>12.1f} {st['avg_events']:>8.1f}")
    
    # Focus patterns cibles
    print(f"\n" + "=" * 80)
    print("PATTERNS CIBLES (pour calibration)")
    print("=" * 80)
    
    target_patterns = [
        "DoubleWave_Overlap",
        "DoubleWave_Cascade",
        "SingleWave_Fort",
        "SingleWave_Intermediate",
        "ZigZag"
    ]
    
    for pattern in target_patterns:
        if pattern in classified:
            total = len(classified[pattern])
            valid = len(validable[pattern])
            st = stats[pattern]
            
            print(f"\n✅ {pattern}")
            print(f"   Total mouvements : {total}")
            print(f"   Avec events (validables) : {valid} ({100.0*valid/total:.1f}%)")
            print(f"   Impact moyen : {st['avg_impact_pips']:.1f} pips")
            print(f"   Events moyen : {st['avg_events']:.1f}")
            
            # Top 3 cas si disponibles
            if validable[pattern]:
                print(f"   Top 3 cas :")
                sorted_cases = sorted(validable[pattern], 
                                     key=lambda x: -x["impact_pips"])[:3]
                for i, case in enumerate(sorted_cases, 1):
                    print(f"      {i}. {case['date']} - {case['impact_pips']:.1f} pips "
                          f"({case['n_events']} events)")
        else:
            print(f"\n❌ {pattern} : Aucun cas détecté")
    
    # Cas non validables
    print(f"\n" + "=" * 80)
    print("CAS NON VALIDABLES (patterns techniques)")
    print("=" * 80)
    
    for pattern in classified:
        total = len(classified[pattern])
        with_events = sum(1 for m in classified[pattern] if m["n_events"] > 0)
        without_events = total - with_events
        
        if without_events > 0:
            print(f"\n{pattern}")
            print(f"   Sans events : {without_events}/{total} ({100.0*without_events/total:.1f}%)")
            print(f"   Impact moyen sans events : "
                  f"{sum(m['impact_pips'] for m in classified[pattern] if m['n_events'] == 0) / max(without_events, 1):.1f} pips")
    
    # Sauvegarde
    print(f"\n" + "=" * 80)
    print("SAUVEGARDE RÉSULTATS")
    print("=" * 80)
    
    output = {
        "metadata": {
            "source_file": str(INPUT_FILE),
            "classification_date": data["metadata"]["scan_date"],
            "total_movements": len(movements)
        },
        "statistics": stats,
        "classified": classified,
        "validable_cases": validable
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Classification sauvegardée : {OUTPUT_FILE}")
    print(f"   Taille : {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    
    # Résumé validation
    total_validable = sum(len(v) for v in validable.values())
    print(f"\n📊 RÉSUMÉ")
    print(f"   Mouvements totaux : {len(movements)}")
    print(f"   Cas validables (avec events) : {total_validable}")
    print(f"   Taux validation : {100.0 * total_validable / len(movements):.1f}%")
    
    # Validation cas connus
    print(f"\n" + "=" * 80)
    print("VALIDATION CAS CONNUS")
    print("=" * 80)
    
    known_dates = {
        "2025-09-11": "DoubleWave",
        "2025-08-01": "SingleWave",
        "2025-09-05": "ZigZag"
    }
    
    for date_str, expected in known_dates.items():
        found = None
        actual_pattern = None
        
        for pattern, cases in classified.items():
            for case in cases:
                if case["date"] == date_str:
                    found = case
                    actual_pattern = pattern
                    break
            if found:
                break
        
        if found:
            match = expected in actual_pattern
            status = "✅" if match else "⚠️"
            print(f"\n{status} {date_str}")
            print(f"   Pattern : {actual_pattern} (attendu: {expected})")
            print(f"   Impact : {found['impact_pips']:.1f} pips")
            print(f"   Events : {found['n_events']}")
        else:
            print(f"\n❌ {date_str} NON trouvé")
    
    print("\n" + "=" * 80)
    print("✅ CLASSIFICATION TERMINÉE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
