"""
Core Calculations Module - EUR/USD Impact Calculator

Ce module contient les fonctions de calcul d'impact des événements macro.
Version migrée et refactorisée depuis forecaster_mvp.py

Auteur : Session 29 (Migration clean)
Date : 22 octobre 2025
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


# ============================================================================
# CALCUL STATISTIQUES FAMILLE D'ÉVÉNEMENTS
# ============================================================================

def calculate_family_stats(
    conn,
    family_pattern: str,
    horizon_minutes: int = 30,
    hist_years: int = 3,
    countries: Optional[List[str]] = None,
    timeframe: str = '1m'
) -> Dict:
    """
    Calcule toutes les statistiques d'impact pour une famille d'événements.
    
    Args:
        conn: Connexion DuckDB
        family_pattern: Pattern regex pour identifier la famille (ex: 'CPI|Consumer Price')
        horizon_minutes: Horizon temporel pour calculer l'impact (défaut: 30 min)
        hist_years: Nombre d'années d'historique à analyser (défaut: 3 ans)
        countries: Liste des pays à inclure (défaut: ['US'])
        timeframe: Timeframe des prix ('1m', '5m', etc.)
    
    Returns:
        Dict contenant:
            - family: Nom de la famille
            - n_events: Nombre d'événements analysés
            - horizon_min: Horizon utilisé
            - p_up: Probabilité mouvement haussier
            - p_down: Probabilité mouvement baissier
            - mfe_median, mfe_p80, mfe_p90, mfe_mean, mfe_std: Stats MFE
            - latency_median, latency_p20, latency_p80, latency_mean: Stats latence
            - ttr_median, ttr_p20, ttr_p80, ttr_mean: Stats Time-To-Reversal
            - timeframe, countries, hist_years: Paramètres utilisés
    
    Example:
        >>> stats = calculate_family_stats(
        ...     conn, 
        ...     family_pattern='CPI|Consumer Price',
        ...     horizon_minutes=60,
        ...     countries=['US', 'EU']
        ... )
        >>> print(f"MFE médian: {stats['mfe_median']:.2f} pips")
    """
    if countries is None:
        countries = ['US']
    
    # Date de début pour l'historique
    cutoff_date = datetime.utcnow() - timedelta(days=hist_years * 365)
    country_filter = "', '".join(countries)
    
    # Récupérer les événements correspondant au pattern
    query_events = f"""
    SELECT ts_utc, event_key, country, importance_n
    FROM events
    WHERE ts_utc >= '{cutoff_date.strftime('%Y-%m-%d')}'
      AND country IN ('{country_filter}')
      AND event_key ~ '{family_pattern}'
    ORDER BY ts_utc
    """
    
    events_df = conn.execute(query_events).fetchdf()
    
    if len(events_df) == 0:
        return _empty_stats(family_pattern)
    
    # Calculer les stats pour chaque événement
    all_impacts = []
    all_latencies = []
    all_ttrs = []
    directions = []
    
    for _, event in events_df.iterrows():
        stats = calculate_single_event_impact(
            conn=conn,
            event_ts=event['ts_utc'],
            horizon_minutes=horizon_minutes,
            timeframe=timeframe
        )
        
        if stats is not None:
            all_impacts.append(stats['mfe'])
            all_latencies.append(stats['latency'])
            all_ttrs.append(stats['ttr'])
            directions.append(stats['direction'])
    
    if len(all_impacts) == 0:
        return _empty_stats(family_pattern)
    
    # Convertir en arrays numpy pour calculs
    all_impacts = np.array(all_impacts)
    all_latencies = np.array(all_latencies)
    all_ttrs = np.array(all_ttrs)
    directions = np.array(directions)
    
    # Retourner statistiques agrégées
    return {
        'family': family_pattern,
        'n_events': len(all_impacts),
        'horizon_min': horizon_minutes,
        'p_up': float(np.mean(directions > 0)),
        'p_down': float(np.mean(directions < 0)),
        'mfe_median': float(np.median(all_impacts)),
        'mfe_p80': float(np.percentile(all_impacts, 80)),
        'mfe_p90': float(np.percentile(all_impacts, 90)),
        'mfe_mean': float(np.mean(all_impacts)),
        'mfe_std': float(np.std(all_impacts)),
        'latency_median': float(np.median(all_latencies)),
        'latency_p20': float(np.percentile(all_latencies, 20)),
        'latency_p80': float(np.percentile(all_latencies, 80)),
        'latency_mean': float(np.mean(all_latencies)),
        'ttr_median': float(np.median(all_ttrs)),
        'ttr_p20': float(np.percentile(all_ttrs, 20)),
        'ttr_p80': float(np.percentile(all_ttrs, 80)),
        'ttr_mean': float(np.mean(all_ttrs)),
        'timeframe': timeframe,
        'countries': countries,
        'hist_years': hist_years
    }


def calculate_single_event_impact(
    conn,
    event_ts: datetime,
    horizon_minutes: int = 30,
    timeframe: str = '1m'
) -> Optional[Dict]:
    """
    Calcule MFE, latence et TTR pour un événement unique.
    
    Args:
        conn: Connexion DuckDB
        event_ts: Timestamp de l'événement
        horizon_minutes: Horizon temporel (défaut: 30 min)
        timeframe: Timeframe des prix ('1m', '5m', etc.)
    
    Returns:
        Dict contenant:
            - mfe: Maximum Favorable Excursion en pips (absolu)
            - latency: Temps en minutes avant mouvement ≥5 pips
            - ttr: Time-To-Reversal en minutes
            - direction: +1 (haussier) ou -1 (baissier)
        
        None si données insuffisantes
    
    Notes:
        - MFE = max(|mouvement|) sur l'horizon
        - Latence = temps avant premier mouvement ≥5 pips
        - TTR = temps avant retour à 50% du pic
        - Direction = sentiment dominant sur la période
    
    Example:
        >>> impact = calculate_single_event_impact(
        ...     conn,
        ...     event_ts=datetime(2025, 9, 11, 14, 30),
        ...     horizon_minutes=60
        ... )
        >>> print(f"MFE: {impact['mfe']:.2f} pips")
        >>> print(f"Latence: {impact['latency']:.1f} min")
    """
    # Normaliser le timestamp (enlever timezone info si présente)
    if hasattr(event_ts, 'tz_localize'):
        event_ts_naive = event_ts.tz_localize(None) if event_ts.tzinfo else event_ts
    else:
        event_ts_naive = pd.Timestamp(event_ts).tz_localize(None) if pd.Timestamp(event_ts).tzinfo else pd.Timestamp(event_ts)
    
    # 1. Obtenir le prix de référence (juste avant l'événement)
    query_ref = f"""
    SELECT close as ref_price
    FROM prices_{timeframe}_v
    WHERE ts_utc < '{event_ts_naive}'
    ORDER BY ts_utc DESC
    LIMIT 1
    """
    
    ref_result = conn.execute(query_ref).fetchdf()
    if len(ref_result) == 0:
        return None
    
    ref_price = ref_result['ref_price'].iloc[0]
    end_ts_naive = event_ts_naive + timedelta(minutes=horizon_minutes)
    
    # 2. Récupérer les prix sur l'horizon
    query_prices = f"""
    SELECT ts_utc, close, (close - {ref_price}) * 10000 as pips
    FROM prices_{timeframe}_v
    WHERE ts_utc >= '{event_ts_naive}' AND ts_utc <= '{end_ts_naive}'
    ORDER BY ts_utc
    """
    
    prices_df = conn.execute(query_prices).fetchdf()
    
    if len(prices_df) < 3:
        return None
    
    # Normaliser les timestamps
    prices_df['ts_utc'] = pd.to_datetime(prices_df['ts_utc']).dt.tz_localize(None)
    
    pips = prices_df['pips'].values
    
    # 3. Calculer MFE et direction
    mfe = float(np.max(np.abs(pips)))
    direction = 1 if np.sum(pips > 0) > np.sum(pips < 0) else -1
    
    # 4. Calculer latence (temps avant mouvement ≥5 pips)
    latency_minutes = calculate_latency(
        prices_df=prices_df,
        event_ts=event_ts_naive,
        threshold_pips=5.0,
        default_latency=horizon_minutes
    )
    
    # 5. Calculer TTR (Time-To-Reversal)
    ttr_minutes = calculate_ttr(
        prices_df=prices_df,
        event_ts=event_ts_naive,
        pips=pips,
        default_ttr=horizon_minutes
    )
    
    return {
        'mfe': mfe,
        'latency': latency_minutes,
        'ttr': ttr_minutes,
        'direction': direction
    }


# ============================================================================
# CALCUL LATENCE
# ============================================================================

def calculate_latency(
    prices_df: pd.DataFrame,
    event_ts: datetime,
    threshold_pips: float = 5.0,
    default_latency: float = 30.0
) -> float:
    """
    Calcule la latence : temps en minutes avant un mouvement significatif.
    
    Args:
        prices_df: DataFrame avec colonnes 'ts_utc' et 'pips'
        event_ts: Timestamp de l'événement
        threshold_pips: Seuil de mouvement en pips (défaut: 5.0)
        default_latency: Latence par défaut si seuil jamais atteint
    
    Returns:
        Latence en minutes (float)
    
    Example:
        >>> latency = calculate_latency(
        ...     prices_df=df,
        ...     event_ts=datetime(2025, 9, 11, 14, 30),
        ...     threshold_pips=5.0
        ... )
        >>> print(f"Latence: {latency:.1f} minutes")
    """
    latency_minutes = default_latency
    
    for idx, row in prices_df.iterrows():
        pip_val = row['pips']
        if abs(pip_val) >= threshold_pips:
            time_diff = row['ts_utc'] - event_ts
            latency_minutes = time_diff.total_seconds() / 60.0
            break
    
    return float(latency_minutes)


# ============================================================================
# CALCUL TIME-TO-REVERSAL (TTR)
# ============================================================================

def calculate_ttr(
    prices_df: pd.DataFrame,
    event_ts: datetime,
    pips: np.ndarray,
    reversal_threshold: float = 0.5,
    default_ttr: float = 30.0
) -> float:
    """
    Calcule le Time-To-Reversal : temps avant retour de 50% du pic.
    
    Args:
        prices_df: DataFrame avec colonne 'ts_utc'
        event_ts: Timestamp de l'événement
        pips: Array numpy des mouvements en pips
        reversal_threshold: Seuil de reversal (0.5 = 50% du pic)
        default_ttr: TTR par défaut si pas de reversal détecté
    
    Returns:
        TTR en minutes (float)
    
    Logic:
        1. Identifier le pic (max absolu)
        2. Chercher après le pic un mouvement < 50% du pic ET de signe opposé
        3. Calculer le temps entre événement et reversal
    
    Example:
        >>> ttr = calculate_ttr(
        ...     prices_df=df,
        ...     event_ts=datetime(2025, 9, 11, 14, 30),
        ...     pips=np.array([0, 5, 10, 15, 8, 3, -2]),
        ...     reversal_threshold=0.5
        ... )
        >>> print(f"TTR: {ttr:.1f} minutes")
    """
    ttr_minutes = default_ttr
    
    # Identifier le pic
    peak_idx = np.argmax(np.abs(pips))
    peak_value = pips[peak_idx]
    threshold = abs(peak_value) * reversal_threshold
    
    # Chercher le reversal après le pic
    for idx in range(peak_idx + 1, len(pips)):
        current_pips = pips[idx]
        
        # Critères de reversal:
        # 1. Mouvement < threshold (50% du pic)
        # 2. Signe opposé au pic
        if abs(current_pips) < threshold and np.sign(current_pips) != np.sign(peak_value):
            time_diff = prices_df.iloc[idx]['ts_utc'] - event_ts
            ttr_minutes = time_diff.total_seconds() / 60.0
            break
    
    return float(ttr_minutes)


# ============================================================================
# PRÉDICTION IMPACT (Formule v9-CLEAN)
# ============================================================================

def predict_impact_v9_clean(
    empirical_score: float,
    num_events: int = 1
) -> Optional[float]:
    """
    Prédit l'impact en pips avec la formule v9-CLEAN (Session 9).
    
    Args:
        empirical_score: Score empirique 0-100 basé sur historique
        num_events: Nombre d'événements simultanés dans la fenêtre
    
    Returns:
        Impact prédit en pips (float)
        None si score est None
    
    Formules:
        - 1 événement seul:
          Impact = -7.08 + 0.419 × score
        
        - ≥2 événements groupés:
          Impact = -10.47 + 0.477 × score
    
    Métriques (Session 9):
        - R² = 0.264
        - MAE = 6.68 pips
        - Dataset: 2,087 groupes (2024-2025)
    
    Examples:
        >>> # 11 septembre 2025: 6 événements, score 81.7
        >>> predict_impact_v9_clean(81.7, 6)
        28.576
        
        >>> # Événement seul, score moyen
        >>> predict_impact_v9_clean(50, 1)
        13.87
        
        >>> # Score NULL
        >>> predict_impact_v9_clean(None, 1)
        None
    
    Notes:
        - Cette formule utilise le score empirique composite (0-100)
        - Le score combine MFE, surprise, importance
        - Validée sur données 2024-2025
        - Meilleure performance que formules précédentes (v8.7)
    """
    if empirical_score is None:
        return None
    
    if num_events >= 2:
        # Formule v9-MULTI (événements groupés)
        return -10.47 + 0.477 * empirical_score
    else:
        # Formule v9-CLEAN (événement seul)
        return -7.08 + 0.419 * empirical_score


# ============================================================================
# CALCUL STATISTIQUES MULTIPLES FAMILLES
# ============================================================================

def calculate_multiple_families(
    conn,
    family_patterns: Dict[str, str],
    horizon_minutes: int = 30,
    hist_years: int = 3,
    countries: Optional[List[str]] = None
) -> Dict[str, Dict]:
    """
    Calcule les statistiques pour plusieurs familles d'événements.
    
    Args:
        conn: Connexion DuckDB
        family_patterns: Dict {nom_famille: pattern_regex}
        horizon_minutes: Horizon temporel (défaut: 30 min)
        hist_years: Historique en années (défaut: 3 ans)
        countries: Liste des pays (défaut: ['US'])
    
    Returns:
        Dict {nom_famille: stats_dict}
    
    Example:
        >>> patterns = {
        ...     'CPI': 'CPI|Consumer Price',
        ...     'GDP': 'GDP|Gross Domestic',
        ...     'Employment': 'Employment|Nonfarm|Unemployment'
        ... }
        >>> results = calculate_multiple_families(conn, patterns)
        >>> for family, stats in results.items():
        ...     print(f"{family}: {stats['n_events']} événements")
    """
    results = {}
    
    for family_name, pattern in family_patterns.items():
        results[family_name] = calculate_family_stats(
            conn=conn,
            family_pattern=pattern,
            horizon_minutes=horizon_minutes,
            hist_years=hist_years,
            countries=countries
        )
    
    return results


# ============================================================================
# UTILITAIRES
# ============================================================================

def _empty_stats(family_pattern: str) -> Dict:
    """
    Retourne un dictionnaire de statistiques vides.
    
    Utilisé quand aucun événement n'est trouvé pour une famille.
    """
    return {
        'family': family_pattern,
        'n_events': 0,
        'horizon_min': 0,
        'p_up': 0.0,
        'p_down': 0.0,
        'mfe_median': 0.0,
        'mfe_p80': 0.0,
        'mfe_p90': 0.0,
        'mfe_mean': 0.0,
        'mfe_std': 0.0,
        'latency_median': 0.0,
        'latency_p20': 0.0,
        'latency_p80': 0.0,
        'latency_mean': 0.0,
        'ttr_median': 0.0,
        'ttr_p20': 0.0,
        'ttr_p80': 0.0,
        'ttr_mean': 0.0
    }
