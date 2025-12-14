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
Prédictions combinées pour événements simultanés avec latence, TTR et retracement
Version 8.4 : TTR réel calculé depuis les prix observés
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import duckdb
import re
import plotly.graph_objects as go
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from forecaster_mvp import ForecastEngine
from scoring_engine import ScoringEngine
from latency_analyzer import LatencyAnalyzer
from unified_chart import create_unified_prediction_chart

# === NOUVEAU : Timeline séquentielle v8.4 ===
import sys
from pathlib import Path

# Chemin vers components (pour streamlit_sequential_ui)
components_path = Path(__file__).parent.parent / "components"
if str(components_path) not in sys.path:
    sys.path.insert(0, str(components_path))

# Chemin vers src (pour sequence_multi_event_timeline - déjà ajouté normalement)
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from sequence_multi_event_timeline import sequence_multi_event_timeline, calculate_ttr_accuracy_stats
    from streamlit_sequential_ui import display_sequential_timeline
    SEQUENTIAL_MODE_AVAILABLE = True
except ImportError as e:
    SEQUENTIAL_MODE_AVAILABLE = False
    import traceback
    print(f"❌ Import séquentiel échoué: {e}")
    print(f"❌ Chemins sys.path: {sys.path[:3]}")
    print(traceback.format_exc())


st.set_page_config(page_title="Planificateur Multi-Événements", page_icon="📅", layout="wide")

# ═══════════════════════════════════════════════════════════════
# 🔍 DEBUG MODE SÉQUENTIEL (TEMPORAIRE)
# ═══════════════════════════════════════════════════════════════
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Debug Mode Séquentiel")
if SEQUENTIAL_MODE_AVAILABLE:
    st.sidebar.success(f"✅ AVAILABLE = True")
else:
    st.sidebar.error(f"❌ AVAILABLE = False")
st.sidebar.caption(f"Python: {sys.version.split()[0]}")
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# MIGRATION DB AUTOMATIQUE
# ═══════════════════════════════════════════════════════════════
try:
    import sys
    from pathlib import Path
    migrate_path = Path(__file__).parent.parent.parent.parent
    if str(migrate_path) not in sys.path:
        sys.path.insert(0, str(migrate_path))
    from migrate_db import migrate_database
    migrate_database()
except Exception as e:
    pass  # Ignore erreurs migration (DB peut être read-only sur cloud)


st.title("📅 Planificateur Multi-Événements")
st.markdown("**Prédictions combinées avec Impact, Latence, TTR, Retracement + Classification Empirique**")

# Session state pour caching
if 'events_loaded' not in st.session_state:
    st.session_state.events_loaded = False
if 'future_events' not in st.session_state:
    st.session_state.future_events = None
if 'selected_events' not in st.session_state:
    st.session_state.selected_events = set()
if 'family_stats_cache' not in st.session_state:
    st.session_state.family_stats_cache = {}
if 'backtest_cache' not in st.session_state:
    st.session_state.backtest_cache = {}


# Fonctions


# ═══════════════════════════════════════════════════════════════
# NOUVELLES FONCTIONS OPTIMISÉES v8.0
# ═══════════════════════════════════════════════════════════════


def group_events_by_time_window(events, max_gap_minutes=30):
    """
    Groupe les événements en clusters selon leur proximité temporelle
    
    Args:
        events: Liste de dict avec 'event_time'
        max_gap_minutes: Écart max entre deux événements d'un même cluster
    
    Returns:
        Liste de clusters, chaque cluster = {
            'window_start': datetime,
            'window_end': datetime,
            'events': [event1, event2, ...],
            'event_times': [time1, time2, ...]
        }
    """
    if not events:
        return []
    
    # Trier par temps
    sorted_events = sorted(events, key=lambda e: e['event_time'])
    
    clusters = []
    current_cluster = {
        'events': [sorted_events[0]],
        'event_times': [sorted_events[0]['event_time']]
    }
    
    for event in sorted_events[1:]:
        # Calculer écart avec dernier événement du cluster actuel
        last_time = current_cluster['event_times'][-1]
        gap = (event['event_time'] - last_time).total_seconds() / 60
        
        if gap <= max_gap_minutes:
            # Ajouter au cluster actuel
            current_cluster['events'].append(event)
            current_cluster['event_times'].append(event['event_time'])
        else:
            # Finaliser cluster actuel
            current_cluster['window_start'] = current_cluster['event_times'][0]
            current_cluster['window_end'] = current_cluster['event_times'][-1] + timedelta(minutes=30)
            clusters.append(current_cluster)
            
            # Démarrer nouveau cluster
            current_cluster = {
                'events': [event],
                'event_times': [event['event_time']]
            }
    
    # Finaliser dernier cluster
    current_cluster['window_start'] = current_cluster['event_times'][0]
    current_cluster['window_end'] = current_cluster['event_times'][-1] + timedelta(minutes=30)
    clusters.append(current_cluster)
    
    return clusters

def calculate_cluster_impact(cluster, predictions_dict):
    """
    Calcule l'impact cumulé d'un cluster d'événements
    
    Args:
        cluster: Dict du cluster (de group_events_by_time_window)
        predictions_dict: Dict {event_key: prediction}
    
    Returns:
        Dict avec impact cumulé, latence min, TTR max
    """
    cluster_impact = {
        'total_pips': 0,
        'min_latency': float('inf'),
        'max_ttr': 0,
        'events_count': len(cluster['events']),
        'window_start': cluster['window_start'],
        'window_end': cluster['window_end'],
        'events': []
    }
    
    for event in cluster['events']:
        event_key = f"{event['family']}_{event['event_time'].strftime('%Y%m%d_%H%M')}"
        pred = predictions_dict.get(event_key)
        
        if pred:
            impact = pred['predicted_pips'] * pred['direction']
            cluster_impact['total_pips'] += impact
            cluster_impact['min_latency'] = min(cluster_impact['min_latency'], pred['latency_median'])
            cluster_impact['max_ttr'] = max(cluster_impact['max_ttr'], pred['ttr_median'])
            cluster_impact['events'].append({
                'time': event['event_time'],
                'family': event['family'],
                'impact': impact,
                'prediction': pred
            })
    
    if cluster_impact['min_latency'] == float('inf'):
        cluster_impact['min_latency'] = 5
    
    return cluster_impact



