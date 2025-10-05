from __future__ import annotations
import pandas as pd
import duckdb
import streamlit as st
from datetime import date
from zoneinfo import ZoneInfo

# Résolution du chemin DB (V5) avec fallback
try:
    from fx_impact_app.src.config import get_db_path
except Exception:
    from pathlib import Path
    def get_db_path() -> str:
        return (Path(__file__).resolve().parents[2] / "data" / "warehouse.duckdb").as_posix()

# Presets centralisés
from fx_impact_app.src.regex_presets import PRESETS, preset_keys, get_regex, get_countries
from fx_impact_app.streamlit_app._ui import apply_sidebar_index
apply_sidebar_index("Home")


st.set_page_config(page_title="Simultaneous Events — V5 (presets)", layout="wide")
st.title("🪄 Simultaneous Events — V5 (presets)")
st.caption(f"Loaded from: {__file__}")

# --------------------------
# UI — paramètres de base
# --------------------------
c0, c1, c2 = st.columns([2, 2, 2])

with c0:
    tz_name = st.selectbox(
        "Fuseau horaire d’affichage",
        ["Europe/Zurich", "UTC", "Europe/Paris", "America/New_York", "Europe/London"],
        index=0,
    )
    day_local = st.date_input("Jour cible (local)", value=date.today())

with c1:
    choices = preset_keys()
    # petit guidage : si “FOMC” dans le nom, on le rend premier par défaut
    default_idx = 0
    for i, k in enumerate(choices):
        if "FOMC" in k or "Fed" in k:
            default_idx = i
            break
    preset_key = st.selectbox("Preset (événement ‘ancre’)", choices, index=default_idx)
    anchor_regex = st.text_input(
        "Regex (ancre) — event_key + event_title",
        value=get_regex(preset_key),
        help="Expression régulière insensible à la casse si préfixée par (?i).",
    )

with c2:
    # Pays des ANCRAGES : on suggère ceux du preset, mais tu peux élargir/réduire
    anchor_countries = st.multiselect(
        "Pays (ancre)",
        options=["US","EA","EU","GB","UK","DE","FR","CH","CA","JP","CN"],
        default=get_countries(preset_key) or ["US"],
        help="Filtre appliqué aux événements d’ancre uniquement.",
    )

st.markdown("---")

c3, c4 = st.columns([2, 2])
with c3:
    win_min = st.slider("Fenêtre simultanéité ± minutes autour de l’ancre", min_value=1, max_value=180, value=30, step=5)
with c4:
    exclude_same_event = st.checkbox("Exclure la ligne d’ancre elle-même", value=True)

st.markdown("---")

