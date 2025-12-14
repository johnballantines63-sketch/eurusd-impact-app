"""
DÉTECTION TENDANCE OPTIMISÉE - PRODUCTION
=========================================

Méthode validée Session 103 :
- Approche TOP-N (simple et robuste)
- Fenêtre dynamique (14 jours, pas 72h)
- Filtre 48h minimum avant événement
- Capture vraies tendances et inversions

Auteur : Session 103
Date : 30 octobre 2025
"""

import numpy as np
import pandas as pd
from scipy.stats import linregress
from datetime import timedelta


def find_top_n_extrema(prices, timestamps, top_n=5, min_hours_apart=12):
    """
    Trouve les TOP N prix les plus hauts et les plus bas
    Élimine doublons temporels (pics trop proches)
    
    Args:
        prices: array numpy de prix
        timestamps: list de timestamps pandas
        top_n: nombre d'extrema par type (HIGH/LOW)
        min_hours_apart: espacement minimum entre extrema (heures)
    
    Returns:
        list: extrema triés chronologiquement
    """
    
    min_minutes_apart = min_hours_apart * 60
    
    # ========== HIGHS ==========
    high_indices = np.argsort(prices)[::-1]  # Décroissant
    
    selected_highs = []
    for idx in high_indices:
        # Vérifier espacement
        too_close = False
        for selected in selected_highs:
            if abs(idx - selected['index']) < min_minutes_apart:
                too_close = True
                break
        
        if not too_close:
            selected_highs.append({
                'type': 'HIGH',
                'index': int(idx),
                'price': float(prices[idx]),
                'timestamp': timestamps[idx] if idx < len(timestamps) else None
            })
        
        if len(selected_highs) >= top_n:
            break
    
    # ========== LOWS ==========
    low_indices = np.argsort(prices)  # Croissant
    
    selected_lows = []
    for idx in low_indices:
        too_close = False
        for selected in selected_lows:
            if abs(idx - selected['index']) < min_minutes_apart:
                too_close = True
                break
        
        if not too_close:
            selected_lows.append({
                'type': 'LOW',
                'index': int(idx),
                'price': float(prices[idx]),
                'timestamp': timestamps[idx] if idx < len(timestamps) else None
            })
        
        if len(selected_lows) >= top_n:
            break
    
    # Combiner et trier chronologiquement
    all_extrema = selected_highs + selected_lows
    all_extrema.sort(key=lambda x: x['index'])
    
    return all_extrema


def detect_inversions(extrema, prices, timestamps, 
                     min_amplitude_pips=30,
                     min_hours_before_event=48):
    """
    Détecte inversions de tendance entre extrema
    
    Args:
        extrema: list d'extrema de find_top_n_extrema()
        prices: array numpy de prix
        timestamps: list de timestamps pandas
        min_amplitude_pips: amplitude minimum pour inversion valide
        min_hours_before_event: temps minimum avant événement
    
    Returns:
        list: inversions détectées
    """
    
    inversions = []
    
    for extremum in extrema:
        start_idx = extremum['index']
        end_idx = len(prices) - 1
        
        if end_idx - start_idx < 60:  # Au moins 1h
            continue
        
        # FILTRE : Au moins 48h avant événement
        hours_before_event = (end_idx - start_idx) / 60.0
        if hours_before_event < min_hours_before_event:
            continue
        
        # Segment
        segment_prices = prices[start_idx:end_idx + 1]
        amplitude = (segment_prices.max() - segment_prices.min()) * 10000
        
        if amplitude < min_amplitude_pips:
            continue
        
        # Durée
        if start_idx < len(timestamps) and end_idx < len(timestamps):
            duration_hours = (timestamps[end_idx] - timestamps[start_idx]).total_seconds() / 3600
        else:
            duration_hours = (end_idx - start_idx) / 60.0
        
        # Direction
        price_start = prices[start_idx]
        price_end = prices[end_idx]
        
        # R²
        t = np.arange(len(segment_prices))
        slope, intercept, r_value, _, _ = linregress(t, segment_prices)
        r_squared = r_value ** 2
        
        # Type inversion
        if extremum['type'] == 'HIGH' and price_end < price_start:
            inversion_type = 'HIGH_TO_LOW'
        elif extremum['type'] == 'LOW' and price_end > price_start:
            inversion_type = 'LOW_TO_HIGH'
        else:
            continue
        
        inversions.append({
            'type': inversion_type,
            'reversal_point': extremum,
            'amplitude_pips': amplitude,
            'duration_hours': duration_hours,
            'r_squared': r_squared,
            'end_price': price_end
        })
    
    return inversions