@st.cache_data(ttl=3600)
def load_precomputed_stats_from_db():
    """Charge stats pré-calculées depuis DB"""
    try:
        conn = duckdb.connect(get_db_path())
        # Vérifier si colonnes latency existent
        schema = conn.execute("DESCRIBE event_families").fetchall()
        cols = [col[0] for col in schema]
        
        if 'latency_median' not in cols:
            conn.close()
            return {}  # Colonnes pas encore créées
        query = """
            SELECT DISTINCT family, latency_median, latency_p20, latency_p80,
                   ttr_median, ttr_p20, ttr_p80, mfe_p80, n_events_latency
            FROM event_families WHERE latency_median IS NOT NULL
        """
        results = conn.execute(query).fetchall()
        conn.close()
        stats_dict = {}
        for row in results:
            stats_dict[row[0]] = {
                'latency_median': row[1], 'latency_p20': row[2], 'latency_p80': row[3],
                'ttr_median': row[4], 'ttr_p20': row[5], 'ttr_p80': row[6],
                'mfe_p80': row[7] if row[7] else 10.0, 'n_events': row[8]
            }
        return stats_dict
    except:
        return {}

def predict_impact_fast(family, surprise, precomputed_stats, years_back=3):
    """Version ULTRA-RAPIDE"""
    # Normaliser le nom de famille (espaces → underscores)
    family_normalized = family.replace(' ', '_')
    if family_normalized in precomputed_stats:
        stats = precomputed_stats[family_normalized]
        mfe = stats['mfe_p80']
        impact_factor = min(2.0, 1.0 + (surprise / 100)) if surprise > 0.5 else 1.0
        impact = mfe * impact_factor
        direction = get_event_direction(family, surprise)
        return {
            'predicted_pips': impact, 'direction': direction,
            'latency_median': stats['latency_median'], 'latency_p20': stats['latency_p20'],
            'latency_p80': stats['latency_p80'], 'ttr_median': stats['ttr_median'],
            'ttr_p20': stats['ttr_p20'], 'ttr_p80': stats['ttr_p80'],
            'n_similar': stats['n_events'], 'mfe_p80': stats['mfe_p80'], 'source': 'precomputed_db'
        }
    else:
        result = predict_impact(family, surprise, years_back)
        if result:
            result['source'] = 'calculated'
        return result



# Dictionnaire de sentiment par famille d'événements
# Pour certains événements, une surprise positive est une MAUVAISE nouvelle pour USD
FAMILY_SENTIMENT = {
    # INVERSÉ : Surprise positive = BAD news = EUR/USD DOWN
    'Jobless_Claims': -1,      # Plus de chômeurs = BAD pour USD
    'Unemployment': -1,         # Plus de chômage = BAD pour USD
    'Inflation': -1,            # Plus d'inflation = Hawkish Fed = BAD pour EUR/USD
    'CPI': -1,                  # Plus d'inflation = Hawkish Fed = BAD pour EUR/USD
    
    # NORMAL : Surprise positive = GOOD news = EUR/USD UP
    'GDP': 1,                   # Plus de croissance = GOOD pour USD
    'Retail_Sales': 1,          # Plus de ventes = GOOD pour USD
    'NFP': 1,                   # Plus d'emplois = GOOD pour USD
    'Factory_Orders': 1,        # Plus de commandes = GOOD pour USD
    'Industrial_Production': 1, # Plus de production = GOOD pour USD
    'Building_Permits': 1,      # Plus de permis = GOOD pour USD
    'Durable_Goods': 1,         # Plus de biens durables = GOOD pour USD
    'Trade_Balance': 1,         # Meilleure balance = GOOD pour USD
    'PMI': 1,                   # Plus d'activité = GOOD pour USD
    'Consumer_Confidence': 1,   # Plus de confiance = GOOD pour USD
    'Wages': 1,                 # Plus de salaires = GOOD pour USD (simplifié)
    'Interest_Rate': 1,         # Hausse taux = GOOD pour USD (simplifié)
}

def get_event_direction(family, surprise):
    """
    Calcule la direction EUR/USD selon le sentiment de la famille
    
    LOGIQUE CORRIGÉE :
    
    Pour événements US (impact USD) :
    - Good news for USD → USD UP → EUR/USD DOWN (direction = -1)
    - Bad news for USD → USD DOWN → EUR/USD UP (direction = +1)
    
    Familles INVERSÉES (Jobless, Unemployment, Inflation, CPI) :
    - Surprise positive = BAD news for USD
    - Exemple : Jobless Claims +28 → Plus de chômeurs → USD DOWN → EUR/USD UP (+1)
    
    Familles NORMALES (GDP, NFP, Retail, etc) :
    - Surprise positive = GOOD news for USD
    - Exemple : NFP +100K → Plus d'emplois → USD UP → EUR/USD DOWN (-1)
    """
    family_normalized = family.replace(' ', '_')
    sentiment = FAMILY_SENTIMENT.get(family_normalized, 1)  # Default: normal
    
    # Déterminer si la surprise est bonne ou mauvaise pour USD
    if surprise > 0:
        # Surprise positive
        if sentiment == -1:
            # Famille inversée : surprise+ = BAD for USD = EUR/USD UP
            direction = 1
        else:
            # Famille normale : surprise+ = GOOD for USD = EUR/USD DOWN
            direction = -1
    else:
        # Surprise négative
        if sentiment == -1:
            # Famille inversée : surprise- = GOOD for USD = EUR/USD DOWN
            direction = -1
        else:
            # Famille normale : surprise- = BAD for USD = EUR/USD UP
            direction = 1
    
    return direction




@st.cache_data(ttl=3600)
def load_all_events_for_date(target_date, countries=['US', 'EU']):
    """
    Charge TOUS les événements d'une date (avec et sans famille)
    
    Returns:
        Dict avec 'mapped' (avec famille) et 'unmapped' (sans famille)
    """
    
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
    
    try:
        conn = duckdb.connect(get_db_path())
        
        # Convertir date en format compatible
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Événements AVEC famille (mappés)
        query_mapped = f"""
            SELECT DISTINCT
                e.ts_utc,
                e.event_key,
                e.country,
                e.importance_n,
                e.actual,
                e.previous,
                e.estimate,
                e.forecast,
                ef.family,
                ef.empirical_score
            FROM events e
            INNER JOIN event_families ef ON e.event_key = ef.event_key
            WHERE DATE(e.ts_utc) = '{date_str}'
              AND (e.country IN ({','.join([f"'{c}'" for c in expanded_countries])})
                   OR e.country IN ('DE', 'FR', 'IT', 'ES', 'GB'))
              AND ef.is_tradable = true
            ORDER BY e.ts_utc
        """
        
        mapped_events = conn.execute(query_mapped).fetchdf()
        
        # Événements SANS famille (non mappés)
        query_unmapped = f"""
            SELECT DISTINCT
                e.ts_utc,
                e.event_key,
                e.country,
                e.importance_n,
                e.actual,
                e.previous,
                e.estimate,
                e.forecast
            FROM events e
            LEFT JOIN event_families ef ON e.event_key = ef.event_key
            WHERE DATE(e.ts_utc) = '{date_str}'
              AND (e.country IN ({','.join([f"'{c}'" for c in expanded_countries])})
                   OR e.country IN ('DE', 'FR', 'IT', 'ES', 'GB'))
              AND ef.event_key IS NULL
              AND e.importance_n >= 1
            ORDER BY e.ts_utc
        """
        
        unmapped_events = conn.execute(query_unmapped).fetchdf()
        
        conn.close()
        
        return {
            'mapped': mapped_events,
            'unmapped': unmapped_events
        }
    except Exception as e:
        st.error(f"Erreur chargement événements: {e}")
        return {'mapped': pd.DataFrame(), 'unmapped': pd.DataFrame()}



