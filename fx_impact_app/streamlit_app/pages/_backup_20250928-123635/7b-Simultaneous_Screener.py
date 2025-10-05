# fx_impact_app/streamlit_app/pages/7b_Simultaneous_Screener.py

from __future__ import annotations
import pandas as pd
import duckdb
import streamlit as st
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

# ------------------------------------------------------------
# DB path (V5) + fallback
# ------------------------------------------------------------
try:
    from fx_impact_app.src.config import get_db_path
except Exception:
    from pathlib import Path
    def get_db_path() -> str:
        return (Path(__file__).resolve().parents[2] / "data" / "warehouse.duckdb").as_posix()

# Tuning mémoire/threads/temp
try:
    from fx_impact_app.src.db_tuning import tune
except Exception:
    def tune(*a, **k): return {}

# ------------------------------------------------------------
# Presets (variants) — on tente d'importer; sinon, fallback minimal
# ------------------------------------------------------------
try:
    from fx_impact_app.src.regex_presets import (
        PRESETS, preset_keys, get_countries, get_variants, get_variant_regex,
    )
except Exception:
    PRESETS = {
        "FOMC (Fed, US)": {
            "countries": ["US"],
            "variants": {
                "Large (tous)": r"(?i)(fomc|federal reserve|fed funds|federal funds|target rate|"
                                r"rate decision|interest rate|policy statement|press conference|"
                                r"dot plot|economic projections|summary of economic projections|sep|minutes)"
            },
        },
        "NFP (US)": {
            "countries": ["US"],
            "variants": {
                "Large (tous emploi)": r"(?i)(nonfarm|non-farm|nfp|payrolls|employment|unemployment rate|"
                                       r"participation rate|average hourly earnings)"
            },
        },
        "CPI (US)": {
            "countries": ["US"],
            "variants": {"Large (tous CPI)": r"(?i)\bcpi\b|consumer price|inflation|core cpi|headline cpi"},
        },
    }
    def preset_keys(): return list(PRESETS.keys())
    def get_countries(k): return PRESETS[k]["countries"]
    def get_variants(k): return list(PRESETS[k]["variants"].keys())
    def get_variant_regex(k, v): return PRESETS[k]["variants"][v]

# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(page_title="Simultaneous Screener — impact & clusters", layout="wide")
st.title("📡 Simultaneous Screener — impact & clusters")
st.caption(f"Loaded from: {__file__}")

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
c0, c1, c2 = st.columns([2.2, 2.2, 2.2])
with c0:
    tz_name = st.selectbox(
        "Fuseau d’affichage",
        ["Europe/Zurich", "UTC", "Europe/Paris", "America/New_York", "Europe/London"],
        index=0,
    )
with c1:
    default_end = date.today()
    default_start = (pd.Timestamp(default_end) - pd.Timedelta(days=180)).date()
    d_start = st.date_input("Début (UTC)", value=default_start)
with c2:
    d_end = st.date_input("Fin (UTC)", value=date.today())

st.markdown("#### Filtre des événements à considérer (optionnel, via presets)")
c3, c4, c5 = st.columns([2.2, 2.2, 2.2])
with c3:
    use_preset = st.checkbox("Utiliser un preset + variante comme filtre des événements", value=True)
with c4:
    choices = preset_keys()
    pk_idx = 0
    preset_key = st.selectbox("Preset", choices, index=pk_idx, disabled=not use_preset)
with c5:
    variants = get_variants(preset_key) if use_preset else []
    v_idx = max(0, variants.index("Large (tous)") if use_preset and "Large (tous)" in variants else 0)
    variant_label = st.selectbox("Variante", variants, index=v_idx, disabled=not use_preset)

c6, c7, c8 = st.columns([2.2, 2.2, 2.2])
with c6:
    pattern = get_variant_regex(preset_key, variant_label) if use_preset else ""
    pattern = st.text_area(
        "Regex (editable)",
        value=pattern, height=90, disabled=not use_preset,
        help="Appliquée à (event_key + event_title), insensible à la casse si (?i)."
    )
