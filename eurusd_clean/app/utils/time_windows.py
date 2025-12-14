"""
Time Windows Utilities

Fonctions pour grouper événements par proximité temporelle et détecter chevauchements.
Migré depuis le Planificateur Multi-Événements (Session 33).

Fonctions principales:
- group_events_by_time_window() : Grouper événements en clusters temporels
- calculate_cluster_impact() : Calculer impact cumulé d'un cluster
- detect_overlaps() : Détecter chevauchements entre fenêtres événements
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def group_events_by_time_window(
    events: List[Dict[str, Any]], 
    max_gap_minutes: int = 30
) -> List[Dict[str, Any]]:
    """
    Groupe les événements en clusters selon leur proximité temporelle.
    
    Événements séparés de moins de max_gap_minutes sont regroupés ensemble.
    Utile pour identifier des sessions d'événements qui se chevauchent.
    
    Args:
        events: Liste de dictionnaires avec clé 'event_time' (datetime)
        max_gap_minutes: Écart maximum en minutes entre deux événements d'un même cluster (défaut: 30)
    
    Returns:
        Liste de clusters, chaque cluster contient:
            - 'window_start': datetime - Début de la fenêtre
            - 'window_end': datetime - Fin de la fenêtre (dernier event + 30 min)
            - 'events': List[Dict] - Liste des événements du cluster
            - 'event_times': List[datetime] - Liste des timestamps
    
    Example:
        >>> events = [
        ...     {'event_time': datetime(2025, 9, 11, 12, 30), 'family': 'CPI'},
        ...     {'event_time': datetime(2025, 9, 11, 12, 30), 'family': 'Core_CPI'},
        ...     {'event_time': datetime(2025, 9, 11, 14, 0), 'family': 'Retail'}
        ... ]
        >>> clusters = group_events_by_time_window(events, max_gap_minutes=60)
        >>> len(clusters)
        2
        >>> len(clusters[0]['events'])
        2
    """
    if not events:
        return []
    
    # Trier par temps
    sorted_events = sorted(events, key=lambda e: e['event_time'])
    
    clusters = []
    current_cluster = {
        'events': [sorted_events[0]],
        'event_times': [sorted_events[0]['event_time']]
    }
    
    for event in sorted_events[1:]:
        # Calculer écart avec dernier événement du cluster actuel
        last_time = current_cluster['event_times'][-1]
        gap = (event['event_time'] - last_time).total_seconds() / 60
        
        if gap <= max_gap_minutes:
            # Ajouter au cluster actuel
            current_cluster['events'].append(event)
            current_cluster['event_times'].append(event['event_time'])
        else:
            # Finaliser cluster actuel
            current_cluster['window_start'] = current_cluster['event_times'][0]
            current_cluster['window_end'] = current_cluster['event_times'][-1] + timedelta(minutes=30)
            clusters.append(current_cluster)
            
            # Démarrer nouveau cluster
            current_cluster = {
                'events': [event],
                'event_times': [event['event_time']]
            }
    
    # Finaliser dernier cluster
    current_cluster['window_start'] = current_cluster['event_times'][0]
    current_cluster['window_end'] = current_cluster['event_times'][-1] + timedelta(minutes=30)
    clusters.append(current_cluster)
    
    return clusters


def calculate_cluster_impact(
    cluster: Dict[str, Any],
    predictions_dict: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calcule l'impact cumulé d'un cluster d'événements.
    
    Agrège les impacts de tous les événements du cluster en utilisant
    une somme vectorielle (directionnelle). Calcule également la latence
    minimale et le TTR maximum du cluster.
    
    Args:
        cluster: Dictionnaire du cluster (produit par group_events_by_time_window)
                 Doit contenir 'events', 'window_start', 'window_end'
        predictions_dict: Dictionnaire {event_key: prediction}
                          event_key format: "family_YYYYMMDD_HHMM"
                          prediction contient: predicted_pips, direction, latency_median, ttr_median
    
    Returns:
        Dictionnaire avec:
            - 'total_pips': float - Impact cumulé (somme vectorielle)
            - 'min_latency': float - Latence minimale du cluster (minutes)
            - 'max_ttr': float - TTR maximum du cluster (minutes)
            - 'events_count': int - Nombre d'événements
            - 'window_start': datetime - Début fenêtre
            - 'window_end': datetime - Fin fenêtre
            - 'events': List[Dict] - Détails événements avec leurs impacts
    
    Example:
        >>> cluster = {
        ...     'events': [
        ...         {'family': 'CPI', 'event_time': datetime(2025, 9, 11, 12, 30)},
        ...         {'family': 'Core_CPI', 'event_time': datetime(2025, 9, 11, 12, 30)}
        ...     ],
        ...     'window_start': datetime(2025, 9, 11, 12, 30),
        ...     'window_end': datetime(2025, 9, 11, 13, 0)
        ... }
        >>> predictions = {
        ...     'CPI_20250911_1230': {'predicted_pips': 20, 'direction': 1, 'latency_median': 5, 'ttr_median': 30},
        ...     'Core_CPI_20250911_1230': {'predicted_pips': 15, 'direction': 1, 'latency_median': 7, 'ttr_median': 25}
        ... }
        >>> result = calculate_cluster_impact(cluster, predictions)
        >>> result['total_pips']
        35.0
        >>> result['min_latency']
        5.0
    """
    cluster_impact = {
        'total_pips': 0.0,
        'min_latency': float('inf'),
        'max_ttr': 0.0,
        'events_count': len(cluster['events']),
        'window_start': cluster['window_start'],
        'window_end': cluster['window_end'],
        'events': []
    }
    
    for event in cluster['events']:
        event_key = f"{event['family']}_{event['event_time'].strftime('%Y%m%d_%H%M')}"
        pred = predictions_dict.get(event_key)
        
        if pred:
            # Somme vectorielle : impact signé selon direction
            impact = pred['predicted_pips'] * pred['direction']
            cluster_impact['total_pips'] += impact
            cluster_impact['min_latency'] = min(cluster_impact['min_latency'], pred['latency_median'])
            cluster_impact['max_ttr'] = max(cluster_impact['max_ttr'], pred['ttr_median'])
            cluster_impact['events'].append({
                'time': event['event_time'],
                'family': event['family'],
                'impact': impact,
                'prediction': pred
            })
    
    # Valeur par défaut si aucune prédiction trouvée
    if cluster_impact['min_latency'] == float('inf'):
        cluster_impact['min_latency'] = 5.0
    
    return cluster_impact


