"""
CORRÉLATION R² ↔ AMPLIFICATION IDÉALE - PIPELINE ORIGINAL (ÉTAPES 8-9)
======================================================================

Module pour calculer l'amplification dynamique basée sur la corrélation
entre le R² de la tendance pré-événement et l'amplification idéale.

Workflow original :
1. Calculer R² de la tendance avant le cluster (détection inversions)
2. Utiliser fonction calibrée pour prédire amplification à partir de R²
3. Appliquer cette amplification dans les prédictions

Auteur : André Valentin avec Claude
Date : 21 novembre 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from scipy.stats import linregress
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_absolute_error


# ═══════════════════════════════════════════════════════════════
# PARAMÈTRES PAR DÉFAUT
# ═══════════════════════════════════════════════════════════════

LOOKBACK_DAYS = 30  # Jours avant événement pour calculer R²
WINDOW_MINUTES = 240  # Fenêtre pour détection swing highs/lows
MIN_AMPLITUDE_PIPS = 30  # Amplitude minimale pour inversions
AMP_MIN = 0.01  # Amplification minimale
AMP_MAX = 5.0  # Amplification maximale (augmenté pour calibration)


# ═══════════════════════════════════════════════════════════════
# DÉTECTION INVERSIONS DE TENDANCE
# ═══════════════════════════════════════════════════════════════

def detect_swing_highs(prices: pd.Series, window: int = 240, threshold: float = 0.0001) -> list:
    """Détecte les swing highs locaux"""
    swing_highs = []
    for i in range(window, len(prices) - window):
        center = prices.iloc[i]
        left = prices.iloc[i-window:i]
        right = prices.iloc[i+1:i+window+1]
        if center > max(left.max(), right.max()) + threshold:
            swing_highs.append(i)
    return swing_highs


def detect_swing_lows(prices: pd.Series, window: int = 240, threshold: float = 0.0001) -> list:
    """Détecte les swing lows locaux"""
    swing_lows = []
    for i in range(window, len(prices) - window):
        center = prices.iloc[i]
        left = prices.iloc[i-window:i]
        right = prices.iloc[i+1:i+window+1]
        if center < min(left.min(), right.min()) - threshold:
            swing_lows.append(i)
    return swing_lows


def detect_trend_reversals(
    prices: pd.Series,
    timestamps: pd.Series,
    window: int = 240,
    min_amplitude_pips: float = 30
) -> list:
    """
    Détecte les inversions de tendance (swing highs/lows)
    
    Returns:
        Liste de dicts avec 'type', 'index', 'price', 'timestamp', 'r2', 'duration_hours'
    """
    swing_highs = detect_swing_highs(prices, window)
    swing_lows = detect_swing_lows(prices, window)
    
    extrema = []
    for idx in swing_highs:
        extrema.append({
            'type': 'HIGH',
            'index': idx,
            'price': prices.iloc[idx],
            'timestamp': timestamps.iloc[idx]
        })
    for idx in swing_lows:
        extrema.append({
            'type': 'LOW',
            'index': idx,
            'price': prices.iloc[idx],
            'timestamp': timestamps.iloc[idx]
        })
    
    extrema.sort(key=lambda x: x['index'])
    
    reversals = []
    for extremum in extrema:
        start_idx = extremum['index']
        end_idx = len(prices) - 1
        
        if end_idx - start_idx < 60:
            continue
        
        segment_prices = prices.iloc[start_idx:end_idx + 1]
        amplitude = (segment_prices.max() - segment_prices.min()) * 10000
        
        if amplitude < min_amplitude_pips:
            continue
        
        price_start = prices.iloc[start_idx]
        price_end = prices.iloc[end_idx]
        
        if extremum['type'] == 'HIGH' and price_end < price_start:
            reversal_type = 'HIGH_TO_LOW'
        elif extremum['type'] == 'LOW' and price_end > price_start:
            reversal_type = 'LOW_TO_HIGH'
        else:
            continue
        
        duration = (timestamps.iloc[end_idx] - timestamps.iloc[start_idx]).total_seconds() / 3600.0
        
        t = np.arange(len(segment_prices))
        slope, intercept, r_value, _, _ = linregress(t, segment_prices.values)
        r_squared = r_value ** 2
        
        reversals.append({
            'type': reversal_type,
            'time': extremum['timestamp'],
            'index': start_idx,
            'price': extremum['price'],
            'amplitude_pips': amplitude,
            'duration_hours': duration,
            'r2': r_squared
        })
    
    return reversals


# ═══════════════════════════════════════════════════════════════
# CALCUL R² TENDANCE PRÉ-ÉVÉNEMENT
# ═══════════════════════════════════════════════════════════════

def calculate_r2_trend_before_event(
    df_prices: pd.DataFrame,
    event_time: datetime,
    lookback_days: int = LOOKBACK_DAYS,
    window_minutes: int = WINDOW_MINUTES,
    min_amplitude_pips: float = MIN_AMPLITUDE_PIPS
) -> Optional[Dict]:
    """
    Calcule le R² de la tendance avant un événement
    
    Args:
        df_prices: DataFrame avec colonnes 'datetime', 'close' (ou index datetime)
        event_time: Timestamp de l'événement
        lookback_days: Nombre de jours avant événement à analyser
        window_minutes: Fenêtre pour détection swing
        min_amplitude_pips: Amplitude minimale pour inversions
    
    Returns:
        Dict avec 'r2', 'duration_hours', 'reversal_type', 'method'
        ou None si impossible de calculer
    """
    # Déterminer colonne prix
    if 'close' in df_prices.columns:
        prices = df_prices['close']
    elif 'datetime' in df_prices.columns:
        prices = df_prices.set_index('datetime')['close']
    else:
        prices = df_prices.iloc[:, 0]  # Première colonne
    
    # Déterminer timestamps
    if 'datetime' in df_prices.columns:
        timestamps = pd.to_datetime(df_prices['datetime'])
    elif isinstance(df_prices.index, pd.DatetimeIndex):
        timestamps = df_prices.index
    else:
        return None
    
    # Filtrer prix avant événement
    start_time = event_time - timedelta(days=lookback_days)
    mask = (timestamps >= start_time) & (timestamps < event_time)
    prices_before = prices[mask]
    timestamps_before = timestamps[mask]
    
    if len(prices_before) < 60:
        return None
    
    # Détecter inversions
    reversals = detect_trend_reversals(
        prices_before,
        timestamps_before,
        window=window_minutes,
        min_amplitude_pips=min_amplitude_pips
    )
    
    if not reversals:
        # Fallback : régression linéaire simple sur toute la période
        t = np.arange(len(prices_before))
        slope, intercept, r_value, _, _ = linregress(t, prices_before.values)
        r_squared = r_value ** 2
        
        ss_res = np.sum((prices_before.values - (slope * t + intercept)) ** 2)
        ss_tot = np.sum((prices_before.values - prices_before.mean()) ** 2)
        if ss_tot == 0:
            return None
        r2 = max(0.0, min(1.0, 1 - (ss_res / ss_tot)))
        return {
            'r2': float(r2),
            'duration_hours': lookback_days * 24,
            'reversal_type': 'SIMPLE_LINEAR',
            'method': 'fallback_simple'
        }
    
    # Utiliser la dernière inversion détectée
    last_reversal = reversals[-1]
    return {
        'r2': float(last_reversal['r2']),
        'duration_hours': float(last_reversal['duration_hours']),
        'reversal_type': last_reversal['type'],
        'reversal_time': last_reversal['time'],
        'method': 'inversion_detection'
    }


# ═══════════════════════════════════════════════════════════════
# FONCTIONS DE CALIBRATION
# ═══════════════════════════════════════════════════════════════

def calibrate_amplification_sigmoid(
    r2_values: np.ndarray,
    amp_ideal_values: np.ndarray
) -> Tuple[callable, Dict]:
    """
    Calibre une fonction sigmoïde pour prédire amplification à partir de R²
    
    Formule : amp = a / (1 + exp(-b × (R² - c))) + d
    
    Args:
        r2_values: Array de R²
        amp_ideal_values: Array d'amplifications idéales
    
    Returns:
        Tuple (fonction, dict avec params et métriques)
    """
    def sigmoid(r2, a, b, c, d):
        return a / (1 + np.exp(-b * (r2 - c))) + d
    
    try:
        # Initial guess
        p0 = [
            (amp_ideal_values.max() - amp_ideal_values.min()) / 2,  # a
            10.0,  # b
            0.5,  # c
            amp_ideal_values.min()  # d
        ]
        
        popt, _ = curve_fit(sigmoid, r2_values, amp_ideal_values, p0=p0, maxfev=10000)
        y_pred = sigmoid(r2_values, *popt)
        y_pred = np.clip(y_pred, AMP_MIN, AMP_MAX)
        
        return (
            lambda r2: np.clip(sigmoid(r2, *popt), AMP_MIN, AMP_MAX),
            {
                'params': popt.tolist(),
                'r2_fit': float(r2_score(amp_ideal_values, y_pred)),
                'mae': float(mean_absolute_error(amp_ideal_values, y_pred)),
                'formula': f"amp = {popt[0]:.6f} / (1 + exp(-{popt[1]:.6f} × (R² - {popt[2]:.6f}))) + {popt[3]:.6f}"
            }
        )
    except Exception as e:
        return None, {'error': str(e)}


def calibrate_amplification_linear(
    r2_values: np.ndarray,
    amp_ideal_values: np.ndarray
) -> Tuple[callable, Dict]:
    """
    Calibre une fonction linéaire pour prédire amplification à partir de R²
    
    Formule : amp = a + b × R²
    """
    def linear(r2, a, b):
        return a + b * r2
    
    try:
        popt, _ = curve_fit(linear, r2_values, amp_ideal_values)
        y_pred = linear(r2_values, *popt)
        y_pred = np.clip(y_pred, AMP_MIN, AMP_MAX)
        
        return (
            lambda r2: np.clip(linear(r2, *popt), AMP_MIN, AMP_MAX),
            {
                'params': popt.tolist(),
                'r2_fit': float(r2_score(amp_ideal_values, y_pred)),
                'mae': float(mean_absolute_error(amp_ideal_values, y_pred)),
                'formula': f"amp = {popt[0]:.6f} + {popt[1]:.6f} × R²"
            }
        )
    except Exception as e:
        return None, {'error': str(e)}


# ═══════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE : PRÉDICTION AMPLIFICATION
# ═══════════════════════════════════════════════════════════════

def predict_amplification_from_r2(
    r2_trend: float,
    calibration_mode: str = 'sigmoid',
    calibration_params: Optional[Dict] = None
) -> float:
    """
    Prédit l'amplification à partir du R² de la tendance
    
    Args:
        r2_trend: R² de la tendance pré-événement (0-1)
        calibration_mode: 'sigmoid' ou 'linear'
        calibration_params: Paramètres de calibration (si None, utilise valeurs par défaut)
    
    Returns:
        Amplification prédite (bornée entre AMP_MIN et AMP_MAX)
    """
    if calibration_params is None:
        # Valeurs par défaut (basées sur tests précédents)
        if calibration_mode == 'sigmoid':
            # Paramètres approximatifs d'une sigmoïde calibrée
            # Ces valeurs devraient être recalibrées avec les nouvelles données
            a, b, c, d = 0.3, 10.0, 0.5, 0.05
            amp = a / (1 + np.exp(-b * (r2_trend - c))) + d
        else:  # linear
            # Formule Session 98 : amp = 1.9938 × R² + 1.4448
            # Adaptée pour notre échelle (0.01-0.5)
            a, b = 0.05, 0.2
            amp = a + b * r2_trend
    else:
        # Utiliser paramètres fournis
        if calibration_mode == 'sigmoid':
            a, b, c, d = calibration_params['params']
            amp = a / (1 + np.exp(-b * (r2_trend - c))) + d
        else:  # linear
            a, b = calibration_params['params']
            amp = a + b * r2_trend
    
    return np.clip(amp, AMP_MIN, AMP_MAX)

