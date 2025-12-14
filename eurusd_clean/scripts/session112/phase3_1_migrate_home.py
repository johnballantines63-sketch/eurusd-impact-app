#!/usr/bin/env python3
"""
MIGRATION HOME PAGE - Phase 3
==============================

Migre Home.py vers nouvelle structure avec stats améliorées.

MODIFICATIONS:
1. Imports adaptés à nouvelle structure
2. Utilise config.py pour DB
3. Utilise prices_bern (vue)
4. Ajoute nouvelles stats (dernière màj, etc.)

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 3
"""

from pathlib import Path
import shutil

print("="*80)
print("📱 MIGRATION HOME PAGE")
print("="*80)

# Chemins
source_home = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/Home.py")
target_home = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/streamlit_app/Home.py")

print(f"\n📋 Source: {source_home.name}")
print(f"📋 Cible: streamlit_app/Home.py")

if not source_home.exists():
    print(f"\n❌ Source introuvable: {source_home}")
    exit(1)

# ══════════════════════════════════════════════════════════════════════
# CONFIRMATION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("⚠️ CONFIRMATION")
print("="*80)

print(f"""
Cette migration va:
  1. Copier Home.py
  2. Adapter imports (nouvelle structure)
  3. Utiliser config.py pour DB
  4. Ajouter nouvelles stats:
     • Dernière màj Events
     • Dernière màj Prix
     • Statut vue prices_bern
     • Nombre de prix
""")

proceed = input("\n👉 Migrer Home.py ? (oui/non): ").strip().lower()

if proceed != "oui":
    print("\n❌ Migration annulée")
    exit(0)

# ══════════════════════════════════════════════════════════════════════
# CRÉATION HOME ADAPTÉ
# ══════════════════════════════════════════════════════════════════════

print("\n🔧 Création Home.py adapté...")

home_content = '''"""
EUR/USD News Impact Calculator - Home Page
===========================================

Version 4.0 - Nouvelle structure eurusd_clean
Utilise vue prices_bern (logique timezone pure)

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

# Dernière màj prix (dernière bougie dans prices_bern)
last_price_update = conn.execute("""
    SELECT MAX(datetime)
    FROM prices_bern
""").fetchone()[0]

# Nombre de prix
price_count = conn.execute("""
    SELECT COUNT(*)
    FROM prices_bern
""").fetchone()[0]

# Vérifier vue prices_bern
try:
    vue_test = conn.execute("SELECT COUNT(*) FROM prices_bern").fetchone()[0]
    vue_status = "✅ Active"
except:
    vue_status = "❌ Erreur"

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
        help="Bougies 1 minute dans prices_bern"
    )

with col4:
    st.metric(
        "Vue prices_bern",
        vue_status,
        help="Vue timezone correcte (Event 14:30 = Prix 14:30)"
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
st.caption("✅ Vue prices_bern active - Logique timezone pure (Event 14:30 = Prix 14:30)")
'''

# Écrire fichier
target_home.write_text(home_content)

print(f"✅ Home.py créé")
print(f"   Emplacement: {target_home.relative_to(target_home.parent.parent)}")
print(f"   Taille: {target_home.stat().st_size / 1024:.1f} KB")

# ══════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("✅ MIGRATION HOME TERMINÉE")
print("="*80)

print(f"""
📋 Modifications appliquées:
  ✅ Imports adaptés (config.py)
  ✅ Utilise prices_bern (vue)
  ✅ Stats existantes conservées
  ✅ Nouvelles stats ajoutées:
     • Dernière màj Events
     • Dernière màj Prix
     • Nombre prix
     • Statut vue prices_bern
  ✅ Pages d'analyse listées

🚀 Test:
  cd eurusd_clean
  streamlit run streamlit_app/Home.py
""")

print("="*80)
