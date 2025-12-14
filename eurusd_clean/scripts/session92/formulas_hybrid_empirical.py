"""
FORMULAS HYBRID EMPIRICAL - Session 92
Approche hybride : Base Impact empirique + Amplification surprise vectorielle
Validé sur 78 occurrences historiques - MAE moyenne 6.9 pips
"""

import numpy as np
from typing import List, Tuple, Dict

# ============================================================================
# LOOKUP TABLE EMPIRIQUE
# ============================================================================

CLUSTER_PARAMETERS = {
    # (Type, Nombre Events) : (Base Impact, Sensitivity)
    
    # Cluster #1 : Construction (29 occurrences, MAE 4.0 pips)
    ('CONSTRUCTION', 6): {'base_impact': 9.7, 'sensitivity': 0.010},
    
    # Cluster #2 : NFP + Earnings (19 occurrences, MAE 10.0 pips)
    ('NFP', 12): {'base_impact': 23.1, 'sensitivity': 0.005},
    
    # Cluster #3 : CPI 9-events (16 occurrences, MAE 4.6 pips)
    ('CPI', 9): {'base_impact': 12.2, 'sensitivity': 0.005},
    
    # Cluster #4 : CPI 11-events (8 occurrences, MAE 12.1 pips)
    ('CPI', 11): {'base_impact': 28.8, 'sensitivity': 0.030},
    
    # Cluster #5 : FOMC Projections (6 occurrences, MAE 3.9 pips)
    ('FOMC', 12): {'base_impact': 8.8, 'sensitivity': 0.005},
}

# Paramètres par défaut si cluster inconnu
DEFAULT_PARAMS = {
    'base_impact': 15.0,  # Impact moyen global
    'sensitivity': 0.01   # Sensitivity moyenne
}


# ============================================================================
# CALCUL SURPRISE VECTORIELLE
# ============================================================================

def calculate_surprise_vectorielle(surprises: List[float]) -> float:
    """
    Calcule la surprise vectorielle (norme euclidienne)
    
    Args:
        surprises: Liste des surprises individuelles en %
    
    Returns:
        Surprise vectorielle en %
    """
    if not surprises:
        return 0.0
    
    # sqrt(sum(surprise_i²))
    return np.sqrt(sum(s**2 for s in surprises))


# ============================================================================
# IDENTIFICATION CLUSTER
# ============================================================================

def identify_cluster(event_families: List[str], num_events: int) -> Tuple[str, int]:
    """
    Identifie le type de cluster basé sur les familles d'événements
    
    Args:
        event_families: Liste des familles d'événements
        num_events: Nombre d'événements
    
    Returns:
        (cluster_type, num_events)
    """
    families_set = set(event_families)
    
    # Détection CPI
    if 'CPI' in families_set or 'INFLATION' in families_set:
        return ('CPI', num_events)
    
    # Détection NFP
    if 'NFP' in families_set or 'EMPLOYMENT' in families_set:
        return ('NFP', num_events)
    
    # Détection FOMC
    if 'FOMC' in families_set or 'FED' in families_set:
        return ('FOMC', num_events)
    
    # Détection Construction
    if 'CONSTRUCTION' in families_set:
        return ('CONSTRUCTION', num_events)
    
    # Défaut : utiliser nombre d'events comme discriminant
    return ('UNKNOWN', num_events)


# ============================================================================
# CALCUL IMPACT HYBRIDE
# ============================================================================

def calculate_impact_hybrid(
    event_families: List[str],
    surprises: List[float],
    num_events: int
) -> Dict:
    """
    Calcule l'impact prédit avec approche hybride empirique
    
    Args:
        event_families: Liste des familles d'événements
        surprises: Liste des surprises individuelles en %
        num_events: Nombre d'événements
    
    Returns:
        Dict avec impact_predicted, base_impact, amplification_factor, etc.
    """
    
    # 1. Identifier le cluster
    cluster_type, cluster_size = identify_cluster(event_families, num_events)
    cluster_key = (cluster_type, cluster_size)
    
    # 2. Récupérer paramètres du cluster
    if cluster_key in CLUSTER_PARAMETERS:
        params = CLUSTER_PARAMETERS[cluster_key]
    else:
        # Chercher cluster avec même type mais taille différente
        matching = [p for (t, s), p in CLUSTER_PARAMETERS.items() if t == cluster_type]
        if matching:
            params = matching[0]  # Prendre premier match
        else:
            params = DEFAULT_PARAMS
    
    base_impact = params['base_impact']
    sensitivity = params['sensitivity']
    
    # 3. Calculer surprise vectorielle
    surprise_vect = calculate_surprise_vectorielle(surprises)
    
    # 4. Calculer facteur d'amplification
    amplification_factor = 1 + (surprise_vect / 100) * sensitivity
    
    # 5. Impact final
    impact_predicted = base_impact * amplification_factor
    
    return {
        'impact_predicted': impact_predicted,
        'base_impact': base_impact,
        'surprise_vectorielle': surprise_vect,
        'amplification_factor': amplification_factor,
        'sensitivity': sensitivity,
        'cluster_type': cluster_type,
        'cluster_size': cluster_size,
        'cluster_found': cluster_key in CLUSTER_PARAMETERS
    }


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    
    print("="*80)
    print("TEST FORMULAS HYBRID EMPIRICAL")
    print("="*80)
    
    # Test Cluster #1 : Construction (surprise faible)
    result1 = calculate_impact_hybrid(
        event_families=['CONSTRUCTION'],
        surprises=[3.0, 5.0, 0.2, 2.1],
        num_events=6
    )
    
    print("\nTest 1 : Construction, surprise faible")
    print(f"  Surprise vectorielle: {result1['surprise_vectorielle']:.1f}%")
    print(f"  Base impact: {result1['base_impact']:.1f} pips")
    print(f"  Amplification: {result1['amplification_factor']:.3f}x")
    print(f"  Impact prédit: {result1['impact_predicted']:.1f} pips")
    
    # Test Cluster #1 : Construction (surprise élevée)
    result2 = calculate_impact_hybrid(
        event_families=['CONSTRUCTION'],
        surprises=[500.0, 500.0, 2.3, 4.2],
        num_events=6
    )
    
    print("\nTest 2 : Construction, surprise élevée")
    print(f"  Surprise vectorielle: {result2['surprise_vectorielle']:.1f}%")
    print(f"  Base impact: {result2['base_impact']:.1f} pips")
    print(f"  Amplification: {result2['amplification_factor']:.3f}x")
    print(f"  Impact prédit: {result2['impact_predicted']:.1f} pips")
    
    # Test Cluster #2 : NFP
    result3 = calculate_impact_hybrid(
        event_families=['NFP', 'EMPLOYMENT'],
        surprises=[900.0, 140.0, 70.7, 49.3],
        num_events=12
    )
    
    print("\nTest 3 : NFP + Earnings")
    print(f"  Surprise vectorielle: {result3['surprise_vectorielle']:.1f}%")
    print(f"  Base impact: {result3['base_impact']:.1f} pips")
    print(f"  Amplification: {result3['amplification_factor']:.3f}x")
    print(f"  Impact prédit: {result3['impact_predicted']:.1f} pips")
    
    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("="*80)
