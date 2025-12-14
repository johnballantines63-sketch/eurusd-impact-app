#!/usr/bin/env python3
"""
Pattern Labeler M1 - Labellisation de Patterns depuis Prix M1
==============================================================

Module pour labelliser les patterns de prix réels depuis données M1.
Version V4 empirique.

Usage:
    from research.pattern_labeler_m1 import label_day, PatternConfig
    
    config = PatternConfig()
    result = label_day('2025-08-01', conn, config=config)
    print(result['pattern_label'])
"""

import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime, timedelta
import duckdb
import pandas as pd
import numpy as np


@dataclass
class PatternConfig:
    """
    Configuration paramétrable pour la labellisation de patterns.
    Tous les seuils sont explicites (pas de magic numbers).
    """
    # Fenêtre prix
    window_before_minutes: int = 15  # Minutes avant t0
    window_after_minutes: int = 180  # Minutes après t0
    max_minutes: int = 180  # Limite max pour t_end
    
    # Lissage prix
    smoothing_window: int = 5  # Rolling median window (3 ou 5 points)
    
    # Détection direction initiale
    direction_window_minutes: int = 5  # Fenêtre pour calculer direction [t0, t0+5min]
    
    # Détection double wave
    retracement_threshold_pct: float = 0.20  # 20% minimum pour retracement significatif
    breakout_pips: float = 10.0  # Pips minimum pour breakout au-dessus peak1
    
    # Détection zigzag
    min_swings: int = 2  # Nombre minimum d'alternances directionnelles
    swing_threshold_pips: float = 15.0  # Seuil pour swing significatif
    
    # Règles de fin (t_end)
    end_reversal_pips: float = 20.0  # Retracement depuis MFE pour considérer fin
    stabilization_band_pips: float = 5.0  # Bande de stabilisation
    stabilization_minutes: int = 15  # Durée stabilisation
    
    # Kernel events (filtre pour identifier t0)
    kernel_country: Optional[str] = 'US'  # Filtrer pays pour kernel
    kernel_importance_min: Optional[int] = None  # Importance minimum (si disponible)
    kernel_window_start_local: str = '13:00:00'  # Heure début fenêtre kernel
    kernel_window_end_local: str = '16:00:00'  # Heure fin fenêtre kernel


def normalize_title(text: str) -> str:
    """Normalise un titre pour matching."""
    if pd.isna(text):
        return ""
    import re
    return re.sub(r'[^a-z0-9 ]', '', str(text).lower()).strip()


