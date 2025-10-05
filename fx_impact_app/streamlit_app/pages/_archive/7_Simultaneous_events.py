
from __future__ import annotations
import streamlit as st, pandas as pd, duckdb
from datetime import date
from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.presets import PRESETS, by_label

st.set_page_config(page_title="Simultaneous events — V5", layout="wide")
st.title("🔗 Simultaneous events — V5")

preset_label = st.selectbox("Préréglages", [p.label for p in PRESETS], index=0)
preset = by_label(preset_label)
tz = st.selectbox("Fuseau d'affichage", ["Europe/Paris","Europe/Zurich","UTC","America/New_York"], index=1)
jour = st.date_input("Jour", value=date.today())
window = st.slider("Fenêtre de simultanéité (min)", 0, 120, 15, 5)

if st.button("Lister les groupes"):
    try:
        with duckdb.connect(get_db_path()) as con:
            start = pd.Timestamp(jour).tz_localize(tz).tz_convert("UTC").to_pydatetime()
            end   = (pd.Timestamp(jour)+pd.Timedelta(days=1)).tz_localize(tz).tz_convert("UTC").to_pydatetime()
            cols = {r[1] for r in con.execute("PRAGMA table_info('events')").fetchall()}
            sel = ["ts_utc"]
            for c in ["country","event_title","event_key","previous","estimate","forecast","unit"]:
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
        df["bucket"] = pd.to_datetime(df["ts_utc"]).dt.floor(f"{max(window,1)}T")
        counts = df.groupby("bucket").size().reset_index(name="n")
        counts = counts[counts["n"]>1].sort_values(["bucket"])
        st.subheader("Groupes de simultanéité")
        st.dataframe(counts, use_container_width=True, hide_index=True)
        st.subheader("Détail")
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.exception(e)
