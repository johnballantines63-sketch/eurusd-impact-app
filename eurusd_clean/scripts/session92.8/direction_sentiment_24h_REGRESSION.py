"""
MODULE DIRECTION_SENTIMENT - ANALYSE 24 HEURES - RÉGRESSION LINÉAIRE

Date : 29 octobre 2025 - Session 92.11
CORRECTION MAJEURE : Tendance par régression linéaire (méthode professionnelle)

RÈGLE TIMEZONE (project_state_new.md) :
========================================
Events et prices utilisent MÊME timezone : +02:00 (Bern)
14:30 Bern time = 12:30:00+02:00 dans la DB

MÉTHODE TENDANCE (Session 92.11) :
===================================
Régression linéaire sur prix 24h (méthode des moindres carrés)
- y = a·t + b
- Pente (a) = direction tendance
- R² = significativité statistique
- R² < 0.10 → NEUTRE / R² ≥ 0.10 ET pente < 0 → BAISSIER / R² ≥ 0.10 ET pente > 0 → HAUSSIER
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import pandas as pd
import duckdb
import numpy as np


def load_prices_24h_before(date_str: str, event_time_bern: str, conn) -> pd.DataFrame:
    """
    Charge prix EURUSD 24h avant événement
    
    Args:
        date_str: Date événement format 'YYYY-MM-DD'
        event_time_bern: Heure Bern format 'HH:MM:SS' (ex: '14:30:00')
        conn: Connexion DuckDB
    
    Returns:
        DataFrame avec colonnes: datetime, close
    """
    # Convertir heure Bern en timestamp DB (14:30 Bern = 12:30:00+02:00)
    hour, minute, _ = event_time_bern.split(':')
    hour_db = int(hour) - 2
    minute_int = int(minute)
    
    # Calculer date 24h avant
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_24h_before = date_obj - timedelta(days=1)
    date_24h_str = date_24h_before.strftime('%Y-%m-%d')
    
    # Timestamps DB
    timestamp_start = f"{date_24h_str} {hour_db:02d}:{minute_int:02d}:00+02:00"
    timestamp_end = f"{date_str} {hour_db:02d}:{minute_int:02d}:00+02:00"
    
    query = f"""
    SELECT ts_utc, close
    FROM eurusd_prices
    WHERE ts_utc >= '{timestamp_start}'::TIMESTAMP
      AND ts_utc <= '{timestamp_end}'::TIMESTAMP
    ORDER BY ts_utc ASC
    """
    
    df = conn.execute(query).df()
    
    print(f"✅ Chargé {len(df)} lignes prix 24h")
    print(f"   Période : {timestamp_start} → {timestamp_end}")
    print(f"   ({event_time_bern} Bern = {hour_db:02d}:{minute_int:02d}:00+02:00 DB)")
    
    return df


def calculate_trend_regression(prices_df: pd.DataFrame) -> Tuple[str, float, float]:
    """
    Détermine tendance par régression linéaire (méthode des moindres carrés)
    
    MÉTHODE PROFESSIONNELLE (Session 92.11) :
    - Régression linéaire sur prix 24h : y = a·t + b
    - Pente (a) = direction tendance
    - R² = significativité statistique
    
    CRITÈRES :
    - R² < 0.10 → NEUTRE (pas de tendance significative)
    - R² ≥ 0.10 ET pente < 0 → BAISSIER
    - R² ≥ 0.10 ET pente > 0 → HAUSSIER
    
    Args:
        prices_df: DataFrame prix 24h avec colonne 'close'
    
    Returns:
        Tuple (tendance: str, pente: float, r_squared: float)
    """
    # Extraire prix
    prices = prices_df['close'].values
    
    # Temps (1, 2, 3, ..., n)
    t = np.arange(1, len(prices) + 1)
    
    # Moyennes
    t_mean = np.mean(t)
    y_mean = np.mean(prices)
    
    # Calcul pente (coefficient directeur)
    numerator = np.sum((t - t_mean) * (prices - y_mean))
    denominator = np.sum((t - t_mean) ** 2)
    slope = numerator / denominator
    
    # Prédictions
    y_pred = slope * t + (y_mean - slope * t_mean)
    
    # R² (coefficient de détermination)
    ss_tot = np.sum((prices - y_mean) ** 2)
    ss_res = np.sum((prices - y_pred) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    # Critère significativité
    r2_threshold = 0.10
    
    # Pente en pips
    slope_pips = slope * 10000
    
    # Détermination tendance
    if r_squared < r2_threshold:
        trend = "NEUTRE"
    elif slope < -0.000001:  # Pente négative significative
        trend = "BAISSIER"
    elif slope > 0.000001:   # Pente positive significative
        trend = "HAUSSIER"
    else:
        trend = "NEUTRE"
    
    print(f"\n🔍 ANALYSE TENDANCE DEPUIS PIC :")
    print(f"   Pic type : LOW")
    print(f"   Pic prix : {prices.min():.5f}")
    print(f"   Prix actuel : {prices[-1]:.5f}")
    print(f"   Temps écoulé : {(len(prices) / 60):.1f}h")
    
    if trend == "BAISSIER" and r_squared >= r2_threshold:
        print(f"   → Prix BAISSE depuis high pendant {(len(prices) / 60):.1f}h → BAISSIER ✅")
    elif trend == "HAUSSIER" and r_squared >= r2_threshold:
        print(f"   → Prix REBONDIT depuis low pendant {(len(prices) / 60):.1f}h → HAUSSIER ✅")
    else:
        print(f"   → Consolidation récente ({(len(prices) / 60):.1f}h) → NEUTRE")
    
    return trend, slope, r_squared


def calculate_24h_indicators(prices_df: pd.DataFrame) -> Dict:
    """
    Calcule indicateurs momentum/volatilité sur 24h
    
    Args:
        prices_df: DataFrame prix 24h
    
    Returns:
        dict avec momentum_24h_pct et position_in_range
    """
    prices = prices_df['close'].values
    
    # Momentum (variation prix premier vs dernier)
    momentum_pct = ((prices[-1] - prices[0]) / prices[0]) * 100
    
    # Position dans range
    price_max = prices.max()
    price_min = prices.min()
    range_24h = price_max - price_min
    
    if range_24h > 0:
        position = (prices[-1] - price_min) / range_24h
    else:
        position = 0.5
    
    return {
        'momentum_24h_pct': momentum_pct,
        'position_in_range': position
    }


def calculate_direction_sentiment(indicators: Dict, trend: str) -> float:
    """
    Calcule direction_sentiment depuis tendance régression
    
    Args:
        indicators: Dict depuis calculate_24h_indicators()
        trend: 'HAUSSIER', 'BAISSIER', 'NEUTRE'
    
    Returns:
        float: direction_sentiment entre -1.0 et +1.0
    """
    momentum = indicators['momentum_24h_pct']
    position = indicators['position_in_range']
    
    # Base sentiment depuis tendance
    if trend == 'HAUSSIER':
        base_sentiment = +0.50
    elif trend == 'BAISSIER':
        base_sentiment = -0.50
    else:
        base_sentiment = 0.00
    
    # Ajustement momentum
    momentum_adjustment = momentum / 100 * 0.3  # Max ±0.3
    
    # Ajustement position
    if position > 0.8:
        position_adjustment = +0.20
    elif position < 0.2:
        position_adjustment = -0.20
    else:
        position_adjustment = 0.00
    
    # Combinaison
    direction_sentiment = base_sentiment + momentum_adjustment + position_adjustment
    direction_sentiment = max(-1.0, min(1.0, direction_sentiment))
    
    print(f"\n💭 CALCUL DIRECTION_SENTIMENT :")
    print(f"   Tendance base : {trend} → {base_sentiment:+.2f}")
    print(f"   Momentum : {momentum:+.2f}% → {momentum_adjustment:+.2f}")
    print(f"   Position range : {position:.2f} → {position_adjustment:+.2f}")
    print(f"   → Direction_sentiment = {direction_sentiment:+.2f}")
    
    return direction_sentiment


def calculate_combined_factor(surprise_net: float, direction_sentiment: float) -> float:
    """
    Calcule facteur combiné (surprise nette + direction sentiment)
    
    Args:
        surprise_net: Surprise nette en %
        direction_sentiment: Entre -1.0 et +1.0
    
    Returns:
        float: Facteur multiplicateur
    """
    # Direction factor (surprise nette V2)
    if surprise_net > 30:
        direction_factor = 1.05
    elif surprise_net > 0:
        direction_factor = min(1.0 + (surprise_net / 200), 1.05)
    elif surprise_net >= -30:
        direction_factor = max(1.0 + (surprise_net / 100), 0.7)
    else:
        direction_factor = 0.7
    
    # Combinaison avec direction_sentiment
    combined = direction_factor * (1 + direction_sentiment * 0.1)
    
    print(f"\n🔢 FACTEUR COMBINÉ :")
    print(f"   Direction factor (V2) : {direction_factor:.3f}")
    print(f"   Direction sentiment : {direction_sentiment:+.2f}")
    print(f"   Combined factor : {combined:.3f}")
    
    return combined
