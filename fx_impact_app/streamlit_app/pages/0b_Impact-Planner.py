# fx_impact_app/streamlit_app/pages/0b_Impact-Planner.py
from __future__ import annotations

import os
from typing import Dict, List, Optional
from datetime import datetime, time as dt_time

import duckdb
import pandas as pd
import requests
import streamlit as st
from zoneinfo import ZoneInfo

from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.forecaster_mvp import ForecastRequest, forecast

# ------------------------------------------------------------
# Config UI
# ------------------------------------------------------------
st.set_page_config(page_title="Impact Planner – Sélection d'événements", page_icon="🗓️", layout="wide")
st.title("🗓️ Impact Planner (sélection basée sur impact/latence/retournement)")

# ------------------------------------------------------------
# Familles / regex (aligné avec le moteur)
# ------------------------------------------------------------
FAMILY_REGEX: Dict[str, str] = {
    "NFP": r"(nonfarm|non-farm|nfp|payrolls|employment|adp)",
    "CPI": r"(cpi|inflation|consumer price)",
    "FOMC": r"(fomc|fed (rate|interest)|policy statement|dot ?plot|press conference|powell)",
}
FAMILY_PRESETS = ["NFP", "CPI", "FOMC"]

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def safe_str(x) -> str:
    try:
        if x is None or pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x)

def parse_ts_utc(x) -> Optional[pd.Timestamp]:
    """Retourne un Timestamp UTC *naïf* (sans tzinfo)."""
    if x is None:
        return None
    try:
        ts = pd.to_datetime(x, utc=True)
        return pd.Timestamp(ts.tz_convert("UTC").tz_localize(None))
    except Exception:
        return None

def detect_family(row: pd.Series) -> Optional[str]:
    """Détecte la famille en cherchant dans tous les champs textuels."""
    hay = " ".join([
        safe_str(row.get("event_title")),
        safe_str(row.get("type")),
        safe_str(row.get("event_key")),
        safe_str(row.get("label")),
        safe_str(row.get("category")),
    ]).lower()
    
    for fam, rgx in FAMILY_REGEX.items():
        if pd.Series([hay]).str.contains(rgx, regex=True, na=False).iloc[0]:
            return fam
    return None

def normalize_eod_row(it: dict) -> dict:
    """
    Normalise une ligne EODHD en extrayant tous les champs possibles.
    EODHD renvoie principalement 'type' comme identifiant de l'événement.
    """
    # Timestamp - essaie plusieurs formats
    ts = it.get("timestamp") or it.get("datetime") or it.get("date") or it.get("time")
    if isinstance(ts, (int, float)) and not pd.isna(ts):
        ts_utc = pd.Timestamp.utcfromtimestamp(int(ts))
    else:
        if it.get("date") and it.get("time"):
            ts_utc = parse_ts_utc(f"{it['date']} {it['time']}")
        else:
            ts_utc = parse_ts_utc(ts)

    def num(v):
        try:
            if v is None or pd.isna(v):
                return None
            return float(str(v).replace(",", "."))
        except Exception:
            return None

    # Importance
    imp = it.get("importance")
    try:
        imp_n = int(imp) if imp is not None and str(imp).strip().isdigit() else None
    except Exception:
        imp_n = None

    # CORRECTION CRITIQUE : EODHD utilise 'type' comme champ principal
    # Ordre de priorité : type > event > title > indicator > name
    event_title = (
        it.get("type") or        # EODHD principal
        it.get("event") or 
        it.get("title") or 
        it.get("indicator") or 
        it.get("name") or 
        None
    )
    
    # event_key : dérivé du type en minuscules
    event_key = (
        safe_str(it.get("type")).lower() or
        it.get("event_id") or
        it.get("id") or
        it.get("code") or
        safe_str(event_title).lower() or
        None
    )
    
    # Type/catégorie (séparé de event_title maintenant)
    event_type = (
        it.get("category") or
        it.get("group") or
        it.get("type") or
        None
    )

    return {
        "ts_utc": ts_utc,
        "country": safe_str(it.get("country")).upper() or None,
        "event_title": event_title,
        "event_key": event_key,
        "type": event_type,
        "label": it.get("label") or it.get("shortname") or None,
        "category": it.get("category") or None,
        "importance_n": imp_n,
        "estimate": num(it.get("estimate")),
        "forecast": num(it.get("forecast")),
        "previous": num(it.get("previous")),
        "actual": num(it.get("actual")),
        "unit": it.get("unit") or None,
    }