def identify_family(event_key):
    for family_name, pattern in FAMILY_PATTERNS.items():
        clean_pattern = pattern.replace('(?i)', '')
        if re.search(clean_pattern, event_key, re.IGNORECASE):
            return family_name
    return None


def get_future_events(date_from, date_to, countries):
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
    
    conn = duckdb.connect(get_db_path())
    
    country_filter = "', '".join(expanded_countries)
    
    query = f"""
    SELECT 
        e.ts_utc, e.event_key, e.country, e.importance_n,
        e.actual, e.forecast, e.previous,
        ef.empirical_score, ef.empirical_impact, ef.impact_level,
        ef.avg_movement_pips, ef.avg_latency_min, ef.reaction_rate
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc >= '{date_from.strftime('%Y-%m-%d %H:%M')}'
      AND e.ts_utc <= '{date_to.strftime('%Y-%m-%d %H:%M')}'
      AND e.country IN ('{country_filter}')
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    if len(df) > 0:
        df['family'] = df['event_key'].apply(identify_family)
        df = df[df['family'].notna()]
    
    return df


def predict_impact(family, surprise, years_back=3):
    """
    Prédit impact avec latence et TTR basés sur historique réel (avec cache)
    ✅ CORRECTION: Utilise LatencyAnalyzer pour latences précises
    """
    # Vérifier cache
    cache_key = f"{family}_{years_back}"
    if cache_key in st.session_state.family_stats_cache:
        stats = st.session_state.family_stats_cache[cache_key]
    else:
        pattern = FAMILY_PATTERNS.get(family, '')
        if not pattern:
            # Pas de warning si appelé depuis pré-chargement
            if surprise != 0:
                st.warning(f"⚠️ Pattern non trouvé pour famille: {family}")
            return None
        
        try:
            # === CORRECTION : Utiliser LatencyAnalyzer pour latences ===
            analyzer = LatencyAnalyzer(get_db_path())
            
            # Calculer stats de latence avec LatencyAnalyzer (PRÉCIS)
            # ✅ CORRECTION: Bons paramètres selon latency_analyzer.py
            latency_stats = analyzer.calculate_family_latency_stats(
                family_pattern=pattern,
                threshold_pips=5.0,
                min_events=5,
                lookback_days=years_back * 365  # ✅ C'est lookback_days !
            )
            
            # ✅ Vérification robuste
            if not latency_stats or not isinstance(latency_stats, dict):
                analyzer.close()
                return None
            
            if latency_stats.get('events_analyzed', 0) == 0:
                analyzer.close()
                if surprise != 0:
                    st.warning(f"⚠️ Aucun événement historique trouvé pour {family}")
                return None
            
            # Vérifier structure initial_reaction
            if 'initial_reaction' not in latency_stats or not latency_stats['initial_reaction']:
                analyzer.close()
                return None
            
            analyzer.close()
            
            # === Utiliser ForecastEngine uniquement pour MFE (impact) ===
            engine = ForecastEngine(get_db_path())
            
            mfe_stats = engine.calculate_family_stats(
                pattern,
                horizon_minutes=60,
                hist_years=years_back,
                countries=None
            )
            
            engine.close()
            
            # Combiner les deux sources
            stats = {
                'n_events': latency_stats['events_analyzed'],
                
                # LATENCE depuis LatencyAnalyzer (CORRECT ✅)
                'latency_median': latency_stats['initial_reaction']['median_minutes'],
                'latency_p20': latency_stats['initial_reaction'].get('p20_minutes', 
                    latency_stats['initial_reaction']['median_minutes'] * 0.5),
                'latency_p80': latency_stats['initial_reaction'].get('p80_minutes', 
                    latency_stats['initial_reaction']['median_minutes'] * 1.5),
                
                # TTR = Latence × 2 (formule empirique optimale ✅)
                'ttr_median': latency_stats['initial_reaction']['median_minutes'] * 2,
                'ttr_p20': latency_stats['initial_reaction']['median_minutes'] * 1.5,
                'ttr_p80': latency_stats['initial_reaction']['median_minutes'] * 3,
                
                # MFE (impact) depuis ForecastEngine
                'mfe_p80': mfe_stats.get('mfe_p80', 10)
            }
            
        except KeyError as e:
            # Erreur structure de données
            if 'analyzer' in locals():
                analyzer.close()
            if 'engine' in locals():
                engine.close()
            if surprise != 0:
                st.error(f"❌ Erreur structure données pour {family}: clé manquante '{e}'")
            return None
        except ImportError as e:
            if surprise != 0:
                st.error(f"❌ Erreur import LatencyAnalyzer: {e}")
                st.info("💡 Vérifiez que latency_analyzer.py existe dans fx_impact_app/src/")
            return None
        except Exception as e:
            if 'analyzer' in locals():
                analyzer.close()
            if 'engine' in locals():
                engine.close()
            if surprise != 0:
                st.error(f"❌ Erreur predict_impact pour {family}: {e}")
            return None
        
        # Mettre en cache
        st.session_state.family_stats_cache[cache_key] = stats
    
    if stats['n_events'] == 0:
        return None
    
    # Impact basé sur MFE P80 historique
    base_impact = stats['mfe_p80']
    
    # Direction selon surprise
    direction = 1 if surprise > 0 else -1
    
    # Ajustement proportionnel à la surprise
    surprise_factor = min(abs(surprise) / 50.0, 2.0)
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


def calculate_fibonacci_levels(impact_pips, direction):
    """Calcule les niveaux de retracement Fibonacci"""
    levels = {
        '0%': 0,
        '23.6%': impact_pips * 0.236,
        '38.2%': impact_pips * 0.382,
        '50%': impact_pips * 0.5,
        '61.8%': impact_pips * 0.618,
        '78.6%': impact_pips * 0.786,
        '100%': impact_pips
    }
    
    if direction < 0:
        levels = {k: -v for k, v in levels.items()}
    
    return levels


def create_timeline_chart(predictions, weighted_latency, min_ttr):
    """Crée timeline visuelle interactive avec Plotly"""
    
    fig = go.Figure()
    
    # Référence T0 = premier événement
    first_event_time = min(pd.to_datetime(p['event']['ts_utc']) for p in predictions)
    
    colors = px.colors.qualitative.Set2
    
    # ═══════════════════════════════════════════════════════════
    # MODE D'ANALYSE : Individuel vs Fenêtres Temporelles
    # ═══════════════════════════════════════════════════════════
    
    st.subheader("⚙️ Mode d'Analyse")
    
    col_mode1, col_mode2 = st.columns([3, 1])
    
    with col_mode1:
        use_time_windows = st.checkbox(
            "🕐 Activer le mode Fenêtres Temporelles",
            value=True,
            help="Groupe les événements proches (< 30 min) pour analyser leur impact cumulé"
        )
    
    with col_mode2:
        if use_time_windows:
            window_gap = st.number_input(
                "Écart max (min)",
                min_value=10,
                max_value=60,
                value=30,
                step=5
            )
        else:
            window_gap = 30
    
    if use_time_windows:
        st.info(f"ℹ️ **Mode Fenêtres** : Événements < {window_gap} min groupés")
    else:
        st.info("ℹ️ **Mode Individuel** : Événements analysés isolément")
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════
    # AFFICHAGE FENÊTRES (si activé)
    # ═══════════════════════════════════════════════════════════
    
    if use_time_windows:
        from datetime import datetime, timedelta
        
        st.subheader("🕐 Fenêtres Temporelles")
        
        # Créer liste événements
        event_list = [{
            'event_time': pred['event']['ts_utc'], 
            'family': pred['event']['family']
        } for pred in predictions]
        
        # Grouper
        clusters = group_events_by_time_window(event_list, max_gap_minutes=window_gap)
        
        # Dict lookup
        pred_dict = {}
        for pred in predictions:
            key = f"{pred['event']['family']}_{pred['event']['ts_utc'].strftime('%Y%m%d_%H%M')}"
            pred_dict[key] = pred
        
        # Message
        if len(clusters) > 1:
            st.success(f"✅ {len(clusters)} fenêtres détectées")
        elif len(clusters) == 1 and len(clusters[0]['events']) > 1:
            st.success(f"✅ {len(clusters[0]['events'])} événements groupés")
        else:
            st.info("ℹ️ Événements espacés")
        
        # Afficher clusters
        for cluster_idx, cluster in enumerate(clusters):
            cluster_impact = calculate_cluster_impact(cluster, pred_dict)
            
            with st.expander(
                f"🕐 Fenêtre {cluster_idx + 1}: "
                f"{cluster['window_start'].strftime('%H:%M')} → "
                f"{cluster['window_end'].strftime('%H:%M')} "
                f"({cluster_impact['events_count']} evt)",
                expanded=True
            ):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    icon = "🔺" if cluster_impact['total_pips'] > 0 else "🔻"
                    st.metric("Impact Cumulé", f"{abs(cluster_impact['total_pips']):.1f} pips", delta=icon)
                
                with col2:
                    st.metric("Réaction", f"{cluster_impact['min_latency']:.0f} min")
                
                with col3:
                    st.metric("Durée", f"{cluster_impact['max_ttr']:.0f} min")
                
                with col4:
                    dur = (cluster['window_end'] - cluster['window_start']).total_seconds() / 60
                    st.metric("Fenêtre", f"{dur:.0f} min")
                
                st.markdown("**📋 Événements:**")
                for evt in cluster_impact['events']:
                    icon = "🔺" if evt['impact'] > 0 else "🔻"
                    st.caption(
                        f"⏰ {evt['time'].strftime('%H:%M')} - "
                        f"**{evt['family']}**: {icon} {abs(evt['impact']):.1f} pips"
                    )
        
        st.divider()
        st.subheader("📊 Détails Individuels")
    else:
        st.subheader("📊 Prédictions Individuelles")
    
    for i, pred in enumerate(predictions):
        event_time = pd.to_datetime(pred['event']['ts_utc'])
        time_offset = (event_time - first_event_time).total_seconds() / 60  # minutes
        
        family_name = f"{pred['event']['family']} ({pred['event']['country']})"
        color = colors[i % len(colors)]
        
        # Point événement
        fig.add_trace(go.Scatter(
            x=[time_offset],
            y=[i],
            mode='markers',
            name=family_name,
            marker=dict(size=15, color=color, symbol='diamond'),
            hovertemplate=f"<b>{family_name}</b><br>" +
                         f"T+{time_offset:.0f} min<br>" +
                         f"Impact: {pred['predicted_pips']:.1f} pips<br>" +
                         "<extra></extra>"
        ))
        
        # Fenêtre de réaction (latence)
        latency_start = time_offset
        latency_end = time_offset + pred['latency_median']
        
        fig.add_trace(go.Scatter(
            x=[latency_start, latency_end],
            y=[i, i],
            mode='lines',
            name=f"{family_name} - Latence",
            line=dict(color=color, width=3),
            showlegend=False,
            hovertemplate=f"Latence: {pred['latency_median']:.0f} min<extra></extra>"
        ))
        
        # Fenêtre de persistance (TTR)
        ttr_end = time_offset + pred['ttr_median']
        
        fig.add_trace(go.Scatter(
            x=[latency_end, ttr_end],
            y=[i, i],
            mode='lines',
            name=f"{family_name} - TTR",
            line=dict(color=color, width=3, dash='dash'),
            showlegend=False,
            hovertemplate=f"TTR: {pred['ttr_median']:.0f} min<extra></extra>"
        ))
    
    # Ligne verticale réaction attendue (moyenne pondérée)
    fig.add_vline(
        x=weighted_latency,
        line_dash="dot",
        line_color="green",
        annotation_text=f"Réaction attendue ({weighted_latency:.0f} min)",
        annotation_position="top"
    )
    
    # Ligne verticale sortie suggérée (min TTR)
    fig.add_vline(
        x=min_ttr,
        line_dash="dot",
        line_color="red",
        annotation_text=f"Sortie suggérée ({min_ttr:.0f} min)",
        annotation_position="top"
    )
    
    fig.update_layout(
        title="Timeline des Événements et Fenêtres de Trading",
        xaxis_title="Temps (minutes depuis premier événement)",
        yaxis_title="Événements",
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(predictions))),
            ticktext=[f"{p['event']['family']}" for p in predictions]
        ),
        height=400,
        hovermode='closest',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def detect_overlaps(predictions):
    """Détecte les chevauchements entre fenêtres d'événements"""
    overlaps = []
    
    for i, pred1 in enumerate(predictions):
        time1 = pd.to_datetime(pred1['event']['ts_utc'])
        end1 = time1 + timedelta(minutes=pred1['ttr_median'])
        
        for j, pred2 in enumerate(predictions[i+1:], start=i+1):
            time2 = pd.to_datetime(pred2['event']['ts_utc'])
            start2 = time2
            
            # Chevauchement si événement 2 démarre avant fin de TTR événement 1
            if start2 < end1:
                overlap_minutes = (end1 - start2).total_seconds() / 60
                overlaps.append({
                    'event1': f"{pred1['event']['family']} ({pred1['event']['country']})",
                    'event2': f"{pred2['event']['family']} ({pred2['event']['country']})",
                    'overlap_minutes': overlap_minutes,
                    'severity': 'HIGH' if overlap_minutes > 10 else 'MEDIUM'
                })
    
    return overlaps


