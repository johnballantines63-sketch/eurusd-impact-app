"""
Générateur de Courbes de Prix Minute par Minute
Modélise l'évolution du cours EUR/USD selon prédictions d'impact
Version 2.0 : Chandeliers avec spread bid/ask
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from typing import List, Dict, Tuple


def sigmoid(x):
    """Fonction sigmoïde pour mouvement progressif réaliste"""
    return 1 / (1 + np.exp(-x))


def generate_ohlc_candle(
    open_price: float,
    target_price: float,
    volatility: float = 0.00003,
    trend_strength: float = 1.0
) -> Dict[str, float]:
    """
    Génère un chandelier OHLC réaliste pour une minute
    
    Args:
        open_price: Prix d'ouverture
        target_price: Prix cible (close désiré)
        volatility: Volatilité intra-minute
        trend_strength: Force de la tendance (0-1)
    
    Returns:
        Dict avec open, high, low, close
    """
    # Close : vers le target avec un peu de bruit
    close_noise = np.random.normal(0, volatility * 0.5)
    close_price = open_price + (target_price - open_price) * trend_strength + close_noise
    
    # High et Low : extensions autour de open/close
    high_extension = abs(np.random.normal(0, volatility * 1.5))
    low_extension = abs(np.random.normal(0, volatility * 1.5))
    
    high_price = max(open_price, close_price) + high_extension
    low_price = min(open_price, close_price) - low_extension
    
    return {
        'open': open_price,
        'high': high_price,
        'low': low_price,
        'close': close_price
    }


def generate_candlestick_curve_multi_events(
    start_price: float,
    predictions: List[Dict],
    base_time: datetime,
    duration_minutes: int = 120,
    volatility_factor: float = 0.3,
    spread_pips: float = 0.0
) -> pd.DataFrame:
    """
    Génère courbe de chandeliers pour PLUSIEURS événements séquentiels
    
    Args:
        start_price: Prix EUR/USD de départ (mid-price)
        predictions: Liste de dicts avec event_time, predicted_pips, direction, latency_median, ttr_median
        base_time: Timestamp de référence
        duration_minutes: Durée totale à simuler
        volatility_factor: Facteur de volatilité (0-1)
        spread_pips: Spread bid/ask en pips (ex: 1.0 = 1 pip)
    
    Returns:
        DataFrame avec time, open, high, low, close, bid, ask, phase
    """
    
    candles = []
    current_mid_price = start_price
    
    # Convertir spread en prix
    spread_price = spread_pips / 10000
    
    for minute in range(duration_minutes + 1):
        current_time = base_time + timedelta(minutes=minute)
        
        # ✅ CORRECTION FINALE V4 : Créer UN événement vectoriel synthétique
        # Calculer l'impact vectoriel total (somme avec directions)
        vectorial_impact_total = sum(
            (pred['predicted_pips'] / 10000) * pred['direction']
            for pred in predictions
        )
        
        # Trouver le premier événement et ses timings moyens
        if predictions:
            first_event_time = min(pred['event_time'] for pred in predictions)
            avg_latency = sum((pred.get('latency_median', 0) or 0) for pred in predictions) / len(predictions)
            avg_ttr = sum(pred.get('ttr_median', 0) or 0 for pred in predictions) / len(predictions) if predictions else 0
            
            minutes_since_event = (current_time - first_event_time).total_seconds() / 60
            
            # Calculer le prix cible en fonction de la phase
            target_price = start_price
            active_phase = "stable"
            
            if minutes_since_event < 0:
                # Avant l'événement
                contribution = 0
                active_phase = "stable"
            
            elif minutes_since_event < avg_latency:
                # Phase latence
                contribution = 0
                active_phase = "latence"
            
            elif minutes_since_event < avg_ttr:
                # Phase mouvement
                progress = (minutes_since_event - avg_latency) / (avg_ttr - avg_latency)
                sigmoid_progress = sigmoid(10 * (progress - 0.5))
                contribution = vectorial_impact_total * sigmoid_progress
                active_phase = "mouvement"
            
            else:
                # Phase retracement (Fibonacci 38.2%)
                time_since_peak = minutes_since_event - avg_ttr
                retracement_progress = min(1.0, time_since_peak / 20)
                exp_progress = 1 - np.exp(-3 * retracement_progress)
                contribution = vectorial_impact_total * (1 - 0.382 * exp_progress)
                active_phase = "retracement"
            
            target_price += contribution
        
        else:
            # Pas de prédictions
            target_price = start_price
            active_phase = "stable"
        
        
        # ✅ CORRECTION V3 : Calculer impact vectoriel AVANT la boucle temporelle
        # On calcule la somme vectorielle des impacts (avec directions)
        # [ANCIEN CODE]         vectorial_impact_at_peak = sum(
        # [ANCIEN CODE]             (pred['predicted_pips'] / 10000) * pred['direction'] 
        # [ANCIEN CODE]             for pred in predictions
        # [ANCIEN CODE]         )
        
        # Direction globale
        # [ANCIEN CODE]         global_direction = 1 if vectorial_impact_at_peak > 0 else -1
        
        # Calculer prix cible pour cette minute
        # [ANCIEN CODE]         target_price = start_price
        # [ANCIEN CODE]         active_phase = "stable"
        
        # Trouver l'événement le plus avancé dans sa phase
        # [ANCIEN CODE]         max_progress = 0.0
        
        # [ANCIEN CODE]         for pred in predictions:
        # [ANCIEN CODE]             event_time = pred['event_time']
        # [ANCIEN CODE]             minutes_since_event = (current_time - event_time).total_seconds() / 60
            
        # [ANCIEN CODE]             if minutes_since_event < 0:
        # [ANCIEN CODE]                 continue
            
        # [ANCIEN CODE]             latency = (pred.get('latency_median', 0) or 0)
        # [ANCIEN CODE]             ttr = pred['ttr_median']
            
            # Calculer le progress pour cet événement
        # [ANCIEN CODE]             if minutes_since_event < latency:
        # [ANCIEN CODE]                 progress = 0.0
        # [ANCIEN CODE]                 active_phase = "latence"
        # [ANCIEN CODE]             elif minutes_since_event < ttr:
        # [ANCIEN CODE]                 progress = (minutes_since_event - latency) / (ttr - latency)
        # [ANCIEN CODE]                 active_phase = "mouvement"
        # [ANCIEN CODE]             else:
        # [ANCIEN CODE]                 time_since_peak = minutes_since_event - ttr
        # [ANCIEN CODE]                 retracement_progress = min(1.0, time_since_peak / 20)
        # [ANCIEN CODE]                 progress = 1.0 - (0.382 * (1 - np.exp(-3 * retracement_progress)))
        # [ANCIEN CODE]                 active_phase = "retracement"
            
        # [ANCIEN CODE]             max_progress = max(max_progress, progress)
        
        # Appliquer le mouvement vectoriel avec le progress maximum
        # [ANCIEN CODE]         if max_progress > 0:
        # [ANCIEN CODE]             if active_phase == "mouvement":
        # [ANCIEN CODE]                 sigmoid_progress = sigmoid(10 * (max_progress - 0.5))
        # [ANCIEN CODE]                 contribution = vectorial_impact_at_peak * sigmoid_progress
        # [ANCIEN CODE]             else:  # retracement
        # [ANCIEN CODE]                 contribution = vectorial_impact_at_peak * max_progress
            
        # [ANCIEN CODE]             target_price += contribution
        
        # Générer chandelier
        candle = generate_ohlc_candle(
            open_price=current_mid_price,
            target_price=target_price,
            volatility=0.00003 * volatility_factor,
            trend_strength=0.8
        )
        
        # Calculer bid/ask
        mid_close = candle['close']
        bid_close = mid_close - spread_price / 2
        ask_close = mid_close + spread_price / 2
        
        candles.append({
            'time': current_time,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'bid': bid_close,
            'ask': ask_close,
            'phase': active_phase,
            'minute_offset': minute
        })
        
        # Update pour prochaine minute
        current_mid_price = mid_close
    
    return pd.DataFrame(candles)


def generate_candlestick_curve_from_phases(
    start_price: float,
    phases: List[Dict],
    base_time: datetime,
    duration_minutes: int = 120,
    volatility_factor: float = 0.3,
    spread_pips: float = 0.0
) -> pd.DataFrame:
    """
    Génère courbe de chandeliers à partir des PHASES calculées (avec pullback)
    
    VERSION 8.6.2 : Intègre le pullback visuel entre phases rapprochées
    
    Args:
        start_price: Prix EUR/USD de départ (mid-price)
        phases: Liste de phases retournées par sequence_multi_event_timeline()
                Chaque phase contient:
                - phase_num: Numéro de phase
                - start_time: Timestamp début
                - peak_time: Timestamp du pic (si disponible)
                - cumulative_price: Prix cumulé au pic
                - impact_combined: Impact en pips (avec direction)
                - pullback_pips: Pullback depuis phase précédente (si < 30 min)
                - minutes_since_prev_phase: Minutes depuis phase précédente
                - latency_minutes: Latence moyenne
                - ttr_predicted: TTR prédit
                - duration_minutes: Durée de la phase
        base_time: Timestamp de référence (début de la timeline)
        duration_minutes: Durée totale à simuler
        volatility_factor: Facteur de volatilité (0-1)
        spread_pips: Spread bid/ask en pips
    
    Returns:
        DataFrame avec time, open, high, low, close, bid, ask, phase, phase_num
    """
    
    candles = []
    current_mid_price = start_price
    
    # Convertir spread en prix
    spread_price = spread_pips / 10000
    
    # Parser les timestamps des phases
    for phase in phases:
        if isinstance(phase['start_time'], str):
            phase['start_time'] = pd.to_datetime(phase['start_time'])
        if 'peak_time' in phase and isinstance(phase['peak_time'], str):
            phase['peak_time'] = pd.to_datetime(phase['peak_time'])
    
    # Trier phases par ordre chronologique
    phases_sorted = sorted(phases, key=lambda p: p['start_time'])
    
    # Générer minute par minute
    for minute in range(duration_minutes + 1):
        current_time = base_time + timedelta(minutes=minute)
        
        # Trouver dans quelle phase/zone nous sommes
        target_price = current_mid_price
        active_phase_label = "stable"
        active_phase_num = 0
        
        # Chercher la phase active
        for idx, phase in enumerate(phases_sorted):
            phase_start = phase['start_time']
            phase_duration = phase['duration_minutes']
            phase_end = phase_start + timedelta(minutes=phase_duration)
            
            # Si avant la première phase
            if current_time < phases_sorted[0]['start_time']:
                target_price = start_price
                active_phase_label = "pre_event"
                break
            
            # Si dans une zone de pullback
            if idx > 0:
                prev_phase = phases_sorted[idx - 1]
                pullback_pips = phase.get('pullback_pips', 0.0)
                
                if pullback_pips > 0:  # Il y a un pullback
                    # Zone de pullback entre pic phase N-1 et début phase N
                    prev_peak_time = prev_phase.get('peak_time', prev_phase['start_time'])
                    pullback_start = prev_peak_time
                    pullback_end = phase_start
                    
                    if pullback_start <= current_time < pullback_end:
                        # NOUS SOMMES DANS LE PULLBACK !
                        prev_cumulative = prev_phase.get('cumulative_price', start_price)
                        pullback_price_change = pullback_pips / 10000
                        
                        # Descente progressive (linéaire)
                        pullback_duration = (pullback_end - pullback_start).total_seconds() / 60
                        progress = (current_time - pullback_start).total_seconds() / 60 / pullback_duration
                        progress = min(1.0, max(0.0, progress))  # Clamper entre 0 et 1
                        
                        # Prix descend du pic vers (pic - pullback)
                        target_price = prev_cumulative - (pullback_price_change * progress)
                        active_phase_label = "pullback"
                        active_phase_num = phase['phase_num']
                        break
            
            # Si dans la phase (après pullback)
            if phase_start <= current_time < phase_end:
                minutes_since_phase = (current_time - phase_start).total_seconds() / 60
                latency = phase['latency_minutes']
                ttr = phase['ttr_predicted']
                impact = phase['impact_combined']  # Déjà avec direction
                # === DEBUG v8.6.6 : Vérifier valeur impact ===
                if active_phase_num == phase['phase_num'] and minutes_since_phase < 1:
                    print(f"\n🔬 DEBUG CONVERSION Phase {phase['phase_num']}:")
                    print(f"   impact (brut)      : {impact}")
                    print(f"   type(impact)       : {type(impact)}")
                    print(f"   impact / 10000     : {impact / 10000}")
                    print(f"   latency            : {latency}")
                    print(f"   ttr (ttr_predicted): {ttr}")
                    print(f"   ttr_real (si existe): {phase.get('ttr_real', 'N/A')}")
                # === FIN DEBUG ===
                impact_price = impact / 10000
                
                # Prix de départ de cette phase
                if idx > 0 and phase.get('pullback_pips', 0) > 0:
                    # Départ depuis le prix après pullback
                    prev_cumulative = phases_sorted[idx - 1].get('cumulative_price', start_price)
                    pullback_change = phase['pullback_pips'] / 10000
                    phase_start_price = prev_cumulative - pullback_change
                else:
                    # Départ depuis le prix cumulé précédent ou start_price
                    if idx > 0:
                        phase_start_price = phases_sorted[idx - 1].get('cumulative_price', start_price)
                    else:
                        phase_start_price = start_price
                
                # Phase latence
                if minutes_since_phase < latency:
                    target_price = phase_start_price
                    active_phase_label = "latence"
                
                # Phase mouvement
                elif minutes_since_phase < ttr:
                    progress = (minutes_since_phase - latency) / (ttr - latency)
                    sigmoid_progress = sigmoid(10 * (progress - 0.5))
                    target_price = phase_start_price + (impact_price * sigmoid_progress)
                    active_phase_label = "mouvement"
                    
                    # === DEBUG v8.6.6 : Tracer génération courbe ===
                    if minute % 5 == 0:  # Afficher toutes les 5 minutes
                        print(f"📊 Minute {minute:3d} | "
                              f"Phase: {active_phase_label:12s} | "
                              f"Impact: {impact_price*10000:+7.1f} pips | "
                              f"phase_start_price: {phase_start_price:.5f} | "
                              f"sigmoid_progress: {sigmoid_progress:.4f} | "
                              f"Target: {target_price:.5f} | "
                              f"Current: {current_mid_price:.5f}")
                    # === FIN DEBUG ===
                
                # Phase retracement (Fibonacci 38.2%)
                else:
                    time_since_peak = minutes_since_phase - ttr
                    retracement_progress = min(1.0, time_since_peak / 20)
                    exp_progress = 1 - np.exp(-3 * retracement_progress)
                    peak_price = phase_start_price + impact_price
                    target_price = peak_price - (impact_price * 0.382 * exp_progress)
                    active_phase_label = "retracement"
                
                active_phase_num = phase['phase_num']
                break
        
        # Si après toutes les phases
        if current_time >= phases_sorted[-1]['start_time'] + timedelta(minutes=phases_sorted[-1]['duration_minutes']):
            # Maintenir le dernier prix
            target_price = current_mid_price
            active_phase_label = "post_event"
            active_phase_num = phases_sorted[-1]['phase_num']
        
        # Générer chandelier
        candle = generate_ohlc_candle(
            open_price=current_mid_price,
            target_price=target_price,
            volatility=0.00003 * volatility_factor,
            trend_strength=0.8
        )
        
        # Calculer bid/ask
        mid_close = candle['close']
        bid_close = mid_close - spread_price / 2
        ask_close = mid_close + spread_price / 2
        
        candles.append({
            'time': current_time,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'bid': bid_close,
            'ask': ask_close,
            'phase': active_phase_label,
            'phase_num': active_phase_num,
            'minute_offset': minute
        })
        
        # Update pour prochaine minute
        current_mid_price = mid_close
    
    return pd.DataFrame(candles)


def calculate_fibonacci_price_levels(start_price: float, impact_pips: float, direction: int) -> Dict[str, float]:
    """
    Calcule niveaux de prix Fibonacci
    
    Returns:
        Dict {level_name: price}
    """
    price_change = (impact_pips / 10000) * direction
    peak_price = start_price + price_change
    
    levels = {}
    
    for fib in [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]:
        level_price = start_price + price_change * fib
        level_name = f"{fib*100:.1f}%"
        levels[level_name] = level_price
    
    return levels


def create_sequential_phases_chart(
    price_df: pd.DataFrame,
    phases: List[Dict],
    start_price: float,
    title: str = "📊 Timeline Séquentielle Multi-Événements avec Pullback"
) -> go.Figure:
    """
    Crée graphique chandeliers avec zones de pullback visuellement marquées
    
    VERSION 8.6.2 : Affiche visuellement les pullbacks entre phases rapprochées
    
    Args:
        price_df: DataFrame retourné par generate_candlestick_curve_from_phases()
                  Colonnes: time, open, high, low, close, phase, phase_num
        phases: Liste des phases (pour annotations)
        start_price: Prix de départ
        title: Titre du graphique
    
    Returns:
        Figure Plotly interactive
    """
    
    fig = go.Figure()
    
    # Séparer les données par type de phase pour coloration différente
    phases_types = price_df['phase'].unique()
    
    # Couleurs par phase
    phase_colors = {
        'pre_event': {'increasing': 'lightgray', 'decreasing': 'darkgray'},
        'stable': {'increasing': 'lightgray', 'decreasing': 'darkgray'},
        'latence': {'increasing': 'lightyellow', 'decreasing': 'khaki'},
        'mouvement': {'increasing': 'green', 'decreasing': 'red'},
        'pullback': {'increasing': 'orange', 'decreasing': 'darkorange'},  # ← PULLBACK
        'retracement': {'increasing': 'lightcoral', 'decreasing': 'indianred'},
        'post_event': {'increasing': 'lightgray', 'decreasing': 'darkgray'}
    }
    
    # Créer un chandelier par segment de phase
    for phase_type in ['pre_event', 'latence', 'mouvement', 'pullback', 'retracement', 'post_event']:
        phase_data = price_df[price_df['phase'] == phase_type]
        
        if len(phase_data) == 0:
            continue
        
        colors = phase_colors.get(phase_type, {'increasing': 'green', 'decreasing': 'red'})
        
        # Label spécial pour pullback
        if phase_type == 'pullback':
            name = '🔄 Pullback (descente)'
            opacity = 0.9
        else:
            name = phase_type.capitalize()
            opacity = 0.8
        
        fig.add_trace(go.Candlestick(
            x=phase_data['time'],
            open=phase_data['open'],
            high=phase_data['high'],
            low=phase_data['low'],
            close=phase_data['close'],
            name=name,
            increasing_line_color=colors['increasing'],
            decreasing_line_color=colors['decreasing'],
            increasing_fillcolor=f"rgba({','.join(str(int(c*255)) for c in plt_to_rgb(colors['increasing']))},0.3)",
            decreasing_fillcolor=f"rgba({','.join(str(int(c*255)) for c in plt_to_rgb(colors['decreasing']))},0.3)",
            line=dict(width=2),
            opacity=opacity
        ))
    
    # Ligne prix de départ
    fig.add_hline(
        y=start_price,
        line_dash="solid",
        line_color="blue",
        line_width=2,
        annotation_text=f"💰 Prix départ: {start_price:.5f}",
        annotation_position="right"
    )
    
    # ✅ CORRECTION v4 FINALE: Utiliser add_shape() au lieu de add_vline()
    # add_vline() cause des problèmes avec datetime même sans annotation
    # add_shape() est plus bas niveau et plus robuste
    
    for phase in phases:
        phase_start = pd.to_datetime(phase['start_time'])
        # Convertir en datetime Python
        if hasattr(phase_start, 'to_pydatetime'):
            phase_start = phase_start.to_pydatetime()
        
        impact = phase['impact_combined']
        pullback = phase.get('pullback_pips', 0)
        
        # Couleur selon type
        if pullback > 0:
            color = 'orange'
            label = f"🔄 Phase {phase['phase_num']}<br>Pullback: -{pullback:.1f} pips<br>Impact: {impact:+.1f} pips"
        else:
            color = 'green' if impact > 0 else 'red'
            label = f"📍 Phase {phase['phase_num']}<br>Impact: {impact:+.1f} pips"
        
        # ✅ Ligne verticale avec add_shape (plus robuste que add_vline)
        fig.add_shape(
            type="line",
            x0=phase_start,
            x1=phase_start,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(
                color=color,
                width=2,
                dash="dash"
            )
        )
        
        # Annotation manuelle
        fig.add_annotation(
            x=phase_start,
            y=1.05,
            yref="paper",
            text=label,
            showarrow=True,
            arrowhead=2,
            arrowcolor=color,
            arrowwidth=2,
            ax=0,
            ay=-30,
            font=dict(size=11, color="white"),
            bgcolor=color,
            bordercolor="white",
            borderwidth=1,
            opacity=0.9
        )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=22, family="Arial Bold"),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Temps",
        yaxis_title="Prix EUR/USD",
        height=800,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            font=dict(size=12),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="black",
            borderwidth=1
        ),
        yaxis=dict(
            tickformat='.5f',
            gridcolor='lightgray'
        ),
        xaxis=dict(
            tickformat='%H:%M',
            gridcolor='lightgray',
            rangeslider=dict(visible=True, thickness=0.05)
        )
    )
    
    return fig


def plt_to_rgb(color_name: str) -> Tuple[float, float, float]:
    """Convertit nom de couleur en RGB (0-1)"""
    color_map = {
        'green': (0, 1, 0),
        'red': (1, 0, 0),
        'orange': (1, 0.647, 0),
        'darkorange': (1, 0.549, 0),
        'lightgray': (0.827, 0.827, 0.827),
        'darkgray': (0.663, 0.663, 0.663),
        'lightyellow': (1, 1, 0.878),
        'khaki': (0.941, 0.902, 0.549),
        'lightcoral': (0.941, 0.502, 0.502),
        'indianred': (0.804, 0.361, 0.361)
    }
    return color_map.get(color_name, (0.5, 0.5, 0.5))


def create_candlestick_prediction_chart(
    price_df: pd.DataFrame,
    start_price: float,
    total_impact_pips: float,
    direction: int,
    event_markers: List[Dict],
    fib_levels: Dict[str, float],
    show_spread: bool = True,
    title: str = "Évolution Prédite EUR/USD"
) -> go.Figure:
    """
    Crée graphique chandeliers interactif de l'évolution prédite des prix
    
    Args:
        price_df: DataFrame avec time, open, high, low, close, bid, ask
        start_price: Prix de départ
        total_impact_pips: Impact total en pips
        direction: Direction (+1/-1)
        event_markers: Liste de dicts {time, label, color}
        fib_levels: Dict {level_name: price}
        show_spread: Afficher bid/ask
        title: Titre du graphique
    
    Returns:
        Figure Plotly
    """
    
    fig = go.Figure()
    
    # === CHANDELIERS PRINCIPAUX (Mid-Price) ===
    fig.add_trace(go.Candlestick(
        x=price_df['time'],
        open=price_df['open'],
        high=price_df['high'],
        low=price_df['low'],
        close=price_df['close'],
        name='EUR/USD (Mid)',
        increasing_line_color='green',
        decreasing_line_color='red',
        increasing_fillcolor='rgba(0,255,0,0.3)',
        decreasing_fillcolor='rgba(255,0,0,0.3)'
    ))
    
    # === LIGNES BID/ASK (si activé) ===
    if show_spread and 'bid' in price_df.columns:
        fig.add_trace(go.Scatter(
            x=price_df['time'],
            y=price_df['bid'],
            mode='lines',
            name='Bid',
            line=dict(color='blue', width=1, dash='dot'),
            opacity=0.5,
            hovertemplate='Bid: %{y:.5f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=price_df['time'],
            y=price_df['ask'],
            mode='lines',
            name='Ask',
            line=dict(color='red', width=1, dash='dot'),
            opacity=0.5,
            hovertemplate='Ask: %{y:.5f}<extra></extra>'
        ))
    
    # === LIGNE HORIZONTALE PRIX DE DÉPART ===
    fig.add_hline(
        y=start_price,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Prix départ: {start_price:.5f}",
        annotation_position="right"
    )
    
    # === NIVEAUX FIBONACCI ===
    fib_colors = {
        '0.0%': 'gray',
        '23.6%': 'lightblue',
        '38.2%': 'lightgreen',
        '50.0%': 'yellow',
        '61.8%': 'orange',
        '78.6%': 'lightsalmon',
        '100.0%': 'red'
    }
    
    for level_name, price in fib_levels.items():
        color = fib_colors.get(level_name, 'lightgray')
        
        # Ligne horizontale
        fig.add_hline(
            y=price,
            line_dash="dot",
            line_color=color,
            opacity=0.5,
            annotation_text=f"Fib {level_name}: {price:.5f}",
            annotation_position="left",
            annotation_font_size=9
        )
    
    # === MARQUEURS D'ÉVÉNEMENTS ===
    for marker in event_markers:
        fig.add_vline(
            x=marker['time'],
            line_dash="solid",
            line_color=marker.get('color', 'black'),
            line_width=2.5,
            annotation_text=marker['label'],
            annotation_position="top"
        )
    
    # === ZONES COLORÉES PAR PHASE ===
    if 'phase' in price_df.columns:
        # Identifier les transitions de phase
        phase_changes = price_df[price_df['phase'] != price_df['phase'].shift()].index
        
        phase_colors = {
            'latence': 'rgba(200, 200, 200, 0.1)',
            'stable': 'rgba(200, 200, 200, 0.1)',
            'mouvement': 'rgba(100, 200, 100, 0.1)',
            'retracement': 'rgba(200, 100, 100, 0.1)'
        }
        
        for i in range(len(phase_changes) - 1):
            start_idx = phase_changes[i]
            end_idx = phase_changes[i + 1] - 1
            phase = price_df.loc[start_idx, 'phase']
            
            fig.add_vrect(
                x0=price_df.loc[start_idx, 'time'],
                x1=price_df.loc[end_idx, 'time'],
                fillcolor=phase_colors.get(phase, 'rgba(0,0,0,0.05)'),
                opacity=0.3,
                layer="below",
                line_width=0
            )
    
    # === LAYOUT ===
    # === LAYOUT AMÉLIORÉ POUR LISIBILITÉ ===
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, family="Arial Bold")  # ← Plus gros
        ),
        xaxis_title="Temps",
        yaxis_title="Prix EUR/USD",
        height=900,  # ← Plus haut (au lieu de 700)
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=14, family="Arial"),  # ← Plus gros
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="black",
            borderwidth=2
        ),
        yaxis=dict(
            tickformat='.5f',
            gridcolor='lightgray',
            tickfont=dict(size=16, family="Arial"),  # ← Plus gros
            title_font=dict(size=18, family="Arial Bold")  # ← Plus gros
        ),
        xaxis=dict(
            tickformat='%H:%M',
            gridcolor='lightgray',
            tickfont=dict(size=16, family="Arial"),  # ← Plus gros
            title_font=dict(size=18, family="Arial Bold"),  # ← Plus gros
            rangeslider=dict(
                visible=True,  # ← Activer slider !
                thickness=0.05
            )
        ),
        # Ajouter boutons de zoom prédéfinis
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=[
                    dict(
                        label="15 min",
                        method="relayout",
                        args=[{"xaxis.range": None}],  # Reset puis zoom
                        args2=[{"xaxis.autorange": False}]
                    ),
                    dict(
                        label="30 min",
                        method="relayout",
                        args=[{"xaxis.range": None}]
                    ),
                    dict(
                        label="60 min",
                        method="relayout",
                        args=[{"xaxis.range": None}]
                    ),
                    dict(
                        label="Tout",
                        method="relayout",
                        args=[{"xaxis.autorange": True}]
                    ),
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.11,
                xanchor="left",
                y=1.12,
                yanchor="top"
            )
        ],
        margin=dict(l=100, r=100, t=120, b=100)  # Plus d'espace
    )

    
    return fig


def add_statistics_to_chart(
    fig: go.Figure,
    price_df: pd.DataFrame,
    start_price: float,
    predicted_impact: float,
    direction: int
) -> go.Figure:
    """
    Ajoute statistiques et annotations au graphique
    """
    
    # Trouver prix max et min
    max_price = price_df['high'].max()
    min_price = price_df['low'].min()
    
    # Calculer amplitude réelle
    actual_amplitude = (max_price - min_price) * 10000
    
    # Peak price
    peak_price = max_price if direction > 0 else min_price
    peak_time = price_df[price_df['high'] == max_price]['time'].iloc[0] if direction > 0 else price_df[price_df['low'] == min_price]['time'].iloc[0]
    
    # Ajouter annotation au peak
    fig.add_annotation(
        x=peak_time,
        y=peak_price,
        text=f"Peak: {peak_price:.5f}<br>({(peak_price - start_price) * 10000:.1f} pips)",
        showarrow=True,
        arrowhead=2,
        arrowcolor="red",
        bgcolor="white",
        bordercolor="red"
    )
    
    return fig


def create_enhanced_prediction_chart_with_real(
    price_df: pd.DataFrame,
    real_prices_df: pd.DataFrame = None,
    start_price: float = None,
    total_impact_pips: float = 0,
    direction: int = 1,
    event_time: datetime = None,
    event_markers: List[Dict] = None,
    fib_levels: Dict[str, float] = None,
    show_spread: bool = False,
    show_real: bool = True,
    title: str = "🔮 Prédiction vs 📈 Réalité EUR/USD"
) -> go.Figure:
    """
    Crée un graphique professionnel comparant prédiction et réalité
    
    Args:
        price_df: DataFrame avec prédictions (time, open, high, low, close)
        real_prices_df: DataFrame avec prix réels (timestamp, open, high, low, close)
        start_price: Prix de départ
        total_impact_pips: Impact prédit en pips
        direction: Direction (+1/-1)
        event_time: Timestamp de l'événement
        event_markers: Liste de marqueurs d'événements
        fib_levels: Niveaux Fibonacci
        show_spread: Afficher bid/ask
        show_real: Afficher les prix réels
        title: Titre du graphique
    
    Returns:
        Figure Plotly interactive style trading professionnel
    """
    
    fig = go.Figure()
    
    # === CHANDELIERS PRÉDITS (vert/rouge translucide) ===
    fig.add_trace(go.Candlestick(
        x=price_df['time'],
        open=price_df['open'],
        high=price_df['high'],
        low=price_df['low'],
        close=price_df['close'],
        name='🔮 Prédiction',
        increasing_line_color='rgba(0,255,0,0.6)',
        decreasing_line_color='rgba(255,0,0,0.6)',
        increasing_fillcolor='rgba(0,255,0,0.2)',
        decreasing_fillcolor='rgba(255,0,0,0.2)',
        line=dict(width=2),
        whiskerwidth=0.8
    ))
    
    # === CHANDELIERS RÉELS (cyan/magenta opaques) ===
    if show_real and real_prices_df is not None and len(real_prices_df) > 0:
        fig.add_trace(go.Candlestick(
            x=real_prices_df['timestamp'],
            open=real_prices_df['open'],
            high=real_prices_df['high'],
            low=real_prices_df['low'],
            close=real_prices_df['close'],
            name='📈 Réalité',
            increasing_line_color='#00FFFF',
            decreasing_line_color='#FF00FF',
            increasing_fillcolor='rgba(0,255,255,0.5)',
            decreasing_fillcolor='rgba(255,0,255,0.5)',
            line=dict(width=3),
            whiskerwidth=1.0
        ))
    
    # === LIGNE PRIX DE DÉPART ===
    if start_price:
        fig.add_hline(
            y=start_price,
            line_dash="solid",
            line_color="white",
            line_width=2.5,
            annotation_text=f"💰 Départ: {start_price:.5f}",
            annotation_position="left",
            annotation=dict(
                font=dict(size=18, color="white", family="Arial Black"),
                bgcolor="rgba(0,0,0,0.8)"
            )
        )
    
    # === NIVEAUX FIBONACCI ===
    if fib_levels:
        fib_colors = {
            '0.0%': 'rgba(128,128,128,0.8)',
            '23.6%': 'rgba(100,150,255,0.8)',
            '38.2%': 'rgba(100,255,150,0.8)',
            '50.0%': 'rgba(255,255,100,0.8)',
            '61.8%': 'rgba(255,150,100,0.8)',
            '78.6%': 'rgba(255,100,100,0.8)',
            '100.0%': 'rgba(255,50,50,0.9)'
        }
        
        for level_name, price in fib_levels.items():
            color = fib_colors.get(level_name, 'lightgray')
            pips_from_start = (price - start_price) * 10000 if start_price else 0
            
            fig.add_hline(
                y=price,
                line_dash="dot",
                line_color=color,
                line_width=2.5,
                opacity=0.7,
                annotation_text=f"Fib {level_name}: {price:.5f} ({pips_from_start:+.1f} pips)",
                annotation_position="right",
                annotation=dict(
                    font=dict(size=14, color=color, family="Courier New", weight="bold"),
                    bgcolor="rgba(0,0,0,0.9)",
                    bordercolor=color,
                    borderwidth=1
                )
            )
    
    # === MARQUEURS D'ÉVÉNEMENTS ===
    if event_markers:
        for marker in event_markers:
            fig.add_vline(
                x=marker['time'],
                line_dash="solid",
                line_color=marker.get('color', 'yellow'),
                line_width=3,
                annotation_text=marker['label'],
                annotation_position="top",
                annotation=dict(
                    font=dict(size=18, color="white", family="Arial Black"),
                    bgcolor=marker.get('color', 'yellow'),
                    bordercolor="white",
                    borderwidth=2
                )
            )
    
    # === AFFICHAGE IMPACT ===
    if total_impact_pips != 0:
        impact_direction = "📈 HAUSSIER" if direction > 0 else "📉 BAISSIER"
        impact_color = "green" if direction > 0 else "red"
        
        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref="paper",
            yref="paper",
            text=f"<b>{impact_direction}</b><br>Impact: {total_impact_pips:.1f} pips",
            showarrow=False,
            font=dict(size=18, color="white", family="Arial Black"),
            bgcolor=impact_color,
            bordercolor="white",
            borderwidth=2,
            opacity=0.9,
            align="left"
        )
    
    # === STATS COMPARAISON ===
    if show_real and real_prices_df is not None and len(real_prices_df) > 0:
        pred_max = price_df['high'].max()
        pred_min = price_df['low'].min()
        real_max = real_prices_df['high'].max()
        real_min = real_prices_df['low'].min()
        
        pred_range_pips = (pred_max - pred_min) * 10000
        real_range_pips = (real_max - real_min) * 10000
        accuracy = min(pred_range_pips, real_range_pips) / max(pred_range_pips, real_range_pips) * 100 if max(pred_range_pips, real_range_pips) > 0 else 0
        
        comparison_text = f"""<b>📊 COMPARAISON</b><br>Amplitude Prédit: {pred_range_pips:.1f} pips<br>Amplitude Réel: {real_range_pips:.1f} pips<br>Précision: {accuracy:.1f}%"""
        
        fig.add_annotation(
            x=0.98,
            y=0.98,
            xref="paper",
            yref="paper",
            text=comparison_text,
            showarrow=False,
            font=dict(size=14, color="white", family="Courier New"),
            bgcolor="rgba(0,0,0,0.8)",
            bordercolor="cyan",
            borderwidth=2,
            opacity=0.9,
            align="right"
        )
    
    # === LAYOUT ===
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=28, color="white", family="Arial Black"),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Temps",
        yaxis_title="Prix EUR/USD",
        height=1100,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=18, color="white", family="Arial"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="white",
            borderwidth=1
        ),
        yaxis=dict(
            tickformat='.5f',
            gridcolor='rgba(128,128,128,0.3)',
            tickfont=dict(size=18, color="white", family="Courier New"),
            title_font=dict(size=18, color="white", family="Arial Black")
        ),
        xaxis=dict(
            tickformat='%H:%M',
            gridcolor='rgba(128,128,128,0.3)',
            tickfont=dict(size=18, color="white", family="Courier New"),
            title_font=dict(size=18, color="white", family="Arial Black"),
            rangeslider=dict(visible=False)
        ),
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117'
    )
    
    return fig