def fetch_eodhd_day(day_utc: pd.Timestamp, countries: List[str], api_key: str) -> List[dict]:
    base = "https://eodhd.com/api/economic-events"
    params = {
        "from": day_utc.strftime("%Y-%m-%d"),
        "to": day_utc.strftime("%Y-%m-%d"),
        "fmt": "json",
        "api_token": api_key,
        "countries": ",".join(countries) if countries else None,
    }
    params = {k: v for k, v in params.items() if v is not None}
    r = requests.get(base, params=params, timeout=20)
    r.raise_for_status()
    data = r.json() if r.text else []
    return data if isinstance(data, list) else []

def annotate_with_stats(df: pd.DataFrame, stats_by_family: Dict[str, dict]) -> pd.DataFrame:
    def _m(row):
        fam = row.get("family")
        s = stats_by_family.get(fam) if fam else None
        if not s:
            return pd.Series({
                "exp_mfe_med": None, "exp_mfe_p80": None,
                "exp_latency_med": None, "exp_ttr_med": None
            })
        return pd.Series({
            "exp_mfe_med": s.get("mfe_med"),
            "exp_mfe_p80": s.get("mfe_p80"),
            "exp_latency_med": s.get("latency_med"),
            "exp_ttr_med": s.get("ttr_med"),
        })
    return pd.concat([df, df.apply(_m, axis=1)], axis=1)

def compute_stats_by_family(families: List[str], horizon: int, hist_years: int, country: str | None) -> Dict[str, dict]:
    """Calcule les stats historiques pour chaque famille."""
    out: Dict[str, dict] = {}
    hist_to = pd.Timestamp.utcnow()
    hist_from = hist_to - pd.DateOffset(years=int(hist_years))

    for fam in families:
        try:
            req = ForecastRequest(
                event_family=fam,
                actual=0.0, consensus=0.0,
                country=(country or "US"),
                horizons=[horizon],
                window_before_min=60,
                window_after_min=60,
                thr_pips=10.0,
                rev_pips=5.0,
            )
            stats, _diags = forecast(req, time_from=hist_from, time_to=hist_to)
            if stats:
                s = stats[0]
                out[fam] = {
                    "p_up": getattr(s, "p_up", None),
                    "mfe_med": getattr(s, "mfe_med", None),
                    "mfe_p80": getattr(s, "mfe_p80", None),
                    "latency_med": getattr(s, "latency_med", None),
                    "latency_p80": getattr(s, "latency_p80", None),
                    "ttr_med": getattr(s, "ttr_med", None),
                    "ttr_p80": getattr(s, "ttr_p80", None),
                    "hist_from": str(hist_from),
                    "hist_to": str(hist_to),
                }
        except Exception as e:
            out.setdefault(fam, {})
    return out

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.header("Paramètres")
    
    # Choix du mode : UTC direct ou fuseau local
    mode = st.radio("Mode de sélection de date", ["UTC (recommandé)", "Fuseau local"], index=0)
    
    if mode == "UTC (recommandé)":
        tz_name = "UTC"
        date_utc = st.date_input("Jour (UTC)", value=pd.Timestamp.now(tz="UTC").date())
        tz_display = st.selectbox("Fuseau d'affichage", 
                                   ["UTC", "Europe/Zurich", "Europe/Paris", "America/New_York", "Europe/London"],
                                   index=1)
    else:
        tz_name = st.selectbox("Fuseau horaire", 
                              ["Europe/Zurich", "UTC", "Europe/Paris", "America/New_York", "Europe/London"],
                              index=0)
        date_utc = st.date_input("Jour (local)", value=pd.Timestamp.now(tz=ZoneInfo(tz_name)).date())
        tz_display = tz_name
        st.warning("⚠️ Mode local : la fenêtre UTC peut chevaucher 2 jours")
    
    countries = st.multiselect("Pays", ["US", "EU"], default=["US"])
    fams = st.multiselect("Familles", FAMILY_PRESETS, default=FAMILY_PRESETS)
    importance_sel = st.multiselect("Importance (EODHD)", [1, 2, 3], default=[1, 2, 3])

    horizon = st.selectbox("Horizon (minutes)", [15, 30, 60], index=1)
    hist_years = st.number_input("Historique (années)", min_value=1, max_value=5, value=3, step=1)

    impact_min, impact_max = st.slider("Filtre impact attendu (MFE P80, pips)", 0, 80, (0, 80))
    lat_min, lat_max = st.slider("Filtre latence médiane (minutes)", 0, 120, (0, 120))
    ttr_min, ttr_max = st.slider("Filtre durée médiane avant renversement (minutes)", 0, 240, (0, 231))

    run_btn = st.button("🔎 Charger & filtrer")

