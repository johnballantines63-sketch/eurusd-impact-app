# fx_impact_app/streamlit_app/pages/11_Glossary.py
from __future__ import annotations
import streamlit as st
import pandas as pd

# Optional UI helper
try:
    from fx_impact_app.streamlit_app._ui import apply_sidebar_index
except Exception:
    def apply_sidebar_index(_: str | int) -> None:
        return

st.set_page_config(page_title="Glossary — EN", layout="wide")
apply_sidebar_index("11")
st.title("📖 Glossary — EN")
st.caption(f"Page: {__file__}")

rows = [
    ("hist_n", "Raw history size after filtering (row count)."),
    ("hist_n_unique_ts", "Count of distinct event timestamps (deduped same-instant rows)."),
    ("n", "Number of occurrences effectively used for stats at a given horizon."),
    ("p_up", "Probability that close at horizon H is above entry (0→1)."),
    ("MFE", "Maximum Favorable Excursion: best run-up (in pips) after entry within the window."),
    ("mfe_med", "Median MFE (in pips)."),
    ("mfe_p80", "80th percentile of MFE (in pips)."),
    ("horizon", "Time window (minutes) for computing p_up and MFE."),
    ("window_before_min", "Minutes before the event included for context/entry."),
    ("window_after_min", "Minutes after the event to measure impact."),
    ("event_family", "Event group (NFP, CPI, FOMC…) mapped via a detection regex."),
    ("regex", "Regular expression applied to event_key/event_title to select the group."),
    ("surprise %", "((Actual − Consensus) / |Consensus|) × 100, for conditional scenarios."),
    ("anchor_ts", "Anchor timestamp of a simultaneous events cluster."),
    ("n_simul", "Number of events within ±X minutes around the anchor."),
    ("preset", "Preconfigured set of regex + country (e.g., “FOMC (US) — Large”)."),
    ("country", "Event country code (US, EU/EA, GB/UK, DE, FR, …)."),
]

df = pd.DataFrame(rows, columns=["Term", "Definition"])
st.dataframe(df, width="stretch", hide_index=True)

st.markdown("---")
st.markdown("Need another term? Ping me and I’ll add it.")
