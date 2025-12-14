"""
Page Streamlit - Mise à Jour des Données Finnhub
==================================================

Permet de mettre à jour automatiquement :
- Prix EUR/USD M1 jusqu'à aujourd'hui
- Événements économiques (7 jours passés → 30 jours futurs)

Date : 2025-12-07
"""

import sys
from pathlib import Path
import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime, timedelta

# Ajouter chemins
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'streamlit_app' / 'utils'))

from utils.finnhub_data_refresh import (
    check_price_freshness,
    check_events_freshness,
    refresh_prices,
    refresh_events,
    refresh_all_data
)

st.set_page_config(
    page_title="Mise à Jour Données",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 Mise à Jour des Données Finnhub")
st.caption("Mettez à jour les prix et événements pour rester à jour")

# Configuration
DB_PATH = Path('../fx_impact_app/data/warehouse.duckdb')

# Vérifier état actuel
st.subheader("📊 État Actuel des Données")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Prix EUR/USD")
    last_price_date, price_age_hours = check_price_freshness()
    
    if last_price_date:
        st.metric(
            "Dernière date",
            last_price_date.strftime('%Y-%m-%d %H:%M') if hasattr(last_price_date, 'strftime') else str(last_price_date),
            delta=f"{price_age_hours:.1f} heures" if price_age_hours else None
        )
        
        if price_age_hours:
            if price_age_hours < 24:
                st.success("✅ Prix à jour (moins de 24h)")
            elif price_age_hours < 48:
                st.warning(f"⚠️ Prix datent de {price_age_hours:.1f} heures")
            else:
                st.error(f"❌ Prix obsolètes ({price_age_hours:.1f} heures)")
    else:
        st.error("❌ Aucune donnée prix disponible")

with col2:
    st.markdown("### Événements Économiques")
    last_event_date, days_ahead = check_events_freshness()
    
    if last_event_date:
        st.metric(
            "Dernier événement futur",
            last_event_date.strftime('%Y-%m-%d %H:%M') if hasattr(last_event_date, 'strftime') else str(last_event_date),
            delta=f"{days_ahead} jours futurs" if days_ahead else None
        )
        
        if days_ahead:
            if days_ahead >= 30:
                st.success(f"✅ Événements jusqu'à {days_ahead} jours")
            elif days_ahead >= 7:
                st.warning(f"⚠️ Événements jusqu'à {days_ahead} jours")
            else:
                st.error(f"❌ Seulement {days_ahead} jours d'événements")
    else:
        st.warning("⚠️ Aucun événement futur disponible")

st.divider()

# Actions de mise à jour
st.subheader("🔄 Mise à Jour")

tab1, tab2, tab3 = st.tabs(["🔄 Tout mettre à jour", "📈 Prix uniquement", "📅 Événements uniquement"])

with tab1:
    st.markdown("**Met à jour prix ET événements**")
    st.caption("Cela peut prendre quelques minutes selon la quantité de données à importer")
    
    if st.button("🔄 Mettre à jour TOUT", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress, message):
            progress_bar.progress(progress)
            status_text.text(message)
        
        try:
            results = refresh_all_data(progress_callback=progress_callback)
            
            progress_bar.progress(1.0)
            
            if results['success']:
                st.success("✅ Mise à jour complète terminée avec succès")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if results['prices']:
                        st.info(f"📈 Prix : {results['prices'].get('message', 'Terminé')}")
                with col_b:
                    if results['events']:
                        st.info(f"📅 Événements : {results['events'].get('message', 'Terminé')}")
            else:
                st.error("❌ Mise à jour terminée avec des erreurs")
                
                if results.get('prices') and not results['prices'].get('success'):
                    st.error(f"Prix : {results['prices'].get('message')}")
                if results.get('events') and not results['events'].get('success'):
                    st.error(f"Événements : {results['events'].get('message')}")
        
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")
            import traceback
            st.code(traceback.format_exc())

with tab2:
    st.markdown("**Met à jour uniquement les prix EUR/USD M1**")
    
    if st.button("📈 Mettre à jour PRIX", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress, message):
            progress_bar.progress(progress)
            status_text.text(message)
        
        try:
            result = refresh_prices(progress_callback=progress_callback)
            
            progress_bar.progress(1.0)
            
            if result['success']:
                st.success(f"✅ {result['message']}")
                if result.get('prices_added', 0) > 0:
                    st.info(f"📊 {result['prices_added']:,} chandeliers ajoutés")
            else:
                st.error(f"❌ {result['message']}")
        
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

with tab3:
    st.markdown("**Met à jour uniquement les événements économiques**")
    st.caption("Période : 7 jours passés → 30 jours futurs")
    
    if st.button("📅 Mettre à jour ÉVÉNEMENTS", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress, message):
            progress_bar.progress(progress)
            status_text.text(message)
        
        try:
            result = refresh_events(progress_callback=progress_callback)
            
            progress_bar.progress(1.0)
            
            if result['success']:
                st.success(f"✅ {result['message']}")
                if result.get('events_count', 0) > 0:
                    st.info(f"📊 {result['events_count']:,} événements disponibles")
            else:
                st.error(f"❌ {result['message']}")
        
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

st.divider()

# Statistiques après mise à jour
if st.button("🔄 Actualiser les statistiques"):
    st.rerun()

# Afficher statistiques détaillées
st.subheader("📊 Statistiques Détaillées")

try:
    if DB_PATH.exists():
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Prix")
            try:
                stats_prices = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        MIN(ts_utc) as min_date,
                        MAX(ts_utc) as max_date
                    FROM prices_1m_v
                """).fetchone()
                
                st.metric("Total chandeliers", f"{stats_prices[0]:,}")
                st.caption(f"Plage : {stats_prices[1]} → {stats_prices[2]}")
            except Exception as e:
                st.error(f"Erreur : {e}")
        
        with col2:
            st.markdown("#### Événements")
            try:
                stats_events = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(DISTINCT DATE(ts_utc)) as jours,
                        MIN(ts_utc) as min_date,
                        MAX(ts_utc) as max_date
                    FROM events
                """).fetchone()
                
                st.metric("Total événements", f"{stats_events[0]:,}")
                st.caption(f"{stats_events[1]} jours | Plage : {stats_events[2]} → {stats_events[3]}")
            except Exception as e:
                st.error(f"Erreur : {e}")
        
        conn.close()
    else:
        st.error(f"Base de données introuvable : {DB_PATH}")

except Exception as e:
    st.error(f"Erreur lors de la lecture des statistiques : {e}")