with c7:
    country_opts = ["US","EA","EU","GB","UK","DE","FR","CH","CA","JP","CN"]
    def_countries = get_countries(preset_key) if use_preset else ["US"]
    countries = st.multiselect(
        "Pays (filtre facultatif)",
        options=country_opts,
        default=[c for c in def_countries if c in country_opts],
        help="Si vide → pas de filtre pays."
    )
with c8:
    limit_variants = st.checkbox("Limiter aux pays ci-dessus", value=bool(countries))

st.markdown("#### Paramètres simultanéité & impact prix")
c9, c10, c11 = st.columns([2.2, 2.2, 2.2])
with c9:
    win_min = st.slider("Fenêtre simultanéité ± minutes", 1, 120, 30, 5)
with c10:
    min_simul = st.number_input("Min # d’événements simultanés", min_value=2, max_value=20, value=3, step=1)
    max_simul = st.number_input("Max # d’événements simultanés", min_value=min_simul, max_value=50, value=6, step=1)
with c11:
    horizon = st.slider("Horizon prix (minutes)", 1, 120, 30, 5)

c12, c13, _ = st.columns([2.2, 2.2, 1])
with c12:
    min_pips = st.number_input("Mouvement min (pips, |MFE|)", min_value=0.0, max_value=1000.0, value=20.0, step=1.0)
with c13:
    max_pips = st.number_input("Mouvement max (pips, |MFE|)", min_value=min_pips, max_value=1000.0, value=50.0, step=1.0)

st.markdown("---")

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
PIP = 10000.0  # EURUSD

def _ensure_price_view(con: duckdb.DuckDBPyConnection) -> str:
    """Crée/replace une vue prices_1m_v(ts_utc, close) depuis prices_1m(datetime, close, ...)."""
    tab = con.execute("""
      SELECT 1
      FROM information_schema.tables
      WHERE lower(table_name)='prices_1m'
      LIMIT 1
    """).fetchone()
    if not tab:
        raise RuntimeError("Table 'prices_1m' introuvable (nécessaire pour mesurer les pips).")

    cols = [r[0] for r in con.execute("""
      SELECT lower(column_name)
      FROM information_schema.columns
      WHERE lower(table_name)='prices_1m'
    """).fetchall()]
    if "datetime" not in cols or "close" not in cols:
        raise RuntimeError("La table 'prices_1m' doit contenir 'datetime' et 'close'.")

    con.execute("""
      CREATE OR REPLACE VIEW prices_1m_v AS
      SELECT CAST(datetime AS TIMESTAMP) AS ts_utc, close
      FROM prices_1m
      WHERE datetime IS NOT NULL
      ORDER BY datetime
    """)
    return "prices_1m_v"

def _utc_range(d_from: date, d_to: date):
    s = pd.Timestamp(datetime.combine(d_from, time(0,0)), tz="UTC").tz_convert("UTC").tz_localize(None)
    e = pd.Timestamp(datetime.combine(d_to, time(23,59,59)), tz="UTC").tz_convert("UTC").tz_localize(None)
    return s, e

def _localize(ts_utc: pd.Timestamp, tz: str) -> str:
    if ts_utc is None or pd.isna(ts_utc):
        return ""
    t = pd.Timestamp(ts_utc).tz_localize("UTC").tz_convert(ZoneInfo(tz))
    return t.strftime("%Y-%m-%d %H:%M:%S %Z")