# --------------------------
# Helpers
# --------------------------
def _utc_bounds_for_local_day(day: date, tz: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    start_local = pd.Timestamp(day).tz_localize(ZoneInfo(tz)).floor("D")
    end_local   = (start_local + pd.Timedelta(days=1)).ceil("D") - pd.Timedelta(seconds=1)
    start_utc   = start_local.tz_convert("UTC").tz_localize(None)
    end_utc     = end_local.tz_convert("UTC").tz_localize(None)
    return start_utc, end_utc

def _cols(con, table: str) -> set[str]:
    try:
        return {r[1].lower() for r in con.execute(f"PRAGMA table_info('{table}')").fetchall()}
    except Exception:
        return set()

# --------------------------
# Action
# --------------------------
if st.button("Chercher les événements simultanés", type="primary"):
    try:
        start_utc, end_utc = _utc_bounds_for_local_day(day_local, tz_name)
        db = get_db_path()

        with duckdb.connect(db) as con:
            cols = _cols(con, "events")
            if "ts_utc" not in cols:
                st.error("Table `events` absente ou sans colonne `ts_utc`.")
                st.stop()

            # Colonnes disponibles (on ajoute celles trouvées)
            base_sel = ["CAST(ts_utc AS TIMESTAMP) AS ts_utc"]
            for c in ["country", "event_title", "event_key", "previous", "estimate", "forecast", "unit", "actual", "result"]:
                if c in cols:
                    base_sel.append(c)
            base_cols_sql = ", ".join(base_sel)

            # ev_all = tous les events du jour (pour trouver les voisins)
            q_ev_all = f"""
                SELECT {base_cols_sql}
                FROM events
                WHERE ts_utc BETWEEN ? AND ?
                ORDER BY ts_utc
            """
            ev_all = con.execute(q_ev_all, [start_utc.to_pydatetime(), end_utc.to_pydatetime()]).df()

            if ev_all.empty:
                st.warning("Aucun événement ce jour-là.")
                st.stop()

            # ev_anchor = events d’ancre (filtre pays + regex)
            where_anchor = ["ts_utc BETWEEN ? AND ?"]
            params_anchor = [start_utc.to_pydatetime(), end_utc.to_pydatetime()]

            if anchor_countries and "country" in cols:
                where_anchor.append("country IN (" + ",".join(["?"] * len(anchor_countries)) + ")")
                params_anchor += anchor_countries

            if anchor_regex.strip():
                parts = []
                if "event_key" in cols:
                    parts.append("regexp_matches(lower(coalesce(event_key,'')), ?)")
                if "event_title" in cols:
                    parts.append("regexp_matches(lower(coalesce(event_title,'')), ?)")
                if parts:
                    where_anchor.append("(" + " OR ".join(parts) + ")")
                    params_anchor += [anchor_regex] * len(parts)

            q_anchor = f"""
                SELECT {base_cols_sql}
                FROM events
                WHERE {" AND ".join(where_anchor)}
                ORDER BY ts_utc
            """
            ev_anchor = con.execute(q_anchor, params_anchor).df()

        st.subheader("Ancrages détectés")
        if ev_anchor.empty:
            st.warning("Aucun événement d’ancre trouvé avec ces filtres.")
            st.stop()
        st.dataframe(ev_anchor, use_container_width=True)

        # Pour chaque ancre, on récupère les voisins ± win_min dans ev_all
        # (Sans refaire des requêtes : on utilise le DataFrame ev_all)
        def _localize(ts: pd.Timestamp) -> str:
            # ts est naïf (UTC) après CAST — on l’attache UTC puis convertit
            t = pd.Timestamp(ts).tz_localize("UTC").tz_convert(ZoneInfo(tz_name))
            return t.strftime("%Y-%m-%d %H:%M:%S %Z")

        rows = []
        ev_all_sorted = ev_all.sort_values("ts_utc").reset_index(drop=True)
        for _, a in ev_anchor.iterrows():
            a_ts: pd.Timestamp = a["ts_utc"]
            mask = (ev_all_sorted["ts_utc"] >= a_ts - pd.Timedelta(minutes=win_min)) & \
                   (ev_all_sorted["ts_utc"] <= a_ts + pd.Timedelta(minutes=win_min))
            neigh = ev_all_sorted.loc[mask].copy()
            if exclude_same_event:
                # on retire la ligne strictement identique (même ts + même titre)
                if "event_title" in neigh.columns and "event_title" in a:
                    neigh = neigh[~((neigh["ts_utc"] == a_ts) &
                                    (neigh["event_title"].fillna("") == str(a.get("event_title",""))))]
                else:
                    neigh = neigh[neigh["ts_utc"] != a_ts]

            if neigh.empty:
                continue

            # Ajoute les colonnes “ancre_*” + delta minutes
            neigh["delta_min"] = (neigh["ts_utc"] - a_ts).dt.total_seconds().div(60).round(1)
            neigh.insert(0, "anchor_ts_local", _localize(a_ts))
            neigh.insert(1, "anchor_ts_utc", a_ts)
            neigh.insert(2, "anchor_country", a.get("country", None))
            neigh.insert(3, "anchor_title", a.get("event_title", None))
            neigh.insert(4, "anchor_key", a.get("event_key", None))
            rows.append(neigh)

        st.markdown("---")
        st.subheader(f"Événements dans ±{win_min} min autour des ancrages")

        if not rows:
            st.info("Aucun événement concomitant trouvé dans la fenêtre choisie.")
        else:
            out = pd.concat(rows, ignore_index=True)
            # Réordonne pour lisibilité
            cols_pref = [c for c in [
                "anchor_ts_local","anchor_ts_utc","anchor_country","anchor_title","anchor_key",
                "ts_utc","country","event_title","event_key","delta_min","previous","estimate","forecast","unit","actual","result"
            ] if c in out.columns]
            ordered = cols_pref + [c for c in out.columns if c not in cols_pref]
            out = out[ordered].sort_values(["anchor_ts_utc","delta_min","ts_utc"]).reset_index(drop=True)

            st.dataframe(out, use_container_width=True, hide_index=True)
            st.download_button(
                "Exporter CSV",
                data=out.to_csv(index=False).encode("utf-8"),
                file_name=f"simultaneous_{day_local.isoformat()}_{preset_key.replace(' ','_')}.csv",
                mime="text/csv",
            )

        with st.expander("Diagnostics"):
            st.json({
                "tz": tz_name,
                "day_local": str(day_local),
                "preset": preset_key,
                "anchor_regex": anchor_regex,
                "anchor_countries": anchor_countries,
                "window_min": win_min,
                "exclude_same_event": exclude_same_event,
                "db_path": get_db_path(),
                "anchors_found": 0 if 'ev_anchor' not in locals() else int(len(ev_anchor)),
                "all_events_today": 0 if 'ev_all' not in locals() else int(len(ev_all)),
            })

    except Exception as e:
        st.error("Erreur pendant la recherche.")
        st.exception(e)
