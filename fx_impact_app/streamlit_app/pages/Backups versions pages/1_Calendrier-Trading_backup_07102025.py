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
Calendrier Trading - Événements futurs avec scores
Affiche les événements à venir triés par score de tradabilité
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from config import get_db_path
from forecaster_mvp import ForecastEngine
from scoring_engine import ScoringEngine
from event_families import FAMILY_PATTERNS, FAMILY_IMPORTANCE, FAMILY_DESCRIPTIONS

st.set_page_config(page_title="Calendrier Trading", page_icon="📅", layout="wide")

st.title("📅 Calendrier Trading - Événements à Surveiller")
st.markdown("**Événements futurs classés par potentiel de trading**")

# Init
@st.cache_resource
def init_engines():
    return ForecastEngine(get_db_path()), ScoringEngine()

forecast_engine, scoring_engine = init_engines()

# === SIDEBAR ===
st.sidebar.header("⚙️ Configuration")

# Période
st.sidebar.subheader("📅 Période à analyser")
lookforward_days = st.sidebar.slider("Jours à venir", 1, 30, 7)
date_from = datetime.now()
date_to = datetime.now() + timedelta(days=lookforward_days)

st.sidebar.info(f"📆 Du {date_from.strftime('%d/%m/%Y %H:%M')} au {date_to.strftime('%d/%m/%Y')}")

# Filtres
st.sidebar.subheader("🎯 Filtres")

countries = st.sidebar.multiselect(
    "Pays",
    ['US', 'EU', 'GB', 'JP', 'CH'],
    default=['US', 'EU']
)

min_importance = st.sidebar.select_slider(
    "Importance minimale",
    options=[1, 2, 3],
    value=2,
    format_func=lambda x: {1: "🟢 Low", 2: "🟡 Medium", 3: "🔴 High"}[x]
)

min_score = st.sidebar.slider("Score minimum", 0, 100, 40, 5)

show_all = st.sidebar.checkbox("Afficher tous les événements (même sans historique)", value=False)

# Paramètres backtest
st.sidebar.subheader("📊 Paramètres d'analyse")
horizon_minutes = st.sidebar.selectbox("Horizon", [15, 30, 60], index=1)
hist_years = st.sidebar.slider("Historique (années)", 1, 5, 3)

# === ZONE PRINCIPALE ===

