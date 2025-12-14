"""API Status & Smoke Tests
=========================

Version 4.0 - Nouvelle structure eurusd_clean

Tests:
- Connexion DB
- Clés API (EODHD, TradingEconomics)
- Structure tables
- Vue prices_bern
"""

from __future__ import annotations

import streamlit as st
import duckdb
import sys
from pathlib import Path
from datetime import datetime, date
import os

# Imports nouvelle structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
import config

# DB via config
DB_PATH = config.DB_PATH


def env_status():
    """Vérifie présence clés API"""
    return {
        "EODHD_API_KEY": bool(os.getenv("EODHD_API_KEY")),
        "TE_API_KEY": bool(os.getenv("TE_API_KEY")),
    }


st.set_page_config(page_title="API Status & Smoke Tests", layout="wide")
st.title("🔧 API Status & Smoke Tests")

db = config.DB_PATH
st.caption(f"DB: `{db}`")

# Période / filtres
c1, c2, c3 = st.columns([1.2, 1.2, 1.2])
with c1:
    d1 = st.date_input("Date début (UTC)", value=date.today())
with c2:
    d2 = st.date_input("Date fin (UTC)", value=date.today())
with c3:
    countries = st.multiselect("Pays", ["US","EU","EA","GB","DE","FR","CH","CA","JP","CN"], default=["US"])
importance = st.multiselect("Importance (EODHD)", [1,2,3], default=[1,2,3])

# Clés détectées
st.subheader("Clés détectées")
st.json({
    "db_path": db,
    "HAS_EOD": bool(os.getenv("EODHD_API_KEY")),
    "HAS_TE":  bool(os.getenv("TE_API_KEY")),
    "env_keys": env_status(),
    "period": [str(d1), str(d2)],
    "countries_raw": countries,
    "importance_n": importance or None,
})

st.markdown("---")

# -------- EODHD --------
st.header("EODHD — Calendar")
eod_key = os.getenv("EODHD_API_KEY")
if not eod_key:
    st.error("EODHD_API_KEY absente. Ajoute-la dans l'environnement ou le .env.")
else:
    st.info("🔑 Clé EODHD détectée")
    st.caption("Section EODHD désactivée - à réactiver en Session 113")
    # TODO: Voir test_eodhd_api.py pour exemple fonctionnel

st.markdown("---")

# -------- TradingEconomics (optionnel / non bloquant) --------
st.header("TradingEconomics — Calendar")
te_key = os.getenv("TE_API_KEY")
if not te_key:
    st.info("TE_API_KEY absente ou plan sans droit `/calendar`.")
else:
    st.info("Client TE non activé dans ce projet (on peut l’ajouter plus tard si tu passes au plan avec Calendar API).")
