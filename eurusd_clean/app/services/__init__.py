"""
Services layer - EUR/USD Impact Calculator

Ce package contient tous les services métier de l'application.

Services disponibles:
- DataService : Interface unique d'accès à warehouse.duckdb
- PredictionService : Calcul prédictions impacts événements
- ScoringService : Calcul scores composite familles événements
"""

__all__ = [
    'DataService',
    'PredictionService',
    'ScoringService',
]

# Import conditionnel pour éviter erreur si module pas encore créé
try:
    from app.services.data_service import DataService
    from app.services.prediction_service import PredictionService
    from app.services.scoring_service import ScoringService
except ImportError:
    pass
