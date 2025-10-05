# fx_impact_app/streamlit_app/pages/10_Lexique.py
from __future__ import annotations
import streamlit as st
import pandas as pd

# Utilitaire menu (optionnel)
try:
    from fx_impact_app.streamlit_app._ui import apply_sidebar_index
except Exception:
    def apply_sidebar_index(_: str | int) -> None:
        return

st.set_page_config(page_title="Lexique — FR", layout="wide")
apply_sidebar_index("10")
st.title("📖 Lexique — FR")
st.caption(f"Page: {__file__}")

# Définitions
rows = [
    ("hist_n", "Taille brute de l’historique filtré (nombre de lignes d’événements)."),
    ("hist_n_unique_ts", "Nombre d’horodatages d’événements distincts (évite les doublons au même instant)."),
    ("n", "Nombre d’occurrences réellement utilisées pour calculer les stats à un horizon donné."),
    ("p_up", "Probabilité que la clôture à l’horizon H soit au-dessus du prix d’entrée (0→1)."),
    ("MFE", "Maximum Favorable Excursion : meilleure progression (en pips) atteinte sur la fenêtre après l’entrée."),
    ("mfe_med", "Médiane du MFE (en pips)."),
    ("mfe_p80", "80e centile du MFE (en pips) — 80% des cas ont un MFE ≤ cette valeur."),
    ("horizon", "Fenêtre temporelle (en minutes) pour mesurer p_up et MFE."),
    ("window_before_min", "Minutes avant l’événement incluses pour le contexte (entrée)."),
    ("window_after_min", "Minutes après l’événement utilisées pour mesurer l’impact."),
    ("event_family", "Groupe d’événements (NFP, CPI, FOMC…) mappé via un regex de détection."),
    ("regex", "Expression régulière appliquée à event_key/event_title pour sélectionner les événements du groupe."),
    ("surprise %", "((Actual - Consensus) / |Consensus|) × 100. Sert pour les scénarios conditionnels."),
    ("anchor_ts", "Horodatage d’ancrage d’un cluster d’événements simultanés."),
    ("n_simul", "Nombre d’événements dans ±X min autour de l’ancrage."),
    ("preset", "Ensemble préconfiguré de regex + pays (ex: “FOMC (US) — Large”)."),
    ("country", "Code pays de l’événement (US, EU/EA, GB/UK, DE, FR, …)."),
]

df = pd.DataFrame(rows, columns=["Terme", "Définition"])
st.dataframe(df, width="stretch", hide_index=True)

st.markdown("---")
st.markdown(
    "Besoin d’un terme en plus ? Ouvre une issue “Docs” ou dis-le moi et je l’ajoute."
)
