# scripts/contracts/v3_2_1_contract.py
from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any
from datetime import date, datetime
import hashlib
import json

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

CONTRACT_NAME = "V3.2.1_TRADING_PAYLOAD"
CONTRACT_VERSION = "1.0.0"

# ✅ ordre FIXE des features du modèle (doit matcher l'artefact JSON et l'applier)
FEATURE_ORDER_V3_2_1: List[str] = [
    "log1p_score_v2_1",
    "dow", "is_mon", "is_fri", "day_of_month", "month", "is_month_start", "is_month_end", "week_of_month",
    "vol_mean_20_lag1", "vol_std_20_lag1", "vol_mean_60_lag1", "vol_std_60_lag1",
    "vol_z_20_lag1", "vol_z_60_lag1", "regime_high_60_lag1", "regime_low_60_lag1",
    "log1p_n_us_events_day",
]


def feature_order_hash(features: List[str]) -> str:
    s = "\n".join(features).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


FEATURE_ORDER_HASH = feature_order_hash(FEATURE_ORDER_V3_2_1)


class ActualRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    ts_local: datetime
    name: str
    country: str = Field(..., min_length=2, max_length=2)
    is_core: bool = True

    previous: Optional[float] = None
    forecast: Optional[float] = None
    actual: Optional[float] = None

    unit: Optional[str] = None

    @model_validator(mode="after")
    def core_requires_inputs(self):
        # Invariant: si event core => au moins previous et forecast doivent exister (actual peut être rempli plus tard)
        if self.is_core:
            if self.previous is None or self.forecast is None:
                raise ValueError(f"Core event {self.event_id} requires previous + forecast.")
        return self


class PatternPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idx: int = Field(..., ge=1, le=10)
    kind: Literal["peak", "pullback", "entry_zone", "exit_zone"]
    t_min_minutes: int = Field(..., ge=-1440, le=2880)  # minutes relatives (ex: -60 avant 1er event)
    t_max_minutes: int = Field(..., ge=-1440, le=2880)
    expected_pips: float = Field(..., ge=-2000, le=2000)

    @model_validator(mode="after")
    def check_window(self):
        if self.t_max_minutes < self.t_min_minutes:
            raise ValueError("Invalid time window: t_max < t_min.")
        return self


class ExitPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["time_window", "pips_target", "hybrid"]
    # time-based
    exit_t_min_minutes: Optional[int] = None
    exit_t_max_minutes: Optional[int] = None
    # price-based
    take_profit_pips: Optional[float] = Field(default=None, ge=0, le=2000)
    stop_loss_pips: Optional[float] = Field(default=None, ge=0, le=2000)

    @model_validator(mode="after")
    def validate_exit_plan(self):
        if self.method in ("time_window", "hybrid"):
            if self.exit_t_min_minutes is None or self.exit_t_max_minutes is None:
                raise ValueError("time_window/hybrid requires exit_t_min_minutes + exit_t_max_minutes.")
            if self.exit_t_max_minutes < self.exit_t_min_minutes:
                raise ValueError("Exit window invalid (max < min).")
        if self.method in ("pips_target", "hybrid"):
            if self.take_profit_pips is None or self.stop_loss_pips is None:
                raise ValueError("pips_target/hybrid requires take_profit_pips + stop_loss_pips.")
        return self


class DayPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    timezone: str = "Europe/Madrid"

    # Résumé trading
    direction: Literal["BUY", "SELL", "NO_TRADE"]
    risk_score: float = Field(..., ge=0.0, le=1.0)

    pattern: Literal["single_wave", "double_wave", "zigzag", "unknown"]
    impact_pred_pips: float = Field(..., ge=0, le=2000)

    # Détails pattern (pics/pullbacks/entry/exit zones)
    points: List[PatternPoint] = Field(default_factory=list)
    exit_plan: ExitPlan

    # Signals "core"
    core_cluster_id: str
    core_events: List[ActualRow] = Field(default_factory=list)

    # optionnel: events non essentiels
    optional_events: List[ActualRow] = Field(default_factory=list)

    # Debug / audit
    model_version: str
    contract_name: str = CONTRACT_NAME
    contract_version: str = CONTRACT_VERSION
    feature_order_hash: str = FEATURE_ORDER_HASH

    # valeurs du modèle pour audit
    pred_vol_pips: float = Field(..., ge=0, le=2000)
    pred_log_vol: float = Field(..., ge=-10, le=20)

    @field_validator("core_events")
    @classmethod
    def must_have_core_events(cls, v):
        # Invariant: pour BUY/SELL => au moins 1 core event (sinon impossible de renseigner actuals)
        return v

    @model_validator(mode="after")
    def invariants(self):
        if self.direction in ("BUY", "SELL") and len(self.core_events) == 0:
            raise ValueError("BUY/SELL requires at least 1 core event.")
        if self.impact_pred_pips <= 0 and self.direction in ("BUY", "SELL"):
            raise ValueError("BUY/SELL requires impact_pred_pips > 0.")
        if self.pred_vol_pips <= 0:
            raise ValueError("pred_vol_pips must be > 0.")
        if self.feature_order_hash != FEATURE_ORDER_HASH:
            raise ValueError("feature_order_hash mismatch (contract drift).")
        return self


def payload_hash(payload: Dict[str, Any]) -> str:
    # hash stable (sorted keys)
    b = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

