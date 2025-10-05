
from __future__ import annotations
import streamlit as st, pandas as pd, duckdb
from datetime import date, timedelta
from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.presets import PRESETS, by_label
from fx_impact_app.src._shared import _title_fr

st.set_page_config(page_title="Top events — V5", layout="wide")
st.title("🏆 Top events — V5")

preset_label = st.selectbox("Préréglages", [p.label for p in PRESETS], index=0)
preset = by_label(preset_label)
tz = st.selectbox("Fuseau d'affichage", ["Europe/Paris","Europe/Zurich","UTC","America/New_York"], index=1)
day0 = st.date_input("Début", value=date.today())
day1 = st.date_input("Fin", value=date.today() + timedelta(days=7))
regex_extra = st.text_input("Regex supplémentaire (optionnel)", value="")

if st.button("Lister"):
    try:
        with duckdb.connect(get_db_path()) as con:
            start = pd.Timestamp(day0).tz_localize(tz).tz_convert("UTC").to_pydatetime()
            end   = (pd.Timestamp(day1)+pd.Timedelta(days=1)).tz_localize(tz).tz_convert("UTC").to_pydatetime()
            cols = {r[1] for r in con.execute("PRAGMA table_info('events')").fetchall()}
            sel = ["ts_utc"]
            for c in ["country","event_title","event_key","previous","estimate","forecast","unit","importance_n"]:
                if c in cols: sel.append(c)
            q = f"SELECT {', '.join(sel)} FROM events WHERE ts_utc BETWEEN ? AND ?"
            params=[start, end]
            if preset.countries and "country" in cols:
                q += " AND country IN (" + ",".join(["?"]*len(preset.countries)) + ")"; params += preset.countries
            regex = preset.include_regex
            if regex_extra:
                regex = (regex or ".") + "|" + regex_extra
            if regex:
                parts=[]
                if "event_key" in cols:   parts.append("regexp_matches(lower(event_key), ?)")
                if "event_title" in cols: parts.append("regexp_matches(lower(event_title), ?)")
                if parts: q += " AND (" + " OR ".join(parts) + ")"; params += [regex]*len(parts)
            q += " ORDER BY ts_utc"
            df = con.execute(q, params).df()
        if df.empty: st.warning("Aucun événement."); st.stop()
        # Ajout FR
        if "event_title" in df.columns:
            country = preset.countries[0] if preset.countries else None
            df["Événement"] = [ _title_fr(t, (df.get("event_key") or [None])[i] if "event_key" in df.columns else None, country) for i,t in enumerate(df["event_title"]) ]
        # Affichage
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.exception(e)
