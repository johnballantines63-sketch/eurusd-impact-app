import sys
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH



src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Télécharger la base de données si nécessaire (une seule fois)
try:
    from download_database import download_database
    download_database()
except Exception as e:
    pass  # Déjà téléchargée ou erreur gérée ailleurs


"""
Planificateur Multi-Événements
Prédictions combinées pour événements simultanés avec latence et TTR
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
import duckdb
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from forecaster_mvp import ForecastEngine
from scoring_engine import ScoringEngine

st.set_page_config(page_title="Planificateur Multi-Événements", page_icon="📅", layout="wide")

st.title("📅 Planificateur Multi-Événements")
st.markdown("**Prédictions combinées avec Impact, Latence et TTR**")

# Session state
if 'events_loaded' not in st.session_state:
    st.session_state.events_loaded = False
if 'future_events' not in st.session_state:
    st.session_state.future_events = None
if 'selected_events' not in st.session_state:
    st.session_state.selected_events = set()




# Fonctions
def identify_family(event_key):
    for family_name, pattern in FAMILY_PATTERNS.items():
        clean_pattern = pattern.replace('(?i)', '')
        if re.search(clean_pattern, event_key, re.IGNORECASE):
            return family_name
    return None

def get_future_events(date_from, date_to, countries):
    conn = duckdb.connect(get_db_path())
    
    country_filter = "', '".join(countries)
    
    query = f"""
    SELECT 
        ts_utc, event_key, country, importance_n,
        actual, forecast, previous
    FROM events
    WHERE ts_utc >= '{date_from.strftime('%Y-%m-%d %H:%M')}'
      AND ts_utc <= '{date_to.strftime('%Y-%m-%d %H:%M')}'
      AND country IN ('{country_filter}')
    ORDER BY ts_utc
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    if len(df) > 0:
        df['family'] = df['event_key'].apply(identify_family)
        df = df[df['family'].notna()]
    
    return df

def predict_impact(family, surprise, years_back=3):
    """
    Prédit impact avec latence et TTR basés sur historique réel
    """
    engine = ForecastEngine(get_db_path())
    
    pattern = FAMILY_PATTERNS.get(family, '')
    if not pattern:
        engine.close()
        return None
    
    # Calculer stats historiques
    stats = engine.calculate_family_stats(
        pattern,
        horizon_minutes=30,
        hist_years=years_back,
        countries=None
    )
    
    engine.close()
    
    if stats['n_events'] == 0:
        return None
    
    # Impact basé sur MFE P80 historique
    base_impact = stats['mfe_p80']
    
    # Direction selon surprise
    direction = 1 if surprise > 0 else -1
    
    # Ajustement proportionnel à la surprise (calibration simplifiée)
    # Plus la surprise est forte, plus l'impact peut dépasser la moyenne
    surprise_factor = min(abs(surprise) / 50.0, 2.0)  # Cap à 2x
    adjusted_impact = base_impact * (0.5 + 0.5 * surprise_factor)
    
    return {
        'predicted_pips': adjusted_impact,
        'direction': direction,
        'latency_median': stats['latency_median'],
        'latency_p20': stats['latency_p20'],
        'latency_p80': stats['latency_p80'],
        'ttr_median': stats['ttr_median'],
        'ttr_p20': stats['ttr_p20'],
        'ttr_p80': stats['ttr_p80'],
        'n_similar': stats['n_events'],
        'mfe_p80': stats['mfe_p80']
    }

# === SIDEBAR ===
st.sidebar.header("⚙️ Configuration")

# Période
st.sidebar.subheader("📅 Période")

mode_date = st.sidebar.radio(
    "Mode de sélection",
    ["Date précise", "Période"],
    key='date_mode'
)

if mode_date == "Date précise":
    selected_date = st.sidebar.date_input(
        "Date",
        datetime.now().date() + timedelta(days=1),
        key='single_date'
    )
    date_from = datetime.combine(selected_date, datetime.min.time())
    date_to = datetime.combine(selected_date, datetime.max.time())
else:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        date_from_input = st.date_input("De", datetime.now().date(), key='date_from')
        date_from = datetime.combine(date_from_input, datetime.min.time())
    with col2:
        date_to_input = st.date_input("À", datetime.now().date() + timedelta(days=7), key='date_to')
        date_to = datetime.combine(date_to_input, datetime.max.time())

# Pays
countries = st.sidebar.multiselect(
    "Pays",
    ['US', 'EU', 'GB', 'JP', 'CH'],
    default=['US', 'EU'],
    key='countries_select'
)

# Charger événements
if st.sidebar.button("🔍 Charger Événements", type="primary", use_container_width=True):
    with st.spinner("Chargement..."):
        events = get_future_events(date_from, date_to, countries)
        
        if len(events) == 0:
            st.error("Aucun événement trouvé")
            st.stop()
        
        st.session_state.future_events = events
        st.session_state.events_loaded = True
        st.session_state.selected_events = set()

# === ZONE PRINCIPALE ===

if not st.session_state.events_loaded:
    st.info("👈 Configurez la période et cliquez sur Charger Événements")
    
    st.markdown("""
    ### 🎯 Fonctionnement
    
    Cette page analyse **plusieurs événements simultanés** avec :
    - **Impact** : Mouvement prix prédit (pips)
    - **Latence** : Temps avant réaction du marché
    - **TTR** : Time To Reversal (persistance du mouvement)
    
    **Méthode vectorielle** :
    ```
    Impact_combiné = Σ(impact_i × direction_i)
    Latence_combinée = moyenne pondérée
    TTR_combiné = minimum (sortie au premier retournement)
    ```
    
    ### 📊 Workflow
    
    1. Sélectionner période
    2. Charger événements
    3. Cocher événements à analyser
    4. Entrer valeurs hypothétiques
    5. Voir prédiction combinée complète
    """)