def detect_overlaps(
    predictions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Détecte les chevauchements entre fenêtres d'événements.
    
    Un chevauchement se produit quand la fenêtre TTR d'un événement
    (event_time + latency + ttr) chevauche l'event_time d'un événement suivant.
    Cela indique des conditions de trading potentiellement complexes.
    
    Args:
        predictions: Liste de dictionnaires de prédictions contenant:
                     - 'event': str - Nom événement
                     - 'event_time': datetime - Timestamp
                     - 'latency_median': float - Latence médiane (minutes)
                     - 'ttr_median': float - TTR médian (minutes)
    
    Returns:
        Liste de chevauchements détectés, chaque chevauchement contient:
            - 'event1': str - Premier événement
            - 'event2': str - Second événement (chevauché)
            - 'event1_end': datetime - Fin fenêtre event1 (event_time + latency + ttr)
            - 'event2_start': datetime - Début event2
            - 'overlap_minutes': float - Durée chevauchement en minutes
            - 'severity': str - 'HIGH' si overlap > 30 min, 'MEDIUM' sinon
    
    Example:
        >>> predictions = [
        ...     {'event': 'CPI', 'event_time': datetime(2025, 9, 11, 12, 30),
        ...      'latency_median': 5, 'ttr_median': 40},
        ...     {'event': 'Retail', 'event_time': datetime(2025, 9, 11, 13, 0),
        ...      'latency_median': 10, 'ttr_median': 30}
        ... ]
        >>> overlaps = detect_overlaps(predictions)
        >>> len(overlaps)
        1
        >>> overlaps[0]['severity']
        'MEDIUM'
    """
    if not predictions or len(predictions) < 2:
        return []
    
    # Trier par event_time
    sorted_preds = sorted(predictions, key=lambda p: p['event_time'])
    
    overlaps = []
    
    for i in range(len(sorted_preds) - 1):
        pred1 = sorted_preds[i]
        pred2 = sorted_preds[i + 1]
        
        # Calculer fin de fenêtre event1
        event1_end = pred1['event_time'] + timedelta(
            minutes=pred1.get('latency_median', 5) + pred1.get('ttr_median', 30)
        )
        
        event2_start = pred2['event_time']
        
        # Vérifier chevauchement
        if event1_end > event2_start:
            overlap_minutes = (event1_end - event2_start).total_seconds() / 60
            
            overlaps.append({
                'event1': pred1.get('event', pred1.get('family', 'Unknown')),
                'event2': pred2.get('event', pred2.get('family', 'Unknown')),
                'event1_end': event1_end,
                'event2_start': event2_start,
                'overlap_minutes': overlap_minutes,
                'severity': 'HIGH' if overlap_minutes > 30 else 'MEDIUM'
            })
    
    return overlaps
