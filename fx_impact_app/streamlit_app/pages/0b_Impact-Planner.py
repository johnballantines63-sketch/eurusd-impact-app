"""
Impact Planner - Interface Streamlit avec scoring complet
Version adaptée aux event_key réels de votre base
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ajouter les chemins nécessaires
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from config import get_db_path
from forecaster_mvp import ForecastEngine
from scoring_engine import ScoringEngine
from event_families import FAMILY_PATTERNS, FAMILY_IMPORTANCE, FAMILY_DESCRIPTIONS

# Configuration page
st.set_page_config(
    page_title="Impact Planner",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Impact Planner - Sélection & Scoring")
st.markdown("Sélectionnez les événements à trader selon leur score d'impact")

# Initialisation
@st.cache_resource
def init_engines():
    forecast_engine = ForecastEngine(get_db_path())
    scoring_engine = ScoringEngine()
    return forecast_engine, scoring_engine

forecast_engine, scoring_engine = init_engines()

# === SIDEBAR ===
st.sidebar.header("🎯 Filtres de Sélection")
# Période
st.sidebar.subheader("📅 Période")
col1, col2 = st.sidebar.columns(2)
with col1:
    date_from = st.date_input("De", datetime.now().date())
with col2:
    date_to = st.date_input("À", datetime.now().date() + timedelta(days=7))
# Pays
st.sidebar.subheader("🌍 Pays")
countries = st.sidebar.multiselect(
    "Sélectionner",
    options=['US', 'EU', 'GB', 'JP', 'CH'],
    default=['US']
)

# Familles d'événements
st.sidebar.subheader("📊 Familles d'événements")

families_selected = st.sidebar.multiselect(
    "Familles à analyser",
    options=list(FAMILY_PATTERNS.keys()),
    default=['NFP', 'CPI', 'Unemployment'],
    format_func=lambda x: f"{x} - {FAMILY_DESCRIPTIONS.get(x, '')}"
)

# Horizon
st.sidebar.subheader("⏱️ Horizon d'analyse")
horizon_minutes = st.sidebar.selectbox(
    "Minutes post-événement",
    options=[15, 30, 60, 120],
    index=1
)

hist_years = st.sidebar.slider("Années d'historique", 1, 5, 3)

# Filtres avancés
st.sidebar.subheader("🔍 Filtres Avancés")

with st.sidebar.expander("Impact (MFE P80)"):
    impact_min, impact_max = st.slider("Pips", 0, 100, (10, 100), 5)

with st.sidebar.expander("Latence"):
    latency_min, latency_max = st.slider("Minutes", 0, 60, (0, 30), 5, key='lat')

with st.sidebar.expander("TTR"):
    ttr_min, ttr_max = st.slider("Minutes", 0, 120, (15, 120), 5, key='ttr')

with st.sidebar.expander("Score"):
    score_min = st.slider("Score minimum", 0, 100, 40, 5)

calculate_btn = st.sidebar.button("🚀 Calculer les Scores", type="primary", use_container_width=True)

# === ZONE PRINCIPALE ===
if calculate_btn:
    if not families_selected:
        st.warning("⚠️ Sélectionnez au moins une famille")
    else:
        with st.spinner("🔄 Calcul en cours..."):
            
            # Calculer stats
            family_patterns = {f: FAMILY_PATTERNS[f] for f in families_selected}
            
            stats_results = forecast_engine.calculate_multiple_families(
                family_patterns,
                horizon_minutes=horizon_minutes,
                hist_years=hist_years,
                countries=countries
            )
            
            # Scoring
            scored_results = scoring_engine.batch_score(stats_results, FAMILY_IMPORTANCE)
            
            # Filtrage
            filtered_results = []
            for result in scored_results:
                metrics = result['metrics']
                
                if (impact_min <= metrics['mfe_p80'] <= impact_max and
                    latency_min <= metrics['latency_median'] <= latency_max and
                    ttr_min <= metrics['ttr_median'] <= ttr_max and
                    result['score'] >= score_min):
                    filtered_results.append(result)
            
            st.success(f"✅ {len(filtered_results)}/{len(scored_results)} événements correspondent")
            
            if len(filtered_results) == 0:
                st.info("💡 Élargissez les critères de filtrage")
            else:
                # Tableau
                display_data = []
                for result in filtered_results:
                    p_up = result['metrics']['p_up']
                    direction_emoji = "🔼" if p_up >= 0.7 else "🔽" if p_up <= 0.3 else "↔️"
                    
                    tradability = result['tradability']
                    badge = {"EXCELLENT": "🟢", "GOOD": "🟡", "FAIR": "🟠"}.get(tradability, "🔴")
                    
                    display_data.append({
                        '': badge,
                        'Famille': result['family'],
                        'Score': f"{result['score']:.0f}",
                        'Grade': result['grade'],
                        'Impact P80': f"{result['metrics']['mfe_p80']:.1f}",
                        'Latence': f"{result['metrics']['latency_median']:.0f}",
                        'TTR': f"{result['metrics']['ttr_median']:.0f}",
                        'Dir': direction_emoji,
                        'P(↑)': f"{result['metrics']['p_up']:.0%}",
                        'N': result['metrics']['n_events']
                    })
                
                df_display = pd.DataFrame(display_data)
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Score': st.column_config.ProgressColumn(
                            'Score',
                            format="%d",
                            min_value=0,
                            max_value=100
                        )
                    }
                )
                
                # Détails
                st.subheader("📊 Détails par Événement")
                
                for result in filtered_results:
                    with st.expander(f"{result['family']} - Score {result['score']:.0f}/100"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Score", f"{result['score']:.0f}/100", delta=result['grade'])
                            st.metric("Impact P80", f"{result['metrics']['mfe_p80']:.1f} pips")
                            st.metric("Échantillon", f"{result['metrics']['n_events']} events")
                        
                        with col2:
                            st.metric("Latence", f"{result['metrics']['latency_median']:.0f} min")
                            st.metric("TTR", f"{result['metrics']['ttr_median']:.0f} min")
                            st.metric("Tradabilité", result['tradability'])
                        
                        with col3:
                            st.metric("P(↑)", f"{result['metrics']['p_up']:.0%}")
                            st.metric("P(↓)", f"{(1-result['metrics']['p_up']):.0%}")
                        
                        # Composantes
                        st.markdown("**Composantes du Score:**")
                        comp_df = pd.DataFrame({
                            'Composante': ['Impact', 'Persistance', 'Fiabilité', 'Importance'],
                            'Score': [
                                result['components']['impact'],
                                result['components']['persistence'],
                                result['components']['reliability'],
                                result['components']['importance']
                            ]
                        })
                        st.bar_chart(comp_df.set_index('Composante'))
                
                # Export
                st.subheader("💾 Export")
                col1, col2 = st.columns(2)
                
                with col1:
                    export_data = scoring_engine.format_for_export(filtered_results)
                    df_export = pd.DataFrame(export_data)
                    csv = df_export.to_csv(index=False)
                    st.download_button(
                        "📥 Télécharger CSV",
                        csv,
                        f"impact_planner_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    import json
                    json_data = json.dumps(filtered_results, indent=2, default=str)
                    st.download_button(
                        "📥 Télécharger JSON",
                        json_data,
                        f"impact_planner_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        "application/json",
                        use_container_width=True
                    )

else:
    st.info("👈 Configurez vos filtres et cliquez sur **Calculer les Scores**")
    
    st.markdown("""
    ### 📖 Guide d'utilisation
    
    **Familles disponibles :**
    - **NFP** : Non-Farm Payrolls (36 événements)
    - **CPI** : Consumer Price Index (36 événements)
    - **Unemployment** : Taux de chômage (40 événements)
    - Et plus...
    
    **Interprétation des scores :**
    - 🟢 **EXCELLENT** (75+) : Tradabilité optimale
    - 🟡 **GOOD** (60-74) : Bon potentiel
    - 🟠 **FAIR** (45-59) : Tradable avec précaution
    - 🔴 **POOR** (<45) : Déconseillé
    
    **Note importante :**
    La latence et TTR à 30 min exactement indiquent qu'il manque des données prix 
    autour des événements. Utilisez `check_and_backfill_window.py` pour compléter.
    """)
