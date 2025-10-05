# fx_impact_app/streamlit_app/pages/10_Calendar_Sim_Backtest.py
from __future__ import annotations

import pandas as pd
import duckdb
import streamlit as st
from datetime import date, time, datetime
from zoneinfo import ZoneInfo

# --- imports projet ---
from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.presets import PRESETS, by_label

# Titre FR optionnel (grâce à _shared). Fallback no-op si absent.
try:
    from fx_impact_app.src._shared import _title_fr  # type: ignore
except Exception:  # pragma: no cover
    def _title_fr(title: str, key: str | None = None, country: str | None = None) -> str:
        return title

# ---------- UI ----------
st.set_page_config(page_title="Calendar Sim Backtest — V5", layout="wide")
st.title("🧪 Calendar Sim Backtest — V5")

colA, colB = st.columns([1, 1])

with colA:
    tz = st.selectbox(
        "Fuseau horaire",
        ["Europe/Zurich", "Europe/Paris", "UTC", "America/New_York"],
        index=0,
    )
    day_local = st.date_input("Jour cible (local)", value=date.today())
    preset_label = st.selectbox(
        "Preset (pour auto-remplir regex & pays)", [p.label for p in PRESETS], index=0
    )
    preset = by_label(preset_label)
    use_preset_filter = st.checkbox(
        "Appliquer le filtre du preset (regex + pays)", value=False
    )
    utc_day = st.checkbox("Interpréter la journée en UTC (00:00 → 24:00 UTC)", value=False)

with colB:
    countries_default = preset.countries or []
    regex_default = preset.include_regex or ""

    regex = st.text_input(
        "Filtre regex (optionnel)",
        value=(regex_default if use_preset_filter else ""),
        help="Laisse vide pour lister tous les événements.",
    )
    countries = st.multiselect(
        "Pays (optionnel)",
        ["US", "EA", "EU", "UK", "DE", "FR", "IT", "ES", "JP", "CN"],
        default=(countries_default if use_preset_filter else []),
    )
    c1, c2 = st.columns(2)
    with c1:
        start_h = st.time_input("Heure début (local)", value=time(0, 0))
    with c2:
        end_h = st.time_input("Heure fin (local)", value=time(23, 59))


# ---------- Helpers SQL ----------
def _has_col(con: duckdb.DuckDBPyConnection, table: str, col: str) -> bool:
    return bool(con.execute(f"PRAGMA table_info({table})").df().query("name == @col").shape[0])


def _query_range(
    con: duckdb.DuckDBPyConnection,
    start_utc: pd.Timestamp,
    end_utc: pd.Timestamp,
    regex: str | None,
    countries: list[str] | None,
) -> pd.DataFrame:
    """
    Interroge la table `events` entre deux bornes UTC.
    Filtre regex et pays optionnels, en ne référencant que les colonnes existantes.
    """
    has_country = _has_col(con, "events", "country")
    has_title = _has_col(con, "events", "event_title")
    has_key = _has_col(con, "events", "event_key")
    has_prev = _has_col(con, "events", "previous")
    has_estimate = _has_col(con, "events", "estimate")
    has_fc = _has_col(con, "events", "forecast")
    has_cons = _has_col(con, "events", "consensus")
    has_act = _has_col(con, "events", "actual")
    has_unit = _has_col(con, "events", "unit")

    sel = ["ts_utc"]
    if has_country:
        sel.append("country")
    if has_title:
        sel.append("event_title")
    if has_key:
        sel.append("lower(event_key) as event_key")
    if has_prev:
        sel.append("previous")
    if has_estimate:
        sel.append("estimate")
    if has_fc:
        sel.append("forecast")
    if has_cons:
        sel.append("consensus")
    if has_act:
        sel.append("actual")
    if has_unit:
        sel.append("unit")
    cols_sql = ", ".join(sel)

    where = ["ts_utc >= ?", "ts_utc < ?"]
    params: list[object] = [start_utc.to_pydatetime(), end_utc.to_pydatetime()]

    if countries and has_country:
        where.append("country IN (" + ",".join(["?"] * len(countries)) + ")")
        params.extend(countries)

    if regex:
        parts: list[str] = []
        if has_key:
            parts.append("regexp_matches(lower(coalesce(event_key,'')), ?)")
        if has_title:
            parts.append("regexp_matches(lower(coalesce(event_title,'')), ?)")
        if parts:
            where.append("(" + " OR ".join(parts) + ")")
            # autant de motifs que de parties
            params.extend([regex] * len(parts))

    q = f"SELECT {cols_sql} FROM events WHERE " + " AND ".join(where) + " ORDER BY ts_utc"
    return con.execute(q, params).df()


# ---------- Action ----------
if st.button("Lister les événements du jour", type="primary"):
    try:
        db_path = get_db_path()
        with duckdb.connect(db_path) as con:
            if utc_day:
                # Fenêtre 00:00→24:00 en UTC
                start_utc = pd.Timestamp(datetime.combine(day_local, time(0, 0)), tz="UTC")
                end_utc = start_utc + pd.Timedelta(days=1)
                df = _query_range(con, start_utc, end_utc, (regex or None), (countries or None))
                base_tz = "UTC"
            else:
                # Fenêtre locale (avec heures personnalisables), puis conversion en UTC
                TZ = ZoneInfo(tz)
                start_local = pd.Timestamp(datetime.combine(day_local, start_h), tz=TZ)
                end_local = pd.Timestamp(datetime.combine(day_local, end_h), tz=TZ)
                if end_local <= start_local:
                    # si fin <= début, on considère que tu veux déborder au lendemain
                    end_local = end_local + pd.Timedelta(days=1)
                start_utc = start_local.tz_convert("UTC")
                end_utc = end_local.tz_convert("UTC")
                df = _query_range(con, start_utc, end_utc, (regex or None), (countries or None))
                base_tz = tz

        if df.empty:
            st.warning("Aucun événement pour ce jour avec ces filtres.")
        else:
            view = df.copy()

            # ts_utc → ISO + local
            ts = pd.to_datetime(view["ts_utc"])
            if ts.dt.tz is None:  # si naïf, on fixe à UTC
                ts = ts.dt.tz_localize("UTC")
            view["ts_utc_iso"] = ts.dt.tz_convert("UTC").dt.strftime("%Y-%m-%d %H:%M:%S")
            view["ts_local"] = ts.dt.tz_convert(ZoneInfo(base_tz)).dt.strftime("%Y-%m-%d %H:%M")

            # Titre FR (si on a event_title)
            if "event_title" in view.columns:
                # pays par défaut pour traduction
                base_country = (
                    (countries[0] if countries else None)
                    or (preset.countries[0] if preset.countries else None)
                    or "US"
                )
                if "event_key" in view.columns:
                    ek = view["event_key"].tolist()
                else:
                    ek = [None] * len(view)

                fr_titles = []
                for i, t in enumerate(view["event_title"].tolist()):
                    fr_titles.append(_title_fr(t, ek[i], base_country))
                view["Événement"] = fr_titles

            # Colonnes à afficher
            cols = ["ts_utc_iso", "ts_local"]
            for c in ["country", "Événement", "event_title", "previous", "estimate", "forecast", "consensus", "actual", "unit"]:
                if c in view.columns:
                    cols.append(c)

            st.caption(f"{len(view)} événement(s) trouvé(s) | fenêtre UTC: {start_utc} → {end_utc}")
            st.dataframe(view[cols], use_container_width=True, hide_index=True)

    except Exception as e:  # affichage trace utile
        st.exception(e)
