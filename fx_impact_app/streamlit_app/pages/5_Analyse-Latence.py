"""
Page Streamlit : Analyse de Latence de Réaction du Marché
"""
import sys
from pathlib import Path

# Ajouter src au PYTHONPATH
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Télécharger la base de données si nécessaire
try:
    from download_database import download_database
    download_database()
except Exception as e:
    pass

import streamlit as st
import pandas as pd
import importlib
import latency_analyzer
importlib.reload(latency_analyzer)
from latency_analyzer import LatencyAnalyzer

st.set_page_config(page_title="Analyse Latence", page_icon="⏱️", layout="wide")

st.title("⏱️ Analyse de Latence de Réaction du Marché")
st.markdown("""
Analyse du **temps de réaction** du marché EUR/USD aux annonces économiques.
Comprendre combien de temps après l'annonce le marché commence à bouger et quand il atteint son pic.
""")

# Initialiser l'analyseur
analyzer = LatencyAnalyzer()

# Sidebar : Configuration
st.sidebar.header("⚙️ Configuration")
threshold_pips = st.sidebar.slider(
    "Seuil de réaction (pips)",
    min_value=3.0,
    max_value=15.0,
    value=5.0,
    step=1.0,
    help="Mouvement minimum pour considérer qu'il y a une réaction"
)

lookback_days = st.sidebar.select_slider(
    "Période d'analyse",
    options=[90, 180, 365, 730],
    value=365,
    format_func=lambda x: f"{x} jours ({x//365}an)" if x >= 365 else f"{x} jours"
)

# Tabs principales
tab1, tab2, tab3 = st.tabs([
    "📊 Vue d'ensemble",
    "🔍 Analyse par famille",
    "🔮 Prédiction"
])

# TAB 1: Vue d'ensemble toutes familles
with tab1:
    st.header("Résumé : Latences par Type d'Événement")
    
    with st.spinner("Calcul des latences pour toutes les familles..."):
        with analyzer:
            all_stats = analyzer.get_all_families_latency_summary(threshold_pips)
    
    if all_stats:
        # Créer DataFrame pour affichage
        data = []
        for stat in all_stats:
            family = stat['family'].upper()
            events = stat['events_with_reaction']
            
            latency = stat.get('initial_reaction', {})
            peak = stat.get('peak_timing', {})
            
            data.append({
                'Famille': family,
                'Événements': events,
                'Latence moy. (min)': latency.get('mean_minutes', '-'),
                'Latence médiane (min)': latency.get('median_minutes', '-'),
                'Min-Max (min)': f"{latency.get('min_minutes', '-')}-{latency.get('max_minutes', '-')}",
                'Peak moy. (min)': peak.get('mean_minutes', '-'),
                'Mouvement moy. (pips)': peak.get('mean_movement_pips', '-')
            })
        
        df = pd.DataFrame(data)
        
        # Affichage tableau avec style
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Latence moy. (min)": st.column_config.NumberColumn(
                    format="%.1f",
                    help="Temps moyen avant première réaction > seuil"
                ),
                "Peak moy. (min)": st.column_config.NumberColumn(
                    format="%.1f",
                    help="Temps moyen avant mouvement maximum"
                ),
                "Mouvement moy. (pips)": st.column_config.NumberColumn(
                    format="%.1f",
                    help="Amplitude moyenne du mouvement au peak"
                )
            }
        )
        
        # Insights clés
        st.subheader("💡 Insights Clés")
        
        col1, col2, col3 = st.columns(3)
        
        fastest = all_stats[0]
        slowest = all_stats[-1]
        
        with col1:
            st.metric(
                "Événement le plus rapide",
                fastest['family'].upper(),
                f"{fastest.get('initial_reaction', {}).get('mean_minutes', 0)} min"
            )
        
        with col2:
            avg_latency = sum(s.get('initial_reaction', {}).get('mean_minutes', 0) 
                            for s in all_stats) / len(all_stats)
            st.metric(
                "Latence moyenne globale",
                f"{avg_latency:.1f} min",
                help="Moyenne de toutes les familles"
            )
        
        with col3:
            avg_peak = sum(s.get('peak_timing', {}).get('mean_minutes', 0) 
                          for s in all_stats) / len(all_stats)
            st.metric(
                "Temps moyen vers le peak",
                f"{avg_peak:.1f} min",
                help="Fenêtre optimale de profit"
            )
        
        # Recommandations trading
        st.info(f"""
        **Recommandations Trading basées sur ces données :**
        
        - **Scalping rapide** : Privilégier {fastest['family'].upper()} (réaction en {fastest.get('initial_reaction', {}).get('mean_minutes', 0)} min)
        - **Window de profit** : La majorité des événements atteignent leur pic entre 15-25 minutes
        - **Entry timing** : Considérer un délai de {fastest.get('initial_reaction', {}).get('mean_minutes', 0)}-{slowest.get('initial_reaction', {}).get('mean_minutes', 0)} min selon le type d'événement
        """)
    else:
        st.warning("Aucune donnée disponible pour cette période")

