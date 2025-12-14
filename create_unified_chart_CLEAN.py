#!/usr/bin/env python3
import os
from datetime import datetime

project_root = "/Users/andrevalentin/Projects/eurusd_news_impact_calculator"

# Code du module unifié
MODULE_CODE = """import plotly.graph_objects as go
from datetime import timedelta
import pandas as pd

def create_unified_prediction_chart(phases, predictions, real_prices_df=None, window_start=None, window_end=None):
    fig = go.Figure()
    
    if window_start is None:
        window_start = min(pd.to_datetime(p['event']['ts_utc']) for p in predictions) - timedelta(minutes=30)
    if window_end is None:
        window_end = max(pd.to_datetime(p['event']['ts_utc']) for p in predictions) + timedelta(minutes=90)
    
    # Prix réel
    if real_prices_df is not None and len(real_prices_df) > 0:
        plot_times = [t.to_pydatetime() if isinstance(t, pd.Timestamp) else t for t in real_prices_df['time']]
        fig.add_trace(go.Scatter(x=plot_times, y=real_prices_df['price'], mode='lines',
            name='💹 Prix Réel', line=dict(color='#2E86DE', width=3)))
        ref_price = real_prices_df.iloc[0]['price']
    else:
        ref_price = 1.17000
        fig.add_annotation(x=0.5, y=0.95, xref='paper', yref='paper',
            text='⚠️ Événements futurs - Trajectoire prédite uniquement',
            showarrow=False, font=dict(size=14, color='orange'))
    
    # Trajectoire prédite
    current_price = ref_price
    traj_times, traj_prices = [], []
    
    for idx, phase in enumerate(phases):
        start = pd.to_datetime(phase['start_time'])
        end = pd.to_datetime(phase['end_time'])
        
        if idx == 0:
            traj_times.append(start.to_pydatetime())
            traj_prices.append(current_price)
        
        impact = phase['predicted_movement_pips'] / 10000
        target = current_price + impact
        traj_times.append(end.to_pydatetime())
        traj_prices.append(target)
        
        color = '#10AC84' if impact > 0 else '#EE5A6F'
        arrow = '↗' if impact > 0 else '↘'
        
        fig.add_shape(type="rect", x0=start, x1=end, y0=current_price, y1=target,
            fillcolor=color, opacity=0.15, line_width=0, layer='below')
        
        label = f"Phase {idx+1}"
        if phase['events']:
            label += f"<br>{'+ '.join([e['family'] for e in phase['events']])}"
        
        mid = start + (end - start) / 2
        fig.add_annotation(x=mid, y=(current_price + target) / 2,
            text=f"{arrow} {label}<br>{abs(phase['predicted_movement_pips']):.0f} pips",
            showarrow=False, font=dict(size=11, color=color),
            bgcolor='rgba(255,255,255,0.8)', bordercolor=color, borderwidth=2)
        
        if phase['events']:
            evt_time = pd.to_datetime(phase['events'][0]['time'])
            fig.add_vline(x=evt_time, line_dash="dot", line_color=color, line_width=2,
                annotation_text=f"📊 {evt_time.strftime('%H:%M')}", annotation_position="top")
        
        current_price = target
    
    fig.add_trace(go.Scatter(x=traj_times, y=traj_prices, mode='lines+markers',
        name='🎯 Trajectoire Prédite', line=dict(color='#FFA502', width=3, dash='dash'),
        marker=dict(size=8, color='#FFA502', symbol='diamond')))
    
    fig.add_hline(y=ref_price, line_dash="dash", line_color="gray", line_width=1,
        annotation_text=f"Ref: {ref_price:.5f}", annotation_position="right")
    
    fig.update_layout(
        title={'text': '📈 Trajectoire Prédite vs Prix Réel EUR/USD', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Temps', yaxis_title='Prix EUR/USD',
        xaxis=dict(range=[window_start, window_end]),
        height=600, hovermode='x unified', showlegend=True,
        plot_bgcolor='#1E1E1E', paper_bgcolor='#2C2C2C', font=dict(color='white'))
    
    return fig
"""

# Sauvegarder
output = os.path.join(project_root, 'fx_impact_app/src/unified_chart.py')
with open(output, 'w') as f:
    f.write(MODULE_CODE)

print(f"✅ Module créé : {output}")

# Patcher le fichier principal
main_file = os.path.join(project_root, "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
backup = main_file + f".bak_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

with open(main_file, 'r') as f:
    content = f.read()

with open(backup, 'w') as f:
    f.write(content)

print(f"✅ Backup : {os.path.basename(backup)}")

# Import
if "from unified_chart import create_unified_prediction_chart" not in content:
    content = content.replace(
        "from latency_analyzer import LatencyAnalyzer",
        "from latency_analyzer import LatencyAnalyzer\nfrom unified_chart import create_unified_prediction_chart"
    )
    print("✅ Import ajouté")

# Code graphique
CHART_CODE = """
                            st.divider()
                            st.subheader("📈 Graphique Unifié : Trajectoire Prédite vs Prix Réel")
                            
                            now = pd.Timestamp.now(tz='UTC')
                            is_past = all(pd.to_datetime(p['event']['ts_utc']).tz_localize('UTC') < now 
                                         for p in predictions)
                            
                            real_prices_df = None
                            if is_past:
                                with st.spinner("📥 Récupération prix..."):
                                    first = min(pd.to_datetime(p['event']['ts_utc']) for p in predictions)
                                    prices_batch = get_real_prices_batch([first - timedelta(minutes=30)], 120)
                                    if 0 in prices_batch:
                                        real_prices_df = prices_batch[0]
                            
                            unified_fig = create_unified_prediction_chart(phases, predictions_for_seq, real_prices_df)
                            st.plotly_chart(unified_fig, use_container_width=True)
"""

if "Graphique Unifié : Trajectoire Prédite vs Prix Réel" not in content:
    content = content.replace(
        "display_sequential_timeline(phases, show_details=True)",
        "display_sequential_timeline(phases, show_details=True)" + CHART_CODE
    )
    print("✅ Graphique ajouté")

with open(main_file, 'w') as f:
    f.write(content)

print("✅ Fichier mis à jour")
print("\n📋 Rafraîchir Streamlit (F5)")
