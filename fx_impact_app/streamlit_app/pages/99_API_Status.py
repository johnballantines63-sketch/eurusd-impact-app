# fx_impact_app/streamlit_app/pages/99_API_Status.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import date
from typing import Any, Dict, List

from fx_impact_app.src.config import get_db_path, get_eod_key, get_te_key, env_status
from fx_impact_app.src.eodhd_client import (
    fetch_calendar_json as eod_fetch,
    calendar_to_events_df as eod_norm,
    upsert_events_df as eod_upsert,
)

st.set_page_config(page_title="API Status & Smoke Tests", layout="wide")
st.title("🔧 API Status & Smoke Tests")

db = get_db_path()
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
    "HAS_EOD": bool(get_eod_key()),
    "HAS_TE":  bool(get_te_key()),
    "env_keys": env_status(),
    "period": [str(d1), str(d2)],
    "countries_raw": countries,
    "importance_eod": importance or None,
})

st.markdown("---")

# -------- EODHD --------
st.header("EODHD — Calendar")
eod_key = get_eod_key()
if not eod_key:
    st.error("EODHD_API_KEY absente. Ajoute-la dans l'environnement ou le .env.")
else:
    try:
        items: List[Dict[str,Any]] = eod_fetch(d1, d2,
                                               countries=countries or None,
                                               importance=importance or None,
                                               api_key=eod_key)
        st.success(f"Réception EODHD OK — {len(items)} éléments bruts.")
        df = eod_norm(items)
        st.caption(f"Normalisés: {len(df)}")
        if not df.empty:
            df = df.sort_values("ts_utc", kind="stable")
            # fuseau
            tz = st.selectbox("Fuseau d’affichage", ["UTC","Europe/Zurich","Europe/Paris","America/New_York"], index=1)
            def _fmt_local(ts):
                t = pd.Timestamp(ts)
                if t.tzinfo is None:
                    t = t.tz_localize("UTC")
                return t.tz_convert(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
            df["ts_local"] = df["ts_utc"].apply(_fmt_local)

            desired = ["ts_local","ts_utc","country","event_title","event_key","label",
                       "estimate","forecast","previous","actual","unit","type","importance_n"]
            present = [c for c in desired if c in df.columns]
            st.dataframe(df[present], use_container_width=True)

            cexp1, cexp2 = st.columns(2)
            with cexp1:
                st.download_button("Export CSV (EODHD normalisé)",
                                   data=df[present].to_csv(index=False).encode("utf-8"),
                                   file_name=f"eodhd_{d1}_{d2}.csv",
                                   mime="text/csv")
            with cexp2:
                if st.button("Insérer dans `events` (UPSERT)"):
                    n = eod_upsert(df, db_path=db)
                    st.success(f"Upsert terminé — lignes traitées : {n}")
        else:
            st.info("Aucun élément renvoyé par EODHD pour la fenêtre/pays donnés.")
    except Exception as e:
        st.error(f"EODHD — erreur: {e}")

st.markdown("---")

# -------- TradingEconomics (optionnel / non bloquant) --------
st.header("TradingEconomics — Calendar")
te_key = get_te_key()
if not te_key:
    st.info("TE_API_KEY absente ou plan sans droit `/calendar`.")
else:
    st.info("Client TE non activé dans ce projet (on peut l’ajouter plus tard si tu passes au plan avec Calendar API).")
