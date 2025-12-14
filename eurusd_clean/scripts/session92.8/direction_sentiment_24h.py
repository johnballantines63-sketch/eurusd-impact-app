"""
MODULE DIRECTION_SENTIMENT - ANALYSE 24 HEURES

Date : 29 octobre 2025 - Session 92.8
Méthodologie validée par André Valentin

PRINCIPE FONDAMENTAL :
- Analyser 24 HEURES avant annonce (PAS 2h)
- Identifier dernier pic absolu (HIGH ou LOW)
- Déterminer vraie tendance depuis pic
- Combiner avec surprise nette

OBJECTIF :
- Réduire régressions sur surprises positives
- MAE 4 dates CPI < 5 pips
- 0 régressions vs baseline
"""

from datetime import datetime, timedelta
from typing import Dict
import pandas as pd
import duckdb


def load_prices_24h_before(event_time: datetime, conn) -> pd.DataFrame:
    """
    Charge prix EURUSD 24h avant événement
    
    PÉRIODE : [event_time - 24h, event_time]
    
    Args:
        event_time: Timestamp événement (ex: 2025-09-11 14:30:00+02:00)
        conn: Connexion DuckDB
    
    Returns:
        DataFrame avec colonnes: datetime, open, high, low, close
        
    Exemple:
        event_time = 2025-09-11 14:30:00+02:00
        → Charge prix de 2025-09-10 14:30:00 à 2025-09-11 14:30:00
        → Environ 1440 lignes (1 minute × 24h)
    """
    # Période : [event_time - 24h, event_time]
    start_time = event_time - timedelta(hours=24)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= ?
      AND datetime < ?
    ORDER BY datetime ASC
    """
    
    df = conn.execute(query, [start_time, event_time]).df()
    
    print(f"✅ Chargé {len(df)} lignes prix 24h avant ({start_time} → {event_time})")
    
    return df


def find_last_absolute_peak(prices_df: pd.DataFrame, event_price: float) -> Dict:
    """
    Identifie le dernier pic absolu dans période 24h
    
    DÉFINITION PIC ABSOLU:
    - High maximum dans période 24h
    - Ou Low minimum dans période 24h
    
    SÉLECTION:
    - Si prix actuel plus proche du high → Pic = high (tendance haussière)
    - Si prix actuel plus proche du low → Pic = low (tendance baissière)
    
    Args:
        prices_df: DataFrame prix 24h (depuis load_prices_24h_before)
        event_price: Prix au moment de l'événement (close à T)
    
    Returns:
        dict: {
            'peak_price': float,
            'peak_time': datetime,
            'peak_type': 'HIGH' ou 'LOW',
            'distance_pips': float,
            'hours_since_peak': float
        }
        
    Exemple:
        Prix actuel: 1.1735
        High 24h: 1.1750 (à T-8h)
        Low 24h: 1.1680 (à T-18h)
        
        Distance high: |1.1735 - 1.1750| = 0.0015 = 15 pips
        Distance low: |1.1735 - 1.1680| = 0.0055 = 55 pips
        
        → Pic = HIGH (plus proche)
        → Type = 'HIGH'
        → Distance = -15 pips (en dessous du high)
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
        # Prix proche du high → Tendance haussière possible
        peak_type = 'HIGH'
        peak_price = peak_high
        peak_time = time_high
        distance_pips = (event_price - peak_high) * 10000  # Négatif si en dessous
        
        print(f"📈 Dernier pic = HIGH à {peak_price:.5f} (distance: {distance_pips:.1f} pips)")
    else:
        # Prix proche du low → Tendance baissière possible
        peak_type = 'LOW'
        peak_price = peak_low
        peak_time = time_low
        distance_pips = (event_price - peak_low) * 10000  # Positif si au dessus
        
        print(f"📉 Dernier pic = LOW à {peak_price:.5f} (distance: {distance_pips:.1f} pips)")
    
    # Calculer temps depuis pic
    hours_since_peak = (prices_df.iloc[-1]['datetime'] - peak_time).total_seconds() / 3600
    
    return {
        'peak_price': peak_price,
        'peak_time': peak_time,
        'peak_type': peak_type,
        'distance_pips': distance_pips,
        'hours_since_peak': hours_since_peak
    }


