import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ajouter le chemin du module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_db_path
from src.forecaster_mvp import ForecastEngine
from src.event_families import FAMILY_PATTERNS, get_family_info

st.set_page_config(page_title="Analyseur Surprise", page_icon="🎯", layout="wide")

st.title("🎯 Analyseur d'Impact par Surprise")
st.markdown("**Prédiction d'impact basée sur l'écart actual vs forecast (ou previous)**")

# Initialiser le forecaster
@st.cache_resource
def get_forecaster():
    return ForecastEngine(get_db_path())

forecaster = get_forecaster()

# Tabs pour les deux modes
tab1, tab2 = st.tabs(["📊 Analyse avec Données Existantes", "✍️ Saisie Manuelle Forecast"])

# ============================================================================
# TAB 1 : Analyse avec données existantes (previous comme fallback)
# ============================================================================
with tab1:
    st.markdown("### Mode Automatique")
    st.info("📌 Utilise **forecast** si disponible, sinon **previous** comme référence.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sélection famille
        families = list(FAMILY_PATTERNS.keys())
        selected_family = st.selectbox(
            "Famille d'événement",
            families,
            index=families.index('CPI') if 'CPI' in families else 0,
            key="auto_family"
        )
        
        family_info = get_family_info(selected_family)
        st.caption(f"Importance: {family_info['importance']}/3 | Sensibilité: {family_info['sensitivity']}")
    
    with col2:
        # Pays
        countries = st.multiselect(
            "Pays",
            ['US', 'EU', 'GB', 'JP', 'AU', 'CA', 'CH', 'NZ'],
            default=['US'],
            key="auto_countries"
        )
    
    # Récupérer les événements récents - nouvelle approche sans connexion
    if countries:
        pattern = FAMILY_PATTERNS[selected_family]
        countries_str = "', '".join(countries)
        
        # Utiliser une nouvelle connexion à chaque fois, sans cache
        try:
            temp_conn = duckdb.connect(get_db_path())
            recent_events = temp_conn.execute(f"""
                SELECT 
                    ts_utc,
                    event_key,
                    country,
                    actual,
                    forecast,
                    previous,
                    unit
                FROM events
                WHERE event_key ~ '{pattern}'
                  AND country IN ('{countries_str}')
                  AND actual IS NOT NULL
                  AND ts_utc >= CURRENT_DATE - INTERVAL '6 months'
                ORDER BY ts_utc DESC
                LIMIT 20
            """).fetchdf()
            temp_conn.close()
        except Exception as e:
            st.error(f"Erreur lors de la récupération des événements : {e}")
            recent_events = pd.DataFrame()
    else:
        recent_events = pd.DataFrame()
    
    if len(recent_events) == 0:
        st.warning("Aucun événement trouvé avec ces critères")
    else:
        st.markdown(f"**{len(recent_events)} événements récents trouvés**")
        
        # Sélectionner un événement
        event_options = [
            f"{row['ts_utc'].strftime('%Y-%m-%d %H:%M')} | {row['event_key']} ({row['country']}) | Actual: {row['actual']}"
            for _, row in recent_events.iterrows()
        ]
        
        selected_idx = st.selectbox(
            "Événement à analyser",
            range(len(event_options)),
            format_func=lambda x: event_options[x],
            key="auto_event"
        )
        
        selected_event = recent_events.iloc[selected_idx]
        
        # Afficher détails
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Date", selected_event['ts_utc'].strftime('%Y-%m-%d %H:%M'))
            st.metric("Pays", selected_event['country'])
        
        with col2:
            st.metric("Actual", f"{selected_event['actual']}{selected_event['unit'] or ''}")
            
            # Déterminer référence (forecast ou previous)
            reference = selected_event['forecast']
            ref_type = "Forecast"
            
            if pd.isna(reference):
                reference = selected_event['previous']
                ref_type = "Previous (fallback)"
            
            st.metric(ref_type, f"{reference}{selected_event['unit'] or ''}" if not pd.isna(reference) else "N/A")
        
        with col3:
            if not pd.isna(reference):
                surprise = selected_event['actual'] - reference
                st.metric("Surprise", f"{surprise:+.2f}{selected_event['unit'] or ''}")
                
                # Calculer impact prédit
                stats = forecaster.calculate_family_stats(
                    pattern, 
                    horizon_minutes=30,
                    hist_years=1,
                    countries=countries 
                )
                
                if stats['n_events'] > 0:
                    # Impact basé sur MFE P80
                    predicted_impact = stats['mfe_p80']
                    
                    # Ajuster selon la surprise
                    if not pd.isna(selected_event['previous']) and selected_event['previous'] != 0:
                        surprise_ratio = abs(surprise) / abs(selected_event['previous'])
                        predicted_impact *= (1 + surprise_ratio)
                    
                    st.metric("Impact Prédit", f"{predicted_impact:.1f} pips")
            else:
                st.warning("Pas de référence (forecast ou previous)")
        
        # Afficher statistiques historiques
        if 'stats' in locals() and stats['n_events'] > 0:
            st.markdown("---")
            st.markdown("### 📈 Statistiques Historiques")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Événements", stats['n_events'])
            with col2:
                st.metric("MFE P80", f"{stats['mfe_p80']:.1f} pips")
            with col3:
                st.metric("Latence Médiane", f"{stats['latency_median']:.0f} min")
            with col4:
                st.metric("TTR Médian", f"{stats['ttr_median']:.0f} min")

# ============================================================================
# TAB 2 : Saisie manuelle du forecast
# ============================================================================
with tab2:
    st.markdown("### Saisie Manuelle du Forecast")
    st.info("✍️ Pour événements critiques : récupérez forecast depuis Investing.com et saisissez-le ici.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        event_date = st.date_input("Date événement", datetime.now() + timedelta(days=1))
        event_time = st.time_input("Heure (UTC)", datetime.now().replace(hour=14, minute=30).time())
        
        manual_family = st.selectbox(
            "Famille",
            families,
            index=families.index('CPI') if 'CPI' in families else 0,
            key="manual_family"
        )
        
        manual_country = st.selectbox(
            "Pays",
            ['US', 'EU', 'GB', 'JP', 'AU', 'CA', 'CH', 'NZ'],
            key="manual_country"
        )
    
    with col2:
        event_name = st.text_input("Nom événement", "CPI m/m")
        forecast_value = st.number_input("Forecast", value=0.3, step=0.1, format="%.2f")
        previous_value = st.number_input("Previous", value=0.2, step=0.1, format="%.2f")
        unit = st.text_input("Unité", "%")
    
    st.markdown("---")
    st.markdown("### 🎯 Simulation Impact")
    
    actual_scenarios = st.multiselect(
        "Scénarios Actual à tester",
        [
            f"{forecast_value - 0.2:.2f} (Très négatif)",
            f"{forecast_value - 0.1:.2f} (Négatif)",
            f"{forecast_value:.2f} (En ligne)",
            f"{forecast_value + 0.1:.2f} (Positif)",
            f"{forecast_value + 0.2:.2f} (Très positif)",
        ],
        default=[f"{forecast_value:.2f} (En ligne)", f"{forecast_value + 0.2:.2f} (Très positif)"]
    )
    
    if st.button("💾 Sauvegarder Forecast dans la Base", type="primary"):
        try:
            event_ts = datetime.combine(event_date, event_time)
            
            conn = duckdb.connect(get_db_path())
            existing = conn.execute("""
                SELECT COUNT(*) FROM events
                WHERE ts_utc = ? AND event_key = ? AND country = ?
            """, [event_ts, event_name, manual_country]).fetchone()[0]
            
            if existing > 0:
                conn.execute("""
                    UPDATE events
                    SET forecast = ?, previous = ?, unit = ?
                    WHERE ts_utc = ? AND event_key = ? AND country = ?
                """, [forecast_value, previous_value, unit, event_ts, event_name, manual_country])
                st.success(f"✅ Forecast mis à jour pour {event_name} du {event_ts}")
            else:
                conn.execute("""
                    INSERT INTO events (ts_utc, event_key, country, forecast, previous, unit, importance_n)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [event_ts, event_name, manual_country, forecast_value, previous_value, unit, 
                     get_family_info(manual_family)['importance']])
                st.success(f"✅ Nouvel événement créé : {event_name} du {event_ts}")
            
            conn.close()
            st.cache_data.clear()
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
    
    if actual_scenarios:
        st.markdown("---")
        
        pattern = FAMILY_PATTERNS[manual_family]
        stats = forecaster.calculate_family_stats(
            pattern,
            horizon_minutes=30,
            hist_years=1,
            countries=[manual_country]
        )
        
        if stats['n_events'] > 0:
            st.markdown(f"**Basé sur {stats['n_events']} événements historiques**")
            
            results = []
            for scenario in actual_scenarios:
                actual_val = float(scenario.split(' ')[0])
                surprise = actual_val - forecast_value
                
                impact = stats['mfe_p80']
                if previous_value != 0:
                    surprise_ratio = abs(surprise) / abs(previous_value)
                    impact *= (1 + surprise_ratio)
                
                direction = "📉 Baisse EUR/USD" if surprise > 0 else "📈 Hausse EUR/USD"
                
                results.append({
                    'Scénario': scenario,
                    'Surprise': f"{surprise:+.2f}{unit}",
                    'Impact Prédit': f"{impact:.1f} pips",
                    'Direction': direction,
                    'Latence': f"{stats['latency_median']:.0f} min",
                    'TTR': f"{stats['ttr_median']:.0f} min"
                })
            
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("Pas assez de données historiques")
