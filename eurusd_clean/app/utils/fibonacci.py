"""
Fibonacci Utilities

Calcul des niveaux de retracement Fibonacci pour analyse technique.
Migré depuis le Planificateur (Session 33).

Fonction principale:
- calculate_fibonacci_levels() : Calculer les 7 niveaux Fibonacci standards
"""

from typing import Dict


def calculate_fibonacci_levels(
    impact_pips: float,
    direction: int
) -> Dict[str, float]:
    """
    Calcule les niveaux de retracement Fibonacci standards.
    
    Les niveaux Fibonacci sont utilisés pour identifier des zones potentielles
    de support/résistance après un mouvement de prix significatif.
    
    Niveaux calculés : 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%
    
    Args:
        impact_pips: Amplitude du mouvement en pips (valeur absolue)
        direction: Direction du mouvement (+1 pour UP, -1 pour DOWN)
    
    Returns:
        Dict avec niveaux Fibonacci {niveau: valeur_pips}
        - Valeurs positives si direction = +1 (UP)
        - Valeurs négatives si direction = -1 (DOWN)
    
    Example:
        >>> # Mouvement UP de 40 pips
        >>> levels = calculate_fibonacci_levels(40.0, direction=1)
        >>> levels['50%']
        20.0
        >>> levels['61.8%']
        24.72
        
        >>> # Mouvement DOWN de 30 pips
        >>> levels = calculate_fibonacci_levels(30.0, direction=-1)
        >>> levels['50%']
        -15.0
        >>> levels['38.2%']
        -11.46
    """
    # Niveaux Fibonacci standards
    levels = {
        '0%': 0.0,
        '23.6%': impact_pips * 0.236,
        '38.2%': impact_pips * 0.382,
        '50%': impact_pips * 0.5,
        '61.8%': impact_pips * 0.618,
        '78.6%': impact_pips * 0.786,
        '100%': impact_pips
    }
    
    # Appliquer direction (négatif si DOWN)
    if direction < 0:
        levels = {k: -v for k, v in levels.items()}
    
    return levels
