"""
SURPRISE UTILS - Session 89
Calcul robuste de la surprise avec fallback estimate/forecast/previous
"""

from typing import Optional


def calculate_surprise_robust(
    actual: float,
    estimate: Optional[float],
    forecast: Optional[float] = None,
    previous: Optional[float] = None
) -> float:
    """
    Calcule la surprise % avec fallback robuste.
    
    Logique de fallback :
    0. Valider actual (si None/NaN → 0%)
    1. estimate (préféré)
    2. forecast (si estimate None/0)
    3. previous (si forecast None/0)
    4. 0% (si aucune référence disponible)
    
    Args:
        actual: Valeur réelle de l'événement
        estimate: Estimation consensus (priorité 1)
        forecast: Prévision alternative (priorité 2)
        previous: Valeur précédente (priorité 3)
    
    Returns:
        float: Surprise en pourcentage (toujours >= 0)
    
    Examples:
        >>> calculate_surprise_robust(3.5, 3.0)
        16.67  # |3.5-3.0| / |3.0| * 100
        
        >>> calculate_surprise_robust(3.5, None, 3.2)
        9.38  # Utilise forecast
        
        >>> calculate_surprise_robust(3.5, None, None, 3.1)
        12.90  # Utilise previous
        
        >>> calculate_surprise_robust(3.5, None, None, None)
        0.0  # Aucune référence
        
        >>> calculate_surprise_robust(None, 3.0)
        0.0  # actual=None → impossible calculer
    """
    
    # CRITIQUE : Valider actual d'abord
    if actual is None:
        return 0.0
    
    # Gérer NaN explicitement
    try:
        if actual != actual:  # Test NaN
            return 0.0
    except (TypeError, ValueError):
        return 0.0
    
    # Essayer estimate
    if estimate is not None and estimate != 0:
        try:
            result = abs((actual - estimate) / estimate) * 100
            # Vérifier si résultat est NaN
            if result != result:
                return 0.0
            return result
        except (TypeError, ValueError, ZeroDivisionError):
            pass  # Continuer au fallback suivant
    
    # Essayer forecast
    if forecast is not None and forecast != 0:
        try:
            result = abs((actual - forecast) / forecast) * 100
            if result != result:  # Test NaN
                return 0.0
            return result
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    
    # Essayer previous
    if previous is not None and previous != 0:
        try:
            result = abs((actual - previous) / previous) * 100
            if result != result:  # Test NaN
                return 0.0
            return result
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    
    # Aucune référence disponible
    return 0.0


def get_surprise_source(
    estimate: Optional[float],
    forecast: Optional[float] = None,
    previous: Optional[float] = None
) -> str:
    """
    Retourne la source utilisée pour le calcul de surprise.
    
    Utile pour debugging et reporting.
    
    Returns:
        str: 'estimate', 'forecast', 'previous', ou 'none'
    """
    if estimate is not None and estimate != 0:
        return 'estimate'
    if forecast is not None and forecast != 0:
        return 'forecast'
    if previous is not None and previous != 0:
        return 'previous'
    return 'none'


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("🧪 TESTS UNITAIRES - surprise_utils.py")
    print("="*80)
    
    # Test 1 : estimate disponible
    s1 = calculate_surprise_robust(3.5, 3.0)
    assert abs(s1 - 16.67) < 0.01, f"Test 1 échoué : {s1}"
    print("✅ Test 1 : estimate disponible → 16.67%")
    
    # Test 2 : fallback forecast
    s2 = calculate_surprise_robust(3.5, None, 3.2)
    assert abs(s2 - 9.375) < 0.01, f"Test 2 échoué : {s2}"
    print("✅ Test 2 : fallback forecast → 9.38%")
    
    # Test 3 : fallback previous
    s3 = calculate_surprise_robust(3.5, None, None, 3.1)
    assert abs(s3 - 12.90) < 0.01, f"Test 3 échoué : {s3}"
    print("✅ Test 3 : fallback previous → 12.90%")
    
    # Test 4 : aucune référence
    s4 = calculate_surprise_robust(3.5, None, None, None)
    assert s4 == 0.0, f"Test 4 échoué : {s4}"
    print("✅ Test 4 : aucune référence → 0.0%")
    
    # Test 5 : estimate = 0 → fallback
    s5 = calculate_surprise_robust(3.5, 0, 3.2)
    assert abs(s5 - 9.375) < 0.01, f"Test 5 échoué : {s5}"
    print("✅ Test 5 : estimate=0 → fallback forecast → 9.38%")
    
    # Test 6 : valeurs négatives
    s6 = calculate_surprise_robust(-0.5, -0.3)
    assert abs(s6 - 66.67) < 0.01, f"Test 6 échoué : {s6}"
    print("✅ Test 6 : valeurs négatives → 66.67%")
    
    # Test 7 : get_surprise_source
    src1 = get_surprise_source(3.0, 3.2, 3.1)
    assert src1 == 'estimate', f"Test 7a échoué : {src1}"
    
    src2 = get_surprise_source(None, 3.2, 3.1)
    assert src2 == 'forecast', f"Test 7b échoué : {src2}"
    
    src3 = get_surprise_source(None, None, 3.1)
    assert src3 == 'previous', f"Test 7c échoué : {src3}"
    
    src4 = get_surprise_source(None, None, None)
    assert src4 == 'none', f"Test 7d échoué : {src4}"
    
    print("✅ Test 7 : get_surprise_source → OK")
    
    # Test 8 : actual=None
    s8 = calculate_surprise_robust(None, 3.0)
    assert s8 == 0.0, f"Test 8 échoué : {s8}"
    print("✅ Test 8 : actual=None → 0.0%")
    
    # Test 9 : actual=NaN (simulé)
    import math
    s9 = calculate_surprise_robust(math.nan, 3.0)
    assert s9 == 0.0, f"Test 9 échoué : {s9}"
    print("✅ Test 9 : actual=NaN → 0.0%")
    
    print("\n" + "="*80)
    print("✅✅✅ TOUS LES TESTS PASSENT (9 tests) !")
    print("="*80)