def calculate_tradability_score(predictions, overlaps, time_span):
    """Calcule un score de tradabilité de 0-100 pour la session"""
    score = 50  # Base
    
    # Bonus : nombre d'événements
    if len(predictions) == 2:
        score += 10
    elif len(predictions) >= 3:
        score += 5
    
    # Bonus : cohérence directionnelle
    directions = [p['direction'] for p in predictions]
    if len(set(directions)) == 1:
        score += 20  # Amplification
    else:
        score -= 10  # Antagonisme
    
    # Bonus : impact total significatif
    total_impact = sum(abs(p['predicted_pips'] * p['direction']) for p in predictions)
    if total_impact > 20:
        score += 15
    elif total_impact > 10:
        score += 10
    
    # Malus : chevauchements
    high_overlaps = len([o for o in overlaps if o['severity'] == 'HIGH'])
    score -= high_overlaps * 10
    
    # Malus : événements trop espacés
    if time_span > 3:
        score -= 15
    
    # Bonus : fenêtre compacte
    if time_span < 1:
        score += 10
    
    return max(0, min(100, score))


def get_real_prices_batch(event_times, window_minutes=60):
    """Récupère les prix réels pour plusieurs événements en UNE SEULE query (OPTIMISÉ)"""
    conn = duckdb.connect(get_db_path())
    
    results = {}
    
    # Convertir tous les timestamps
    epochs = []
    for i, event_time in enumerate(event_times):
        if isinstance(event_time, str):
            event_time = pd.to_datetime(event_time)
        
        if hasattr(event_time, 'tz') and event_time.tz is not None:
            event_time = event_time.tz_convert('UTC').tz_localize(None)
        elif hasattr(event_time, 'tz_localize'):
            event_time = pd.Timestamp(event_time).tz_localize('UTC').tz_localize(None)
        else:
            event_time = pd.Timestamp(event_time)
        
        event_epoch = int(event_time.timestamp())
        end_epoch = event_epoch + (window_minutes * 60)
        epochs.append((i, event_epoch, end_epoch))
    
    # UNE SEULE query pour tous les événements
    if len(epochs) > 0:
        # Créer conditions OR pour tous les événements
        conditions = " OR ".join([f"(timestamp >= {e[1]} AND timestamp <= {e[2]})" for e in epochs])
        
        query = f"""
        SELECT timestamp, close
        FROM prices_1m
        WHERE {conditions}
        ORDER BY timestamp ASC
        """
        
        try:
            all_prices = conn.execute(query).fetchall()
            conn.close()
            
            # Dispatcher les prix vers chaque événement
            for i, event_epoch, end_epoch in epochs:
                event_prices = [(t, p) for t, p in all_prices if event_epoch <= t <= end_epoch]
                
                if len(event_prices) > 0:
                    times = [datetime.fromtimestamp(r[0]) for r in event_prices]
                    prices = [r[1] for r in event_prices]
                    results[i] = pd.DataFrame({'time': times, 'price': prices})
                else:
                    results[i] = None
        except Exception as e:
            print(f"Erreur get_real_prices_batch: {e}")
            conn.close()
            return {}
    else:
        conn.close()
    
    return results