# ------------------------------------------------------------
# Corps
# ------------------------------------------------------------
api_key = os.environ.get("EODHD_API_KEY", "").strip()
if not api_key:
    st.error("EODHD_API_KEY manquant dans l'environnement. Ajoute-le à ton `.env` puis relance.")
    st.stop()

# ------------------------------------------------------------
# Fenêtre du jour - Gestion intelligente du fuseau
# ------------------------------------------------------------
if mode == "UTC (recommandé)":
    # Mode UTC : simple et direct, pas de conversion
    start_utc = pd.Timestamp(datetime.combine(date_utc, dt_time(0, 0)))
    end_utc = pd.Timestamp(datetime.combine(date_utc, dt_time(23, 59, 59)))
else:
    # Mode local : convertit le jour local en fenêtre UTC
    start_local_dt = datetime.combine(date_utc, dt_time(0, 0))
    end_local_dt = datetime.combine(date_utc, dt_time(23, 59, 59))
    
    start_local = pd.Timestamp(start_local_dt).tz_localize(ZoneInfo(tz_name))
    end_local = pd.Timestamp(end_local_dt).tz_localize(ZoneInfo(tz_name))
    
    start_utc = start_local.tz_convert("UTC").tz_localize(None)
    end_utc = end_local.tz_convert("UTC").tz_localize(None)

# --- Fetch du jour ---
raw: List[dict] = []
err_fetch = None
try:
    # TEST : Récupère TOUS les pays (pas de filtre API)
    # Le filtrage se fait après via le multiselect "Pays" de la sidebar
    raw = fetch_eodhd_day(start_utc, [], api_key)
except Exception as e:
    err_fetch = str(e)

norm = pd.DataFrame([normalize_eod_row(it) for it in raw]) if raw else pd.DataFrame()

# Filtrage sur la fenêtre du jour (UTC)
if not norm.empty:
    norm = norm.dropna(subset=["ts_utc"])
    mask = (norm["ts_utc"] >= start_utc) & (norm["ts_utc"] < end_utc)
    norm = norm.loc[mask].copy()
else:
    norm = pd.DataFrame(columns=["ts_utc","country","event_title","event_key","type","importance_n","estimate","forecast","previous","actual","unit"])

# ============================================================
# DÉBOGAGE : Affichage des événements bruts reçus
# ============================================================
if not norm.empty:
    st.subheader("🔍 DEBUG : Événements bruts reçus (avant détection famille)")
    debug_cols = ["ts_utc", "country", "event_title", "event_key", "type", "category", "label", "importance_n"]
    st.dataframe(norm[[c for c in debug_cols if c in norm.columns]], use_container_width=True)
    st.caption(f"Total reçu : {len(norm)} événements")
    
    # Affiche aussi les données brutes JSON pour diagnostic
    with st.expander("Voir JSON brut EODHD (premier événement)"):
        if raw:
            st.json(raw[0])
    
    st.markdown("---")
