# fx_impact_app/streamlit_app/_ui.py
from __future__ import annotations
import streamlit as st

def apply_sidebar_index(prefix: str | int) -> None:
    """
    Ajoute un petit préfixe visuel devant les libellés du menu de gauche.
    (Purement cosmétique : n’affecte pas l’ordre réel des pages.)
    Usage: apply_sidebar_index("10") ou apply_sidebar_index(10)
    """
    try:
        p = str(prefix).strip()
    except Exception:
        p = ""
    if not p:
        return

    css = f"""
    <style>
      /* Ajoute le préfixe en gris avant le texte des entrées du sidebar nav */
      [data-testid="stSidebarNav"] li a span:first-child::before {{
        content: "{p} ";
        opacity: 0.6;
        margin-right: 2px;
        font-feature-settings: "tnum";
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
