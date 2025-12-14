#!/usr/bin/env python3
"""
impact_unified.py
=================

Fonction(s) de calcul de l'impact selon la spécification IMPACT_SPEC_V1.

⚠️ DÉFINITION CANONIQUE
-----------------------
Cette implémentation définit LA métrique "officielle" d'impact macro du projet.

- Baseline : event_open (open première bougie M1 avec datetime >= event_timestamp)
- Horizon  : 120 minutes après l'événement (par défaut)
- Direction: +1 = UP (pic sur les highs), -1 = DOWN (pic sur les lows)

Références:
- docs/IMPACT_SPEC_V1.md
- docs/RAPPORT_AUDIT_IMPACT_V2_FINAL.md

Objectif :
    - Avoir UNE implémentation canonique de l'impact en pips,
      basée sur une baseline explicite et un horizon configurable.
    - Pouvoir l'utiliser aussi bien dans:
        * measure_impact_from_finnhub
        * le Planificateur
        * les scripts de catalogage de clusters
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Literal, Dict, Any

import pandas as pd
import pytz


BaselineMethod = Literal["event_open", "event_close", "custom_price"]


@dataclass
class ImpactResult:
    impact_pips: float
    direction: int                 # +1 = UP, -1 = DOWN
    baseline_price: float
    baseline_time: datetime
    peak_price: float
    peak_time: datetime
    time_to_peak_minutes: float
    impact_signed_pips: float
    meta: Dict[str, Any]


def _ensure_tz_aware(ts: datetime, timezone_str: str) -> datetime:
    tz = pytz.timezone(timezone_str)
    if ts.tzinfo is None:
        return tz.localize(ts)
    return ts.astimezone(tz)


def calculate_impact_unified(
    df_prices: pd.DataFrame,
    event_timestamp: datetime,
    *,
    baseline_method: BaselineMethod = "event_open",
    horizon_minutes: int = 120,
    lookback_minutes: int = 5,
    min_pips: Optional[float] = None,
    custom_baseline_price: Optional[float] = None,
    timezone_str: str = "Europe/Zurich",
    debug: bool = False,
) -> Optional[ImpactResult]:
    """
    Calcule l'impact de prix (en pips) autour d'un événement selon IMPACT_SPEC_V1.

    Hypothèses sur df_prices:
        - contient au minimum les colonnes: 'datetime', 'open', 'high', 'low'
        - 'datetime' est convertible en pandas.Timestamp

    Args:
        df_prices: DataFrame de prix M1 EURUSD.
        event_timestamp: timestamp de l'événement (naïf ou tz-aware).
        baseline_method:
            - 'event_open'  : open première bougie avec datetime >= event_timestamp
            - 'event_close' : close dernière bougie avec datetime < event_timestamp
            - 'custom_price': prix explicite via custom_baseline_price
        horizon_minutes: nombre de minutes après l'événement pour chercher le pic.
        lookback_minutes: lookback pour éventuelle analyse, actuellement utilisé pour meta seulement.
        min_pips: si non None, seuil minimal pour considérer l'impact comme significatif.
        custom_baseline_price: utilisé si baseline_method == 'custom_price'.
        timezone_str: timezone de travail.
        debug: si True, renvoie plus d'infos dans meta et ne supprime pas silencieusement.

    Returns:
        ImpactResult ou None si:
            - pas de données de prix suffisantes
            - impact < min_pips (si min_pips est défini)
    """
    if df_prices.empty:
        if debug:
            print("calculate_impact_unified: df_prices vide")
        return None

    # Normalisation datetime + timezone
    df = df_prices.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["datetime"] = df["datetime"].dt.tz_localize(timezone_str) \
        if df["datetime"].dt.tz is None else df["datetime"].dt.tz_convert(timezone_str)

    event_ts = _ensure_tz_aware(event_timestamp, timezone_str)

    # Fenêtre temporelle
    window_start = event_ts - timedelta(minutes=lookback_minutes)
    window_end = event_ts + timedelta(minutes=horizon_minutes)

    df_window = df[(df["datetime"] >= window_start) & (df["datetime"] <= window_end)].copy()
    if df_window.empty:
        if debug:
            print("calculate_impact_unified: df_window vide")
        return None

    # -------------------------
    # 1) Détermination baseline
    # -------------------------
    if baseline_method == "event_open":
        df_at_event = df_window[df_window["datetime"] >= event_ts]
        if not df_at_event.empty:
            first_candle = df_at_event.iloc[0]
            baseline_price = float(first_candle["open"])
            baseline_time = first_candle["datetime"].to_pydatetime()
        else:
            # Fallback: dernière bougie avant l'événement dans la fenêtre
            df_before_event = df_window[df_window["datetime"] < event_ts]
            if df_before_event.empty:
                if debug:
                    print("calculate_impact_unified: aucune bougie >= event_ts ni < event_ts")
                return None
            last_before = df_before_event.iloc[-1]
            baseline_price = float(last_before["close"])
            baseline_time = last_before["datetime"].to_pydatetime()

    elif baseline_method == "event_close":
        df_before_event = df_window[df_window["datetime"] < event_ts]
        if df_before_event.empty:
            if debug:
                print("calculate_impact_unified: pas de bougie avant event_ts pour event_close")
            return None
        last_before = df_before_event.iloc[-1]
        baseline_price = float(last_before["close"])
        baseline_time = last_before["datetime"].to_pydatetime()

    elif baseline_method == "custom_price":
        if custom_baseline_price is None:
            raise ValueError("custom_baseline_price doit être fourni si baseline_method='custom_price'")
        baseline_price = float(custom_baseline_price)
        baseline_time = event_ts

    else:
        raise ValueError(f"baseline_method inconnu: {baseline_method}")

    # -------------------------
    # 2) Calcul pips UP / DOWN
    # -------------------------
    df_after = df_window[df_window["datetime"] >= event_ts].copy()
    if df_after.empty:
        if debug:
            print("calculate_impact_unified: aucune bougie après event_ts")
        return None

    df_after["pips_high"] = (df_after["high"] - baseline_price) * 10000.0
    df_after["pips_low"] = (baseline_price - df_after["low"]) * 10000.0

    peak_high = float(df_after["pips_high"].max())
    peak_low = float(df_after["pips_low"].max())

    # Direction & impact
    if peak_high > peak_low:
        impact_pips = peak_high
        direction = 1
        peak_row = df_after.loc[df_after["pips_high"].idxmax()]
        peak_price = float(peak_row["high"])
    else:
        impact_pips = peak_low
        direction = -1
        peak_row = df_after.loc[df_after["pips_low"].idxmax()]
        peak_price = float(peak_row["low"])

    peak_time = peak_row["datetime"].to_pydatetime()
    time_to_peak_minutes = (peak_time - event_ts).total_seconds() / 60.0
    impact_signed_pips = direction * impact_pips

    # Seuil minimal
    if min_pips is not None and impact_pips < min_pips:
        if debug:
            print(f"calculate_impact_unified: impact {impact_pips:.1f} < min_pips {min_pips}")
        return None

    meta: Dict[str, Any] = {
        "baseline_method": baseline_method,
        "event_timestamp": event_ts,
        "window_start": window_start,
        "window_end": window_end,
        "peak_high_pips": peak_high,
        "peak_low_pips": peak_low,
        "n_candles_window": int(len(df_window)),
        "n_candles_after": int(len(df_after)),
    }

    return ImpactResult(
        impact_pips=float(impact_pips),
        direction=direction,
        baseline_price=baseline_price,
        baseline_time=baseline_time,
        peak_price=peak_price,
        peak_time=peak_time,
        time_to_peak_minutes=float(time_to_peak_minutes),
        impact_signed_pips=float(impact_signed_pips),
        meta=meta,
    )
