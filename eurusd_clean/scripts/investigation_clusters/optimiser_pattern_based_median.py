#!/usr/bin/env python3
"""
OPTIMISATION PATTERN-BASED - IDENTIFIER GROUPES POUR MÉDIANE
============================================================

Identifie les groupes pattern-based qui pourraient bénéficier de la médiane
au lieu de la moyenne, basé sur :
- Coefficient de variation (CV) > 30%
- Présence d'outliers
- Taille groupe >= 5

Auteur : André Valentin avec Claude
Date : 16 novembre 2025
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import sys

# Chemins
INPUT_FILE = Path(__file__).parent.parent / "session137" / "step3_movements_with_patterns_v2.csv"
OUTPUT_DIR = Path(__file__).parent / "optimisation_pattern_based"
OUTPUT_DIR.mkdir(exist_ok=True)

# Paramètres
CV_THRESHOLD = 0.30  # Coefficient de variation > 30%
MIN_GROUP_SIZE = 5  # Minimum 5 cas pour tester médiane
OUTLIER_THRESHOLD = 1.5  # IQR multiplier pour détecter outliers


def assign_score_range(score):
    """Assigne score à une range."""
    if score < 100:
        return "0-100"
    elif score < 200:
        return "100-200"
    elif score < 300:
        return "200-300"
    elif score < 400:
        return "300-400"
    elif score < 500:
        return "400-500"
    else:
        return "500+"


def detect_outliers(values):
    """Détecte outliers avec méthode IQR."""
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    
    if iqr == 0:
        return []
    
    lower_bound = q1 - OUTLIER_THRESHOLD * iqr
    upper_bound = q3 + OUTLIER_THRESHOLD * iqr
    
    outliers = []
    for i, val in enumerate(values):
        if val < lower_bound or val > upper_bound:
            outliers.append(i)
    
    return outliers


def perform_loocv_median(group_df: pd.DataFrame) -> Dict:
    """Effectue LOO-CV avec médiane."""
    n = len(group_df)
    if n < 2:
        return {"mae": 0.0, "errors": [], "count": n}
    
    errors = []
    for i in range(n):
        train_df = group_df.drop(group_df.index[i])
        test_row = group_df.iloc[i]
        
        prediction = float(train_df['impact_pips'].median())
        actual = float(test_row['impact_pips'])
        error = abs(actual - prediction)
        
        errors.append(error)
    
    mae = float(np.mean(errors)) if errors else 0.0
    
    return {
        "mae": mae,
        "errors": errors,
        "count": n
    }


def perform_loocv_mean(group_df: pd.DataFrame) -> Dict:
    """Effectue LOO-CV avec moyenne."""
    n = len(group_df)
    if n < 2:
        return {"mae": 0.0, "errors": [], "count": n}
    
    errors = []
    for i in range(n):
        train_df = group_df.drop(group_df.index[i])
        test_row = group_df.iloc[i]
        
        prediction = float(train_df['impact_pips'].mean())
        actual = float(test_row['impact_pips'])
        error = abs(actual - prediction)
        
        errors.append(error)
    
    mae = float(np.mean(errors)) if errors else 0.0
    
    return {
        "mae": mae,
        "errors": errors,
        "count": n
    }


def analyze_group(group_df: pd.DataFrame, pattern: str, score_range: str) -> Dict:
    """Analyse un groupe pour déterminer si médiane serait meilleure."""
    n = len(group_df)
    
    if n < MIN_GROUP_SIZE:
        return {
            'pattern': pattern,
            'score_range': score_range,
            'count': n,
            'recommendation': 'skip',
            'reason': f'Taille insuffisante (n={n} < {MIN_GROUP_SIZE})'
        }
    
    impacts = group_df['impact_pips'].values
    
    # Statistiques
    mean_impact = float(np.mean(impacts))
    median_impact = float(np.median(impacts))
    std_impact = float(np.std(impacts))
    cv = std_impact / mean_impact if mean_impact > 0 else 0
    
    # Détecter outliers
    outliers = detect_outliers(impacts)
    n_outliers = len(outliers)
    outlier_pct = (n_outliers / n) * 100
    
    # LOO-CV moyenne
    loocv_mean = perform_loocv_mean(group_df)
    mae_mean = loocv_mean['mae']
    
    # LOO-CV médiane
    loocv_median = perform_loocv_median(group_df)
    mae_median = loocv_median['mae']
    
    # Décision
    gain = mae_mean - mae_median
    gain_pct = (gain / mae_mean * 100) if mae_mean > 0 else 0
    
    # Critères pour recommander médiane
    criteria_met = {
        'cv_high': cv > CV_THRESHOLD,
        'has_outliers': n_outliers > 0,
        'outlier_pct_high': outlier_pct > 10,
        'median_better': mae_median < mae_mean,
        'gain_significant': gain > 2.0  # Gain > 2 pips
    }
    
    should_use_median = (
        criteria_met['median_better'] and
        (criteria_met['cv_high'] or criteria_met['outlier_pct_high']) and
        criteria_met['gain_significant']
    )
    
    recommendation = 'median' if should_use_median else 'mean'
    
    return {
        'pattern': pattern,
        'score_range': score_range,
        'count': n,
        'mean_impact': mean_impact,
        'median_impact': median_impact,
        'std_impact': std_impact,
        'cv': cv,
        'n_outliers': n_outliers,
        'outlier_pct': outlier_pct,
        'mae_mean': mae_mean,
        'mae_median': mae_median,
        'gain_pips': gain,
        'gain_pct': gain_pct,
        'criteria_met': criteria_met,
        'recommendation': recommendation,
        'current_method': 'mean'  # Par défaut
    }


def main():
    print("="*80)
    print("OPTIMISATION PATTERN-BASED - IDENTIFIER GROUPES POUR MÉDIANE")
    print("="*80)
    print()
    
    # Charger données
    print("📂 Chargement données...")
    df = pd.read_csv(INPUT_FILE)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'])
    df['score_range'] = df['total_score'].apply(assign_score_range)
    
    print(f"✅ {len(df)} mouvements chargés")
    print()
    
    # Grouper par pattern + score_range
    print("🔬 Analyse groupes...")
    groups = df.groupby(['pattern_type', 'score_range'])
    
    results = []
    recommendations = []
    
    for (pattern, score_range), group_df in groups:
        result = analyze_group(group_df, pattern, score_range)
        results.append(result)
        
        if result['recommendation'] == 'median':
            recommendations.append(result)
    
    print(f"✅ {len(results)} groupes analysés")
    print(f"📊 {len(recommendations)} groupes recommandés pour médiane")
    print()
    
    # Afficher recommandations
    if recommendations:
        print("🎯 GROUPES RECOMMANDÉS POUR MÉDIANE :")
        print("-"*80)
        print(f"{'Pattern':<30s} {'Score Range':<12s} {'Count':<8s} {'MAE Mean':<12s} {'MAE Median':<12s} {'Gain':<10s}")
        print("-"*80)
        
        for rec in sorted(recommendations, key=lambda x: -x['gain_pips']):
            print(f"{rec['pattern']:<30s} {rec['score_range']:<12s} {rec['count']:<8d} "
                  f"{rec['mae_mean']:>10.2f} {rec['mae_median']:>10.2f} {rec['gain_pips']:>+8.2f} pips")
        
        print()
        
        # Détails par groupe
        print("📋 DÉTAILS PAR GROUPE :")
        print("-"*80)
        for rec in recommendations:
            print(f"\n{rec['pattern']} {rec['score_range']}:")
            print(f"  Taille : {rec['count']} cas")
            print(f"  CV : {rec['cv']:.1%} ({'Élevé' if rec['cv'] > CV_THRESHOLD else 'Normal'})")
            print(f"  Outliers : {rec['n_outliers']} ({rec['outlier_pct']:.1f}%)")
            print(f"  MAE moyenne : {rec['mae_mean']:.2f} pips")
            print(f"  MAE médiane : {rec['mae_median']:.2f} pips")
            print(f"  Gain : {rec['gain_pips']:+.2f} pips ({rec['gain_pct']:+.1f}%)")
    else:
        print("ℹ️  Aucun groupe recommandé pour médiane")
        print("   (Tous les groupes sont mieux prédits avec moyenne)")
    
    # Sauvegarder résultats
    output_data = {
        'analysis_date': pd.Timestamp.now().isoformat(),
        'parameters': {
            'cv_threshold': CV_THRESHOLD,
            'min_group_size': MIN_GROUP_SIZE,
            'outlier_threshold': OUTLIER_THRESHOLD
        },
        'summary': {
            'total_groups': len(results),
            'recommended_median': len(recommendations),
            'current_median_groups': sum(1 for r in results if r.get('current_method') == 'median')
        },
        'all_results': results,
        'recommendations': recommendations
    }
    
    output_file = OUTPUT_DIR / "optimisation_median_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Résultats sauvegardés : {output_file}")
    
    # CSV recommandations
    if recommendations:
        df_rec = pd.DataFrame(recommendations)
        csv_file = OUTPUT_DIR / "recommendations_median.csv"
        df_rec.to_csv(csv_file, index=False)
        print(f"✅ Recommandations CSV : {csv_file}")
    
    print(f"\n{'='*80}")
    print("✅ OPTIMISATION TERMINÉE")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

