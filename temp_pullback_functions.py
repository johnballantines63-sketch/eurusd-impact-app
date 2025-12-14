

# ═══════════════════════════════════════════════════════════════
# NOUVELLES FONCTIONS PHASE 2 - PULLBACK GRAPHIQUE v8.6.2
# Ajoutées le 14 octobre 2025
# ═══════════════════════════════════════════════════════════════

def generate_candlestick_curve_from_phases(
    start_price: float,
    phases: List[Dict],
    base_time: datetime,
    duration_minutes: int = 120,
    volatility_factor: float = 0.3,
    spread_pips: float = 0.0
) -> pd.DataFrame:
    """
    Génère courbe chandeliers à partir des phases séquentielles avec PULLBACK
    
    Args:
        start_price: Prix de départ EUR/USD
        phases: Liste phases de sequence_multi_event_timeline_v86
        base_time: Timestamp de référence
        duration_minutes: Durée totale simulation
        volatility_factor: Facteur volatilité (0.1=calme, 1.0=fort)
        spread_pips: Spread bid/ask en pips
    
    Returns:
        DataFrame avec colonnes: time, open, high, low, close, bid, ask, phase, phase_num
    """
    candles = []
    current_price = start_price
    spread_price = spread_pips / 10000
    
    # Convertir timestamps en datetime
    for phase in phases:
        if isinstance(phase.get('start_time'), str):
            phase['start_time'] = pd.to_datetime(phase['start_time'])
        if isinstance(phase.get('peak_time'), str):
            phase['peak_time'] = pd.to_datetime(phase['peak_time'])
    
    # Générer minute par minute
    for minute in range(duration_minutes + 1):
        current_time = base_time + timedelta(minutes=minute)
        
        # Trouver phase active et type de période
        active_phase_num = 0
        phase_type = "pre_event"
        target_price = current_price
        
        for i, phase in enumerate(phases):
            phase_start = phase['start_time']
            phase_peak = phase.get('peak_time', phase_start + timedelta(minutes=phase.get('ttr_predicted', 30)))
            phase_end = phase_start + timedelta(minutes=phase.get('duration_minutes', 60))
            
            # PULLBACK : Zone entre pic phase précédente et début phase actuelle
            if i > 0 and phases[i].get('pullback_pips', 0) > 0:
                prev_peak = phases[i-1].get('peak_time', phases[i-1]['start_time'])
                
                if prev_peak <= current_time < phase_start:
                    # ON EST DANS LA ZONE PULLBACK !
                    active_phase_num = i
                    phase_type = "pullback"
                    
                    # Calculer progression dans le pullback (0.0 à 1.0)
                    total_pullback_minutes = (phase_start - prev_peak).total_seconds() / 60
                    elapsed_minutes = (current_time - prev_peak).total_seconds() / 60
                    progress = min(1.0, elapsed_minutes / max(1, total_pullback_minutes))
                    
                    # Descente linéaire
                    prev_cumul_price = phases[i-1].get('cumulative_price', start_price)
                    pullback_amount = phases[i].get('pullback_pips', 0) / 10000
                    
                    target_price = prev_cumul_price - (pullback_amount * progress)
                    break
            
            # Phase normale
            if current_time < phase_start:
                # Avant cette phase
                continue
            elif current_time >= phase_start and current_time <= phase_end:
                active_phase_num = phase['phase_num']
                latency = phase.get('latency_minutes', 1.0)
                ttr = phase.get('ttr_predicted', 30.0)
                duration = phase.get('duration_minutes', 60.0)
                
                minutes_in_phase = (current_time - phase_start).total_seconds() / 60
                
                if minutes_in_phase < latency:
                    # LATENCE
                    phase_type = "latence"
                    target_price = current_price
                
                elif minutes_in_phase < ttr:
                    # MOUVEMENT
                    phase_type = "mouvement"
                    
                    # Progression sigmoid
                    progress = (minutes_in_phase - latency) / max(1, (ttr - latency))
                    sigmoid_progress = sigmoid(10 * (progress - 0.5))
                    
                    # Impact avec direction
                    impact_pips = phase.get('impact_combined', 0)
                    impact_price = impact_pips / 10000
                    
                    # Calculer prix depuis cumulative_price ou depuis current
                    phase_start_price = current_price if i == 0 else phases[i-1].get('cumulative_price', start_price)
                    target_price = phase_start_price + (impact_price * sigmoid_progress)
                
                else:
                    # RETRACEMENT (Fibonacci 38.2%)
                    phase_type = "retracement"
                    
                    time_since_peak = minutes_in_phase - ttr
                    retracement_progress = min(1.0, time_since_peak / 20)
                    exp_progress = 1 - np.exp(-3 * retracement_progress)
                    
                    impact_price = phase.get('impact_combined', 0) / 10000
                    phase_start_price = current_price if i == 0 else phases[i-1].get('cumulative_price', start_price)
                    peak_price = phase_start_price + impact_price
                    
                    target_price = peak_price - (impact_price * 0.382 * exp_progress)
                
                break
        
        # Générer chandelier avec volatilité
        candle = generate_ohlc_candle(
            open_price=current_price,
            target_price=target_price,
            volatility=0.00003 * volatility_factor,
            trend_strength=0.8
        )
        
        # Ajouter spread
        mid_close = candle['close']
        
        candles.append({
            'time': current_time,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': mid_close,
            'bid': mid_close - spread_price/2,
            'ask': mid_close + spread_price/2,
            'phase': phase_type,
            'phase_num': active_phase_num,
            'minute_offset': minute
        })
        
        current_price = mid_close
    
    return pd.DataFrame(candles)


