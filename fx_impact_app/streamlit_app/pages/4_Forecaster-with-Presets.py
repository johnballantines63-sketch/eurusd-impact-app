from __future__ import annotations
from datetime import datetime, time
import pandas as pd, streamlit as st
from fx_impact_app.streamlit_app._ui import apply_sidebar_index
apply_sidebar_index("Home")

st.set_page_config(page_title="Forecaster (with presets)", layout="wide")
st.title("🔮 Forecaster (with presets)")
st.caption(f"Loaded from: {__file__}")

try:
    from fx_impact_app.src.forecaster_mvp import ForecastRequest, forecast, HORIZONS, compute_surprise
except Exception as e:
    st.error("Impossible d'importer fx_impact_app.src.forecaster_mvp")
    st.exception(e)
    st.stop()

from fx_impact_app.src.regex_presets import regex_selectbox, default_preset_for_family, coalesce_regex

c1, c2 = st.columns([3,2])
with c1:
    family = st.selectbox("Famille d’événements", ["NFP", "CPI", "FOMC"], index=0)
    country = st.selectbox("Pays", ["US", "EA", "EU", "GB", "DE", "FR"], index=0)
    actual = st.number_input("Actual", value=250.0, step=1.0, format="%.2f")
    consensus = st.number_input("Consensus", value=180.0, step=1.0, format="%.2f")
    st.caption(f"Surprise % : {compute_surprise(actual, consensus):.2f}%")

with c2:
    horizons = st.multiselect("Horizons (min)", HORIZONS, default=HORIZONS)
    before = st.slider("Fenêtre before (min)", 0, 180, 60, 5)
    after  = st.slider("Fenêtre after (min)", 0, 180, 15, 5)
    use_dates = st.checkbox("Limiter l'historique par dates (UTC)", value=False)
    d_from = d_to = None
    if use_dates:
        d_from = st.date_input("De (UTC)")
        d_to   = st.date_input("À (UTC)")

st.markdown("---")
st.subheader("🎯 Filtre par presets (regex)")
preset_default = default_preset_for_family(family)
preset_pattern, preset_name = regex_selectbox("Preset", default=preset_default, help="Géré dans src/regex_presets.py")
regex_free = st.text_input("Regex personnalisé (optionnel)", value="")
pattern = coalesce_regex(preset_name, regex_free)
st.caption(f"Regex appliqué : `{pattern}` (preset : {preset_name})")

if st.button("Calculer", type="primary"):
    try:
        kwargs = {}
        if use_dates and d_from and d_to:
            kwargs["time_from"] = pd.Timestamp(datetime.combine(d_from, time(0,0)), tz="UTC")
            kwargs["time_to"]   = pd.Timestamp(datetime.combine(d_to,   time(23,59)), tz="UTC")

        req = ForecastRequest(
            event_family=family, actual=float(actual), consensus=float(consensus),
            country=country, window_before_min=int(before), window_after_min=int(after),
            horizons=[int(h) for h in (horizons or HORIZONS)]
        )
        stats, diags = forecast(req, include_regex=pattern, **kwargs)

        rows = [{"horizon_min": s.horizon, "n": s.n, "p_up": s.p_up, "mfe_med": s.mfe_med, "mfe_p80": s.mfe_p80} for s in stats]
        st.subheader("Résultats")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        with st.expander("Diagnostics"):
            st.json(diags)
            hn = diags.get("hist_n"); hu = diags.get("hist_n_unique_ts")
            if hn is not None or hu is not None:
                st.caption(f"Événements (bruts / uniques) : {hn} / {hu}")
    except Exception as e:
        st.error("Erreur pendant le calcul.")
        st.exception(e)
