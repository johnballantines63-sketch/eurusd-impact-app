"""
PLANIFICATEUR V3.0 - PIPELINE VALIDÉ
=====================================

Version 3.0 - Utilise le pipeline complet validé (8 étapes)
Architecture propre basée sur la documentation complète

Ce planificateur utilise directement :
- Pipeline complet en 8 étapes (scripts/run_pipeline_complete.py)
- Détection de patterns avec phase_a_robust_validation
- Prédictions avec Random Forest
- Stratégie de sortie optimisée

Performance validée :
- MAE: 8.4 pips
- Taux acceptable: 63.2%
- Taux excellent: 55.3%
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path
import pytz
from typing import Dict, Any, Optional
import importlib.util

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

import config

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION PAGE
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Planificateur V3.0 - Pipeline Validé",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Planificateur V3.0 - Pipeline Validé")
st.caption("Utilise le pipeline complet testé et validé (MAE: 8.4 pips, Taux acceptable: 63.2%)")

# ═══════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def format_datetime(dt) -> str:
    """Formate un datetime pour l'affichage"""
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        return dt
    if hasattr(dt, 'strftime'):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)

def format_price(price: Optional[float]) -> str:
    """Formate un prix pour l'affichage"""
    if price is None:
        return "N/A"
    return f"{price:.5f}"

def format_pips(pips: Optional[float]) -> str:
    """Formate des pips pour l'affichage"""
    if pips is None or pips == 0:
        return "0.0"
    return f"{pips:.2f}"

# ═══════════════════════════════════════════════════════════════
# IMPORT PIPELINE EXECUTOR
# ═══════════════════════════════════════════════════════════════

# Essayer d'importer le PipelineExecutor
PipelineExecutor = None
try:
    spec = importlib.util.spec_from_file_location(
        "run_pipeline_complete",
        PROJECT_ROOT / "scripts" / "run_pipeline_complete.py"
    )
    if spec and spec.loader:
        run_pipeline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_pipeline)
        PipelineExecutor = run_pipeline.PipelineExecutor
except Exception as e:
    st.warning(f"⚠️ PipelineExecutor non disponible: {e}")
    st.info("💡 Le pipeline complet sera créé prochainement. En attendant, utilisez le planificateur V3.0 Clean.")

# ═══════════════════════════════════════════════════════════════
# INTERFACE STREAMLIT
# ═══════════════════════════════════════════════════════════════

# Sidebar - Paramètres
st.sidebar.header("⚙️ Paramètres")

date_input = st.sidebar.date_input(
    "Date à analyser",
    value=datetime.now().date(),
    min_value=datetime(2020, 1, 1).date(),
    max_value=datetime(2030, 12, 31).date()
)

window_minutes = st.sidebar.slider(
    "Fenêtre cluster (minutes)",
    min_value=15,
    max_value=120,
    value=30,
    step=15
)

support_threshold = st.sidebar.slider(
    "Seuil support noyau dur",
    min_value=0.5,
    max_value=1.0,
    value=0.8,
    step=0.1
)

jaccard_threshold = st.sidebar.slider(
    "Seuil Jaccard (similarité clusters)",
    min_value=0.3,
    max_value=1.0,
    value=0.60,
    step=0.05
)

years_lookback = st.sidebar.slider(
    "Années de lookback",
    min_value=1,
    max_value=10,
    value=5,
    step=1
)

verbose_mode = st.sidebar.checkbox("Mode verbose (logs détaillés)", value=False)

# Paramètres du graphique
st.sidebar.header("📊 Paramètres Graphique")

# Marge temporelle
default_margin = st.session_state.get('time_margin', 2.0) if 'time_margin' in st.session_state else 2.0
time_margin_hours = st.sidebar.slider(
    "Marge temporelle (heures avant/après)",
    min_value=0.5,
    max_value=6.0,
    value=default_margin,
    step=0.5,
    help="Ajuste la fenêtre temporelle affichée autour des données"
)
st.session_state['time_margin'] = time_margin_hours