else:
    df = st.session_state.future_events
    
    st.success(f"✅ {len(df)} événements trouvés")
    
    # Grouper par date
    df['date'] = pd.to_datetime(df['ts_utc']).dt.date
    dates = sorted(df['date'].unique())
    
    # Sélection événements
    st.header("📋 Sélection des Événements")
    
    selected_indices = []
    
    for date in dates:
        st.subheader(f"📆 {date.strftime('%A %d/%m/%Y')}")
        
        day_events = df[df['date'] == date]
        
        for idx, event in day_events.iterrows():
            col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1])
            
            with col1:
                checked = st.checkbox(
                    "",
                    value=idx in st.session_state.selected_events,
                    key=f"check_{idx}"
                )
                if checked:
                    selected_indices.append(idx)
            
            with col2:
                time_str = pd.to_datetime(event['ts_utc']).strftime('%H:%M')
                st.write(f"**{time_str}** - {event['family']} ({event['country']})")
                st.caption(event['event_key'])
            
            with col3:
                st.write(f"Previous: {event['previous'] if pd.notna(event['previous']) else 'N/A'}")
            
            with col4:
                st.write(f"Forecast: {event['forecast'] if pd.notna(event['forecast']) else 'N/A'}")
    
    st.session_state.selected_events = set(selected_indices)
    
    # Configuration des événements sélectionnés
    if len(st.session_state.selected_events) > 0:
        st.divider()
        st.header("⚙️ Configuration des Événements Sélectionnés")
        
        predictions = []
        
        for idx in sorted(st.session_state.selected_events):
            event = df.loc[idx]
            
            with st.expander(f"📊 {event['family']} - {pd.to_datetime(event['ts_utc']).strftime('%H:%M')} ({event['country']})", expanded=True):
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    previous = st.number_input(
                        "Previous",
                        value=float(event['previous']) if pd.notna(event['previous']) else 0.0,
                        step=0.1,
                        format="%.2f",
                        key=f"prev_{idx}"
                    )
                
                with col2:
                    reference = st.number_input(
                        "Référence",
                        value=float(event['forecast']) if pd.notna(event['forecast']) else float(previous),
                        step=0.1,
                        format="%.2f",
                        key=f"ref_{idx}",
                        help="Forecast si dispo, sinon previous"
                    )
                
                with col3:
                    hypothetical = st.number_input(
                        "Actuel hypothétique",
                        value=float(reference),
                        step=0.1,
                        format="%.2f",
                        key=f"hyp_{idx}"
                    )
                
                with col4:
                    surprise = hypothetical - reference
                    st.metric("Surprise", f"{surprise:+.2f}")
                
                # Prédiction individuelle
                if surprise != 0:
                    pred = predict_impact(event['family'], surprise)
                    
                    if pred:
                        predictions.append({
                            'event': event,
                            'surprise': surprise,
                            **pred
                        })
                        
                        direction_text = "🔼 UP" if pred['direction'] > 0 else "🔽 DOWN"
                        
                        # Affichage enrichi
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.metric("Impact", f"{pred['predicted_pips']:.1f} pips", delta=direction_text)
                        
                        with col_b:
                            st.metric("Latence", f"{pred['latency_median']:.0f} min", 
                                     help=f"P20: {pred['latency_p20']:.0f} - P80: {pred['latency_p80']:.0f} min")
                        
                        with col_c:
                            st.metric("TTR", f"{pred['ttr_median']:.0f} min",
                                     help=f"P20: {pred['ttr_p20']:.0f} - P80: {pred['ttr_p80']:.0f} min")
                        
                        st.caption(f"Basé sur {pred['n_similar']} événements historiques (MFE P80: {pred['mfe_p80']:.1f} pips)")
        
        # Prédiction combinée
        if len(predictions) > 1:
            st.divider()
            st.header("🎲 Prédiction Combinée")
            
            # Analyser fenêtre temporelle
            timestamps = [pd.to_datetime(p['event']['ts_utc']) for p in predictions]
            time_span = (max(timestamps) - min(timestamps)).total_seconds() / 3600
            
            if time_span <= 2:
                st.info(f"⏱️ Événements dans fenêtre de {time_span:.1f}h → Interaction forte probable")
            else:
                st.warning(f"⚠️ Événements espacés de {time_span:.1f}h → Interaction modérée")
            
            # Calculs combinés
            vectorial_impact = sum(p['predicted_pips'] * p['direction'] for p in predictions)
            combined_direction = "🔼 HAUSSE" if vectorial_impact > 0 else "🔽 BAISSE"
            
            # Latence pondérée (par impact)
            total_impact = sum(p['predicted_pips'] for p in predictions)
            if total_impact > 0:
                weighted_latency = sum(p['latency_median'] * p['predicted_pips'] for p in predictions) / total_impact
            else:
                weighted_latency = np.mean([p['latency_median'] for p in predictions])
            
            # TTR = minimum (sortie au premier retournement)
            min_ttr = min(p['ttr_median'] for p in predictions)
            
            # Détails
            st.subheader("📊 Détails du Calcul")
            
            calc_data = []
            for p in predictions:
                calc_data.append({
                    'Événement': f"{p['event']['family']} ({p['event']['country']})",
                    'Surprise': f"{p['surprise']:+.2f}",
                    'Impact': f"{p['predicted_pips']:.1f}",
                    'Dir': "UP" if p['direction'] > 0 else "DN",
                    'Latence': f"{p['latency_median']:.0f}",
                    'TTR': f"{p['ttr_median']:.0f}",
                    'Contribution': f"{p['predicted_pips'] * p['direction']:+.1f}"
                })
            
            st.table(pd.DataFrame(calc_data))
            
            # Résultat final
            st.subheader("🎯 Impact Combiné Final")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Impact Total",
                    f"{abs(vectorial_impact):.1f} pips",
                    delta=combined_direction
                )
            
            with col2:
                st.metric(
                    "Latence Attendue",
                    f"{weighted_latency:.0f} min",
                    help="Moyenne pondérée par impact"
                )
            
            with col3:
                st.metric(
                    "TTR Combiné",
                    f"{min_ttr:.0f} min",
                    help="Premier retournement attendu"
                )
            
            with col4:
                # Cohérence
                directions = [p['direction'] for p in predictions]
                if len(set(directions)) == 1:
                    st.success("✅ AMPLIFICATION")
                    st.caption("Même direction")
                else:
                    st.warning("⚠️ ANTAGONISME")
                    st.caption("Directions opposées")
            
            # Fenêtre de trading suggérée
            st.divider()
            st.subheader("⏰ Fenêtre de Trading Suggérée")
            
            first_event_time = min(timestamps)
            
            entry_time = first_event_time - timedelta(minutes=2)
            reaction_time = first_event_time + timedelta(minutes=weighted_latency)
            exit_time = first_event_time + timedelta(minutes=min_ttr)
            
            col_t1, col_t2, col_t3 = st.columns(3)
            
            with col_t1:
                st.info(f"**Entrée** : {entry_time.strftime('%H:%M')}\n\n(2 min avant)")
            
            with col_t2:
                st.success(f"**Réaction attendue** : {reaction_time.strftime('%H:%M')}\n\n(+{weighted_latency:.0f} min)")
            
            with col_t3:
                st.warning(f"**Sortie** : {exit_time.strftime('%H:%M')}\n\n(TTR à {min_ttr:.0f} min)")
            
            # Scénarios
            st.divider()
            st.subheader("🎭 Scénarios Alternatifs")
            
            scenarios = []
            for delta in [-2, -1, 0, 1, 2]:
                scenario_predictions = []
                
                for p in predictions:
                    new_surprise = p['surprise'] + delta
                    new_pred = predict_impact(p['event']['family'], new_surprise)
                    
                    if new_pred:
                        scenario_predictions.append({
                            'impact': new_pred['predicted_pips'] * new_pred['direction'],
                            'latency': new_pred['latency_median'],
                            'ttr': new_pred['ttr_median']
                        })
                
                if scenario_predictions:
                    scenario_impact = sum(sp['impact'] for sp in scenario_predictions)
                    scenario_latency = np.mean([sp['latency'] for sp in scenario_predictions])
                    scenario_ttr = min(sp['ttr'] for sp in scenario_predictions)
                    
                    scenarios.append({
                        'Variation': f"{delta:+d}",
                        'Impact': f"{abs(scenario_impact):.1f} pips",
                        'Direction': "UP" if scenario_impact > 0 else "DOWN",
                        'Latence': f"{scenario_latency:.0f} min",
                        'TTR': f"{scenario_ttr:.0f} min"
                    })
            
            if scenarios:
                st.table(pd.DataFrame(scenarios))
            
            # Export
            st.divider()
            st.subheader("💾 Export")
            
            export_data = {
                'date': date_from.strftime('%Y-%m-%d'),
                'n_events': len(predictions),
                'combined_impact_pips': abs(vectorial_impact),
                'direction': 'UP' if vectorial_impact > 0 else 'DOWN',
                'latency_minutes': round(weighted_latency, 1),
                'ttr_minutes': round(min_ttr, 1),
                'entry_time': entry_time.strftime('%H:%M'),
                'exit_time': exit_time.strftime('%H:%M'),
                'events': [
                    {
                        'family': p['event']['family'],
                        'country': p['event']['country'],
                        'time': pd.to_datetime(p['event']['ts_utc']).strftime('%H:%M'),
                        'surprise': round(p['surprise'], 2),
                        'predicted_pips': round(p['predicted_pips'], 1),
                        'direction': 'UP' if p['direction'] > 0 else 'DOWN',
                        'latency': round(p['latency_median'], 0),
                        'ttr': round(p['ttr_median'], 0)
                    }
                    for p in predictions
                ]
            }
            
            import json
            json_export = json.dumps(export_data, indent=2)
            
            st.download_button(
                "📥 Télécharger Analyse Complète (JSON)",
                json_export,
                f"multi_events_{date_from.strftime('%Y%m%d')}.json",
                "application/json",
                use_container_width=True
            )
        
        elif len(predictions) == 1:
            st.info("ℹ️ Sélectionnez au moins 2 événements pour voir l'impact combiné")

