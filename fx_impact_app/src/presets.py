
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Preset:
    key: str
    label: str
    include_regex: Optional[str] = None
    countries: Optional[List[str]] = None

PRESETS = [
    Preset(key="FOMC_US", label="FOMC (Fed, US)", include_regex=r"(fomc|fed funds|rate decision)", countries=["US"]),
    Preset(key="CPI_US",  label="CPI (US)", include_regex=r"\bcpi\b|consumer price", countries=["US"]),
    Preset(key="NFP_US",  label="NFP (US)", include_regex=r"(nonfarm|non-farm|nfp)", countries=["US"]),
    Preset(key="ECB_EA",  label="ECB (EA/EU)", include_regex=r"\becb\b|main refinancing|deposit facility", countries=["EA","EU"]),
]

def by_label(label: str) -> Preset:
    for p in PRESETS:
        if p.label == label: return p
    return PRESETS[0]
# fx_impact_app/src/regex_presets.py
from __future__ import annotations
from typing import Dict, List, Tuple

# Presets lisibles côté UI
REGEX_PRESETS: Dict[str, str] = {
    # US — Emploi / inflation / banques centrales
    "NFP (US)": r"(?i)(nonfarm|non-farm|nfp|payrolls|employment)",
    "Unemployment rate (US)": r"(?i)\bunemployment\b|\bjobless\b",
    "Average Hourly Earnings (US)": r"(?i)average hourly earnings|ahe",
    "CPI (US)": r"(?i)\bcpi\b|consumer price",
    "Core CPI (US)": r"(?i)core cpi|core consumer price",
    "PCE / Core PCE (US)": r"(?i)\bpce\b|core pce|personal consumption",
    "Retail Sales (US)": r"(?i)retail sales",
    "ISM Manufacturing (US)": r"(?i)\bism\b.*manufacturing|manufacturing pmi|s&p global .*manufacturing",
    "ISM Services (US)": r"(?i)\bism\b.*services|services pmi|s&p global .*services",
    "GDP (US)": r"(?i)\bgdp\b|gross domestic product",
    "Initial Jobless Claims (US)": r"(?i)initial (jobless|unemployment) claims",
    "FOMC (Fed, US)": r"(?i)fomc|fed funds|rate decision|interest rate|dot plot|press conference",

    # Eurozone / Allemagne / France / UK
    "CPI (EA/EU)": r"(?i)(hicp|cpi).*(ea|euro|eurozone|euro area)",
    "ECB (EA/EU)": r"(?i)ecb|main refinancing|deposit facility|marginal lending|rate decision|press conference",
    "PMI (EA/EU)": r"(?i)pmi|s&p global",
    "GDP (EA/EU)": r"(?i)\bgdp\b|gross domestic product",
    "ZEW (DE)": r"(?i)\bzew\b",
    "IFO (DE)": r"(?i)\bifo\b",
    "CPI (DE)": r"(?i)(hicp|cpi).*(germany|deutschland|de\\b)",
    "CPI (FR)": r"(?i)(hicp|cpi).*(france|fr\\b)",
    "BoE / Rate Decision (UK)": r"(?i)bank of england|boe|rate decision|bank rate",

    # Génériques utiles
    "Any Rate Decision": r"(?i)rate decision|monetary policy decision|policy rate",
    "Press conference (CB)": r"(?i)press conference|statement|minutes",
    "Housing (US)": r"(?i)(housing starts|building permits|existing home sales|new home sales)",
}

def preset_names() -> List[str]:
    return list(REGEX_PRESETS.keys())

def pattern_for(name: str) -> str:
    return REGEX_PRESETS.get(name, r"(?i).")

def regex_selectbox(label: str = "Preset (regex)",
                    default: str | None = None,
                    help: str | None = None) -> Tuple[str, str]:
    """
    Composant Streamlit prêt-à-l’emploi.
    Retourne (pattern, name) selon la sélection.
    """
    import streamlit as st
    names = preset_names()
    idx = names.index(default) if default in names else 0
    name = st.selectbox(label, names, index=idx, help=help)
    pattern = REGEX_PRESETS[name]
    with st.expander("Voir le regex"):
        st.code(pattern)
    return pattern, name

