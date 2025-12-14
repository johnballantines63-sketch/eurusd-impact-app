"""
Utilities Package

Fonctions utilitaires pour l'application EUR/USD Impact Calculator.
Migrées depuis le Planificateur Multi-Événements (Sessions 33-34).
"""

from app.utils.time_windows import (
    group_events_by_time_window,
    calculate_cluster_impact,
    detect_overlaps
)

from app.utils.backtest import (
    get_real_prices_batch,
    measure_real_impact
)

from app.utils.fibonacci import (
    calculate_fibonacci_levels
)

from app.utils.visualization import (
    create_timeline_chart,
    create_backtest_chart
)

from app.utils.scoring import (
    calculate_tradability_score
)

__all__ = [
    # Time windows
    'group_events_by_time_window',
    'calculate_cluster_impact',
    'detect_overlaps',
    
    # Backtest
    'get_real_prices_batch',
    'measure_real_impact',
    
    # Fibonacci
    'calculate_fibonacci_levels',
    
    # Visualization
    'create_timeline_chart',
    'create_backtest_chart',
    
    # Scoring
    'calculate_tradability_score',
]
