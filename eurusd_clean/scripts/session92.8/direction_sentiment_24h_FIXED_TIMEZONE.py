"""
MODULE DIRECTION_SENTIMENT - ANALYSE 24 HEURES - TIMEZONE CORRIGÉ

Date : 29 octobre 2025 - Session 92.10
CORRECTION CRITIQUE : Timestamps corrects selon règle timezone

RÈGLE TIMEZONE (project_state_new.md) :
========================================
Events et prices utilisent MÊME timezone : +02:00 (Bern)
14:30 Bern time = 12:30:00+02:00 dans la DB

EXEMPLE :
- Événement CPI 11.09.2025 à 14:30 Bern
- Dans DB : '2025-09-11 12:30:00+02:00'
- Query prix : WHERE datetime >= '2025-09-11 12:30:00+02:00'::TIMESTAMP

PAS de conversion nécessaire !
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import pandas as pd
import duckdb


def load_prices_24h_before(date_str: str, event_time_bern: str, conn) -> pd.DataFrame:
    """
    Charge prix EURUSD 24h avant événement
    
    TIMEZONE CORRIGÉ SESSION 92.10 :
    ==================================
    - date_str : '2025-09-11'
    - event_time_bern : '14:30:00' (heure Bern)
    - Conversion DB : 14:30 Bern = 12:30:00+02:00
    
    Args:
        date_str: Date événement format 'YYYY-MM-DD'
        event_time_bern: Heure Bern format 'HH:MM:SS' (ex: '14:30:00')
        conn: Connexion DuckDB
    
    Returns:
        DataFrame avec colonnes: datetime, open, high, low, close
        
    Exemple:
        date_str = '2025-09-11'
        event_time_bern = '14:30:00'
        → Calcule timestamp DB : '2025-09-11 12:30:00+02:00' (14:30-2h)
        → Charge prix 24h avant : '2025-09-10 12:30:00+02:00' à '2025-09-11 12:30:00+02:00'
    """
    # Convertir heure Bern en timestamp DB (Bern - 2h = UTC, puis +02:00)
    hour, minute, _ = event_time_bern.split(':')
    hour_int = int(hour)
    minute_int = int(minute)
    
    # 14:30 Bern = 12:30:00+02:00 dans DB
    hour_db = hour_int - 2
    
    # Calculer date 24h avant
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_24h_before = date_obj - timedelta(days=1)
    date_24h_str = date_24h_before.strftime('%Y-%m-%d')
    
    # Construire timestamps DB (format string avec +02:00)
    timestamp_start = f"{date_24h_str} {hour_db:02d}:{minute_int:02d}:00+02:00"
    timestamp_end = f"{date_str} {hour_db:02d}:{minute_int:02d}:00+02:00"
    
    query = f"""
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= '{timestamp_start}'::TIMESTAMP
      AND datetime < '{timestamp_end}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df = conn.execute(query).df()
    
    print(f"✅ Chargé {len(df)} lignes prix 24h")
    print(f"   Période : {timestamp_start} → {timestamp_end}")
    print(f"   ({event_time_bern} Bern = {hour_db:02d}:{minute_int:02d}:00+02:00 DB)")
    
    if len(df) == 0:
        print(f"⚠️ ATTENTION : Aucune donnée trouvée pour cette période !")
    
    return df