# TAB 2: Analyse détaillée par famille
with tab2:
    st.header("Analyse Détaillée par Famille d'Événements")
    
    families = ['CPI', 'NFP', 'GDP', 'PMI', 'Unemployment', 'Retail', 
                'FOMC', 'Fed', 'Jobless', 'Inflation', 'Confidence']
    
    selected_family = st.selectbox(
        "Sélectionner une famille d'événements",
        families,
        help="Choisir le type d'événement à analyser en détail"
    )
    
    if st.button("Analyser", type="primary"):
        with st.spinner(f"Analyse des événements {selected_family}..."):
            with analyzer:
                stats = analyzer.calculate_family_latency_stats(
                    family_pattern=selected_family.lower(),
                    threshold_pips=threshold_pips,
                    lookback_days=lookback_days,
                    min_events=5
                )
        
        if "error" in stats:
            st.error(f"❌ {stats['error']}")
        else:
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Événements analysés",
                    stats['events_analyzed']
                )
            
            with col2:
                st.metric(
                    "Avec réaction détectée",
                    stats['events_with_reaction'],
                    f"{stats['events_with_reaction']/stats['events_analyzed']*100:.0f}%"
                )
            
            with col3:
                if 'initial_reaction' in stats:
                    st.metric(
                        "Latence moyenne",
                        f"{stats['initial_reaction']['mean_minutes']} min",
                        help=f"Médiane: {stats['initial_reaction']['median_minutes']} min"
                    )
            
            with col4:
                if 'peak_timing' in stats:
                    st.metric(
                        "Peak moyen",
                        f"{stats['peak_timing']['mean_minutes']} min",
                        f"{stats['peak_timing']['mean_movement_pips']} pips"
                    )
            
            # Distribution de la latence
            if 'initial_reaction' in stats:
                st.subheader("📊 Distribution de la Latence Initiale")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Statistiques**")
                    ir = stats['initial_reaction']
                    st.write(f"- Minimum : {ir['min_minutes']} min")
                    st.write(f"- Médiane : {ir['median_minutes']} min")
                    st.write(f"- Moyenne : {ir['mean_minutes']} min")
                    st.write(f"- Maximum : {ir['max_minutes']} min")
                
                with col2:
                    st.markdown("**Interprétation**")
                    mean_lat = ir['mean_minutes']
                    
                    if mean_lat < 5:
                        st.success("⚡ Réaction très rapide - Idéal pour scalping")
                    elif mean_lat < 10:
                        st.info("🚀 Réaction rapide - Bon pour day trading")
                    else:
                        st.warning("🐌 Réaction plus lente - Plus de temps pour analyser")
                
                # Timing du peak
                if 'peak_timing' in stats:
                    st.subheader("📈 Timing du Mouvement Maximum")
                    
                    pt = stats['peak_timing']
                    
                    st.write(f"""
                    Le pic de mouvement est atteint en moyenne **{pt['mean_minutes']} minutes** après l'annonce,
                    avec un mouvement moyen de **{pt['mean_movement_pips']} pips**.
                    
                    **Stratégie suggérée :**
                    - Entrée : {ir['mean_minutes']:.0f} minutes après l'annonce
                    - Take-profit : Environ {pt['mean_minutes']:.0f} minutes après l'annonce
                    - Fenêtre de trading : {pt['mean_minutes'] - ir['mean_minutes']:.0f} minutes
                    """)

# TAB 3: Prédiction pour événement futur
with tab3:
    st.header("🔮 Prédiction de Latence pour Événement Futur")
    
    st.markdown("""
    Estimez la latence attendue pour un événement à venir basé sur l'historique
    et la magnitude de surprise anticipée.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        event_key = st.text_input(
            "Nom de l'événement",
            placeholder="Ex: CPI m/m, Nonfarm Payrolls, GDP q/q",
            help="Le type d'événement pour lequel faire une prédiction"
        )
    
    with col2:
        surprise_pct = st.number_input(
            "Surprise anticipée (%)",
            min_value=0.0,
            max_value=5.0,
            value=0.5,
            step=0.1,
            help="Écart attendu entre forecast et actual en %"
        )
    
    if st.button("Prédire la Latence", type="primary"):
        if event_key:
            with st.spinner("Calcul de la prédiction..."):
                with analyzer:
                    prediction = analyzer.predict_latency_for_event(
                        event_key=event_key,
                        surprise_magnitude=surprise_pct,
                        threshold_pips=threshold_pips
                    )
            
            if "error" in prediction:
                st.error(f"❌ {prediction['error']}")
            else:
                st.success("✅ Prédiction calculée")
                
                # Affichage de la prédiction
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.subheader("Famille détectée")
                    st.write(f"**{prediction['family'].upper()}**")
                
                with col2:
                    st.subheader("Latence historique")
                    if 'base_prediction' in prediction and prediction['base_prediction']:
                        bp = prediction['base_prediction']
                        st.metric(
                            "Moyenne",
                            f"{bp.get('mean_minutes', 'N/A')} min",
                            help=f"Médiane: {bp.get('median_minutes', 'N/A')} min"
                        )
                
                with col3:
                    st.subheader("Latence prédite")
                    if 'adjusted_prediction' in prediction:
                        ap = prediction['adjusted_prediction']
                        st.metric(
                            "Ajustée",
                            f"{ap['latency_minutes']} min",
                            help=ap['note']
                        )
                
                # Peak attendu
                if 'peak_prediction' in prediction and prediction['peak_prediction']:
                    pp = prediction['peak_prediction']
                    
                    st.info(f"""
                    **Timing attendu :**
                    
                    - Première réaction : ~{prediction.get('adjusted_prediction', {}).get('latency_minutes', 'N/A')} min
                    - Peak attendu : ~{pp.get('mean_minutes', 'N/A')} min
                    - Mouvement attendu : ~{pp.get('mean_movement_pips', 'N/A')} pips
                    
                    *Plus la surprise est importante, plus la réaction est rapide.*
                    """)
        else:
            st.warning("Veuillez saisir un nom d'événement")

# Footer
st.divider()
st.caption(f"""
💡 **Note :** Toutes les analyses sont basées sur {lookback_days} jours de données historiques 
avec un seuil de réaction de {threshold_pips} pips.
""")
