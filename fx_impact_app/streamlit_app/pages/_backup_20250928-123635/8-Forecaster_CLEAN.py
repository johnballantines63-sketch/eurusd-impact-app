# fx_impact_app/streamlit_app/pages/8_Forecaster_CLEAN.py

import datetime as dt
import pandas as pd
import streamlit as st

# Import du moteur de forecast (doit exister dans src/forecaster_mvp.py)
from fx_impact_app.src.forecaster_mvp import (
    ForecastRequest,
    forecast,
    HORIZONS,
    compute_surprise,
)

st.set_page_config(page_title="Forecaster (MVP — clean)", layout="wide")
st.title("🔮 Forecaster (MVP — clean)")
st.caption(f"Loaded from: {__file__}")

# -----------------------------
# Entrées utilisateur
# -----------------------------
c1, c2 = st.columns([3, 2])

with c1:
    family = st.selectbox("Famille d’événements", ["NFP", "CPI", "FOMC"], index=0)
    country = st.selectbox("Pays", ["US", "EA", "EU", "GB", "DE", "FR"], index=0)
    actual = st.number_input("Actual", value=250.0, step=1.0, format="%.2f")
    consensus = st.number_input("Consensus", value=180.0, step=1.0, format="%.2f")
    st.caption(f"Surprise % : {compute_surprise(actual, consensus):.2f}%")

with c2:
    horizons = st.multiselect("Horizons (min)", HORIZONS, default=HORIZONS)
    before = st.slider("Fenêtre before (min)", 0, 180, 60, 5)
    after = st.slider("Fenêtre after (min)", 0, 180, 15, 5)

    use_dates = st.checkbox("Limiter l'historique par dates (UTC)", value=False)
    d_from = d_to = None
    if use_dates:
        d_from = st.date_input("De (UTC)")
        d_to = st.date_input("À (UTC)")

# -----------------------------
# Action
# -----------------------------
if st.button("Calculer", type="primary"):
    try:
        kwargs = {}
        if use_dates and d_from and d_to:
            kwargs["time_from"] = pd.Timestamp(dt.datetime.combine(d_from, dt.time(0, 0)), tz="UTC")
            kwargs["time_to"] = pd.Timestamp(dt.datetime.combine(d_to, dt.time(23, 59, 59)), tz="UTC")

        req = ForecastRequest(
            event_family=family,
            actual=float(actual),
            consensus=float(consensus),
            country=country,
            window_before_min=int(before),
            window_after_min=int(after),
            horizons=[int(h) for h in horizons] or list(HORIZONS),
        )

        stats, diags = forecast(req, **kwargs)

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
            st.json(diags)

    except Exception as e:
        st.error("Erreur pendant le calcul.")
        st.exception(e)
