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
        
        # ✅ CORRECTION V3 : Calculer impact vectoriel AVANT la boucle temporelle
        # On calcule la somme vectorielle des impacts (avec directions)
        vectorial_impact_at_peak = sum(
            (pred['predicted_pips'] / 10000) * pred['direction'] 
            for pred in predictions
        )
        
        # Direction globale
        global_direction = 1 if vectorial_impact_at_peak > 0 else -1
        
        # Calculer prix cible pour cette minute
        target_price = start_price
        active_phase = "stable"
        
        # Trouver l'événement le plus avancé dans sa phase
        max_progress = 0.0
        
        for pred in predictions:
            event_time = pred['event_time']
            minutes_since_event = (current_time - event_time).total_seconds() / 60
            
            if minutes_since_event < 0:
                continue
            
            latency = pred['latency_median']
            ttr = pred['ttr_median']
            
            # Calculer le progress pour cet événement
            if minutes_since_event < latency:
                progress = 0.0
                active_phase = "latence"
            elif minutes_since_event < ttr:
                progress = (minutes_since_event - latency) / (ttr - latency)
                active_phase = "mouvement"
            else:
                time_since_peak = minutes_since_event - ttr
                retracement_progress = min(1.0, time_since_peak / 20)
                progress = 1.0 - (0.382 * (1 - np.exp(-3 * retracement_progress)))
                active_phase = "retracement"
            
            max_progress = max(max_progress, progress)
        
        # Appliquer le mouvement vectoriel avec le progress maximum
        if max_progress > 0:
            if active_phase == "mouvement":
                sigmoid_progress = sigmoid(10 * (max_progress - 0.5))
                contribution = vectorial_impact_at_peak * sigmoid_progress
            else:  # retracement
                contribution = vectorial_impact_at_peak * max_progress
            
            target_price += contribution
        
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
