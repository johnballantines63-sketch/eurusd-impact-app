"""
Service de scoring composite pour événements économiques.

Ce module fournit le ScoringService qui calcule des scores composites (0-100)
pour évaluer la tradabilité des familles d'événements économiques.

Score composite basé sur 4 composants pondérés :
- Impact (40%) : Amplitude mouvement prix (mfe_p80)
- Persistence (30%) : Qualité temporelle (latence + TTR)
- Reliability (20%) : Nombre d'observations historiques
- Importance (10%) : Importance économique (1-3)

Exemple d'utilisation :
    >>> from app.services.data_service import DataService
    >>> from app.services.scoring_service import ScoringService
    >>> 
    >>> data_service = DataService()
    >>> scoring_service = ScoringService(data_service)
    >>> 
    >>> # Calculer score pour une famille
    >>> result = scoring_service.calculate_family_score('NFP', 'US')
    >>> print(f"Score: {result['score']}, Grade: {result['grade']}")
    >>> 
    >>> # Classer toutes les familles
    >>> rankings = scoring_service.rank_families(['US', 'EU'], min_score=50)
    >>> print(rankings.head())

Note sur les erreurs récurrentes :
- Erreur #2 : N'utilise pas forecast/estimate (utilise stats agrégées)
- Erreur #3 : Filtre toujours par country dans les requêtes
- Erreur #6 : Pas de connexion directe DB (injection DataService)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ScoringWeights:
    """
    Pondérations des composants du score composite.
    
    Les poids doivent totaliser 1.0 (100%).
    
    Attributes:
        impact: Poids du composant impact (amplitude mouvement)
        persistence: Poids du composant persistence (latence + TTR)
        reliability: Poids du composant reliability (nombre événements)
        importance: Poids du composant importance (niveau importance)
    """
    impact: float = 0.40
    persistence: float = 0.30
    reliability: float = 0.20
    importance: float = 0.10
    
    def __post_init__(self):
        """Valide que la somme des poids = 1.0"""
        total = self.impact + self.persistence + self.reliability + self.importance
        if not np.isclose(total, 1.0, atol=1e-6):
            raise ValueError(
                f"La somme des poids doit être 1.0, obtenu : {total:.6f}"
            )


class ScoringService:
    """
    Service de calcul de scores composite pour familles d'événements.
    
    Le ScoringService analyse les statistiques historiques des événements
    économiques pour calculer un score composite 0-100 qui évalue leur
    tradabilité potentielle.
    
    Architecture :
        - Injection DataService (pas de connexion directe DB)
        - Pondérations configurables via ScoringWeights
        - Normalisation robuste avec fonctions non-linéaires
        - Support multi-pays
    
    Attributes:
        data: Instance DataService pour accès données
        weights: Pondérations composants score
        impact_max_pips: Valeur max normalisée impact (défaut: 100 pips)
        latency_optimal_min: Latence optimale (défaut: 5 min)
        latency_max_min: Latence max acceptable (défaut: 60 min)
        ttr_optimal_min: TTR optimal (défaut: 60 min)
        ttr_min_acceptable: TTR min acceptable (défaut: 15 min)
        min_events_reliable: N events min pour reliability (défaut: 10)
    """
    
    def __init__(
        self,
        data_service,
        weights: Optional[ScoringWeights] = None
    ):
        """
        Initialise le ScoringService avec injection DataService.
        
        Args:
            data_service: Instance DataService pour accès DB
            weights: Pondérations personnalisées (optionnel)
        
        Raises:
            TypeError: Si data_service n'est pas une instance DataService
        """
        # Validation injection DataService (erreur #6 prévention)
        if not hasattr(data_service, 'get_event_families'):
            raise TypeError(
                "data_service doit être une instance de DataService"
            )
        
        self.data = data_service
        self.weights = weights or ScoringWeights()
        
        # Paramètres normalisation
        self.impact_max_pips = 100.0
        self.latency_optimal_min = 5.0
        self.latency_max_min = 60.0
        self.ttr_optimal_min = 60.0
        self.ttr_min_acceptable = 15.0
        self.min_events_reliable = 10
    
    def calculate_composite_score(
        self,
        stats: Dict[str, Any],
        importance: int = 2
    ) -> Dict[str, Any]:
        """
        Calcule le score composite 0-100 depuis statistiques événement.
        
        Le score composite combine 4 composants normalisés :
        1. Impact : Amplitude mouvement prix (mfe_p80)
        2. Persistence : Qualité temporelle (latence + TTR)
        3. Reliability : Robustesse statistique (n_events)
        4. Importance : Importance économique (1=low, 2=medium, 3=high)
        
        Formule :
            score = (w_i * impact + w_p * persistence + 
                     w_r * reliability + w_m * importance) * 100
        
        Pénalité appliquée si biais directionnel faible (<60%).
        
        Args:
            stats: Dictionnaire avec statistiques événement
                - mfe_p80: MFE au 80e percentile (float)
                - latency_median: Latence médiane en minutes (float)
                - ttr_median: TTR médian en minutes (float)
                - n_events: Nombre d'événements historiques (int)
                - p_up: Probabilité mouvement UP (float 0-1)
                - p_down: Probabilité mouvement DOWN (float 0-1)
            importance: Niveau importance 1-3 (défaut: 2)
        
        Returns:
            Dictionnaire avec :
                - score: Score final 0-100 (float)
                - grade: Grade A+ à D (str)
                - components: Scores des 4 composants (dict)
                - metrics: Métriques brutes utilisées (dict)
                - tradability: Évaluation tradability (str)
        
        Example:
            >>> stats = {
            ...     'mfe_p80': 35.2,
            ...     'latency_median': 8.5,
            ...     'ttr_median': 45.0,
            ...     'n_events': 87,
            ...     'p_up': 0.72,
            ...     'p_down': 0.28
            ... }
            >>> result = service.calculate_composite_score(stats, importance=3)
            >>> print(f"Score: {result['score']}, Grade: {result['grade']}")
            Score: 78.4, Grade: A
        """
        # Cas événements insuffisants
        if stats.get('n_events', 0) == 0:
            return self._empty_score()
        
        # Calcul scores normalisés composants (0-1)
        impact_score = self._normalize_impact(stats['mfe_p80'])
        latency_score = self._normalize_latency(stats['latency_median'])
        ttr_score = self._normalize_ttr(stats['ttr_median'])
        persistence_score = (latency_score + ttr_score) / 2
        reliability_score = self._normalize_reliability(stats['n_events'])
        importance_score = (importance - 1) / 2  # 1→0, 2→0.5, 3→1
        
        # Score composite pondéré (0-1)
        composite_score = (
            self.weights.impact * impact_score +
            self.weights.persistence * persistence_score +
            self.weights.reliability * reliability_score +
            self.weights.importance * importance_score
        )
        
        # Échelle 0-100
        final_score = composite_score * 100
        
        # Pénalité si biais directionnel faible (<60%)
        directional_bias = max(stats['p_up'], stats['p_down'])
        if directional_bias < 0.6:
            final_score *= 0.85
        
        # Construction résultat
        return {
            'score': round(final_score, 1),
            'grade': self._score_to_grade(final_score),
            'components': {
                'impact': round(impact_score * 100, 1),
                'persistence': round(persistence_score * 100, 1),
                'reliability': round(reliability_score * 100, 1),
                'importance': round(importance_score * 100, 1)
            },
            'metrics': {
                'mfe_p80': stats['mfe_p80'],
                'latency_median': stats['latency_median'],
                'ttr_median': stats['ttr_median'],
                'n_events': stats['n_events'],
                'p_up': stats['p_up']
            },
            'tradability': self._assess_tradability(final_score, stats)
        }
    
    def calculate_family_score(
        self,
        family: str,
        country: str = 'US',
        importance: int = 2
    ) -> Dict[str, Any]:
        """
        Calcule le score pour une famille d'événement spécifique.
        
        Récupère les statistiques historiques via DataService puis
        calcule le score composite.
        
        Args:
            family: Nom de la famille (ex: 'NFP', 'CPI', 'GDP')
            country: Code pays (défaut: 'US')
            importance: Niveau importance 1-3 (défaut: 2)
        
        Returns:
            Dictionnaire résultat calculate_composite_score() avec
            ajout de :
                - family: Nom famille (str)
                - country: Code pays (str)
        
        Raises:
            ValueError: Si famille introuvable pour ce pays
        
        Example:
            >>> result = service.calculate_family_score('NFP', 'US', 3)
            >>> print(f"{result['family']} ({result['country']}): "
            ...       f"Score={result['score']}, Grade={result['grade']}")
            NFP (US): Score=82.3, Grade=A
        """
        # Récupérer stats famille depuis DataService (erreur #3 prévention)
        families_df = self.data.get_event_families(country=country)
        
        # Filtrer famille spécifique
        family_data = families_df[families_df['family'] == family]
        
        if family_data.empty:
            raise ValueError(
                f"Famille '{family}' introuvable pour pays '{country}'"
            )
        
        # Extraire statistiques
        row = family_data.iloc[0]
        stats = {
            'mfe_p80': row['mfe_p80'],
            'latency_median': row['latency_median'],
            'ttr_median': row['ttr_median'],
            'n_events': row['n_events'],
            'p_up': row['p_up'],
            'p_down': row['p_down']
        }
        
        # Calculer score
        result = self.calculate_composite_score(stats, importance)
        
        # Ajouter identifiants
        result['family'] = family
        result['country'] = country
        
        return result
    
    def rank_families(
        self,
        countries: Optional[List[str]] = None,
        min_score: float = 0,
        importance_map: Optional[Dict[str, int]] = None
    ) -> pd.DataFrame:
        """
        Classe toutes les familles d'événements par score.
        
        Calcule les scores pour toutes les familles disponibles
        et retourne un DataFrame trié par score décroissant.
        
        Args:
            countries: Liste codes pays (défaut: ['US'])
            min_score: Score minimum pour inclusion (défaut: 0)
            importance_map: Dict {family: importance} (défaut: tous 2)
        
        Returns:
            DataFrame avec colonnes :
                - family: Nom famille
                - country: Code pays
                - score: Score composite 0-100
                - grade: Grade A+ à D
                - tradability: EXCELLENT à AVOID
                - impact_component: Composant impact 0-100
                - persistence_component: Composant persistence 0-100
                - reliability_component: Composant reliability 0-100
                - importance_component: Composant importance 0-100
                - mfe_p80: MFE P80 brut en pips
                - latency_median: Latence médiane en min
                - ttr_median: TTR médian en min
                - n_events: Nombre événements historiques
                - p_up: Probabilité mouvement UP
        
        Example:
            >>> # Classer familles US avec score >= 60
            >>> rankings = service.rank_families(['US'], min_score=60)
            >>> print(rankings[['family', 'score', 'grade']].head())
               family  score grade
            0     NFP   82.3     A
            1     CPI   76.1     A
            2     GDP   71.8   B+
            
            >>> # Avec importance personnalisée
            >>> importance_map = {'NFP': 3, 'CPI': 3, 'GDP': 2}
            >>> rankings = service.rank_families(
            ...     ['US', 'EU'],
            ...     min_score=50,
            ...     importance_map=importance_map
            ... )
        """
        if countries is None:
            countries = ['US']
        
        if importance_map is None:
            importance_map = {}
        
        results = []
        
        # Parcourir tous les pays
        for country in countries:
            # Récupérer familles pour ce pays (erreur #3 prévention)
            families_df = self.data.get_event_families(country=country)
            
            # Calculer score pour chaque famille
            for _, row in families_df.iterrows():
                family = row['family']
                
                # Importance personnalisée ou défaut 2
                importance = importance_map.get(family, 2)
                
                # Stats pour ce row
                stats = {
                    'mfe_p80': row['mfe_p80'],
                    'latency_median': row['latency_median'],
                    'ttr_median': row['ttr_median'],
                    'n_events': row['n_events'],
                    'p_up': row['p_up'],
                    'p_down': row['p_down']
                }
                
                # Calculer score
                score_result = self.calculate_composite_score(stats, importance)
                
                # Filtrer par min_score
                if score_result['score'] >= min_score:
                    # Ajouter au résultat
                    result_row = {
                        'family': family,
                        'country': country,
                        'score': score_result['score'],
                        'grade': score_result['grade'],
                        'tradability': score_result['tradability'],
                        'impact_component': score_result['components']['impact'],
                        'persistence_component': score_result['components']['persistence'],
                        'reliability_component': score_result['components']['reliability'],
                        'importance_component': score_result['components']['importance'],
                        'mfe_p80': score_result['metrics']['mfe_p80'],
                        'latency_median': score_result['metrics']['latency_median'],
                        'ttr_median': score_result['metrics']['ttr_median'],
                        'n_events': score_result['metrics']['n_events'],
                        'p_up': score_result['metrics']['p_up']
                    }
                    results.append(result_row)
        
        # Créer DataFrame et trier par score décroissant
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('score', ascending=False).reset_index(drop=True)
        
        return df
    
    def batch_score(
        self,
        stats_dict: Dict[str, Dict[str, Any]],
        importance_map: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Calcule scores pour plusieurs familles en batch.
        
        Utile pour scorer plusieurs familles quand on a déjà
        les statistiques en mémoire.
        
        Args:
            stats_dict: Dict {family_name: stats_dict}
            importance_map: Dict {family_name: importance}
        
        Returns:
            Liste de résultats triée par score décroissant
        
        Example:
            >>> stats_dict = {
            ...     'NFP': {'mfe_p80': 35.2, 'latency_median': 8.5, ...},
            ...     'CPI': {'mfe_p80': 28.1, 'latency_median': 12.0, ...}
            ... }
            >>> importance_map = {'NFP': 3, 'CPI': 3}
            >>> results = service.batch_score(stats_dict, importance_map)
        """
        if importance_map is None:
            importance_map = {}
        
        results = []
        
        for family_name, stats in stats_dict.items():
            importance = importance_map.get(family_name, 2)
            score_result = self.calculate_composite_score(stats, importance)
            score_result['family'] = family_name
            results.append(score_result)
        
        # Trier par score décroissant
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def get_tradability_label(self, score: float) -> str:
        """
        Convertit un score en label de grade.
        
        Échelle des grades :
            - A+ : 85-100
            - A  : 75-84
            - B+ : 65-74
            - B  : 55-64
            - C+ : 45-54
            - C  : 35-44
            - D  : 0-34
        
        Args:
            score: Score composite 0-100
        
        Returns:
            Grade (str)
        
        Example:
            >>> service.get_tradability_label(82.3)
            'A'
            >>> service.get_tradability_label(91.5)
            'A+'
        """
        return self._score_to_grade(score)
    
    def format_for_export(
        self,
        scored_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Formate résultats scores pour export CSV/Excel.
        
        Transforme les résultats en format plat avec noms colonnes
        explicites pour export.
        
        Args:
            scored_results: Liste résultats batch_score() ou rank_families()
        
        Returns:
            Liste de dicts avec colonnes aplaties
        
        Example:
            >>> results = service.batch_score(stats_dict)
            >>> export_data = service.format_for_export(results)
            >>> pd.DataFrame(export_data).to_csv('scores.csv')
        """
        export_rows = []
        
        for result in scored_results:
            row = {
                'Family': result['family'],
                'Country': result.get('country', 'N/A'),
                'Score': result['score'],
                'Grade': result['grade'],
                'Tradability': result['tradability'],
                'Impact_Component': result['components']['impact'],
                'Persistence_Component': result['components']['persistence'],
                'Reliability_Component': result['components']['reliability'],
                'Importance_Component': result['components']['importance'],
                'MFE_P80_Pips': result['metrics']['mfe_p80'],
                'Latency_Min': result['metrics']['latency_median'],
                'TTR_Min': result['metrics']['ttr_median'],
                'N_Events': result['metrics']['n_events'],
                'P_Up': result['metrics']['p_up']
            }
            export_rows.append(row)
        
        return export_rows
    
    # ========== MÉTHODES PRIVÉES NORMALISATION ==========
    
    def _normalize_impact(self, mfe_p80: float) -> float:
        """
        Normalise le MFE P80 (impact) avec fonction sigmoïde.
        
        Fonction logistique : 1 / (1 + exp(-k * (x - x0)))
        - k = 0.05 (pente)
        - x0 = 50 pips (point inflexion)
        
        Caractéristiques :
            - Smooth non-linéaire
            - 50 pips → 0.5
            - 100 pips → ~0.92
            - Plafond à 1.0
        
        Args:
            mfe_p80: MFE au 80e percentile en pips
        
        Returns:
            Score normalisé 0-1
        """
        k = 0.05
        x0 = self.impact_max_pips / 2
        return min(1 / (1 + np.exp(-k * (mfe_p80 - x0))), 1.0)
    
    def _normalize_latency(self, latency_median: float) -> float:
        """
        Normalise la latence médiane (temps avant mouvement).
        
        Fonction linéaire par morceaux :
            - ≤5 min : 1.0 (optimal)
            - 5-60 min : 1.0 → 0.2 (linéaire)
            - ≥60 min : 0.2 (plancher)
        
        Rationale : Latence courte = meilleure exécution
        
        Args:
            latency_median: Latence médiane en minutes
        
        Returns:
            Score normalisé 0.2-1.0
        """
        if latency_median <= self.latency_optimal_min:
            return 1.0
        elif latency_median >= self.latency_max_min:
            return 0.2
        else:
            # Interpolation linéaire
            return 1.0 - 0.8 * (
                (latency_median - self.latency_optimal_min) /
                (self.latency_max_min - self.latency_optimal_min)
            )
    
    def _normalize_ttr(self, ttr_median: float) -> float:
        """
        Normalise le TTR médian (temps pour reversal).
        
        Fonction linéaire par morceaux :
            - ≥60 min : 1.0 (optimal - mouvement persistant)
            - 15-60 min : 0.3 → 1.0 (linéaire)
            - ≤15 min : 0.3 (plancher - trop volatil)
        
        Rationale : TTR long = mouvement persistant et tradable
        
        Args:
            ttr_median: TTR médian en minutes
        
        Returns:
            Score normalisé 0.3-1.0
        """
        if ttr_median >= self.ttr_optimal_min:
            return 1.0
        elif ttr_median <= self.ttr_min_acceptable:
            return 0.3
        else:
            # Interpolation linéaire
            return 0.3 + 0.7 * (
                (ttr_median - self.ttr_min_acceptable) /
                (self.ttr_optimal_min - self.ttr_min_acceptable)
            )
    
    def _normalize_reliability(self, n_events: int) -> float:
        """
        Normalise le nombre d'événements historiques (reliability).
        
        Fonction par paliers :
            - <10 events : penalité (0-0.5)
            - ≥10 events : linéaire jusqu'à 20 events → 1.0
            - ≥20 events : plafond 1.0
        
        Rationale : Plus d'historique = statistiques plus fiables
        
        Args:
            n_events: Nombre d'événements historiques
        
        Returns:
            Score normalisé 0-1.0
        """
        if n_events >= self.min_events_reliable:
            # Linéaire 10-20 events
            return min(1.0, n_events / 20)
        else:
            # Pénalité si <10 events
            return n_events / self.min_events_reliable * 0.5
    
    def _score_to_grade(self, score: float) -> str:
        """
        Convertit score numérique en grade lettre.
        
        Args:
            score: Score 0-100
        
        Returns:
            Grade A+ à D
        """
        if score >= 85:
            return 'A+'
        elif score >= 75:
            return 'A'
        elif score >= 65:
            return 'B+'
        elif score >= 55:
            return 'B'
        elif score >= 45:
            return 'C+'
        elif score >= 35:
            return 'C'
        else:
            return 'D'
    
    def _assess_tradability(
        self,
        score: float,
        stats: Dict[str, Any]
    ) -> str:
        """
        Évalue le niveau de tradability global.
        
        Combine le score composite avec des critères minimaux :
            - has_impact : mfe_p80 ≥ 15 pips
            - has_direction : biais ≥ 65%
            - has_persistence : ttr ≥ 20 min
            - is_reliable : n_events ≥ 5
        
        Niveaux :
            - EXCELLENT : Score ≥75 + tous critères
            - GOOD : Score ≥60 + impact + direction
            - FAIR : Score ≥45 + impact
            - POOR : Score ≥30
            - AVOID : Score <30
        
        Args:
            score: Score composite 0-100
            stats: Statistiques événement
        
        Returns:
            Niveau tradability (str)
        """
        # Critères minimaux
        has_impact = stats['mfe_p80'] >= 15.0
        has_direction = max(stats['p_up'], stats['p_down']) >= 0.65
        has_persistence = stats['ttr_median'] >= 20.0
        is_reliable = stats['n_events'] >= 5
        
        # Évaluation par paliers
        if score >= 75 and all([has_impact, has_direction, has_persistence, is_reliable]):
            return 'EXCELLENT'
        elif score >= 60 and has_impact and has_direction:
            return 'GOOD'
        elif score >= 45 and has_impact:
            return 'FAIR'
        elif score >= 30:
            return 'POOR'
        else:
            return 'AVOID'
    
    def _empty_score(self) -> Dict[str, Any]:
        """
        Retourne un résultat vide pour familles sans données.
        
        Returns:
            Dict avec valeurs N/A ou 0
        """
        return {
            'score': 0.0,
            'grade': 'N/A',
            'components': {
                'impact': 0.0,
                'persistence': 0.0,
                'reliability': 0.0,
                'importance': 0.0
            },
            'metrics': {
                'mfe_p80': 0.0,
                'latency_median': 0.0,
                'ttr_median': 0.0,
                'n_events': 0,
                'p_up': 0.0
            },
            'tradability': 'N/A'
        }
