"""
Mise à Jour Base de Données
============================

Version 4.0 - Nouvelle structure eurusd_clean

Fonctionnalités:
1. Mettre à jour Events (EODHD + corrections)
2. Mettre à jour Prix (Dukascopy EUR/USD 1min)
3. Vérifier statut DB
4. Logs en temps réel

Utilise scripts existants:
- eodhd_client_FULL_IMPORT_20251019_135735.py
- fix_eodhd_estimate_session28.py  
- dukascopy_eurusd_m1_3y.py
"""

import streamlit as st
import sys
from pathlib import Path
import subprocess
from datetime import datetime
import duckdb

# Imports nouvelle structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
import config

# Configuration
st.set_page_config(
    page_title="Mise à jour DB",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 Mise à Jour Base de Données")
st.caption("Actualisation Events et Prix | Version 4.0")

# Chemins scripts
project_root = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")
script_eodhd = project_root / "eodhd_client_FULL_IMPORT_20251019_135735.py"
script_fix = project_root / "fix_eodhd_estimate_session28.py"
script_dukascopy = project_root / "dukascopy_eurusd_m1_3y.py"

# ══════════════════════════════════════════════════════════════════════
# STATUT DB ACTUEL
# ══════════════════════════════════════════════════════════════════════

st.subheader("📊 Statut Actuel")

if config.DB_PATH.exists():
    conn = duckdb.connect(str(config.DB_PATH), read_only=True)
    
    # Stats events
    events_stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(ts_utc) as first_event,
            MAX(ts_utc) as last_event
        FROM events
    """).fetchone()
    
    # Stats prix
    price_stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            MIN(datetime) as first_price,
            MAX(datetime) as last_price
        FROM prices_bern
    """).fetchone()
    
    conn.close()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Events", f"{events_stats[0]:,}")
        if events_stats[1] and events_stats[2]:
            st.caption(f"Du {events_stats[1]} au {events_stats[2]}")
    
    with col2:
        st.metric("Prix (bougies 1min)", f"{price_stats[0]:,}")
        if price_stats[1] and price_stats[2]:
            st.caption(f"Du {price_stats[1]} au {price_stats[2]}")
            
            # Calculer âge dernière bougie
            if hasattr(price_stats[2], 'to_pydatetime'):
                last_dt = price_stats[2].to_pydatetime()
            else:
                last_dt = price_stats[2]
            
            if hasattr(last_dt, 'date'):
                days_old = (datetime.now().date() - last_dt.date()).days
                if days_old > 1:
                    st.warning(f"⚠️ Prix datent de {days_old} jours")
else:
    st.error("❌ DB introuvable")

# ══════════════════════════════════════════════════════════════════════
# MISE À JOUR EVENTS
# ══════════════════════════════════════════════════════════════════════

st.subheader("📅 Mise à jour Events")

st.info("""
**Process:**
1. Import EODHD (API économique)
2. Application corrections estimates
3. Insertion dans DB
""")

col1, col2 = st.columns([1, 3])

with col1:
    if st.button("🔄 Mettre à jour Events", type="primary"):
        with col2:
            with st.spinner("Import EODHD en cours..."):
                # Vérifier scripts
                if not script_eodhd.exists():
                    st.error(f"❌ Script EODHD introuvable: {script_eodhd.name}")
                elif not script_fix.exists():
                    st.error(f"❌ Script corrections introuvable: {script_fix.name}")
                else:
                    # Logs container
                    log_container = st.empty()
                    
                    try:
                        # 1. Import EODHD
                        log_container.text("1/2 Import EODHD...")
                        result = subprocess.run(
                            ["python3", str(script_eodhd)],
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        
                        if result.returncode == 0:
                            st.success("✅ Import EODHD réussi")
                            
                            # 2. Corrections
                            log_container.text("2/2 Application corrections...")
                            result2 = subprocess.run(
                                ["python3", str(script_fix)],
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            
                            if result2.returncode == 0:
                                st.success("✅ Corrections appliquées")
                                st.balloons()
                                st.info("🔄 Rechargez la page pour voir les nouvelles stats")
                            else:
                                st.error(f"❌ Erreur corrections: {result2.stderr}")
                        else:
                            st.error(f"❌ Erreur import: {result.stderr}")
                            
                    except subprocess.TimeoutExpired:
                        st.error("❌ Timeout (>5min)")
                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")

with col2:
    if script_eodhd.exists():
        st.caption(f"✅ Script EODHD: {script_eodhd.name}")
    else:
        st.caption(f"❌ Script EODHD introuvable")
    
    if script_fix.exists():
        st.caption(f"✅ Script corrections: {script_fix.name}")
    else:
        st.caption(f"❌ Script corrections introuvable")

# ══════════════════════════════════════════════════════════════════════
# MISE À JOUR PRIX
# ══════════════════════════════════════════════════════════════════════

st.subheader("💹 Mise à jour Prix")

st.info("""
**Process:**
1. Téléchargement Dukascopy (EUR/USD 1min)
2. Import dans prices_1m
3. Vue prices_bern se met à jour automatiquement
""")

col1, col2 = st.columns([1, 3])

with col1:
    if st.button("🔄 Mettre à jour Prix", type="primary"):
        with col2:
            with st.spinner("Import Dukascopy en cours..."):
                if not script_dukascopy.exists():
                    st.error(f"❌ Script Dukascopy introuvable: {script_dukascopy.name}")
                else:
                    log_container = st.empty()
                    
                    try:
                        log_container.text("Import prix en cours (peut prendre 5-10min)...")
                        result = subprocess.run(
                            ["python3", str(script_dukascopy)],
                            capture_output=True,
                            text=True,
                            timeout=900  # 15 min max
                        )
                        
                        if result.returncode == 0:
                            st.success("✅ Import prix réussi")
                            st.balloons()
                            st.info("🔄 Rechargez la page pour voir les nouvelles stats")
                        else:
                            st.error(f"❌ Erreur: {result.stderr}")
                            
                    except subprocess.TimeoutExpired:
                        st.error("❌ Timeout (>15min)")
                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")

with col2:
    if script_dukascopy.exists():
        st.caption(f"✅ Script Dukascopy: {script_dukascopy.name}")
    else:
        st.caption(f"❌ Script Dukascopy introuvable")

# ══════════════════════════════════════════════════════════════════════
# NOTES
# ══════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("📋 Notes")

st.markdown("""
**Fréquence recommandée:**
- Events: Quotidien (le matin)
- Prix: Quotidien (après clôture marchés)

**Durées typiques:**
- Import Events: 2-3 minutes
- Import Prix: 5-10 minutes

**Important:**
- Vérifier clés API dans environnement
- Vue `prices_bern` se met à jour automatiquement
- Pas besoin de recréer la vue après màj prix
""")

st.caption("Mise à jour DB v1.0 | Session 112")
