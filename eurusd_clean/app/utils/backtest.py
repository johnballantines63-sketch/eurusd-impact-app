"""
Backtest Utilities

Fonctions pour récupérer prix réels et mesurer impact observé.
Migré depuis backtest_utils.py (Session 33).

Fonctions principales:
- get_real_prices_batch() : Récupérer prix réels pour plusieurs événements (optimisé SQL)
- measure_real_impact() : Mesurer impact réel depuis prix observés (TTR observé critique)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.services.data_service import DataService


def get_real_prices_batch(
    data_service: DataService,
    event_times: List[datetime],
    window_minutes: int = 120
) -> Dict[int, Optional[pd.DataFrame]]:
    """
    Récupère les prix EURUSD 1-minute pour plusieurs événements en UNE SEULE query.
    
    OPTIMISATION CRITIQUE : Utilise une seule query SQL avec OR conditions
    au lieu de N queries (1 par événement). Beaucoup plus rapide pour 10+ événements.
    
    Args:
        data_service: Instance DataService pour accès DB
        event_times: Liste de datetime des événements
        window_minutes: Durée en minutes après chaque événement (défaut: 120)
    
    Returns:
        Dict {index: DataFrame} avec colonnes ['time', 'price']
        Si aucun prix trouvé pour un événement, la valeur est None
    
    Example:
        >>> data = DataService(db_path)
        >>> events = [datetime(2025, 9, 11, 12, 30), datetime(2025, 9, 11, 14, 0)]
        >>> prices = get_real_prices_batch(data, events, window_minutes=60)
        >>> len(prices)
        2
        >>> prices[0].shape
        (60, 2)  # 60 minutes × 2 colonnes (time, price)
    """
    if not event_times:
        return {}
    
    prices_batch = {}
    
    # Préparer toutes les fenêtres temporelles
    windows = []
    for idx, event_time in enumerate(event_times):
        try:
            # Normaliser timestamp
            if isinstance(event_time, pd.Timestamp):
                event_time = event_time.to_pydatetime()
            
            event_time = pd.to_datetime(event_time)
            
            # Retirer timezone si présente (pour compatibilité avec DB)
            if hasattr(event_time, 'tz') and event_time.tz is not None:
                event_time = event_time.tz_convert('UTC').tz_localize(None)
            
            # Calculer fenêtre de temps
            end_time = event_time + timedelta(minutes=window_minutes)
            
            windows.append((idx, event_time, end_time))
            
        except Exception as e:
            print(f"⚠️ Erreur normalisation timestamp événement {idx}: {e}")
            prices_batch[idx] = None
    
    if not windows:
        return prices_batch
    
    # OPTIMISATION : UNE SEULE query avec OR conditions
    # IMPORTANT: Utiliser 'datetime' (pas 'timestamp' qui est NULL)
    conditions = " OR ".join([
        f"(datetime >= '{start.strftime('%Y-%m-%d %H:%M:%S')}' AND datetime <= '{end.strftime('%Y-%m-%d %H:%M:%S')}')" 
        for _, start, end in windows
    ])
    
    query = f"""
    SELECT datetime, close
    FROM prices_1m
    WHERE {conditions}
    ORDER BY datetime ASC
    """
    
    try:
        with data_service.get_connection() as conn:
            result = conn.execute(query).fetchall()
        
        if not result:
            # Aucun prix trouvé pour aucun événement
            for idx, _, _ in windows:
                prices_batch[idx] = None
            return prices_batch
        
        # Séparer les résultats par événement
        for idx, start_time, end_time in windows:
            # Filtrer les prix de cette fenêtre
            event_prices = [
                (r[0], r[1]) for r in result 
                if start_time <= r[0].replace(tzinfo=None) <= end_time
            ]
            
            if event_prices:
                # Convertir datetime en objet Python sans timezone
                times = [dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') else dt for dt, _ in event_prices]
                values = [price for _, price in event_prices]
                prices_batch[idx] = pd.DataFrame({'time': times, 'price': values})
            else:
                prices_batch[idx] = None
    
    except Exception as e:
        print(f"❌ Erreur query prix batch: {e}")
        # En cas d'erreur, retourner None pour tous
        for idx, _, _ in windows:
            prices_batch[idx] = None
    
    return prices_batch


def measure_real_impact(
    prices_df: pd.DataFrame,
    threshold_pips: float = 5.0,
    max_lookback: int = 60
) -> Optional[Dict[str, Any]]:
    """
    Mesure l'impact réel d'un événement depuis les prix observés.
    
    CRITIQUE : Cette fonction calcule le TTR OBSERVÉ depuis les prix réels,
    ce qui est beaucoup plus précis que le TTR prédit (MAE de 30.1 min sur cas 11 sept).
    
    Le TTR observé est défini comme le temps jusqu'au retracement de 20% du mouvement max.
    
    Args:
        prices_df: DataFrame avec colonnes ['time', 'price']
        threshold_pips: Seuil minimal de mouvement pour considérer une réaction (défaut: 5.0)
        max_lookback: Durée maximale d'observation en minutes (défaut: 60)
    
    Returns:
        Dict avec métriques réelles si réaction détectée:
            - 'had_reaction': bool - True si mouvement >= threshold
            - 'real_impact_pips': float - Mouvement max observé (signé selon direction)
            - 'real_direction': int - +1 (UP) ou -1 (DOWN)
            - 'real_latency_minutes': float - Minutes jusqu'au pic
            - 'real_ttr_minutes': float - Minutes jusqu'au retracement 20%
            - 'peak_price': float - Prix au pic
            - 'peak_time': datetime - Timestamp du pic
            - 'ref_price': float - Prix de référence (début)
            - 'ref_time': datetime - Timestamp de référence
            - 'move_up_pips': float - Mouvement UP total
            - 'move_down_pips': float - Mouvement DOWN total
        
        Ou dict avec 'had_reaction': False si pas de réaction significative
        
        Ou None si erreur ou données insuffisantes
    
    Example - Cas 11 septembre 2025:
        >>> # Prix de 12:30 à 13:30
        >>> prices = pd.DataFrame({
        ...     'time': [...],
        ...     'price': [1.16816, 1.16850, ..., 1.17190, ..., 1.16919]
        ... })
        >>> metrics = measure_real_impact(prices, threshold_pips=5.0)
        >>> metrics['real_impact_pips']
        37.4  # Phase 1 confirmée
        >>> metrics['real_ttr_minutes']
        5.0  # TTR observé (vs 31-50 min prédit)
    """
    if prices_df is None or len(prices_df) < 2:
        return None
    
    try:
        # Limiter à max_lookback minutes
        prices = prices_df.head(max_lookback).copy()
        
        if len(prices) < 2:
            return None
        
        # Prix de référence (première minute)
        ref_price = prices.iloc[0]['price']
        ref_time = prices.iloc[0]['time']
        
        # Trouver les extrêmes (haut et bas)
        max_price = prices['price'].max()
        min_price = prices['price'].min()
        
        max_idx = prices['price'].idxmax()
        min_idx = prices['price'].idxmin()
        
        # Calculer mouvements en pips
        move_up = (max_price - ref_price) * 10000
        move_down = (ref_price - min_price) * 10000
        
        # Déterminer direction dominante
        if move_up > move_down and move_up >= threshold_pips:
            # Mouvement UP
            real_impact_pips = move_up
            real_direction = 1
            peak_idx = max_idx
            peak_price = max_price
            peak_time = prices.loc[peak_idx, 'time']
            
        elif move_down > move_up and move_down >= threshold_pips:
            # Mouvement DOWN
            real_impact_pips = move_down
            real_direction = -1
            peak_idx = min_idx
            peak_price = min_price
            peak_time = prices.loc[peak_idx, 'time']
            
        else:
            # Pas de mouvement significatif
            return {
                'had_reaction': False,
                'reason': 'movement_too_small',
                'max_move': max(move_up, move_down),
                'threshold': threshold_pips
            }
        
        # Calculer latence (index du pic = nombre de minutes)
        latency_minutes = prices.index.get_loc(peak_idx)
        
        # Chercher le TTR (Time To Reversal)
        # CRITIQUE : Défini comme retracement de 20% du mouvement max
        ttr_minutes = None
        
        if peak_idx < len(prices) - 1:
            # Seuil de retracement : 20% du mouvement (optimisé empiriquement)
            retracement_threshold = real_impact_pips * 0.20
            
            # Parcourir les prix après le pic
            for i in range(peak_idx + 1, len(prices)):
                current_price = prices.iloc[i]['price']
                
                # Calculer retracement depuis le pic
                if real_direction == 1:  # Mouvement UP
                    retracement_pips = (peak_price - current_price) * 10000
                else:  # Mouvement DOWN
                    retracement_pips = (current_price - peak_price) * 10000
                
                # Vérifier si retracement significatif atteint
                if retracement_pips >= retracement_threshold:
                    ttr_minutes = i
                    break
        
        # Si pas de TTR trouvé dans la fenêtre, utiliser fin de fenêtre
        if ttr_minutes is None:
            ttr_minutes = len(prices) - 1
        
        return {
            'had_reaction': True,
            'real_impact_pips': real_impact_pips * real_direction,  # Signé
            'real_direction': real_direction,
            'real_latency_minutes': float(latency_minutes),
            'real_ttr_minutes': float(ttr_minutes),
            'peak_price': float(peak_price),
            'peak_time': peak_time,
            'ref_price': float(ref_price),
            'ref_time': ref_time,
            'move_up_pips': float(move_up),
            'move_down_pips': float(move_down)
        }
        
    except Exception as e:
        print(f"⚠️ Erreur measure_real_impact: {e}")
        return None
