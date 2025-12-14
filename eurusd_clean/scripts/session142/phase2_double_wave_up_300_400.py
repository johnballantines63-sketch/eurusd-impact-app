"""
SESSION 142 - PHASE 2 : DOUBLE_WAVE_UP 300-400
===============================================

Objectif : Optimiser groupe DOUBLE_WAVE_UP 300-400 (MAE 29.79 → 23-25 pips)

Méthodologie :
1. Analyser variance groupe (CV, outliers, distribution)
2. Test LOO-CV avec médiane vs moyenne
3. Décision : Adopter médiane si gain >= -2 pips

Date : 16 novembre 2025
Auteur : André Valentin avec Claude
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_FILE = Path(__file__).parent.parent / "session137" / "step3_movements_with_patterns_v2.csv"
OUTPUT_DIR = Path(__file__).parent
OUTPUT_VARIANCE = OUTPUT_DIR / "phase2_variance_double_wave_up.json"
OUTPUT_COMPARISON = OUTPUT_DIR / "phase2_median_vs_mean_double_wave_up.json"
OUTPUT_DETAILED = OUTPUT_DIR / "phase2_detailed_results_double_wave_up.csv"

PATTERN = "DOUBLE_WAVE_UP"
SCORE_MIN = 300
SCORE_MAX = 400
THRESHOLD_GAIN = -2.0  # Seuil minimum pour adopter médiane (pips)

# ============================================================================
# FONCTIONS (réutilisées de Phase 1)
# ============================================================================

def load_movements() -> pd.DataFrame:
    """Charge les mouvements avec patterns."""
    print(f"📂 Chargement : {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'], utc=True)
    print(f"✅ {len(df)} mouvements chargés")
    return df

def filter_group(df: pd.DataFrame) -> pd.DataFrame:
    """Filtre le groupe DOUBLE_WAVE_UP 300-400."""
    filtered = df[
        (df['pattern_type'] == PATTERN) &
        (df['total_score'] >= SCORE_MIN) &
        (df['total_score'] < SCORE_MAX)
    ].copy()
    
    print(f"\n🎯 Groupe {PATTERN} {SCORE_MIN}-{SCORE_MAX}:")
    print(f"   {len(filtered)} cas trouvés")
    
    return filtered

def analyze_variance(group_df: pd.DataFrame) -> Dict:
    """Analyse la variance du groupe."""
    impacts = group_df['impact_pips'].values
    
    # Statistiques de base
    mean_impact = float(np.mean(impacts))
    median_impact = float(np.median(impacts))
    std_impact = float(np.std(impacts))
    min_impact = float(np.min(impacts))
    max_impact = float(np.max(impacts))
    
    # Quartiles
    q1_impact = float(np.percentile(impacts, 25))
    q3_impact = float(np.percentile(impacts, 75))
    iqr_impact = q3_impact - q1_impact
    
    # Coefficient de variation
    cv_impact = (std_impact / mean_impact * 100) if mean_impact > 0 else 0.0
    
    # Détection outliers (méthode IQR)
    outlier_threshold_high = q3_impact + 1.5 * iqr_impact
    outliers = group_df[group_df['impact_pips'] > outlier_threshold_high].copy()
    
    # Corrélation impact vs score
    correlation = float(np.corrcoef(group_df['impact_pips'], group_df['total_score'])[0, 1])
    
    # Distribution num_events
    events_dist = group_df['num_events'].value_counts().to_dict()
    events_dist = {str(k): int(v) for k, v in events_dist.items()}
    
    variance_analysis = {
        "count": len(group_df),
        "mean_impact": mean_impact,
        "median_impact": median_impact,
        "std_impact": std_impact,
        "min_impact": min_impact,
        "max_impact": max_impact,
        "q1_impact": q1_impact,
        "q3_impact": q3_impact,
        "iqr_impact": iqr_impact,
        "cv_impact": cv_impact,
        "num_outliers": len(outliers),
        "outliers": [
            {
                "movement_datetime": str(row['movement_datetime']),
                "impact_pips": float(row['impact_pips']),
                "total_score": float(row['total_score']),
                "num_events": int(row['num_events'])
            }
            for _, row in outliers.iterrows()
        ],
        "mean_score": float(group_df['total_score'].mean()),
        "mean_num_events": float(group_df['num_events'].mean()),
        "correlation_impact_score": correlation,
        "events_distribution": events_dist
    }
    
    return variance_analysis

def perform_loocv_mean(group_df: pd.DataFrame) -> Dict:
    """Effectue LOO-CV avec moyenne."""
    n = len(group_df)
    predictions = []
    actuals = []
    errors = []
    
    for i in range(n):
        # Retirer cas i
        train_df = group_df.drop(group_df.index[i])
        test_row = group_df.iloc[i]
        
        # Prédiction = moyenne des n-1 cas restants
        prediction = float(train_df['impact_pips'].mean())
        actual = float(test_row['impact_pips'])
        error = abs(actual - prediction)
        
        predictions.append(prediction)
        actuals.append(actual)
        errors.append(error)
    
    mae = float(np.mean(errors))
    
    return {
        "mae": mae,
        "predictions": predictions,
        "actuals": actuals,
        "errors": errors
    }

def perform_loocv_median(group_df: pd.DataFrame) -> Dict:
    """Effectue LOO-CV avec médiane."""
    n = len(group_df)
    predictions = []
    actuals = []
    errors = []
    
    for i in range(n):
        # Retirer cas i
        train_df = group_df.drop(group_df.index[i])
        test_row = group_df.iloc[i]
        
        # Prédiction = médiane des n-1 cas restants
        prediction = float(train_df['impact_pips'].median())
        actual = float(test_row['impact_pips'])
        error = abs(actual - prediction)
        
        predictions.append(prediction)
        actuals.append(actual)
        errors.append(error)
    
    mae = float(np.mean(errors))
    
    return {
        "mae": mae,
        "predictions": predictions,
        "actuals": actuals,
        "errors": errors
    }

def compare_methods(mean_results: Dict, median_results: Dict) -> Dict:
    """Compare moyenne vs médiane."""
    mae_mean = mean_results['mae']
    mae_median = median_results['mae']
    gain = mae_median - mae_mean  # Négatif = amélioration
    
    decision = "ADOPTER MÉDIANE" if gain <= THRESHOLD_GAIN else "GARDER MOYENNE"
    status = "✅" if gain <= THRESHOLD_GAIN else "⚠️"
    
    # Analyser cas améliorés/dégradés
    mean_errors = mean_results['errors']
    median_errors = median_results['errors']
    
    improved = [i for i in range(len(mean_errors)) if median_errors[i] < mean_errors[i]]
    degraded = [i for i in range(len(mean_errors)) if median_errors[i] > mean_errors[i]]
    
    if improved:
        avg_improvement = np.mean([mean_errors[i] - median_errors[i] for i in improved])
    else:
        avg_improvement = 0.0
    
    if degraded:
        avg_degradation = np.mean([median_errors[i] - mean_errors[i] for i in degraded])
    else:
        avg_degradation = 0.0
    
    comparison = {
        "mae_mean": mae_mean,
        "mae_median": mae_median,
        "gain_mae": float(gain),
        "gain_percent": float((gain / mae_mean) * 100) if mae_mean > 0 else 0.0,
        "decision": decision,
        "status": status,
        "threshold": THRESHOLD_GAIN,
        "num_improved": len(improved),
        "num_degraded": len(degraded),
        "avg_improvement": float(avg_improvement) if improved else 0.0,
        "avg_degradation": float(avg_degradation) if degraded else 0.0
    }
    
    return comparison

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("SESSION 142 - PHASE 2 : DOUBLE_WAVE_UP 300-400")
    print("=" * 80)
    
    # 1. Charger données
    df = load_movements()
    
    # 2. Filtrer groupe
    group_df = filter_group(df)
    
    if len(group_df) == 0:
        print("❌ Aucun cas trouvé pour ce groupe")
        return
    
    # 3. Analyser variance
    print("\n" + "=" * 80)
    print("ÉTAPE 1 : ANALYSE VARIANCE")
    print("=" * 80)
    
    variance_analysis = analyze_variance(group_df)
    
    print(f"\n📊 Statistiques impact :")
    print(f"   Moyenne  : {variance_analysis['mean_impact']:.2f} pips")
    print(f"   Médiane  : {variance_analysis['median_impact']:.2f} pips")
    print(f"   Écart    : {variance_analysis['mean_impact'] - variance_analysis['median_impact']:.2f} pips")
    print(f"   Std      : {variance_analysis['std_impact']:.2f} pips")
    print(f"   CV       : {variance_analysis['cv_impact']:.1f}%")
    print(f"   Range    : {variance_analysis['min_impact']:.2f} → {variance_analysis['max_impact']:.2f} pips")
    print(f"   IQR      : {variance_analysis['iqr_impact']:.2f} pips")
    print(f"\n🔍 Outliers détectés : {variance_analysis['num_outliers']}")
    for outlier in variance_analysis['outliers']:
        print(f"   - {outlier['movement_datetime']}: {outlier['impact_pips']:.2f} pips "
              f"(score={outlier['total_score']:.1f}, events={outlier['num_events']})")
    print(f"\n📈 Corrélation impact ↔ score : {variance_analysis['correlation_impact_score']:.3f}")
    
    # Sauvegarder analyse variance
    with open(OUTPUT_VARIANCE, 'w') as f:
        json.dump(variance_analysis, f, indent=2)
    print(f"\n✅ Analyse variance sauvegardée : {OUTPUT_VARIANCE}")
    
    # 4. Test LOO-CV avec moyenne
    print("\n" + "=" * 80)
    print("ÉTAPE 2 : TEST LOO-CV - MOYENNE")
    print("=" * 80)
    
    mean_results = perform_loocv_mean(group_df)
    print(f"   MAE moyenne : {mean_results['mae']:.2f} pips")
    
    # 5. Test LOO-CV avec médiane
    print("\n" + "=" * 80)
    print("ÉTAPE 3 : TEST LOO-CV - MÉDIANE")
    print("=" * 80)
    
    median_results = perform_loocv_median(group_df)
    print(f"   MAE médiane : {median_results['mae']:.2f} pips")
    
    # 6. Comparer méthodes
    print("\n" + "=" * 80)
    print("ÉTAPE 4 : COMPARAISON MOYENNE vs MÉDIANE")
    print("=" * 80)
    
    comparison = compare_methods(mean_results, median_results)
    
    print(f"\n📊 Résultats :")
    print(f"   MAE moyenne : {comparison['mae_mean']:.2f} pips")
    print(f"   MAE médiane : {comparison['mae_median']:.2f} pips")
    print(f"   Gain       : {comparison['gain_mae']:+.2f} pips ({comparison['gain_percent']:+.1f}%)")
    print(f"\n🎯 Décision : {comparison['decision']} {comparison['status']}")
    print(f"   Seuil      : {comparison['threshold']:.1f} pips")
    print(f"\n📈 Analyse détaillée :")
    print(f"   Cas améliorés : {comparison['num_improved']}/{len(group_df)} "
          f"({100.0*comparison['num_improved']/len(group_df):.1f}%)")
    if comparison['num_improved'] > 0:
        print(f"   Gain moyen    : {comparison['avg_improvement']:.2f} pips")
    print(f"   Cas dégradés : {comparison['num_degraded']}/{len(group_df)} "
          f"({100.0*comparison['num_degraded']/len(group_df):.1f}%)")
    if comparison['num_degraded'] > 0:
        print(f"   Perte moyenne : {comparison['avg_degradation']:.2f} pips")
    
    # Sauvegarder comparaison
    comparison_full = {
        "variance_analysis": variance_analysis,
        "mean_results": mean_results,
        "median_results": median_results,
        "comparison": comparison
    }
    
    with open(OUTPUT_COMPARISON, 'w') as f:
        json.dump(comparison_full, f, indent=2)
    print(f"\n✅ Comparaison sauvegardée : {OUTPUT_COMPARISON}")
    
    # 7. Export détaillé CSV
    detailed_df = pd.DataFrame({
        'movement_datetime': group_df['movement_datetime'],
        'impact_pips': group_df['impact_pips'],
        'total_score': group_df['total_score'],
        'num_events': group_df['num_events'],
        'prediction_mean': mean_results['predictions'],
        'prediction_median': median_results['predictions'],
        'error_mean': mean_results['errors'],
        'error_median': median_results['errors'],
        'improvement': [median_results['errors'][i] - mean_results['errors'][i] 
                       for i in range(len(mean_results['errors']))]
    })
    
    detailed_df.to_csv(OUTPUT_DETAILED, index=False)
    print(f"✅ Résultats détaillés sauvegardés : {OUTPUT_DETAILED}")
    
    # 8. Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION PHASE 2")
    print("=" * 80)
    
    if comparison['gain_mae'] <= THRESHOLD_GAIN:
        print(f"\n✅ SUCCÈS : Médiane améliore MAE de {abs(comparison['gain_mae']):.2f} pips")
        print(f"   MAE optimisé : {comparison['mae_median']:.2f} pips")
        print(f"   Objectif : 23-25 pips")
        if comparison['mae_median'] <= 25:
            print(f"   🎉 OBJECTIF ATTEINT !")
        else:
            print(f"   ⚠️  Objectif proche mais pas encore atteint")
    else:
        print(f"\n⚠️  Médiane n'améliore pas suffisamment (gain {comparison['gain_mae']:.2f} pips)")
        print(f"   ⚠️  ATTENTION : Taille échantillon très petite (n={len(group_df)})")
        print(f"   ⚠️  Sub-grouping NON RECOMMANDÉ (risque sur-ajustement)")
        print(f"   💡 Considérer accepter MAE actuel ou chercher autres approches")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

