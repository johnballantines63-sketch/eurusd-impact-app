# fx_impact_app/streamlit_app/Home.py
from __future__ import annotations
import re
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Home — FX Impact App", layout="wide")
st.title("🏠 Home")

PAGES_DIR = Path(__file__).resolve().parent / "pages"

# Un seul endroit pour choisir l’ordre et limiter les pages affichées.
# Laisse vide (None) pour tout afficher; sinon liste exact des basenames attendus.
WHITELIST = None
# Exemple si tu veux restreindre:
# WHITELIST = [
#   "00-Live-Calendar-Forecast.py",
#   "07a-Simultaneous-Presets.py",
#   "07b-Simultaneous-Screener.py",
#   "08a-Forecaster-with-Presets.py",
#   "08-Forecaster-CLEAN.py",
#   "09a-Baskets-with-Presets.py",
#   "10a-Calendar-Sim-Baskets-Presets.py",
#   "11-Lexique.py",
#   "98-Glossary.py",
# ]

# Accepte anciens et nouveaux styles: "7b_Simultaneous_Screener.py" ou "07b-Simultaneous-Screener.py"
PAT = re.compile(r"""
    ^(?P<num>\d+)
    (?P<suf>[a-z])?
    [-_]
    (?P<slug>.+?)\.py$
""", re.IGNORECASE | re.VERBOSE)

def humanize(slug: str) -> str:
    # transforme "Simultaneous_Screener" / "Simultaneous-Screener" -> "Simultaneous Screener"
    title = re.sub(r"[-_]+", " ", slug).strip()
    # majuscule mot à mot mais garde les acronymes simples
    return " ".join(w if w.isupper() else w.capitalize() for w in title.split())

def parse_page(p: Path):
    m = PAT.match(p.name)
    if not m:
        return None
    num = int(m.group("num"))
    suf = m.group("suf") or ""
    slug = m.group("slug")
    label = f"{num}{suf} — {humanize(slug)}"
    order_key = (num, suf or "z")  # 07a < 07b < 08
    return dict(path=p, name=p.name, label=label, order=order_key)

pages = []
for p in sorted(PAGES_DIR.glob("*.py")):
    if p.name.startswith("_"):  # ignore _helpers éventuels
        continue
    if WHITELIST and p.name not in WHITELIST:
        continue
    rec = parse_page(p)
    if rec:
        pages.append(rec)

if not pages:
    st.warning("Aucune page trouvée dans ./pages. Vérifie les noms de fichiers.")
else:
    for rec in sorted(pages, key=lambda r: r["order"]):
        st.page_link(f"pages/{rec['name']}", label=rec["label"], icon="➡️")

with st.expander("Diagnostics"):
    st.write("Base:", str(PAGES_DIR))
    st.write([p["name"] for p in sorted(pages, key=lambda r: r["order"])])