def find_last_absolute_peak(prices_df: pd.DataFrame, event_price: float) -> Dict:
    """
    Identifie le dernier pic absolu dans période 24h
    
    DÉFINITION PIC ABSOLU:
    - High maximum dans période 24h
    - Ou Low minimum dans période 24h
    
    SÉLECTION:
    - Si prix actuel plus proche du high → Pic = high
    - Si prix actuel plus proche du low → Pic = low
    
    Args:
        prices_df: DataFrame prix 24h (depuis load_prices_24h_before)
        event_price: Prix au moment de l'événement (close dernier)
    
    Returns:
        dict: {
            'peak_price': float,
            'peak_time': datetime,
            'peak_type': 'HIGH' ou 'LOW',
            'distance_pips': float,
            'hours_since_peak': float
        }
    """
    # Identifier high/low absolus période 24h
    idx_high = prices_df['high'].idxmax()
    idx_low = prices_df['low'].idxmin()
    
    peak_high = prices_df.loc[idx_high, 'high']
    peak_low = prices_df.loc[idx_low, 'low']
    
    time_high = prices_df.loc[idx_high, 'datetime']
    time_low = prices_df.loc[idx_low, 'datetime']
    
    # Distance du prix actuel aux pics
    distance_to_high = abs(event_price - peak_high)
    distance_to_low = abs(event_price - peak_low)
    
    # Sélectionner pic le plus proche
    if distance_to_high < distance_to_low:
        peak_type = 'HIGH'
        peak_price = peak_high
        peak_time = time_high
        distance_pips = (event_price - peak_high) * 10000
        
        print(f"📈 Dernier pic = HIGH à {peak_price:.5f} (distance: {distance_pips:.1f} pips)")
    else:
        peak_type = 'LOW'
        peak_price = peak_low
        peak_time = time_low
        distance_pips = (event_price - peak_low) * 10000
        
        print(f"📉 Dernier pic = LOW à {peak_price:.5f} (distance: {distance_pips:.1f} pips)")
    
    # Calculer temps écoulé depuis pic
    event_time = prices_df.iloc[-1]['datetime']
    hours_since = (event_time - peak_time).total_seconds() / 3600
    
    return {
        'peak_price': peak_price,
        'peak_time': peak_time,
        'peak_type': peak_type,
        'distance_pips': distance_pips,
        'hours_since_peak': hours_since
    }


def calculate_24h_indicators(prices_df: pd.DataFrame, peak_info: Dict, event_price: float) -> Dict:
    """
    Calcule indicateurs momentum/volatilité sur 24h
    
    Args:
        prices_df: DataFrame prix 24h
        peak_info: Dict depuis find_last_absolute_peak()
        event_price: Prix au moment événement
    
    Returns:
        dict: {
            'range_24h_pips': float,
            'atr_24h_pips': float,
            'momentum_24h_pct': float,
            'position_in_range': float (0-1)
        }
    """
    high_24h = prices_df['high'].max()
    low_24h = prices_df['low'].min()
    range_24h = (high_24h - low_24h) * 10000
    
    # ATR simplifié (moyenne des ranges)
    prices_df_copy = prices_df.copy()
    prices_df_copy['range'] = (prices_df_copy['high'] - prices_df_copy['low']) * 10000
    atr_24h = prices_df_copy['range'].mean()
    
    # Momentum (variation prix premier vs dernier)
    price_start = prices_df.iloc[0]['close']
    momentum_pct = ((event_price - price_start) / price_start) * 100
    
    # Position dans range
    if range_24h > 0:
        position = (event_price - low_24h) / (high_24h - low_24h)
    else:
        position = 0.5
    
    return {
        'range_24h_pips': range_24h,
        'atr_24h_pips': atr_24h,
        'momentum_24h_pct': momentum_pct,
        'position_in_range': position
    }


def determine_trend_from_peak(peak_info: Dict, event_price: float, date_str: str, event_time_bern: str) -> str:
    """
    Détermine VRAIE tendance depuis pic
    
    CORRECTION SESSION 92.9 :
    ==========================
    Distance du pic ≠ Direction tendance !
    
    LOGIQUE CORRECTE :
    - Si prix < peak HIGH ET temps > 12h → BAISSIER (correction depuis high)
    - Si prix > peak LOW ET temps > 12h → HAUSSIER (rebond depuis low)
    - Si temps < 12h → NEUTRE (consolidation récente)
    
    Args:
        peak_info: Dict depuis find_last_absolute_peak()
        event_price: Prix au moment événement
        date_str: Date événement (pour affichage)
        event_time_bern: Heure Bern (pour affichage)
    
    Returns:
        str: 'HAUSSIER', 'BAISSIER', ou 'NEUTRE'
    """
    hours_since = peak_info['hours_since_peak']
    peak_type = peak_info['peak_type']
    peak_price = peak_info['peak_price']
    
    print(f"\n🔍 ANALYSE TENDANCE DEPUIS PIC :")
    print(f"   Pic type : {peak_type}")
    print(f"   Pic prix : {peak_price:.5f}")
    print(f"   Prix actuel : {event_price:.5f}")
    print(f"   Temps écoulé : {hours_since:.1f}h")
    
    if peak_type == 'HIGH':
        # Pic était un HIGH
        if event_price < peak_price:
            # Prix en dessous du high
            if hours_since > 12:
                trend = 'BAISSIER'
                print(f"   → Prix BAISSE depuis high pendant {hours_since:.1f}h → BAISSIER ✅")
            else:
                trend = 'NEUTRE'
                print(f"   → Consolidation récente ({hours_since:.1f}h) → NEUTRE")
        else:
            # Prix remonte vers high
            trend = 'HAUSSIER'
            print(f"   → Prix REMONTE vers high → HAUSSIER")
    
    else:  # peak_type == 'LOW'
        # Pic était un LOW
        if event_price > peak_price:
            # Prix au-dessus du low
            if hours_since > 12:
                trend = 'HAUSSIER'
                print(f"   → Prix REBONDIT depuis low pendant {hours_since:.1f}h → HAUSSIER ✅")
            else:
                trend = 'NEUTRE'
                print(f"   → Consolidation récente ({hours_since:.1f}h) → NEUTRE")
        else:
            # Prix continue à baisser
            trend = 'BAISSIER'
            print(f"   → Prix CONTINUE à baisser → BAISSIER")
    
    return trend


