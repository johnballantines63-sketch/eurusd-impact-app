"""
Détection de tendance par inversion (Session 107 - Validée)
===========================================================

Méthode validée Session 107 pour détecter les tendances pré-événement.
Validée pour 11.09.2025 : détecte 09.09 08h00, durée 54.6h, R² 0.6376

Algorithme :
1. Découper période en segments (12h)
2. Calculer tendance (régression) pour chaque segment
3. Détecter inversions : UP→DOWN (pic) ou DOWN→UP (creux)
4. Valider que les deux côtés ont tendance claire (R² > seuil)
5. Prendre dernière inversion valide
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
from scipy.stats import linregress


def detect_trend_by_inversion_s107(
    prices: pd.Series,
    event_time_idx: int,
    lookback_days: int = 14,
    segment_hours: int = 12,
    min_r2_for_trend: float = 0.3,
    min_hours_before_event: int = 24,
    timeframe: str = "M1"
) -> Dict:
    """
    Détecte tendance en cherchant dernière inversion majeure (Session 107).
    
    Parameters
    ----------
    prices : pd.Series
        Série de prix (close) avec index datetime
    event_time_idx : int
        Index de l'instant événement dans la série
    lookback_days : int
        Nombre de jours à regarder en arrière
    segment_hours : int
        Durée des segments pour analyse tendance (défaut: 12h)
    min_r2_for_trend : float
        R² minimum pour considérer tendance valide (défaut: 0.3)
    min_hours_before_event : int
        Ignore inversions trop récentes (défaut: 24h)
    timeframe : str
        Timeframe utilisé ('M1', 'M15', 'H1')
    
    Returns
    -------
    Dict avec résultats de détection
    """
    if event_time_idx >= len(prices):
        return {
            'trend_exists': False,
            'error': 'event_time_idx hors limites'
        }
    
    # Convertir event_time_idx en datetime
    event_datetime = prices.index[event_time_idx]
    
    # Query time = event - 2h (comme Session 107)
    query_dt = event_datetime - timedelta(hours=2)
    
    # Période d'analyse
    start_dt = query_dt - timedelta(days=lookback_days)
    
    # Pour H1 : besoin de données après query_dt pour mesurer tendance après inversion
    # Nécessite >= 100 chandeliers après inversion = 100 heures = ~4 jours
    # Inclure données jusqu'à query_dt + 5 jours pour avoir assez de données
    # Pour M30 : inclure aussi données après query_dt (2 jours suffisent car M30 a plus de barres)
    if timeframe == 'H1':
        end_dt_for_window = query_dt + timedelta(days=5)
    elif timeframe == 'M30':
        end_dt_for_window = query_dt + timedelta(days=2)  # 2 jours = 96 barres M30, suffisant pour mesurer tendance
    else:
        end_dt_for_window = query_dt
    
    # Filtrer prix dans la fenêtre (inclure données après query_dt pour H1)
    mask = (prices.index >= start_dt) & (prices.index < end_dt_for_window)
    df_window = pd.DataFrame({
        'datetime': prices.index[mask],
        'close': prices.values[mask]
    })
    
    # Ajouter high/low si disponibles (sinon utiliser close)
    if hasattr(prices, 'high') and hasattr(prices, 'low'):
        df_window['high'] = prices.high[mask].values if hasattr(prices.high, '__getitem__') else df_window['close']
        df_window['low'] = prices.low[mask].values if hasattr(prices.low, '__getitem__') else df_window['close']
    else:
        df_window['high'] = df_window['close']
        df_window['low'] = df_window['close']
    
    # Ajuster seuil selon timeframe (H1 a moins de bougies que M1)
    # Pour M30 : réduire seuil à 400 barres (14 jours * 48 barres/jour = 672 théoriques, mais weekends réduisent à ~480 barres)
    min_bars = 100 if timeframe == 'H1' else (500 if timeframe == 'M15' else (400 if timeframe == 'M30' else 1000))
    
    if len(df_window) < min_bars:
        return {
            'trend_exists': False,
            'error': f'Pas assez de données ({len(df_window)} < {min_bars})'
        }
    
    # === ÉTAPE 1 : DÉCOUPER EN SEGMENTS ET CALCULER TENDANCES ===
    
    segment_duration = timedelta(hours=segment_hours)
    current_time = start_dt
    segments = []
    
    # Pour détection inversions : utiliser seulement jusqu'à query_dt
    # (les données après query_dt sont pour mesurer tendance après inversion)
    while current_time < query_dt:
        end_time = current_time + segment_duration
        
        # Filtrer données segment
        mask = (df_window['datetime'] >= current_time) & (df_window['datetime'] < end_time)
        df_segment = df_window[mask].copy()
        
        # Ajuster seuil selon timeframe (M15 a moins de bougies que M1 pour 12h)
        # Pour M30 : 12h = 24 barres théoriques, seuil à 20 barres (tolère quelques manquantes)
        min_segment_bars = 20 if timeframe == 'H1' else (40 if timeframe == 'M15' else (20 if timeframe == 'M30' else 100))
        
        if len(df_segment) < min_segment_bars:
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
        return {
            'trend_exists': False,
            'error': 'Pas assez de segments valides'
        }
    
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
        return {
            'trend_exists': False,
            'error': 'Aucune inversion détectée'
        }
    
    # === ÉTAPE 3 : FILTRER INVERSIONS TROP RÉCENTES ===
    
    valid_inversions = [inv for inv in inversions 
                       if inv['hours_before_event'] >= min_hours_before_event]
    
    if len(valid_inversions) == 0:
        return {
            'trend_exists': False,
            'error': 'Aucune inversion valide (trop récentes)'
        }
    
    # === ÉTAPE 4 : PRENDRE DERNIÈRE INVERSION VALIDE ===
    
    # Trier par qualité et temps
    valid_inversions = sorted(valid_inversions, 
                             key=lambda x: (x['datetime'], x['quality_score']), 
                             reverse=True)
    
    reversal = valid_inversions[0]
    
    # === ÉTAPE 5 : MESURER TENDANCE DEPUIS INVERSION ===
    
    reversal_datetime = reversal['datetime']
    df_trend = df_window[df_window['datetime'] >= reversal_datetime].copy()
    
    # Ajuster seuil selon timeframe : M30 a moins de barres que M1 pour même durée
    # Pour M30 : 2 jours après inversion = 96 barres, seuil à 50 barres (tolère weekends)
    min_bars_after_inversion = 50 if timeframe == 'M30' else (100 if timeframe == 'H1' else 100)
    
    if len(df_trend) < min_bars_after_inversion:
        return {
            'trend_exists': False,
            'error': f'Pas assez de données après inversion ({len(df_trend)} < {min_bars_after_inversion})'
        }
    
    # Durée en minutes
    duration_minutes = int((query_dt - reversal_datetime).total_seconds() / 60)
    duration_hours = duration_minutes / 60.0
    
    # Régression sur tendance complète
    df_trend['timestamp_numeric'] = (df_trend['datetime'] - reversal_datetime).dt.total_seconds()
    X = df_trend['timestamp_numeric'].values
    y = df_trend['close'].values
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(X, y)
        r2 = r_value ** 2
    except:
        r2 = 0.0
        slope = 0.0
    
    # Métriques
    amplitude_pips = (df_trend['high'].max() - df_trend['low'].min()) * 10000
    price_start = df_trend['close'].iloc[0]
    price_end = df_trend['close'].iloc[-1]
    direction = 'DOWN' if slope < 0 else 'UP'
    
    # Pente en pips/heure
    slope_pips_per_hour = abs(slope * 10000 * 3600) if slope != 0 else 0.0
    
    return {
        'trend_exists': True,
        't_start_datetime': reversal_datetime,
        'duration_minutes': duration_minutes,
        'duration_hours': duration_hours,
        'amplitude_pips': amplitude_pips,
        'r2': r2,
        'direction': direction,
        'slope_pips_per_hour': slope_pips_per_hour,
        'inversion_type': reversal['type'],
        'method_used': 'inversion-s107',
        'quality_score': reversal['quality_score']
    }

