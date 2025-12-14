#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Double Wave Detector — rev10 (math-based, robust, single file)
==============================================================
- Pure price-structure logic, no fixed windows.
- Baseline configurable (default: 14:29 close, Europe/Zurich).
- Wave2 uses Break-then-Trough rule (must break Peak1 first).
- Adaptive thresholds by volatility regime (ATR vs daily median).
- Works on a pandas DataFrame (1m OHLC), plus optional DuckDB loader.
- CLI supports single date or batch (CSV export).

Dependencies: pandas, numpy
Optional (for DuckDB loading): duckdb

Usage (DuckDB, single day):
  python double_wave_detector_rev10.py --db-path /path/to/warehouse.duckdb --table prices_bern --date 2025-09-11

Usage (batch + CSV):
  python double_wave_detector_rev10.py --db-path ... --table prices_bern --start 2025-01-01 --end 2025-12-31 --csv-out double_wave_results.csv
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, List

import numpy as np
import pandas as pd

# ------------- Defaults (overridable via CLI) -------------
DEFAULT_TZ = "Europe/Zurich"
DEFAULT_BASELINE_MODE = "prev_close_14_29"  # "prev_close_14_29" | "low_14_30" | "high_14_30" | "close_14_30"
BASELINE_BACK_TOL_MIN = 5                   # if target bar missing, look back up to N minutes
BREAK_EPS_PIPS = 1.0                        # min pip break above Peak1 to confirm Wave2
LOCAL_WIDTH = 2                             # neighbors to confirm local peak/trough
MAX_IDLE_BARS = 20                          # stop if no new extreme for N bars
SCAN_MINUTES_AFTER_HINT = 90                # horizon after 14:30 to search the pattern

# Adaptive threshold anchors
MIN_W1_PULLBACK = 0.25  # base min for W1 retracement
MIN_W2_PULLBACK = 0.15  # base min for W2 retracement
ATRK_MIN = 0.40         # min ATR_K
ATRK_MAX = 0.60         # max ATR_K
ATR_LEN = 14            # ATR period in 1m
# ----------------------------------------------------------

@dataclass
class WaveDetection:
    date: str
    symbol: str
    direction: str
    baseline_time: str
    baseline_price: float
    peak1_time: str
    peak1_price: float
    pullback1_time: str
    pullback1_price: float
    peak2_time: str
    peak2_price: float
    pullback2_time: str
    pullback2_price: float
    wave1_amp_pips: float
    wave2_amp_pips: float
    pullback1_ratio: float
    pullback2_ratio: float
    double_wave: bool
    confidence: float

# ---------------- Core math utilities ----------------

def atr1m(df: pd.DataFrame, n: int = ATR_LEN) -> pd.Series:
    """Average True Range on 1m OHLC (classic TR rolling mean)."""
    hl = df['high'] - df['low']
    hc = (df['high'] - df['close'].shift()).abs()
    lc = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()

def to_pips(x: float) -> float:
    return 1e4 * x

def is_local_trough(series: pd.Series, i: int, width: int) -> bool:
    L, R = max(0, i - width), min(len(series)-1, i + width)
    return series.iloc[i] == series.iloc[L:R+1].min()

def is_local_peak(series: pd.Series, i: int, width: int) -> bool:
    L, R = max(0, i - width), min(len(series)-1, i + width)
    return series.iloc[i] == series.iloc[L:R+1].max()

def choose_direction(df: pd.DataFrame) -> str:
    """Impulse probe on first ~6 bars after 14:30."""
    probe = df.iloc[:6].copy()
    up_probe = probe['high'].max() - df['low'].iloc[0]
    dn_probe = df['high'].iloc[0] - probe['low'].min()
    return "bullish" if up_probe >= dn_probe else "bearish"

def dynamic_thresholds(day_atr_median: float, atr_now: float) -> Tuple[float,float,float]:
    """
    Returns (w1_min_dd, w2_min_dd, atr_k) where dd are retracement ratios.
    Scales with volatility regime.
    """
    ratio = (atr_now / max(1e-12, day_atr_median)) if day_atr_median > 0 else 1.0
    w1 = MIN_W1_PULLBACK + 0.05 * ratio
    w2 = MIN_W2_PULLBACK + 0.05 * ratio
    atr_k = np.clip(0.5 * (day_atr_median / max(1e-12, atr_now)) if atr_now>0 else 0.5, ATRK_MIN, ATRK_MAX)
    return float(w1), float(w2), float(atr_k)

