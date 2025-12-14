def calculate_amplification_from_r2(r2_value):
    """
    Calcule facteur amplification basé sur R² de la tendance.
    
    Calibré sur 29 clusters CPI identiques.
    Modèle : quadratic
    
    Args:
        r2_value: R² de la tendance (0-1)
    
    Returns:
        float: Facteur amplification
    
    Exemple:
        >>> calculate_amplification_from_r2(0.8)
        0.0586
    """
    import numpy as np
    
    # Paramètres calibrés
    a = 0.0225716399
    b = 0.0947710630
    c = -0.0621867245
    
    return a + b * r2_value + c * r2_value**2