# Fonction pour récupérer les événements futurs
def get_future_events(date_from, date_to, countries, min_importance):
    """Récupère les événements dans la période future"""
    
    conn = duckdb.connect(get_db_path())
    
    country_filter = "', '".join(countries)
    
    query = f"""
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        forecast,
        previous
    FROM events
    WHERE ts_utc >= '{date_from.strftime('%Y-%m-%d %H:%M:%S')}'
      AND ts_utc <= '{date_to.strftime('%Y-%m-%d %H:%M:%S')}'
      AND country IN ('{country_filter}')
      AND importance_n >= {min_importance}
    ORDER BY ts_utc
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    return df

# Fonction pour identifier la famille d'un événement
def identify_family(event_key):
    """Identifie à quelle famille appartient un événement"""
    import re
    
    for family_name, pattern in FAMILY_PATTERNS.items():
        # Enlever le (?i) du pattern pour re.search
        clean_pattern = pattern.replace('(?i)', '')
        if re.search(clean_pattern, event_key, re.IGNORECASE):
            return family_name
    
    return None

# Bouton de calcul
if st.sidebar.button("🔍 Analyser la Période", type="primary", use_container_width=True):
    
    with st.spinner("🔄 Récupération des événements futurs..."):
        
        # 1. Récupérer événements futurs
        future_events = get_future_events(date_from, date_to, countries, min_importance)
        
        if len(future_events) == 0:
            st.warning(f"⚠️ Aucun événement trouvé dans la période sélectionnée")
            st.info("💡 Essayez d'élargir la période ou de réduire l'importance minimale")
            st.stop()
        
        st.success(f"✅ {len(future_events)} événements trouvés dans la période")
        
        # 2. Calculer les scores historiques pour chaque famille
        with st.spinner("📊 Calcul des scores historiques..."):
            
            # Identifier toutes les familles présentes
            future_events['family'] = future_events['event_key'].apply(identify_family)
            
            families_in_period = future_events['family'].dropna().unique()
            
            # Calculer stats pour ces familles
            family_stats = {}
            family_scores = {}
            
            for family in families_in_period:
                if family in FAMILY_PATTERNS:
                    stats = forecast_engine.calculate_family_stats(
                        FAMILY_PATTERNS[family],
                        horizon_minutes=horizon_minutes,
                        hist_years=hist_years,
                        countries=None  # Tous pays pour stats historiques
                    )
                    
                    if stats['n_events'] > 0 or show_all:
                        family_stats[family] = stats
                        score = scoring_engine.calculate_score(
                            stats, 
                            FAMILY_IMPORTANCE.get(family, 2)
                        )
                        family_scores[family] = score
        
        # 3. Enrichir les événements avec leurs scores
        enriched_events = []
        
        for _, event in future_events.iterrows():
            family = event['family']
            
            if family and family in family_scores:
                score_data = family_scores[family]
                stats_data = family_stats[family]
                
                enriched_events.append({
                    'datetime': event['ts_utc'],
                    'date': event['ts_utc'].strftime('%d/%m/%Y'),
                    'time': event['ts_utc'].strftime('%H:%M'),
                    'event': event['event_key'],
                    'family': family,
                    'country': event['country'],
                    'importance': event['importance_n'],
                    'score': score_data['score'],
                    'grade': score_data['grade'],
                    'tradability': score_data['tradability'],
                    'impact_p80': stats_data['mfe_p80'],
                    'latency': stats_data['latency_median'],
                    'ttr': stats_data['ttr_median'],
                    'p_up': stats_data['p_up'],
                    'n_events': stats_data['n_events'],
                    'forecast': event['forecast'],
                    'previous': event['previous']
                })
            elif show_all:
                enriched_events.append({
                    'datetime': event['ts_utc'],
                    'date': event['ts_utc'].strftime('%d/%m/%Y'),
                    'time': event['ts_utc'].strftime('%H:%M'),
                    'event': event['event_key'],
                    'family': family or 'Autre',
                    'country': event['country'],
                    'importance': event['importance_n'],
                    'score': 0,
                    'grade': 'N/A',
                    'tradability': 'N/A',
                    'impact_p80': 0,
                    'latency': 0,
                    'ttr': 0,
                    'p_up': 0,
                    'n_events': 0,
                    'forecast': event['forecast'],
                    'previous': event['previous']
                })
        
        if not enriched_events:
            st.warning("⚠️ Aucun événement avec historique trouvé")
            st.info("💡 Activez 'Afficher tous les événements' pour voir ceux sans historique")
            st.stop()
        
        # Filtrer par score minimum
        filtered_events = [e for e in enriched_events if e['score'] >= min_score]
        
        if not filtered_events:
            st.warning(f"⚠️ Aucun événement avec score >= {min_score}")
            st.info(f"💡 {len(enriched_events)} événements disponibles avec score plus faible")
            filtered_events = enriched_events
        
        # Trier par score décroissant
        filtered_events.sort(key=lambda x: x['score'], reverse=True)
        
        # === AFFICHAGE ===
        
        # Statistiques globales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Événements totaux", len(enriched_events))
        
        with col2:
            tradable = len([e for e in filtered_events if e['score'] >= 60])
            st.metric("✅ Tradables (>60)", tradable)
        
        with col3:
            avg_score = sum(e['score'] for e in filtered_events) / len(filtered_events) if filtered_events else 0
            st.metric("📊 Score moyen", f"{avg_score:.1f}")
        
        with col4:
            best = max(filtered_events, key=lambda x: x['score']) if filtered_events else None
            if best:
                st.metric("🏆 Meilleur", f"{best['family']} ({best['score']:.0f})")
        
        st.divider()
        
        # Calendrier détaillé
        st.subheader("📋 Calendrier des Événements")
        
        # Grouper par date
        events_by_date = {}
        for event in filtered_events:
            date_key = event['date']
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append(event)
        
        # Afficher par date
        for date_str in sorted(events_by_date.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y')):
            events_today = events_by_date[date_str]
            
            # Header de la date
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            day_name = date_obj.strftime('%A')
            
            st.markdown(f"### 📆 {day_name} {date_str}")
            
            # Tableau des événements du jour
            for event in sorted(events_today, key=lambda x: x['time']):
                
                # Badge tradability
                badge_map = {
                    'EXCELLENT': '🟢',
                    'GOOD': '🟡',
                    'FAIR': '🟠',
                    'POOR': '🔴',
                    'N/A': '⚪'
                }
                badge = badge_map.get(event['tradability'], '⚪')
                
                # Direction
                p_up = event['p_up']
                if p_up >= 0.7:
                    direction = "🔼 Hausse probable"
                elif p_up <= 0.3:
                    direction = "🔽 Baisse probable"
                else:
                    direction = "↔️ Direction incertaine"
                
                # Importance
                imp_stars = "🔴" * event['importance']
                
                with st.expander(f"{badge} **{event['time']}** | {imp_stars} | **{event['family']}** - {event['event']} ({event['country']}) | Score: {event['score']:.0f}/100"):
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**📊 Score & Performance**")
                        st.metric("Score Global", f"{event['score']:.0f}/100", delta=event['grade'])
                        st.metric("Tradabilité", event['tradability'])
                        st.metric("Historique", f"{event['n_events']} événements")
                    
                    with col2:
                        st.markdown("**💥 Impact Attendu**")
                        st.metric("Impact P80", f"{event['impact_p80']:.1f} pips")
                        st.metric("Latence", f"{event['latency']:.0f} min")
                        st.metric("Persistance (TTR)", f"{event['ttr']:.0f} min")
                    
                    with col3:
                        st.markdown("**🎯 Direction & Données**")
                        st.metric("Direction", direction)
                        st.metric("Probabilité Hausse", f"{event['p_up']:.0%}")
                        if event['forecast'] is not None:
                            st.metric("Consensus", f"{event['forecast']}")
                        if event['previous'] is not None:
                            st.metric("Précédent", f"{event['previous']}")
                    
                    # Fenêtre de trading suggérée
                    st.markdown("**⏰ Fenêtre de Trading Suggérée**")
                    event_time = datetime.strptime(f"{event['date']} {event['time']}", '%d/%m/%Y %H:%M')
                    window_start = event_time - timedelta(minutes=5)
                    window_end = event_time + timedelta(minutes=int(event['ttr']))
                    
                    st.info(f"🕐 Position: {window_start.strftime('%H:%M')} → 📊 Événement: {event['time']} → 🎯 Sortie attendue: ~{window_end.strftime('%H:%M')}")
                    
                    # Recommandation
                    if event['score'] >= 70:
                        st.success("✅ **RECOMMANDÉ** - Forte probabilité de mouvement exploitable")
                    elif event['score'] >= 50:
                        st.warning("⚠️ **À CONSIDÉRER** - Potentiel modéré, surveiller le contexte")
                    else:
                        st.error("❌ **PRUDENCE** - Historique peu favorable")
        
        # Export
        st.divider()
        st.subheader("💾 Export du Calendrier")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export CSV
            export_df = pd.DataFrame(filtered_events)
            csv = export_df.to_csv(index=False)
            st.download_button(
                "📥 Télécharger CSV",
                csv,
                f"calendrier_trading_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            # Export watchlist (top événements)
            top_events = [e for e in filtered_events if e['score'] >= 60]
            if top_events:
                watchlist = "WATCHLIST TRADING\n" + "="*50 + "\n\n"
                for e in top_events[:10]:  # Top 10
                    watchlist += f"{e['date']} {e['time']} | {e['family']} ({e['country']}) | Score: {e['score']:.0f}\n"
                    watchlist += f"   Impact: {e['impact_p80']:.0f} pips | Direction: {e['p_up']:.0%} hausse\n\n"
                
                st.download_button(
                    "📋 Watchlist (TXT)",
                    watchlist,
                    f"watchlist_{date_from.strftime('%Y%m%d')}.txt",
                    "text/plain",
                    use_container_width=True
                )

else:
    # État initial
    st.info("👈 Configurez la période et cliquez sur **Analyser la Période**")
    
    st.markdown("""
    ### 🎯 Utilisation
    
    Cette page vous permet de :
    
    1. **📅 Sélectionner une période future** (1-30 jours)
    2. **🔍 Identifier les événements à fort potentiel** dans cette période
    3. **📊 Voir leur score de tradabilité** basé sur l'historique
    4. **⏰ Obtenir les fenêtres de trading suggérées**
    5. **💾 Exporter une watchlist** pour votre préparation
    
    ### 💡 Interprétation
    
    - **Score 70+** : Événement à fort potentiel, à trader en priorité
    - **Score 50-69** : Potentiel modéré, surveiller le contexte
    - **Score <50** : Historique peu favorable, prudence
    
    ### ⚠️ Note
    
    Les scores sont basés sur l'analyse des **3 dernières années** d'historique.
    La latence/TTR à 30 min exactement indique qu'il manque des données prix.
    Utilisez `check_and_backfill_window.py` pour compléter les données autour des événements.
    """)