def _select_kernel_events(
    df_events: pd.DataFrame,
    config: PatternConfig,
    date_str: str
) -> Tuple[pd.DataFrame, Optional[datetime], List[str]]:
    """
    Sélectionne les événements kernel et détermine t0.
    
    Args:
        df_events: DataFrame avec colonnes ts_local, country, event_key, importance_n
        config: Configuration
        date_str: Date au format 'YYYY-MM-DD'
    
    Returns:
        tuple (kernel_df, t0, kernel_keys):
        - kernel_df: DataFrame des événements kernel (ts_local ∈ [t0, t0+60s])
        - t0: Timestamp du premier événement déclencheur (datetime ou None)
        - kernel_keys: Liste des event_keys uniques du kernel
    
    Logique:
    1. Trier df_events par ts_local
    2. Appliquer filtres (pays, importance, fenêtre horaire)
    3. Déterminer t0 = premier événement filtré
    4. Sélectionner événements dans [t0, t0+60 secondes]
    5. Extraire kernel_keys uniques
    """
    if df_events.empty:
        return pd.DataFrame(), None, []
    
    df = df_events.copy()
    df['ts_local'] = pd.to_datetime(df['ts_local'])
    df = df.sort_values('ts_local')
    
    # Appliquer filtres pour trouver t0
    df_filtered = df.copy()
    
    # Filtre 1: pays
    if config.kernel_country:
        df_filtered = df_filtered[df_filtered['country'] == config.kernel_country]
    
    # Filtre 2: importance
    if config.kernel_importance_min is not None and 'importance_n' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['importance_n'] >= config.kernel_importance_min]
    
    # Filtre 3: fenêtre horaire locale
    if config.kernel_window_start_local and config.kernel_window_end_local:
        date_obj = pd.to_datetime(date_str).date()
        window_start = pd.to_datetime(f"{date_str} {config.kernel_window_start_local}").time()
        window_end = pd.to_datetime(f"{date_str} {config.kernel_window_end_local}").time()
        
        df_filtered['time_local'] = df_filtered['ts_local'].dt.time
        df_filtered = df_filtered[
            (df_filtered['time_local'] >= window_start) &
            (df_filtered['time_local'] <= window_end)
        ]
    
    # Déterminer t0
    if df_filtered.empty:
        # Fallback: premier événement de la journée
        warnings.warn(f"Aucun événement kernel trouvé pour {date_str}, utilisation premier événement")
        if not df.empty:
            t0 = pd.to_datetime(df.iloc[0]['ts_local'])
        else:
            return pd.DataFrame(), None, []
    else:
        # Prendre le premier (plus tôt)
        t0 = pd.to_datetime(df_filtered.iloc[0]['ts_local'])
    
    t0_dt = t0.to_pydatetime()
    
    # Sélectionner événements dans [t0, t0+60 secondes]
    t0_end = t0 + timedelta(seconds=60)
    kernel_df = df[
        (df['ts_local'] >= t0) &
        (df['ts_local'] <= t0_end)
    ].copy()
    
    # Extraire kernel_keys uniques
    kernel_keys = kernel_df['event_key'].dropna().unique().tolist()
    if not kernel_keys:
        kernel_keys = []
    
    return kernel_df, t0_dt, kernel_keys


def find_t0_kernel(
    df_events: pd.DataFrame,
    config: PatternConfig,
    date_str: str
) -> Optional[datetime]:
    """
    Identifie t0: premier événement "kernel".
    
    NOTE: Cette fonction est maintenue pour compatibilité.
    Utiliser _select_kernel_events() pour obtenir aussi kernel_keys.
    
    Stratégie:
    1. Filtrer par pays si config.kernel_country
    2. Filtrer par importance si config.kernel_importance_min
    3. Filtrer par fenêtre horaire locale [kernel_window_start, kernel_window_end]
    4. Prendre le premier événement filtré
    5. Sinon: premier événement de la journée
    """
    _, t0, _ = _select_kernel_events(df_events, config, date_str)
    return t0


def load_prices_m1(
    conn: duckdb.DuckDBPyConnection,
    t0: datetime,
    config: PatternConfig
) -> pd.DataFrame:
    """
    Charge les prix M1 sur fenêtre [t0-window_before, t0+window_after].
    
    Note: prices_finnhub_m1 utilise colonne 'datetime' (pas ts_utc) et est en UTC.
    """
    t0_utc = pd.to_datetime(t0).tz_localize(None)  # Convertir en UTC si nécessaire
    
    start_utc = t0_utc - timedelta(minutes=config.window_before_minutes)
    end_utc = t0_utc + timedelta(minutes=config.window_after_minutes)
    
    query = """
        SELECT datetime, close, high, low
        FROM prices_finnhub_m1
        WHERE datetime >= CAST(? AS TIMESTAMP)
          AND datetime <= CAST(? AS TIMESTAMP)
        ORDER BY datetime
    """
    
    df = conn.execute(query, [start_utc, end_utc]).df()
    
    if df.empty:
        warnings.warn(f"Aucun prix M1 trouvé pour fenêtre [{start_utc}, {end_utc}]")
        return pd.DataFrame()
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df


def smooth_prices(prices_series: pd.Series, window: int) -> pd.Series:
    """Lisse les prix avec rolling median."""
    return prices_series.rolling(window=window, center=True, min_periods=1).median()


