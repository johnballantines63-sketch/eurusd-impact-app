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
# from db_connection_manager import get_db_connection, execute_query  # Import obsolète retiré
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


# ═══════════════════════════════════════════════════════════
# PRÉ-CHARGEMENT DB (comme Planificateur) - Réponse instantanée
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def load_precomputed_stats_from_db():
    """Charge stats pré-calculées depuis DB (CACHE pour vitesse) + MÉTRIQUES EMPIRIQUES"""
    try:
        conn = duckdb.connect(get_db_path())
        
        # ✅ NOUVELLE QUERY : Charge TOUTES les métriques empiriques
        query = """
            SELECT 
                event_key, country, family,
                empirical_score, empirical_impact, 
                avg_movement_pips, reaction_rate, avg_latency_min,
                latency_median, latency_p20, latency_p80,
                ttr_median, ttr_p20, ttr_p80, 
                mfe_p80, n_events_latency
            FROM event_families 
            WHERE empirical_score IS NOT NULL
        """
        results = conn.execute(query).fetchall()
        conn.close()
        
        # ✅ Créer dict par (event_key, country)
        stats_dict = {}
        for row in results:
            key = (row[0], row[1])  # (event_key, country)
            stats_dict[key] = {
                'family': row[2],
                'empirical_score': row[3],
                'empirical_impact': row[4],
                'avg_movement_pips': row[5],
                'reaction_rate': row[6],
                'avg_latency_min': row[7],
                'latency_median': row[8],
                'latency_p20': row[9],
                'latency_p80': row[10],
                'ttr_median': row[11],
                'ttr_p20': row[12],
                'ttr_p80': row[13],
                'mfe_p80': row[14] if row[14] else 10.0,
                'n_events': row[15]
            }
        return stats_dict
    except Exception as e:
        st.error(f"❌ Erreur chargement DB: {e}")
        return {}

# Pré-charger au démarrage (UNE SEULE FOIS)
if 'preloaded' not in st.session_state:
    with st.spinner("⚡ Chargement stats DB..."):
        precomputed_stats = load_precomputed_stats_from_db()
        if precomputed_stats:
            st.session_state.precomputed_stats = precomputed_stats
            st.session_state.preloaded = True
            st.success(f"✅ {len(precomputed_stats)} familles en cache - Réponse instantanée !", icon="⚡")
        else:
            st.session_state.precomputed_stats = {}
            st.session_state.preloaded = True

forecast_engine, scoring_engine = init_engines()

# === SIDEBAR ===
st.sidebar.header("⚙️ Configuration")

# Classification
st.sidebar.subheader("📊 Classification")
classification_mode = st.sidebar.radio(
    "Source d'importance",
    ["📅 Calendrier (a priori)", "📊 Empirique (historique)"],
    index=0,
    help=(
        "📅 **Calendrier** : Importance théorique selon économistes\n\n"
        "📊 **Empirique** : Impact réel observé sur EUR/USD (3 ans)"
    )
)


# === Définir le mode de classification ===
use_empirical = classification_mode == "📊 Empirique (historique)"

st.sidebar.divider()


# Période
st.sidebar.subheader("📅 Période à analyser")