def pick_baseline(df: pd.DataFrame, hint_ts: pd.Timestamp, mode: str = DEFAULT_BASELINE_MODE, back_tol_min: int = BASELINE_BACK_TOL_MIN) -> Tuple[Optional[float], Optional[pd.Timestamp]]:
    if df.empty: return None, None
    if mode == "prev_close_14_29":
        prior = df.loc[:hint_ts - pd.Timedelta(seconds=1)]
        if prior.empty: return None, None
        target = hint_ts - pd.Timedelta(minutes=1)
        win_start = hint_ts - pd.Timedelta(minutes=back_tol_min+1)
        candidates = prior.loc[win_start:target]
        if candidates.empty:
            row = prior.iloc[-1]; return float(row['close']), prior.index[-1]
        if target in candidates.index:
            t = target
        else:
            t = candidates.index[-1]
        return float(df.loc[t,'close']), t
    elif mode == "low_14_30":
        if hint_ts in df.index:
            return float(df.loc[hint_ts,'low']), hint_ts
    elif mode == "high_14_30":
        if hint_ts in df.index:
            return float(df.loc[hint_ts,'high']), hint_ts
    elif mode == "close_14_30":
        if hint_ts in df.index:
            return float(df.loc[hint_ts,'close']), hint_ts
    return None, None

# --------------- Universal detection (DataFrame) ----------------