def detect_trend_dynamic(event_datetime, conn, 
                        lookback_days=14,
                        top_n=5,
                        min_hours_apart=12,
                        min_hours_before_event=48,
                        min_amplitude_pips=30):
    """
    Détecte la tendance actuelle avant un événement
    
    Méthode :
    1. Charge N jours de données (pas 72h fixe !)
    2. Identifie TOP N extrema (prix les plus hauts/bas)
    3. Détecte inversions de tendance
    4. Retourne dernière inversion = tendance actuelle
    
    Args:
        event_datetime: datetime de l'événement (timezone-aware UTC)
        conn: connexion DuckDB
        lookback_days: jours de données à charger (défaut 14)
        top_n: nombre d'extrema par type (défaut 5)
        min_hours_apart: espacement min entre extrema (défaut 12h)
        min_hours_before_event: temps min avant événement (défaut 48h)
        min_amplitude_pips: amplitude min tendance (défaut 30 pips)
    
    Returns:
        dict ou None
    """
    
    # Charger données
    lookback_time = event_datetime - timedelta(days=lookback_days)
    
    query = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= ?
      AND datetime < ?
    ORDER BY datetime ASC
    """
    
    try:
        df_prices = conn.execute(query, [lookback_time, event_datetime]).fetchdf()
    except Exception as e:
        print(f"Erreur query prices : {e}")
        return None
    
    if len(df_prices) < 1000:  # Au moins ~16h de données
        return None
    
    prices = df_prices['close'].values
    timestamps = pd.to_datetime(df_prices['datetime']).tolist()
    
    # Trouver extrema
    extrema = find_top_n_extrema(
        prices, 
        timestamps,
        top_n=top_n,
        min_hours_apart=min_hours_apart
    )
    
    if len(extrema) == 0:
        return None
    
    # Détecter inversions
    inversions = detect_inversions(
        extrema,
        prices,
        timestamps,
        min_amplitude_pips=min_amplitude_pips,
        min_hours_before_event=min_hours_before_event
    )
    
    if len(inversions) == 0:
        return None
    
    # Prendre dernière inversion (tendance actuelle)
    current_trend = inversions[-1]
    rev = current_trend['reversal_point']
    
    # Direction
    if current_trend['type'] == 'HIGH_TO_LOW':
        direction = 'DOWN'
    else:
        direction = 'UP'
    
    return {
        'type': current_trend['type'],
        'reversal_datetime': rev['timestamp'],
        'reversal_price': rev['price'],
        'duration_hours': current_trend['duration_hours'],
        'amplitude_pips': current_trend['amplitude_pips'],
        'r_squared': current_trend['r_squared'],
        'direction': direction,
        'end_price': current_trend['end_price']
    }


def calculate_trend_strength_score(trend_info):
    """
    Calcule score force tendance (0-100)
    
    Critères :
    - R² (40% du score)
    - Durée (30% du score)
    - Amplitude (30% du score)
    """
    
    if trend_info is None:
        return 0.0
    
    r2 = trend_info['r_squared']
    duration = trend_info['duration_hours']
    amplitude = trend_info['amplitude_pips']
    
    # R² (40%)
    r2_score = r2 * 40
    
    # Durée (30%) - optimal 48-72h
    if duration >= 48:
        duration_score = 30
    elif duration >= 24:
        duration_score = (duration / 48) * 30
    else:
        duration_score = (duration / 24) * 15
    
    # Amplitude (30%) - optimal > 80 pips
    if amplitude >= 80:
        amplitude_score = 30
    elif amplitude >= 40:
        amplitude_score = (amplitude / 80) * 30
    else:
        amplitude_score = (amplitude / 40) * 15
    
    total_score = r2_score + duration_score + amplitude_score
    
    return min(total_score, 100.0)
