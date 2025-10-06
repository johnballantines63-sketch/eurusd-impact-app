#!/usr/bin/env python3
"""
Page d'accueil EUR/USD News Impact Calculator
Dashboard principal avec accès rapide aux 5 pages essentielles
"""
"""
EUR/USD News Impact Calculator - Home Page
"""
import sys
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Télécharger la base de données depuis Google Drive si nécessaire
try:
    from download_database import download_database
    download_database()
except Exception as e:
    import streamlit as st
    st.error(f"❌ Erreur lors du téléchargement de la base de données: {e}")
    st.info("Vérifiez que GDRIVE_DB_FILE_ID est configuré dans les secrets Streamlit")
    st.stop()

# Imports originaux ci-dessous


import streamlit as st
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Ajouter le chemin parent pour imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configuration
st.set_page_config(
    page_title="EUR/USD Impact Calculator",
    page_icon="🏠",
    layout="wide"
)

# Chemins relatifs depuis la racine du projet
project_root = Path(__file__).parent.parent.parent
DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"

# Header
st.title("🏠 EUR/USD News Impact Calculator")
st.caption("Système d'analyse d'impact des événements macroéconomiques | Version 3.0")

# Statistiques globales
if DB_PATH.exists():
    conn = duckdb.connect(str(DB_PATH))
    
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
    
    conn.close()
    
    # Afficher métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Événements", f"{stats[0]:,}", 
                  help="Base complète US, EU, GB")
    
    with col2:
        st.metric("Avec Forecast", f"{stats[1]:,}", 
                  delta=f"{stats[1]/stats[0]*100:.1f}%",
                  help="Consensus de marché disponibles")
    
    with col3:
        st.metric("Cette Semaine", f"{stats[3]}", 
                  help="Événements à venir dans 7 jours")
    
    with col4:
        st.metric("Aujourd'hui", f"{today_events}",
                  help="Événements publiés aujourd'hui")

else:
    st.error("Base de données non trouvée - Vérifiez l'installation")

st.divider()

# Navigation rapide
st.header("📊 Pages d'Analyse")

# Grille 2x3
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ Impact Planner")
    st.write("**Objectif** : Scorer les familles d'événements (NFP, CPI, etc.)")
    st.write("**Utilisation** : Identifier événements à surveiller")
    
    if st.button("🎯 Ouvrir Impact Planner", use_container_width=True):
        st.switch_page("pages/0b_Impact-Planner.py")
    
    st.caption("Score composite 0-100 | Grades A+ à D | Impact/Latence/TTR")
    
    st.write("")
    st.subheader("2️⃣ Calendrier Trading")
    st.write("**Objectif** : Liste événements à venir avec scores")
    st.write("**Utilisation** : Planifier semaine de trading")
    
    if st.button("📅 Ouvrir Calendrier", use_container_width=True):
        st.switch_page("pages/1_Calendrier-Trading.py")
    
    st.caption("Filtres période/pays/score | Export CSV watchlist")
    
    st.write("")
    st.subheader("3️⃣ Backtest Stratégie")
    st.write("**Objectif** : Tester stratégie sur historique")
    st.write("**Utilisation** : Valider paramètres TP/SL")
    
    if st.button("📈 Ouvrir Backtest", use_container_width=True):
        st.switch_page("pages/2_Backtest-Strategie.py")
    
    st.caption("Win rate | P&L | Drawdown | Simulations réalistes")

with col2:
    st.subheader("4️⃣ Analyseur Surprise")
    st.write("**Objectif** : Prédire impact basé sur surprise")
    st.write("**Utilisation** : Analyser actual vs previous/forecast")
    
    if st.button("🔍 Ouvrir Analyseur", use_container_width=True):
        st.switch_page("pages/3_Analyseur-Surprise.py")
    
    st.caption("Surprise = Actual - Previous | Impact estimé en pips")
    
    st.write("")
    st.subheader("5️⃣ Multi-Événements")
    st.write("**Objectif** : Gérer événements simultanés")
    st.write("**Utilisation** : Jour NFP (5+ événements à 14:30)")
    
    if st.button("🎲 Ouvrir Planificateur", use_container_width=True):
        st.switch_page("pages/4_Planificateur-Multi-Evenements.py")
    
    st.caption("Méthode vectorielle | Impact combiné | Latence/TTR pondérés")