def detect_double_wave_on_df(df: pd.DataFrame,
                             date_label: str,
                             symbol: str = "EURUSD",
                             tz: str = DEFAULT_TZ,
                             baseline_mode: str = DEFAULT_BASELINE_MODE,
                             minutes_after_hint: int = SCAN_MINUTES_AFTER_HINT,
                             max_idle_bars: int = MAX_IDLE_BARS,
                             local_width: int = LOCAL_WIDTH) -> Optional[Dict]:
    """
    Input: df is 1m OHLC (index tz-aware), columns: open, high, low, close.
    Output: dict (WaveDetection) or None.
    """
    if df.empty:
        return None

    df = df.sort_index().copy()
    assert {'open','high','low','close'}.issubset(df.columns), "DataFrame must contain OHLC columns"
    assert df.index.tz is not None, "Index must be timezone-aware"

    # ATR & regime stats
    df['ATR'] = atr1m(df)
    day_atr_median = float(df['ATR'].median()) if not df['ATR'].empty else 0.0

    # Hint (14:30) in provided index timezone
    hint_ts = df.index[0].replace(hour=14, minute=30, second=0, microsecond=0)
    baseline_price, baseline_time = pick_baseline(df, hint_ts, mode=baseline_mode)
    if baseline_time is None:
        return None

    # Slice after 14:30 up to horizon
    end_ts = hint_ts + pd.Timedelta(minutes=minutes_after_hint)
    df_after = df.loc[hint_ts:end_ts].copy()
    if df_after.empty:
        return None

    direction = choose_direction(df_after)
    highs, lows = df_after['high'], df_after['low']

    # Adaptive thresholds based on first-bar ATR
    atr0 = float(df_after['ATR'].iloc[0]) if not df_after['ATR'].empty else day_atr_median
    w1_min_dd, w2_min_dd, atr_k = dynamic_thresholds(day_atr_median, atr0)

    # ---- Wave 1 ----
    peak1_price = baseline_price
    peak1_time  = baseline_time
    pullback1_price = None
    pullback1_time  = None

    idle = 0
    for i in range(len(df_after)):
        ts = df_after.index[i]
        atr_i = float(df_after['ATR'].iloc[i])
        if direction == "bullish":
            if highs.iloc[i] > peak1_price:
                peak1_price = highs.iloc[i]; peak1_time = ts; idle = 0
            else:
                idle += 1
            amp = max(1e-9, peak1_price - baseline_price)
            dd = (peak1_price - lows.iloc[i]) / amp if amp>0 else 0.0
            dd_filter = (peak1_price - lows.iloc[i]) >= atr_k * atr_i
            if amp>0 and dd >= w1_min_dd and dd_filter and is_local_trough(lows, i, local_width):
                pullback1_price = lows.iloc[i]; pullback1_time = ts; break
        else:  # bearish
            if lows.iloc[i] < peak1_price:
                peak1_price = lows.iloc[i]; peak1_time = ts; idle = 0
            else:
                idle += 1
            amp = max(1e-9, baseline_price - peak1_price)
            dd = (highs.iloc[i] - peak1_price) / amp if amp>0 else 0.0
            dd_filter = (highs.iloc[i] - peak1_price) >= atr_k * atr_i
            if amp>0 and dd >= w1_min_dd and dd_filter and is_local_peak(highs, i, local_width):
                pullback1_price = highs.iloc[i]; pullback1_time = ts; break
        if idle >= max_idle_bars:
            return None

    if pullback1_time is None:
        return None

    # ---- Wave 2 (Break-then-Trough) ----
    peak2_price = peak1_price
    peak2_time  = peak1_time
    pullback2_price = None
    pullback2_time = None

    start_i = df_after.index.get_loc(pullback1_time) + 1
    has_broken_peak1 = False
    idle = 0

    for i in range(start_i, len(df_after)):
        ts = df_after.index[i]
        atr_i = float(df_after['ATR'].iloc[i])

        if direction == "bullish":
            if highs.iloc[i] > peak2_price:
                peak2_price = highs.iloc[i]; peak2_time = ts; idle = 0
                if to_pips(peak2_price - peak1_price) >= BREAK_EPS_PIPS:
                    has_broken_peak1 = True
            else:
                idle += 1
            if not has_broken_peak1:
                continue
            amp2 = max(1e-9, peak2_price - baseline_price)
            dd2 = (peak2_price - lows.iloc[i]) / amp2 if amp2>0 else 0.0
            dd2_filter = (peak2_price - lows.iloc[i]) >= atr_k * atr_i
            if amp2>0 and dd2 >= w2_min_dd and dd2_filter and is_local_trough(lows, i, local_width):
                pullback2_price = lows.iloc[i]; pullback2_time = ts; break

        else:
            if lows.iloc[i] < peak2_price:
                peak2_price = lows.iloc[i]; peak2_time = ts; idle = 0
                if to_pips(peak1_price - peak2_price) >= BREAK_EPS_PIPS:
                    has_broken_peak1 = True
            else:
                idle += 1
            if not has_broken_peak1:
                continue
            amp2 = max(1e-9, baseline_price - peak2_price)
            dd2 = (highs.iloc[i] - peak2_price) / amp2 if amp2>0 else 0.0
            dd2_filter = (highs.iloc[i] - peak2_price) >= atr_k * atr_i
            if amp2>0 and dd2 >= w2_min_dd and dd2_filter and is_local_peak(highs, i, local_width):
                pullback2_price = highs.iloc[i]; pullback2_time = ts; break

        if idle >= max_idle_bars:
            break

    if pullback2_time is None:
        return None

    double_ok = (peak2_price > peak1_price) if direction=="bullish" else (peak2_price < peak1_price)

    w1_pips = round(to_pips(abs(peak1_price - baseline_price)), 1)
    w2_pips = round(to_pips(abs(peak2_price - baseline_price)), 1)
    r1 = round(abs(peak1_price - pullback1_price) / max(1e-9, abs(peak1_price - baseline_price)), 3)
    r2 = round(abs(peak2_price - pullback2_price) / max(1e-9, abs(peak2_price - baseline_price)), 3)

    # Confidence score (simple, transparent)
    conf = 50.0
    if double_ok: conf += 20
    # timing plausibility
    dt1 = (pd.Timestamp(peak1_time) - pd.Timestamp(baseline_time)).total_seconds()/60.0
    dt2 = (pd.Timestamp(peak2_time) - pd.Timestamp(pullback1_time)).total_seconds()/60.0
    if 5 <= dt1 <= 20: conf += 5
    if 5 <= dt2 <= 30: conf += 10
    # extension factor
    if w1_pips > 0 and 1.0 <= (w2_pips / w1_pips) <= 2.5: conf += 10
    conf = float(max(0.0, min(100.0, conf)))

    res = WaveDetection(
        date=date_label, symbol=symbol, direction=direction,
        baseline_time=str(baseline_time), baseline_price=float(baseline_price),
        peak1_time=str(peak1_time), peak1_price=float(peak1_price),
        pullback1_time=str(pullback1_time), pullback1_price=float(pullback1_price),
        peak2_time=str(peak2_time), peak2_price=float(peak2_price),
        pullback2_time=str(pullback2_time), pullback2_price=float(pullback2_price),
        wave1_amp_pips=w1_pips, wave2_amp_pips=w2_pips,
        pullback1_ratio=r1, pullback2_ratio=r2,
        double_wave=bool(double_ok), confidence=conf
    )
    return asdict(res)

# --------------- Optional: DuckDB loading helpers ---------------

