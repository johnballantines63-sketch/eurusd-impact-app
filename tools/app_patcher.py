#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Patcher — crée les fichiers partagés & pages utiles sans toucher à l'existant.
- fx_impact_app/src/regex_presets.py
- fx_impact_app/streamlit_app/pages/98_Glossary.py
- fx_impact_app/streamlit_app/pages/8a_Forecaster_with_Presets.py
"""
from __future__ import annotations
import sys, os
from pathlib import Path

ROOT = Path.cwd()
SRC_DIR = ROOT / "fx_impact_app" / "src"
PAGES_DIR = ROOT / "fx_impact_app" / "streamlit_app" / "pages"
PAGES_DIR.mkdir(parents=True, exist_ok=True)
SRC_DIR.mkdir(parents=True, exist_ok=True)

def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        # Idempotent: si même contenu, on ne fait rien
        try:
            if path.read_text(encoding="utf-8") == content:
                print(f"= inchangé: {path}")
                return
        except Exception:
            pass
        # Backup si différent
        bak = path.with_suffix(path.suffix + ".bak")
        try:
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"~ backup -> {bak.name}")
        except Exception as e:
            print(f"! warning: backup échoué pour {path}: {e}")
    path.write_text(content, encoding="utf-8")
    print(f"+ écrit: {path.relative_to(ROOT)}")

# ---------- regex_presets.py ----------
REGEX_PRESETS_PY = r'''from __future__ import annotations
from typing import Dict, List, Tuple, Optional

REGEX_PRESETS: Dict[str, str] = {
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

    "CPI (EA/EU)": r"(?i)(hicp|cpi).*(ea|euro|eurozone|euro area)",
    "ECB (EA/EU)": r"(?i)ecb|main refinancing|deposit facility|marginal lending|rate decision|press conference",
    "PMI (EA/EU)": r"(?i)pmi|s&p global",
    "GDP (EA/EU)": r"(?i)\bgdp\b|gross domestic product",
    "ZEW (DE)": r"(?i)\bzew\b",
    "IFO (DE)": r"(?i)\bifo\b",
    "CPI (DE)": r"(?i)(hicp|cpi).*(germany|deutschland|\\bde\\b)",
    "CPI (FR)": r"(?i)(hicp|cpi).*(france|\\bfr\\b)",
    "BoE / Rate Decision (UK)": r"(?i)bank of england|boe|rate decision|bank rate",

    "Any Rate Decision": r"(?i)rate decision|monetary policy decision|policy rate",
    "Press conference (CB)": r"(?i)press conference|statement|minutes",
    "Housing (US)": r"(?i)(housing starts|building permits|existing home sales|new home sales)",
}

_FAMILY_DEFAULT = {"NFP": "NFP (US)", "CPI": "CPI (US)", "FOMC": "FOMC (Fed, US)"}

def preset_names() -> List[str]: 
    return list(REGEX_PRESETS.keys())

def pattern_for(name: str) -> str: 
    return REGEX_PRESETS.get(name, r"(?i).")

def default_preset_for_family(family: Optional[str]) -> str:
    return _FAMILY_DEFAULT.get((family or "").upper(), "NFP (US)")

def regex_selectbox(label: str = "Filtre regex (preset)", default: Optional[str] = None, help: Optional[str] = None) -> Tuple[str, str]:
    import streamlit as st
    names = preset_names()
    idx = names.index(default) if default in names else 0
    name = st.selectbox(label, names, index=idx, help=help)
    pattern = REGEX_PRESETS[name]
    with st.expander("Voir le regex"):
        st.code(pattern)
    return pattern, name

def coalesce_regex(preset_name: str, free_text: str) -> str:
    ft = (free_text or "").strip()
    return ft if ft else pattern_for(preset_name)
'''

# ---------- 98_Glossary.py ----------
GLOSSARY_PAGE = r'''import streamlit as st
from textwrap import dedent

st.set_page_config(page_title="Glossary / Lexique", layout="wide")
st.title("📚 Glossary / Lexique")

GLOSSARY_MD = dedent(r"""
# Glossary / Lexique
## Événements & filtres
- **event_family** : famille macro ciblée (NFP, CPI, FOMC…)
- **country** : pays (US, EA/EU, GB, DE…)
- **include_regex** : filtre texte (regex) appliqué à *event_key/event_title*
- **strict_decision (FOMC)** : ne retient que la décision de taux

## Fenêtres & horizons
- **window_before_min** : minutes avant l’événement (prix d’entrée)
- **window_after_min** : minutes après l’événement (réaction)
- **horizon (min)** : durée de projection (ex. 15/30/60)

## Mesures de prix / performance
- **entry_px** : dernier close ≤ ts_utc
- **max_px** : plus haut close entre ts_utc et ts_utc + horizon
- **end_px** : close à la fin de l’horizon
- **Pip factor** : conversion en pips (EURUSD=10 000)
### MFE
- **mfe_med** : médiane de MFE (pips)
- **mfe_p80** : 80e percentile de MFE (pips)

## Statistiques de direction
- **p_up** : part des cas avec end_px > entry_px
- **n** : nb d’événements scorés à l’horizon

## Surprise & entrées
- **Actual**, **Consensus**
- **Surprise %** : `(Actual - Consensus)/|Consensus|*100`

## Diagnostics
- **hist_n** / **hist_n_unique_ts**
- **db_path** : chemin DuckDB
""").strip()

st.markdown(GLOSSARY_MD)
st.divider()
st.subheader("⬇️ Export")
st.download_button(
    "Télécharger le lexique (.md)",
    data=GLOSSARY_MD.encode("utf-8"),
    file_name="Glossary_Forex_Forecaster.md",
    mime="text/markdown"
)
with st.expander("Voir la source Markdown"):
    st.code(GLOSSARY_MD, language="markdown")
'''

# ---------- 8a_Forecaster_with_Presets.py ----------
FORECASTER_WITH_PRESETS = r'''from __future__ import annotations
from datetime import datetime, time
import pandas as pd, streamlit as st

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
'''

def main():
    files = [
        (SRC_DIR / "regex_presets.py", REGEX_PRESETS_PY),
        (PAGES_DIR / "98_Glossary.py", GLOSSARY_PAGE),
        (PAGES_DIR / "8a_Forecaster_with_Presets.py", FORECASTER_WITH_PRESETS),
    ]
    for path, content in files:
        write_file(path, content)

    print("\n✅ Terminé.")
    print("➡️ Ensuite, relance Streamlit proprement :")
    print("   streamlit cache clear")
    print('   export PYTHONPATH="$(pwd)"')
    print("   streamlit run fx_impact_app/streamlit_app/Home.py")

if __name__ == "__main__":
    sys.exit(main() or 0)
