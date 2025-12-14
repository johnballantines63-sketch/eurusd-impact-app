# scripts/contracts/validate_payload.py
from __future__ import annotations
from typing import Any, Dict
from scripts.contracts.v3_2_1_contract import DayPrediction


def validate_day_payload(payload: Dict[str, Any]) -> DayPrediction:
    """
    Valide strictement le payload.
    -> retourne l'objet DayPrediction si OK, lève ValidationError sinon.
    """
    return DayPrediction.model_validate(payload)

