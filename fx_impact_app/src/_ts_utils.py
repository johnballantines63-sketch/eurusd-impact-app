# fx_impact_app/src/_ts_utils.py
from __future__ import annotations
import pandas as pd
from zoneinfo import ZoneInfo
from datetime import datetime as _dt, date as _date, time as _time
from typing import Optional

def as_utc_naive(ts) -> pd.Timestamp:
    """
    Retourne un Timestamp UTC *naïf* (sans tzinfo).
    - si tz-naïf → supposé déjà en UTC
    - si tz-aware → convertit en UTC puis retire le TZ
    """
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        return t
    return t.tz_convert("UTC").tz_localize(None)

def to_utc_aware_series(s: pd.Series, assume_tz: Optional[str] = None) -> pd.Series:
    """
    Convertit une série de dates en UTC *aware*.
    - si les valeurs sont tz-naïves:
        * assume_tz → localise dans ce TZ puis convertit en UTC
        * sinon → considère déjà UTC
    """
    out = pd.to_datetime(s, errors="coerce")
    if out.isna().any():
        n = int(out.isna().sum())
        raise ValueError(f"{n} timestamp(s) invalides dans la série.")
    try:
        tzobj = out.dt.tz
    except Exception:
        tzobj = None
    if tzobj is None:
        if assume_tz:
            out = out.dt.tz_localize(ZoneInfo(assume_tz)).dt.tz_convert("UTC")
        else:
            out = out.dt.tz_localize("UTC")
    else:
        out = out.dt.tz_convert("UTC")
    return out

def to_utc_naive_series(s: pd.Series, assume_tz: Optional[str] = None) -> pd.Series:
    """Comme ci-dessus, mais renvoie des timestamps UTC *naïfs*."""
    return to_utc_aware_series(s, assume_tz=assume_tz).dt.tz_convert("UTC").dt.tz_localize(None)

def local_date_time_to_utc_naive(d: _date | pd.Timestamp, t: _time, tz: str) -> pd.Timestamp:
    """
    Combine (date, time) locaux → UTC naïf.
    Évite `Timestamp.combine(..., tzinfo=...)` (qui n’existe pas).
    """
    if isinstance(d, pd.Timestamp):
        d = d.date()
    raw = _dt.combine(d, t)  # naïf en local
    aware = pd.Timestamp(raw).tz_localize(ZoneInfo(tz)).tz_convert("UTC")
    return pd.Timestamp(aware.tz_localize(None))
