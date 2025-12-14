"""
SESSION 110 - DÉTECTION INVERSION (COPIE EXACTE SESSION 107)
=============================================================

Copie EXACTE de la méthodologie Session 107 Phase 2E
Sans modification !

Date : 3 novembre 2025
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from scipy.stats import linregress
from typing import Optional, Dict

def detect_trend_by_inversion_S107(
    df_prices: pd.DataFrame,
    event_datetime: pd.Timestamp,
    lookback_days: int = 14,
    segment_hours: int = 12,
    min_r2_for_trend: float = 0.3,
    min_hours_before_event: int = 24
) -> Optional[Dict]:
    """
    COPIE EXACTE Session 107 Phase 2E
    
    Détecte tendance en cherchant dernière inversion majeure
    
    Params:
    - segment_hours: Durée segments pour analyse tendance
    - min_r2_for_trend: R² minimum pour considérer tendance valide
    - min_hours_before_event: Ignore inversions trop récentes
    """
    # Timestamp
    event_dt = pd.to_datetime(event_datetime)
    query_dt = event_dt - timedelta(hours=2)  # CLÉMENT : -2h comme Session 107
    
    # Période d'analyse
    start_dt = query_dt - timedelta(days=lookback_days)
    
    # Filtrer prix
    mask = (df_prices['datetime'] >= start_dt) & (df_prices['datetime'] < query_dt)
    df_window = df_prices[mask].copy()
    
    if len(df_window) < 1000:
        return None
    
    # === ÉTAPE 1 : DÉCOUPER EN SEGMENTS ET CALCULER TENDANCES ===
    
    segment_duration = timedelta(hours=segment_hours)
    current_time = start_dt
    segments = []
    
    while current_time < query_dt:
        end_time = current_time + segment_duration
        
        # Filtrer données segment
        mask = (df_window['datetime'] >= current_time) & (df_window['datetime'] < end_time)
        df_segment = df_window[mask].copy()
        
        if len(df_segment) < 100:
            current_time = end_time
            continue
        
        # Régression linéaire
        df_segment['time_numeric'] = (df_segment['datetime'] - df_segment['datetime'].iloc[0]).dt.total_seconds()
        X = df_segment['time_numeric'].values
        y = df_segment['close'].values
        
        try:
            slope, intercept, r_value, p_value, std_err = linregress(X, y)
            r2 = r_value ** 2
            
            # Déterminer direction
            if slope > 0:
                direction = 'UP'
            elif slope < 0:
                direction = 'DOWN'
            else:
                direction = 'FLAT'
            
            segments.append({
                'start': current_time,
                'end': end_time,
                'direction': direction,
                'slope': slope,
                'r2': r2,
                'num_points': len(df_segment),
                'price_start': df_segment['close'].iloc[0],
                'price_end': df_segment['close'].iloc[-1]
            })
            
        except Exception:
            pass
        
        current_time = end_time
    
    if len(segments) < 3:
        return None
    
    # === ÉTAPE 2 : DÉTECTER INVERSIONS ===
    
    inversions = []
    
    for i in range(len(segments) - 1):
        seg_before = segments[i]
        seg_after = segments[i + 1]
        
        # Vérifier inversion de direction
        if seg_before['direction'] == seg_after['direction']:
            continue
        
        if seg_before['direction'] == 'FLAT' or seg_after['direction'] == 'FLAT':
            continue
        
        # Vérifier qualité tendances (R² suffisant)
        if seg_before['r2'] < min_r2_for_trend and seg_after['r2'] < min_r2_for_trend:
            continue  # Au moins un côté doit avoir tendance claire
        
        # Type inversion
        if seg_before['direction'] == 'UP' and seg_after['direction'] == 'DOWN':
            inversion_type = 'PEAK'  # Pic
        elif seg_before['direction'] == 'DOWN' and seg_after['direction'] == 'UP':
            inversion_type = 'TROUGH'  # Creux
        else:
            continue
        
        # Point d'inversion = chercher dans zone transition
        # Chercher pic/creux entre début segment avant et fin segment après
        search_start = seg_before['start']
        search_end = seg_after['end']
        
        mask = (df_window['datetime'] >= search_start) & (df_window['datetime'] <= search_end)
        df_inv = df_window[mask]
        
        if len(df_inv) == 0:
            continue
        
        if inversion_type == 'PEAK':
            inv_idx = df_inv['high'].idxmax()
            inv_price = df_inv.loc[inv_idx, 'high']
        else:
            inv_idx = df_inv['low'].idxmin()
            inv_price = df_inv.loc[inv_idx, 'low']
        
        inv_datetime = df_inv.loc[inv_idx, 'datetime']
        hours_before = (query_dt - inv_datetime).total_seconds() / 3600
        
        inversions.append({
            'type': inversion_type,
            'datetime': inv_datetime,
            'price': inv_price,
            'hours_before_event': hours_before,
            'seg_before': seg_before,
            'seg_after': seg_after,
            'quality_score': (seg_before['r2'] + seg_after['r2']) / 2
        })
    
    if len(inversions) == 0:
        return None
    
    # === ÉTAPE 3 : FILTRER INVERSIONS TROP RÉCENTES ===
    
    valid_inversions = [inv for inv in inversions 
                       if inv['hours_before_event'] >= min_hours_before_event]
    
    if len(valid_inversions) == 0:
        return None
    
    # === ÉTAPE 4 : PRENDRE DERNIÈRE INVERSION VALIDE ===
    
    # Trier par qualité et temps
    valid_inversions = sorted(valid_inversions, 
                             key=lambda x: (x['datetime'], x['quality_score']), 
                             reverse=True)
    
    reversal = valid_inversions[0]
    
    # === ÉTAPE 5 : MESURER TENDANCE DEPUIS INVERSION ===
    
    reversal_datetime = reversal['datetime']
    df_trend = df_window[df_window['datetime'] >= reversal_datetime].copy()
    
    if len(df_trend) < 100:
        return None
    
    # Durée
    duration_hours = (query_dt - reversal_datetime).total_seconds() / 3600
    
    # Régression
    df_trend['timestamp_numeric'] = (df_trend['datetime'] - reversal_datetime).dt.total_seconds()
    X = df_trend['timestamp_numeric'].values
    y = df_trend['close'].values
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(X, y)
        r2 = r_value ** 2
    except:
        r2 = 0
    
    # Métriques
    amplitude_pips = (df_trend['high'].max() - df_trend['low'].min()) * 10000
    volatility_pips = df_trend['close'].std() * 10000
    
    return {
        'inversion_time': reversal_datetime,
        'inversion_type': reversal['type'],
        'hours_before_event': duration_hours,
        'r2_linear': r2,
        'volatility_pips': volatility_pips,
        'amplitude_pips': amplitude_pips,
        'r2_before': reversal['seg_before']['r2'],
        'r2_after': reversal['seg_after']['r2'],
        'trend_before': reversal['seg_before']['direction'],
        'trend_after': reversal['seg_after']['direction'],
        'quality_score': reversal['quality_score']
    }


if __name__ == "__main__":
    # Test basique
    print("Module détection inversion Session 107 - Chargé ✅")
