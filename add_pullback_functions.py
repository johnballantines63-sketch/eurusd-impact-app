#!/usr/bin/env python3
"""
Script pour ajouter les fonctions de pullback à price_curve_generator.py
"""

# Fonctions à ajouter
functions_to_add = '''

# ═══════════════════════════════════════════════════════════════
# NOUVELLES FONCTIONS PHASE 2 - PULLBACK GRAPHIQUE v8.6.2
# Ajoutées le 15 octobre 2025
# ═══════════════════════════════════════════════════════════════

def create_sequential_phases_chart(
    price_df: pd.DataFrame,
    phases: List[Dict],
    start_price: float,
    title: str = "📊 Timeline Séquentielle Multi-Événements avec Pullback"
) -> go.Figure:
    """
    Crée graphique Plotly avec zones colorées par type de phase
    
    CORRECTION v2: Conversion pd.Timestamp en datetime pour compatibilité Plotly
    
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
        # ✅ CORRECTION: Convertir pd.Timestamp en datetime Python
        phase_start = pd.to_datetime(phase['start_time'])
        if hasattr(phase_start, 'to_pydatetime'):
            phase_start = phase_start.to_pydatetime()
        
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
            annotation_text += f"\\n🔄 Pullback: -{pullback:.1f} pips"
        annotation_text += f"\\nImpact: {impact:+.1f} pips"
        
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
'''

# Lire le fichier actuel
with open('fx_impact_app/src/price_curve_generator.py', 'r', encoding='utf-8') as f:
    current_content = f.read()

# Vérifier si les fonctions existent déjà
if 'def create_sequential_phases_chart' in current_content:
    print("⚠️ Les fonctions existent déjà dans le fichier")
    print("   Elles seront remplacées par les versions corrigées")
    
    # Chercher où insérer (avant la dernière fonction existante)
    # Pour simplifier, on ajoute juste à la fin
    import re
    # Supprimer les anciennes versions si elles existent
    pattern = r'\n# ═+\n# NOUVELLES FONCTIONS PHASE 2.*?(?=\n(?:def |# ═+|$))'
    current_content = re.sub(pattern, '', current_content, flags=re.DOTALL)

# Ajouter les nouvelles fonctions
new_content = current_content + functions_to_add

# Sauvegarder
with open('fx_impact_app/src/price_curve_generator.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Fonctions ajoutées avec succès à price_curve_generator.py")
print("   - create_sequential_phases_chart() (avec correction pandas)")
print("   - plt_to_rgb()")