def calculate_direction_initial(
    prices_df: pd.DataFrame,
    t0: datetime,
    config: PatternConfig
) -> int:
    """
    Calcule la direction initiale sur [t0, t0+direction_window_minutes].
    
    Returns:
        +1 si hausse, -1 si baisse, 0 si indéterminé
    """
    prices_after = prices_df[prices_df['datetime'] >= pd.to_datetime(t0)].copy()
    if prices_after.empty:
        return 0
    
    window_end = pd.to_datetime(t0) + timedelta(minutes=config.direction_window_minutes)
    window_prices = prices_after[prices_after['datetime'] <= window_end]
    
    if len(window_prices) < 2:
        return 0
    
    delta = window_prices['close'].iloc[-1] - window_prices['close'].iloc[0]
    return 1 if delta > 0 else (-1 if delta < 0 else 0)


def calculate_mfe_mae(
    prices_df: pd.DataFrame,
    t0: datetime,
    direction: int,
    baseline_price: float
) -> Dict[str, float]:
    """
    Calcule MFE (Max Favorable Excursion) et MAE (Max Adverse Excursion).
    
    Args:
        prices_df: DataFrame avec colonnes datetime, close
        t0: Timestamp événement
        direction: +1 (hausse attendue) ou -1 (baisse attendue)
        baseline_price: Prix de référence (juste avant t0)
    
    Returns:
        Dict avec MFE_pips, MAE_pips, time_to_peak_min
    """
    prices_after = prices_df[prices_df['datetime'] >= pd.to_datetime(t0)].copy()
    
    if prices_after.empty:
        return {
            'MFE_pips': 0.0,
            'MAE_pips': 0.0,
            'time_to_peak_min': 0.0
        }
    
    # Calculer mouvements en pips
    prices_after['pips_from_baseline'] = (prices_after['close'] - baseline_price) * 10000
    
    if direction == 1:  # Hausse attendue
        MFE_pips = prices_after['pips_from_baseline'].max()
        MAE_pips = -prices_after['pips_from_baseline'].min() if prices_after['pips_from_baseline'].min() < 0 else 0.0
        peak_idx = prices_after['pips_from_baseline'].idxmax()
    else:  # Baisse attendue (ou direction inconnue)
        MFE_pips = abs(prices_after['pips_from_baseline'].min())
        MAE_pips = prices_after['pips_from_baseline'].max() if prices_after['pips_from_baseline'].max() > 0 else 0.0
        peak_idx = prices_after['pips_from_baseline'].idxmin()
    
    # Time to peak
    peak_time = prices_after.loc[peak_idx, 'datetime']
    time_to_peak = (peak_time - pd.to_datetime(t0)).total_seconds() / 60.0
    
    return {
        'MFE_pips': float(MFE_pips),
        'MAE_pips': float(MAE_pips),
        'time_to_peak_min': float(time_to_peak)
    }


