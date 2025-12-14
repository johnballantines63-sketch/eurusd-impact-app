#!/usr/bin/env python3
"""
Validation Pipeline Complet - Multi-Dates
==========================================

Script pour valider le pipeline complet sur plusieurs dates historiques
et comparer les prédictions avec les impacts réels.

Objectifs :
1. Exécuter le pipeline complet sur 10-20 dates
2. Comparer prédictions vs impacts réels
3. Calculer métriques (MAE, RMSE, précision)
4. Identifier les cas problématiques

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Ajouter chemins
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'session120'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor

# Dates de test avec impacts réels connus
# Source : outputs/validation_finale_pipeline.csv
TEST_DATES = [
    {
        'date': '2025-09-11',
        'expected_impact_real': 21.7,  # impact_real depuis CSV
        'expected_pattern': 'DOUBLE_WAVE',
        'notes': 'Cas de référence principal'
    },
    {
        'date': '2025-08-01',
        'expected_impact_real': 188.3,
        'expected_pattern': 'SINGLE_WAVE_FORT',
        'notes': 'Single Wave Fort, importance high'
    },
    {
        'date': '2025-11-20',  # Anciennement 2025-11-26
        'expected_impact_real': 34.4,
        'expected_pattern': 'SINGLE_WAVE_STANDARD',
        'notes': 'Single Wave Standard'
    },
    {
        'date': '2025-10-10',
        'expected_impact_real': 56.7,
        'expected_pattern': 'DOUBLE_WAVE',
        'notes': 'Double Wave'
    },
    {
        'date': '2025-06-23',
        'expected_impact_real': 83.9,
        'expected_pattern': 'DOUBLE_WAVE',
        'notes': 'Double Wave'
    },
    {
        'date': '2025-01-15',
        'expected_impact_real': None,  # À mesurer
        'expected_pattern': 'CPI',
        'notes': 'CPI'
    },
    {
        'date': '2025-05-29',
        'expected_impact_real': None,  # À mesurer
        'expected_pattern': 'JOBLESS_PCE',
        'notes': 'JOBLESS_PCE'
    },
]

def calculate_metrics(predictions, reals):
    """Calcule les métriques de performance"""
    # Filtrer les valeurs None
    valid_pairs = [(p, r) for p, r in zip(predictions, reals) if p is not None and r is not None]
    
    if not valid_pairs:
        return {
            'mae': None,
            'rmse': None,
            'precision_10_pips': None,
            'precision_20_pips': None,
            'n_valid': 0
        }
    
    preds = [p for p, r in valid_pairs]
    reals_list = [r for p, r in valid_pairs]
    
    errors = [abs(p - r) for p, r in valid_pairs]
    
    mae = np.mean(errors)
    rmse = np.sqrt(np.mean([(p - r)**2 for p, r in valid_pairs]))
    precision_10 = sum(1 for e in errors if e <= 10) / len(errors) * 100
    precision_20 = sum(1 for e in errors if e <= 20) / len(errors) * 100
    
    return {
        'mae': mae,
        'rmse': rmse,
        'precision_10_pips': precision_10,
        'precision_20_pips': precision_20,
        'n_valid': len(valid_pairs),
        'errors': errors
    }

def main():
    print('='*80)
    print('VALIDATION PIPELINE COMPLET - MULTI-DATES')
    print('='*80)
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=False)
    
    results = []
    start_time_total = time.time()
    
    for i, test_case in enumerate(TEST_DATES, 1):
        date_str = test_case['date']
        expected_impact = test_case.get('expected_impact_real')
        expected_pattern = test_case.get('expected_pattern')
        notes = test_case.get('notes', '')
        
        print(f'[{i}/{len(TEST_DATES)}] 📅 {date_str} - {notes}')
        print('-'*80)
        
        try:
            # Exécuter pipeline complet
            start_time = time.time()
            result = executor.execute_complete_pipeline(date_str)
            elapsed_time = time.time() - start_time
            
            if result['success']:
                final_pred = result['final_prediction']
                
                predicted_impact = final_pred.get('prediction_finale')
                pattern_detected = final_pred.get('pattern_type')
                impact_base = final_pred.get('impact_base')
                amplification = final_pred.get('amplification_predite')
                exit_target = final_pred.get('exit_target')
                
                # Calculer erreur si impact réel connu
                error = None
                error_pct = None
                if expected_impact is not None and predicted_impact is not None:
                    error = abs(predicted_impact - expected_impact)
                    error_pct = (error / expected_impact * 100) if expected_impact > 0 else None
                
                # Vérifier pattern
                pattern_match = (pattern_detected == expected_pattern) if expected_pattern else None
                
                print(f'   ✅ Succès ({elapsed_time:.2f}s)')
                print(f'   Pattern détecté : {pattern_detected} {"✅" if pattern_match else "⚠️" if pattern_match is False else ""}')
                print(f'   Impact base : {impact_base:.2f} pips')
                print(f'   Amplification : {amplification:.4f}x')
                print(f'   Prédiction finale : {predicted_impact:.2f} pips')
                print(f'   Exit target : {exit_target:.2f} pips')
                
                if expected_impact is not None:
                    print(f'   Impact réel attendu : {expected_impact:.2f} pips')
                    if error is not None:
                        print(f'   Erreur : {error:.2f} pips ({error_pct:.1f}%)' if error_pct else f'   Erreur : {error:.2f} pips')
                
                # Informations supplémentaires
                cluster_info = result.get('results', {}).get('etape3_cluster_info', {})
                n_clusters_identical = len(result.get('results', {}).get('etape4_identical_clusters', []))
                
                print(f'   Clusters identiques trouvés : {n_clusters_identical}')
                print(f'   Noyau dur : {cluster_info.get("core_type", "N/A")} ({len(cluster_info.get("core_events", []))} événements)')
                
                results.append({
                    'date': date_str,
                    'success': True,
                    'pattern_detected': pattern_detected,
                    'pattern_expected': expected_pattern,
                    'pattern_match': pattern_match,
                    'impact_base': impact_base,
                    'amplification': amplification,
                    'prediction_finale': predicted_impact,
                    'exit_target': exit_target,
                    'impact_real_expected': expected_impact,
                    'error_abs': error,
                    'error_pct': error_pct,
                    'n_clusters_identical': n_clusters_identical,
                    'core_type': cluster_info.get('core_type', 'N/A'),
                    'time_seconds': elapsed_time,
                    'notes': notes
                })
            else:
                error_msg = result.get('error', 'Erreur inconnue')
                print(f'   ❌ Échec : {error_msg}')
                
                results.append({
                    'date': date_str,
                    'success': False,
                    'error': error_msg,
                    'pattern_detected': None,
                    'prediction_finale': None,
                    'impact_real_expected': expected_impact,
                    'error_abs': None,
                    'time_seconds': elapsed_time,
                    'notes': notes
                })
        
        except Exception as e:
            print(f'   ❌ Exception : {e}')
            import traceback
            traceback.print_exc()
            
            results.append({
                'date': date_str,
                'success': False,
                'error': str(e),
                'pattern_detected': None,
                'prediction_finale': None,
                'impact_real_expected': expected_impact,
                'error_abs': None,
                'time_seconds': 0,
                'notes': notes
            })
        
        print()
    
    elapsed_total = time.time() - start_time_total
    
    # Calculer métriques globales
    print('='*80)
    print('RÉSUMÉ GLOBAL')
    print('='*80)
    print()
    
    df_results = pd.DataFrame(results)
    
    n_success = df_results['success'].sum()
    n_total = len(df_results)
    n_failures = n_total - n_success
    
    print(f'✅ Succès : {n_success}/{n_total}')
    print(f'❌ Échecs : {n_failures}/{n_total}')
    print(f'⏱️  Temps total : {elapsed_total:.2f} secondes')
    print(f'⏱️  Temps moyen par date : {elapsed_total/n_total:.2f} secondes')
    print()
    
    # Métriques sur les prédictions
    valid_predictions = df_results[df_results['success'] & df_results['impact_real_expected'].notna()]
    
    if len(valid_predictions) > 0:
        predictions = valid_predictions['prediction_finale'].tolist()
        reals = valid_predictions['impact_real_expected'].tolist()
        
        metrics = calculate_metrics(predictions, reals)
        
        print('📊 MÉTRIQUES DE PERFORMANCE')
        print('-'*80)
        print(f'   Nombre de dates validées : {metrics["n_valid"]}')
        if metrics['mae'] is not None:
            print(f'   MAE (Mean Absolute Error) : {metrics["mae"]:.2f} pips')
            print(f'   RMSE (Root Mean Squared Error) : {metrics["rmse"]:.2f} pips')
            print(f'   Précision (±10 pips) : {metrics["precision_10_pips"]:.1f}%')
            print(f'   Précision (±20 pips) : {metrics["precision_20_pips"]:.1f}%')
            print()
            
            # Distribution des erreurs
            errors = metrics['errors']
            if errors:
                print(f'   Erreur min : {min(errors):.2f} pips')
                print(f'   Erreur max : {max(errors):.2f} pips')
                print(f'   Erreur médiane : {np.median(errors):.2f} pips')
        print()
    
    # Analyse par pattern
    print('📊 ANALYSE PAR PATTERN')
    print('-'*80)
    pattern_stats = df_results[df_results['success']].groupby('pattern_detected').agg({
        'date': 'count',
        'error_abs': ['mean', 'std'],
        'prediction_finale': 'mean'
    }).round(2)
    print(pattern_stats)
    print()
    
    # Cas problématiques
    if len(valid_predictions) > 0:
        problematic = valid_predictions[valid_predictions['error_abs'] > 20]
        if len(problematic) > 0:
            print('⚠️  CAS PROBLÉMATIQUES (erreur > 20 pips)')
            print('-'*80)
            for _, row in problematic.iterrows():
                print(f'   {row["date"]} : Erreur {row["error_abs"]:.2f} pips')
                print(f'      Prédit : {row["prediction_finale"]:.2f} pips')
                print(f'      Réel : {row["impact_real_expected"]:.2f} pips')
                print(f'      Pattern : {row["pattern_detected"]}')
            print()
    
    # Sauvegarder résultats
    output_path = PROJECT_ROOT / 'outputs' / 'validation_pipeline_multi_dates.csv'
    df_results.to_csv(output_path, index=False)
    print(f'💾 Résultats sauvegardés : {output_path}')
    print()
    
    # Afficher tableau détaillé
    print('='*80)
    print('RÉSULTATS DÉTAILLÉS')
    print('='*80)
    print()
    
    display_cols = ['date', 'success', 'pattern_detected', 'prediction_finale', 
                    'impact_real_expected', 'error_abs', 'n_clusters_identical', 'time_seconds']
    display_df = df_results[display_cols].copy()
    print(display_df.to_string(index=False))
    print()
    
    return df_results, metrics

if __name__ == '__main__':
    df_results, metrics = main()