# ============================================================

# Détection famille + label + ts local (utilise tz_display)
if not norm.empty:
    norm["family"] = norm.apply(detect_family, axis=1)
    norm["label_final"] = norm["event_title"].fillna(norm["type"]).fillna(norm["event_key"])
    norm["ts_local"] = norm["ts_utc"].apply(lambda t: pd.Timestamp(t, tz="UTC").tz_convert(ZoneInfo(tz_display)).strftime("%Y-%m-%d %H:%M"))

norm = norm.sort_values("ts_utc", kind="stable").reset_index(drop=True)

# Stats par famille
stats_by_family: Dict[str, dict] = {}
err_stats = None
if fams:
    try:
        country_for_stats = "US" if "US" in countries else (countries[0] if countries else "US")
        stats_by_family = compute_stats_by_family(fams, horizon, hist_years, country_for_stats)
    except Exception as e:
        err_stats = str(e)

if fams and not any(stats_by_family.get(f) for f in fams):
    st.warning("Stats par famille indisponibles. Les filtres d'impact/latence/TTR seront inopérants.")

if not norm.empty and stats_by_family:
    norm = annotate_with_stats(norm, stats_by_family)

# Filtres
df = norm.copy()
if not df.empty:
    if countries:
        df = df[df["country"].isin(countries)]
    if fams:
        df = df[df["family"].isin(fams)]
    if importance_sel:
        df = df[df["importance_n"].isin(importance_sel)]
    if "exp_mfe_p80" in df.columns:
        df = df[df["exp_mfe_p80"].between(impact_min, impact_max, inclusive="both")]
    if "exp_latency_med" in df.columns:
        df = df[df["exp_latency_med"].fillna(99999).between(lat_min, lat_max, inclusive="both")]
    if "exp_ttr_med" in df.columns:
        df = df[df["exp_ttr_med"].fillna(99999).between(ttr_min, ttr_max, inclusive="both")]

# Affichage
cols_show = [
    "ts_local", "country", "family", "importance_n",
    "event_title", "type", "unit",
    "exp_mfe_p80", "exp_mfe_med", "exp_latency_med", "exp_ttr_med"
]
st.subheader("Sélection d'événements (filtrés)")
if df.empty:
    st.info("Aucun événement ne correspond aux filtres actuels pour ce jour.")
else:
    st.dataframe(df[[c for c in cols_show if c in df.columns]], use_container_width=True, height=380)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "💾 Exporter la sélection (CSV)",
        data=csv,
        file_name=f"impact_selection_{start_utc.date()}_{'_'.join(countries) if countries else 'ALL'}.csv",
        mime="text/csv",
    )

# Diagnostics
with st.expander("Diagnostics"):
    st.write("Params")
    st.json({
        "db_path": get_db_path(),
        "mode": mode,
        "period": [str(start_utc.date()), str(end_utc.date())],
        "tz_display": tz_display,
        "countries": countries,
        "families_selected": fams,
        "horizon_selected": horizon,
        "hist_years": hist_years,
        "impact_filter_p80": [impact_min, impact_max],
        "latency_filter_med": [lat_min, lat_max],
        "ttr_filter_med": [ttr_min, ttr_max],
    })
    st.write("Réception EODHD")
    st.json({
        "received_rows": len(raw),
        "normalized_rows": int(len(norm)),
        "family_counts_detected": ({} if norm.empty else norm["family"].value_counts(dropna=False).to_dict()),
        "stats_by_family": stats_by_family,
        "fetch_error": err_fetch,
        "stats_error": err_stats,
        "source": "eodhd_live",
    })
