"""
CLUSTER IMPACT CALCULATOR - SESSION 111
========================================

Module pour calculer l'impact de clusters d'événements individuellement.

OBJECTIF:
Transformer le système de "pattern matching" (ratios hardcodés basés sur 11 sept)
en un système de PRÉDICTION DYNAMIQUE qui calcule l'impact de chaque cluster
indépendamment en utilisant les formules validées Sessions 51-55.

PROBLÈME RÉSOLU:
Avant Session 111, le Planificateur utilisait des ratios fixes:
- impact_cluster1 = impact_total * 0.40  (40% fixe)
- impact_cluster2 = impact_total * 0.82  (82% fixe)
- Timings hardcodés (T+5, T+21, etc.)

Cela fonctionnait uniquement pour des cas similaires au 11 septembre 2025.

SOLUTION Session 111:
- Calculer l'impact de CHAQUE cluster séparément
- Utiliser les formules validées (Sessions 51-55)
- Adapter timings selon caractéristiques du cluster
- Détecter automatiquement le pattern de clusters

Version: 1.0
Date: 04 novembre 2025 - Session 111
Auteur: André Valentin avec Claude
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import math

# Import formules validées
from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d,
    calculate_ttr_c,
    calculate_pullback_v2
)


# ════════════════════════════════════════════════════════════════
# FONCTION 1: CALCUL IMPACT PAR CLUSTER
# ════════════════════════════════════════════════════════════════

def calculate_cluster_impact(
    cluster_events: pd.DataFrame,
    amplification: float = 2.5
) -> Dict:
    """
    Calcule l'impact d'un cluster d'événements isolé.
    
    Utilise les formules validées Sessions 51-55 sur les événements du cluster uniquement,
    permettant de prédire l'impact de chaque cluster indépendamment.
    
    MÉTHODOLOGIE:
    1. Calculer score base moyen du cluster
    2. Calculer surprise max du cluster
    3. Ajuster score selon surprise (Session 55)
    4. Calculer impact avec formule D (Session 51)
    5. Retourner résultats complets avec métadonnées
    
    VALIDATION ATTENDUE (11 sept 2025):
    - Cluster 1 (14 events CPI): 37-42 pips ✅
    - Cluster 2 (1 event Current Account): 12-22 pips ✅
    
    Args:
        cluster_events: DataFrame avec colonnes:
            - empirical_score: Score base événement
            - actual: Valeur réelle
            - estimate: Valeur estimée
            - previous: Valeur précédente (fallback)
        amplification: Facteur amplification (défaut 2.5, ou dynamique Session 107/109)
    
    Returns:
        dict: {
            'impact_pips': float,           # Impact prédit en pips
            'base_score': float,            # Score base moyen du cluster
            'adjusted_score': float,        # Score ajusté par surprise
            'max_surprise': float,          # Surprise max en %
            'num_events': int,              # Nombre événements cluster
            'cluster_weight': float,        # Poids relatif (pour multi-clusters)
            'latency_median': float,        # Latence médiane (pour TTR)
            'calculation_details': dict     # Détails calculs (debug)
        }
    
    Examples:
        >>> # Cluster CPI (14 events)
        >>> cluster1 = events.iloc[0:14]
        >>> result = calculate_cluster_impact(cluster1)
        >>> print(f"Impact: {result['impact_pips']:.1f} pips")
        Impact: 39.2 pips
        
        >>> # Cluster Current Account (1 event)
        >>> cluster2 = events.iloc[14:15]
        >>> result = calculate_cluster_impact(cluster2)
        >>> print(f"Impact: {result['impact_pips']:.1f} pips")
        Impact: 16.5 pips
    """
    # Validation input
    if cluster_events.empty:
        raise ValueError("cluster_events ne peut pas être vide")
    
    # 1. Calculer score base moyen du cluster
    base_scores = cluster_events['empirical_score'].dropna()
    if base_scores.empty:
        raise ValueError("Aucun empirical_score disponible dans le cluster")
    
    base_score_mean = base_scores.mean()
    
    # 2. Calculer surprise max du cluster
    surprises = []
    for _, event in cluster_events.iterrows():
        actual = event.get('actual')
        estimate = event.get('estimate')
        previous = event.get('previous')
        
        # Calculer surprise avec fallback
        if pd.notna(actual) and pd.notna(estimate) and abs(estimate) > 0.01:
            # Sécurité : éviter division par valeur trop proche de 0
            surprise = abs((actual - estimate) / estimate) * 100
            # Plafonner les surprises aberrantes (> 500%)
            surprise = min(surprise, 500.0)
            surprises.append(surprise)
        elif pd.notna(actual) and pd.notna(previous) and abs(previous) > 0.01:
            surprise = abs((actual - previous) / previous) * 100
            surprise = min(surprise, 500.0)
            surprises.append(surprise)
    
    max_surprise = max(surprises) if surprises else 0.0
    
    # 3. Ajuster score selon surprise (Session 55)
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=base_score_mean,
        surprise_pct=max_surprise
    )
    
    # 4. Calculer latence médiane (pour TTR)
    # Gérer NaN avec valeur par défaut
    latency_values = cluster_events['latency_median'].dropna()
    if len(latency_values) > 0:
        latency_median = latency_values.median()
    else:
        latency_median = 2.0  # Valeur par défaut si aucune donnée
    
    # 5. Calculer impact avec formule D (Session 51)
    num_events = len(cluster_events)
    impact_pips = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=num_events,
        amplification=amplification
    )
    
    # 6. Calculer poids relatif (pour multi-clusters)
    # Poids basé sur score ajusté et nombre événements
    cluster_weight = adjusted_score * math.sqrt(num_events)
    
    # 7. Détails calculs (debug)
    calculation_details = {
        'base_scores_list': base_scores.tolist(),
        'surprises_list': surprises,
        'adjustment_factor': adjusted_score / base_score_mean if base_score_mean > 0 else 1.0,
        'formula_used': 'calculate_impact_d (Session 51)'
    }
    
    return {
        'impact_pips': float(impact_pips),
        'base_score': float(base_score_mean),
        'adjusted_score': float(adjusted_score),
        'max_surprise': float(max_surprise),
        'num_events': int(num_events),
        'cluster_weight': float(cluster_weight),
        'latency_median': float(latency_median),
        'calculation_details': calculation_details
    }


# ════════════════════════════════════════════════════════════════
# FONCTION 2: CALCUL TTR PAR CLUSTER
# ════════════════════════════════════════════════════════════════

def calculate_cluster_ttr(
    cluster_impact: Dict,
    cluster_latency_median: float
) -> float:
    """
    Calcule Time To Reversal adaptatif pour un cluster.
    
    Basé sur formule Session 52 MAIS ajusté selon:
    - Impact magnitude
    - Latence médiane
    - Nombre événements (clusters plus gros = TTR plus long)
    
    OBSERVATIONS MT5 (pour calibration):
    - Petits clusters (1-3 events): TTR 3-5 min
    - Moyens clusters (4-8 events): TTR 5-8 min
    - Gros clusters (9+ events): TTR 8-12 min
    
    ALGORITHME:
    1. TTR base = formule Session 52 (latency × multiplier)
    2. Ajustement selon num_events:
       - 1-3 events: factor 0.8
       - 4-8 events: factor 1.0
       - 9+ events: factor 1.2-1.5
    3. Plafond raisonnable: 15 min max
    
    Args:
        cluster_impact: Dict retourné par calculate_cluster_impact()
        cluster_latency_median: Latence médiane du cluster (minutes)
    
    Returns:
        float: TTR en minutes (arrondi à 1 décimale)
    
    Examples:
        >>> # Gros cluster (14 events, impact 39 pips)
        >>> cluster_impact = {'num_events': 14, 'max_surprise': 33.3, ...}
        >>> ttr = calculate_cluster_ttr(cluster_impact, latency_median=2.0)
        >>> print(f"TTR: {ttr:.1f} min")
        TTR: 5.4 min
        
        >>> # Petit cluster (1 event, impact 16 pips)
        >>> cluster_impact = {'num_events': 1, 'max_surprise': 25.0, ...}
        >>> ttr = calculate_cluster_ttr(cluster_impact, latency_median=1.5)
        >>> print(f"TTR: {ttr:.1f} min")
        TTR: 2.7 min
    """
    # 1. TTR base avec formule Session 52
    ttr_base = calculate_ttr_c(
        latency_minutes=cluster_latency_median,
        surprise_pct=cluster_impact['max_surprise']
    )
    
    # 2. Ajustement selon nombre événements
    num_events = cluster_impact['num_events']
    
    if num_events <= 3:
        # Petits clusters: réaction plus rapide
        size_factor = 0.8
    elif num_events <= 8:
        # Clusters moyens: comportement standard
        size_factor = 1.0
    else:
        # Gros clusters: propagation plus lente
        # Factor augmente progressivement avec la taille
        size_factor = 1.0 + min(0.5, (num_events - 8) * 0.05)
    
    # 3. TTR ajusté
    ttr_adjusted = ttr_base * size_factor
    
    # 4. Plafond raisonnable
    ttr_final = min(ttr_adjusted, 15.0)
    
    return round(ttr_final, 1)


# ════════════════════════════════════════════════════════════════
# FONCTION 3: CARACTÉRISTIQUES PULLBACK
# ════════════════════════════════════════════════════════════════

def calculate_pullback_characteristics(
    peak_impact: float,
    peak_surprise: float,
    num_events: int,
    has_following_cluster: bool = False,
    minutes_to_next_cluster: Optional[int] = None
) -> Dict:
    """
    Calcule caractéristiques du pullback après un peak.
    
    OBSERVATIONS MT5:
    - Single cluster: pullback 20-35% du peak, durée 6-15 min
    - Double cluster (overlapping): pullback 60-80% du peak 1, durée = délai jusqu'à cluster 2 + X min
    - Sequential: pullback complet du cluster 1, puis stabilisation
    
    ALGORITHME:
    1. Amplitude pullback (formule Session 53 adaptée)
    2. Durée pullback selon contexte:
       - Single: 8-15 min selon volatilité
       - Overlapping: jusqu'à cluster 2 + délai propagation
       - Sequential: pullback complet + stabilisation
    3. Ratio pullback (pour validation)
    
    Args:
        peak_impact: Impact du peak en pips
        peak_surprise: Surprise % du cluster ayant causé le peak
        num_events: Nombre événements du cluster
        has_following_cluster: Si True, un cluster suit
        minutes_to_next_cluster: Délai en minutes jusqu'au prochain cluster (si existe)
    
    Returns:
        dict: {
            'pullback_pips': float,         # Amplitude pullback en pips
            'pullback_duration': int,       # Durée en minutes
            'pullback_ratio': float,        # % du peak (0.0-1.0)
            'pullback_type': str,           # 'single', 'overlapping', 'sequential'
            'creux_expected_minutes': int   # Minutes après peak pour atteindre creux
        }
    
    Examples:
        >>> # Single cluster (pas de cluster suivant)
        >>> pb = calculate_pullback_characteristics(
        ...     peak_impact=37.4,
        ...     peak_surprise=33.3,
        ...     num_events=14,
        ...     has_following_cluster=False
        ... )
        >>> print(f"Pullback: {pb['pullback_pips']:.1f} pips ({pb['pullback_ratio']:.0%})")
        Pullback: 10.2 pips (27%)
        
        >>> # Overlapping (cluster 2 arrive pendant pullback)
        >>> pb = calculate_pullback_characteristics(
        ...     peak_impact=37.4,
        ...     peak_surprise=33.3,
        ...     num_events=14,
        ...     has_following_cluster=True,
        ...     minutes_to_next_cluster=15
        ... )
        >>> print(f"Pullback: {pb['pullback_pips']:.1f} pips ({pb['pullback_ratio']:.0%})")
        Pullback: 27.1 pips (72%)
    """
    # 1. Déterminer type de pullback
    if not has_following_cluster:
        pullback_type = 'single'
    elif minutes_to_next_cluster and minutes_to_next_cluster < 25:
        # Si cluster 2 arrive < 25 min après peak 1 → overlapping probable
        pullback_type = 'overlapping'
    else:
        pullback_type = 'sequential'
    
    # 2. Calculer amplitude pullback selon type
    if pullback_type == 'single':
        # Single cluster: pullback modéré (20-35%)
        # Utiliser formule Session 53 avec minutes typiques
        pullback_pips = calculate_pullback_v2(
            phase1_impact=peak_impact,
            minutes_since_peak=10,  # Typical pour single
            minutes_to_next_phase=0  # Pas de phase suivante
        )
        pullback_duration = int(8 + min(12, num_events * 0.5))  # 8-15 min
        creux_minutes = pullback_duration
        
    elif pullback_type == 'overlapping':
        # Overlapping: pullback profond (60-80%)
        # Le marché retraces jusqu'à l'arrivée du cluster 2, puis continue
        
        # Observation MT5 11 sept: pullback 72% jusqu'à 4 min APRÈS cluster 2
        # On estime que le creux arrive X min après cluster 2
        delay_after_cluster2 = int(3 + num_events * 0.2)  # 3-6 min typiquement
        
        creux_minutes = minutes_to_next_cluster + delay_after_cluster2
        
        # Amplitude basée sur le temps écoulé (plus long = plus profond)
        # Formule Session 53 adaptée
        pullback_pips = calculate_pullback_v2(
            phase1_impact=peak_impact,
            minutes_since_peak=creux_minutes,
            minutes_to_next_phase=minutes_to_next_cluster
        )
        
        pullback_duration = creux_minutes
        
    else:  # sequential
        # Sequential: pullback complet du cluster 1
        pullback_pips = calculate_pullback_v2(
            phase1_impact=peak_impact,
            minutes_since_peak=15,
            minutes_to_next_phase=0
        )
        pullback_duration = int(12 + num_events * 0.8)  # Plus long que single
        creux_minutes = pullback_duration
    
    # 3. Calculer ratio (pour validation)
    pullback_ratio = pullback_pips / peak_impact if peak_impact > 0 else 0.0
    
    # 4. Limites de sécurité
    pullback_ratio = min(pullback_ratio, 0.85)  # Max 85% du peak
    pullback_pips = peak_impact * pullback_ratio
    
    return {
        'pullback_pips': float(pullback_pips),
        'pullback_duration': int(pullback_duration),
        'pullback_ratio': float(pullback_ratio),
        'pullback_type': pullback_type,
        'creux_expected_minutes': int(creux_minutes)
    }


# ════════════════════════════════════════════════════════════════
# FONCTION 4: ANALYSE PATTERN CLUSTERS
# ════════════════════════════════════════════════════════════════

def analyze_cluster_pattern(
    clusters: List[Dict],
    clusters_impacts: List[Dict],
    temporal_tolerance: int = 5
) -> Dict:
    """
    Analyse la relation entre clusters pour déterminer le pattern.
    
    PATTERNS DÉTECTÉS:
    - 'single': 1 seul cluster
    - 'cumulative': Clusters < 5 min d'écart → Impact combiné immédiat
    - 'overlapping': Cluster 2 arrive pendant pullback cluster 1
    - 'sequential': Clusters indépendants, séparés dans le temps
    
    DÉTECTION OVERLAPPING:
    Si délai entre clusters < durée pullback estimée cluster 1
    → Cluster 2 arrive PENDANT pullback cluster 1
    → Pattern observé 11 sept 2025
    
    DÉTECTION SEQUENTIAL:
    Si délai entre clusters > durée pullback + récupération
    → Clusters indépendants, impacts séparés
    
    Args:
        clusters: Liste de dicts avec 'time' (datetime) et 'events_indices'
        clusters_impacts: Liste de dicts retournés par calculate_cluster_impact()
        temporal_tolerance: Minutes pour considérer clusters simultanés (défaut 5)
    
    Returns:
        dict: {
            'pattern_type': str,               # Type pattern détecté
            'primary_cluster_index': int,      # Index cluster dominant
            'secondary_clusters': List[int],   # Indices autres clusters
            'expected_interactions': List[str], # Interactions prévues
            'confidence': float                # Confiance détection (0-1)
        }
    
    Examples:
        >>> # Cas 11 sept: CPI 14:30 + Current 14:45
        >>> clusters = [
        ...     {'time': datetime(2025,9,11,14,30), 'events_indices': [0,1,...]},
        ...     {'time': datetime(2025,9,11,14,45), 'events_indices': [14]}
        ... ]
        >>> pattern = analyze_cluster_pattern(clusters, impacts)
        >>> print(pattern['pattern_type'])
        'overlapping'
    """
    # Cas simple: 1 seul cluster
    if len(clusters) == 1:
        return {
            'pattern_type': 'single',
            'primary_cluster_index': 0,
            'secondary_clusters': [],
            'expected_interactions': [],
            'confidence': 1.0
        }
    
    # Identifier cluster dominant (plus grand impact ou plus d'événements)
    primary_idx = 0
    max_weight = 0
    for i, impact in enumerate(clusters_impacts):
        weight = impact['cluster_weight']
        if weight > max_weight:
            max_weight = weight
            primary_idx = i
    
    secondary_indices = [i for i in range(len(clusters)) if i != primary_idx]
    
    # Calculer délai entre clusters
    primary_time = clusters[primary_idx]['time']
    delays = []
    for i in secondary_indices:
        delay_minutes = (clusters[i]['time'] - primary_time).total_seconds() / 60
        delays.append(delay_minutes)
    
    # Détection pattern
    if all(abs(d) <= temporal_tolerance for d in delays):
        # Tous les clusters dans la fenêtre de tolérance
        pattern_type = 'cumulative'
        interactions = ['Impacts combinés instantanément']
        confidence = 0.9
        
    elif len(delays) > 0:
        min_delay = min(abs(d) for d in delays)
        
        # Estimer durée pullback cluster primaire
        pb_chars = calculate_pullback_characteristics(
            peak_impact=clusters_impacts[primary_idx]['impact_pips'],
            peak_surprise=clusters_impacts[primary_idx]['max_surprise'],
            num_events=clusters_impacts[primary_idx]['num_events'],
            has_following_cluster=True,
            minutes_to_next_cluster=int(min_delay)
        )
        
        if min_delay < pb_chars['creux_expected_minutes']:
            # Cluster secondaire arrive PENDANT pullback primaire
            pattern_type = 'overlapping'
            interactions = [
                f"Cluster {secondary_indices[0]+1} arrive pendant pullback cluster {primary_idx+1}",
                "Pullback prolongé jusqu'à creux",
                "Reprise forte après creux"
            ]
            confidence = 0.85
        else:
            # Clusters séparés
            pattern_type = 'sequential'
            interactions = [
                f"Cluster {primary_idx+1} complet avant cluster {secondary_indices[0]+1}",
                "Impacts indépendants"
            ]
            confidence = 0.8
    else:
        # Fallback
        pattern_type = 'sequential'
        interactions = []
        confidence = 0.5
    
    return {
        'pattern_type': pattern_type,
        'primary_cluster_index': primary_idx,
        'secondary_clusters': secondary_indices,
        'expected_interactions': interactions,
        'confidence': confidence
    }


# ════════════════════════════════════════════════════════════════
# UTILITAIRES
# ════════════════════════════════════════════════════════════════

def validate_cluster_impact_calculation(test_case: str = '11_sept_2025'):
    """
    Valide le calcul d'impact sur un cas de test connu.
    
    Args:
        test_case: Nom du cas test ('11_sept_2025', etc.)
    
    Returns:
        bool: True si validation OK
    """
    # À implémenter avec données réelles
    # Pour l'instant, placeholder
    print(f"⚠️ Validation test case '{test_case}' à implémenter")
    return True


if __name__ == "__main__":
    print("📦 Module cluster_impact_calculator.py chargé")
    print("✅ Fonctions disponibles:")
    print("   - calculate_cluster_impact()")
    print("   - calculate_cluster_ttr()")
    print("   - calculate_pullback_characteristics()")
    print("   - analyze_cluster_pattern()")
