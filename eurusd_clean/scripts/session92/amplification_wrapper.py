"""
AMPLIFICATION WRAPPER - Session 94
Fonction wrapper pour extraire le facteur d'amplification des formules hybrides
Utilisé pour intégration ADD-ON dans Planificateur V2

Architecture :
- Garde formules S51-55 (calculate_impact_d)
- Remplace seulement coefficient fixe 2.5
- Utilise calibration par cluster (Session 92)
"""

import sys
from pathlib import Path
from typing import List, Dict

# Import module formules hybrides (Session 92)
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from formulas_hybrid_empirical import (
    identify_cluster,
    calculate_surprise_vectorielle,
    CLUSTER_PARAMETERS,
    DEFAULT_PARAMS
)


def get_amplification_factor_hybrid(
    event_families: List[str],
    surprises: List[float],
    num_events: int
) -> Dict:
    """
    Calcule le facteur d'amplification calibré par cluster
    
    Remplace le coefficient fixe 2.5 du Planificateur par une valeur
    adaptée au type de cluster et à la surprise vectorielle.
    
    Architecture ADD-ON :
    - NE remplace PAS calculate_impact_d()
    - Fournit SEULEMENT amplification calibrée
    - Compatible avec formules S51-55
    
    Args:
        event_families: Liste des familles d'événements (['CPI', 'CPI', ...])
        surprises: Liste des surprises individuelles en % ([25.3, 18.1, ...])
        num_events: Nombre d'événements dans le cluster
    
    Returns:
        dict: {
            'amplification_factor': float,  # Facteur à utiliser (remplace 2.5)
            'base_impact': float,           # Impact base cluster (info)
            'sensitivity': float,           # Sensitivity cluster (info)
            'cluster_type': str,            # Type cluster identifié
            'surprise_vectorielle': float,  # Surprise calculée (info)
            'num_events': int               # Nombre events (info)
        }
    
    Exemple :
        >>> amplification = get_amplification_factor_hybrid(
        ...     event_families=['CPI', 'CPI', 'CPI'],
        ...     surprises=[25.3, 18.1, 12.7],
        ...     num_events=3
        ... )
        >>> print(amplification['amplification_factor'])
        1.31  # À utiliser AU LIEU DE 2.5
    
    Usage dans Planificateur :
        # AVANT (coefficient fixe)
        impact = calculate_impact_d(
            empirical_score=adjusted_score,
            num_events=len(events),
            amplification=2.5  # ❌ Fixe
        )
        
        # APRÈS (coefficient calibré)
        ampl_result = get_amplification_factor_hybrid(
            event_families=events['family'].tolist(),
            surprises=surprises,
            num_events=len(events)
        )
        impact = calculate_impact_d(
            empirical_score=adjusted_score,
            num_events=len(events),
            amplification=ampl_result['amplification_factor']  # ✅ Calibré
        )
    """
    
    # 1. Identifier le cluster
    cluster_type, cluster_size = identify_cluster(event_families, num_events)
    
    # 2. Récupérer paramètres cluster
    cluster_key = (cluster_type, cluster_size)
    
    if cluster_key in CLUSTER_PARAMETERS:
        params = CLUSTER_PARAMETERS[cluster_key]
        base_impact = params['base_impact']
        sensitivity = params['sensitivity']
    else:
        # Fallback sur defaults si cluster inconnu
        base_impact = DEFAULT_PARAMS['base_impact']
        sensitivity = DEFAULT_PARAMS['sensitivity']
        cluster_type = f"{cluster_type}_DEFAULT"  # Indiquer qu'on utilise default
    
    # 3. Calculer surprise vectorielle
    surprise_vect = calculate_surprise_vectorielle(surprises)
    
    # 4. Calculer facteur d'amplification
    # Formule hybride : amplification = 1 + (surprise_vect / 100) × sensitivity
    amplification_factor = 1.0 + (surprise_vect / 100.0) * sensitivity
    
    # 5. Retourner résultats complets
    return {
        'amplification_factor': amplification_factor,  # ⭐ Valeur principale
        'base_impact': base_impact,                    # Info cluster
        'sensitivity': sensitivity,                    # Info cluster
        'cluster_type': cluster_type,                  # Type identifié
        'surprise_vectorielle': surprise_vect,         # Surprise calculée
        'num_events': num_events,                      # Nombre events
        'cluster_key': cluster_key,                    # Clé lookup (debug)
        'using_default': cluster_key not in CLUSTER_PARAMETERS  # Flag default
    }


