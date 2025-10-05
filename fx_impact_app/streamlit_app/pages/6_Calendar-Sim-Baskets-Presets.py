import pandas as pd
import duckdb
import streamlit as st
from datetime import date
from fx_impact_app.streamlit_app._ui import apply_sidebar_index
apply_sidebar_index("Home")

# Résolution du chemin DB (V5) avec fallback
try:
    from fx_impact_app.src.config import get_db_path
except Exception:
    from pathlib import Path
    def get_db_path() -> str:
        return (Path(__file__).resolve().parents[2] / "data" / "warehouse.duckdb").as_posix()

from fx_impact_app.src.regex_presets import preset_keys, PRESETS, get_countries


st.set_page_config(page_title="Calendar Sim Backtest — V5 (presets)", layout="wide")
st.title("🧪 Calendar Sim Backtest — V5 (presets)")

# ---------- UI ----------
tz = st.selectbox(
    "Fuseau horaire d’affichage",
    ["Europe/Zurich", "UTC", "America/New_York", "Europe/London"],
    index=0,
)
day_local = st.date_input("Jour cible (local)", value=date.today())

preset_list = ["— Custom —"] + preset_keys()
preset_key = st.selectbox("Preset (auto-remplit regex & pays)", preset_list, index=1)

regex_in = st.text_input(
    "Filtre regex (optionnel)",
    value=(PRESETS[preset_key].include_regex if preset_key != "— Custom —" else ""),
    help="Expression régulière appliquée à event_key + event_title (insensible à la casse si (?i)).",
)

countries_default = get_countries(preset_key) if preset_key != "— Custom —" else []
countries = st.multiselect(
    "Pays (optionnel)",
    options=["US", "EA", "EU", "GB", "UK", "DE", "FR", "CH", "CA", "JP", "CN"],
    default=countries_default,
)

if st.button("Lister les événements du jour", type="primary"):
    try:
        # Convertit le jour local -> bornes UTC naïves
        start_local = pd.Timestamp(day_local).tz_localize(tz).floor("D")
        end_local = (start_local + pd.Timedelta(days=1)) - pd.Timedelta(seconds=1)
        start_utc = start_local.tz_convert("UTC").tz_localize(None)
        end_utc = end_local.tz_convert("UTC").tz_localize(None)

        with duckdb.connect(get_db_path()) as con:
            # Cast TS WITH TIME ZONE -> TIMESTAMP sans tz pour jointures simples
            q = """
                SELECT
                    CAST(ts_utc AS TIMESTAMP) AS ts_utc,
                    COALESCE(country,'')     AS country,
                    COALESCE(event_title,'') AS event_title,
                    COALESCE(event_key,'')   AS event_key
                FROM events
                WHERE ts_utc BETWEEN ? AND ?
            """
            params = [start_utc.to_pydatetime(), end_utc.to_pydatetime()]

            if countries:
                q += " AND country IN (" + ",".join(["?"] * len(countries)) + ")"
                params += countries

            if regex_in.strip():
                q += " AND regexp_matches(lower(coalesce(event_key,'') || ' ' || coalesce(event_title,'')), ?)"
                params.append(regex_in)

            q += " ORDER BY ts_utc"
            df = con.execute(q, params).df()

        st.caption(f"Intervalle UTC interrogé : {start_utc} → {end_utc}")

        if df.empty:
            st.warning("Aucun événement pour ce jour avec ces filtres.")
        else:
            st.dataframe(df, use_container_width=True)
            if "country" in df.columns:
                pays = ", ".join(sorted(df["country"].dropna().unique()))
            else:
                pays = "N/A"
            st.caption(f"Total lignes: {len(df)} — pays: {pays}")

        with st.expander("Diagnostics"):
            st.json(
                {
                    "tz": tz,
                    "jour_local": str(day_local),
                    "preset": preset_key,
                    "regex": regex_in or None,
                    "countries": countries,
                    "db_path": get_db_path(),
                }
            )

    except Exception as e:
        st.error("Erreur pendant la liste du jour.")
        st.exception(e)