def measure_real_impact(prices_df, threshold_pips=5.0):
    """Mesure l'impact réel du marché à partir des prix"""
    if prices_df is None or len(prices_df) == 0:
        return None
    
    ref_price = prices_df.iloc[0]['price']
    
    # Trouver mouvement max et latence
    max_movement = 0
    latency_minutes = None
    peak_time = None
    direction = 0
    
    for i, row in prices_df.iterrows():
        movement_pips = (row['price'] - ref_price) * 10000
        
        if abs(movement_pips) > abs(max_movement):
            max_movement = movement_pips
            peak_time = i
        
        if latency_minutes is None and abs(movement_pips) >= threshold_pips:
            latency_minutes = i
            direction = 1 if movement_pips > 0 else -1
    
    # Trouver TTR (premier retournement significatif après le peak)
    ttr_minutes = None
    if peak_time is not None and peak_time < len(prices_df) - 1:
        peak_price = prices_df.iloc[peak_time]['price']
        
        for i in range(peak_time + 1, len(prices_df)):
            current_price = prices_df.iloc[i]['price']
            retracement = abs((current_price - peak_price) * 10000)
            
            # Retournement = retracement > 30% du mouvement initial
            if retracement > abs(max_movement) * 0.3:
                ttr_minutes = i - peak_time
                break
    
    if ttr_minutes is None:
        ttr_minutes = len(prices_df) - peak_time if peak_time else len(prices_df)
    
    return {
        'real_impact_pips': max_movement,
        'real_direction': direction,
        'real_latency_minutes': latency_minutes if latency_minutes is not None else len(prices_df),
        'real_ttr_minutes': ttr_minutes,
        'peak_time_minutes': peak_time,
        'had_reaction': latency_minutes is not None
    }