def create_sequential_phases_chart(
    price_df: pd.DataFrame,
    phases: List[Dict],
    start_price: float,
    title: str = "📊 Timeline Séquentielle Multi-Événements avec Pullback"
) -> go.Figure:
    """
    Crée graphique Plotly avec zones colorées par type de phase
    
    Args:
        price_df: DataFrame de generate_candlestick_curve_from_phases
        phases: Liste phases (pour annotations)
        start_price: Prix de départ
        title: Titre du graphique
    
    Returns:
        Figure Plotly interactive
    """
    fig = go.Figure()
    
    # Couleurs par type de phase
    phase_colors = {
        'pre_event': {'increasing': 'lightgray', 'decreasing': 'darkgray'},
        'latence': {'increasing': 'lightyellow', 'decreasing': 'khaki'},
        'mouvement': {'increasing': 'green', 'decreasing': 'red'},
        'pullback': {'increasing': 'orange', 'decreasing': 'darkorange'},  # ← CLÉ !
        'retracement': {'increasing': 'lightcoral', 'decreasing': 'indianred'},
        'post_event': {'increasing': 'lightgray', 'decreasing': 'darkgray'}
    }
    
    # Grouper par phase pour afficher avec bonne couleur
    for phase_type in price_df['phase'].unique():
        phase_data = price_df[price_df['phase'] == phase_type]
        
        if len(phase_data) == 0:
            continue
        
        colors = phase_colors.get(phase_type, {'increasing': 'gray', 'decreasing': 'gray'})
        
        # Ajouter trace chandelier
        fig.add_trace(go.Candlestick(
            x=phase_data['time'],
            open=phase_data['open'],
            high=phase_data['high'],
            low=phase_data['low'],
            close=phase_data['close'],
            name=f"{phase_type.capitalize()}",
            increasing_line_color=colors['increasing'],
            decreasing_line_color=colors['decreasing'],
            showlegend=True
        ))
    
    # Ligne horizontale prix de départ
    fig.add_hline(
        y=start_price,
        line_dash="dash",
        line_color="cyan",
        annotation_text="Prix départ",
        annotation_position="right"
    )
    
    # Lignes verticales et annotations pour chaque phase
    for phase in phases:
        phase_start = pd.to_datetime(phase['start_time'])
        phase_num = phase['phase_num']
        impact = phase.get('impact_combined', 0)
        pullback = phase.get('pullback_pips', 0)
        
        # Ligne verticale
        fig.add_vline(
            x=phase_start,
            line_dash="dot",
            line_color="white",
            opacity=0.5
        )
        
        # Annotation
        annotation_text = f"📍 Phase {phase_num}"
        if pullback > 0:
            annotation_text += f"\n🔄 Pullback: -{pullback:.1f} pips"
        annotation_text += f"\nImpact: {impact:+.1f} pips"
        
        fig.add_annotation(
            x=phase_start,
            y=price_df['high'].max(),
            text=annotation_text,
            showarrow=True,
            arrowhead=2,
            arrowcolor="white",
            ax=0,
            ay=-40,
            font=dict(size=12, color="white"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="white",
            borderwidth=1
        )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=24, color="white", family="Arial Black"),
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
            font=dict(size=12, color="white"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="white",
            borderwidth=1
        ),
        yaxis=dict(
            tickformat='.5f',
            gridcolor='rgba(128,128,128,0.3)',
            tickfont=dict(size=12, color="white"),
            title_font=dict(size=14, color="white", family="Arial Black")
        ),
        xaxis=dict(
            tickformat='%H:%M',
            gridcolor='rgba(128,128,128,0.3)',
            tickfont=dict(size=12, color="white"),
            title_font=dict(size=14, color="white", family="Arial Black"),
            rangeslider=dict(visible=False)
        ),
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117'
    )
    
    return fig


def plt_to_rgb(color_name: str) -> Tuple[float, float, float]:
    """
    Convertit nom de couleur matplotlib en RGB normalisé (0-1)
    
    Args:
        color_name: Nom couleur ('green', 'orange', etc.)
    
    Returns:
        Tuple (R, G, B) avec valeurs 0-1
    """
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
        'indianred': (0.804, 0.361, 0.361),
        'cyan': (0, 1, 1),
        'white': (1, 1, 1),
        'black': (0, 0, 0)
    }
    
    return color_map.get(color_name.lower(), (0.5, 0.5, 0.5))  # Gris par défaut