def detect_double_wave(
    prices_df: pd.DataFrame,
    t0: datetime,
    direction: int,
    baseline_price: float,
    peak1_time: datetime,
    peak1_price: float,
    config: PatternConfig
) -> Optional[Dict[str, Any]]:
    """
    Détecte un pattern double wave.
    
    Conditions:
    1. Wave1 peak atteint
    2. Retracement >= threshold depuis peak1
    3. Breakout au-dessus (ou en dessous) peak1 >= breakout_pips
    
    Returns:
        Dict avec wave1_pips, retracement_pips, wave2_pips, peak2_time, peak2_price
        ou None si pas de double wave
    """
    prices_after_peak1 = prices_df[prices_df['datetime'] > pd.to_datetime(peak1_time)].copy()
    
    if prices_after_peak1.empty:
        return None
    
    wave1_pips = abs(peak1_price - baseline_price) * 10000
    
    # Trouver retracement minimum après peak1
    if direction == 1:  # Hausse
        retracement_price = prices_after_peak1['close'].min()
        retracement_pips = (peak1_price - retracement_price) * 10000
        breakout_price = prices_after_peak1['close'].max()
        breakout_pips = (breakout_price - peak1_price) * 10000
    else:  # Baisse
        retracement_price = prices_after_peak1['close'].max()
        retracement_pips = (retracement_price - peak1_price) * 10000
        breakout_price = prices_after_peak1['close'].min()
        breakout_pips = (peak1_price - breakout_price) * 10000
    
    retracement_pct = retracement_pips / wave1_pips if wave1_pips > 0 else 0.0
    
    # Vérifier conditions
    if (retracement_pct >= config.retracement_threshold_pct and 
        breakout_pips >= config.breakout_pips):
        
        # Trouver peak2
        if direction == 1:
            peak2_idx = prices_after_peak1['close'].idxmax()
        else:
            peak2_idx = prices_after_peak1['close'].idxmin()
        
        peak2_time = prices_after_peak1.loc[peak2_idx, 'datetime']
        peak2_price = prices_after_peak1.loc[peak2_idx, 'close']
        wave2_pips = abs(peak2_price - retracement_price) * 10000
        
        return {
            'wave1_pips': float(wave1_pips),
            'retracement_pips': float(retracement_pips),
            'retracement_pct': float(retracement_pct),
            'wave2_pips': float(wave2_pips),
            'peak1_time': peak1_time,
            'peak1_price': float(peak1_price),
            'peak2_time': peak2_time.to_pydatetime(),
            'peak2_price': float(peak2_price),
            'retracement_time': prices_after_peak1.loc[prices_after_peak1['close'] == retracement_price, 'datetime'].iloc[0].to_pydatetime()
        }
    
    return None