mode_date = st.sidebar.radio(
    "Mode de sélection",
    ["Date précise", "Période"],
    index=0,
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
    # Mode Période (code existant ci-dessous)
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

# Filtre Impact (adapté selon classification)
if use_empirical:
    impact_options = ['HIGH', 'MEDIUM', 'LOW', 'Unknown']
else:
    impact_options = ['High', 'Medium', 'Low']

selected_impacts = st.sidebar.multiselect(
    "Impact",
    impact_options,
    default=impact_options[:2]
)


min_importance = st.sidebar.select_slider(
    "Importance minimale",
    options=[1, 2, 3],
    value=2,
    format_func=lambda x: {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}[x]
)

min_score = st.sidebar.slider("Score minimum", 0, 100, 40, 5)

show_all = st.sidebar.checkbox("Afficher tous les événements (même sans historique)", value=True)

# Paramètres backtest
st.sidebar.subheader("📊 Paramètres d'analyse")
horizon_minutes = st.sidebar.selectbox("Horizon", [15, 30, 60], index=1)
hist_years = st.sidebar.slider("Historique (années)", 1, 5, 3)

# === ZONE PRINCIPALE ===

# Fonction pour récupérer les événements futurs
def get_future_events(date_from, date_to, countries, min_importance=1):
    """Récupère les événements futurs + ENRICHIT avec stats pré-chargées"""
    # Expansion : EU → tous pays eurozone
    expanded_countries = []
    eurozone_countries = ['EU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'PT', 'IE', 'GR']
    
    for country in countries:
        if country == 'EU':
            expanded_countries.extend(eurozone_countries)
        else:
            expanded_countries.append(country)
    
    # Dédupliquer
    expanded_countries = list(set(expanded_countries))
    
    # ✅ PAS de read_only
    conn = duckdb.connect(get_db_path())
    
    country_filter = "', '".join(expanded_countries)
    
    # ✅ Query SIMPLIFIÉE : uniquement events (stats viennent du cache)
    query = f"""
    SELECT 
        e.ts_utc, e.event_key, e.country, e.importance_n,
        e.actual, e.forecast, e.previous
    FROM events e
    WHERE e.ts_utc >= '{date_from.strftime('%Y-%m-%d %H:%M')}'
      AND e.ts_utc <= '{date_to.strftime('%Y-%m-%d %H:%M')}'
      AND e.country IN ('{country_filter}')
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    # ✅ TOUJOURS créer les colonnes (même si df vide)
    if len(df) == 0:
        # DataFrame vide avec colonnes nécessaires
        df = pd.DataFrame(columns=[
            'ts_utc', 'event_key', 'country', 'importance_n',
            'actual', 'forecast', 'previous',
            'empirical_score', 'empirical_impact', 'avg_movement_pips',
            'reaction_rate', 'family', 'impact_calendar', 'impact_empirical'
        ])
    else:
        # ✅ ENRICHIR avec stats pré-chargées
        precomputed = st.session_state.get('precomputed_stats', {})
        
        # Ajouter colonnes empiriques depuis cache
        # ⚡ MAPPING : EA (Eurozone) → EU pour compatibilité
        def get_stats_with_mapping(event_key, country):
            # Essayer d'abord avec le pays exact
            stats = precomputed.get((event_key, country), {})
            if not stats:
                # Si EU, essayer EA (pour ECB et autres événements Eurozone)
                if country == 'EU':
                    stats = precomputed.get((event_key, 'EA'), {})
                # Si EA, essayer EU
                elif country == 'EA':
                    stats = precomputed.get((event_key, 'EU'), {})
            return stats
        
        df['empirical_score'] = df.apply(
            lambda row: get_stats_with_mapping(row['event_key'], row['country']).get('empirical_score', None), 
            axis=1
        )
        df['empirical_impact'] = df.apply(
            lambda row: get_stats_with_mapping(row['event_key'], row['country']).get('empirical_impact', 'Unknown'), 
            axis=1
        )
        df['avg_movement_pips'] = df.apply(
            lambda row: get_stats_with_mapping(row['event_key'], row['country']).get('avg_movement_pips', 0), 
            axis=1
        )
        df['reaction_rate'] = df.apply(
            lambda row: get_stats_with_mapping(row['event_key'], row['country']).get('reaction_rate', 0), 
            axis=1
        )
        df['family'] = df.apply(
            lambda row: get_stats_with_mapping(row['event_key'], row['country']).get('family', identify_family(row['event_key'])), 
            axis=1
        )
        
        # Créer colonnes impact (importance inversée: 1=High, 3=Low)
        df['impact_calendar'] = df['importance_n'].map({1:'High', 2:'Medium', 3:'Low'})
        df['impact_empirical'] = df['empirical_impact'].fillna('Unknown')
    
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

        # === Switch Classification (Calendrier vs Empirique) ===
        if use_empirical:
            future_events['impact'] = future_events['impact_empirical'].fillna('Unknown')
        else:
            future_events['impact'] = future_events['impact_calendar']
        # === Fin Switch ===

        
        if len(future_events) == 0:
            st.warning(f"⚠️ Aucun événement trouvé dans la période sélectionnée")
            st.info("💡 Essayez d'élargir la période ou de réduire l'importance minimale")
            st.stop()
        
        st.success(f"✅ {len(future_events)} événements trouvés dans la période")
        
        # 2. Utiliser les stats pré-chargées au lieu de recalculer (⚡ RAPIDE)
        with st.spinner("📊 Calcul des scores historiques..."):
            
            # Identifier toutes les familles présentes
            future_events['family'] = future_events['event_key'].apply(identify_family)
            
            families_in_period = future_events['family'].dropna().unique()
            
            # ✅ UTILISER LE CACHE au lieu de recalculer
            precomputed = st.session_state.get('precomputed_stats', {})
            
            family_stats = {}
            family_scores = {}
            
            for family in families_in_period:
                # Chercher dans le cache par family
                family_entries = {k: v for k, v in precomputed.items() if v.get('family') == family}
                
                if family_entries:
                    # Prendre le premier (ils ont tous les mêmes stats par famille)
                    first_key = list(family_entries.keys())[0]
                    stats_cached = family_entries[first_key]
                    
                    # Convertir au format attendu par scoring_engine
                    stats = {
                        'n_events': stats_cached.get('n_events', 0),
                        'mfe_p80': stats_cached.get('mfe_p80', 0),
                        'latency_median': stats_cached.get('latency_median', 0),
                        'ttr_median': stats_cached.get('ttr_median', 0),
                        'p_up': 0.5,  # Default (pas stocké dans DB actuellement)
                        'p_down': 0.5  # ✅ AJOUTER pour scoring_engine
                    }
                    
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
            
            # ✅ UTILISER DIRECTEMENT empirical_score de la DB (via precomputed_stats)
            precomputed = st.session_state.get('precomputed_stats', {})
            event_key = event['event_key']
            country = event['country']
            
            # ⚡ MAPPING EA ↔ EU pour trouver les stats
            stats = precomputed.get((event_key, country), {})
            if not stats:
                if country == 'EU':
                    stats = precomputed.get((event_key, 'EA'), {})
                elif country == 'EA':
                    stats = precomputed.get((event_key, 'EU'), {})
            
            # ✅ Score prioritaire: empirical_score de la DB
            has_empirical = stats.get('empirical_score') is not None
            
            if has_empirical:
                # Utiliser le score empirique directement
                score = stats['empirical_score']
                
                # Calculer grade et tradability basés sur empirical_score
                if score >= 70:
                    grade = 'A'
                    tradability = 'EXCELLENT'
                elif score >= 60:
                    grade = 'B'
                    tradability = 'GOOD'
                elif score >= 50:
                    grade = 'C'
                    tradability = 'FAIR'
                else:
                    grade = 'D'
                    tradability = 'POOR'
                
                enriched_events.append({
                    'datetime': event['ts_utc'],
                    'date': event['ts_utc'].strftime('%d/%m/%Y'),
                    'time': event['ts_utc'].strftime('%H:%M'),
                    'event': event['event_key'],
                    'event_original_key': event['event_key'],
                    'family': family,
                    'country': event['country'],
                    'importance': event['importance_n'],
                    'empirical_impact': event.get('empirical_impact', 'Unknown'),
                    'score': score,  # ✅ Score empirique de la DB
                    'grade': grade,
                    'tradability': tradability,
                    'impact_p80': stats.get('mfe_p80') or 0,
                    'latency': stats.get('latency_median') or 0,
                    'ttr': stats.get('ttr_median') or 0,
                    'p_up': 0.5,  # Default (pas stocké actuellement)
                    'n_events': stats.get('n_events') or 0,
                    'forecast': event['forecast'],
                    'previous': event['previous']
                })
            
            elif family and family in family_scores:
                # Fallback: utiliser scoring_engine si pas de score empirique
                score_data = family_scores[family]
                stats_data = family_stats[family]
                
                enriched_events.append({
                    'datetime': event['ts_utc'],
                    'date': event['ts_utc'].strftime('%d/%m/%Y'),
                    'time': event['ts_utc'].strftime('%H:%M'),
                    'event': event['event_key'],
                    'event_original_key': event['event_key'],
                    'family': family,
                    'country': event['country'],
                    'importance': event['importance_n'],
                    'empirical_impact': event.get('empirical_impact', 'Unknown'),
                    'score': score_data['score'],
                    'grade': score_data['grade'],
                    'tradability': score_data['tradability'],
                    'impact_p80': stats_data.get('mfe_p80') or 0,
                    'latency': stats_data.get('latency_median') or 0,
                    'ttr': stats_data.get('ttr_median') or 0,
                    'p_up': stats_data.get('p_up') or 0.5,
                    'n_events': stats_data.get('n_events') or 0,
                    'forecast': event['forecast'],
                    'previous': event['previous']
                })
            elif show_all:
                enriched_events.append({
                    'datetime': event['ts_utc'],
                    'date': event['ts_utc'].strftime('%d/%m/%Y'),
                    'time': event['ts_utc'].strftime('%H:%M'),
                    'event': event['event_key'],
                    'event_original_key': event['event_key'],  # ✅ Pour lookup stats
                    'family': family or 'Autre',
                    'country': event['country'],
                    'importance': event['importance_n'],
                    'empirical_impact': event.get('empirical_impact', 'Unknown'),  # ✅ Ajouter
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
        # filtered_events = [e for e in enriched_events if e['score'] >= min_score]  # ❌ Filtre désactivé
        filtered_events = enriched_events  # ✅ Afficher TOUS
        
        if not filtered_events:
            st.warning(f"⚠️ Aucun événement avec score >= {min_score}")
            st.info(f"💡 {len(enriched_events)} événements disponibles avec score plus faible")
            filtered_events = enriched_events
        
        # Trier par score décroissant
        filtered_events.sort(key=lambda x: x['score'], reverse=True)
        
        # Filtrer par impact sélectionné (BUG 3 CORRIGÉ)
        # if selected_impacts:  # ❌ Filtre désactivé
            # if use_empirical:
                # # Mode Empirique : filtrer sur impact_empirical
                # filtered_events = [e for e in filtered_events 
                                  # if e.get('impact_empirical', 'Unknown') in selected_impacts]
            # else:
                # # Mode Calendrier : filtrer sur impact_calendar
                # filtered_events = [e for e in filtered_events 
                                  # if e.get('impact_calendar', 'Unknown') in selected_impacts]
            
            # print(f"   ✅ Filtrage par impact appliqué : {len(filtered_events)} événements restants")

        
        # === AFFICHAGE ===
        
        
        
        # Statistiques globales (adapté au mode Classification - BUG 4 CORRIGÉ)
        if use_empirical:
            high_count = len([e for e in enriched_events if e.get('impact_empirical') == 'HIGH'])
            medium_count = len([e for e in enriched_events if e.get('impact_empirical') == 'MEDIUM'])
        else:
            high_count = len([e for e in enriched_events if e.get('impact_calendar') == 'High'])
            medium_count = len([e for e in enriched_events if e.get('impact_calendar') == 'Medium'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Événements totaux", len(enriched_events))
            if use_empirical:
                st.caption(f"🔴 {high_count} HIGH | 🟡 {medium_count} MEDIUM")
            else:
                st.caption(f"🔴 {high_count} High | 🟡 {medium_count} Medium")
        
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
                p_up = event.get('p_up', 0.5)
                if p_up >= 0.7:
                    direction = "🔼 Hausse probable"
                elif p_up <= 0.3:
                    direction = "🔽 Baisse probable"
                else:
                    direction = "↔️ Direction incertaine"
                
                # ✅ IMPORTANCE VÉRIFIÉE (empirique)
                # Utiliser empirical_impact si disponible, sinon calendrier
                if use_empirical:
                    # Mode Empirique : priorité aux données vérifiées
                    if event.get('empirical_impact') and event['empirical_impact'] != 'Unknown':
                        impact_display = event['empirical_impact']
                        if impact_display == 'HIGH':
                            imp_stars = "🔴🔴🔴"  # 3 rouge
                        elif impact_display == 'MEDIUM':
                            imp_stars = "🟡🟡"  # 2 jaune
                        else:  # LOW
                            imp_stars = "🟢"  # 1 vert
                    else:
                        # Pas de données historiques en mode Empirique
                        imp_stars = "⚪⚪⚪"  # 3 blancs = non vérifié
                else:
                    # Mode Calendrier : afficher importance ForexFactory
                    imp_n = event['importance']
                    if imp_n == 1:  # High
                        imp_stars = "🔴🔴🔴"
                    elif imp_n == 2:  # Medium
                        imp_stars = "🟡🟡"
                    else:  # 3 = Low
                        imp_stars = "🟢"
                
                with st.expander(f"{badge} **{event['time']}** | {imp_stars} | **{event['family']}** - {event['event']} ({event['country']}) | Score: {event['score']:.0f}/100"):
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**📊 Score & Performance**")
                        st.metric("Score Global", f"{event.get('score', 0):.0f}/100", delta=event.get('grade', 'N/A'))
                        st.metric("Tradabilité", event.get('tradability', 'N/A'))
                        st.metric("Historique", f"{event.get('n_events', 0)} événements")
                    
                    with col2:
                        st.markdown("**💥 Impact Attendu**")
                        st.metric("Impact P80", f"{event.get('impact_p80', 0):.1f} pips")
                        st.metric("Latence", f"{event.get('latency', 0):.0f} min")
                        st.metric("Persistance (TTR)", f"{event.get('ttr', 0):.0f} min")
                    
                    with col3:
                        st.markdown("**🎯 Direction & Données**")
                        st.metric("Direction", direction)
                        st.metric("Probabilité Hausse", f"{event.get('p_up', 0.5):.0%}")
                        if event.get('forecast') is not None:
                            st.metric("Consensus", f"{event['forecast']}")
                        if event.get('previous') is not None:
                            st.metric("Précédent", f"{event['previous']}")
                    
                    # ✅ NOUVELLE SECTION : Métriques Backtest Vérifiées
                    if use_empirical and event.get('empirical_impact') and event['empirical_impact'] != 'Unknown':
                        st.divider()
                        st.markdown("**📊 Métriques Backtest Vérifiées**")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Récupérer stats du cache avec mapping EA ↔ EU
                            precomputed = st.session_state.get('precomputed_stats', {})
                            event_key = event.get('event_original_key', event['event'])
                            country = event['country']
                            
                            # ⚡ MAPPING EA ↔ EU
                            stats = precomputed.get((event_key, country), {})
                            if not stats:
                                if country == 'EU':
                                    stats = precomputed.get((event_key, 'EA'), {})
                                elif country == 'EA':
                                    stats = precomputed.get((event_key, 'EU'), {})
                            
                            st.metric(
                                "🎯 Impact Vérifié", 
                                event.get('empirical_impact', 'N/A'),
                                help="Impact réel observé sur historique"
                            )
                            st.metric(
                                "📈 Mouvement Moyen", 
                                f"{stats.get('avg_movement_pips') or 0:.1f} pips",
                                help="Mouvement moyen observé historiquement"
                            )
                        
                        with col2:
                            st.metric(
                                "✅ Taux Réaction", 
                                f"{stats.get('reaction_rate') or 0:.0%}",
                                help="% d'événements ayant causé un mouvement > 5 pips"
                            )
                            st.metric(
                                "📊 Score Empirique", 
                                f"{stats.get('empirical_score') or 0:.0f}/100",
                                help="Score basé sur données historiques"
                            )
                        
                        with col3:
                            st.metric(
                                "⏱️ Latence Moyenne", 
                                f"{stats.get('avg_latency_min') or 0:.1f} min",
                                help="Temps moyen avant réaction du marché"
                            )
                            st.metric(
                                "📊 Événements Analysés", 
                                f"{stats.get('n_events') or 0}",
                                help="Nombre d'événements dans l'historique"
                            )
                    
                    # Fenêtre de trading suggérée
                    st.markdown("**⏰ Fenêtre de Trading Suggérée**")
                    event_time = datetime.strptime(f"{event['date']} {event['time']}", '%d/%m/%Y %H:%M')
                    window_start = event_time - timedelta(minutes=5)
                    window_end = event_time + timedelta(minutes=int(event.get('ttr', 0) or 30))
                    
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
                    watchlist += f"{e['date']} {e['time']} | {e['family']} ({e['country']}) | Score: {e.get('score', 0):.0f}\n"
                    watchlist += f"   Impact: {e.get('impact_p80', 0):.0f} pips | Direction: {e.get('p_up', 0.5):.0%} hausse\n\n"
                
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
