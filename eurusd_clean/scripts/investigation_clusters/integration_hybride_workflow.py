#!/usr/bin/env python3
"""
INTÉGRATION HYBRIDE - WORKFLOW ORIGINAL + PATTERN-BASED
=======================================================

Stratégie :
1. Si cluster très similaire trouvé (Jaccard > 0.7) → Workflow Original
2. Sinon → Pattern-Based

Auteur : André Valentin avec Claude
Date : 16 novembre 2025
"""

import json
import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

# Chemins
DB_PATH = Path("data/warehouse.duckdb")
INVESTIGATION_RESULTS = Path(__file__).parent / "investigation_results.json"
WORKFLOW_RESULTS = Path(__file__).parent / "test_formules_predictives_final" / "test_results_final.json"
OUTPUT_DIR = Path(__file__).parent / "integration_hybride"
OUTPUT_DIR.mkdir(exist_ok=True)

# Seuil similarité pour utiliser workflow original
SIMILARITY_THRESHOLD = 0.7

# Bornes amplification
AMP_MIN = 0.01
AMP_MAX = 0.5


def load_workflow_functions() -> Dict:
    """Charge fonctions calibrées du workflow original."""
    with open(WORKFLOW_RESULTS, 'r') as f:
        data = json.load(f)
    
    functions = {}
    
    # Mode US ONLY (meilleur résultat : MAE 26.49 pips)
    if 'us_only' in data.get('results', {}):
        us_result = data['results']['us_only']
        calibration = us_result.get('calibration', {})
        best_model = calibration.get('best_model', {})
        
        if best_model:
            model_name = best_model.get('name')
            params = best_model.get('parameters', [])
            
            if model_name == 'sigmoid' and len(params) == 3:
                def sigmoid(r2, a, b, c):
                    return a / (1 + np.exp(-b * (r2 - c)))
                
                def amp_function(r2):
                    amp = sigmoid(r2, *params)
                    return max(AMP_MIN, min(AMP_MAX, amp))
                
                functions['us_only'] = {
                    'function': amp_function,
                    'model': 'sigmoid',
                    'params': params,
                    'mae': us_result.get('validation', {}).get('metrics', {}).get('mae_function', 0)
                }
    
    # Mode FULL (fallback si US ONLY pas disponible)
    if 'full' in data.get('results', {}) and 'us_only' not in functions:
        full_result = data['results']['full']
        calibration = full_result.get('calibration', {})
        best_model = calibration.get('best_model', {})
        
        if best_model:
            model_name = best_model.get('name')
            params = best_model.get('parameters', [])
            
            if model_name == 'exponential' and len(params) == 2:
                def exponential(r2, a, b):
                    return a * np.exp(b * r2)
                
                def amp_function(r2):
                    amp = exponential(r2, *params)
                    return max(AMP_MIN, min(AMP_MAX, amp))
                
                functions['full'] = {
                    'function': amp_function,
                    'model': 'exponential',
                    'params': params,
                    'mae': full_result.get('validation', {}).get('metrics', {}).get('mae_function', 0)
                }
    
    return functions


def find_similar_cluster(cluster_composition: set, similarity_threshold: float = 0.7) -> Optional[Dict]:
    """Cherche cluster similaire dans résultats investigation."""
    with open(INVESTIGATION_RESULTS, 'r') as f:
        data = json.load(f)
    
    period_key = 'period_0'
    method_key = 'jaccard_0.5'
    
    if period_key not in data.get('search_results', {}):
        return None
    
    period_data = data['search_results'][period_key]
    if method_key not in period_data.get('methods', {}):
        return None
    
    method_data = period_data['methods'][method_key]
    
    # Chercher dans composition complète
    clusters_full = method_data.get('clusters_variants_full_details', [])
    for cluster in clusters_full:
        cluster_comp = set(cluster.get('composition', []))
        similarity = len(cluster_composition & cluster_comp) / len(cluster_composition | cluster_comp) if cluster_comp else 0
        
        if similarity >= similarity_threshold:
            return {
                'cluster': cluster,
                'similarity': similarity,
                'mode': 'full'
            }
    
    # Chercher dans US uniquement
    clusters_us = method_data.get('clusters_variants_us_only_details', [])
    for cluster in clusters_us:
        cluster_comp = set(cluster.get('composition', []))
        similarity = len(cluster_composition & cluster_comp) / len(cluster_composition | cluster_comp) if cluster_comp else 0
        
        if similarity >= similarity_threshold:
            return {
                'cluster': cluster,
                'similarity': similarity,
                'mode': 'us_only'
            }
    
    return None


