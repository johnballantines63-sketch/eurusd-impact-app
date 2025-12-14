"""
ENSEMBLE PREDICTION - Méthode de prédiction combinant moyenne, médiane et KNN
==============================================================================

Version : 1.0 (Session 142+)
Auteur : André Valentin avec Claude
Date : 16 novembre 2025

Principe :
- Combine 4 méthodes : moyenne, médiane, KNN (moyenne), KNN (médiane)
- Poids optimisés par groupe (pattern + score_range) avec LOO-CV
- MAE global : 13.30 pips (vs 14.71 baseline, -1.41 pips, -9.6%)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json


# Chemins
MOVEMENTS_FILE = Path(__file__).parent.parent.parent / "scripts" / "session137" / "step3_movements_with_patterns_v2.csv"
ENSEMBLE_WEIGHTS_FILE = Path(__file__).parent.parent.parent / "scripts" / "investigation_clusters" / "test_ensemble" / "ensemble_results.json"

# Paramètres KNN
K_DEFAULT = 5
DISTANCE_WEIGHTS = {
    'date': 0.3,
    'score': 0.7
}


def assign_score_range(score: float) -> str:
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


def load_historical_movements() -> pd.DataFrame:
    """
    Charge les mouvements historiques avec patterns.
    
    Returns:
        DataFrame avec colonnes : movement_datetime, impact_pips, pattern_type, total_score, etc.
    """
    if not MOVEMENTS_FILE.exists():
        raise FileNotFoundError(f"Fichier mouvements non trouvé : {MOVEMENTS_FILE}")
    
    df = pd.read_csv(MOVEMENTS_FILE)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'], utc=True)
    df['score_range'] = df['total_score'].apply(assign_score_range)
    
    return df


def load_ensemble_weights() -> Dict:
    """
    Charge les poids optimaux par groupe depuis ensemble_results.json.
    
    Returns:
        Dict : {(pattern, score_range): {mean: w1, median: w2, knn_mean: w3, knn_median: w4}}
    """
    if not ENSEMBLE_WEIGHTS_FILE.exists():
        # Fallback : poids par défaut (médiane uniquement)
        return {}
    
    with open(ENSEMBLE_WEIGHTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    weights_dict = {}
    for result in data.get('results', []):
        pattern = result['pattern']
        score_range = result['score_range']
        weights = result.get('weights', {})
        
        key = (pattern, score_range)
        weights_dict[key] = {
            'mean': weights.get('mean', 0.0),
            'median': weights.get('median', 0.25),
            'knn_mean': weights.get('knn_mean', 0.25),
            'knn_median': weights.get('knn_median', 0.5)
        }
    
    return weights_dict


def calculate_distance(case1: Dict, case2: Dict) -> float:
    """
    Calcule distance multi-dimensionnelle entre deux cas.
    
    Features :
    - date : Différence en jours (normalisée par 90 jours)
    - score : Différence score total (normalisée par 100)
    """
    date1 = pd.to_datetime(case1.get('movement_datetime', case1.get('date')))
    date2 = pd.to_datetime(case2.get('movement_datetime', case2.get('date')))
    date_diff = abs((date1 - date2).days) / 90.0
    
    score_diff = abs(case1.get('total_score', 0) - case2.get('total_score', 0)) / 100.0
    
    distance = np.sqrt(
        DISTANCE_WEIGHTS['date'] * date_diff**2 +
        DISTANCE_WEIGHTS['score'] * score_diff**2
    )
    
    return distance


def predict_knn(
    test_case: Dict,
    train_cases: List[Dict],
    k: int = K_DEFAULT,
    use_median: bool = False
) -> float:
    """
    Prédit avec K-Nearest Neighbors.
    
    Args:
        test_case: Cas à prédire
        train_cases: Cas historiques d'entraînement
        k: Nombre de voisins
        use_median: Si True, utilise médiane des k voisins, sinon moyenne
    
    Returns:
        Prédiction en pips
    """
    if len(train_cases) == 0:
        return 0.0
    
    distances = []
    for train_case in train_cases:
        distance = calculate_distance(test_case, train_case)
        distances.append((distance, train_case))
    
    # Trier par distance
    distances.sort(key=lambda x: x[0])
    
    # Prendre k plus proches
    k_actual = min(k, len(distances))
    k_nearest = distances[:k_actual]
    
    # Extraire impacts
    impacts = [case['impact_pips'] for _, case in k_nearest]
    
    # Prédire par moyenne ou médiane
    if use_median:
        return float(np.median(impacts))
    else:
        return float(np.mean(impacts))


def predict_ensemble_group(
    test_case: Dict,
    train_cases: List[Dict],
    weights: Dict[str, float]
) -> Dict:
    """
    Prédit avec ensemble de méthodes.
    
    Méthodes :
    - mean : Moyenne groupe
    - median : Médiane groupe
    - knn_mean : KNN avec moyenne
    - knn_median : KNN avec médiane
    
    Args:
        test_case: Cas à prédire
        train_cases: Cas historiques d'entraînement
        weights: Poids pour chaque méthode
    
    Returns:
        Dict avec prédiction et détails
    """
    if len(train_cases) == 0:
        return {
            'prediction': 0.0,
            'method': 'fallback',
            'individual': {}
        }
    
    impacts = [c['impact_pips'] for c in train_cases]
    
    # Calculer prédictions individuelles
    predictions = {
        'mean': float(np.mean(impacts)),
        'median': float(np.median(impacts)),
        'knn_mean': predict_knn(test_case, train_cases, k=K_DEFAULT, use_median=False),
        'knn_median': predict_knn(test_case, train_cases, k=K_DEFAULT, use_median=True)
    }
    
    # Ensemble pondéré
    prediction_ensemble = sum(
        weights.get(method, 0) * predictions[method]
        for method in predictions
    )
    
    return {
        'prediction': float(prediction_ensemble),
        'method': 'ensemble',
        'individual': predictions,
        'weights': weights
    }


def predict_pattern_based_ensemble(
    pattern_type: str,
    total_score: float,
    num_events: int,
    movement_datetime: pd.Timestamp,
    historical_movements: Optional[pd.DataFrame] = None,
    ensemble_weights: Optional[Dict] = None
) -> Dict:
    """
    Prédit impact avec Ensemble Methods pour un pattern donné.
    
    Args:
        pattern_type: Type de pattern (ex: 'SINGLE_WAVE_FORT_UP')
        total_score: Score total des événements
        num_events: Nombre d'événements
        movement_datetime: Date/heure du mouvement
        historical_movements: DataFrame mouvements historiques (optionnel, chargé si None)
        ensemble_weights: Poids optimaux (optionnel, chargé si None)
    
    Returns:
        Dict avec prédiction et détails
    """
    # Charger données si non fournies
    if historical_movements is None:
        historical_movements = load_historical_movements()
    
    if ensemble_weights is None:
        ensemble_weights = load_ensemble_weights()
    
    # Déterminer score_range
    score_range = assign_score_range(total_score)
    
    # Normaliser pattern_type (enlever _UP/_DOWN si présent)
    pattern_base = pattern_type.replace('_UP', '').replace('_DOWN', '').replace('_FORT', '')
    
    # Chercher groupe correspondant
    group_key = None
    for (pattern, sr), weights in ensemble_weights.items():
        pattern_normalized = pattern.replace('_UP', '').replace('_DOWN', '').replace('_FORT', '')
        if pattern_normalized == pattern_base and sr == score_range:
            group_key = (pattern, sr)
            break
    
    # Si groupe trouvé, utiliser poids optimaux
    if group_key:
        weights = ensemble_weights[group_key]
    else:
        # Fallback : poids par défaut (médiane uniquement)
        weights = {
            'mean': 0.0,
            'median': 1.0,
            'knn_mean': 0.0,
            'knn_median': 0.0
        }
    
    # Filtrer mouvements historiques pour ce groupe
    pattern_filter = historical_movements['pattern_type'] == pattern_type
    score_filter = historical_movements['score_range'] == score_range
    
    group_movements = historical_movements[pattern_filter & score_filter].copy()
    
    if len(group_movements) < 2:
        # Pas assez de cas historiques : fallback moyenne simple
        all_movements = historical_movements[historical_movements['pattern_type'] == pattern_type]
        if len(all_movements) > 0:
            fallback_prediction = float(all_movements['impact_pips'].mean())
        else:
            fallback_prediction = 0.0
        
        return {
            'prediction': fallback_prediction,
            'method': 'fallback_mean',
            'reason': f'Groupe {pattern_type} {score_range} trop petit (n={len(group_movements)})',
            'individual': {},
            'weights': weights
        }
    
    # Convertir en list de dicts pour prédiction
    train_cases = [row.to_dict() for _, row in group_movements.iterrows()]
    
    # Cas de test
    test_case = {
        'movement_datetime': movement_datetime,
        'total_score': total_score,
        'num_events': num_events,
        'pattern_type': pattern_type,
        'score_range': score_range
    }
    
    # Prédire avec ensemble
    result = predict_ensemble_group(test_case, train_cases, weights)
    
    return {
        'prediction': result['prediction'],
        'method': 'ensemble',
        'reason': f'Ensemble Methods (pattern={pattern_type}, score_range={score_range}, n={len(group_movements)})',
        'individual': result.get('individual', {}),
        'weights': weights,
        'n_historical': len(group_movements)
    }