# ============================================================================
# FONCTION VALIDATION (OPTIONNELLE)
# ============================================================================

def validate_amplification_vs_fixed(
    event_families: List[str],
    surprises: List[float],
    num_events: int,
    fixed_coefficient: float = 2.5
) -> Dict:
    """
    Compare amplification hybride vs coefficient fixe
    
    Utile pour validation/debug
    
    Args:
        event_families: Familles événements
        surprises: Surprises individuelles
        num_events: Nombre events
        fixed_coefficient: Coefficient fixe à comparer (défaut 2.5)
    
    Returns:
        dict: Comparaison détaillée
    """
    result = get_amplification_factor_hybrid(event_families, surprises, num_events)
    
    hybrid_ampl = result['amplification_factor']
    difference = hybrid_ampl - fixed_coefficient
    difference_pct = (difference / fixed_coefficient) * 100
    
    return {
        'hybrid_amplification': hybrid_ampl,
        'fixed_coefficient': fixed_coefficient,
        'difference': difference,
        'difference_pct': difference_pct,
        'cluster_type': result['cluster_type'],
        'using_default': result['using_default'],
        'recommendation': 'Hybrid' if abs(difference_pct) > 10 else 'Both OK'
    }


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TEST AMPLIFICATION WRAPPER - Session 94")
    print("=" * 80)
    
    # Test 1 : CPI 9-events (cluster connu)
    print("\n📊 TEST 1 : CPI 9-events (cluster connu)")
    result1 = get_amplification_factor_hybrid(
        event_families=['CPI'] * 9,
        surprises=[25.3, 18.1, 12.7, 8.5, 6.2, 4.1, 3.0, 2.5, 1.8],
        num_events=9
    )
    print(f"Cluster identifié : {result1['cluster_type']}")
    print(f"Amplification factor : {result1['amplification_factor']:.3f}")
    print(f"Base impact : {result1['base_impact']:.1f} pips")
    print(f"Sensitivity : {result1['sensitivity']:.3f}")
    print(f"Surprise vectorielle : {result1['surprise_vectorielle']:.1f}%")
    print(f"Using default : {result1['using_default']}")
    
    # Test 2 : NFP 12-events (cluster connu)
    print("\n📊 TEST 2 : NFP 12-events (cluster connu)")
    result2 = get_amplification_factor_hybrid(
        event_families=['NFP'] * 12,
        surprises=[50.0] * 12,
        num_events=12
    )
    print(f"Cluster identifié : {result2['cluster_type']}")
    print(f"Amplification factor : {result2['amplification_factor']:.3f}")
    print(f"Comparaison vs 2.5 : {result2['amplification_factor'] - 2.5:+.3f}")
    
    # Test 3 : Cluster inconnu (fallback defaults)
    print("\n📊 TEST 3 : RETAIL 5-events (cluster inconnu)")
    result3 = get_amplification_factor_hybrid(
        event_families=['RETAIL'] * 5,
        surprises=[15.0, 10.0, 8.0, 5.0, 3.0],
        num_events=5
    )
    print(f"Cluster identifié : {result3['cluster_type']}")
    print(f"Amplification factor : {result3['amplification_factor']:.3f}")
    print(f"Using default : {result3['using_default']}")
    
    # Test 4 : Comparaison hybride vs fixe
    print("\n📊 TEST 4 : Comparaison hybride vs coefficient fixe 2.5")
    comparison = validate_amplification_vs_fixed(
        event_families=['CPI'] * 9,
        surprises=[33.3] * 9,  # Surprise élevée
        num_events=9
    )
    print(f"Hybride : {comparison['hybrid_amplification']:.3f}")
    print(f"Fixe : {comparison['fixed_coefficient']:.3f}")
    print(f"Différence : {comparison['difference']:+.3f} ({comparison['difference_pct']:+.1f}%)")
    print(f"Recommandation : {comparison['recommendation']}")
    
    print("\n✅ Tests terminés")