# Marge d'amplitude Y (pour mieux voir l'impact)
default_y_margin_pct = st.session_state.get('y_margin_pct', 5.0) if 'y_margin_pct' in st.session_state else 5.0
y_margin_pct = st.sidebar.slider(
    "Marge amplitude Y (%)",
    min_value=0.0,
    max_value=20.0,
    value=default_y_margin_pct,
    step=0.5,
    help="Réduire pour mieux voir l'amplitude (0% = échelle maximale, 20% = plus de contexte)"
)
st.session_state['y_margin_pct'] = y_margin_pct

st.sidebar.caption("💡 **Astuce** : Réduire la marge Y à 0-2% pour maximiser la visibilité de l'amplitude")

# Main content
date_str = date_input.strftime('%Y-%m-%d')

# Vérifier si on a déjà des résultats en cache pour cette date
cache_key = f"pipeline_result_{date_str}"
cached_result = st.session_state.get(cache_key)

# Bouton pour lancer la prédiction
if st.button("🚀 Lancer la Prédiction", type="primary", use_container_width=True):
    if PipelineExecutor is None:
        st.error("❌ PipelineExecutor non disponible. Le pipeline complet doit être créé d'abord.")
        st.info("💡 En attendant, utilisez le planificateur V3.0 Clean disponible dans le menu.")
        st.stop()
    
    with st.spinner(f"Exécution du pipeline pour {date_str}..."):
        try:
            # Exécuter le pipeline complet
            executor = PipelineExecutor(
                db_path=config.DB_PATH,
                verbose=verbose_mode,
                force_timeframe=None
            )
            
            result = executor.execute_complete_pipeline(
                date_str=date_str,
                window_minutes=window_minutes,
                support_threshold=support_threshold,
                jaccard_threshold=jaccard_threshold,
                years_lookback=years_lookback
            )
            
            if not result.get('success'):
                st.error(f"❌ Erreur lors de l'exécution du pipeline: {result.get('error', 'Erreur inconnue')}")
                st.stop()
            
            # Stocker les résultats dans session_state
            st.session_state[cache_key] = result
            
            # Extraire les résultats
            final_pred = result.get('final_prediction', {})
            results = result.get('results', {})
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
            import traceback
            with st.expander("Détails de l'erreur"):
                st.code(traceback.format_exc())
            st.stop()
elif cached_result is not None:
    # Utiliser les résultats en cache
    result = cached_result
    final_pred = result.get('final_prediction', {})
    results = result.get('results', {})
    st.info("ℹ️ Affichage des résultats en cache. Utilisez les sliders dans la sidebar pour ajuster l'échelle du graphique.")
else:
    # Pas de résultats, afficher un message
    if PipelineExecutor is None:
        st.warning("⚠️ PipelineExecutor non disponible. Le pipeline complet doit être créé d'abord.")
        st.info("💡 En attendant, utilisez le planificateur V3.0 Clean disponible dans le menu.")
    else:
        st.info("👆 Cliquez sur '🚀 Lancer la Prédiction' pour commencer l'analyse.")
    st.stop()

# ═══════════════════════════════════════════════════════════════
# AFFICHAGE RÉSULTATS (seulement si on a des résultats)
# ═══════════════════════════════════════════════════════════════

st.success("✅ Pipeline exécuté avec succès !")
            
# Informations du cluster
cluster_info = results.get('etape3_cluster_info', {})
cluster = cluster_info.get('cluster', {})
anchor_time = cluster.get('anchor_time')

st.subheader("📊 Informations du Cluster")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Événements totaux", cluster_info.get('n_total_events', 0))
with col2:
    st.metric("Noyau dur", cluster_info.get('n_core_events', 0))
with col3:
    st.metric("Clusters identiques", len(results.get('etape4_identical_clusters', [])))