def predict_with_workflow_original(
    cluster_composition: set,
    r2_trend: float,
    total_score: float,
    n_events: int,
    workflow_functions: Dict
) -> Optional[Dict]:
    """Prédit avec workflow original si cluster similaire trouvé."""
    similar = find_similar_cluster(cluster_composition, SIMILARITY_THRESHOLD)
    
    if not similar:
        return None
    
    mode = similar['mode']
    
    if mode not in workflow_functions:
        return None
    
    amp_function = workflow_functions[mode]['function']
    amp = amp_function(r2_trend)
    
    impact_pred = total_score * amp * np.sqrt(n_events)
    
    return {
        'impact_pred': impact_pred,
        'amplification': amp,
        'method': 'workflow_original',
        'mode': mode,
        'similarity': similar['similarity'],
        'model': workflow_functions[mode]['model']
    }


def predict_with_pattern_based(
    pattern_type: str,
    score_range: str,
    use_median: bool = False
) -> Optional[Dict]:
    """
    Prédit avec approche pattern-based.
    
    Note: Cette fonction devrait charger les données historiques
    et calculer moyenne/médiane du groupe. Pour l'instant, retourne None
    car nécessite accès aux données pattern-based.
    """
    # TODO: Implémenter chargement données pattern-based
    # Pour l'instant, retourne None (sera implémenté dans intégration complète)
    return None


def predict_hybrid(
    cluster_composition: set,
    r2_trend: float,
    total_score: float,
    n_events: int,
    pattern_type: str,
    score_range: str,
    workflow_functions: Dict
) -> Dict:
    """
    Prédit avec stratégie hybride :
    1. Essayer workflow original (si cluster similaire)
    2. Sinon, utiliser pattern-based
    """
    # Essayer workflow original
    workflow_pred = predict_with_workflow_original(
        cluster_composition, r2_trend, total_score, n_events, workflow_functions
    )
    
    if workflow_pred:
        return {
            **workflow_pred,
            'strategy': 'workflow_original'
        }
    
    # Fallback pattern-based
    pattern_pred = predict_with_pattern_based(pattern_type, score_range)
    
    if pattern_pred:
        return {
            **pattern_pred,
            'strategy': 'pattern_based'
        }
    
    # Fallback baseline
    return {
        'impact_pred': total_score * 2.5 * np.sqrt(n_events),
        'amplification': 2.5,
        'method': 'baseline',
        'strategy': 'baseline'
    }


def main():
    print("="*80)
    print("INTÉGRATION HYBRIDE - WORKFLOW ORIGINAL + PATTERN-BASED")
    print("="*80)
    print()
    
    # Charger fonctions workflow original
    print("📂 Chargement fonctions workflow original...")
    workflow_functions = load_workflow_functions()
    
    if not workflow_functions:
        print("❌ Aucune fonction workflow original disponible")
        return 1
    
    print(f"✅ {len(workflow_functions)} fonction(s) chargée(s)")
    for mode, func_data in workflow_functions.items():
        print(f"   - {mode}: {func_data['model']} (MAE: {func_data['mae']:.2f} pips)")
    print()
    
    # Exemple d'utilisation
    print("📊 Exemple d'utilisation :")
    print("-"*80)
    
    # Cluster test (composition complète)
    test_composition = {
        'continuing jobless claims',
        'core inflation rate',
        'cpi',
        'current account',
        'inflation rate',
        'initial jobless claims',
        'jobless claims 4 week average',
        'real earnings'
    }
    
    test_r2 = 0.5
    test_score = 150.0
    test_n_events = 8
    
    result = predict_hybrid(
        test_composition,
        test_r2,
        test_score,
        test_n_events,
        'DOUBLE_WAVE_UP',
        '200-300',
        workflow_functions
    )
    
    print(f"Composition : {len(test_composition)} événements")
    print(f"R² tendance : {test_r2:.4f}")
    print(f"Score total : {test_score:.2f}")
    print(f"Nombre événements : {test_n_events}")
    print()
    print(f"Stratégie : {result['strategy']}")
    print(f"Impact prédit : {result['impact_pred']:.2f} pips")
    print(f"Amplification : {result.get('amplification', 'N/A')}")
    
    if result['strategy'] == 'workflow_original':
        print(f"Similarité : {result.get('similarity', 'N/A'):.3f}")
        print(f"Mode : {result.get('mode', 'N/A')}")
        print(f"Modèle : {result.get('model', 'N/A')}")
    
    # Sauvegarder configuration
    config = {
        'workflow_functions': {
            mode: {
                'model': func_data['model'],
                'mae': func_data['mae']
            }
            for mode, func_data in workflow_functions.items()
        },
        'similarity_threshold': SIMILARITY_THRESHOLD,
        'amp_bounds': {'min': AMP_MIN, 'max': AMP_MAX}
    }
    
    config_file = OUTPUT_DIR / "hybrid_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Configuration sauvegardée : {config_file}")
    
    print(f"\n{'='*80}")
    print("✅ INTÉGRATION HYBRIDE TERMINÉE")
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

