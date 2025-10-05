from __future__ import annotations
import pandas as pd, duckdb, streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from fx_impact_app.streamlit_app._ui import apply_sidebar_index
apply_sidebar_index("Home")

st.set_page_config(page_title="Backtest (with presets)", layout="wide")
st.title("📊 Backtest — V5 (with presets)")
st.caption(f"Loaded from: {__file__}")

# --- DB path (V5) ---
def _get_db_path() -> str:
    try:
        from fx_impact_app.src.config import get_db_path
        return get_db_path()
    except Exception:
        here = Path(__file__).resolve().parents[3]
        return (here / "fx_impact_app" / "data" / "warehouse.duckdb").as_posix()

# --- Presets (try import, else fallback minimal) ---
try:
    from fx_impact_app.src.regex_presets import (
        regex_selectbox, coalesce_regex, default_preset_for_family
    )
except Exception:
    PRESETS = {
        "FOMC (Fed, US)": r"(fomc|fed funds|rate decision|interest rate)",
        "NFP (US)": r"(nonfarm|non-farm|nfp|payrolls|employment)",
        "CPI (US)": r"\bcpi\b|consumer price",
        "ECB (EA/EU)": r"(ecb|deposit rate|main refinancing)",
        "Unemployment rate (US)": r"(?i)\bunemployment\b|\bjobless\b",
    }
    FAMILY_DEFAULT = {"FOMC": "FOMC (Fed, US)", "NFP": "NFP (US)", "CPI": "CPI (US)"}

    def regex_selectbox(label: str, default: str | None = None, help: str | None = None):
        names = list(PRESETS.keys())
        idx = names.index(default) if default in names else 0
        name = st.selectbox(label, names, index=idx, help=help)
        return PRESETS[name], name

    def coalesce_regex(preset_name: str, custom: str | None) -> str:
        if custom and custom.strip():
            return custom.strip()
        return PRESETS.get(preset_name, r"." )

    def default_preset_for_family(family: str) -> str:
        return FAMILY_DEFAULT.get((family or "").upper(), "NFP (US)")

# --- UI ---
c0,c1,c2 = st.columns([2,2,2])
with c0:
    tz_name = st.selectbox("Fuseau horaire (affichage)",
                           ["Europe/Zurich","UTC","Europe/Paris","America/New_York"], index=0)
with c1:
    day_local = st.date_input("Jour cible (local)")
with c2:
    countries = st.multiselect("Pays (optionnel)", ["US","EA","EU","GB","DE","FR"])

st.markdown("—")
st.subheader("🎯 Filtre par presets (regex)")
fam = st.selectbox("Famille (guidage preset)", ["NFP","CPI","FOMC"], index=0)
preset_default = default_preset_for_family(fam)
preset_pattern, preset_name = regex_selectbox("Preset", default=preset_default,
                                              help="Sélectionne un motif prédéfini")
regex_free = st.text_input("Regex personnalisé (optionnel)", "")
pattern = coalesce_regex(preset_name, regex_free)
st.caption(f"Regex appliqué : `{pattern}` (preset : {preset_name})")

# --- Helpers ---
def _utc_bounds(day, tz):
    start_local = datetime(day.year, day.month, day.day, 0, 0, tzinfo=ZoneInfo(tz))
    end_local   = datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=ZoneInfo(tz))
    s_utc = pd.Timestamp(start_local).tz_convert("UTC").tz_localize(None)
    e_utc = pd.Timestamp(end_local).tz_convert("UTC").tz_localize(None)
    return s_utc, e_utc

def _columns(con, table: str) -> set[str]:
    try:
        return {r[1].lower() for r in con.execute(f"PRAGMA table_info('{table}')").fetchall()}
    except Exception:
        return set()

# --- Action ---
if st.button("Lister les événements du jour", type="primary"):
    try:
        s_utc, e_utc = _utc_bounds(day_local, tz_name)
        path = _get_db_path()
        with duckdb.connect(path) as con:
            cols = _columns(con, "events")
            if "ts_utc" not in cols:
                st.error("Table 'events' absente ou sans colonne ts_utc.")
                st.stop()

            select_cols = ["CAST(ts_utc AS TIMESTAMP) AS ts_utc"]
            for c in ["country","event_title","event_key","previous","estimate","forecast",
                      "unit","actual","result"]:
                if c in cols: select_cols.append(c)

            q = f"SELECT {', '.join(select_cols)} FROM events WHERE ts_utc BETWEEN ? AND ?"
            params = [s_utc.to_pydatetime(), e_utc.to_pydatetime()]

            if countries and "country" in cols:
                q += " AND country IN (" + ",".join(["?"]*len(countries)) + ")"
                params += countries

            parts=[]
            if "event_key" in cols:   parts.append("regexp_matches(lower(coalesce(event_key,'')), ?)")
            if "event_title" in cols: parts.append("regexp_matches(lower(coalesce(event_title,'')), ?)")
            if parts:
                q += " AND (" + " OR ".join(parts) + ")"
                params += [pattern]*len(parts)

            q += " ORDER BY ts_utc"
            df = con.execute(q, params).df()

        st.subheader("Événements du jour (filtrés)")
        if df.empty:
            st.warning("Aucun événement pour ces filtres.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                "Exporter CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"events_{day_local.isoformat()}_{preset_name}.csv",
                mime="text/csv",
            )
            if "country" in df.columns:
                pays = ", ".join(sorted(df["country"].dropna().unique()))
            else:
                pays = "N/A"
            st.caption(f"Total lignes: {len(df)} — pays: {pays}")

    except Exception as e:
        st.error("Erreur pendant la liste du jour.")
        st.exception(e)