def detect_zigzag(
    prices_df: pd.DataFrame,
    t0: datetime,
    baseline_price: float,
    config: PatternConfig
) -> Dict[str, Any]:
    """
    Détecte un pattern zigzag (alternances directionnelles).
    
    Utilise un algorithme de détection d'extrema plus robuste:
    - Utilise prix lissé pour réduire bruit
    - Exige un mouvement minimum entre swings
    - Ne compte que les swings significatifs
    
    Returns:
        Dict avec n_swings, swing_times, swing_prices, swing_types
    """
    prices_after = prices_df[prices_df['datetime'] >= pd.to_datetime(t0)].copy()
    
    if prices_after.empty:
        return {'n_swings': 0, 'swing_times': [], 'swing_prices': [], 'swing_types': []}
    
    # Lisser prix pour détection plus robuste
    prices_after['close_smooth'] = smooth_prices(prices_after['close'], config.smoothing_window)
    prices_vals = prices_after['close_smooth'].values
    prices_times = prices_after['datetime'].values
    prices_prices = prices_after['close_smooth'].values
    
    swings = []
    threshold_pips = config.swing_threshold_pips
    
    # Détecter extrema locaux avec fenêtre plus large pour réduire bruit
    window = max(3, config.smoothing_window // 2)  # Fenêtre pour comparaison
    
    for i in range(window, len(prices_vals) - window):
        val = prices_vals[i]
        
        # Vérifier si c'est un extremum local significatif
        is_peak = all(val >= prices_vals[i-j] for j in range(1, window+1)) and \
                  all(val >= prices_vals[i+j] for j in range(1, window+1)) and \
                  val > prices_vals[i-1] and val > prices_vals[i+1]
        
        is_trough = all(val <= prices_vals[i-j] for j in range(1, window+1)) and \
                    all(val <= prices_vals[i+j] for j in range(1, window+1)) and \
                    val < prices_vals[i-1] and val < prices_vals[i+1]
        
        if is_peak:
            # Vérifier mouvement depuis dernier swing
            if swings:
                last_price = swings[-1][2]
                movement_pips = abs(val - last_price) * 10000
                if movement_pips >= threshold_pips:
                    swings.append(('peak', prices_times[i], prices_prices[i]))
            else:
                # Premier swing: vérifier depuis baseline
                movement_pips = abs(val - baseline_price) * 10000
                if movement_pips >= threshold_pips:
                    swings.append(('peak', prices_times[i], prices_prices[i]))
        
        elif is_trough:
            if swings:
                last_price = swings[-1][2]
                movement_pips = abs(val - last_price) * 10000
                if movement_pips >= threshold_pips:
                    swings.append(('trough', prices_times[i], prices_prices[i]))
            else:
                movement_pips = abs(val - baseline_price) * 10000
                if movement_pips >= threshold_pips:
                    swings.append(('trough', prices_times[i], prices_prices[i]))
    
    # Compter alternances (pattern zigzag = alternance peak-trough-peak-trough...)
    n_alternances = 0
    if len(swings) >= 2:
        # Compter changements de direction
        for i in range(len(swings) - 1):
            if swings[i][0] != swings[i+1][0]:
                n_alternances += 1
    
    return {
        'n_swings': len(swings),  # Nombre total de swings
        'n_alternances': n_alternances,  # Nombre d'alternances directionnelles
        'swing_times': [s[1] for s in swings],
        'swing_prices': [float(s[2]) for s in swings],
        'swing_types': [s[0] for s in swings]
    }


def determine_t_end(
    prices_df: pd.DataFrame,
    t0: datetime,
    MFE_time: datetime,
    MFE_price: float,
    config: PatternConfig
) -> datetime:
    """
    Détermine t_end selon règles paramétrables.
    
    Règles:
    - Si retracement depuis MFE >= end_reversal_pips
      ET stabilisation (range <= stabilization_band_pips pendant stabilization_minutes)
      → t_end = fin stabilisation
    - Sinon → t_end = t0 + max_minutes
    """
    prices_after_mfe = prices_df[prices_df['datetime'] > pd.to_datetime(MFE_time)].copy()
    
    if prices_after_mfe.empty:
        return pd.to_datetime(t0) + timedelta(minutes=config.max_minutes)
    
    # Vérifier retracement
    retracement_pips = abs((prices_after_mfe['close'] - MFE_price).min()) * 10000
    
    if retracement_pips >= config.end_reversal_pips:
        # Vérifier stabilisation
        for i in range(len(prices_after_mfe) - config.stabilization_minutes):
            window = prices_after_mfe.iloc[i:i+config.stabilization_minutes]
            price_range = (window['close'].max() - window['close'].min()) * 10000
            
            if price_range <= config.stabilization_band_pips:
                # Stabilisation trouvée
                return window.iloc[-1]['datetime'].to_pydatetime()
    
    # Pas de fin détectée → utiliser max_minutes
    t_end = pd.to_datetime(t0) + timedelta(minutes=config.max_minutes)
    # Limiter à la fin des données disponibles
    if len(prices_after_mfe) > 0:
        max_available = prices_after_mfe.iloc[-1]['datetime']
        t_end = min(t_end, max_available)
    
    return t_end.to_pydatetime()


def classify_pattern(
    prices_df: pd.DataFrame,
    t0: datetime,
    direction: int,
    baseline_price: float,
    MFE_pips: float,
    time_to_peak: float,
    double_wave_result: Optional[Dict],
    zigzag_result: Dict,
    config: PatternConfig
) -> str:
    """
    Classifie le pattern: single_wave, double_wave, zigzag, unknown.
    """
    # Double wave prioritaire
    if double_wave_result is not None:
        return 'double_wave'
    
    # Zigzag si assez d'alternances (utiliser n_alternances plutôt que n_swings)
    n_alternances = zigzag_result.get('n_alternances', 0)
    if n_alternances >= config.min_swings:  # min_swings alternances = 2*min_swings swings min
        return 'zigzag'
    
    # Sinon single wave (ou unknown si mouvement faible)
    if MFE_pips < config.swing_threshold_pips:
        return 'unknown'
    
    return 'single_wave'


def label_day(
    date_str: str,
    conn: duckdb.DuckDBPyConnection,
    config: Optional[PatternConfig] = None
) -> Dict[str, Any]:
    """
    Labellise le pattern pour une date donnée.
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
        conn: Connexion DuckDB
        config: Configuration (optionnel, utilise défaut si None)
    
    Returns:
        Dict avec:
        - pattern_label: 'single_wave'|'double_wave'|'zigzag'|'unknown'
        - t_start, t0, t_end
        - metrics: MFE_pips, MAE_pips, retracement_pips, time_to_peak_min, n_swings, etc.
        - events_snapshot: DataFrame des événements core
        - prices_snippet: DataFrame des prix (optionnel)
    """
    if config is None:
        config = PatternConfig()
    
    warnings.warn(f"Labellisation pattern pour {date_str}")
    
    # 1. Charger événements depuis events_enriched_v1
    query_events = """
        SELECT 
            ts_utc, ts_local, date_local, country, event_key, event_title,
            actual, consensus, previous, importance_n, has_consensus, has_actual
        FROM events_enriched_v1
        WHERE date_local = CAST(? AS DATE)
        ORDER BY ts_local
    """
    
    df_events = conn.execute(query_events, [date_str]).df()
    
    if df_events.empty:
        warnings.warn(f"Aucun événement trouvé pour {date_str}")
        return {
            'pattern_label': 'unknown',
            'error': 'no_events'
        }
    
    # 2. Sélectionner kernel events et déterminer t0 (UNE SEULE FOIS)
    kernel_df, t0, kernel_keys = _select_kernel_events(df_events, config, date_str)
    
    if t0 is None:
        warnings.warn(f"Impossible de déterminer t0 pour {date_str}")
        return {
            'pattern_label': 'unknown',
            'error': 'no_t0'
        }
    
    # Extraire métadonnées kernel
    kernel_event_count = len(kernel_df)
    kernel_first_ts_local = kernel_df.iloc[0]['ts_local'].isoformat() if kernel_event_count > 0 else None
    
    # 3. Charger prix M1
    prices_df = load_prices_m1(conn, t0, config)
    
    if prices_df.empty:
        warnings.warn(f"Aucun prix M1 trouvé pour {date_str}")
        return {
            'pattern_label': 'unknown',
            'error': 'no_prices',
            't0': t0.isoformat()
        }
    
    # 4. Baseline price (juste avant t0)
    prices_before = prices_df[prices_df['datetime'] < pd.to_datetime(t0)]
    if prices_before.empty:
        baseline_price = prices_df.iloc[0]['close']
    else:
        baseline_price = prices_before.iloc[-1]['close']
    
    # 5. Lisser prix
    prices_df['close_smooth'] = smooth_prices(prices_df['close'], config.smoothing_window)
    
    # 6. Direction initiale
    direction = calculate_direction_initial(prices_df, t0, config)
    
    # 7. MFE/MAE
    mfe_mae = calculate_mfe_mae(prices_df, t0, direction, baseline_price)
    
    # Trouver peak1 pour double wave detection
    prices_after = prices_df[prices_df['datetime'] >= pd.to_datetime(t0)].copy()
    if direction == 1:
        peak1_idx = prices_after['close_smooth'].idxmax()
    else:
        peak1_idx = prices_after['close_smooth'].idxmin()
    
    peak1_time = prices_after.loc[peak1_idx, 'datetime']
    peak1_price = prices_after.loc[peak1_idx, 'close_smooth']
    
    # 8. Détection double wave
    double_wave_result = detect_double_wave(
        prices_df, t0, direction, baseline_price,
        peak1_time.to_pydatetime(), peak1_price, config
    )
    
    # 9. Détection zigzag
    zigzag_result = detect_zigzag(prices_df, t0, baseline_price, config)
    
    # 10. Classifier pattern
    pattern_label = classify_pattern(
        prices_df, t0, direction, baseline_price,
        mfe_mae['MFE_pips'], mfe_mae['time_to_peak_min'],
        double_wave_result, zigzag_result, config
    )
    
    # 11. Déterminer t_end
    t_start = (pd.to_datetime(t0) - timedelta(minutes=config.window_before_minutes)).to_pydatetime()
    t_end = determine_t_end(prices_df, t0, peak1_time.to_pydatetime(), peak1_price, config)
    
    # 12. Calculer retracement depuis peak
    prices_after_peak = prices_df[prices_df['datetime'] > pd.to_datetime(peak1_time)].copy()
    if not prices_after_peak.empty:
        if direction == 1:
            retracement_pips = ((peak1_price - prices_after_peak['close'].min()) * 10000)
        else:
            retracement_pips = ((prices_after_peak['close'].max() - peak1_price) * 10000)
    else:
        retracement_pips = 0.0
    
    # 13. Events snapshot (core events)
    events_snapshot = df_events[
        (pd.to_datetime(df_events['ts_local']) >= t_start) &
        (pd.to_datetime(df_events['ts_local']) <= t_end)
    ].copy()
    
    # 14. Résultat (kernel_keys déjà extraits dans _select_kernel_events)
    result = {
        'date': date_str,
        'pattern_label': pattern_label,
        't_start': t_start.isoformat(),
        't0': t0.isoformat(),
        't_end': t_end.isoformat(),
        'direction': direction,
        'baseline_price': float(baseline_price),
        'kernel_keys': kernel_keys,  # Liste des event_keys du kernel (ts_local ∈ [t0, t0+60s])
        'kernel_event_count': kernel_event_count,
        'kernel_first_ts_local': kernel_first_ts_local,
        'metrics': {
            **mfe_mae,
            'retracement_pips': float(retracement_pips),
            'n_swings': zigzag_result.get('n_swings', 0),
            'n_alternances': zigzag_result.get('n_alternances', 0)
        },
        'events_snapshot': events_snapshot,
        'config': {
            'window_before_minutes': config.window_before_minutes,
            'window_after_minutes': config.window_after_minutes,
            'smoothing_window': config.smoothing_window,
            'retracement_threshold_pct': config.retracement_threshold_pct,
            'breakout_pips': config.breakout_pips,
            'swing_threshold_pips': config.swing_threshold_pips,
            'end_reversal_pips': config.end_reversal_pips,
            'stabilization_band_pips': config.stabilization_band_pips,
            'stabilization_minutes': config.stabilization_minutes
        }
    }
    
    if double_wave_result:
        result['double_wave'] = double_wave_result
    
    if zigzag_result['n_swings'] > 0:
        result['zigzag'] = {
            'n_swings': zigzag_result['n_swings'],
            'swing_times': [t.isoformat() if hasattr(t, 'isoformat') else str(t) for t in zigzag_result['swing_times']]
        }
    
    return result


if __name__ == "__main__":
    """Test rapide sur dates panel."""
    from pathlib import Path
    
    DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.duckdb"
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    config = PatternConfig()
    
    test_dates = ['2025-08-01', '2025-09-11']
    
    print("=" * 80)
    print("TEST PATTERN LABELER M1")
    print("=" * 80)
    print()
    
    for date_str in test_dates:
        print(f"\n{'='*80}")
        print(f"DATE: {date_str}")
        print(f"{'='*80}")
        
        try:
            result = label_day(date_str, conn, config=config)
            
            print(f"\nPattern: {result.get('pattern_label', 'unknown')}")
            print(f"Direction: {result.get('direction', 'N/A')}")
            print(f"t0: {result.get('t0', 'N/A')}")
            print(f"\nMétriques:")
            metrics = result.get('metrics', {})
            for k, v in metrics.items():
                print(f"  {k}: {v:.2f}" if isinstance(v, (int, float)) else f"  {k}: {v}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    conn.close()
    print(f"\n{'='*80}")
    print("✅ Tests terminés")
    print("=" * 80)

