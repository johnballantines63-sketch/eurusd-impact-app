
from __future__ import annotations
from typing import Optional

_FR = {
    "retail sales": "Ventes au détail",
    "cpi": "Indice des prix à la consommation",
    "producer price": "Indice des prix à la production",
    "unemployment rate": "Taux de chômage",
    "nonfarm": "Emplois NFP (hors agriculture)",
    "fomc": "Décision de la Fed (FOMC)",
    "ecb": "Décision de la BCE",
    "gdp": "PIB",
}

def _title_fr(event_title: str, event_key: Optional[str], country: Optional[str]) -> str:
    base = (event_key or event_title or "").lower()
    for k,v in _FR.items():
        if k in base: return v
    return event_title or (event_key or "")
