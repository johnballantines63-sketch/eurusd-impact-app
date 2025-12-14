"""
MODULE DIRECTION_SENTIMENT - SCORE TENDANCE PONDÉRÉ

Date : 29 octobre 2025 - Session 92.12
AMÉLIORATION MAJEURE : Score pondéré Direction × Durée × R²

INTUITION ANDRÉ :
==================
"pondérer la tendance haussière ou baissière avec sa durée 
plus elle est longue plus l'impact de la tendance sera forte sur une inversion"

CHANGEMENT vs SESSION 92.11 :
===============================
AVANT (S92.11) : base_sentiment FIXE
- HAUSSIER → +0.50
- BAISSIER → -0.50
- NEUTRE → 0.00

APRÈS (S92.12) : base_sentiment VARIABLE (score pondéré)
- score = direction × (duree/24) × r_squared
- Exemple 11.09 : -1.0 × (22.9/24) × 0.55 = -0.52
- Exemple 01.15 : +1.0 × (5.3/24) × 0.70 = +0.15

IMPACT ATTENDU :
================
Date 11.09 (tendance longue) : score -0.52 au lieu de -0.50 → Légère différence
Date 01.15 (tendance courte) : score +0.15 au lieu de +0.50 → GRANDE différence
→ Résout sur-amplification date 01.15
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import pandas as pd
import duckdb
import numpy as np

# Import module durée
from calculate_trend_duration import (
    calculate_regression_on_window,
    find_trend_duration,
    calculate_weighted_trend_score
)


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
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= '{timestamp_start}'::TIMESTAMP
      AND datetime <= '{timestamp_end}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df = conn.execute(query).df()
    
    print(f"✅ Chargé {len(df)} lignes prix 24h")
    print(f"   Période : {timestamp_start} → {timestamp_end}")
    print(f"   ({event_time_bern} Bern = {hour_db:02d}:{minute_int:02d}:00+02:00 DB)")
    
    return df


def calculate_trend_regression(prices_df: pd.DataFrame) -> Tuple[str, float, float]:
    """
    Détermine tendance par régression linéaire
    (Réutilise fonction Session 92.11)
    
    Args:
        prices_df: DataFrame prix 24h avec colonne 'close'
    
    Returns:
        Tuple (tendance: str, pente: float, r_squared: float)
    """
    prices = prices_df['close'].values
    
    # Réutiliser fonction existante
    trend, slope, r_squared = calculate_regression_on_window(prices)
    
    print(f"\n🔍 RÉGRESSION LINÉAIRE 24H :")
    print(f"   Tendance : {trend}")
    print(f"   Pente : {slope*10000:.2f} pips/min")
    print(f"   R² : {r_squared:.3f}")
    
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


def calculate_direction_sentiment_weighted(
    indicators: Dict,
    trend_score_info: Dict
) -> float:
    """
    Calcule direction_sentiment avec score pondéré
    
    CHANGEMENT SESSION 92.12 :
    ===========================
    Base sentiment = score pondéré (au lieu de ±0.50 fixe)
    
    Args:
        indicators: Dict depuis calculate_24h_indicators()
        trend_score_info: Dict depuis calculate_weighted_trend_score()
            - score: Score pondéré (-1.0 à +1.0)
            - trend: 'HAUSSIER', 'BAISSIER', 'NEUTRE'
            - duration_hours: Durée tendance
            - r_squared: R²
    
    Returns:
        float: direction_sentiment entre -1.0 et +1.0
    """
    momentum = indicators['momentum_24h_pct']
    position = indicators['position_in_range']
    
    # Base sentiment = score pondéré (NOUVEAU S92.12)
    base_sentiment = trend_score_info['score']
    
    # Ajustement momentum (comme avant)
    momentum_adjustment = momentum / 100 * 0.3  # Max ±0.3
    
    # Ajustement position (comme avant)
    if position > 0.8:
        position_adjustment = +0.20
    elif position < 0.2:
        position_adjustment = -0.20
    else:
        position_adjustment = 0.00
    
    # Combinaison
    direction_sentiment = base_sentiment + momentum_adjustment + position_adjustment
    direction_sentiment = max(-1.0, min(1.0, direction_sentiment))
    
    print(f"\n💭 CALCUL DIRECTION_SENTIMENT PONDÉRÉ :")
    print(f"   Base (score pondéré) : {base_sentiment:+.3f}")
    print(f"     → {trend_score_info['trend']} {trend_score_info['duration_hours']:.1f}h R²={trend_score_info['r_squared']:.2f}")
    print(f"   Momentum : {momentum:+.2f}% → {momentum_adjustment:+.3f}")
    print(f"   Position range : {position:.2f} → {position_adjustment:+.3f}")
    print(f"   → Direction_sentiment = {direction_sentiment:+.3f}")
    
    print(f"\n📊 COMPARAISON S92.11 vs S92.12 :")
    if trend_score_info['trend'] == 'HAUSSIER':
        old_base = +0.50
    elif trend_score_info['trend'] == 'BAISSIER':
        old_base = -0.50
    else:
        old_base = 0.00
    old_sentiment = max(-1.0, min(1.0, old_base + momentum_adjustment + position_adjustment))
    
    print(f"   S92.11 (fixe) : {old_sentiment:+.3f}")
    print(f"   S92.12 (pondéré) : {direction_sentiment:+.3f}")
    print(f"   Différence : {direction_sentiment - old_sentiment:+.3f}")
    
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
    print(f"   Direction sentiment : {direction_sentiment:+.3f}")
    print(f"   Combined factor : {combined:.3f}")
    
    return combined


def calculate_all_weighted(
    date_str: str,
    event_time_bern: str,
    surprise_net: float,
    db_path: str = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb'
) -> Dict:
    """
    Fonction complète : Calcule tous indicateurs avec score pondéré
    
    Args:
        date_str: Date format 'YYYY-MM-DD'
        event_time_bern: Heure Bern format 'HH:MM:SS'
        surprise_net: Surprise nette en %
        db_path: Chemin base de données
    
    Returns:
        Dict avec tous résultats
    """
    print(f"\n{'='*60}")
    print(f"CALCUL DIRECTION_SENTIMENT PONDÉRÉ")
    print(f"Date : {date_str} {event_time_bern}")
    print(f"Surprise nette : {surprise_net:+.1f}%")
    print(f"{'='*60}")
    
    # Connexion DB
    conn = duckdb.connect(db_path, read_only=True)
    
    try:
        # 1. Charger prix 24h
        prices_df = load_prices_24h_before(date_str, event_time_bern, conn)
        
        # 2. Régression linéaire globale
        trend, slope, r_squared = calculate_trend_regression(prices_df)
        
        # 3. Trouver durée tendance
        duration_info = find_trend_duration(prices_df, trend)
        
        # 4. Calculer score pondéré
        trend_score_info = calculate_weighted_trend_score(
            trend,
            r_squared,
            duration_info['duration_hours']
        )
        
        # 5. Indicateurs 24h
        indicators = calculate_24h_indicators(prices_df)
        
        # 6. Direction sentiment pondéré
        direction_sentiment = calculate_direction_sentiment_weighted(
            indicators,
            trend_score_info
        )
        
        # 7. Facteur combiné
        combined = calculate_combined_factor(surprise_net, direction_sentiment)
        
        return {
            'trend': trend,
            'slope': slope,
            'r_squared': r_squared,
            'duration_hours': duration_info['duration_hours'],
            'duration_method': duration_info['method'],
            'trend_score': trend_score_info['score'],
            'momentum_24h_pct': indicators['momentum_24h_pct'],
            'position_in_range': indicators['position_in_range'],
            'direction_sentiment': direction_sentiment,
            'combined_factor': combined
        }
    
    finally:
        conn.close()


if __name__ == "__main__":
    # Test cas 11.09.2025
    print("\n" + "="*60)
    print("TEST CAS 11.09.2025 - Tendance longue")
    print("="*60)
    
    result = calculate_all_weighted(
        date_str='2025-09-11',
        event_time_bern='14:30:00',
        surprise_net=33.6
    )
    
    print(f"\n{'='*60}")
    print(f"RÉSULTAT FINAL 11.09.2025 :")
    print(f"  Direction sentiment : {result['direction_sentiment']:+.3f}")
    print(f"  Combined factor : {result['combined_factor']:.3f}")
    print(f"{'='*60}")
