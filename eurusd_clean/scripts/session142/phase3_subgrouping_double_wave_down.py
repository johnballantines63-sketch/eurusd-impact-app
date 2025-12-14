"""
SESSION 142 - PHASE 3 : SUB-GROUPING DOUBLE_WAVE_DOWN 300-400
=============================================================

Objectif : Tester sub-grouping pour DOUBLE_WAVE_DOWN 300-400
(Médiane n'a pas fonctionné : +1.30 pips)

Méthodologie :
1. Tester Option A : Sub-grouping par num_events
2. Tester Option B : Sub-grouping par score fin
3. Calculer MAE par sous-groupe (min 3 cas/sous-groupe)
4. MAE global pondéré
5. Retenir meilleure option

Date : 16 novembre 2025
Auteur : André Valentin avec Claude
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_FILE = Path(__file__).parent.parent / "session137" / "step3_movements_with_patterns_v2.csv"
OUTPUT_DIR = Path(__file__).parent
OUTPUT_RESULTS = OUTPUT_DIR / "phase3_subgrouping_results.json"

PATTERN = "DOUBLE_WAVE_DOWN"
SCORE_MIN = 300
SCORE_MAX = 400
MIN_CASES_PER_SUBGROUP = 3  # Minimum statistiquement robuste

# ============================================================================
# FONCTIONS
# ============================================================================

def load_movements() -> pd.DataFrame:
    """Charge les mouvements avec patterns."""
    print(f"📂 Chargement : {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'], utc=True)
    print(f"✅ {len(df)} mouvements chargés")
    return df

def filter_group(df: pd.DataFrame) -> pd.DataFrame:
    """Filtre le groupe DOUBLE_WAVE_DOWN 300-400."""
    filtered = df[
        (df['pattern_type'] == PATTERN) &
        (df['total_score'] >= SCORE_MIN) &
        (df['total_score'] < SCORE_MAX)
    ].copy()
    
    print(f"\n🎯 Groupe {PATTERN} {SCORE_MIN}-{SCORE_MAX}:")
    print(f"   {len(filtered)} cas trouvés")
    
    return filtered

def assign_subgroup_by_events(num_events: int) -> str:
    """Assigne sous-groupe selon num_events."""
    if num_events < 15:
        return "events_<15"
    elif num_events < 20:
        return "events_15-19"
    elif num_events < 25:
        return "events_20-24"
    else:
        return "events_25+"

def assign_subgroup_by_score(score: float) -> str:
    """Assigne sous-groupe selon score fin."""
    if score < 320:
        return "score_300-320"
    elif score < 340:
        return "score_320-340"
    elif score < 360:
        return "score_340-360"
    else:
        return "score_360-400"

def perform_loocv_subgroup(group_df: pd.DataFrame, subgroup_col: str) -> Dict:
    """Effectue LOO-CV avec sub-grouping."""
    n = len(group_df)
    predictions = []
    actuals = []
    errors = []
    subgroup_info = []
    
    for i in range(n):
        # Retirer cas i
        train_df = group_df.drop(group_df.index[i])
        test_row = group_df.iloc[i]
        
        # Identifier sous-groupe du cas test
        test_subgroup = test_row[subgroup_col]
        
        # Filtrer train par sous-groupe
        train_subgroup = train_df[train_df[subgroup_col] == test_subgroup]
        
        if len(train_subgroup) >= MIN_CASES_PER_SUBGROUP:
            # Prédiction = moyenne du sous-groupe
            prediction = float(train_subgroup['impact_pips'].mean())
        else:
            # Fallback : moyenne globale (sous-groupe trop petit)
            prediction = float(train_df['impact_pips'].mean())
        
        actual = float(test_row['impact_pips'])
        error = abs(actual - prediction)
        
        predictions.append(prediction)
        actuals.append(actual)
        errors.append(error)
        subgroup_info.append({
            "subgroup": test_subgroup,
            "subgroup_size": len(train_subgroup),
            "used_fallback": len(train_subgroup) < MIN_CASES_PER_SUBGROUP
        })
    
    mae = float(np.mean(errors))
    
    return {
        "mae": mae,
        "predictions": predictions,
        "actuals": actuals,
        "errors": errors,
        "subgroup_info": subgroup_info
    }

def test_subgrouping_by_events(group_df: pd.DataFrame) -> Dict:
    """Teste sub-grouping par num_events."""
    print("\n" + "=" * 80)
    print("OPTION A : SUB-GROUPING PAR NUM_EVENTS")
    print("=" * 80)
    
    # Assigner sous-groupes
    group_df = group_df.copy()
    group_df['subgroup_events'] = group_df['num_events'].apply(assign_subgroup_by_events)
    
    # Afficher distribution
    print("\n📊 Distribution sous-groupes :")
    subgroup_counts = group_df['subgroup_events'].value_counts().sort_index()
    for subgroup, count in subgroup_counts.items():
        print(f"   {subgroup:20s}: {count:2d} cas")
    
    # Vérifier taille minimale
    min_size = subgroup_counts.min()
    if min_size < MIN_CASES_PER_SUBGROUP:
        print(f"\n⚠️  ATTENTION : Sous-groupe minimum = {min_size} cas (< {MIN_CASES_PER_SUBGROUP})")
        print(f"   Risque sur-ajustement élevé")
    
    # LOO-CV
    results = perform_loocv_subgroup(group_df, 'subgroup_events')
    
    print(f"\n📊 Résultats LOO-CV :")
    print(f"   MAE : {results['mae']:.2f} pips")
    
    # Analyser utilisation fallback
    fallback_count = sum(1 for info in results['subgroup_info'] if info['used_fallback'])
    print(f"   Utilisation fallback : {fallback_count}/{len(group_df)} cas")
    
    return {
        "method": "by_events",
        "subgroup_distribution": subgroup_counts.to_dict(),
        "results": results
    }

def test_subgrouping_by_score(group_df: pd.DataFrame) -> Dict:
    """Teste sub-grouping par score fin."""
    print("\n" + "=" * 80)
    print("OPTION B : SUB-GROUPING PAR SCORE FIN")
    print("=" * 80)
    
    # Assigner sous-groupes
    group_df = group_df.copy()
    group_df['subgroup_score'] = group_df['total_score'].apply(assign_subgroup_by_score)
    
    # Afficher distribution
    print("\n📊 Distribution sous-groupes :")
    subgroup_counts = group_df['subgroup_score'].value_counts().sort_index()
    for subgroup, count in subgroup_counts.items():
        print(f"   {subgroup:20s}: {count:2d} cas")
        scores = group_df[group_df['subgroup_score'] == subgroup]['total_score']
        print(f"      Score range : {scores.min():.1f} → {scores.max():.1f}")
    
    # Vérifier taille minimale
    min_size = subgroup_counts.min()
    if min_size < MIN_CASES_PER_SUBGROUP:
        print(f"\n⚠️  ATTENTION : Sous-groupe minimum = {min_size} cas (< {MIN_CASES_PER_SUBGROUP})")
        print(f"   Risque sur-ajustement élevé")
    
    # LOO-CV
    results = perform_loocv_subgroup(group_df, 'subgroup_score')
    
    print(f"\n📊 Résultats LOO-CV :")
    print(f"   MAE : {results['mae']:.2f} pips")
    
    # Analyser utilisation fallback
    fallback_count = sum(1 for info in results['subgroup_info'] if info['used_fallback'])
    print(f"   Utilisation fallback : {fallback_count}/{len(group_df)} cas")
    
    return {
        "method": "by_score",
        "subgroup_distribution": subgroup_counts.to_dict(),
        "results": results
    }

def compare_subgrouping_options(options: List[Dict], baseline_mae: float) -> Dict:
    """Compare les options de sub-grouping."""
    print("\n" + "=" * 80)
    print("COMPARAISON OPTIONS")
    print("=" * 80)
    
    print(f"\n📊 Baseline (moyenne) : {baseline_mae:.2f} pips")
    
    best_option = None
    best_mae = float('inf')
    
    for option in options:
        mae = option['results']['mae']
        gain = mae - baseline_mae  # Négatif = amélioration
        
        print(f"\n{option['method']:20s}:")
        print(f"   MAE : {mae:.2f} pips")
        print(f"   Gain : {gain:+.2f} pips ({gain/baseline_mae*100:+.1f}%)")
        
        if mae < best_mae:
            best_mae = mae
            best_option = option
    
    if best_option:
        best_gain = best_option['results']['mae'] - baseline_mae
        print(f"\n🏆 Meilleure option : {best_option['method']}")
        print(f"   MAE : {best_mae:.2f} pips")
        print(f"   Gain : {best_gain:+.2f} pips")
        
        if best_gain <= -2.0:
            decision = "ADOPTER SUB-GROUPING"
            status = "✅"
        else:
            decision = "GARDER MOYENNE"
            status = "⚠️"
        
        return {
            "best_option": best_option['method'],
            "best_mae": best_mae,
            "best_gain": best_gain,
            "decision": decision,
            "status": status,
            "baseline_mae": baseline_mae,
            "all_options": options
        }
    
    return None

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("SESSION 142 - PHASE 3 : SUB-GROUPING DOUBLE_WAVE_DOWN 300-400")
    print("=" * 80)
    
    # 1. Charger données
    df = load_movements()
    
    # 2. Filtrer groupe
    group_df = filter_group(df)
    
    if len(group_df) < MIN_CASES_PER_SUBGROUP * 2:
        print(f"\n❌ Taille échantillon insuffisante pour sub-grouping")
        print(f"   Minimum requis : {MIN_CASES_PER_SUBGROUP * 2} cas")
        print(f"   Disponible : {len(group_df)} cas")
        print(f"   ⚠️  Sub-grouping NON RECOMMANDÉ (risque sur-ajustement)")
        return
    
    # Baseline : MAE avec moyenne (26.66 pips d'après Phase 1)
    baseline_mae = 26.66
    
    print(f"\n📊 Baseline (moyenne) : {baseline_mae:.2f} pips")
    
    # 3. Tester Option A : Sub-grouping par num_events
    option_a = test_subgrouping_by_events(group_df)
    
    # 4. Tester Option B : Sub-grouping par score fin
    option_b = test_subgrouping_by_score(group_df)
    
    # 5. Comparer options
    comparison = compare_subgrouping_options([option_a, option_b], baseline_mae)
    
    # 6. Sauvegarder résultats
    results_full = {
        "baseline_mae": baseline_mae,
        "comparison": comparison,
        "options": {
            "by_events": option_a,
            "by_score": option_b
        }
    }
    
    with open(OUTPUT_RESULTS, 'w') as f:
        json.dump(results_full, f, indent=2, default=str)
    print(f"\n✅ Résultats sauvegardés : {OUTPUT_RESULTS}")
    
    # 7. Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION PHASE 3")
    print("=" * 80)
    
    if comparison:
        if comparison['status'] == "✅":
            print(f"\n✅ SUCCÈS : Sub-grouping améliore MAE de {abs(comparison['best_gain']):.2f} pips")
            print(f"   MAE optimisé : {comparison['best_mae']:.2f} pips")
            print(f"   Méthode : {comparison['best_option']}")
            print(f"   Objectif : 22-23 pips")
            if comparison['best_mae'] <= 23:
                print(f"   🎉 OBJECTIF ATTEINT !")
        else:
            print(f"\n⚠️  Sub-grouping n'améliore pas suffisamment")
            print(f"   Gain : {comparison['best_gain']:+.2f} pips")
            print(f"   💡 Considérer accepter MAE actuel (26.66 pips)")
            print(f"   💡 Ou chercher autres approches (pondération, etc.)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

