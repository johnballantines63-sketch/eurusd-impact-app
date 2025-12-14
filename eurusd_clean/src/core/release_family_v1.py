"""
Mapping release_family V1
==========================

Fonction pour regrouper les composantes d'une même publication macro.

Règles:
- Mapping explicite (dict) prioritaire
- Fallback heuristique (keywords)
- Fallback final = event_key
"""

import re
from typing import Optional


# Mapping explicite prioritaire
RELEASE_FAMILY_MAP = {
    # US - CPI
    "cpi yoy": "cpi_release",
    "cpi mom": "cpi_release",
    "core cpi yoy": "cpi_release",
    "core cpi mom": "cpi_release",
    "consumer price index": "cpi_release",
    "core consumer price index": "cpi_release",
    
    # US - PCE
    "pce price index yoy": "pce_release",
    "pce price index mom": "pce_release",
    "core pce price index yoy": "pce_release",
    "core pce price index mom": "pce_release",
    "personal consumption expenditures": "pce_release",
    
    # US - NFP
    "non farm payrolls": "nfp_release",
    "nonfarm payrolls": "nfp_release",
    "non-farm payrolls": "nfp_release",
    "unemployment rate": "nfp_release",
    "average hourly earnings yoy": "nfp_release",
    "average hourly earnings mom": "nfp_release",
    "average weekly hours": "nfp_release",
    "labor force participation rate": "nfp_release",
    
    # US - FOMC
    "fomc rate decision": "fomc_release",
    "fomc statement": "fomc_release",
    "fomc minutes": "fomc_release",
    "fomc press conference": "fomc_release",
    "federal reserve interest rate decision": "fomc_release",
    "fed rate decision": "fomc_release",
    
    # US - ISM
    "ism manufacturing pmi": "ism_manufacturing_release",
    "ism services pmi": "ism_services_release",
    "ism manufacturing": "ism_manufacturing_release",
    "ism services": "ism_services_release",
    
    # US - PMI (S&P/Markit)
    "s&p global manufacturing pmi": "pmi_manufacturing_release",
    "s&p global services pmi": "pmi_services_release",
    "markit manufacturing pmi": "pmi_manufacturing_release",
    "markit services pmi": "pmi_services_release",
    
    # US - Retail Sales
    "retail sales mom": "retail_sales_release",
    "retail sales ex autos mom": "retail_sales_release",
    "retail sales ex autos and gas mom": "retail_sales_release",
    
    # EU - ECB
    "ecb interest rate decision": "ecb_release",
    "ecb rate decision": "ecb_release",
    "ecb press conference": "ecb_release",
    "ecb monetary policy statement": "ecb_release",
    
    # EU - CPI/HICP
    "eurozone cpi yoy": "eurozone_cpi_release",
    "eurozone cpi mom": "eurozone_cpi_release",
    "eurozone hicp yoy": "eurozone_cpi_release",
    "eurozone hicp mom": "eurozone_cpi_release",
    "eurozone core cpi yoy": "eurozone_cpi_release",
    
    # EU - PMI
    "eurozone manufacturing pmi": "eurozone_pmi_release",
    "eurozone services pmi": "eurozone_pmi_release",
    "eurozone composite pmi": "eurozone_pmi_release",
    
    # UK - CPI
    "uk cpi yoy": "uk_cpi_release",
    "uk cpi mom": "uk_cpi_release",
    "uk core cpi yoy": "uk_cpi_release",
    
    # UK - BoE
    "boe interest rate decision": "boe_release",
    "bank of england rate decision": "boe_release",
    "boe monetary policy summary": "boe_release",
    
    # CH - SNB (optionnel)
    "snb interest rate decision": "snb_release",
    "swiss national bank rate decision": "snb_release",
    
    # JP - BoJ (optionnel)
    "boj interest rate decision": "boj_release",
    "bank of japan rate decision": "boj_release",
}


def release_family_v1(event_key: str, event_title: Optional[str] = None) -> str:
    """
    Retourne une famille de release (string stable) pour regrouper les composantes d'une même publication.
    
    Args:
        event_key: Clé de l'événement (normalisée, lowercase)
        event_title: Titre de l'événement (optionnel, pour fallback)
    
    Returns:
        release_family: String stable identifiant la famille de release
    """
    # Normaliser event_key pour lookup
    key_normalized = event_key.lower().strip()
    
    # 1. Mapping explicite prioritaire
    if key_normalized in RELEASE_FAMILY_MAP:
        return RELEASE_FAMILY_MAP[key_normalized]
    
    # 2. Fallback heuristique (keywords)
    key_lower = key_normalized
    
    # CPI / HICP
    if re.search(r'\b(cpi|hicp|consumer price)\b', key_lower):
        return "cpi_release"
    
    # NFP
    if re.search(r'\b(non[- ]?farm|payroll|unemployment rate|average hourly earnings)\b', key_lower):
        return "nfp_release"
    
    # PMI (mais pas ISM)
    if re.search(r'\bpmi\b', key_lower) and not re.search(r'\bism\b', key_lower):
        if re.search(r'\b(manufacturing|manufacturing pmi)\b', key_lower):
            return "pmi_manufacturing_release"
        elif re.search(r'\b(services|services pmi)\b', key_lower):
            return "pmi_services_release"
        return "pmi_release"
    
    # ISM (distinct de PMI)
    if re.search(r'\bism\b', key_lower):
        if re.search(r'\b(manufacturing|manufacturing pmi)\b', key_lower):
            return "ism_manufacturing_release"
        elif re.search(r'\b(services|services pmi)\b', key_lower):
            return "ism_services_release"
        return "ism_release"
    
    # FOMC / Fed
    if re.search(r'\b(fomc|fed|federal reserve)\b', key_lower):
        if re.search(r'\b(decision|statement|minutes|press)\b', key_lower):
            return "fomc_release"
    
    # ECB
    if re.search(r'\becb\b', key_lower):
        if re.search(r'\b(decision|press|rate|monetary)\b', key_lower):
            return "ecb_release"
    
    # BoE
    if re.search(r'\b(boe|bank of england)\b', key_lower):
        if re.search(r'\b(decision|rate|monetary)\b', key_lower):
            return "boe_release"
    
    # PCE
    if re.search(r'\b(pce|personal consumption)\b', key_lower):
        return "pce_release"
    
    # Retail Sales
    if re.search(r'\bretail sales\b', key_lower):
        return "retail_sales_release"
    
    # 3. Fallback final = event_key
    return event_key