# ------------------------------------------------------------
# Action
# ------------------------------------------------------------
if st.button("Scanner la période", type="primary"):
    try:
        start_utc, end_utc = _utc_range(d_start, d_end)
        db = get_db_path()

        with duckdb.connect(db) as con:
            # Tuning (évite l'OOM sur de longues fenêtres)
            tune(con, mem_gb=6, threads=2, max_temp_gb=100)

            price_view = _ensure_price_view(con)

            cols = {r[1].lower() for r in con.execute("PRAGMA table_info('events')").fetchall()}
            if "ts_utc" not in cols:
                st.error("Table `events` absente ou sans colonne `ts_utc`."); st.stop()

            # 1) Sous-ensemble d'événements dans la fenêtre
            where = ["ts_utc BETWEEN ? AND ?"]
            params = [start_utc.to_pydatetime(), end_utc.to_pydatetime()]

            if limit_variants and countries and "country" in cols:
                where.append("country IN (" + ",".join(["?"] * len(countries)) + ")")
                params += countries

            if use_preset and pattern.strip():
                parts = []
                if "event_key" in cols:   parts.append("regexp_matches(lower(coalesce(event_key,'')), ?)")
                if "event_title" in cols: parts.append("regexp_matches(lower(coalesce(event_title,'')), ?)")
                if parts:
                    where.append("(" + " OR ".join(parts) + ")")
                    params += [pattern] * len(parts)

            base_sel = ["CAST(ts_utc AS TIMESTAMP) AS ts_utc"]
            for c in ["country", "event_title", "event_key", "previous", "estimate", "forecast", "unit", "actual"]:
                if c in cols:
                    base_sel.append(c)
            base_cols_sql = ", ".join(base_sel)

            q_ev = f"""
                SELECT {base_cols_sql}
                FROM events
                WHERE {" AND ".join(where)}
                ORDER BY ts_utc
            """
            ev = con.execute(q_ev, params).df()
            if ev.empty:
                st.warning("Aucun événement trouvé sur la période avec ces filtres.")
                st.stop()

            # 2) Ancrages par self-join (simultanéité)
            q_anchors = f"""
                WITH ev AS (
                    SELECT CAST(ts_utc AS TIMESTAMP) AS ts_utc
                    FROM events
                    WHERE {" AND ".join(where)}
                )
                SELECT a.ts_utc AS anchor_ts,
                       COUNT(*)  AS n_simul
                FROM ev a
                JOIN ev b
                  ON b.ts_utc BETWEEN a.ts_utc - INTERVAL {win_min} MINUTE
                                  AND a.ts_utc + INTERVAL {win_min} MINUTE
                GROUP BY 1
                HAVING COUNT(*) BETWEEN {int(min_simul)} AND {int(max_simul)}
                ORDER BY anchor_ts
            """
            anchors = con.execute(q_anchors, params).df()
            if anchors.empty:
                st.info("Aucun cluster d’événements simultanés dans la fenêtre choisie.")
                st.stop()

            # 3) Score prix (MFE absolu) pour chaque ancre
            q_score = f"""
                WITH anchors AS ({q_anchors}),
                snap AS (
                  SELECT
                    an.anchor_ts,
                    an.n_simul,
                    (SELECT p.close FROM {price_view} p
                      WHERE p.ts_utc <= an.anchor_ts
                      ORDER BY p.ts_utc DESC LIMIT 1) AS entry_px,
                    (SELECT p.close FROM {price_view} p
                      WHERE p.ts_utc <= an.anchor_ts + INTERVAL {horizon} MINUTE
                      ORDER BY p.ts_utc DESC LIMIT 1) AS end_px,
                    (SELECT max(p.close) FROM {price_view} p
                      WHERE p.ts_utc BETWEEN an.anchor_ts AND an.anchor_ts + INTERVAL {horizon} MINUTE) AS max_px,
                    (SELECT min(p.close) FROM {price_view} p
                      WHERE p.ts_utc BETWEEN an.anchor_ts AND an.anchor_ts + INTERVAL {horizon} MINUTE) AS min_px
                  FROM anchors an
                )
                SELECT
                  anchor_ts,
                  n_simul,
                  entry_px, end_px, max_px, min_px,
                  {PIP} * abs(end_px - entry_px)                          AS end_abs_pips,
                  {PIP} * (max_px - entry_px)                              AS mfe_up_pips,
                  {PIP} * (entry_px - min_px)                              AS mfe_down_pips,
                  {PIP} * GREATEST(max_px - entry_px, entry_px - min_px)   AS mfe_abs_pips
                FROM snap
                WHERE entry_px IS NOT NULL AND end_px IS NOT NULL AND max_px IS NOT NULL AND min_px IS NOT NULL
            """
            scored = con.execute(q_score, params).df()
            if scored.empty:
                st.info("Pas de prix disponibles autour des ancrages pour calculer le MFE.")
                st.stop()

            filt = scored[(scored["mfe_abs_pips"] >= float(min_pips)) & (scored["mfe_abs_pips"] <= float(max_pips))]
            if filt.empty:
                st.info("Aucun ancrage avec un mouvement dans la fourchette demandée.")
                st.stop()

            # 4) Détails voisins par ancre (sélection dynamique des colonnes dispo)
            allowable = ["country","event_title","event_key","previous","estimate","forecast","unit","actual"]
            present = [c for c in allowable if c in cols]
            select_e_cols = ", ".join(["e.ts_utc"] + [f"e.{c}" for c in present]) if present else "e.ts_utc"

            q_neigh = f"""
                WITH ev AS (
                    SELECT {base_cols_sql}
                    FROM events
                    WHERE {" AND ".join(where)}
                ),
                anchors AS ({q_anchors})
                SELECT
                    a.anchor_ts,
                    {select_e_cols}
                FROM anchors a
                JOIN ev e
                  ON e.ts_utc BETWEEN a.anchor_ts - INTERVAL {win_min} MINUTE
                                  AND a.anchor_ts + INTERVAL {win_min} MINUTE
                ORDER BY a.anchor_ts, e.ts_utc
            """
            # q_neigh réutilise le WHERE deux fois (ev + q_anchors) => il faut dupliquer les params
            repeat = max(1, q_neigh.count("?") // max(1, len(params)))
            neigh = con.execute(q_neigh, params * repeat).df()

        # 5) Présentation
        filt = filt.sort_values(["n_simul", "mfe_abs_pips", "anchor_ts"], ascending=[False, False, True]).reset_index(drop=True)
        filt["anchor_ts_local"] = filt["anchor_ts"].apply(lambda t: _localize(t, tz_name))

        st.subheader("⏱️ Ancrages retenus (clusters + impact prix)")
        view_cols = ["anchor_ts_local", "anchor_ts", "n_simul", "mfe_abs_pips", "end_abs_pips", "mfe_up_pips", "mfe_down_pips"]
        st.dataframe(filt[view_cols], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🧩 Détails des événements simultanés (par ancre)")
        if not neigh.empty:
            neigh["anchor_ts_local"] = neigh["anchor_ts"].apply(lambda t: _localize(t, tz_name))
            for a_ts, df_g in neigh.groupby("anchor_ts", sort=True):
                tsl = _localize(a_ts, tz_name)
                with st.expander(f"📌 {tsl} — total {len(df_g)} événements dans ±{win_min} min"):
                    cols_pref = ["ts_utc"] + [c for c in allowable if c in df_g.columns]
                    st.dataframe(df_g[cols_pref], use_container_width=True, hide_index=True)

        # Exports
        st.markdown("---")
        cexp1, cexp2 = st.columns(2)
        with cexp1:
            st.download_button(
                "Exporter (ancrages scorés) CSV",
                data=filt.to_csv(index=False).encode("utf-8"),
                file_name=f"screener_anchors_{d_start}_{d_end}.csv",
                mime="text/csv",
            )
        with cexp2:
            if not neigh.empty:
                st.download_button(
                    "Exporter (détails voisins) CSV",
                    data=neigh.to_csv(index=False).encode("utf-8"),
                    file_name=f"screener_neighbors_{d_start}_{d_end}.csv",
                    mime="text/csv",
                )

        with st.expander("Diagnostics"):
            st.json({
                "db_path": get_db_path(),
                "period_utc": [str(start_utc), str(end_utc)],
                "use_preset": use_preset,
                "preset": preset_key if use_preset else None,
                "variant": variant_label if use_preset else None,
                "regex": pattern if use_preset else None,
                "countries": countries if limit_variants else None,
                "window_min": win_min,
                "min_simul": int(min_simul),
                "max_simul": int(max_simul),
                "horizon_min": int(horizon),
                "mfe_abs_range_pips": [float(min_pips), float(max_pips)],
                "anchors_scored": int(len(filt)),
            })

    except Exception as e:
        st.error("Erreur pendant le scan.")
        st.exception(e)