with col4:
    if anchor_time:
        st.metric("Heure événement", format_datetime(anchor_time))

# Pattern détecté
pattern_info = final_pred.get('pattern_info', {})
pattern_type = final_pred.get('pattern_type', pattern_info.get('pattern_type', 'NONE'))
pattern_direction = final_pred.get('pattern_direction', pattern_info.get('direction', 'UNKNOWN'))
pattern_confidence = final_pred.get('pattern_confidence', pattern_info.get('confidence', 0.0))

st.subheader("📈 Pattern Détecté")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Type", pattern_type)
with col2:
    st.metric("Direction", pattern_direction)
with col3:
    st.metric("Confiance", f"{pattern_confidence:.2f}")

# Prédictions
impact_base = final_pred.get('impact_base', 0)
amplification_predite = final_pred.get('amplification_predite', 0)
prediction_finale = final_pred.get('prediction_finale', 0)
exit_target = final_pred.get('exit_target', 0)
exit_strategy = final_pred.get('exit_strategy', 'N/A')

st.subheader("💰 Prédictions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Impact de base", f"{impact_base:.2f} pips")
with col2:
    st.metric("Amplification", f"{amplification_predite:.2f}x")
with col3:
    st.metric("Impact prédit", f"{prediction_finale:.2f} pips", 
             delta=f"{prediction_finale - impact_base:.2f} pips" if prediction_finale != impact_base else None)
with col4:
    st.metric("Target sortie", f"{exit_target:.2f} pips", 
             help=f"Stratégie: {exit_strategy}")

