import plotly.graph_objects as go
from datetime import timedelta
import pandas as pd

def create_unified_prediction_chart(phases, predictions, real_prices_df=None, window_start=None, window_end=None):
    """
    Crée le graphique unifié avec la NOUVELLE structure de phases (calcul vectoriel)
    """
    fig = go.Figure()
    
    # Fenêtre temporelle
    if window_start is None:
        window_start = min(pd.to_datetime(p['event']['ts_utc']) for p in predictions) - timedelta(minutes=30)
    if window_end is None:
        window_end = max(pd.to_datetime(p['event']['ts_utc']) for p in predictions) + timedelta(minutes=90)
    
    # Prix réel (si disponible)
    if real_prices_df is not None and len(real_prices_df) > 0:
        plot_times = [t.to_pydatetime() if isinstance(t, pd.Timestamp) else t for t in real_prices_df['time']]
        fig.add_trace(go.Scatter(
            x=plot_times, 
            y=real_prices_df['price'], 
            mode='lines',
            name='💹 Prix Réel EUR/USD', 
            line=dict(color='#2E86DE', width=3),
            hovertemplate='<b>Prix</b><br>%{x}<br>%{y:.5f}<extra></extra>'
        ))
        ref_price = real_prices_df.iloc[0]['price']
    else:
        ref_price = 1.17000
        fig.add_annotation(
            x=0.5, y=0.95, 
            xref='paper', yref='paper',
            text='⚠️ Événements futurs - Trajectoire prédite uniquement',
            showarrow=False, 
            font=dict(size=14, color='orange'),
            bgcolor='rgba(255,165,0,0.1)',
            bordercolor='orange',
            borderwidth=2
        )
    
    # Trajectoire prédite
    current_price = ref_price
    traj_times = [window_start.to_pydatetime()]
    traj_prices = [current_price]
    
    for idx, phase in enumerate(phases):
        # Parser timestamps (format string)
        start = pd.to_datetime(eval(phase['start_time']))
        end = pd.to_datetime(eval(phase['predicted_end']))
        
        # Impact combiné (déjà signé avec direction)
        impact_pips = phase['impact_pips']
        impact_price = impact_pips / 10000
        target_price = current_price + impact_price
        
        # Ajouter points à la trajectoire
        traj_times.append(start.to_pydatetime())
        traj_prices.append(current_price)
        
        traj_times.append(end.to_pydatetime())
        traj_prices.append(target_price)
        
        # Couleur selon direction
        color = '#10AC84' if impact_pips > 0 else '#EE5A6F'
        arrow = '↗' if impact_pips > 0 else '↘'
        
        # Zone colorée pour le mouvement
        fig.add_shape(
            type="rect",
            x0=start, x1=end,
            y0=current_price, y1=target_price,
            fillcolor=color,
            opacity=0.15,
            line_width=0,
            layer='below'
        )
        
        # Label de la phase
        families = [e['family'] for e in phase['events']]
        families_str = ' + '.join(families)
        label = f"Phase {idx + 1}<br>{families_str}"
        
        mid_time = start + (end - start) / 2
        mid_price = (current_price + target_price) / 2
        
        fig.add_annotation(
            x=mid_time,
            y=mid_price,
            text=f"{arrow} {label}<br>{abs(impact_pips):.0f} pips",
            showarrow=False,
            font=dict(size=11, color=color, family='Arial Black'),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor=color,
            borderwidth=2,
            borderpad=4
        )
        
        # Ligne verticale événement(s)
        fig.add_vline(
            x=start,
            line_dash="dot",
            line_color=color,
            line_width=2,
            annotation_text=f"📊 {start.strftime('%H:%M')}",
            annotation_position="top"
        )
        
        # Mettre à jour prix courant pour prochaine phase
        current_price = target_price
    
    # Ligne trajectoire prédite
    fig.add_trace(go.Scatter(
        x=traj_times,
        y=traj_prices,
        mode='lines+markers',
        name='🎯 Trajectoire Prédite',
        line=dict(color='#FFA502', width=3, dash='dash'),
        marker=dict(size=8, color='#FFA502', symbol='diamond'),
        hovertemplate='<b>Prédit</b><br>%{x}<br>%{y:.5f}<extra></extra>'
    ))
    
    # Ligne de référence
    fig.add_hline(
        y=ref_price,
        line_dash="dash",
        line_color="gray",
        line_width=1,
        annotation_text=f"Référence: {ref_price:.5f}",
        annotation_position="right"
    )
    
    # Configuration du graphique
    fig.update_layout(
        title={
            'text': '📈 Trajectoire Prédite vs Prix Réel EUR/USD',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'family': 'Arial Black'}
        },
        xaxis_title='Temps',
        yaxis_title='Prix EUR/USD',
        xaxis=dict(
            range=[window_start, window_end],
            gridcolor='rgba(128,128,128,0.2)',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='rgba(128,128,128,0.2)',
            showgrid=True,
            tickformat='.5f'
        ),
        height=600,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)'
        ),
        plot_bgcolor='#1E1E1E',
        paper_bgcolor='#2C2C2C',
        font=dict(color='white')
    )
    
    return fig