def determine_trend_from_peak(peak_info: Dict, event_price: float, event_time: datetime) -> str:
    """
    Détermine VRAIE tendance depuis pic (correction André Session 92.9)
    
    PROBLÈME SESSION 92.8:
    - Distance du pic ≠ Direction tendance
    - Prix proche high ≠ Tendance haussière
    
    CORRECTION:
    - Analyser si prix MONTE ou BAISSE depuis pic
    - Tenir compte TEMPS écoulé depuis pic
    
    RÈGLES:
    - Si prix < peak HIGH ET temps > 12h → BAISSIER (correction)
    - Si prix > peak LOW ET temps > 12h → HAUSSIER (rebond)
    - Si temps < 12h → NEUTRE (consolidation)
    
    Args:
        peak_info: Dict depuis find_last_absolute_peak()
        event_price: Prix au moment événement
        event_time: Timestamp événement
    
    Returns:
        str: 'HAUSSIER', 'BAISSIER', ou 'NEUTRE'
        
    Exemple:
        Pic HIGH à 1.17289 (10.09 17h08)
        Prix événement: 1.1732 (11.09 14h30)
        Temps écoulé: 21h
        
        → Prix < peak HIGH (baisse depuis pic)
        → Temps > 12h (tendance établie)
        → Retourne: 'BAISSIER' ✅
    """
    hours_since_peak = peak_info['hours_since_peak']
    peak_price = peak_info['peak_price']
    peak_type = peak_info['peak_type']
    
    if peak_type == 'HIGH':
        # Pic était un high
        if event_price < peak_price:
            # Prix EN DESSOUS du high
            if hours_since_peak > 12:
                return 'BAISSIER'  # Correction depuis high (tendance établie)
            else:
                return 'NEUTRE'    # Consolidation récente (< 12h)
        else:
            # Prix remonte vers high ou au-dessus
            return 'HAUSSIER'
    
    else:  # peak_type == 'LOW'
        # Pic était un low
        if event_price > peak_price:
            # Prix AU DESSUS du low
            if hours_since_peak > 12:
                return 'HAUSSIER'  # Rebond depuis low (tendance établie)
            else:
                return 'NEUTRE'    # Consolidation récente (< 12h)
        else:
            # Prix continue à baisser ou au niveau low
            return 'BAISSIER'


