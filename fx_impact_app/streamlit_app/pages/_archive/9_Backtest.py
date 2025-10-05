
from __future__ import annotations
import streamlit as st, pandas as pd, duckdb
from datetime import date
from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.presets import PRESETS, by_label
from fx_impact_app.src.forecaster_mvp import ForecastRequest, forecast, HORIZONS

st.set_page_config(page_title="Backtest — V5", layout="wide")
st.title("📊 Backtest — V5 (simplifié)")

preset_label = st.selectbox("Preset", [p.label for p in PRESETS], index=0)
preset = by_label(preset_label)
tz = st.selectbox("Fuseau d'affichage", ["Europe/Paris","Europe/Zurich","UTC","America/New_York"], index=1)
jour = st.date_input("Jour", value=date.today())

if st.button("Charger les events du jour", type="primary"):
    try:
        with duckdb.connect(get_db_path()) as con:
            start = pd.Timestamp(jour).tz_localize(tz).tz_convert("UTC").to_pydatetime()
            end   = (pd.Timestamp(jour)+pd.Timedelta(days=1)).tz_localize(tz).tz_convert("UTC").to_pydatetime()
            cols = {r[1] for r in con.execute("PRAGMA table_info('events')").fetchall()}
            sel = ["ts_utc"]
            for c in ["country","event_title","event_key","previous","estimate","forecast","unit","actual"]:
                if c in cols: sel.append(c)
            q = f"SELECT {', '.join(sel)} FROM events WHERE ts_utc BETWEEN ? AND ?"
            params=[start, end]
            if preset.countries and "country" in cols:
                q += " AND country IN (" + ",".join(["?"]*len(preset.countries)) + ")"; params += preset.countries
            if preset.include_regex:
                parts=[]
                if "event_key" in cols:   parts.append("regexp_matches(lower(event_key), ?)")
                if "event_title" in cols: parts.append("regexp_matches(lower(event_title), ?)")
                if parts: q += " AND (" + " OR ".join(parts) + ")"; params += [preset.include_regex]*len(parts)
            q += " ORDER BY ts_utc"
            df = con.execute(q, params).df()
        if df.empty: st.warning("Aucun événement."); st.stop()
        df["consensus"] = df.get("estimate") if "estimate" in df.columns else df.get("forecast")
        st.session_state["bt_df"] = df
        st.success(f"{len(df)} events chargés.")
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.exception(e)

df_bt = st.session_state.get("bt_df")
if df_bt is not None and not df_bt.empty:
    st.subheader("Simuler un pronostic pour le 1er event")
    row = df_bt.iloc[0]
    actual = float(row.get("actual") or 0.0)
    consensus = float(row.get("consensus") or 0.0)
    req = ForecastRequest("NFP", actual, consensus, country=(row.get("country") or "US"))
    if st.button("Calculer le pronostic de test"):
        stats, diags = forecast(req, db_path=get_db_path())
        st.json({"n_events_hist": diags.get("hist_n")})
