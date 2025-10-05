from __future__ import annotations
import datetime as dt
import pandas as pd
import streamlit as st

# API modèle (déjà en place dans ta V5)
from fx_impact_app.src.forecaster_mvp import (
    ForecastRequest,
    forecast,
    HORIZONS,
    compute_surprise,
)

# Presets centralisés
from fx_impact_app.src.regex_presets import PRESETS, preset_keys, get_regex, get_countries


st.set_page_config(page_title="Forecaster (Presets — V5)", layout="wide")
st.title("🔮 Forecaster (Presets — V5)")
st.caption(f"Loaded from: {__file__}")  # pour vérifier le bon fichier chargé


# -----------------------------
# UI — Presets & filtres
# -----------------------------
c0, c1 = st.columns([2, 2])

with c0:
    fam = st.selectbox("Famille (guidage seulement)", ["NFP", "CPI", "FOMC"], index=0)

    # Choix du preset
    choices = preset_keys()
    # petite heuristique: présélectionne un preset cohérent avec la famille
    default_idx = 0
    for i, k in enumerate(choices):
        if fam == "NFP" and "NFP" in k:
            default_idx = i
        elif fam == "CPI" and "CPI" in k:
            default_idx = i
        elif fam == "FOMC" and ("FOMC" in k or "Fed" in k):
            default_idx = i
    preset_key = st.selectbox("Preset (regex + pays suggérés)", choices, index=default_idx)

    # Regex préremplie par preset, éditable
    pattern = st.text_input(
        "Regex appliquée (event_key + event_title)",
        value=get_regex(preset_key),
        help="Expression régulière (insensible à la casse si préfixée par (?i)).",
    )

with c1:
    # Pays par défaut selon preset (le modèle prend un seul pays : on propose le 1er par défaut)
    preset_countries = get_countries(preset_key) or ["US"]
    country = st.selectbox(
        "Pays",
        options=["US", "EA", "EU", "GB", "UK", "DE", "FR", "CH", "CA", "JP", "CN"],
        index=max(0, ["US", "EA", "EU", "GB", "UK", "DE", "FR", "CH", "CA", "JP", "CN"].index(preset_countries[0]) if preset_countries[0] in ["US", "EA", "EU", "GB", "UK", "DE", "FR", "CH", "CA", "JP", "CN"] else 0)
    )

st.markdown("---")

# -----------------------------
# UI — Paramètres de calcul
# -----------------------------
c2, c3 = st.columns([3, 2])
with c2:
    actual = st.number_input("Actual (test)", value=250.0, step=1.0, format="%.2f")
    consensus = st.number_input("Consensus", value=180.0, step=1.0, format="%.2f")
    st.caption(f"Surprise % : {compute_surprise(actual, consensus):.2f}%")

with c3:
    horizons = st.multiselect("Horizons (min)", HORIZONS, default=HORIZONS)
    before = st.slider("Fenêtre before (min)", 0, 180, 60, 5)
    after = st.slider("Fenêtre after (min)", 0, 180, 15, 5)

st.markdown("---")

# Limitation temporelle (UTC)
use_dates = st.checkbox("Limiter l'historique par dates (UTC)", value=False)
d_from = d_to = None
if use_dates:
    c4, c5 = st.columns(2)
    with c4:
        d_from = st.date_input("De (UTC)")
    with c5:
        d_to = st.date_input("À (UTC)")

# -----------------------------
# Action
# -----------------------------
if st.button("Calculer", type="primary"):
    try:
        kwargs = {}
        if use_dates and d_from and d_to:
            # bornes jour UTC (00:00 → 23:59)
            kwargs["time_from"] = pd.Timestamp(dt.datetime.combine(d_from, dt.time(0, 0)), tz="UTC")
            kwargs["time_to"] = pd.Timestamp(dt.datetime.combine(d_to, dt.time(23, 59, 59)), tz="UTC")

        req = ForecastRequest(
            event_family=fam,
            actual=float(actual),
            consensus=float(consensus),
            country=country,
            window_before_min=int(before),
            window_after_min=int(after),
            horizons=[int(h) for h in horizons] or list(HORIZONS),
        )

        stats, diags = forecast(req, include_regex=pattern, **kwargs)

        # Résultats
        rows = [
            {
                "horizon_min": s.horizon,
                "n": s.n,
                "p_up": s.p_up,
                "mfe_med": s.mfe_med,
                "mfe_p80": s.mfe_p80,
            }
            for s in stats
        ]

        st.subheader("Résultats")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        with st.expander("Diagnostics"):
            st.json({
                "preset": preset_key,
                "regex": pattern,
                **diags
            })

    except Exception as e:
        st.error("Erreur pendant le calcul.")
        st.exception(e)
