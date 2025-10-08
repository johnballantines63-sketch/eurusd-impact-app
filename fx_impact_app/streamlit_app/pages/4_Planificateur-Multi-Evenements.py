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
from latency_analyzer import LatencyAnalyzer  # ✅ AJOUT IMPORT

st.set_page_config(page_title="Planificateur Multi-Événements", page_icon="📅", layout="wide")

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

@st.cache_data(ttl=3600)
def load_precomputed_stats_from_db():
    """Charge stats pré-calculées depuis DB"""
    try:
        conn = duckdb.connect(get_db_path(), read_only=True)
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
        direction = 1 if surprise > 0 else -1
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
    
    ### 📊 Nouveautés
    
    - 📈 **Timeline visuelle** interactive
    - ⚠️ **Détection chevauchements** entre fenêtres
    - 🎯 **Score de tradabilité** 0-100
    - 📐 **Niveaux Fibonacci** pour retracements
    - ✅ **Latences précises** via LatencyAnalyzer
    
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
    
    selected_indices = []
    
    for date in dates:
        st.subheader(f"📆 {date.strftime('%A %d/%m/%Y')}")
        
        day_events = df[df['date'] == date]
        
        for idx, event in day_events.iterrows():
            col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1, 1, 1])
            
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
            
            # Analyser fenêtre temporelle
            timestamps = [pd.to_datetime(p['event']['ts_utc']) for p in predictions]
            time_span = (max(timestamps) - min(timestamps)).total_seconds() / 3600
            
            # Calculs combinés
            vectorial_impact = sum(p['predicted_pips'] * p['direction'] for p in predictions)
            combined_direction = "🔼 HAUSSE" if vectorial_impact > 0 else "🔽 BAISSE"
            
            # Latence pondérée
            total_impact = sum(p['predicted_pips'] for p in predictions)
            if total_impact > 0:
                weighted_latency = sum(p['latency_median'] * p['predicted_pips'] for p in predictions) / total_impact
            else:
                weighted_latency = np.mean([p['latency_median'] for p in predictions])
            
            # TTR = minimum
            min_ttr = min(p['ttr_median'] for p in predictions)
            
            # Détection chevauchements
            overlaps = detect_overlaps(predictions)
            
            # Score de tradabilité
            tradability_score = calculate_tradability_score(predictions, overlaps, time_span)
            
            # === SECTION 1 : SCORE DE TRADABILITÉ ===
            st.subheader("🎯 Score de Tradabilité de la Session")
            
            score_col1, score_col2, score_col3 = st.columns([2, 1, 1])
            
            with score_col1:
                # Gauge visuelle
                if tradability_score >= 70:
                    score_color = "green"
                    score_label = "EXCELLENT"
                elif tradability_score >= 50:
                    score_color = "orange"
                    score_label = "BON"
                else:
                    score_color = "red"
                    score_label = "RISQUÉ"
                
                st.metric("Score Global", f"{tradability_score}/100", delta=score_label)
            
            with score_col2:
                if time_span <= 2:
                    st.success(f"⏱️ Fenêtre compacte\n\n{time_span:.1f}h")
                else:
                    st.warning(f"⚠️ Événements espacés\n\n{time_span:.1f}h")
            
            with score_col3:
                directions = [p['direction'] for p in predictions]
                if len(set(directions)) == 1:
                    st.success("✅ AMPLIFICATION\n\nMême direction")
                else:
                    st.warning("⚠️ ANTAGONISME\n\nDirections opposées")
            
            # Alertes chevauchements
            if overlaps:
                st.warning(f"⚠️ **{len(overlaps)} chevauchement(s) détecté(s)**")
                for overlap in overlaps:
                    severity_emoji = "🔴" if overlap['severity'] == 'HIGH' else "🟡"
                    st.caption(f"{severity_emoji} {overlap['event1']} ↔️ {overlap['event2']} : {overlap['overlap_minutes']:.0f} min de chevauchement")
            else:
                st.success("✅ Aucun chevauchement détecté")
            
            st.divider()
            
            # === SECTION 2 : TIMELINE VISUELLE ===
            st.subheader("📈 Timeline Visuelle Interactive")
            
            timeline_fig = create_timeline_chart(predictions, weighted_latency, min_ttr)
            st.plotly_chart(timeline_fig, use_container_width=True)
            
            st.divider()
            
            # === SECTION 3 : DÉTAILS CALCUL ===
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
            
            # === SECTION 4 : RÉSULTAT FINAL ===
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
            
            # === SECTION 5 : RETRACEMENT FIBONACCI ===
            st.subheader("📐 Niveaux de Retracement Fibonacci")
            
            fib_levels = calculate_fibonacci_levels(abs(vectorial_impact), np.sign(vectorial_impact))
            
            fib_col1, fib_col2 = st.columns(2)
            
            with fib_col1:
                st.markdown("**Zones de Support/Résistance**")
                for level, pips in fib_levels.items():
                    if level in ['38.2%', '50%', '61.8%']:  # Niveaux clés
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
            
            # === SECTION 6 : FENÊTRE DE TRADING ===
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
            
            # Plan de trading détaillé
            with st.expander("📋 Plan de Trading Détaillé", expanded=False):
                st.markdown(f"""
                ### Phase 1 : Préparation ({entry_time.strftime('%H:%M')})
                - ✅ Vérifier conditions de marché (spread, liquidité)
                - ✅ Placer ordres limite aux niveaux Fibonacci 23.6% - 38.2%
                - ✅ Définir stop loss à 78.6% = {fib_levels['78.6%']:+.1f} pips
                
                ### Phase 2 : Entrée (T0 = {first_event_time.strftime('%H:%M')})
                - 📊 Événements : {', '.join([p['event']['family'] for p in predictions])}
                - 🎯 Impact attendu : {abs(vectorial_impact):.1f} pips {combined_direction}
                - ⏱️ Réaction dans {weighted_latency:.0f} minutes
                
                ### Phase 3 : Gestion ({reaction_time.strftime('%H:%M')} - {exit_time.strftime('%H:%M')})
                - 💰 TP partiel à 61.8% = {fib_levels['61.8%']:+.1f} pips
                - 🎁 TP final à 100% = {fib_levels['100%']:+.1f} pips
                - ⚠️ Sortie complète à {exit_time.strftime('%H:%M')} (TTR)
                
                ### Phase 4 : Retracement éventuel
                - 📉 Si retracement, surveiller support 50% = {fib_levels['50%']:+.1f} pips
                - 🔄 Possible re-entrée si rebond confirmé sur 50% ou 61.8%
                """)
            
            st.divider()
            
            # === SECTION 7 : SCÉNARIOS ===
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
                        'Direction': "🔼 UP" if scenario_impact > 0 else "🔽 DOWN",
                        'Latence': f"{scenario_latency:.0f} min",
                        'TTR': f"{scenario_ttr:.0f} min"
                    })
            
            if scenarios:
                st.table(pd.DataFrame(scenarios))
            
            st.divider()
            
            # === SECTION 8 : BACKTESTING (SI ÉVÉNEMENTS PASSÉS) ===
            
            # Vérifier si événements sont dans le passé
            now = pd.Timestamp.now(tz='UTC')
            
            def to_utc_aware(ts):
                """Convertit timestamp en UTC aware"""
                ts = pd.to_datetime(ts)
                if ts.tz is None:
                    return ts.tz_localize('UTC')
                else:
                    return ts.tz_convert('UTC')
            
            is_past = all(to_utc_aware(p['event']['ts_utc']) < now for p in predictions)
            
            if is_past:
                st.header("🔬 Backtesting - Comparaison Prédiction vs Réalité")
                
                st.info("📊 Les événements sélectionnés sont dans le passé. Analyse des résultats réels...")
                
                # OPTIMISATION : Récupérer TOUS les prix en UNE SEULE query
                event_times = [pd.to_datetime(p['event']['ts_utc']) for p in predictions]
                
                with st.spinner("📥 Récupération des prix réels (batch optimisé)..."):
                    prices_batch = get_real_prices_batch(event_times, window_minutes=60)
                
                # Pour chaque événement, mesurer impact réel
                backtest_results = []
                
                progress_bar = st.progress(0)
                for i, pred in enumerate(predictions):
                    event_time = pd.to_datetime(pred['event']['ts_utc'])
                    
                    # Récupérer depuis batch
                    prices_df = prices_batch.get(i)
                    
                    if prices_df is not None and len(prices_df) > 0:
                        # Mesurer impact réel
                        real_metrics = measure_real_impact(prices_df)
                        
                        if real_metrics:
                            backtest_results.append({
                                'prediction': pred,
                                'prices': prices_df,
                                'real_metrics': real_metrics,
                                'event_time': event_time
                            })
                    
                    progress_bar.progress((i + 1) / len(predictions))
                
                progress_bar.empty()
                
                if backtest_results:
                    # Tableau comparatif
                    st.subheader("📊 Tableau Comparatif Prédiction vs Réalité")
                    
                    comparison_data = []
                    for result in backtest_results:
                        pred = result['prediction']
                        real = result['real_metrics']
                        
                        # Calcul erreurs
                        error_impact = abs(pred['predicted_pips'] - abs(real['real_impact_pips']))
                        error_latency = abs(pred['latency_median'] - real['real_latency_minutes'])
                        error_ttr = abs(pred['ttr_median'] - real['real_ttr_minutes'])
                        
                        comparison_data.append({
                            'Événement': f"{pred['event']['family']} ({pred['event']['country']})",
                            'Impact Prédit': f"{pred['predicted_pips']:.1f} pips",
                            'Impact Réel': f"{abs(real['real_impact_pips']):.1f} pips",
                            'Erreur Impact': f"{error_impact:.1f} pips",
                            'Latence Prédite': f"{pred['latency_median']:.0f} min",
                            'Latence Réelle': f"{real['real_latency_minutes']:.0f} min",
                            'Erreur Latence': f"{error_latency:.0f} min",
                            'TTR Prédit': f"{pred['ttr_median']:.0f} min",
                            'TTR Réel': f"{real['real_ttr_minutes']:.0f} min",
                            'Erreur TTR': f"{error_ttr:.0f} min"
                        })
                    
                    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
                    
                    # Métriques globales d'erreur
                    st.subheader("🎯 Métriques d'Erreur Globales")
                    
                    errors_impact = [abs(r['prediction']['predicted_pips'] - abs(r['real_metrics']['real_impact_pips'])) 
                                    for r in backtest_results]
                    errors_latency = [abs(r['prediction']['latency_median'] - r['real_metrics']['real_latency_minutes']) 
                                     for r in backtest_results]
                    errors_ttr = [abs(r['prediction']['ttr_median'] - r['real_metrics']['real_ttr_minutes']) 
                                 for r in backtest_results]
                    
                    col_err1, col_err2, col_err3 = st.columns(3)
                    
                    with col_err1:
                        mae_impact = np.mean(errors_impact)
                        rmse_impact = np.sqrt(np.mean([e**2 for e in errors_impact]))
                        st.metric("MAE Impact", f"{mae_impact:.1f} pips")
                        st.caption(f"RMSE: {rmse_impact:.1f} pips")
                    
                    with col_err2:
                        mae_latency = np.mean(errors_latency)
                        rmse_latency = np.sqrt(np.mean([e**2 for e in errors_latency]))
                        st.metric("MAE Latence", f"{mae_latency:.1f} min")
                        st.caption(f"RMSE: {rmse_latency:.1f} min")
                    
                    with col_err3:
                        mae_ttr = np.mean(errors_ttr)
                        rmse_ttr = np.sqrt(np.mean([e**2 for e in errors_ttr]))
                        st.metric("MAE TTR", f"{mae_ttr:.1f} min")
                        st.caption(f"RMSE: {rmse_ttr:.1f} min")
                    
                    # Interprétation
                    if mae_impact < 5:
                        st.success("✅ Excellente précision sur l'impact (MAE < 5 pips)")
                    elif mae_impact < 10:
                        st.info("ℹ️ Bonne précision sur l'impact (MAE < 10 pips)")
                    else:
                        st.warning("⚠️ Précision modérée sur l'impact (MAE ≥ 10 pips)")
                    
                    if mae_latency < 5:
                        st.success("✅ Excellente précision sur la latence (MAE < 5 min)")
                    elif mae_latency < 10:
                        st.info("ℹ️ Bonne précision sur la latence (MAE < 10 min)")
                    else:
                        st.warning("⚠️ Précision modérée sur la latence (MAE ≥ 10 min)")
                    
                    st.divider()
                    
                    # Graphiques individuels (lazy loading - seulement si demandé)
                    st.subheader("📈 Graphiques Prix Réels vs Prédictions")
                    
                    show_charts = st.checkbox("📊 Afficher les graphiques détaillés (peut ralentir)", value=False)
                    
                    if show_charts:
                        for result in backtest_results:
                            pred = result['prediction']
                            real = result['real_metrics']
                            
                            with st.expander(f"📊 {pred['event']['family']} - {result['event_time'].strftime('%d/%m/%Y %H:%M')}", expanded=False):
                                
                                # Graphique
                                chart = create_backtest_chart(
                                    result['prices'],
                                    result['event_time'],
                                    pred['predicted_pips'] * pred['direction'],
                                    pred['latency_median'],
                                    pred['ttr_median'],
                                    real
                                )
                                
                                st.plotly_chart(chart, use_container_width=True)
                                
                                # Résumé
                                col_sum1, col_sum2, col_sum3 = st.columns(3)
                                
                                with col_sum1:
                                    error_impact = abs(pred['predicted_pips'] - abs(real['real_impact_pips']))
                                    st.metric(
                                        "Impact",
                                        f"{abs(real['real_impact_pips']):.1f} pips (réel)",
                                        delta=f"{error_impact:.1f} pips erreur"
                                    )
                                
                                with col_sum2:
                                    error_latency = abs(pred['latency_median'] - real['real_latency_minutes'])
                                    st.metric(
                                        "Latence",
                                        f"{real['real_latency_minutes']:.0f} min (réel)",
                                        delta=f"{error_latency:.0f} min erreur"
                                    )
                                
                                with col_sum3:
                                    error_ttr = abs(pred['ttr_median'] - real['real_ttr_minutes'])
                                    st.metric(
                                        "TTR",
                                        f"{real['real_ttr_minutes']:.0f} min (réel)",
                                        delta=f"{error_ttr:.0f} min erreur"
                                    )
                                
                                # Direction
                                pred_dir = "🔼 UP" if pred['direction'] > 0 else "🔽 DOWN"
                                real_dir = "🔼 UP" if real['real_direction'] > 0 else "🔽 DOWN"
                                
                                if pred['direction'] == real['real_direction']:
                                    st.success(f"✅ Direction correctement prédite : {pred_dir} = {real_dir}")
                                else:
                                    st.error(f"❌ Direction incorrecte : prédit {pred_dir}, réel {real_dir}")
                    else:
                        st.info("💡 Cochez la case ci-dessus pour afficher les graphiques individuels")
                
                else:
                    st.warning("⚠️ Impossible de récupérer les prix réels pour ces événements")
            
            st.divider()
            
            # === SECTION 9 : EXPORT ===
            st.subheader("💾 Export de l'Analyse")
            
            export_data = {
                'date': date_from.strftime('%Y-%m-%d'),
                'n_events': len(predictions),
                'tradability_score': tradability_score,
                'combined_impact_pips': abs(vectorial_impact),
                'direction': 'UP' if vectorial_impact > 0 else 'DOWN',
                'latency_minutes': round(weighted_latency, 1),
                'ttr_minutes': round(min_ttr, 1),
                'entry_time': entry_time.strftime('%H:%M'),
                'reaction_time': reaction_time.strftime('%H:%M'),
                'exit_time': exit_time.strftime('%H:%M'),
                'fibonacci_levels': {k: round(v, 1) for k, v in fib_levels.items()},
                'overlaps': overlaps,
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
                f"multi_events_analysis_{date_from.strftime('%Y%m%d')}.json",
                "application/json",
                use_container_width=True
            )
        
        elif len(predictions) == 1:
            st.info("ℹ️ Sélectionnez au moins 2 événements pour voir l'analyse multi-événements complète")
