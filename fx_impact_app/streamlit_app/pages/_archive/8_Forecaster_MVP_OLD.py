# fx_impact_app/streamlit_app/pages/8_Forecaster_MVP.py
from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Any, Iterable
from dataclasses import asdict, is_dataclass

# --- imports projet ---
from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.presets import PRESETS, by_label
from fx_impact_app.src.forecaster_mvp import (
    ForecastRequest,
    forecast,
    compute_surprise,
)

# --------------------------------------------------------------------
# Petite compat : wrapper qui ne passe à forecast() que les kwargs supportés
# --------------------------------------------------------------------
def _forecast(req: ForecastRequest, **kwargs):
    from inspect import signature

    params = signature(forecast).parameters
    accepted = {k: v for k, v in kwargs.items() if k in params}
    return forecast(req, **accepted)


# --------------------------------------------------------------------
# Utils d'affichage
# --------------------------------------------------------------------
def _stats_to_df(stats: Any) -> pd.DataFrame:
    """Convertit la sortie stats (liste de dataclasses / objets / DF) en DataFrame."""
    if isinstance(stats, pd.DataFrame):
        return stats.copy()

    # liste ? dicts ? dataclasses ?
    if isinstance(stats, Iterable) and not isinstance(stats, (str, bytes, dict)):
        rows = []
        for x in stats:
            if is_dataclass(x):
                rows.append(asdict(x))
            elif hasattr(x, "__dict__"):
                rows.append({k: v for k, v in vars(x).items() if not k.startswith("_")})
            else:
                rows.append({"value": str(x)})
        if rows:
            return pd.DataFrame(rows)

    if isinstance(stats, dict):
        return pd.DataFrame([stats])

    # fallback
    return pd.DataFrame([{"result": str(stats)}])


# --------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------
st.set_page_config(page_title="Forecaster (MVP — V5 full)", layout="wide")
st.title("🔮 Forecaster (MVP — V5 full) — NFP / CPI / FOMC")
st.caption("Empirique: direction, MFE attendue, persistance. DB: " + get_db_path())

# --------------------------------------------------------------------
# Panneau paramètres
# --------------------------------------------------------------------
colL, colR = st.columns([1.2, 1])

with colL:
    # Preset (récupère regex & pays par défaut)
    preset_label = st.selectbox("Préréglages", [p.label for p in PRESETS], index=0)
    preset = by_label(preset_label)

    family = st.selectbox("Famille d’événements", ["NFP", "CPI", "FOMC"], index=0)
    country = st.selectbox(
        "Pays",
        ["US", "EA", "EU", "UK", "DE", "FR", "IT", "ES", "JP", "CN"],
        index=0 if not preset.countries else max(0, ["US", "EA", "EU", "UK", "DE", "FR", "IT", "ES", "JP", "CN"].index(preset.countries[0]) if preset.countries[0] in ["US", "EA", "EU", "UK", "DE", "FR", "IT", "ES", "JP", "CN"] else 0),
    )

    actual = st.number_input("Actual", value=0.0, step=0.1, format="%.2f")
    consensus = st.number_input("Consensus (forecast/estimate)", value=0.0, step=0.1, format="%.2f")

    # Surprise % informative
    try:
        surpr = compute_surprise(actual, consensus)
        st.write(f"**Surprise %** : {surpr:.2f} %")
    except Exception:
        st.write("**Surprise %** : —")

with colR:
    # Horizons en minutes -> tags MFE
    HORIZON_TAGS = {
        1: "mfe_1m_pips",
        5: "mfe_5m_pips",
        15: "mfe_15m_pips",
        30: "mfe_30m_pips",
        60: "mfe_1h_pips",
    }
    horizons_min = st.multiselect(
        "Horizons MFE (minutes)",
        [1, 5, 15, 30, 60],
        default=[15, 30, 60],
        key="horizons_min",
    )
    horizons_tags = [HORIZON_TAGS[m] for m in horizons_min if m in HORIZON_TAGS]

    win_before = st.slider("Fenêtre before (min)", 0, 180, 60, 5)
    win_after = st.slider("Fenêtre after (min)", 0, 180, 15, 5)
    strict = st.checkbox("Décision stricte (FOMC)", value=(family == "FOMC"))

# Regex (depuis le preset, modifiable)
regex_default = preset.include_regex or ""
regex = st.text_input("Filtre regex (optionnel)", value=regex_default, help="Laisse vide pour ne pas filtrer côté base.")

st.divider()

# --------------------------------------------------------------------
# Action
# --------------------------------------------------------------------
if st.button("Calculer", type="primary"):
    try:
        # Construire la requête
        req = ForecastRequest(
            event_family=family,
            actual=float(actual),
            consensus=float(consensus),
            country=country,
            window_before_min=int(win_before),
            window_after_min=int(win_after),
            horizons=horizons_tags,      # IMPORTANT: on passe les tags MFE
            strict_decision=bool(strict),
        )

        # Appel modèle (on force db_path vers la V5)
        stats, diags = _forecast(
            req,
            include_regex=(regex or None),
            db_path=get_db_path(),
        )

        # Rendu résultats
        df = _stats_to_df(stats)
        if not df.empty:
            # Colonnes d'intérêt si présentes
            cols_pref = [c for c in ["horizon", "support", "n", "p_up", "mfe_med", "mfe_p80"] if c in df.columns]
            # Détecte des colonnes MFE dynamiques éventuelles
            mfe_cols = [c for c in df.columns if c.startswith("mfe_") and c.endswith("_pips")]
            ordered = cols_pref + [c for c in df.columns if c not in cols_pref and c not in mfe_cols] + mfe_cols

            st.subheader("Résultats")
            st.dataframe(df[ordered], hide_index=True, use_container_width=True)
        else:
            st.info("Aucun résultat calculé (vérifie les données / horizons).")

        # Diagnostics utiles
        with st.expander("Diagnostics"):
            diag_keep = {k: diags.get(k) for k in ["hist_n", "regex", "db_path", "bin_label", "hist_query", "moves_hint"] if k in diags}
            st.json(diag_keep or diags or {"note": "Aucun diagnostic fourni."})

    except Exception as e:
        st.error(f"Erreur pendant le calcul: {e}")

# Fin de page
