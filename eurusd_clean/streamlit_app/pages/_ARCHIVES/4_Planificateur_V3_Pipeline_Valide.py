"""
PLANIFICATEUR V3.0 - PIPELINE VALIDÉ
=====================================

Version 3.0 - Utilise le pipeline complet validé (PipelineExecutor)
Architecture propre et simple, basée sur le pipeline testé et validé

Ce planificateur utilise directement :
- scripts/run_pipeline_complete.py (PipelineExecutor)
- Pipeline complet en 8 étapes
- Détection de patterns avec phase_a_robust_validation
- Prédictions avec Random Forest
- Stratégie de sortie optimisée
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

# Import pandas explicitement pour les conversions
pd = pd

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

import config

# Import PipelineExecutor
spec = importlib.util.spec_from_file_location(
    "run_pipeline_complete",
    PROJECT_ROOT / "scripts" / "run_pipeline_complete.py"
)
run_pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_pipeline)
PipelineExecutor = run_pipeline.PipelineExecutor

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

# Main content
date_str = date_input.strftime('%Y-%m-%d')

# Vérifier si on a déjà des résultats en cache pour cette date
cache_key = f"pipeline_result_{date_str}"
cached_result = st.session_state.get(cache_key)

# Bouton pour lancer la prédiction
if st.button("🚀 Lancer la Prédiction", type="primary", use_container_width=True):
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
    st.info("ℹ️ Affichage des résultats en cache.")
else:
    # Pas de résultats, afficher un message
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

st.caption(f"📊 Résultats pour {date_str}")