def create_backtest_chart(prices_df, event_time, predicted_impact, predicted_latency, predicted_ttr, real_metrics):
    """Crée graphique comparaison prédiction vs réalité"""
    from datetime import timedelta
    
    fig = go.Figure()
    
    # Convertir event_time en datetime natif pour Plotly
    if isinstance(event_time, pd.Timestamp):
        event_time = event_time.to_pydatetime()
    
    # Convertir DataFrame times en datetime natifs
    plot_times = [t.to_pydatetime() if isinstance(t, pd.Timestamp) else t for t in prices_df['time']]
    
    # Prix réel
    fig.add_trace(go.Scatter(
        x=plot_times,
        y=prices_df['price'],
        mode='lines',
        name='Prix EUR/USD',
        line=dict(color='blue', width=2),
        hovertemplate='%{y:.5f}<extra></extra>'
    ))
    
    # Prix de référence (horizontal)
    ref_price = prices_df.iloc[0]['price']
    fig.add_hline(
        y=ref_price,
        line_dash="dash",
        line_color="gray",
        annotation_text="Prix référence"
    )
    
    # Ligne verticale événement
    fig.add_shape(
        type="line",
        x0=event_time, x1=event_time,
        y0=0, y1=1,
        yref="paper",
        line=dict(color="black", width=2)
    )
    fig.add_annotation(
        x=event_time, y=1, yref="paper",
        text="📊 Événement",
        showarrow=False,
        yshift=10
    )
    
    # Ligne verticale latence prédite
    predicted_latency_time = event_time + timedelta(minutes=float(predicted_latency))
    fig.add_shape(
        type="line",
        x0=predicted_latency_time, x1=predicted_latency_time,
        y0=0, y1=1,
        yref="paper",
        line=dict(color="orange", width=2, dash="dot")
    )
    fig.add_annotation(
        x=predicted_latency_time, y=0.9, yref="paper",
        text=f"Latence prédite ({predicted_latency:.0f} min)",
        showarrow=False,
        font=dict(color="orange")
    )
    
    # Ligne verticale latence réelle
    if real_metrics and real_metrics['had_reaction']:
        real_latency_time = event_time + timedelta(minutes=float(real_metrics['real_latency_minutes']))
        fig.add_shape(
            type="line",
            x0=real_latency_time, x1=real_latency_time,
            y0=0, y1=1,
            yref="paper",
            line=dict(color="green", width=2, dash="dot")
        )
        fig.add_annotation(
            x=real_latency_time, y=0.1, yref="paper",
            text=f"Latence réelle ({real_metrics['real_latency_minutes']:.0f} min)",
            showarrow=False,
            font=dict(color="green")
        )
    
    # Ligne verticale TTR prédit
    predicted_ttr_time = event_time + timedelta(minutes=float(predicted_ttr))
    fig.add_shape(
        type="line",
        x0=predicted_ttr_time, x1=predicted_ttr_time,
        y0=0, y1=1,
        yref="paper",
        line=dict(color="red", width=2, dash="dot")
    )
    fig.add_annotation(
        x=predicted_ttr_time, y=0.8, yref="paper",
        text=f"TTR prédit ({predicted_ttr:.0f} min)",
        showarrow=False,
        font=dict(color="red")
    )
    
    # Zone impact prédit
    predicted_price = ref_price + (predicted_impact / 10000)
    fig.add_hrect(
        y0=ref_price,
        y1=predicted_price,
        fillcolor="orange",
        opacity=0.2,
        line_width=0
    )
    
    fig.update_layout(
        title="Comparaison Prédiction vs Réalité du Marché",
        xaxis_title="Temps",
        yaxis_title="Prix EUR/USD",
        height=500,
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


# ✅ PRÉ-CHARGEMENT DES FAMILLES COMMUNES (Option 4)
# Placé ici car TOUTES les fonctions sont définies
if 'preloaded' not in st.session_state:
    st.info("⚡ Chargement stats DB...")
    precomputed_stats = load_precomputed_stats_from_db()
    if precomputed_stats:
        st.session_state.precomputed_stats = precomputed_stats
        st.session_state.preloaded = True
        st.success(f"✅ {len(precomputed_stats)}/16 familles - Calculs ultra-rapides !", icon="⚡")
        with st.expander("📊 Familles disponibles"):
            for fam in sorted(precomputed_stats.keys()):
                st.caption(f"✅ {fam}")
    else:
        st.warning("⚠️ Calculs classiques")
        st.session_state.precomputed_stats = {}
        st.session_state.preloaded = True
    

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
    with st.spinner("Chargement des événements..."):
        # Charger événements mappés (avec famille)
        events = get_future_events(date_from, date_to, countries)
        
        # Charger TOUS les événements (mappés + non mappés)
        all_events = load_all_events_for_date(date_from, countries)
        
        if len(events) == 0 and len(all_events['unmapped']) == 0:
            st.error("Aucun événement trouvé")
            st.stop()
        
        st.session_state.future_events = events
        st.session_state.all_events = all_events  # Stocker tous les événements
        st.session_state.events_loaded = True
        st.session_state.selected_events = set()
        
        # Message de confirmation
        mapped_count = len(events)
        unmapped_count = len(all_events['unmapped'])
        st.sidebar.success(f"✅ {mapped_count} événements mappés")
        if unmapped_count > 0:
            st.sidebar.warning(f"⚠️ {unmapped_count} événements sans famille")

# === ZONE PRINCIPALE ===

if not st.session_state.events_loaded:
    st.info("👈 Configurez la période et cliquez sur Charger Événements")
    
    st.markdown("""
    ### 🎯 Fonctionnement
    
    Cette page analyse **plusieurs événements simultanés** avec :
    - **Score Empirique** : Classification basée sur 3 ans de données réelles (0-100)
    - **Impact** : Mouvement prix prédit (pips)
    - **Latence** : Temps avant réaction du marché (✅ CORRIGÉ avec LatencyAnalyzer)
    - **TTR** : Time To Reversal (persistance du mouvement)
    - **Retracement** : Niveaux Fibonacci de correction
    
    **Méthode vectorielle** :
    ```
    Impact_combiné = Σ(impact_i × direction_i)
    Latence_combinée = moyenne pondérée
    TTR_combiné = minimum (sortie au premier retournement)
    ```
    
    ### 📊 Nouveautés v8.4
    
    - 📈 **Timeline visuelle** interactive
    - ⚠️ **Détection chevauchements** entre fenêtres
    - 🎯 **Score de tradabilité** 0-100
    - 📐 **Niveaux Fibonacci** pour retracements
    - ✅ **TTR RÉEL** calculé depuis les prix observés (événements passés)
    - 📊 **MAE/RMSE** pour validation du TTR
    
    ### 🚀 Workflow
    
    1. Sélectionner période
    2. Charger événements
    3. Cocher événements à analyser
    4. Entrer valeurs hypothétiques
    5. Voir prédiction combinée + analyse complète
    """)

else:
    df = st.session_state.future_events
    
    st.success(f"✅ {len(df)} événements trouvés")
    
    # Grouper par date
    df['date'] = pd.to_datetime(df['ts_utc']).dt.date
    dates = sorted(df['date'].unique())
    
    # Sélection événements
    st.header("📋 Sélection des Événements")
    
    
    # ═══════════════════════════════════════════════════════════
    # ÉVÉNEMENTS SANS FAMILLE (Non mappés)
    # ═══════════════════════════════════════════════════════════
    
    if 'all_events' in st.session_state and len(st.session_state.all_events['unmapped']) > 0:
        st.divider()
        
        unmapped_count = len(st.session_state.all_events['unmapped'])
        
        with st.expander(
            f"⚠️ {unmapped_count} événement{'s' if unmapped_count > 1 else ''} sans famille",
            expanded=False
        ):
            st.warning(
                "**Ces événements n'ont pas de famille configurée** → Pas de prédiction automatique. "
                "Ils peuvent néanmoins impacter les marchés !"
            )
            
            unmapped_df = st.session_state.all_events['unmapped']
            
            st.markdown("### 📋 Liste")
            
            for idx, row in unmapped_df.iterrows():
                col_time, col_event, col_data = st.columns([1, 3, 2])
                
                with col_time:
                    event_time = row['ts_utc'].strftime('%H:%M')
                    importance = "🔴" if row['importance_n'] >= 3 else "🟡" if row['importance_n'] == 2 else "🟢"
                    st.markdown(f"**{event_time}** {importance}")
                
                with col_event:
                    st.markdown(f"**{row['event_key']}** ({row['country']})")
                    
                    # Surprise si disponible
                    if pd.notna(row['actual']) and pd.notna(row['estimate']) and row['estimate'] != 0:
                        surprise = row['actual'] - row['estimate']
                        surprise_pct = (surprise / row['estimate'] * 100)
                        icon = "🔺" if surprise > 0 else "🔻" if surprise < 0 else "➖"
                        st.caption(f"{icon} Surprise: {surprise_pct:+.1f}%")
                
                with col_data:
                    parts = []
                    if pd.notna(row['previous']):
                        parts.append(f"Prev: {row['previous']:.2f}")
                    if pd.notna(row['estimate']):
                        parts.append(f"Fcst: {row['estimate']:.2f}")
                    if pd.notna(row['actual']):
                        parts.append(f"**{row['actual']:.2f}**")
                    
                    if parts:
                        st.caption(" | ".join(parts))
                
                st.markdown("---")
            
            st.info(
                "💡 **Ex:** Le **Current Account (DE) à 14:45** peut relancer EUR/USD même sans prédiction. "
                "Surveillez ces événements manuellement !"
            )
    
    st.divider()
    
    selected_indices = []
    
    for date in dates:
        st.subheader(f"📆 {date.strftime('%A %d/%m/%Y')}")
        
        day_events = df[df['date'] == date]
        
        for idx, event in day_events.iterrows():
            col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1, 1, 1])
            
            with col1:
                checked = st.checkbox(
                    "",
                    value=True,  # ✅ Coché par défaut
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
            
            with col5:
                # Score empirique
                if pd.notna(event.get('empirical_score')):
                    score = event['empirical_score']
                    impact_level = event.get('empirical_impact', 'N/A')
                    
                    # Couleur selon niveau
                    if score >= 70:
                        st.success(f"⭐ {score:.0f}")
                        st.caption(f"🔴 {impact_level}")
                    elif score >= 40:
                        st.info(f"📊 {score:.0f}")
                        st.caption(f"🟡 {impact_level}")
                    else:
                        st.warning(f"📉 {score:.0f}")
                        st.caption(f"🟢 {impact_level}")
                else:
                    st.caption("Score: N/A")
    
    st.session_state.selected_events = set(selected_indices)
    
    # Configuration des événements sélectionnés
    if len(st.session_state.selected_events) > 0:
        st.divider()
        st.header("⚙️ Configuration des Événements Sélectionnés")
        
        predictions = []
        
        for idx in sorted(st.session_state.selected_events):
            event = df.loc[idx]
            
            with st.expander(f"📊 {event['family']} - {pd.to_datetime(event['ts_utc']).strftime('%H:%M')} ({event['country']})", expanded=True):
                
                # Afficher classification empirique en haut si disponible
                if pd.notna(event.get('empirical_score')):
                    col_class1, col_class2, col_class3 = st.columns(3)
                    with col_class1:
                        st.metric("📊 Score Empirique", f"{event['empirical_score']:.0f}/100")
                    with col_class2:
                        emp_impact = event.get('empirical_impact', 'N/A')
                        emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(emp_impact, "⚪")
                        st.metric("🎯 Impact Empirique", f"{emoji} {emp_impact}")
                    with col_class3:
                        theo_impact = event.get('impact_level', 'N/A')
                        emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(theo_impact, "⚪")
                        st.metric("📖 Impact Théorique", f"{emoji} {theo_impact}")
                
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
                    precomputed_stats = st.session_state.get('precomputed_stats', {})
                    pred = predict_impact_fast(event['family'], surprise, precomputed_stats)
                    
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
            st.header("🎲 Analyse Multi-Événements Complète")
            
            # ═══════════════════════════════════════════════════════════
            # 🆕 NOUVEAU v8.4 : TOGGLE TIMELINE SÉQUENTIELLE
            # ═══════════════════════════════════════════════════════════
            
            if SEQUENTIAL_MODE_AVAILABLE:
                st.markdown("---")
                
                col_toggle, col_info = st.columns([3, 1])
                
                with col_toggle:
                    use_sequential = st.checkbox(
                        "🔄 Activer le Mode Timeline Séquentielle",
                        value=True,
                        key="use_sequential_toggle",
                        help=(
                            "Analyse événements multiples comme phases distinctes au lieu d'un TTR global. "
                            "Recommandé quand plusieurs événements se suivent de près (< 30 min)."
                        )
                    )
                
                with col_info:
                    with st.expander("❓ Pourquoi ce mode ?"):
                        st.markdown("""
                        **Le problème résolu :**
                        
                        Quand événements multiples se suivent (ex: 14:30 et 14:45), 
                        le 2ème événement **"coupe"** le TTR du 1er.
                        
                        📊 **Exemple 11/09/2025 :**
                        ```
                        14:30 → Jobless + CPI (DOWN)
                        14:35 → Premier TTR (~5 min) ✅
                        14:45 → Current Account (UP) ← Nouveau mouvement !
                        14:50 → Deuxième TTR (~5 min) ✅
                        ```
                        
                        ❌ **Sans séquençage :** TTR global = 20-40 min (très imprécis)  
                        ✅ **Avec séquençage :** TTR₁ = 5 min, TTR₂ = 5 min (précis)
                        
                        **Amélioration v8.4 :** TTR RÉEL calculé depuis prix observés
                        """)
                
                st.markdown("---")
                
                # ========== Calcul et Affichage selon mode ==========
                if use_sequential:
                    # MODE SÉQUENTIEL v8.4
                    try:
                        with st.spinner("🔄 Calcul timeline séquentielle..."):
                            # Préparer données pour séquençage
                            predictions_for_seq = []
                            for pred in predictions:
                                predictions_for_seq.append({
                                    'event': {
                                        'ts_utc': pd.to_datetime(pred['event']['ts_utc']),
                                        'family': pred['event']['family'],
                                        'event_key': pred['event']['event_key'],
                                        'country': pred['event']['country']
                                    },
                                    'predicted_pips': pred['predicted_pips'],
                                    'direction': pred['direction'],
                                    'latency_median': pred['latency_median'],
                                    'ttr_median': pred['ttr_median'],
                                    'surprise': pred['surprise']
                                })
                            
                            # === NOUVEAU v8.4 : Récupérer prix réels pour calcul TTR observé ===
                            now = pd.Timestamp.now(tz='UTC')
                            
                            def to_utc_aware(ts):
                                ts = pd.to_datetime(ts)
                                if ts.tz is None:
                                    return ts.tz_localize('UTC')
                                else:
                                    return ts.tz_convert('UTC')
                            
                            is_past = all(to_utc_aware(p['event']['ts_utc']) < now 
                                         for p in predictions_for_seq)
                            
                            real_prices_df = None
                            if is_past:
                                with st.spinner("📥 Récupération prix pour calcul TTR réel..."):
                                    first_event = min(pd.to_datetime(p['event']['ts_utc']) 
                                                     for p in predictions_for_seq)
                                    start_fetch = first_event - timedelta(minutes=30)
                                    
                                    prices_batch = get_real_prices_batch([start_fetch], window_minutes=120)
                                    
                                    if 0 in prices_batch:
                                        real_prices_df = prices_batch[0]
                                        st.success("✅ Prix réels récupérés → TTR observé calculé")
                                    else:
                                        st.warning("⚠️ Prix introuvables → TTR théorique utilisé")
                            
                            # Calculer phases avec TTR réel si disponible
                            phases = sequence_multi_event_timeline(
                                predictions_for_seq, 
                                real_prices_df=real_prices_df
                            )
                            
                            # Afficher source du TTR
                            if real_prices_df is not None:
                                n_observed = sum(1 for p in phases if p.get('ttr_source') == 'observed')
                                if n_observed > 0:
                                    st.info(f"🎯 {n_observed}/{len(phases)} phases avec TTR observé depuis prix réels")
                                    
                                    # Statistiques d'erreur TTR
                                    ttr_stats = calculate_ttr_accuracy_stats(phases)
                                    if ttr_stats['n_phases'] > 0:
                                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                                        with col_stat1:
                                            st.metric("📊 MAE TTR", f"{ttr_stats['mae']:.1f} min")
                                        with col_stat2:
                                            st.metric("📊 RMSE TTR", f"{ttr_stats['rmse']:.1f} min")
                                        with col_stat3:
                                            st.metric("📊 Erreur Max", f"{ttr_stats['max_error']:.1f} min")
                            
                            # Afficher timeline
                            display_sequential_timeline(phases, show_details=True)
                            
                            # Stocker dans session_state
                            st.session_state['sequential_phases'] = phases
                            st.session_state['use_sequential_mode'] = True
                            st.session_state['original_predictions'] = predictions
                            
                            st.success(f"✅ {len(phases)} phases calculées avec succès")
                            
                            # ═══════════════════════════════════════════════════════════
                            # 📊 AJOUTER LES SECTIONS CLASSIQUES EN MODE SÉQUENTIEL
                            # ═══════════════════════════════════════════════════════════
                            
                            st.divider()
                            
                            # Calculer métriques globales pour affichage classique
                            timestamps = [pd.to_datetime(p['event']['ts_utc']) for p in predictions]
                            time_span = (max(timestamps) - min(timestamps)).total_seconds() / 3600
                            
                            vectorial_impact = sum(p['predicted_pips'] * p['direction'] for p in predictions)
                            combined_direction = "🔼 HAUSSE" if vectorial_impact > 0 else "🔽 BAISSE"
                            
                            total_impact = sum(p['predicted_pips'] for p in predictions)
                            if total_impact > 0:
                                weighted_latency = sum(p['latency_median'] * p['predicted_pips'] for p in predictions) / total_impact
                            else:
                                weighted_latency = np.mean([p['latency_median'] for p in predictions])
                            
                            min_ttr = min(p['ttr_median'] for p in predictions)
                            overlaps = detect_overlaps(predictions)
                            tradability_score = calculate_tradability_score(predictions, overlaps, time_span)
                            
                            # === SECTION : DÉTAILS CALCUL ===
                            st.subheader("📊 Détails du Calcul Vectoriel")
                            
                            calc_data = []
                            for p in predictions:
                                calc_data.append({
                                    'Événement': f"{p['event']['family']} ({p['event']['country']})",
                                    'Heure': pd.to_datetime(p['event']['ts_utc']).strftime('%H:%M'),
                                    'Surprise': f"{p['surprise']:+.2f}",
                                    'Impact': f"{p['predicted_pips']:.1f}",
                                    'Direction': "🔼 UP" if p['direction'] > 0 else "🔽 DOWN",
                                    'Latence': f"{p['latency_median']:.0f} min",
                                    'TTR': f"{p['ttr_median']:.0f} min",
                                    'Contribution': f"{p['predicted_pips'] * p['direction']:+.1f} pips"
                                })
                            
                            st.table(pd.DataFrame(calc_data))
                            
                            st.divider()
                            
                            # === SECTION : RÉSULTAT FINAL ===
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
                                cohesion = "Forte" if len(set([p['direction'] for p in predictions])) == 1 else "Faible"
                                st.metric("Cohésion", cohesion)
                            
                            st.divider()
                            
                            # === SECTION : RETRACEMENT FIBONACCI ===
                            st.subheader("📐 Niveaux de Retracement Fibonacci")
                            
                            fib_levels = calculate_fibonacci_levels(abs(vectorial_impact), np.sign(vectorial_impact))
                            
                            fib_col1, fib_col2 = st.columns(2)
                            
                            with fib_col1:
                                st.markdown("**Zones de Support/Résistance**")
                                for level, pips in fib_levels.items():
                                    if level in ['38.2%', '50%', '61.8%']:
                                        st.info(f"**{level}** : {pips:+.1f} pips")
                                    else:
                                        st.caption(f"{level} : {pips:+.1f} pips")
                            
                            with fib_col2:
                                st.markdown("**Recommandations**")
                                st.write("🎯 **Zone d'entrée idéale** : 23.6% - 38.2%")
                                st.write("⚠️ **Stop loss suggéré** : en dessous de 78.6%")
                                st.write("🎁 **Take profit** : 100% (mouvement complet)")
                                st.write("💰 **TP partiel** : 61.8% (zone de résistance)")
                            
                            st.divider()
                            
                            # === SECTION : FENÊTRE DE TRADING ===
                            st.subheader("⏰ Fenêtre de Trading Suggérée")
                            
                            first_event_time = min(timestamps)
                            
                            entry_time = first_event_time - timedelta(minutes=2)
                            reaction_time = first_event_time + timedelta(minutes=weighted_latency)
                            exit_time = first_event_time + timedelta(minutes=min_ttr)
                            
                            col_t1, col_t2, col_t3 = st.columns(3)
                            
                            with col_t1:
                                st.info(f"**🕐 Entrée suggérée**\n\n{entry_time.strftime('%H:%M')}\n\n(2 min avant)")
                            
                            with col_t2:
                                st.success(f"**📊 Réaction attendue**\n\n{reaction_time.strftime('%H:%M')}\n\n(+{weighted_latency:.0f} min)")
                            
                            with col_t3:
                                st.warning(f"**🎯 Sortie suggérée**\n\n{exit_time.strftime('%H:%M')}\n\n(TTR à {min_ttr:.0f} min)")
                            
                            # === FIN SECTIONS CLASSIQUES ===
                            
                    except Exception as e:
                        st.error(f"❌ Erreur calcul timeline séquentielle: {e}")
                        st.exception(e)
                        use_sequential = False
                        st.warning("⚠️ Basculement sur mode classique...")
                
                if not use_sequential:
                    st.session_state['use_sequential_mode'] = False
            else:
                st.session_state['use_sequential_mode'] = False
                use_sequential = False