def load_ohlc_1m_duckdb(db_path: str, table: str, tz: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """Load OHLC 1m from DuckDB (datetime stored UTC), return tz-aware index in `tz`."""
    try:
        import duckdb  # optional dependency
    except Exception as e:
        raise RuntimeError("duckdb not installed. `pip install duckdb` or pass a DataFrame directly.") from e

    conn = duckdb.connect(db_path, read_only=True)
    q = f"SELECT datetime, open, high, low, close FROM {table} WHERE datetime BETWEEN ? AND ? ORDER BY datetime"
    df = conn.execute(q, [start_dt, end_dt]).df()
    conn.close()
    if df.empty: return df
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert(tz)
    return df.set_index('datetime').sort_index()

def detect_for_date_duckdb(db_path: str, table: str, date: datetime,
                           tz: str = DEFAULT_TZ,
                           baseline_mode: str = DEFAULT_BASELINE_MODE,
                           minutes_after_hint: int = SCAN_MINUTES_AFTER_HINT,
                           trading_window: bool = True) -> Optional[Dict]:
    ts = pd.Timestamp(date, tz=tz)
    if trading_window:
        start_dt = ts.replace(hour=13, minute=0, second=0, microsecond=0)
        end_dt   = ts.replace(hour=16, minute=30, second=0, microsecond=0)
    else:
        start_dt = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt   = ts.replace(hour=23, minute=59, second=59, microsecond=0)

    df = load_ohlc_1m_duckdb(db_path, table, tz, start_dt, end_dt)
    if df.empty: return None
    return detect_double_wave_on_df(
        df, date_label=ts.strftime("%Y-%m-%d"), symbol="EURUSD", tz=tz,
        baseline_mode=baseline_mode, minutes_after_hint=minutes_after_hint
    )

# ----------------------------- CLI -----------------------------

def main():
    ap = argparse.ArgumentParser(description="Double Wave Detector — rev10 (math-based)")
    ap.add_argument("--db-path", type=str, help="DuckDB path (optional if you pass DF in your own app)")
    ap.add_argument("--table", type=str, default="prices_bern", help="DuckDB table/view name")
    ap.add_argument("--date", type=str, help="YYYY-MM-DD (single day)")
    ap.add_argument("--start", type=str, help="YYYY-MM-DD (batch start)")
    ap.add_argument("--end", type=str, help="YYYY-MM-DD (batch end)")
    ap.add_argument("--tz", type=str, default=DEFAULT_TZ, help="Timezone for indexing (default Europe/Zurich)")
    ap.add_argument("--baseline-mode", type=str, default=DEFAULT_BASELINE_MODE,
                    choices=["prev_close_14_29","low_14_30","high_14_30","close_14_30"],
                    help="How to anchor the baseline")
    ap.add_argument("--minutes-after-hint", type=int, default=SCAN_MINUTES_AFTER_HINT,
                    help="Horizon after 14:30 (minutes) to scan for the full pattern (default 90)")
    ap.add_argument("--full-day", action="store_true", help="Scan full day instead of 13:00–16:30")
    ap.add_argument("--csv-out", type=str, help="Path to CSV output for batch mode")

    args = ap.parse_args()

    if not args.db_path:
        print("No --db-path provided. This CLI expects DuckDB. For in-app use, import detect_double_wave_on_df.")
        return

    if args.date:
        res = detect_for_date_duckdb(
            db_path=args.db_path, table=args.table, date=datetime.fromisoformat(args.date),
            tz=args.tz, baseline_mode=args.baseline_mode,
            minutes_after_hint=args.minutes_after_hint,
            trading_window=not args.full_day
        )
        if res is None:
            print("No pattern detected or no data.")
        else:
            import json
            print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    if not (args.start and args.end):
        print("Specify --date OR --start and --end for batch.")
        return

    # Batch
    start = pd.Timestamp(args.start)
    end   = pd.Timestamp(args.end)
    rows: List[Dict] = []
    d = start
    while d <= end:
        res = detect_for_date_duckdb(
            db_path=args.db_path, table=args.table, date=d.to_pydatetime(),
            tz=args.tz, baseline_mode=args.baseline_mode,
            minutes_after_hint=args.minutes_after_hint,
            trading_window=not args.full_day
        )
        if res:
            rows.append(res)
        d += pd.Timedelta(days=1)

    if not rows:
        print("No detections in range.")
        return

    df_out = pd.DataFrame(rows)
    if args.csv_out:
        df_out.to_csv(args.csv_out, index=False)
        print(f"Saved CSV → {args.csv_out}")
    else:
        # Print as JSON list
        import json
        print(json.dumps(rows, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