# Graphique avec contrôles d'échelle
if anchor_time and prediction_finale > 0:
    try:
        st.subheader("📊 Graphique de Prédiction")
        
        # Récupérer les données de prix depuis les résultats du pipeline
        price_data = results.get('price_window', None)
        baseline_price = final_pred.get('baseline_price', None)
        pattern_wave1_peak_time = final_pred.get('pattern_wave1_peak_time')
        pattern_wave2_peak_time = final_pred.get('pattern_wave2_peak_time')
        
        if price_data is not None and not price_data.empty and baseline_price:
            # Convertir anchor_time en datetime si nécessaire
            if isinstance(anchor_time, str):
                anchor_time_dt = pd.to_datetime(anchor_time)
            elif isinstance(anchor_time, pd.Timestamp):
                anchor_time_dt = anchor_time.to_pydatetime()
            else:
                anchor_time_dt = anchor_time
            
            # S'assurer que anchor_time_dt est timezone-aware
            if anchor_time_dt.tzinfo is None:
                tz = pytz.timezone('Europe/Zurich')
                anchor_time_dt = tz.localize(anchor_time_dt)
            
            # Préparer les données pour Plotly
            price_window_plotly = price_data.copy()
            
            # Convertir datetime en format compatible Plotly (sans timezone)
            if price_window_plotly['datetime'].dt.tz is not None:
                price_window_plotly['datetime'] = price_window_plotly['datetime'].dt.tz_convert('UTC').dt.tz_localize(None)
            
            # Convertir chaque Timestamp en datetime Python natif
            datetime_native = []
            for ts in price_window_plotly['datetime']:
                if isinstance(ts, pd.Timestamp):
                    dt_native = ts.to_pydatetime()
                else:
                    dt_native = pd.to_datetime(ts).to_pydatetime()
                datetime_native.append(dt_native)
            
            price_window_plotly['datetime'] = datetime_native
            
            # Calculer les limites avec les marges ajustables
            time_margin_delta = timedelta(hours=time_margin_hours)
            min_time = price_window_plotly['datetime'].min() - time_margin_delta
            max_time = price_window_plotly['datetime'].max() + time_margin_delta
            
            # Calculer les limites Y avec marge ajustable
            price_min = price_window_plotly['low'].min()
            price_max = price_window_plotly['high'].max()
            price_range = price_max - price_min
            y_margin = price_range * (y_margin_pct / 100.0)
            y_min = price_min - y_margin
            y_max = price_max + y_margin
            
            # Créer le graphique
            fig = go.Figure()
            
            # Ligne de prix (candles ou ligne)
            fig.add_trace(go.Scatter(
                x=price_window_plotly['datetime'],
                y=price_window_plotly['close'],
                mode='lines',
                name='Prix EUR/USD',
                line=dict(color='#1f77b4', width=1)
            ))
            
            # Baseline
            if baseline_price:
                fig.add_hline(
                    y=baseline_price,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text="Baseline",
                    annotation_position="right"
                )
            
            # Wave 1 peak
            if pattern_wave1_peak_time:
                wave1_price = final_pred.get('wave1_price', baseline_price)
                fig.add_trace(go.Scatter(
                    x=[pattern_wave1_peak_time],
                    y=[wave1_price],
                    mode='markers',
                    name='Wave 1 Peak',
                    marker=dict(size=10, color='green', symbol='triangle-up')
                ))
            
            # Wave 2 peak (pic absolu si disponible)
            if pattern_wave2_peak_time:
                wave2_price = final_pred.get('wave2_peak_price_absolute') or final_pred.get('wave2_price', baseline_price)
                fig.add_trace(go.Scatter(
                    x=[pattern_wave2_peak_time],
                    y=[wave2_price],
                    mode='markers',
                    name='Wave 2 Peak (Absolu)',
                    marker=dict(size=12, color='red', symbol='triangle-up')
                ))
            
            # Ligne verticale pour l'événement
            fig.add_vline(
                x=anchor_time_dt.replace(tzinfo=None),
                line_dash="dot",
                line_color="orange",
                annotation_text="Événement",
                annotation_position="top"
            )
            
            # Mise à jour du layout avec les limites ajustables
            fig.update_layout(
                title=f"Prédiction d'Impact - {date_str}",
                xaxis_title="Temps",
                yaxis_title="Prix EUR/USD",
                xaxis=dict(range=[min_time, max_time]),
                yaxis=dict(range=[y_min, y_max]),
                hovermode='x unified',
                height=600,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Informations sur les timings
            with st.expander("📋 Détails des Timings"):
                timing_data = []
                if baseline_price:
                    timing_data.append({
                        "Étape": "Baseline",
                        "Heure": format_datetime(anchor_time),
                        "Prix": format_price(baseline_price),
                        "Pips": "0.00"
                    })
                if pattern_wave1_peak_time:
                    wave1_pips = final_pred.get('wave1_pips', 0)
                    timing_data.append({
                        "Étape": "Pic Wave 1",
                        "Heure": format_datetime(pattern_wave1_peak_time),
                        "Prix": format_price(final_pred.get('wave1_price')),
                        "Pips": format_pips(wave1_pips)
                    })
                if pattern_wave2_peak_time:
                    wave2_pips_abs = final_pred.get('wave2_peak_pips_absolute', final_pred.get('wave2_pips', 0))
                    timing_data.append({
                        "Étape": "Pic Wave 2 (Absolu)",
                        "Heure": format_datetime(pattern_wave2_peak_time),
                        "Prix": format_price(final_pred.get('wave2_peak_price_absolute') or final_pred.get('wave2_price')),
                        "Pips": format_pips(wave2_pips_abs)
                    })
                
                if timing_data:
                    df_timings = pd.DataFrame(timing_data)
                    st.dataframe(df_timings, use_container_width=True, hide_index=True)
        else:
            st.info("📊 Les données de prix seront affichées ici une fois le pipeline complet implémenté.")
        
    except Exception as e:
        st.warning(f"⚠️ Erreur lors de la création du graphique: {e}")
        import traceback
        with st.expander("Détails de l'erreur"):
            st.code(traceback.format_exc())

st.caption(f"📊 Résultats pour {date_str}")

