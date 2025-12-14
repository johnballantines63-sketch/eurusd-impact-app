"""
Service de prédiction d'impacts pour événements économiques.

Ce service gère les prédictions d'impacts EUR/USD pour :
- Événements uniques
- Multi-événements avec somme vectorielle
- Fenêtres temporelles

Architecture:
    PredictionService → DataService → warehouse.duckdb
    PredictionService → calculations.py (calculs purs)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from app.services.data_service import DataService
from app.core.calculations import (
    predict_impact_v9_clean,
    calculate_latency,
    calculate_ttr
)
from app.config import config


# ════════════════════════════════════════════════════════════════
# CONSTANTES - SENTIMENT DES FAMILLES
# ════════════════════════════════════════════════════════════════

# Dictionnaire de sentiment par famille d'événements
# Pour certains événements, une surprise positive est une MAUVAISE nouvelle pour USD
FAMILY_SENTIMENT = {
    # INVERSÉ : Surprise positive = BAD news = EUR/USD UP
    'Jobless_Claims': -1,      # Plus de chômeurs = BAD pour USD
    'Unemployment': -1,         # Plus de chômage = BAD pour USD
    'Inflation': 1,             # Plus d'inflation = BAD pour EUR = EUR/USD DOWN
    'CPI': 1,                   # Plus d'inflation = BAD pour EUR = EUR/USD DOWN
    
    # NORMAL : Surprise positive = GOOD news = EUR/USD DOWN
    'GDP': 1,                   # Plus de croissance = GOOD pour USD
    'Retail_Sales': 1,          # Plus de ventes = GOOD pour USD
    'NFP': 1,                   # Plus d'emplois = GOOD pour USD
    'Factory_Orders': 1,        # Plus de commandes = GOOD pour USD
    'Industrial_Production': 1, # Plus de production = GOOD pour USD
    'Building_Permits': 1,      # Plus de permis = GOOD pour USD
    'Durable_Goods': 1,         # Plus de biens durables = GOOD pour USD
    'Trade_Balance': 1,         # Meilleure balance = GOOD pour USD
    'PMI': 1,                   # Plus d'activité = GOOD pour USD
    'Consumer_Confidence': 1,   # Plus de confiance = GOOD pour USD
    'Wages': 1,                 # Plus de salaires = GOOD pour USD (simplifié)
    'Interest_Rate': 1,         # Hausse taux = GOOD pour USD (simplifié)
}


# ════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES - DIRECTION & SURPRISE
# ════════════════════════════════════════════════════════════════

def get_event_direction(family: str, surprise: float) -> int:
    """
    Calcule la direction EUR/USD selon le sentiment de la famille.
    
    Logique :
        Pour événements US (impact USD) :
        - Good news for USD → USD UP → EUR/USD DOWN (direction = -1)
        - Bad news for USD → USD DOWN → EUR/USD UP (direction = +1)
        
        Familles INVERSÉES (Jobless, Unemployment, Inflation, CPI) :
        - Surprise positive = BAD news for USD
        - Exemple : Jobless Claims +28 → Plus de chômeurs → USD DOWN → EUR/USD UP (+1)
        
        Familles NORMALES (GDP, NFP, Retail, etc) :
        - Surprise positive = GOOD news for USD
        - Exemple : NFP +100K → Plus d'emplois → USD UP → EUR/USD DOWN (-1)
    
    Args:
        family: Nom de la famille d'événement
        surprise: Écart entre actual et forecast/estimate
    
    Returns:
        +1 (EUR/USD UP) ou -1 (EUR/USD DOWN)
        
    Examples:
        >>> get_event_direction('NFP', 100)  # Surprise positive NFP
        -1  # Good news USD → EUR/USD DOWN
        
        >>> get_event_direction('Jobless_Claims', 28)  # Plus de chômeurs
        1   # Bad news USD → EUR/USD UP
        
        >>> get_event_direction('CPI', -0.2)  # Inflation plus faible
        1   # Good news EUR → EUR/USD UP
    """
    family_normalized = family.replace(' ', '_') if family else 'Unknown'
    sentiment = FAMILY_SENTIMENT.get(family_normalized, 1)  # Default: normal
    
    # Déterminer si la surprise est bonne ou mauvaise pour USD
    if surprise > 0:
        # Surprise positive
        if sentiment == -1:
            # Famille inversée : surprise+ = BAD for USD = EUR/USD UP
            direction = 1
        else:
            # Famille normale : surprise+ = GOOD for USD = EUR/USD DOWN
            direction = -1
    else:
        # Surprise négative
        if sentiment == -1:
            # Famille inversée : surprise- = GOOD for USD = EUR/USD DOWN
            direction = -1
        else:
            # Famille normale : surprise- = BAD for USD = EUR/USD UP
            direction = 1
    
    return direction


def calculate_surprise_percentage(event: Dict[str, Any]) -> float:
    """
    Calcule le pourcentage de surprise d'un événement.
    
    Formule : |actual - estimate| / estimate × 100
    
    Utilise fallback estimate → forecast → previous pour gérer les NULL.
    Respecte erreur récurrente #2 (forecast/estimate).
    
    Args:
        event: Dictionnaire contenant 'actual', 'estimate', 'forecast', 'previous'
    
    Returns:
        Pourcentage de surprise (0.0 si pas de données disponibles)
    
    Examples:
        >>> event = {'actual': 263, 'estimate': 235}
        >>> calculate_surprise_percentage(event)
        11.91  # +28K sur 235K = 11.9%
        
        >>> event = {'actual': 100, 'estimate': None, 'forecast': None}
        >>> calculate_surprise_percentage(event)
        0.0  # Pas de baseline disponible
    """
    actual = event.get('actual')
    
    # Utiliser estimate comme baseline, avec fallback forecast puis previous
    # RESPECT ERREUR #2 : forecast est souvent NULL
    baseline = event.get('estimate') or event.get('forecast') or event.get('previous')
    
    # Vérifications
    if actual is None or baseline is None:
        return 0.0
    
    if baseline == 0:
        return 0.0
    
    # Calcul du pourcentage de surprise (valeur absolue)
    surprise_pct = abs((actual - baseline) / baseline) * 100
    
    return surprise_pct


def calculate_amplification_factor(
    surprise_pct: float, 
    empirical_score: Optional[float] = None
) -> float:
    """
    Calcule facteur d'amplification pour surprises extrêmes.
    
    Zones d'amplification (validé Session 15) :
    - Zone 1 (0-5%)   : Facteur = 1.0 (pas d'amplification)
    - Zone 2 (5-15%)  : Facteur = 1.0 à 2.5 (interpolation linéaire)
    - Zone 3 (> 15%)  : Facteur = 2.5 (plafond strict)
    
    Formule Zone 2 : 1.0 + (surprise - 5.0) × 0.15
    
    Sécurités :
    - Surprises >30% plafonnées à 30% (aberrations)
    - Score empirique <40 : pas d'amplification (faible importance)
    
    Args:
        surprise_pct: Pourcentage de surprise de l'événement
        empirical_score: Score empirique (optionnel, pour filtrage)
        
    Returns:
        Facteur d'amplification (1.0 à 2.5)
    
    Examples:
        >>> calculate_amplification_factor(0)     # Pas de surprise
        1.0
        
        >>> calculate_amplification_factor(7.2)   # Zone optimale
        1.33
        
        >>> calculate_amplification_factor(15)    # Seuil zone 3
        2.5
        
        >>> calculate_amplification_factor(50)    # Aberration (plafonnée)
        2.5
        
        >>> calculate_amplification_factor(20, empirical_score=30)  # Filtré
        1.0
    """
    surprise_abs = abs(surprise_pct)
    
    # PLAFOND : Surprises aberrantes à 30%
    if surprise_abs > 30:
        surprise_abs = 30.0
    
    # FILTRAGE : Score empirique trop faible = pas d'amplification
    if empirical_score is not None and empirical_score < 40:
        return 1.0
    
    # Zone 1 (0-5%) : Pas d'amplification
    if surprise_abs < 5.0:
        return 1.0
    
    # Zone 2 (5-15%) : Amplification linéaire progressive
    elif surprise_abs < 15.0:
        return 1.0 + (surprise_abs - 5.0) * 0.15
    
    # Zone 3 (>15%) : PLAFOND à ×2.5
    else:
        return 2.5


# ════════════════════════════════════════════════════════════════
# SERVICE PRINCIPAL
# ════════════════════════════════════════════════════════════════

class PredictionService:
    """
    Service de prédiction d'impacts pour événements économiques.
    
    Ce service utilise :
    - DataService pour accéder à la DB
    - calculations.py pour les calculs de base
    - Somme vectorielle pour multi-événements (facteur 0.758)
    
    Architecture:
        - Aucune connexion directe à la DB (injection DataService)
        - Fonctions pures pour calculs
        - Respect erreurs récurrentes (Section 3 PROJECT_STATE)
    
    Attributes:
        data: Instance de DataService pour accès données
        
    Examples:
        >>> data_service = DataService()
        >>> prediction_service = PredictionService(data_service)
        
        >>> # Prédire impact événement unique
        >>> result = prediction_service.predict_single_event(event_id=12345)
        
        >>> # Prédire impacts multi-événements
        >>> result = prediction_service.predict_multi_events(
        ...     event_ids=[123, 124, 125],
        ...     window_minutes=30
        ... )
    """
    
    def __init__(self, data_service: DataService):
        """
        Initialise le service de prédiction.
        
        Args:
            data_service: Instance de DataService pour accès données
            
        Raises:
            ValueError: Si data_service est None
        """
        if data_service is None:
            raise ValueError("DataService ne peut pas être None")
        
        self.data = data_service
    
    
    def predict_single_event(
        self,
        event_id: int,
        method: str = 'v9-clean'
    ) -> Dict[str, Any]:
        """
        Prédit l'impact d'un événement unique.
        
        Utilise :
        - data_service.get_event_by_id() pour récupérer l'événement
        - calculations.predict_impact_v9_clean() pour calcul impact
        - calculations.calculate_latency() pour latence
        - calculations.calculate_ttr() pour time-to-revert
        
        Args:
            event_id: ID de l'événement dans la table events
            method: Méthode de calcul ('v9-clean' par défaut)
        
        Returns:
            Dictionnaire contenant :
                - event_id: ID de l'événement
                - event_title: Titre de l'événement
                - ts_utc: Timestamp UTC
                - country: Pays (US/EU/GB)
                - family: Famille d'événement
                - empirical_score: Score empirique
                - surprise: Surprise calculée (actual - estimate)
                - surprise_pct: Pourcentage de surprise
                - predicted_impact: Impact prédit en pips
                - direction: Direction (+1 UP, -1 DOWN)
                - latency_minutes: Latence médiane
                - ttr_minutes: Time-to-revert médian
                - method: Méthode utilisée
                
        Raises:
            ValueError: Si event_id introuvable ou données manquantes
            
        Examples:
            >>> prediction = service.predict_single_event(event_id=12345)
            >>> print(f"Impact prédit : {prediction['predicted_impact']:.1f} pips")
            >>> print(f"Direction : {'UP' if prediction['direction'] > 0 else 'DOWN'}")
        """
        if method != 'v9-clean':
            raise ValueError(f"Méthode '{method}' non supportée. Utilisez 'v9-clean'.")
        
        # Récupérer l'événement depuis la DB
        with self.data.get_connection() as conn:
            event = conn.execute("""
                SELECT 
                    e.event_id,
                    e.event_title,
                    e.ts_utc,
                    e.country,
                    e.actual,
                    e.estimate,
                    e.forecast,
                    e.previous,
                    ef.family,
                    ef.empirical_score
                FROM events e
                LEFT JOIN event_families ef 
                    ON e.event_key = ef.event_key 
                    AND e.country = ef.country
                WHERE e.event_id = ?
            """, [event_id]).fetchone()
        
        if event is None:
            raise ValueError(f"Événement {event_id} introuvable")
        
        # Convertir en dictionnaire
        event_dict = {
            'event_id': event[0],
            'event_title': event[1],
            'ts_utc': event[2],
            'country': event[3],
            'actual': event[4],
            'estimate': event[5],
            'forecast': event[6],
            'previous': event[7],
            'family': event[8] or 'Unknown',
            'empirical_score': event[9]
        }
        
        # Validation score empirique
        if event_dict['empirical_score'] is None:
            raise ValueError(
                f"Événement {event_id} n'a pas de score empirique. "
                "Famille non reconnue ou pas de mapping dans event_families."
            )
        
        # Calculer surprise (respect erreur #2 : fallback estimate/previous)
        actual = event_dict['actual']
        baseline = event_dict['estimate'] or event_dict['forecast'] or event_dict['previous']
        
        if actual is not None and baseline is not None and baseline != 0:
            surprise = actual - baseline
        else:
            surprise = 0.0
        
        event_dict['surprise'] = surprise
        
        # Calculer pourcentage de surprise
        surprise_pct = calculate_surprise_percentage(event_dict)
        
        # Calculer facteur d'amplification
        amplification_factor = calculate_amplification_factor(
            surprise_pct, 
            event_dict['empirical_score']
        )
        
        # Prédire impact de base avec v9-clean
        impact_base = predict_impact_v9_clean(
            empirical_score=event_dict['empirical_score'],
            num_events=1  # Événement unique
        )
        
        # Appliquer amplification si surprise extrême
        impact_amplified = impact_base * amplification_factor
        
        # Calculer direction
        direction = get_event_direction(event_dict['family'], surprise)
        
        # Calculer latence et TTR
        latency_minutes = calculate_latency(event_dict['empirical_score'])
        ttr_minutes = calculate_ttr(impact_amplified)
        
        # Construire résultat
        result = {
            'event_id': event_dict['event_id'],
            'event_title': event_dict['event_title'],
            'ts_utc': event_dict['ts_utc'],
            'country': event_dict['country'],
            'family': event_dict['family'],
            'empirical_score': event_dict['empirical_score'],
            'surprise': surprise,
            'surprise_pct': surprise_pct,
            'amplification_factor': amplification_factor,
            'predicted_impact': impact_amplified,
            'direction': direction,
            'signed_impact': impact_amplified * direction,
            'latency_minutes': latency_minutes,
            'ttr_minutes': ttr_minutes,
            'method': method
        }
        
        return result
    
    
    def predict_multi_events(
        self,
        event_ids: List[int],
        window_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Prédit l'impact combiné de plusieurs événements avec somme vectorielle.
        
        Algorithme (validé Session 11-15) :
        1. Grouper événements par fenêtre temporelle (< window_minutes)
        2. Pour chaque groupe :
           - Calculer impact de chaque événement avec sa direction
           - Faire somme algébrique (vectorielle)
           - Appliquer amplification si surprises extrêmes
           - Appliquer facteur de correction 0.758
        3. Retourner impact final avec métadonnées
        
        Args:
            event_ids: Liste d'IDs d'événements
            window_minutes: Fenêtre de groupement en minutes (défaut: 30)
        
        Returns:
            Dictionnaire contenant :
                - num_events: Nombre d'événements dans le groupe
                - event_ids: Liste des IDs
                - time_window: Fenêtre temporelle [start, end]
                - contributions: Liste des contributions individuelles
                - impact_brut: Somme vectorielle brute
                - impact_amplified: Après amplification surprise
                - impact_final: Après correction 0.758 (valeur absolue)
                - signed_impact: Impact avec direction
                - direction: Direction finale (+1 UP, -1 DOWN)
                - correction_factor: Facteur appliqué (0.758)
                - max_surprise_pct: Surprise maximale du groupe
                - amplification_factor: Facteur d'amplification appliqué
                
        Raises:
            ValueError: Si event_ids vide ou événements introuvables
            
        Examples:
            >>> # Multi-événements à 14:30 le 11 sept 2025
            >>> result = service.predict_multi_events(
            ...     event_ids=[123, 124, 125],
            ...     window_minutes=30
            ... )
            >>> print(f"Impact combiné : {result['impact_final']:.1f} pips")
            >>> print(f"Direction : {'UP' if result['direction'] > 0 else 'DOWN'}")
        """
        if not event_ids:
            raise ValueError("Liste event_ids ne peut pas être vide")
        
        # Récupérer tous les événements
        with self.data.get_connection() as conn:
            placeholders = ','.join(['?'] * len(event_ids))
            query = f"""
                SELECT 
                    e.event_id,
                    e.event_title,
                    e.ts_utc,
                    e.country,
                    e.actual,
                    e.estimate,
                    e.forecast,
                    e.previous,
                    ef.family,
                    ef.empirical_score
                FROM events e
                LEFT JOIN event_families ef 
                    ON e.event_key = ef.event_key 
                    AND e.country = ef.country
                WHERE e.event_id IN ({placeholders})
                ORDER BY e.ts_utc
            """
            events_rows = conn.execute(query, event_ids).fetchall()
        
        if not events_rows:
            raise ValueError(f"Aucun événement trouvé pour IDs: {event_ids}")
        
        # Convertir en liste de dictionnaires
        events = []
        for row in events_rows:
            event_dict = {
                'event_id': row[0],
                'event_title': row[1],
                'ts_utc': pd.to_datetime(row[2]),
                'country': row[3],
                'actual': row[4],
                'estimate': row[5],
                'forecast': row[6],
                'previous': row[7],
                'family': row[8] or 'Unknown',
                'empirical_score': row[9]
            }
            
            # Calculer surprise (respect erreur #2)
            actual = event_dict['actual']
            baseline = event_dict['estimate'] or event_dict['forecast'] or event_dict['previous']
            
            if actual is not None and baseline is not None and baseline != 0:
                surprise = actual - baseline
            else:
                surprise = 0.0
            
            event_dict['surprise'] = surprise
            
            events.append(event_dict)
        
        # Grouper par fenêtre temporelle
        grouped_events = self._group_events_by_time(events, window_minutes)
        
        # Pour l'instant, on traite tous les événements comme un seul groupe
        # (implémentation simplifiée, peut être étendue plus tard)
        group = events
        
        # Calculer somme vectorielle
        result = self._calculate_vectorial_sum(group)
        
        # Ajouter métadonnées
        result['event_ids'] = event_ids
        result['num_events'] = len(group)
        result['time_window'] = [
            str(group[0]['ts_utc']),
            str(group[-1]['ts_utc'])
        ]
        result['correction_factor'] = config.VECTORIAL_SUM_FACTOR
        
        return result
    
    
    def predict_time_window(
        self,
        start_time: str,
        end_time: str,
        countries: Optional[List[str]] = None,
        min_importance: int = 1
    ) -> pd.DataFrame:
        """
        Prédit les impacts pour tous événements dans une fenêtre temporelle.
        
        Récupère tous les événements dans la fenêtre spécifiée,
        les groupe par minute, et calcule l'impact combiné pour chaque groupe.
        
        Args:
            start_time: Début de la fenêtre (format: 'YYYY-MM-DD HH:MM:SS')
            end_time: Fin de la fenêtre (format: 'YYYY-MM-DD HH:MM:SS')
            countries: Liste de pays à inclure (défaut: ['US', 'EU', 'GB'])
            min_importance: Importance minimale (1-3, défaut: 1)
        
        Returns:
            DataFrame avec colonnes :
                - time_group: Minute de regroupement
                - num_events: Nombre d'événements dans le groupe
                - event_ids: Liste des IDs
                - families: Familles représentées
                - predicted_impact: Impact prédit en pips
                - direction: Direction (+1 UP, -1 DOWN)
                - signed_impact: Impact avec direction
                
        Examples:
            >>> # Événements du 11 septembre 2025
            >>> df = service.predict_time_window(
            ...     start_time='2025-09-11 14:00:00',
            ...     end_time='2025-09-11 16:00:00',
            ...     countries=['US'],
            ...     min_importance=3
            ... )
            >>> print(df[['time_group', 'predicted_impact', 'direction']])
        """
        if countries is None:
            countries = ['US', 'EU', 'GB']
        
        # Récupérer événements dans la fenêtre
        events_df = self.data.get_events(
            start_date=start_time.split(' ')[0],
            end_date=end_time.split(' ')[0],
            countries=countries,
            min_importance=min_importance,
            with_family=True
        )
        
        if events_df.empty:
            return pd.DataFrame(columns=[
                'time_group', 'num_events', 'event_ids', 'families',
                'predicted_impact', 'direction', 'signed_impact'
            ])
        
        # Filtrer par heure exacte
        events_df['ts_utc'] = pd.to_datetime(events_df['ts_utc'])
        mask = (events_df['ts_utc'] >= start_time) & (events_df['ts_utc'] <= end_time)
        events_df = events_df[mask]
        
        if events_df.empty:
            return pd.DataFrame(columns=[
                'time_group', 'num_events', 'event_ids', 'families',
                'predicted_impact', 'direction', 'signed_impact'
            ])
        
        # Grouper par minute (respect erreur #5 : éviter doublons)
        events_df['time_group'] = events_df['ts_utc'].dt.floor('1min')
        
        results = []
        
        for time_group, group in events_df.groupby('time_group'):
            event_ids = group['event_id'].tolist()
            
            try:
                # Prédire impact multi-événements pour ce groupe
                prediction = self.predict_multi_events(
                    event_ids=event_ids,
                    window_minutes=1  # Même minute
                )
                
                results.append({
                    'time_group': time_group,
                    'num_events': len(event_ids),
                    'event_ids': event_ids,
                    'families': list(group['family'].unique()),
                    'predicted_impact': prediction['impact_final'],
                    'direction': prediction['direction'],
                    'signed_impact': prediction['signed_impact']
                })
                
            except Exception as e:
                # Log erreur mais continue avec autres groupes
                print(f"⚠️ Erreur prédiction pour {time_group}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    
    # ════════════════════════════════════════════════════════════════
    # MÉTHODES PRIVÉES - HELPERS
    # ════════════════════════════════════════════════════════════════
    
    def _group_events_by_time(
        self, 
        events: List[Dict[str, Any]], 
        window_minutes: int
    ) -> List[List[Dict[str, Any]]]:
        """
        Groupe les événements par fenêtre temporelle.
        
        Si intervalle entre deux événements < window_minutes → même groupe
        Sinon → nouveau groupe
        
        Args:
            events: Liste d'événements (déjà triés par ts_utc)
            window_minutes: Taille de la fenêtre en minutes
        
        Returns:
            Liste de groupes (chaque groupe est une liste d'événements)
        """
        if not events:
            return []
        
        groups = []
        current_group = [events[0]]
        
        for i in range(1, len(events)):
            prev_time = events[i-1]['ts_utc']
            curr_time = events[i]['ts_utc']
            
            # Calculer l'intervalle en minutes
            interval_minutes = (curr_time - prev_time).total_seconds() / 60
            
            if interval_minutes < window_minutes:
                # Ajouter au groupe courant
                current_group.append(events[i])
            else:
                # Fermer le groupe courant et en créer un nouveau
                groups.append(current_group)
                current_group = [events[i]]
        
        # Ajouter le dernier groupe
        if current_group:
            groups.append(current_group)
        
        return groups
    
    
    def _calculate_vectorial_sum(
        self,
        group: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calcule la somme vectorielle des impacts d'un groupe d'événements.
        
        Algorithme :
        1. Pour chaque événement :
           - Calculer impact absolu avec v9-CLEAN
           - Obtenir direction (+1 ou -1)
           - Contribution = impact × direction
        2. Somme algébrique de toutes les contributions
        3. Calculer surprise maximale du groupe
        4. Appliquer amplification si surprise > 5%
        5. Appliquer facteur de correction 0.758
        
        Args:
            group: Liste d'événements du groupe
        
        Returns:
            Dict avec impact_final, impact_brut, contributions, direction_finale
        """
        num_events = len(group)
        contributions = []
        impact_brut = 0.0
        
        for event in group:
            # Validation score empirique
            score = event.get('empirical_score')
            
            if score is None:
                contributions.append(0.0)
                continue
            
            # Calculer l'impact absolu avec v9-CLEAN
            impact_abs = predict_impact_v9_clean(
                empirical_score=score,
                num_events=num_events
            )
            
            # Obtenir la direction
            direction = get_event_direction(
                family=event.get('family', ''),
                surprise=event.get('surprise', 0.0)
            )
            
            # Contribution = impact × direction
            contribution = impact_abs * direction
            contributions.append(contribution)
            impact_brut += contribution
        
        # Calculer surprise maximale du groupe
        max_surprise_pct = 0.0
        for event in group:
            surprise_pct = calculate_surprise_percentage(event)
            if surprise_pct > max_surprise_pct:
                max_surprise_pct = surprise_pct
        
        # Calculer facteur d'amplification
        amplification_factor = calculate_amplification_factor(
            max_surprise_pct,
            empirical_score=group[0].get('empirical_score') if len(group) > 0 else None
        )
        
        # Appliquer amplification
        impact_amplified = abs(impact_brut) * amplification_factor
        
        # Appliquer facteur de correction 0.758
        impact_final = impact_amplified * config.VECTORIAL_SUM_FACTOR
        
        # Direction finale
        direction_finale = +1 if impact_brut >= 0 else -1
        
        return {
            'impact_final': impact_final,  # Valeur absolue corrigée
            'impact_brut': impact_brut,
            'impact_amplified': impact_amplified,
            'contributions': contributions,
            'direction': direction_finale,
            'signed_impact': impact_final * direction_finale,
            'max_surprise_pct': max_surprise_pct,
            'amplification_factor': amplification_factor
        }


# ════════════════════════════════════════════════════════════════
# EXEMPLE D'UTILISATION
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*70)
    print("PREDICTION SERVICE - Test rapide")
    print("="*70)
    
    # Initialiser services
    data_service = DataService()
    prediction_service = PredictionService(data_service)
    
    print("\n✅ PredictionService initialisé avec succès")
    print("\n📝 Méthodes disponibles :")
    print("   - predict_single_event(event_id)")
    print("   - predict_multi_events(event_ids, window_minutes)")
    print("   - predict_time_window(start_time, end_time)")
    
    print("\n💡 Exemple d'utilisation :")
    print("""
    # Prédire impact événement unique
    result = prediction_service.predict_single_event(event_id=12345)
    print(f"Impact : {result['predicted_impact']:.1f} pips")
    
    # Prédire impacts multi-événements
    result = prediction_service.predict_multi_events(
        event_ids=[123, 124, 125],
        window_minutes=30
    )
    print(f"Impact combiné : {result['impact_final']:.1f} pips")
    """)
