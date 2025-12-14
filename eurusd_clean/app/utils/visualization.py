"""
Visualization Utilities

Fonctions pour créer des graphiques Plotly pour le planificateur multi-événements.
Migré depuis le Planificateur Multi-Événements et backtest_utils.py (Session 34).

Fonctions principales:
- create_timeline_chart() : Timeline visuelle interactive des événements
- create_backtest_chart() : Graphique comparaison prédiction vs réalité
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import pandas as pd


def create_timeline_chart(
    predictions: List[Dict[str, Any]],
    weighted_latency: float,
    min_ttr: float
) -> go.Figure:
    """
    Crée une timeline visuelle interactive des événements avec Plotly.
    
    Affiche les événements dans le temps avec leur fenêtre d'impact prédite,
    incluant la latence et le TTR. Utile pour visualiser la séquence temporelle
    des événements et identifier les périodes de complexité.
    
    Args:
        predictions: Liste de prédictions contenant:
                     - 'event': str - Nom événement
                     - 'event_time': datetime - Timestamp
                     - 'predicted_pips': float - Impact prédit (pips)
                     - 'direction': int - Direction (+1 ou -1)
                     - 'latency_median': float - Latence médiane (minutes)
                     - 'ttr_median': float - TTR médian (minutes)
        weighted_latency: Latence moyenne pondérée de la session (minutes)
        min_ttr: TTR minimum de la session (minutes)
    
    Returns:
        Figure Plotly interactive
    
    Example:
        >>> predictions = [
        ...     {'event': 'CPI', 'event_time': datetime(2025, 9, 11, 12, 30),
        ...      'predicted_pips': 20, 'direction': 1,
        ...      'latency_median': 5, 'ttr_median': 30}
        ... ]
        >>> fig = create_timeline_chart(predictions, weighted_latency=5.0, min_ttr=30.0)
        >>> # Display with: st.plotly_chart(fig) or fig.show()
    """
    fig = go.Figure()
    
    if not predictions:
        # Graphique vide avec message
        fig.add_annotation(
            text="Aucune prédiction à afficher",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    # Trier par event_time
    sorted_predictions = sorted(predictions, key=lambda p: p['event_time'])
    
    # Calculer positions Y (espacées)
    y_positions = list(range(len(sorted_predictions)))
    y_labels = [p['event'] for p in sorted_predictions]
    
    for idx, pred in enumerate(sorted_predictions):
        event_time = pred['event_time']
        latency = pred.get('latency_median', 5)
        ttr = pred.get('ttr_median', 30)
        impact = pred.get('predicted_pips', 0)
        direction = pred.get('direction', 1)
        
        # Calculer fenêtre complète
        reaction_start = event_time + timedelta(minutes=latency)
        reaction_end = reaction_start + timedelta(minutes=ttr)
        
        # Couleur selon direction
        color = '#10AC84' if direction > 0 else '#EE5A6F'
        arrow = '↗' if direction > 0 else '↘'
        
        # Marker pour l'événement
        fig.add_trace(go.Scatter(
            x=[event_time],
            y=[idx],
            mode='markers',
            name=pred['event'],
            marker=dict(
                size=15,
                color=color,
                symbol='diamond',
                line=dict(width=2, color='white')
            ),
            hovertemplate=(
                f"<b>{pred['event']}</b><br>"
                f"Temps: %{{x|%H:%M}}<br>"
                f"Impact: {arrow} {abs(impact):.1f} pips<br>"
                f"Latence: {latency:.0f} min<br>"
                f"TTR: {ttr:.0f} min<br>"
                "<extra></extra>"
            ),
            showlegend=False
        ))
        
        # Ligne horizontale pour la fenêtre d'impact
        fig.add_trace(go.Scatter(
            x=[reaction_start, reaction_end],
            y=[idx, idx],
            mode='lines',
            line=dict(color=color, width=6, dash='solid'),
            hovertemplate=(
                f"<b>Fenêtre d'impact</b><br>"
                f"Début: %{{x|%H:%M}}<br>"
                f"<extra></extra>"
            ),
            showlegend=False
        ))
        
        # Annotations pour latence et TTR
        fig.add_annotation(
            x=reaction_start,
            y=idx,
            text=f"L:{latency:.0f}m",
            showarrow=False,
            yshift=15,
            font=dict(size=9, color='gray'),
            bgcolor='rgba(255,255,255,0.8)',
            borderpad=2
        )
        
        fig.add_annotation(
            x=reaction_end,
            y=idx,
            text=f"TTR:{ttr:.0f}m",
            showarrow=False,
            yshift=15,
            font=dict(size=9, color='gray'),
            bgcolor='rgba(255,255,255,0.8)',
            borderpad=2
        )
    
    # Ligne verticale pour l'heure actuelle (si future)
    now = datetime.now()
    if sorted_predictions[0]['event_time'] > now:
        fig.add_vline(
            x=now,
            line=dict(color='blue', width=2, dash='dash'),
            annotation_text="Maintenant",
            annotation_position="top"
        )
    
    # Layout
    fig.update_layout(
        title={
            'text': f"Timeline Événements (Latence moy: {weighted_latency:.1f}min, TTR min: {min_ttr:.1f}min)",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        xaxis=dict(
            title="Temps",
            gridcolor='lightgray',
            showgrid=True
        ),
        yaxis=dict(
            title="Événements",
            tickmode='array',
            tickvals=y_positions,
            ticktext=y_labels,
            gridcolor='lightgray',
            showgrid=True
        ),
        hovermode='closest',
        height=max(400, len(sorted_predictions) * 60),
        plot_bgcolor='white',
        showlegend=False
    )
    
    return fig


def create_backtest_chart(
    prices_df: pd.DataFrame,
    event_time: datetime,
    predicted_impact_pips: float,
    predicted_latency: float,
    predicted_ttr: float,
    real_metrics: Optional[Dict[str, Any]]
) -> go.Figure:
    """
    Crée un graphique Plotly comparant prédictions vs réalité.
    
    Affiche les prix réels observés avec les marqueurs de prédiction
    (latence, TTR, impact) et les métriques réelles mesurées pour
    validation des prédictions.
    
    Args:
        prices_df: DataFrame avec colonnes 'time' (datetime) et 'price' (float)
        event_time: Timestamp de l'événement
        predicted_impact_pips: Impact prédit (signé, en pips)
        predicted_latency: Latence prédite (minutes)
        predicted_ttr: TTR prédit (minutes)
        real_metrics: Dictionnaire de métriques réelles depuis measure_real_impact():
                      - 'had_reaction': bool
                      - 'real_impact_pips': float
                      - 'real_direction': int
                      - 'real_latency_minutes': float
                      - 'real_ttr_minutes': float
                      - 'peak_time': datetime
                      - 'peak_price': float
                      - 'ref_price': float
                      - 'ref_time': datetime
    
    Returns:
        Figure Plotly interactive
    
    Example:
        >>> prices_df = pd.DataFrame({
        ...     'time': [datetime(2025, 9, 11, 12, 30), datetime(2025, 9, 11, 12, 31)],
        ...     'price': [1.1700, 1.1705]
        ... })
        >>> real_metrics = {
        ...     'had_reaction': True,
        ...     'real_impact_pips': 35.0,
        ...     'real_latency_minutes': 3.0,
        ...     'real_ttr_minutes': 7.0,
        ...     'peak_time': datetime(2025, 9, 11, 12, 33),
        ...     'peak_price': 1.1735
        ... }
        >>> fig = create_backtest_chart(
        ...     prices_df, datetime(2025, 9, 11, 12, 30),
        ...     predicted_impact_pips=40.0, predicted_latency=5.0, predicted_ttr=30.0,
        ...     real_metrics=real_metrics
        ... )
    """
    fig = go.Figure()
    
    # Normaliser event_time
    event_time = pd.to_datetime(event_time)
    if hasattr(event_time, 'tz') and event_time.tz is not None:
        event_time = event_time.tz_localize(None)
    
    # Ligne des prix réels
    fig.add_trace(go.Scatter(
        x=prices_df['time'],
        y=prices_df['price'],
        mode='lines',
        name='Prix EURUSD Observé',
        line=dict(color='#2E86DE', width=2),
        hovertemplate='<b>%{x|%H:%M:%S}</b><br>Prix: %{y:.5f}<extra></extra>'
    ))
    
    # Ligne verticale : Événement
    fig.add_vline(
        x=event_time,
        line=dict(color='red', width=2, dash='dash'),
        annotation_text="📅 Événement",
        annotation_position="top"
    )
    
    # Métriques réelles (si disponibles)
    if real_metrics and real_metrics.get('had_reaction'):
        # Marquer le pic réel
        fig.add_trace(go.Scatter(
            x=[real_metrics['peak_time']],
            y=[real_metrics['peak_price']],
            mode='markers',
            name='Pic Réel',
            marker=dict(color='#10AC84', size=15, symbol='star'),
            hovertemplate=(
                f"<b>⭐ Pic Réel</b><br>"
                f"Temps: %{{x|%H:%M:%S}}<br>"
                f"Prix: %{{y:.5f}}<br>"
                f"Latence: {real_metrics['real_latency_minutes']:.1f} min<br>"
                f"Impact: {real_metrics['real_impact_pips']:.1f} pips<br>"
                f"<extra></extra>"
            )
        ))
        
        # Ligne verticale : TTR réel
        if real_metrics['real_ttr_minutes'] < len(prices_df):
            ttr_time = prices_df.iloc[int(real_metrics['real_ttr_minutes'])]['time']
            fig.add_vline(
                x=ttr_time,
                line=dict(color='#10AC84', width=2, dash='dot'),
                annotation_text=f"✅ TTR Réel ({real_metrics['real_ttr_minutes']:.0f}min)",
                annotation_position="bottom"
            )
    
    # Lignes de prédiction
    pred_latency_time = event_time + timedelta(minutes=predicted_latency)
    fig.add_vline(
        x=pred_latency_time,
        line=dict(color='orange', width=1, dash='dot'),
        annotation_text=f"🔮 Latence Prédite ({predicted_latency:.0f}min)",
        annotation_position="top"
    )
    
    pred_ttr_time = event_time + timedelta(minutes=predicted_ttr)
    fig.add_vline(
        x=pred_ttr_time,
        line=dict(color='purple', width=1, dash='dot'),
        annotation_text=f"🔮 TTR Prédit ({predicted_ttr:.0f}min)",
        annotation_position="bottom"
    )
    
    # Annotation avec métriques comparatives
    if real_metrics and real_metrics.get('had_reaction'):
        latency_error = abs(real_metrics['real_latency_minutes'] - predicted_latency)
        ttr_error = abs(real_metrics['real_ttr_minutes'] - predicted_ttr)
        impact_error = abs(real_metrics['real_impact_pips'] - predicted_impact_pips)
        
        comparison_text = (
            f"<b>Comparaison Prédiction vs Réalité</b><br>"
            f"Impact: {predicted_impact_pips:.1f} pips (prédit) vs {real_metrics['real_impact_pips']:.1f} pips (réel) | ±{impact_error:.1f}<br>"
            f"Latence: {predicted_latency:.0f} min (prédit) vs {real_metrics['real_latency_minutes']:.0f} min (réel) | ±{latency_error:.0f}<br>"
            f"TTR: {predicted_ttr:.0f} min (prédit) vs {real_metrics['real_ttr_minutes']:.0f} min (réel) | ±{ttr_error:.0f}"
        )
        
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            text=comparison_text,
            showarrow=False,
            font=dict(size=11, color='black'),
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='gray',
            borderwidth=1,
            borderpad=8,
            align='left',
            xanchor='left',
            yanchor='top'
        )
    
    # Layout
    fig.update_layout(
        title={
            'text': "📊 Backtest : Prix Réels vs Prédictions",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        xaxis=dict(
            title="Temps",
            gridcolor='lightgray',
            showgrid=True
        ),
        yaxis=dict(
            title="Prix EURUSD",
            gridcolor='lightgray',
            showgrid=True
        ),
        hovermode='x unified',
        height=500,
        plot_bgcolor='white',
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
