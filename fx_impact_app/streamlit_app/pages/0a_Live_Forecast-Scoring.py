# fx_impact_app/streamlit_app/pages/0a_Live-Forecast-Scoring.py
from __future__ import annotations
import datetime as dt
from typing import List, Dict, Any
import pandas as pd
import streamlit as st
from zoneinfo import ZoneInfo

# --- Imports projet
from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.eodhd_client import (
    fetch_calendar_json as eod_fetch,
    calendar_to_events_df as eod_norm,
)
from fx_impact_app.src.forecaster_mvp import ForecastRequest, forecast
# Presets + mappage famille (ex. "ADP (US)" -> family "NFP")
try:
    from fx_impact_app.src.regex_presets import (
        PRESETS, preset_keys, get_countries, get_variants, get_variant_regex, get_family
    )
except Exception:
    # Fallback minimal si le module n'est pas présent
    PRESETS = {
        "NFP (US)": {
            "countries": ["US"],
            "variants": {
                "NFP headline": r"(?i)\b(nfp|non[- ]?farm)\b"
            },
            "family": "NFP",
        },
        "ADP (US)": {
            "countries": ["US"],
            "variants": {
                "ADP Employment Change": r"(?i)\badp\b"
            },
            "family": "NFP",
        },
        "CPI (US)": {
            "countries": ["US"],
            "variants": {
                "CPI (all)": r"(?i)\bcpi\b|consumer price|core cpi|headline cpi"
            },
            "family": "CPI",
        },
        "FOMC (US)": {
            "countries": ["US"],
            "variants": {
                "Large": r"(?i)(fomc|federal reserve|fed funds|federal funds|"
                         r"target rate|rate decision|interest rate|policy statement|"
                         r"press conference|dot plot|economic projections|"
                         r"summary of economic projections|sep|minutes)"
            },
            "family": "FOMC",
        },
    }
    def preset_keys(): return list(PRESETS.keys())
    def get_countries(k): return PRESETS[k]["countries"]
    def get_variants(k): return list(PRESETS[k]["variants"].keys())
    def get_variant_regex(k, v): return PRESETS[k]["variants"][v]
    def get_family(k): return PRESETS[k].get("family")

# ------------- Utilitaires temps & format ----------------
def _to_utc_naive(ts) -> pd.Timestamp:
    """
    Retourne un Timestamp UTC **naïf** (sans tzinfo) quelle que soit l'entrée:
    - string ISO, tz-aware, tz-naive → converti proprement.
    """
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    else:
        t = t.tz_convert("UTC")
    return t.tz_localize(None)

