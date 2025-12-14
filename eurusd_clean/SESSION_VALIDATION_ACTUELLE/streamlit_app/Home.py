"""
EUR/USD News Impact Calculator - Home Page
===========================================

Version 4.0 - Nouvelle structure eurusd_clean
Utilise table prices_h1 (bougies horaires)

Stats améliorées:
- Événements (total, forecast, semaine, aujourd'hui)
- Dernière mise à jour Events
- Dernière mise à jour Prix
- Statut système
"""

import streamlit as st
import duckdb
from pathlib import Path
from datetime import datetime
import sys

# Imports nouvelle structure
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
import config

# Configuration page
st.set_page_config(
    page_title="EUR/USD Impact Calculator",
    page_icon="🏠",
    layout="wide"
)

# ══════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════

st.title("🏠 EUR/USD News Impact Calculator")
st.caption("Système d'analyse d'impact des événements macroéconomiques | Version 4.0")

# ══════════════════════════════════════════════════════════════════════
# CONNEXION DB
# ══════════════════════════════════════════════════════════════════════

if not config.DB_PATH.exists():
    st.error(f"❌ Base de données introuvable: {config.DB_PATH}")
    st.stop()

conn = duckdb.connect(str(config.DB_PATH), read_only=True)

# ══════════════════════════════════════════════════════════════════════
# STATISTIQUES ÉVÉNEMENTS (existantes)
# ══════════════════════════════════════════════════════════════════════

stats = conn.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(forecast) as with_forecast,
        COUNT(CASE WHEN ts_utc > CURRENT_TIMESTAMP THEN 1 END) as future,
        COUNT(CASE WHEN ts_utc > CURRENT_TIMESTAMP AND ts_utc < CURRENT_TIMESTAMP + INTERVAL '7 days' THEN 1 END) as week
    FROM events
    WHERE country IN ('US', 'EU', 'GB')
""").fetchone()

# Événements aujourd'hui
today_events = conn.execute("""
    SELECT COUNT(*)
    FROM events
    WHERE DATE(ts_utc) = CURRENT_DATE
      AND country IN ('US', 'EU', 'GB')
""").fetchone()[0]

# ══════════════════════════════════════════════════════════════════════
# NOUVELLES STATISTIQUES (améliorées)
# ══════════════════════════════════════════════════════════════════════

# Dernière màj events
last_event_update = conn.execute("""
    SELECT MAX(ts_utc) 
    FROM events 
    WHERE ts_utc < CURRENT_TIMESTAMP
""").fetchone()[0]

# Dernière màj prix (dernière bougie dans prices_h1)
last_price_update = conn.execute("""
    SELECT MAX(datetime)
    FROM prices_h1
""").fetchone()[0]

# Nombre de prix
price_count = conn.execute("""
    SELECT COUNT(*)
    FROM prices_h1
""").fetchone()[0]

# Vérifier table prices_h1
try:
    table_test = conn.execute("SELECT COUNT(*) FROM prices_h1").fetchone()[0]
    table_status = "✅ Active"
except:
    table_status = "❌ Erreur"

conn.close()

# ══════════════════════════════════════════════════════════════════════
# AFFICHAGE MÉTRIQUES
# ══════════════════════════════════════════════════════════════════════

st.subheader("📊 Événements Économiques")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Événements", 
        f"{stats[0]:,}", 
        help="Base complète US, EU, GB"
    )

with col2:
    st.metric(
        "Avec Forecast", 
        f"{stats[1]:,}", 
        delta=f"{stats[1]/stats[0]*100:.1f}%",
        help="Consensus de marché disponibles"
    )

with col3:
    st.metric(
        "Cette Semaine", 
        f"{stats[3]}", 
        help="Événements à venir dans 7 jours"
    )

with col4:
    st.metric(
        "Aujourd'hui", 
        f"{today_events}",
        help="Événements publiés aujourd'hui"
    )

# ══════════════════════════════════════════════════════════════════════
# NOUVELLES MÉTRIQUES (système)
# ══════════════════════════════════════════════════════════════════════

st.subheader("🔧 Statut Système")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if last_event_update:
        days_ago = (datetime.now().date() - last_event_update.date()).days
        st.metric(
            "Dernière màj Events",
            f"Il y a {days_ago}j",
            help=f"Dernier événement: {last_event_update.strftime('%Y-%m-%d')}"
        )
    else:
        st.metric("Dernière màj Events", "N/A")

with col2:
    if last_price_update:
        # Convertir en datetime Python si nécessaire
        if hasattr(last_price_update, 'to_pydatetime'):
            last_price_dt = last_price_update.to_pydatetime()
        else:
            last_price_dt = last_price_update
        
        if hasattr(last_price_dt, 'date'):
            days_ago = (datetime.now().date() - last_price_dt.date()).days
            st.metric(
                "Dernière màj Prix",
                f"Il y a {days_ago}j",
                help=f"Dernière bougie: {last_price_dt.strftime('%Y-%m-%d %H:%M')}"
            )
    else:
        st.metric("Dernière màj Prix", "N/A")

with col3:
    st.metric(
        "Prix disponibles",
        f"{price_count:,}",
        help="Bougies 1 heure dans prices_h1"
    )

with col4:
    st.metric(
        "Table prices_h1",
        table_status,
        help="Table principale des prix H1"
    )

# ══════════════════════════════════════════════════════════════════════
# PAGES D'ANALYSE
# ══════════════════════════════════════════════════════════════════════

st.subheader("📊 Pages d'Analyse")

col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown("### 📅 1. Calendrier Trading")
        st.markdown("**Objectif**: Liste événements à venir avec scores")
        st.markdown("**Utilisation**: Planifier semaine de trading")
        
    with st.container():
        st.markdown("### 🎯 2. Planificateur V2")
        st.markdown("**Objectif**: Prédire impact basé sur surprise")
        st.markdown("**Utilisation**: Analyser actual vs previous/forecast")

with col2:
    with st.container():
        st.markdown("### 🔧 3. API Status")
        st.markdown("**Objectif**: Tests connexion DB et clés API")
        st.markdown("**Utilisation**: Vérifier configuration système")
        
    with st.container():
        st.markdown("### 🔄 4. Mise à jour DB")
        st.markdown("**Objectif**: Actualiser Events et Prix")
        st.markdown("**Utilisation**: Mettre à jour données quotidiennement")

# ══════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════

st.markdown("---")
st.caption("EUR/USD News Impact Calculator v4.0 | Structure eurusd_clean | Session 112")
st.caption("✅ Table prices_h1 active - Bougies horaires")
