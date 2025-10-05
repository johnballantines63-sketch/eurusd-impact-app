# fx_impact_app/src/regex_presets.py
"""
Presets regex pour filtrage d'événements macro-économiques.
Version unifiée compatible avec toutes les pages.
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional

# ============================================================
# PRESETS REGEX (structure simple, dict plat)
# ============================================================
REGEX_PRESETS: Dict[str, str] = {
    # US — Emploi
    "NFP (US)": r"(?i)(nonfarm|non-farm|nfp|payrolls|employment)",
    "ADP (US)": r"(?i)\badp\b",
    "Unemployment rate (US)": r"(?i)\bunemployment\b|\bjobless\b",
    "Average Hourly Earnings (US)": r"(?i)average hourly earnings|ahe",
    
    # US — Inflation
    "CPI (US)": r"(?i)\bcpi\b|consumer price",
    "Core CPI (US)": r"(?i)core cpi|core consumer price",
    "PCE / Core PCE (US)": r"(?i)\bpce\b|core pce|personal consumption",
    
    # US — Activité
    "Retail Sales (US)": r"(?i)retail sales",
    "ISM Manufacturing (US)": r"(?i)\bism\b.*manufacturing|manufacturing pmi",
    "ISM Services (US)": r"(?i)\bism\b.*services|services pmi",
    "GDP (US)": r"(?i)\bgdp\b|gross domestic product",
    "Initial Jobless Claims (US)": r"(?i)initial (jobless|unemployment) claims",
    "Housing (US)": r"(?i)(housing starts|building permits|existing home sales|new home sales)",
    
    # US — Banque centrale
    "FOMC (Fed, US)": r"(?i)fomc|fed funds|rate decision|interest rate|dot plot|press conference|powell",
    
    # Eurozone
    "CPI (EA/EU)": r"(?i)(hicp|cpi).*(ea|euro|eurozone|euro area)",
    "ECB (EA/EU)": r"(?i)ecb|main refinancing|deposit facility|marginal lending",
    "PMI (EA/EU)": r"(?i)pmi|s&p global",
    "GDP (EA/EU)": r"(?i)\bgdp\b|gross domestic product",
    
    # Allemagne
    "ZEW (DE)": r"(?i)\bzew\b",
    "IFO (DE)": r"(?i)\bifo\b",
    "CPI (DE)": r"(?i)(hicp|cpi).*(germany|deutschland|\bde\b)",
    
    # France
    "CPI (FR)": r"(?i)(hicp|cpi).*(france|\bfr\b)",
    
    # UK
    "BoE / Rate Decision (UK)": r"(?i)bank of england|boe|rate decision|bank rate",
    
    # Génériques
    "Any Rate Decision": r"(?i)rate decision|monetary policy decision|policy rate",
    "Press conference (CB)": r"(?i)press conference|statement|minutes",
}

# ============================================================
# MAPPING FAMILLE -> PRESET PAR DÉFAUT
# ============================================================
_FAMILY_DEFAULT: Dict[str, str] = {
    "NFP": "NFP (US)",
    "CPI": "CPI (US)",
    "FOMC": "FOMC (Fed, US)",
}

# ============================================================
# MAPPING PRESET -> PAYS SUGGÉRÉS
# ============================================================
_PRESET_COUNTRIES: Dict[str, List[str]] = {
    "NFP (US)": ["US"],
    "ADP (US)": ["US"],
    "Unemployment rate (US)": ["US"],
    "Average Hourly Earnings (US)": ["US"],
    "CPI (US)": ["US"],
    "Core CPI (US)": ["US"],
    "PCE / Core PCE (US)": ["US"],
    "Retail Sales (US)": ["US"],
    "ISM Manufacturing (US)": ["US"],
    "ISM Services (US)": ["US"],
    "GDP (US)": ["US"],
    "Initial Jobless Claims (US)": ["US"],
    "Housing (US)": ["US"],
    "FOMC (Fed, US)": ["US"],
    "CPI (EA/EU)": ["EA", "EU"],
    "ECB (EA/EU)": ["EA", "EU"],
    "PMI (EA/EU)": ["EA", "EU"],
    "GDP (EA/EU)": ["EA", "EU"],
    "ZEW (DE)": ["DE"],
    "IFO (DE)": ["DE"],
    "CPI (DE)": ["DE"],
    "CPI (FR)": ["FR"],
    "BoE / Rate Decision (UK)": ["GB", "UK"],
    "Any Rate Decision": [],
    "Press conference (CB)": [],
}

# ============================================================
# FONCTIONS D'ACCÈS (API publique)
# ============================================================

def preset_names() -> List[str]:
    """Liste des noms de presets disponibles."""
    return list(REGEX_PRESETS.keys())

def pattern_for(name: str) -> str:
    """Retourne le pattern regex pour un preset donné."""
    return REGEX_PRESETS.get(name, r"(?i).")

def default_preset_for_family(family: Optional[str]) -> str:
    """Retourne le preset par défaut pour une famille donnée."""
    return _FAMILY_DEFAULT.get((family or "").upper(), "NFP (US)")

def get_countries(preset_name: str) -> List[str]:
    """Retourne les pays suggérés pour un preset."""
    return _PRESET_COUNTRIES.get(preset_name, [])

def get_regex(preset_name: str) -> str:
    """Alias de pattern_for() pour compatibilité."""
    return pattern_for(preset_name)

def coalesce_regex(preset_name: str, free_text: str) -> str:
    """Retourne free_text si non-vide, sinon le pattern du preset."""
    ft = (free_text or "").strip()
    return ft if ft else pattern_for(preset_name)

# ============================================================
# COMPOSANT STREAMLIT (optionnel)
# ============================================================

def regex_selectbox(
    label: str = "Filtre regex (preset)",
    default: Optional[str] = None,
    help: Optional[str] = None
) -> Tuple[str, str]:
    """
    Composant Streamlit pour sélectionner un preset.
    Retourne (pattern, preset_name)
    """
    import streamlit as st
    names = preset_names()
    idx = names.index(default) if default in names else 0
    name = st.selectbox(label, names, index=idx, help=help)
    pattern = REGEX_PRESETS[name]
    with st.expander("Voir le regex"):
        st.code(pattern, language="regex")
    return pattern, name

# ============================================================
# COMPATIBILITÉ LEGACY (pour anciennes pages)
# ============================================================

# Alias pour compatibilité avec les anciennes pages qui importent PRESETS
def preset_keys():
    """Alias de preset_names()."""
    return preset_names()

def get_variants(preset_name: str) -> List[str]:
    """Retourne une liste à un élément (compatibilité)."""
    return ["Standard"]

def get_variant_regex(preset_name: str, variant: str) -> str:
    """Retourne le regex du preset (ignore variant)."""
    return pattern_for(preset_name)

def get_family(preset_name: str) -> Optional[str]:
    """Devine la famille depuis le nom du preset."""
    name_upper = preset_name.upper()
    if "NFP" in name_upper or "ADP" in name_upper or "EMPLOYMENT" in name_upper:
        return "NFP"
    if "CPI" in name_upper or "INFLATION" in name_upper or "PCE" in name_upper:
        return "CPI"
    if "FOMC" in name_upper or "FED" in name_upper:
        return "FOMC"
    return None
