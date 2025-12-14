"""
Nouvelle fonction pour générer la courbe avec phases multiples et pullback
À intégrer dans price_curve_generator.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

def sigmoid(x):
    """Fonction sigmoïde pour mouvement progressif réaliste"""
    return 1 / (1 + np.exp(-x))


def generate_candlestick_curve_from_phases(
    start_price: float,
    phases: List[Dict],
    base_time: datetime,
    duration_minutes: int = 120,
    volatility_factor: float = 0.3,
    spread_pips: float = 0.0
) -> pd.DataFrame:
    """
    Génère courbe de chandeliers à partir de PHASES (v8.6)
    Gère le pullback entre phases rapprochées
    
    Args:
        start_price: Prix EUR/USD de départ
        phases: Liste des phases retournées par sequence_multi_event_timeline_v86
        base_time: Timestamp de référence
        duration_minutes: Durée totale à simuler
        volatility_factor: Facteur de volatilité (0-1)
        spread_pips: Spread bid/ask en pips
    
    Returns:
        DataFrame avec time, open, high, low, close, bid, ask, phase_num, phase_type
    """
    
    candles = []
    current_price = start_price
    spread_price = spread_pips / 10000
    
    # Convertir les phases en format utilisable
    phases_data = []
    for phase in phases:
        phase_start = pd.to_datetime(phase['start_time'])
        
        # Calculer le temps au pic (TTR ou durée)
        ttr = phase.get('ttr_real', phase.get('ttr_predicted', 30))
        
        phases_data.append({
            'num': phase['phase_num'],
            'start_time': phase_start,
            'latency_minutes': phase['latency_minutes'],
            'ttr_minutes': ttr,
            'impact_pips': phase['impact_combined'],
            'direction': 1 if phase['direction'] == 'UP' else -1,
            'pullback_pips': phase.get('pullback_pips', 0)
        })
    
    # Simuler minute par minute
    for minute in range(duration_minutes + 1):
        current_time = base_time + timedelta(minutes=minute)
        
        # Déterminer quelle phase est active
        target_price = start_price
        active_phase_num = 0
        phase_type = "stable"
        cumulative_impact = 0.0
        
        for phase in phases_data:
            minutes_since_phase_start = (current_time - phase['start_time']).total_seconds() / 60
            
            if minutes_since_phase_start < 0:
                # Pas encore commencé
                continue
            
            elif minutes_since_phase_start < phase['latency_minutes']:
                # Phase latence
                active_phase_num = phase['num']
                phase_type = f"Phase {phase['num']} - Latence"
                # Pas de mouvement pendant la latence
            
            elif minutes_since_phase_start < phase['ttr_minutes']:
                # Phase mouvement
                active_phase_num = phase['num']
                phase_type = f"Phase {phase['num']} - Mouvement"
                
                # Progress dans le mouvement (0 à 1)
                movement_time = minutes_since_phase_start - phase['latency_minutes']
                total_movement_time = phase['ttr_minutes'] - phase['latency_minutes']
                
                if total_movement_time > 0:
                    progress = movement_time / total_movement_time
                    sigmoid_progress = sigmoid(10 * (progress - 0.5))
                    
                    # Impact de cette phase (en prix)
                    phase_impact_price = (phase['impact_pips'] / 10000) * phase['direction']
                    
                    # Appliquer le pullback si présent
                    pullback_price = (phase['pullback_pips'] / 10000) * (-phase['direction'])
                    
                    # Mouvement total = impact - pullback
                    cumulative_impact += (phase_impact_price + pullback_price) * sigmoid_progress
            
            else:
                # Phase terminée, impact complet atteint
                phase_impact_price = (phase['impact_pips'] / 10000) * phase['direction']
                pullback_price = (phase['pullback_pips'] / 10000) * (-phase['direction'])
                cumulative_impact += phase_impact_price + pullback_price
                
                # Retracement après le pic (Fibonacci 38.2%)
                time_since_peak = minutes_since_phase_start - phase['ttr_minutes']
                if time_since_peak < 20:  # Retracement sur 20 minutes
                    retracement_progress = min(1.0, time_since_peak / 20)
                    exp_progress = 1 - np.exp(-3 * retracement_progress)
                    retracement = (phase_impact_price + pullback_price) * 0.382 * exp_progress
                    cumulative_impact -= retracement
                    
                    if active_phase_num == 0 or active_phase_num < phase['num']:
                        active_phase_num = phase['num']
                        phase_type = f"Phase {phase['num']} - Retracement"
        
        target_price = start_price + cumulative_impact
        
        # Générer chandelier simplifié
        volatility = 0.00003 * volatility_factor
        close_noise = np.random.normal(0, volatility * 0.5)
        close_price = current_price + (target_price - current_price) * 0.8 + close_noise
        
        # High/Low
        high_extension = abs(np.random.normal(0, volatility * 1.5))
        low_extension = abs(np.random.normal(0, volatility * 1.5))
        
        high_price = max(current_price, close_price) + high_extension
        low_price = min(current_price, close_price) - low_extension
        
        # Bid/Ask
        bid_close = close_price - spread_price / 2
        ask_close = close_price + spread_price / 2
        
        candles.append({
            'time': current_time,
            'open': current_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'bid': bid_close,
            'ask': ask_close,
            'phase_num': active_phase_num,
            'phase_type': phase_type,
            'minute_offset': minute
        })
        
        current_price = close_price
    
    return pd.DataFrame(candles)
