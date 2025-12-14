#!/usr/bin/env python3
"""
SESSION 126 - MODULE 5 : VALIDATION PRÉDICTIONS
================================================
Valide prédictions fonction calibrée vs baseline

Basé sur : cross_validate_nfp_final.py (Session 125)
Intègre : utils_mapping.py (Session 126)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, List, Callable, Optional


def validate_predictions_with_baseline(
    amplification_function: Callable[[float], float],
    clusters_with_r2: List[Dict],
    df_scores: pd.DataFrame,
    baseline_amp: float = 2.5
) -> Dict:
    """
    Valide prédictions avec fonction calibrée vs baseline
    
    Args:
        amplification_function: Fonction amp(R²) calibrée
        clusters_with_r2: Liste clusters avec R² tendances calculés
            Format: [{
                'cluster_time': datetime,
                'events': [...],
                'impact_measured': float (pips),
                'r2_trend': float,
                'duration_hours': float,
                'amplitude_pips': float
            }]
        df_scores: DataFrame scores empiriques
        baseline_amp: Amplification baseline pour comparaison (default: 2.5)
    
    Returns:
        {
            'predictions': List[Dict],  # Prédictions détaillées
            'metrics': {
                'n_samples': int,
                'mae_function': float,
                'mae_baseline': float,
                'rmse_function': float,
                'rmse_baseline': float,
                'improvement_mae_pct': float,
                'improvement_rmse_pct': float,
                'r2_predictions': float
            }
        }
    """
    
    # Import utils après validation disponibilité
    try:
        from utils_mapping import (
            get_empirical_score,
            calculate_adjusted_empirical_score,
            calculate_surprise_pct
        )
    except ImportError:
        print("❌ Erreur : utils_mapping.py non trouvé")
        print("   Assurez-vous d'être dans le bon répertoire")
        sys.exit(1)
    
    predictions = []
    
    for cluster_data in clusters_with_r2:
        cluster_time = cluster_data['cluster_time']
        impact_measured = cluster_data['impact_measured']
        r2_trend = cluster_data.get('r2_trend', 0.5)  # Default si manquant
        events = cluster_data.get('events', [])
        
        if not events:
            continue
        
        # Calculer score total cluster
        total_score = 0
        n_events = len(events)
        
        for event in events:
            event_key = event.get('event_key', '')
            country = event.get('country', 'US')
            
            # Récupérer score empirique (avec mapping automatique)
            score = get_empirical_score(event_key, country, df_scores)
            
            if score is not None:
                # Ajuster selon surprise si disponible
                actual = event.get('actual')
                estimate = event.get('estimate')
                
                if actual is not None and estimate is not None:
                    surprise_pct = calculate_surprise_pct(actual, estimate)
                    score_adjusted = calculate_adjusted_empirical_score(score, surprise_pct)
                else:
                    score_adjusted = score
                    surprise_pct = 0.0
                
                total_score += score_adjusted
        
        if total_score == 0:
            # Aucun score trouvé pour ce cluster
            continue
        
        # Prédiction avec fonction calibrée
        amp_from_function = amplification_function(r2_trend)
        impact_pred_function = total_score * amp_from_function * np.sqrt(n_events)
        
        # Prédiction avec baseline
        impact_pred_baseline = total_score * baseline_amp * np.sqrt(n_events)
        
        # Erreurs
        error_function = abs(impact_pred_function - impact_measured)
        error_baseline = abs(impact_pred_baseline - impact_measured)
        
        predictions.append({
            'cluster_time': cluster_time,
            'impact_measured': float(impact_measured),
            'impact_pred_function': float(impact_pred_function),
            'impact_pred_baseline': float(impact_pred_baseline),
            'error_function': float(error_function),
            'error_baseline': float(error_baseline),
            'r2_trend': float(r2_trend),
            'amp_from_function': float(amp_from_function),
            'total_score': float(total_score),
            'n_events': n_events
        })
    
    if len(predictions) == 0:
        return {
            'predictions': [],
            'metrics': {
                'n_samples': 0,
                'mae_function': float('inf'),
                'mae_baseline': float('inf'),
                'rmse_function': float('inf'),
                'rmse_baseline': float('inf'),
                'improvement_mae_pct': 0.0,
                'improvement_rmse_pct': 0.0,
                'r2_predictions': 0.0
            }
        }
    
    # Calculer métriques globales
    df_pred = pd.DataFrame(predictions)
    
    mae_function = df_pred['error_function'].mean()
    mae_baseline = df_pred['error_baseline'].mean()
    
    rmse_function = np.sqrt((df_pred['error_function'] ** 2).mean())
    rmse_baseline = np.sqrt((df_pred['error_baseline'] ** 2).mean())
    
    improvement_mae = ((mae_baseline - mae_function) / mae_baseline) * 100 if mae_baseline > 0 else 0
    improvement_rmse = ((rmse_baseline - rmse_function) / rmse_baseline) * 100 if rmse_baseline > 0 else 0
    
    # R² prédictions (qualité fit)
    from sklearn.metrics import r2_score
    r2_pred = r2_score(df_pred['impact_measured'], df_pred['impact_pred_function'])
    
    metrics = {
        'n_samples': len(predictions),
        'mae_function': float(mae_function),
        'mae_baseline': float(mae_baseline),
        'rmse_function': float(rmse_function),
        'rmse_baseline': float(rmse_baseline),
        'improvement_mae_pct': float(improvement_mae),
        'improvement_rmse_pct': float(improvement_rmse),
        'r2_predictions': float(r2_pred)
    }
    
    return {
        'predictions': predictions,
        'metrics': metrics
    }


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTS UNITAIRES - VALIDATE_PREDICTIONS")
    print("=" * 80)
    print()
    
    # Fonction amplification test (linéaire simple)
    def test_amp_function(r2):
        return 0.05 + 0.05 * r2
    
    # Données test
    import pandas as pd
    
    # Scores test
    df_scores_test = pd.DataFrame([
        {'event_name': 'test_event', 'country': 'usd', 'empirical_score': 50.0}
    ])
    
    # Clusters test
    clusters_test = [
        {
            'cluster_time': pd.Timestamp('2023-06-15 13:30:00'),
            'events': [
                {'event_key': 'test event', 'country': 'US', 'actual': 3.5, 'estimate': 3.0}
            ],
            'impact_measured': 45.0,
            'r2_trend': 0.6,
            'duration_hours': 4.0,
            'amplitude_pips': 35.0
        },
        {
            'cluster_time': pd.Timestamp('2023-07-15 13:30:00'),
            'events': [
                {'event_key': 'test event', 'country': 'US', 'actual': 3.2, 'estimate': 3.0}
            ],
            'impact_measured': 38.0,
            'r2_trend': 0.4,
            'duration_hours': 3.5,
            'amplitude_pips': 30.0
        }
    ]
    
    print("[TEST 1] validate_predictions_with_baseline()")
    print("-" * 80)
    print()
    
    try:
        result = validate_predictions_with_baseline(
            test_amp_function,
            clusters_test,
            df_scores_test,
            baseline_amp=2.5
        )
        
        print(f"✅ Fonction exécutée sans erreur")
        print()
        print(f"Métriques :")
        print(f"  N échantillons        : {result['metrics']['n_samples']}")
        print(f"  MAE fonction          : {result['metrics']['mae_function']:.2f} pips")
        print(f"  MAE baseline          : {result['metrics']['mae_baseline']:.2f} pips")
        print(f"  Amélioration MAE      : {result['metrics']['improvement_mae_pct']:+.1f}%")
        print(f"  RMSE fonction         : {result['metrics']['rmse_function']:.2f} pips")
        print(f"  RMSE baseline         : {result['metrics']['rmse_baseline']:.2f} pips")
        print(f"  Amélioration RMSE     : {result['metrics']['improvement_rmse_pct']:+.1f}%")
        print(f"  R² prédictions        : {result['metrics']['r2_predictions']:.4f}")
        print()
        
        print("Prédictions détaillées :")
        for pred in result['predictions']:
            print(f"  {pred['cluster_time']} | "
                  f"mesuré={pred['impact_measured']:.1f} | "
                  f"prédit={pred['impact_pred_function']:.1f} | "
                  f"R²={pred['r2_trend']:.2f} | "
                  f"amp={pred['amp_from_function']:.4f}")
        
    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
    
    print()
    print("=" * 80)
    print("TESTS TERMINÉS")
    print("=" * 80)
