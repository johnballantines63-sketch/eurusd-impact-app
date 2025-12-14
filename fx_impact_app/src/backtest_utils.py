"""
Utilitaires pour le backtest des prédictions multi-événements
Fonctions pour récupérer les prix réels et mesurer les performances
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import duckdb
import plotly.graph_objects as go
from config import get_db_path


def get_real_prices_batch(
    event_times: List,
    window_minutes: int = 120
) -> Dict[int, pd.DataFrame]:
    """
    Récupère les prix EURUSD 1-minute pour plusieurs événements
    
    Args:
        event_times: Liste de timestamps des événements
        window_minutes: Durée en minutes après chaque événement
    
    Returns:
        Dict {index: DataFrame} avec colonnes 'time' et 'price'
    """
    
    db_path = get_db_path()
    conn = duckdb.connect(db_path, read_only=True)
    
    prices_batch = {}
    
    for idx, event_time in enumerate(event_times):
        try:
            # Normaliser le timestamp
            if isinstance(event_time, pd.Timestamp):
                event_time = event_time.to_pydatetime()
            
            event_time = pd.to_datetime(event_time)
            
            if hasattr(event_time, 'tz') and event_time.tz is not None:
                event_time = event_time.tz_convert('UTC').tz_localize(None)
            
            # Convertir en epoch
            start_epoch = int(event_time.timestamp())
            end_epoch = start_epoch + (window_minutes * 60)
            
            # Requête SQL
            query = f"""
            SELECT timestamp, close as price
            FROM prices_1m
            WHERE timestamp >= {start_epoch} AND timestamp <= {end_epoch}
            ORDER BY timestamp ASC
            """
            
            result = conn.execute(query).fetchall()
            
            if len(result) > 0:
                times = [datetime.fromtimestamp(r[0]) for r in result]
                values = [r[1] for r in result]
                prices_batch[idx] = pd.DataFrame({'time': times, 'price': values})
            else:
                prices_batch[idx] = None
                
        except Exception as e:
            print(f"⚠️ Erreur récupération prix événement {idx}: {e}")
            prices_batch[idx] = None
    
    conn.close()
    
    return prices_batch


def measure_real_impact(
    prices_df: pd.DataFrame,
    threshold_pips: float = 5.0,
    max_lookback: int = 60
) -> Optional[Dict]:
    """
    Mesure l'impact réel d'un événement depuis les prix observés
    
    Args:
        prices_df: DataFrame avec colonnes 'time' et 'price'
        threshold_pips: Seuil minimal de mouvement pour considérer une réaction
        max_lookback: Durée maximale d'observation (minutes)
    
    Returns:
        Dict avec metrics réelles ou None si pas de réaction détectée
    """
    
    if prices_df is None or len(prices_df) < 2:
        return None
    
    try:
        # Limiter à max_lookback
        prices = prices_df.head(max_lookback).copy()
        
        if len(prices) < 2:
            return None
        
        # Prix de référence (première minute)
        ref_price = prices.iloc[0]['price']
        ref_time = prices.iloc[0]['time']
        
        # Trouver le pic (haut et bas)
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
                'max_move': max(move_up, move_down)
            }
        
        # Calculer latence (temps jusqu'au pic)
        latency_minutes = prices.index.get_loc(peak_idx)
        
        # Chercher le TTR (Time To Reversal)
        ttr_minutes = None
        
        if peak_idx < len(prices) - 1:
            # Définir seuil de retracement (20% du mouvement - optimisé)
            retracement_threshold = real_impact_pips * 0.20
            
            # DEBUG : Afficher le seuil utilisé
            print(f"🔍 DEBUG measure_real_impact: movement={real_impact_pips:.1f} pips, threshold={retracement_threshold:.1f} pips (20%)")
            
            for i in range(peak_idx + 1, len(prices)):
                current_price = prices.iloc[i]['price']
                
                # Calculer retracement
                if real_direction == 1:  # UP
                    retracement_pips = (peak_price - current_price) * 10000
                else:  # DOWN
                    retracement_pips = (current_price - peak_price) * 10000
                
                # Vérifier si retracement significatif
                if retracement_pips >= retracement_threshold:
                    ttr_minutes = i
                    break
        
        # Si pas de TTR trouvé, utiliser fin de fenêtre
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


def create_backtest_chart(
    prices_df: pd.DataFrame,
    event_time,
    predicted_impact_pips: float,
    predicted_latency: float,
    predicted_ttr: float,
    real_metrics: Dict
) -> go.Figure:
    """
    Crée un graphique Plotly comparant prédictions vs réalité
    
    Args:
        prices_df: Prix observés
        event_time: Timestamp de l'événement
        predicted_impact_pips: Impact prédit (signé)
        predicted_latency: Latence prédite (min)
        predicted_ttr: TTR prédit (min)
        real_metrics: Métriques réelles de measure_real_impact()
    
    Returns:
        Figure Plotly
    """
    
    fig = go.Figure()
    
    # Normaliser event_time
    event_time = pd.to_datetime(event_time)
    if hasattr(event_time, 'tz') and event_time.tz is not None:
        event_time = event_time.tz_localize(None)
    
    # Ligne des prix
    fig.add_trace(go.Scatter(
        x=prices_df['time'],
        y=prices_df['price'],
        mode='lines',
        name='Prix EURUSD',
        line=dict(color='blue', width=2),
        hovertemplate='<b>%{x|%H:%M:%S}</b><br>Prix: %{y:.5f}<extra></extra>'
    ))
    
    # Ligne événement
    fig.add_vline(
        x=event_time,
        line=dict(color='red', width=2, dash='dash'),
        annotation_text="Événement",
        annotation_position="top"
    )
    
    if real_metrics and real_metrics.get('had_reaction'):
        # Marquer le pic réel
        fig.add_trace(go.Scatter(
            x=[real_metrics['peak_time']],
            y=[real_metrics['peak_price']],
            mode='markers',
            name='Pic Réel',
            marker=dict(color='green', size=12, symbol='star'),
            hovertemplate=(
                f"<b>Pic Réel</b><br>"
                f"Temps: %{{x|%H:%M:%S}}<br>"
                f"Prix: %{{y:.5f}}<br>"
                f"Latence: {real_metrics['real_latency_minutes']:.0f} min<br>"
                f"<extra></extra>"
            )
        ))
        
        # Ligne TTR réel
        if real_metrics['real_ttr_minutes'] < len(prices_df):
            ttr_time = prices_df.iloc[int(real_metrics['real_ttr_minutes'])]['time']
            fig.add_vline(
                x=ttr_time,
                line=dict(color='green', width=2, dash='dot'),
                annotation_text=f"TTR Réel ({real_metrics['real_ttr_minutes']:.0f}min)",
                annotation_position="bottom"
            )
    
    # Ligne latence prédite
    pred_latency_time = event_time + timedelta(minutes=predicted_latency)
    fig.add_vline(
        x=pred_latency_time,
        line=dict(color='orange', width=1, dash='dot'),
        annotation_text=f"Latence Prédite ({predicted_latency:.0f}min)",
        annotation_position="top"
    )
    
    # Ligne TTR prédit
    pred_ttr_time = event_time + timedelta(minutes=predicted_ttr)
    fig.add_vline(
        x=pred_ttr_time,
        line=dict(color='purple', width=1, dash='dot'),
        annotation_text=f"TTR Prédit ({predicted_ttr:.0f}min)",
        annotation_position="bottom"
    )
    
    # Layout
    fig.update_layout(
        title={
            'text': "Backtest : Prix Réels vs Prédictions",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Temps",
        yaxis_title="Prix EURUSD",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig
