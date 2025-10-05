# fx_impact_app/src/family_detect.py
from __future__ import annotations
import re
from typing import Optional, Iterable
import pandas as pd

# Familles supportées
FAMILIES = ["NFP", "CPI", "FOMC"]

# Regex explicites par famille (sans capture, robustes à la casse)
PATTERNS = {
    "NFP": re.compile(
        r"(?i)\b(adp|non[- ]?farm|payroll|employment|unemployment rate|average hourly earnings)\b"
    ),
    "CPI": re.compile(
        r"(?i)\b(cpi|consumer price|inflation|core cpi|headline cpi)\b"
    ),
    "FOMC": re.compile(
        r"(?i)\b(fomc|federal reserve|fed funds|federal funds|target rate|rate decision|"
        r"policy statement|press conference|dot plot|economic projections|summary of economic projections|sep|minutes|powell)\b"
    ),
}

def _coerce_str(x) -> str:
    if x is None or x is pd.NA:
        return ""
    try:
        return str(x)
    except Exception:
        return ""

def detect_family_from_text(*parts: Iterable[str]) -> Optional[str]:
    text = " ".join(_coerce_str(p) for p in parts)
    for fam, rx in PATTERNS.items():
        if rx.search(text):
            return fam
    return None

def detect_family_row(row: pd.Series) -> Optional[str]:
    return detect_family_from_text(
        row.get("event_title"),
        row.get("event_key"),
        row.get("label"),
        row.get("type"),
    )