def _utc_range(d_from: dt.date, d_to: dt.date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Borne [00:00:00 ; 23:59:59] en UTC → **naïf** pour requêtes DB nickel.
    """
    s = pd.Timestamp(dt.datetime.combine(d_from, dt.time(0, 0)), tz="UTC").tz_convert("UTC").tz_localize(None)
    e = pd.Timestamp(dt.datetime.combine(d_to, dt.time(23, 59, 59)), tz="UTC").tz_convert("UTC").tz_localize(None)
    return s, e

def _fmt_local(ts, tz: str) -> str:
    """
    Affiche une heure **locale** lisible quel que soit le type de ts.
    """
    if ts is None or pd.isna(ts):
        return ""
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    else:
        t = t.tz_convert("UTC")
    return t.tz_convert(ZoneInfo(tz)).strftime("%Y-%m-%d %H:%M:%S %Z")

# ------------- Page UI ----------------
st.set_page_config(page_title="Live Forecast — Scoring (presets + mapping)", layout="wide")
st.title("⚡️ Live Forecast — Scoring (presets + mapping)")
st.caption(f"Loaded from: {__file__}")

# Barre latérale : réglages globaux
with st.sidebar:
    st.markdown("### Réglages")
    tz_name = st.selectbox("Fuseau local", ["Europe/Zurich", "UTC", "Europe/Paris", "America/New_York", "Europe/London"], index=0)
    horizons = st.multiselect("Horizons (min)", [15, 30, 60], default=[15, 30, 60])
    hist_years = st.slider("Historique (années)", 1, 10, 3, 1)
    force_score = st.checkbox("Forcer le scoring même si famille non détectée", value=True)

# Filtres période & pays
c1, c2, c3 = st.columns([2.2, 2.2, 2.2])
with c1:
    today = dt.date.today()
    d_from = st.date_input("Date début (UTC)", value=today)
with c2:
    d_to = st.date_input("Date fin (UTC)", value=today)
with c3:
    countries = st.multiselect("Pays", ["US","EU","EA","GB","UK","DE","FR","CH","CA","JP","CN"], default=["US","EU"])

# Preset & regex
st.markdown("#### Filtre via Presets (détecte la famille automatiquement)")
c4, c5, c6 = st.columns([2.2, 2.2, 2.2])
with c4:
    preset = st.selectbox("Preset", preset_keys(), index=0)
with c5:
    variants = get_variants(preset)
    variant = st.selectbox("Variante", variants, index=0)
with c6:
    regex = get_variant_regex(preset, variant)
    st.text_area("Regex appliquée sur label/event/type", value=regex, height=80)

# Bouton principal
do_run = st.button("Récupérer & Calculer", type="primary")

if do_run:
    try:
        # Fenêtre UTC pour EODHD (chaînes ISO UTC)
        start_utc, end_utc = _utc_range(d_from, d_to)
        # EODHD: on passe des ISO avec 'Z'
        d1_iso = start_utc.tz_localize("UTC").isoformat().replace("+00:00", "Z")
        d2_iso = end_utc.tz_localize("UTC").isoformat().replace("+00:00", "Z")

        # Récup & normalisation
        items: List[Dict[str, Any]] = eod_fetch(d1_iso, d2_iso, countries=countries or None, importance=None, api_key=None)
        if not items:
            st.warning("Aucun élément renvoyé par EODHD pour la fenêtre/pays donnés.")
            st.stop()

        raw_df = eod_norm(items)
        if raw_df is None or raw_df.empty:
            st.warning("Normalisation EODHD → DataFrame vide.")
            st.stop()

        # Nettoyages / types
        df = raw_df.copy()
        # ts_utc -> uniformisé (naïf UTC), ts_local formatté
        if "ts_utc" in df.columns:
            df["ts_utc"] = df["ts_utc"].apply(_to_utc_naive)
        df["ts_local"] = df["ts_utc"].apply(lambda t: _fmt_local(t, tz_name))

        # label_final : event_title -> label -> type
        # (évite .fillna(None) qui plante)
        label_final = pd.Series(pd.NA, index=df.index, dtype="object")
        for col in ["event_title", "label", "type"]:
            if col in df.columns:
                s = df[col].astype(str)
                s = s.where(s.str.len() > 0, pd.NA)
                label_final = label_final.fillna(s)
        df["label_final"] = label_final.astype(str)

        # Stats sur familles détectées (regex du preset)
        if regex:
            mask = (
                df.get("event_title", pd.Series([None]*len(df))).astype(str).str.contains(regex, case=False, regex=True, na=False)
                | df.get("event_key", pd.Series([None]*len(df))).astype(str).str.contains(regex, case=False, regex=True, na=False)
                | df.get("label", pd.Series([None]*len(df))).astype(str).str.contains(regex, case=False, regex=True, na=False)
                | df.get("type", pd.Series([None]*len(df))).astype(str).str.contains(regex, case=False, regex=True, na=False)
            )
            df["_fam_hit"] = mask
        else:
            df["_fam_hit"] = False

        # Quelle famille utiliser pour scorer ?
        fam_auto = get_family(preset) or None
        fam_used = fam_auto if (fam_auto or force_score) else None

        # Filtrage des événements à scorer
        df_score = df.copy()
        if fam_auto and not force_score:
            df_score = df_score[df_score["_fam_hit"] == True].copy()

        if df_score.empty:
            st.info("Aucune ligne scorable (famille non détectée et force désactivée).")
            with st.expander("Diagnostics"):
                st.json({
                    "period": [str(d_from), str(d_to)],
                    "countries": countries,
                    "received_rows": int(len(df)),
                    "regex_preset": regex,
                    "family_auto": fam_auto,
                    "force_score": force_score,
                    "db_path": get_db_path(),
                })
            st.stop()

        # Appel au moteur de forecast une seule fois par famille & fenêtre historique (évite charge)
        tf_hist = (_to_utc_naive(end_utc) - pd.DateOffset(years=int(hist_years)))
        tt_hist = _to_utc_naive(end_utc)

        horizons_min = list(map(int, horizons or [15, 30, 60]))
        family_for_engine = fam_used or "NFP"  # fallback si force_score sans preset
        req = ForecastRequest(
            event_family=family_for_engine,
            actual=0.0, consensus=0.0,  # pas utilisé dans l'algo historique
            country=(countries[0] if countries else "US"),  # filtre pays hist si dispo en base
            window_before_min=60,
            window_after_min=15,
            horizons=horizons_min,
            strict_decision=False,
        )

        stats, diags = forecast(req, include_regex=None, time_from=tf_hist, time_to=tt_hist, db_path=get_db_path())
        # On indexe les stats par horizon pour joindre ensuite
        by_h = {int(s.horizon): {"n": s.n, "p_up": s.p_up, "mfe_med": s.mfe_med, "mfe_p80": s.mfe_p80} for s in stats}

        # Projection d'impact pour chaque event sélectionné : on **réutilise** la même stat par horizon
        rows_out = []
        for _, r in df_score.iterrows():
            base = {
                "ts_local": r.get("ts_local"),
                "ts_utc": r.get("ts_utc"),
                "country": r.get("country"),
                "event_key": r.get("event_key"),
                "event_title": r.get("event_title"),
                "label": r.get("label"),
                "label_final": r.get("label_final"),
                "estimate": r.get("estimate"),
                "forecast": r.get("forecast"),
                "previous": r.get("previous"),
                "unit": r.get("unit"),
                "type": r.get("type"),
                "family_used": family_for_engine,
            }
            # pour chaque horizon, ajoute med/p80 attendus (hist)
            for h in horizons_min:
                s = by_h.get(int(h), {})
                base[f"h{h}_n"] = s.get("n")
                base[f"h{h}_p_up"] = s.get("p_up")
                base[f"h{h}_mfe_med"] = s.get("mfe_med")
                base[f"h{h}_mfe_p80"] = s.get("mfe_p80")
            rows_out.append(base)

        out_df = pd.DataFrame(rows_out)

        # Affichage
        st.subheader("📅 Événements scorable & impacts attendus (historiques)")
        # Colonnes principales visibles d’abord
        main_cols = ["ts_local", "ts_utc", "country", "label_final", "event_key", "event_title", "estimate", "forecast", "previous", "unit", "type", "family_used"]
        for c in main_cols:
            if c not in out_df.columns:
                out_df[c] = pd.NA
        # Colonnes d’impact triées par horizon
        impact_cols = []
        for h in horizons_min:
            impact_cols += [f"h{h}_n", f"h{h}_p_up", f"h{h}_mfe_med", f"h{h}_mfe_p80"]

        show_cols = main_cols + [c for c in impact_cols if c in out_df.columns]
        st.dataframe(out_df[show_cols].sort_values(["ts_utc", "country", "label_final"]), width="stretch", hide_index=True)

        # Export
        st.download_button(
            "⬇️ Export CSV (événements + impacts attendus)",
            data=out_df[show_cols].to_csv(index=False).encode("utf-8"),
            file_name=f"live_forecast_scored_{d_from}_{d_to}.csv",
            mime="text/csv",
        )

        # Résumé des stats historiques utilisées
        st.markdown("---")
        st.subheader("📊 Stats historiques utilisées (par horizon)")
        stats_df = pd.DataFrame([
            {"horizon_min": int(h), **by_h[int(h)]} for h in sorted(by_h.keys())
        ])
        if not stats_df.empty:
            st.dataframe(stats_df, width="stretch", hide_index=True)

        # Diagnostics
        with st.expander("Diagnostics"):
            st.json({
                "period": [str(d_from), str(d_to)],
                "countries": countries,
                "received_rows": int(len(df)),
                "kept_rows": int(len(df_score)),
                "regex_preset": regex,
                "family_auto": fam_auto,
                "family_used": family_for_engine,
                "hist_window_used": [str(tf_hist), str(tt_hist)],
                "db_path": get_db_path(),
                "diags_engine": diags,
            })

    except Exception as e:
        st.error("Erreur pendant le scoring.")
        st.exception(e)