st.divider()

# Outils de gestion
st.header("🛠️ Outils de Gestion")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Gestion Forecast")
    st.write("Saisie manuelle des consensus pour événements majeurs")
    st.code("streamlit run manual_forecast_form_fixed.py", language="bash")
    st.caption("3-4 événements/semaine | Investing.com → Base de données")

with col2:
    st.subheader("🔄 Auto-Update Actual")
    st.write("Mise à jour automatique valeurs publiées")
    st.code("python auto_update_actuals.py window 14 16", language="bash")
    st.caption("Mode fenêtre pour jour NFP | Polling EODHD toutes les 5 min")

st.divider()

# Événements à venir (aperçu)
st.header("📅 Aperçu Semaine Prochaine")

if DB_PATH.exists():
    conn = duckdb.connect(str(DB_PATH))
    
    upcoming = conn.execute("""
        SELECT 
            ts_utc,
            event_key,
            country,
            forecast,
            previous
        FROM events
        WHERE ts_utc > CURRENT_TIMESTAMP
          AND ts_utc < CURRENT_TIMESTAMP + INTERVAL '7 days'
          AND country IN ('US', 'EU', 'GB')
          AND (
              event_key LIKE '%farm payroll%'
              OR event_key LIKE '%cpi%'
              OR event_key LIKE '%unemployment%'
              OR event_key LIKE '%gdp%'
              OR event_key LIKE '%fomc%'
              OR event_key LIKE '%ecb%'
          )
        ORDER BY ts_utc
        LIMIT 10
    """).fetchdf()
    
    conn.close()
    
    if not upcoming.empty:
        # Formater pour affichage propre
        upcoming_display = upcoming.copy()
        upcoming_display['ts_utc'] = upcoming_display['ts_utc'].dt.strftime('%d/%m/%Y %H:%M')
        
        st.dataframe(
            upcoming_display,
            use_container_width=True,
            column_config={
                "ts_utc": "Date/Heure",
                "event_key": "Événement",
                "country": "Pays",
                "forecast": st.column_config.NumberColumn("Forecast", format="%.2f"),
                "previous": st.column_config.NumberColumn("Previous", format="%.2f"),
            },
            hide_index=True
        )
        
        if upcoming['forecast'].isna().sum() > 0:
            missing = upcoming['forecast'].isna().sum()
            st.warning(f"⚠️ {missing} événement(s) sans forecast - Complétez via le formulaire")
    else:
        st.info("Aucun événement majeur prévu dans les 7 prochains jours")

st.divider()

# Workflow recommandé
with st.expander("💡 Workflow Recommandé"):
    st.markdown("""
    ### Dimanche Soir (15 min)
    1. Consulter Investing.com calendrier
    2. Lancer formulaire forecast pour 3-4 événements majeurs
    3. Ouvrir **Calendrier Trading** pour watchlist semaine
    
    ### Jeudi Soir avant NFP (10 min)
    1. Vérifier forecast NFP sur Investing.com
    2. Ouvrir **Planificateur Multi-Événements**
    3. Analyser impact combiné NFP + Unemployment
    4. Noter : Entry timing, TP, SL, Exit au TTR
    
    ### Vendredi NFP (Automatique)
    1. Lancer `auto_update_actuals.py window 14 16`
    2. Laisser tourner en background
    3. Actual mis à jour automatiquement après publication
    
    ### Fin de Mois (20 min)
    1. Ouvrir **Backtest Stratégie**
    2. Période : 6 derniers mois
    3. Analyser win rate, P&L, drawdown
    4. Ajuster paramètres si nécessaire
    """)

# Footer
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("**Version** : 3.0 (Octobre 2025)")

with col2:
    st.caption("**Base** : 31,988 événements (2022-2026)")

with col3:
    if st.button("📚 Mode d'Emploi Complet"):
        st.info("Consultez `Mode d'Emploi - EUR/USD Impact Calculator.md`")