def calculate_direction_sentiment(indicators: Dict, peak_info: Dict, trend: str) -> float:
    """
    Calcule direction_sentiment depuis vraie tendance
    
    CORRECTION SESSION 92.9 :
    ==========================
    Utilise trend calculé (pas distance pic)
    
    Args:
        indicators: Dict depuis calculate_24h_indicators()
        peak_info: Dict depuis find_last_absolute_peak()
        trend: 'HAUSSIER', 'BAISSIER', 'NEUTRE' (depuis determine_trend_from_peak)
    
    Returns:
        float: direction_sentiment entre -1.0 et +1.0
    """
    # Composantes sentiment
    momentum = indicators['momentum_24h_pct']
    position = indicators['position_in_range']
    
    # Base sentiment depuis tendance (CORRIGÉ Session 92.9)
    if trend == 'HAUSSIER':
        base_sentiment = +0.5  # Marché monte
    elif trend == 'BAISSIER':
        base_sentiment = -0.5  # Marché baisse
    else:  # NEUTRE
        base_sentiment = 0.0  # Pas de tendance claire
    
    # Ajustement momentum
    momentum_adjustment = momentum / 100 * 0.3  # Max ±0.3
    
    # Ajustement position (extrêmes renforcent)
    if position > 0.8:
        position_adjustment = +0.2  # Très haut dans range
    elif position < 0.2:
        position_adjustment = -0.2  # Très bas dans range
    else:
        position_adjustment = 0.0
    
    # Combinaison
    direction_sentiment = base_sentiment + momentum_adjustment + position_adjustment
    direction_sentiment = max(-1.0, min(1.0, direction_sentiment))  # Clamp [-1, +1]
    
    print(f"\n💭 CALCUL DIRECTION_SENTIMENT :")
    print(f"   Tendance base : {trend} → {base_sentiment:+.2f}")
    print(f"   Momentum : {momentum:+.2f}% → {momentum_adjustment:+.2f}")
    print(f"   Position range : {position:.2f} → {position_adjustment:+.2f}")
    print(f"   → Direction_sentiment = {direction_sentiment:+.2f}")
    
    return direction_sentiment


def calculate_combined_factor(surprise_net: float, direction_sentiment: float) -> float:
    """
    Calcule facteur combiné (surprise nette + direction sentiment)
    
    Formule :
    combined = direction_factor × (1 + direction_sentiment × 0.1)
    
    Args:
        surprise_net: Surprise nette en % (ex: +33.6)
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
    # direction_sentiment entre -1 et +1
    # Si marché haussier (+1) → Amplifie légèrement (+10%)
    # Si marché baissier (-1) → Atténue légèrement (-10%)
    combined = direction_factor * (1 + direction_sentiment * 0.1)
    
    print(f"\n🔢 FACTEUR COMBINÉ :")
    print(f"   Direction factor (V2) : {direction_factor:.3f}")
    print(f"   Direction sentiment : {direction_sentiment:+.2f}")
    print(f"   Combined factor : {combined:.3f}")
    
    return combined
