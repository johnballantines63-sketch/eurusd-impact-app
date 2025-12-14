"""
Core package - EUR/USD Impact Calculator

Ce package contient les modules de logique métier pure.

Modules:
    - calculations: Calculs d'impact, MFE, latence, TTR
    - models: Data models et patterns de familles d'événements
    - formulas: Formules de prédiction (v9-CLEAN, v87, etc.)
"""

from .calculations import (
    calculate_family_stats,
    calculate_single_event_impact,
    calculate_latency,
    calculate_ttr,
    predict_impact_v9_clean,
    calculate_multiple_families
)

from .models import (
    EventFamily,
    get_family_info,
    create_event_family,
    get_pattern,
    get_importance,
    get_sensitivity,
    list_all_families,
    get_families_by_importance,
    get_high_importance_families,
    get_medium_importance_families,
    get_low_importance_families,
    get_all_families,
    validate_families,
    FAMILY_PATTERNS,
    FAMILY_IMPORTANCE,
    FAMILY_SENSITIVITIES
)

__all__ = [
    # Calculations
    'calculate_family_stats',
    'calculate_single_event_impact',
    'calculate_latency',
    'calculate_ttr',
    'predict_impact_v9_clean',
    'calculate_multiple_families',
    
    # Models
    'EventFamily',
    'get_family_info',
    'create_event_family',
    'get_pattern',
    'get_importance',
    'get_sensitivity',
    'list_all_families',
    'get_families_by_importance',
    'get_high_importance_families',
    'get_medium_importance_families',
    'get_low_importance_families',
    'get_all_families',
    'validate_families',
    'FAMILY_PATTERNS',
    'FAMILY_IMPORTANCE',
    'FAMILY_SENSITIVITIES',
]

__version__ = '1.0.0'
__author__ = 'Session 29 - Migration Clean'