def calculate_24h_indicators(prices_df: pd.DataFrame, peak_info: Dict, event_price: float) -> Dict:
    """
    Calcule indicateurs techniques sur période 24h
    
    INDICATEURS:
    1. Range 24h : high - low (volatilité absolue)
    2. ATR 24h : Average True Range (volatilité moyenne)
    3. Momentum 24h : (prix actuel - prix T-24h) / prix T-24h
    4. Position dans range : (prix - low) / (high - low)
    5. Distance du pic : Depuis find_last_absolute_peak()
    
    Args:
        prices_df: DataFrame prix 24h
        peak_info: Dict depuis find_last_absolute_peak()
        event_price: Prix au moment événement
    
    Returns:
        dict: {
            'range_24h_pips': float,
            'atr_24h_pips': float,
            'momentum_24h_pct': float,
            'position_in_range': float (0 à 1),
            'distance_from_peak_pips': float,
            'hours_since_peak': float
        }
        
    Exemple:
        Range 24h: 45 pips
        ATR 24h: 28 pips (faible)
        Momentum: +0.15% (haussier)
        Position: 0.65 (haut de range)
    """
    # Range 24h
    high_24h = prices_df['high'].max()
    low_24h = prices_df['low'].min()
    range_24h_pips = (high_24h - low_24h) * 10000
    
    # ATR 24h (simplifié : moyenne des ranges)
    prices_df = prices_df.copy()
    prices_df['range'] = (prices_df['high'] - prices_df['low']) * 10000
    atr_24h_pips = prices_df['range'].mean()
    
    # Momentum 24h
    price_start_24h = prices_df.iloc[0]['close']
    momentum_24h_pct = ((event_price - price_start_24h) / price_start_24h) * 100
    
    # Position dans range
    if (high_24h - low_24h) > 0:
        position_in_range = (event_price - low_24h) / (high_24h - low_24h)
    else:
        position_in_range = 0.5
    
    print(f"📊 Range 24h: {range_24h_pips:.1f} pips | ATR: {atr_24h_pips:.1f} pips")
    print(f"📊 Momentum 24h: {momentum_24h_pct:+.2f}% | Position range: {position_in_range:.2f}")
    
    return {
        'range_24h_pips': range_24h_pips,
        'atr_24h_pips': atr_24h_pips,
        'momentum_24h_pct': momentum_24h_pct,
        'position_in_range': position_in_range,
        'distance_from_peak_pips': peak_info['distance_pips'],
        'hours_since_peak': peak_info['hours_since_peak']
    }


def calculate_direction_sentiment(indicators: Dict, peak_info: Dict, trend: str) -> float:
    """
    Calcule score direction_sentiment basé sur analyse 24h
    CORRECTION SESSION 92.9 : Ajout paramètre 'trend'
    
    LOGIQUE PONDÉRATION:
    1. Tendance depuis pic (poids 40%) - UTILISER TREND AU LIEU DE DISTANCE
       - HAUSSIER → +0.4
       - BAISSIER → -0.4
       - NEUTRE → 0.0
    
    2. Momentum 24h (poids 30%)
       - Momentum > 0 → Haussier
       - Momentum < 0 → Baissier
    
    3. Position dans range (poids 20%)
       - > 0.7 → Haussier (sommet range)
       - < 0.3 → Baissier (bas range)
    
    4. Volatilité (poids 10%)
       - ATR faible + tendance claire → Amplifier sentiment
       - ATR forte → Atténuer sentiment (incertitude)
    
    Args:
        indicators: Dict depuis calculate_24h_indicators()
        peak_info: Dict depuis find_last_absolute_peak()
        trend: str depuis determine_trend_from_peak() ('HAUSSIER', 'BAISSIER', 'NEUTRE')
    
    Returns:
        float: Score -1 (baissier fort) à +1 (haussier fort)
        
    Exemple (CORRIGÉ 2025-09-11):
        Trend: BAISSIER (correction 21h depuis HIGH)
        Momentum: +0.09%
        Position: 0.85
        ATR: 1.5 pips (faible)
        
        → Score = -0.4 + 0.0 + 0.2 + 0.0 = -0.2
        → direction_sentiment = -0.2 (baissier modéré) ✅
    """
    score = 0.0
    
    # 1. Tendance depuis pic (40%) - UTILISER TREND AU LIEU DE DISTANCE
    if trend == 'HAUSSIER':
        score += 0.4
        print(f"  → Tendance pic: +0.4 (tendance HAUSSIÈRE établie)")
    elif trend == 'BAISSIER':
        score -= 0.4
        print(f"  → Tendance pic: -0.4 (tendance BAISSIÈRE établie)")
    else:  # NEUTRE
        score += 0.0
        print(f"  → Tendance pic: 0.0 (consolidation neutre)")
    
    # 2. Momentum 24h (30%) - GARDER TEL QUEL
    momentum = indicators['momentum_24h_pct']
    if momentum > 0.2:
        score += 0.3
        print(f"  → Momentum: +0.3 (fort haussier)")
    elif momentum > 0.05:
        score += 0.15
        print(f"  → Momentum: +0.15 (haussier)")
    elif momentum < -0.2:
        score -= 0.3
        print(f"  → Momentum: -0.3 (fort baissier)")
    elif momentum < -0.05:
        score -= 0.15
        print(f"  → Momentum: -0.15 (baissier)")
    else:
        print(f"  → Momentum: 0.0 (neutre)")
    
    # 3. Position dans range (20%)
    position = indicators['position_in_range']
    if position > 0.7:
        score += 0.2  # Sommet range
        print(f"  → Position range: +0.2 (sommet)")
    elif position > 0.5:
        score += 0.1
        print(f"  → Position range: +0.1 (haut)")
    elif position < 0.3:
        score -= 0.2  # Bas range
        print(f"  → Position range: -0.2 (bas)")
    elif position < 0.5:
        score -= 0.1
        print(f"  → Position range: -0.1 (bas)")
    else:
        print(f"  → Position range: 0.0 (milieu)")
    
    # 4. Volatilité (10%)
    atr = indicators['atr_24h_pips']
    if atr < 30 and abs(score) > 0.3:
        score *= 1.1  # Amplifier conviction
        print(f"  → Volatilité: ×1.1 (ATR faible, amplification)")
    elif atr > 60:
        score *= 0.9  # Atténuer conviction
        print(f"  → Volatilité: ×0.9 (ATR forte, atténuation)")
    else:
        print(f"  → Volatilité: ×1.0 (ATR normale)")
    
    # Borner entre -1 et +1
    final_score = max(-1.0, min(1.0, score))
    
    print(f"🎯 Direction_sentiment final: {final_score:+.2f}")
    
    return final_score


