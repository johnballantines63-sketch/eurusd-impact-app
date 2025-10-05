# fx_impact_app/streamlit_app/pages/0_Live-Calendar-Forecast.py
from __future__ import annotations
import pandas as pd
import streamlit as st
import duckdb
from datetime import date
from zoneinfo import ZoneInfo

# --- UI helpers (optionnel)
try:
    from fx_impact_app.streamlit_app.ui import apply_sidebar_index
except Exception:
    def apply_sidebar_index(_i:int): pass

# --- Config / Clients
from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.eodhd_client import (
    get_eod_key,
    fetch_calendar_json as eod_fetch,
    calendar_to_events_df as eod_norm,
    upsert_events,
)

st.set_page_config(page_title="Live Calendar (EODHD) — Ingestion & Preview", layout="wide")
apply_sidebar_index(0)

st.title("🗓️ Live Calendar — EODHD (ingestion & preview)")
st.caption(f"Loaded from: {__file__}")

# -----------------------------
# Helpers
# -----------------------------
def _fmt_local(ts, tz: str) -> str:
    if ts is None or (isinstance(ts, float) and pd.isna(ts)):
        return ""
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return t.tz_convert(ZoneInfo(tz)).strftime("%Y-%m-%d %H:%M:%S %Z")

def _expand_country_filter(sel: list[str]) -> set[str]:
    mapping = {
        "EU": {"EU", "EA"},   # Euro Area
        "EA": {"EU", "EA"},
        "UK": {"UK", "GB"},
        "GB": {"UK", "GB"},
        # autres => eux-mêmes
    }
    out = set()
    for c in (sel or []):
        c2 = str(c).strip().upper()
        out |= mapping.get(c2, {c2})
    return out

def _label_final(df: pd.DataFrame) -> pd.Series:
    # Priorité: event_title -> label -> type
    out = pd.Series(pd.NA, index=df.index, dtype="object")
    for c in ("event_title", "label", "type"):
        if c in df.columns:
            out = out.fillna(df[c].astype("string"))
    return out.fillna("").astype(str)

# -----------------------------
# UI
# -----------------------------
c0, c1, c2, c3 = st.columns([1.6, 1.6, 1.2, 3])
with c0:
    tz_name = st.selectbox(
        "Fuseau d’affichage",
        ["Europe/Zurich", "Europe/Paris", "UTC", "America/New_York", "Europe/London"],
        index=0,
    )
with c1:
    d = st.date_input("Jour (UTC)", value=date.today())
with c2:
    countries = st.multiselect("Pays", ["US","EU","EA","UK","GB","DE","FR","CH","JP","CA"], default=["US","EU"])
with c3:
    importance = st.multiselect("Importance (EODHD)", [1,2,3], default=[1,2,3])

c4, c5 = st.columns([1,1])
with c4:
    do_fetch = st.button("Récupérer", type="primary")
with c5:
    do_insert = st.button("Insérer en base", type="secondary")

# -----------------------------
# Action
# -----------------------------
df = pd.DataFrame()
diagnostics = {}

if do_fetch or do_insert:
    try:
        eod_key = get_eod_key()
        d1 = pd.Timestamp(d).strftime("%Y-%m-%d")
        d2 = pd.Timestamp(d).strftime("%Y-%m-%d")

        raw = eod_fetch(d1, d2, countries=countries or None, importance=importance or None, api_key=eod_key)
        diagnostics["received_rows"] = len(raw)

        if raw:
            df = eod_norm(raw).copy()

            # Numériques
            for cnum in ("estimate", "forecast", "previous", "actual"):
                if cnum in df.columns:
                    df[cnum] = pd.to_numeric(df[cnum], errors="coerce")

            # Pays en upper
            if "country" in df.columns:
                df["country"] = df["country"].astype(str).str.upper()

            # Label final pour l'affichage
            df["label_final"] = _label_final(df)

            # Timestamp local lisible
            if "ts_utc" in df.columns:
                df["ts_local"] = df["ts_utc"].apply(lambda t: _fmt_local(t, tz_name))

            # Importance locale (si besoin)
            if "importance_n" in df.columns and importance:
                df = df[df["importance_n"].isin(importance)]

            # 🔒 Filtre pays STRICT à la fin (gère EU⇔EA, UK⇔GB)
            allowed = _expand_country_filter(countries)
            if "country" in df.columns and allowed:
                before = len(df)
                df = df[df["country"].astype(str).str.upper().isin(allowed)]
                diagnostics["after_country_strict"] = {"kept": int(len(df)), "dropped": int(before - len(df))}
                diagnostics["countries_shown"] = sorted(df["country"].dropna().astype(str).str.upper().unique().tolist())

        else:
            st.info("Aucun élément renvoyé par EODHD pour la fenêtre/pays donnés.")

    except Exception as e:
        st.error("Erreur pendant la récupération/normalisation.")
        st.exception(e)

# -----------------------------
# Preview & Export
# -----------------------------
if not df.empty:
    st.subheader("Aperçu normalisé")
    view_cols = [c for c in ["ts_local","ts_utc","country","label_final","event_title","event_key","type","estimate","forecast","previous","unit","importance_n"] if c in df.columns]
    st.dataframe(df[view_cols], width="stretch", hide_index=True)

    st.download_button(
        "Exporter CSV (normalisé)",
        data=df[view_cols].to_csv(index=False).encode("utf-8"),
        file_name=f"eodhd_calendar_{d1}.csv",
        mime="text/csv",
    )

# -----------------------------
# Insert
# -----------------------------
if do_insert and not df.empty:
    try:
        with duckdb.connect(get_db_path()) as con:
            n_before = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            upsert_events(con, df)  # gère les colonnes manquantes et types
            n_after = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        st.success(f"✅ Insertion OK — {n_after - n_before} ligne(s) ajoutée(s)/fusionnée(s).")
    except Exception as e:
        st.error("Insertion en base échouée.")
        st.exception(e)

# -----------------------------
# Diagnostics
# -----------------------------
with st.expander("Diagnostics"):
    diagnostics.update({
        "db_path": get_db_path(),
        "period": [str(d1), str(d2)],
        "tz": tz_name,
        "countries": countries,
        "importance": importance or None,
    })
    st.json(diagnostics)
