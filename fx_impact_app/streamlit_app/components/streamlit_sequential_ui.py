"""
COMPOSANT UI STREAMLIT POUR TIMELINE SÉQUENTIELLE v8.3
Fichier complet prêt à copier

À copier dans : fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Any

# Import du générateur de courbe avec pullback
try:
    from price_curve_generator import (
        generate_candlestick_curve_from_phases,
        create_sequential_phases_chart
    )
    PRICE_CURVE_AVAILABLE = True
except ImportError:
    PRICE_CURVE_AVAILABLE = False
    print("⚠️ Import price_curve_generator échoué - graphique prix non disponible")

# Import depuis le module principal
try:
    from sequence_multi_event_timeline import (
        calculate_sequential_metrics,
        phases_to_dataframe
    )
except ImportError:
    # Si import échoue, définir fonctions localement
    pass

import re

def parse_timestamp_string(ts_str):
    """
    Parse un timestamp au format string vers datetime
    
    Gère les formats :
    - "2025-09-11 14:30:00+02:00"
    - "Timestamp('2025-09-11 14:30:00+0200', tz='Europe/Zurich')"
    """
    import pandas as pd
    import re
    
    if not ts_str:
        return pd.Timestamp.now()
    
    # Si c'est déjà un Timestamp ou datetime
    if isinstance(ts_str, pd.Timestamp):
        return ts_str
    
    # Extraire la date du format "Timestamp('...')" ou directement
    # Pattern: chercher une date ISO (2025-09-11 14:30:00...)
    match = re.search(r'(\d{4}-\d{2}-\d{2}[^"\']*)', str(ts_str))
    if match:
        date_str = match.group(1)
        # Nettoyer le timezone si présent (format court → format ISO)
        date_str = date_str.replace('+0200', '+02:00').replace('+0100', '+01:00')
        try:
            return pd.to_datetime(date_str)
        except:
            pass
    
    # Fallback : essayer de parser directement
    try:
        return pd.to_datetime(str(ts_str))
    except:
        return pd.Timestamp.now()




def display_sequential_timeline(phases: List[Dict[str, Any]], show_details: bool = True):
    """
    Afficher la timeline séquentielle multi-événements dans Streamlit
    
    Args:
        phases: Liste de phases retournées par sequence_multi_event_timeline()
        show_details: Si True, affiche les détails de chaque phase (expanders)
    """
    
    if not phases:
        st.warning("Aucune phase à afficher")
        return
    
    # En-tête
    st.subheader("📊 Timeline Séquentielle Multi-Événements")
    
    # Info box explicative
    with st.expander("ℹ️ Comment lire cette timeline ?", expanded=False):
        st.markdown("""
        **Concept :** Quand plusieurs événements se suivent de près, ils créent des **phases distinctes**.
        
        **Problème résolu :**
        - ❌ **Avant :** On calculait un TTR global depuis le 1er événement jusqu'au retournement final
        - ✅ **Maintenant :** Chaque événement a sa propre phase avec son TTR réel
        
        **Exemple 11/09/2025 :**
        ```
        14:30 → Jobless + CPI (mouvement DOWN)
        14:35 → Retracement (TTR₁ = 5 min) ✅
        14:45 → Current Account (NOUVEAU mouvement UP)
        14:50 → Retracement (TTR₂ = 5 min) ✅
        ```
        
        Sans séquençage, on aurait mesuré : TTR = 20 min ❌  
        Avec séquençage, on mesure : TTR₁ = 5 min, TTR₂ = 5 min ✅
        
        **Légende :**
        - 🟢 **Phase complète** : L'événement a eu le temps de faire son TTR complet
        - 🟡 **Phase interrompue** : Un événement suivant a coupé le mouvement avant son TTR théorique
        - 🔺 **UP** : Mouvement haussier (EUR/USD monte)
        - 🔻 **DOWN** : Mouvement baissier (EUR/USD descend)
        """)
    
    # Statistiques globales en haut
    metrics = calculate_sequential_metrics(phases)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Phases totales", 
            metrics['total_phases'],
            help="Nombre d'événements analysés"
        )
    
    with col2:
        st.metric(
            "Durée totale", 
            f"{metrics['total_duration']:.0f} min",
            help="Du premier événement au dernier retournement"
        )
    
    with col3:
        st.metric(
            "TTR moyen", 
            f"{metrics['avg_ttr']:.1f} min",
            help="Time-To-Reversal moyen par phase"
        )
    
    with col4:
        pct_interrupted = metrics['interrupted_pct']
        st.metric(
            "Interrompues", 
            f"{metrics['interrupted_count']}/{metrics['total_phases']}",
            delta=f"{pct_interrupted:.0f}%",
            delta_color="inverse",
            help="Phases coupées par événement suivant"
        )
    
    # Impact net
    impact_icon = "🔺" if metrics['net_direction'] == 'UP' else "🔻" if metrics['net_direction'] == 'DOWN' else "➡️"
    st.info(
        f"{impact_icon} **Impact net cumulé :** {abs(metrics['total_impact']):.1f} pips "
        f"**{metrics['net_direction']}**"
    )
    
    st.markdown("---")
    
    # Affichage de chaque phase
    st.subheader("📋 Détails par Phase")
    
    for phase in phases:
        display_phase_detail(phase, show_details)
    
    st.markdown("---")
    
    # Tableau récapitulatif
    display_phase_summary_table(phases)
    
    # Graphique timeline
    if st.checkbox("📈 Afficher graphique timeline", value=False, key="show_timeline_chart"):
        display_timeline_gantt_chart(phases)
    
    # ✨ NOUVEAU : Graphique de prix avec pullback
    st.markdown("---")
    if st.checkbox("📈 Afficher évolution des prix avec pullback", value=True, key="show_price_chart"):
        # Déterminer prix de départ et durée
        start_price = 1.17000  # Valeur par défaut
        
        # Calculer durée totale et base_time
        first_time = pd.to_datetime(phases[0]['start_time'])
        last_time = pd.to_datetime(phases[-1]['start_time']) + pd.Timedelta(minutes=phases[-1]['duration_minutes'])
        duration_minutes = int((last_time - first_time).total_seconds() / 60) + 30  # +30 min buffer
        
        display_price_chart_with_pullback(
            phases=phases,
            start_price=start_price,
            base_time=first_time,
            duration_minutes=duration_minutes
        )


def display_phase_detail(phase: Dict[str, Any], expanded: bool = True):
    """
    Afficher détails d'une phase individuelle
    
    Args:
        phase: Dictionnaire de phase
        expanded: Si True, expander ouvert par défaut
    """
    # Couleur selon interruption
    status_icon = "🟡" if False else "🟢"
    status_text = "Interrompue" if False else "Complète"
    
    # Direction icon
    direction_icon = "🔺" if phase['direction'] == 'UP' else "🔻"
    
    # Titre de la phase
    phase_title = (
        f"{status_icon} **Phase {phase['phase_num']}** : "
        f"{' + '.join([e['family'] for e in phase['events']])} ({phase['events'][0]['country'] if phase.get('events') else 'N/A'}) "
        f"à {parse_timestamp_string(phase['start_time']).strftime('%H:%M')} {direction_icon}"
    )
    
    with st.expander(phase_title, expanded=expanded):
        # Métriques en colonnes
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            impact_value = abs(phase.get('impact_combined', 0))
            delta_text = phase['direction']
            st.metric(
                "Impact", 
                f"{impact_value:.1f} pips",
                delta=delta_text,
                help="Impact prédit en pips (direction indiquée par flèche)"
            )
        
        with col2:
            st.metric(
                "Latence",
                f"{phase['latency_minutes']:.0f} min",
                help="Temps avant que le mouvement commence après l'annonce"
            )
        
        with col3:
            # Afficher TTR avec warning si interrompu
            ttr_delta = None
            ttr_delta_color = "off"
            
            if False:
                diff = phase.get('ttr_predicted', 30) - phase.get('ttr_predicted', phase.get('duration_minutes', 30))
                ttr_delta = f"-{diff:.0f} min"
                ttr_delta_color = "inverse"
            
            st.metric(
                "TTR réel",
                f"{phase.get('ttr_predicted', phase.get('duration_minutes', 30)):.0f} min",
                delta=ttr_delta,
                delta_color=ttr_delta_color,
                help="Time To Reversal réel (tronqué si interrompu)"
            )
        
        with col4:
            st.metric(
                "Durée",
                f"{phase['duration_minutes']:.0f} min",
                help="Durée totale de la phase (latence + TTR)"
            )
        
        # Fenêtre temporelle
        st.markdown("**⏰ Fenêtre temporelle :**")
        col_start, col_arrow, col_end = st.columns([2, 1, 2])
        
        with col_start:
            st.code(parse_timestamp_string(phase['start_time']).strftime('%H:%M:%S'))
        with col_arrow:
            st.markdown("<center>→</center>", unsafe_allow_html=True)
        with col_end:
            st.code(parse_timestamp_string(phase.get('predicted_end', '')).strftime('%H:%M:%S'))
        
        # Données économiques
        if phase.get('surprise') or phase.get('actual_value') or phase.get('forecast'):
            st.markdown("**📊 Données économiques :**")
            data_col1, data_col2, data_col3 = st.columns(3)
            
            with data_col1:
                if phase.get('actual_value'):
                    st.caption(f"Réel : {phase['actual_value']}")
            with data_col2:
                if phase.get('forecast'):
                    st.caption(f"Prévu : {phase['forecast']}")
            with data_col3:
                if phase.get('surprise'):
                    surprise_icon = "⬆️" if phase['surprise'] > 0 else "⬇️"
                    st.caption(f"Surprise : {surprise_icon} {phase['surprise']:+.1f}%")
        
        # Message statut
        if False:
            st.warning(
                f"⚠️ **{phase['note']}**"
            )
            
            # Détails interruption
            pct_completed = (phase.get('ttr_predicted', phase.get('duration_minutes', 30)) / phase.get('ttr_predicted', 30)) * 100
            st.caption(
                f"💡 TTR prévu: {phase.get('ttr_predicted', 30):.0f} min → "
                f"TTR réel: {phase.get('ttr_predicted', phase.get('duration_minutes', 30)):.0f} min "
                f"(**{pct_completed:.0f}%** du temps prévu utilisé)"
            )
        else:
            st.success(phase.get('note', '✅ Phase complète sans interférence'))
        
        # Données brutes (debug)
        if st.checkbox(
            f"🔍 Voir données brutes", 
            key=f"raw_phase_{phase['phase_num']}", 
            value=False
        ):
            st.json(phase)


def display_phase_summary_table(phases: List[Dict[str, Any]]):
    """
    Afficher tableau récapitulatif de toutes les phases
    
    Args:
        phases: Liste de phases
    """
    st.subheader("📋 Tableau Récapitulatif")
    
    # Créer DataFrame
    df = phases_to_dataframe(phases)
    
    # Styliser (si possible)
    try:
        # Fonction de style pour colorier selon statut
        def highlight_interrupted(row):
            if '🟡' in str(row['Statut']):
                return ['background-color: #fff3cd'] * len(row)
            else:
                return ['background-color: #d4edda'] * len(row)
        
        styled_df = df.style.apply(highlight_interrupted, axis=1)
        st.dataframe(styled_df, width='stretch', height=min(400, (len(phases) + 1) * 35))
    except:
        # Fallback sans style
        st.dataframe(df, width='stretch', height=min(400, (len(phases) + 1) * 35))
    
    # Export CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Télécharger CSV",
        data=csv,
        file_name=f"timeline_sequential_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def display_price_chart_with_pullback(
    phases: List[Dict[str, Any]],
    start_price: float,
    base_time: datetime,
    duration_minutes: int = 120
):
    """
    Affiche le graphique de prix avec pullback visible
    
    VERSION 8.6.6 : FONCTION CRITIQUE pour corriger le bug d'affichage ×9.3
    
    Args:
        phases: Liste de phases retournées par sequence_multi_event_timeline_v86()
        start_price: Prix EUR/USD de départ
        base_time: Timestamp de référence
        duration_minutes: Durée totale à simuler
    """
    
    if not PRICE_CURVE_AVAILABLE:
        st.error("⚠️ Module price_curve_generator non disponible - impossible d'afficher le graphique")
        st.info("Vérifiez que le fichier fx_impact_app/src/price_curve_generator.py existe et contient les fonctions requises.")
        return
    
    if not phases:
        st.warning("Aucune phase à afficher")
        return
    
    # Afficher section graphique
    st.subheader("📈 Graphique de Prix avec Pullback")
    
    # Calculer statistiques pullback
    total_pullback = sum(p.get('pullback_pips', 0) for p in phases)
    phases_with_pullback = sum(1 for p in phases if p.get('pullback_pips', 0) > 0)
    
    # Colonnes pour stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🔄 Durée Pullback",
            value=f"{sum(p.get('minutes_since_prev_phase', 0) for p in phases if p.get('pullback_pips', 0) > 0):.0f} min"
        )
    
    with col2:
        st.metric(
            label="📉 Amplitude Pullback",
            value=f"{total_pullback:.1f} pips",
            delta=f"↓ {phases_with_pullback} phase{'s' if phases_with_pullback > 1 else ''}"
        )
    
    with col3:
        total_impact = sum(abs(p.get('impact_combined', 0)) for p in phases)
        st.metric(
            label="📈 Impact Total",
            value=f"+{total_impact:.1f} pips",
            help="Somme des impacts de toutes les phases (pic max)"
        )
    
    # Options graphique
    with st.expander("⚙️ Options du graphique", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            volatility = st.slider(
                "Volatilité simulée",
                min_value=0.1,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Contrôle la volatilité intra-minute des chandeliers"
            )
        with col_b:
            spread_pips = st.number_input(
                "Spread bid/ask (pips)",
                min_value=0.0,
                max_value=5.0,
                value=1.0,
                step=0.5,
                help="Écart bid/ask à simuler"
            )
    
    # Normaliser base_time si nécessaire
    if isinstance(base_time, str):
        base_time = pd.to_datetime(base_time)
    
    try:
        # === DEBUG v8.6.6 : TRACER LES VALEURS AVANT GÉNÉRATION ===
        st.write("🔍 **DEBUG - Phases transmises au générateur :**")
        for phase in phases:
            st.write(f"Phase {phase['phase_num']}: impact_combined = {phase.get('impact_combined', 0):.1f} pips, "
                    f"pullback = {phase.get('pullback_pips', 0):.1f} pips")
        # === FIN DEBUG ===
        
        # Générer la courbe de prix minute par minute
        with st.spinner("Génération de la courbe de prix avec pullback..."):
            price_df = generate_candlestick_curve_from_phases(
                start_price=start_price,
                phases=phases,
                base_time=base_time,
                duration_minutes=duration_minutes,
                volatility_factor=volatility,
                spread_pips=spread_pips
            )
        
        # Créer le graphique avec zones de pullback marquées
        fig = create_sequential_phases_chart(
            price_df=price_df,
            phases=phases,
            start_price=start_price,
            title="📊 Évolution Prédite EUR/USD avec Pullback"
        )
        
        # Afficher le graphique
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiques du graphique
        with st.expander("📊 Statistiques du graphique", expanded=False):
            max_price = price_df['high'].max()
            min_price = price_df['low'].min()
            amplitude_pips = (max_price - min_price) * 10000
            
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("Prix départ", f"{start_price:.5f}")
            with col_stat2:
                st.metric("Prix max", f"{max_price:.5f}", delta=f"+{(max_price - start_price)*10000:.1f} pips")
            with col_stat3:
                st.metric("Prix min", f"{min_price:.5f}", delta=f"{(min_price - start_price)*10000:.1f} pips")
            with col_stat4:
                st.metric("Amplitude totale", f"{amplitude_pips:.1f} pips")
            
            # Tableau récapitulatif par phase
            st.write("**Détails par phase :**")
            phase_stats = []
            for phase in phases:
                phase_data = price_df[price_df['phase_num'] == phase['phase_num']]
                if len(phase_data) > 0:
                    phase_max = phase_data['high'].max()
                    phase_min = phase_data['low'].min()
                    phase_amplitude = (phase_max - phase_min) * 10000
                    
                    phase_stats.append({
                        'Phase': phase['phase_num'],
                        'Impact prédit (pips)': f"{phase.get('impact_combined', 0):.1f}",
                        'Amplitude observée (pips)': f"{phase_amplitude:.1f}",
                        'Pullback (pips)': f"{phase.get('pullback_pips', 0):.1f}",
                        'Prix max': f"{phase_max:.5f}",
                        'Prix min': f"{phase_min:.5f}"
                    })
            
            if phase_stats:
                st.dataframe(pd.DataFrame(phase_stats), use_container_width=True)
        
        # Téléchargement des données
        with st.expander("💾 Télécharger les données", expanded=False):
            csv = price_df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger courbe de prix (CSV)",
                data=csv,
                file_name=f"eurusd_prediction_pullback_{base_time.strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération du graphique : {str(e)}")
        st.exception(e)
        st.info("💡 Vérifiez que les phases contiennent les champs requis : impact_combined, pullback_pips, start_time, etc.")


def display_timeline_gantt_chart(phases: List[Dict[str, Any]]):
    """
    Afficher graphique Gantt de la timeline
    
    Args:
        phases: Liste de phases
    """
    st.subheader("📊 Graphique Timeline (Gantt)")
    
    try:
        fig = go.Figure()
        
        # Ajouter une barre pour chaque phase
        for phase in phases:
            # Couleur selon direction
            if phase['direction'] == 'UP':
                color = '#28a745'  # Vert
            else:
                color = '#dc3545'  # Rouge
            
            # Opacité selon statut
            opacity = 0.6 if False else 0.9
            
            # Text sur barre
            text_on_bar = f"{' + '.join([e['family'] for e in phase['events']])}<br>{phase.get('ttr_predicted', phase.get('duration_minutes', 30)):.0f} min"
            
            # Barre principale (durée totale)
            fig.add_trace(go.Bar(
                name=f"Phase {phase['phase_num']}",
                x=[phase['duration_minutes']],
                y=[f"Phase {phase['phase_num']}<br>{parse_timestamp_string(phase['start_time']).strftime('%H:%M')}"],
                orientation='h',
                marker=dict(
                    color=color, 
                    opacity=opacity,
                    line=dict(color='black', width=1) if False else dict(width=0)
                ),
                text=text_on_bar,
                textposition='inside',
                textfont=dict(color='white', size=10),
                hovertemplate=(
                    f"<b>{' + '.join([e['family'] for e in phase['events']])} ({phase['events'][0]['country'] if phase.get('events') else 'N/A'})</b><br>"
                    f"Heure: {parse_timestamp_string(phase['start_time']).strftime('%H:%M:%S')}<br>"
                    f"Direction: {phase['direction']}<br>"
                    f"Impact: {abs(phase.get('impact_combined', 0)):.1f} pips<br>"
                    f"Latence: {phase['latency_minutes']:.0f} min<br>"
                    f"TTR réel: {phase.get('ttr_predicted', phase.get('duration_minutes', 30)):.0f} min<br>"
                    f"Durée: {phase['duration_minutes']:.0f} min<br>"
                    f"Statut: {'Interrompue 🟡' if False else 'Complète 🟢'}"
                    "<extra></extra>"
                )
            ))
        
        # Layout
        fig.update_layout(
            title={
                'text': "Timeline Séquentielle Multi-Événements",
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Durée (minutes)",
            yaxis_title="Phases",
            showlegend=False,
            height=max(300, len(phases) * 80),
            barmode='overlay',
            plot_bgcolor='rgba(240,240,240,0.5)',
            hovermode='closest'
        )
        
        # Ajouter grille
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=False)
        
        st.plotly_chart(fig, width='stretch', key="timeline_gantt_chart")
        
    except Exception as e:
        st.error(f"Erreur lors de la création du graphique: {e}")
        st.exception(e)


def display_backtest_comparison(
    phases: List[Dict[str, Any]],
    phase_errors: List[Dict[str, Any]]
):
    """
    Afficher comparaison backtesting prédictions vs réalité
    
    Args:
        phases: Liste de phases prédites
        phase_errors: Liste d'erreurs calculées par backtesting
    """
    st.subheader("🎯 Backtesting : Prédit vs Réel")
    
    # Métriques globales
    from sequence_multi_event_timeline import calculate_sequential_mae
    mae_results = calculate_sequential_mae(phase_errors)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "MAE TTR",
            f"{mae_results['mae_ttr']:.1f} min",
            help="Mean Absolute Error sur Time-To-Reversal"
        )
    
    with col2:
        st.metric(
            "MAE Impact",
            f"{mae_results['mae_impact']:.1f} pips",
            help="Mean Absolute Error sur l'impact"
        )
    
    with col3:
        st.metric(
            "Précision Direction",
            f"{mae_results['accuracy_direction']:.0f}%",
            help="Pourcentage de directions correctement prédites"
        )
    
    # Comparaison interrompu vs complet
    if mae_results.get('n_interrupted', 0) > 0:
        st.markdown("**📊 Comparaison Phases Interrompues vs Complètes :**")
        
        comp_col1, comp_col2 = st.columns(2)
        
        with comp_col1:
            st.metric(
                f"MAE TTR Interrompues ({mae_results['n_interrupted']})",
                f"{mae_results['mae_ttr_interrupted']:.1f} min"
            )
        
        with comp_col2:
            st.metric(
                f"MAE TTR Complètes ({mae_results['n_complete']})",
                f"{mae_results['mae_ttr_complete']:.1f} min"
            )
    
    st.markdown("---")
    
    # Graphique comparaison
    fig = go.Figure()
    
    # Barres prédites
    fig.add_trace(go.Bar(
        name='TTR Prédit',
        x=[f"Phase {e['phase_num']}" for e in phase_errors],
        y=[e['predicted_ttr'] for e in phase_errors],
        marker_color='lightblue',
        text=[f"{e['predicted_ttr']:.1f}" for e in phase_errors],
        textposition='auto'
    ))
    
    # Barres réelles
    fig.add_trace(go.Bar(
        name='TTR Réel',
        x=[f"Phase {e['phase_num']}" for e in phase_errors],
        y=[e['real_ttr'] for e in phase_errors],
        marker_color='darkblue',
        text=[f"{e['real_ttr']:.1f}" for e in phase_errors],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Comparaison TTR Prédit vs Réel par Phase",
        xaxis_title="Phase",
        yaxis_title="TTR (minutes)",
        barmode='group',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, width='stretch', key="backtest_comparison_chart")
    
    # Tableau détaillé
    st.markdown("**📋 Détails par Phase :**")
    
    df_errors = pd.DataFrame(phase_errors)
    df_errors['Direction Correcte'] = df_errors['direction_correct'].apply(
        lambda x: '✅' if x else '❌'
    )
    
    # Formater colonnes
    df_display = df_errors[[
        'phase_num', 'event', 'predicted_ttr', 'real_ttr', 'ttr_error',
        'predicted_impact', 'real_impact', 'impact_error', 'Direction Correcte'
    ]].copy()
    
    df_display.columns = [
        'Phase', 'Événement', 'TTR Prédit', 'TTR Réel', 'Erreur TTR',
        'Impact Prédit', 'Impact Réel', 'Erreur Impact', 'Direction OK'
    ]
    
    # Arrondir
    for col in ['TTR Prédit', 'TTR Réel', 'Erreur TTR']:
        df_display[col] = df_display[col].round(1)
    
    for col in ['Impact Prédit', 'Impact Réel', 'Erreur Impact']:
        df_display[col] = df_display[col].round(1)
    
    st.dataframe(df_display, width='stretch')


# ============================================================================
# FONCTIONS HELPER (si imports échouent)
# ============================================================================

def calculate_sequential_metrics_fallback(phases):
    """Fallback si import échoue"""
    if not phases:
        return {}
    
    total_duration = sum(p['duration_minutes'] for p in phases)
    avg_ttr = sum(p.get('ttr_predicted', p.get('duration_minutes', 30)) for p in phases) / len(phases)
    interrupted_count = sum(1 for p in phases if False)
    total_impact = sum(p.get('impact_combined', 0) for p in phases)
    
    if abs(total_impact) < 5:
        net_direction = 'NEUTRAL'
    elif total_impact > 0:
        net_direction = 'UP'
    else:
        net_direction = 'DOWN'
    
    return {
        'total_phases': len(phases),
        'total_duration': total_duration,
        'avg_ttr': avg_ttr,
        'interrupted_count': interrupted_count,
        'interrupted_pct': (interrupted_count / len(phases)) * 100,
        'total_impact': total_impact,
        'net_direction': net_direction,
        'first_event_time': phases[0]['start_time'],
        'last_event_time': phases[-1].get('predicted_end', '')
    }


def phases_to_dataframe_fallback(phases):
    """Fallback si import échoue"""
    df_data = []
    
    for phase in phases:
        df_data.append({
            'Phase': phase['phase_num'],
            'Événement': ' + '.join([e['family'] for e in phase['events']]),
            'Pays': phase['events'][0]['country'] if phase.get('events') else 'N/A',
            'Heure': parse_timestamp_string(phase['start_time']).strftime('%H:%M'),
            'Direction': phase['direction'],
            'Impact (pips)': f"{abs(phase.get('impact_combined', 0)):.1f}",
            'Latence (min)': f"{phase['latency_minutes']:.0f}",
            'TTR théo. (min)': f"{phase.get('ttr_predicted', 30):.0f}",
            'TTR réel (min)': f"{phase.get('ttr_predicted', phase.get('duration_minutes', 30)):.0f}",
            'Écart (min)': f"{phase.get('ttr_predicted', 30) - phase.get('ttr_predicted', phase.get('duration_minutes', 30)):.0f}",
            'Durée (min)': f"{phase['duration_minutes']:.0f}",
            'Statut': '🟡 Interrompue' if False else '🟢 Complète'
        })
    
    return pd.DataFrame(df_data)


# Utiliser fallback si imports ont échoué
try:
    calculate_sequential_metrics
    phases_to_dataframe
except NameError:
    calculate_sequential_metrics = calculate_sequential_metrics_fallback
    phases_to_dataframe = phases_to_dataframe_fallback


if __name__ == "__main__":
    print("=" * 70)
    print("COMPOSANT UI STREAMLIT POUR TIMELINE SÉQUENTIELLE")
    print("=" * 70)
    print()
    print("📁 À copier dans :")
    print("   fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py")
    print()
    print("✅ Fonctions disponibles:")
    print("   1. display_sequential_timeline(phases, show_details=True)")
    print("   2. display_phase_detail(phase, expanded=True)")
    print("   3. display_phase_summary_table(phases)")
    print("   4. display_timeline_gantt_chart(phases)")
    print("   5. display_backtest_comparison(phases, phase_errors)")
    print()
    print("📋 Utilisation dans Streamlit:")
    print("   from streamlit_sequential_ui import display_sequential_timeline")
    print("   display_sequential_timeline(phases)")