def calculate_combined_factor(surprise_net: float, direction_sentiment: float) -> float:
    """
    Combine surprise nette ET direction_sentiment
    
    HYPOTHÈSE:
    - Si surprise nette positive + marché haussier → Amplification
    - Si surprise nette positive + marché baissier → Atténuation
    - Si surprise nette négative + marché baissier → Amplification
    - Si surprise nette négative + marché haussier → Atténuation
    
    FORMULE:
    combined_factor = direction_factor_v2 × (1 + direction_sentiment × 0.1)
    
    Args:
        surprise_net: Surprise nette en %
        direction_sentiment: Score -1 à +1
    
    Returns:
        float: Facteur combiné (0.65 à 1.15 environ)
        
    Exemple:
        surprise_net = +33.6%
        direction_sentiment = +0.5
        
        direction_factor = 1.05 (surprise > 30%)
        combined = 1.05 × (1 + 0.5 × 0.1)
        combined = 1.05 × 1.05 = 1.1025
    """
    # Facteur direction depuis surprise nette (V2)
    if surprise_net > 30:
        direction_factor = 1.05
    elif surprise_net > 0:
        direction_factor = min(1.0 + (surprise_net / 200), 1.05)
    elif surprise_net >= -30:
        direction_factor = max(1.0 + (surprise_net / 100), 0.7)
    else:
        direction_factor = 0.7
    
    # Ajustement par direction_sentiment (±10% max)
    combined_factor = direction_factor * (1 + direction_sentiment * 0.1)
    
    print(f"\n🔧 FACTEURS:")
    print(f"  Surprise nette: {surprise_net:+.1f}%")
    print(f"  Direction factor V2: {direction_factor:.3f}")
    print(f"  Direction sentiment: {direction_sentiment:+.2f}")
    print(f"  Combined factor: {combined_factor:.3f}")
    
    return combined_factor


if __name__ == "__main__":
    print("Module direction_sentiment_24h.py chargé.")
    print("Fonctions disponibles:")
    print("  - load_prices_24h_before()")
    print("  - find_last_absolute_peak()")
    print("  - calculate_24h_indicators()")
    print("  - calculate_direction_sentiment()")
    print("  - calculate_combined_factor()")
