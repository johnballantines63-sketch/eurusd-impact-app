"""
Scoring Utilities

Fonctions pour calculer des scores de qualité et tradabilité des sessions.
Migré depuis le Planificateur Multi-Événements (Session 34).

Fonctions principales:
- calculate_tradability_score() : Score de tradabilité d'une session 0-100
"""

from typing import List, Dict, Any


def calculate_tradability_score(
    predictions: List[Dict[str, Any]],
    overlaps: List[Dict[str, Any]],
    time_span_hours: float
) -> float:
    """
    Calcule un score de tradabilité de 0-100 pour une session d'événements.
    
    Le score évalue la qualité de la session de trading basé sur plusieurs facteurs:
    - Cohérence directionnelle (événements dans la même direction = mieux)
    - Nombre de chevauchements (moins = mieux)
    - Densité temporelle (ni trop dense ni trop sparse)
    - Impact cumulé relatif
    
    Un score élevé (>70) indique une session favorable pour trader.
    Un score faible (<40) indique des conditions complexes ou contradictoires.
    
    Args:
        predictions: Liste de prédictions contenant:
                     - 'predicted_pips': float - Impact prédit
                     - 'direction': int - Direction (+1 ou -1)
                     - 'latency_median': float - Latence (minutes)
                     - 'ttr_median': float - TTR (minutes)
        overlaps: Liste de chevauchements depuis detect_overlaps()
                  Chaque chevauchement contient:
                  - 'severity': str - 'HIGH' ou 'MEDIUM'
                  - 'overlap_minutes': float
        time_span_hours: Durée totale de la fenêtre temporelle (heures)
    
    Returns:
        Score de tradabilité entre 0 et 100
    
    Example:
        >>> predictions = [
        ...     {'predicted_pips': 20, 'direction': 1, 'latency_median': 5, 'ttr_median': 30},
        ...     {'predicted_pips': 15, 'direction': 1, 'latency_median': 7, 'ttr_median': 25}
        ... ]
        >>> overlaps = [{'severity': 'MEDIUM', 'overlap_minutes': 15}]
        >>> score = calculate_tradability_score(predictions, overlaps, time_span_hours=2.0)
        >>> score > 60  # Session assez favorable
        True
    """
    if not predictions:
        return 0.0
    
    # Score de base
    base_score = 100.0
    
    # 1. Pénalité pour chevauchements
    overlap_penalty = 0
    for overlap in overlaps:
        if overlap['severity'] == 'HIGH':
            overlap_penalty += 15  # Pénalité forte
        else:  # MEDIUM
            overlap_penalty += 5   # Pénalité modérée
    
    # Limiter la pénalité maximale pour chevauchements
    overlap_penalty = min(overlap_penalty, 40)
    
    # 2. Bonus/Pénalité pour cohérence directionnelle
    directions = [p['direction'] for p in predictions]
    positive_count = sum(1 for d in directions if d > 0)
    negative_count = sum(1 for d in directions if d < 0)
    total_events = len(predictions)
    
    # Calculer ratio de cohérence
    max_direction = max(positive_count, negative_count)
    coherence_ratio = max_direction / total_events
    
    if coherence_ratio >= 0.8:
        # Très cohérent : bonus
        direction_adjustment = 10
    elif coherence_ratio >= 0.6:
        # Assez cohérent : petit bonus
        direction_adjustment = 5
    elif coherence_ratio <= 0.5:
        # Très contradictoire : pénalité
        direction_adjustment = -15
    else:
        # Moyennement contradictoire : petite pénalité
        direction_adjustment = -5
    
    # 3. Pénalité/Bonus pour densité temporelle
    events_per_hour = total_events / max(time_span_hours, 0.5)
    
    if events_per_hour > 5:
        # Trop dense : difficile à trader
        density_penalty = 10
    elif events_per_hour < 0.5:
        # Trop sparse : peu d'opportunités
        density_penalty = 5
    else:
        # Densité idéale
        density_penalty = 0
    
    # 4. Bonus pour impact cumulé significatif
    total_impact = sum(abs(p['predicted_pips']) for p in predictions)
    
    if total_impact > 50:
        # Impact fort : opportunité intéressante
        impact_bonus = 10
    elif total_impact > 30:
        # Impact modéré
        impact_bonus = 5
    else:
        # Impact faible
        impact_bonus = 0
    
    # Calcul du score final
    final_score = (
        base_score
        - overlap_penalty
        + direction_adjustment
        - density_penalty
        + impact_bonus
    )
    
    # Limiter entre 0 et 100
    final_score = max(0.0, min(100.0, final_score))
    
    return round(final_score, 1)
