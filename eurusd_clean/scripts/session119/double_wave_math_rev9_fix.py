#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Double Wave Detector (rev 9 FIX — math-based, baseline at 14:30)
================================================================
- Baseline = 14:30 candle: low (bullish) / high (bearish) for true delta
- No fixed windows: waves end on significant pullbacks (percent + ATR filter)
- Robust to overlaps (e.g., 14:30 US → 14:45 ECB press conf)
"""

from pathlib import Path
import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional

import duckdb
import numpy as np
import pandas as pd
import pytz
import matplotlib.pyplot as plt

# ------------------ CONFIG ------------------
DB_PATH = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
PRICES_TABLE = "prices_bern"     # expects 1m bars in Europe/Zurich tz

# Detection hyper-parameters
THR_WAVE1_DD = 0.30          # 30% retracement ends Wave1
THR_WAVE2_DD = 0.20          # 20% retracement ends Wave2 (as requested)
ATR_K = 0.50                 # require pullback >= ATR_K * ATR1m
ATR_LEN = 14                 # ATR period in minutes
LOCAL_WIDTH = 2              # neighbor window to confirm trough/peak
DIRECTION_MODE = "auto"      # "auto" | "bullish" | "bearish"

# Plot & export
OUT_JSON = "double_wave_results.json"
PLOT_DIR = "plots_double_wave_math"

# --------------------------------------------

@dataclass
class WaveResult:
    direction: str
    baseline_price: float
    baseline_time: str
    peak1_price: float
    peak1_time: str
    pullback1_price: float
    pullback1_time: str
    peak2_price: float
    peak2_time: str
    pullback2_price: float
    pullback2_time: str
    wave1_amp_pips: float
    wave2_amp_pips: float
    double_wave: bool
    pullback1_ratio: float
    pullback2_ratio: float

def atr1m(df: pd.DataFrame, n: int = 14) -> pd.Series:
    hl = df['high'] - df['low']
    hc = (df['high'] - df['close'].shift()).abs()
    lc = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()

def find_nearest_row(df: pd.DataFrame, ts: pd.Timestamp, tolerance: timedelta = timedelta(minutes=1)) -> Optional[int]:
    i = df.index.get_indexer([ts], method='nearest')[0]
    if abs(df.index[i] - ts) <= tolerance:
        return i
    return None

def detect_double_wave_math(
    df_1m: pd.DataFrame,
    hint_ts: pd.Timestamp,
    direction_mode: str = DIRECTION_MODE,
    thr_wave1_dd: float = THR_WAVE1_DD,
    thr_wave2_dd: float = THR_WAVE2_DD,
    atr_k: float = ATR_K,
    atr_len: int = ATR_LEN,
    local_trough_width: int = LOCAL_WIDTH
) -> Optional[WaveResult]:
    """Pure mathematical double-wave detection as described by the user."""
    df = df_1m.sort_index().copy()
    if df.empty:
        return None

    # Compute ATR for pullback filter
    df['ATR'] = atr1m(df, n=atr_len)

    # Locate 14:30 bar (with ±1 min tolerance)
    if hint_ts not in df.index:
        idx0 = find_nearest_row(df, hint_ts, tolerance=timedelta(minutes=1))
        if idx0 is None:
            return None
    else:
        idx0 = df.index.get_loc(hint_ts)

    df_after = df.iloc[idx0:].copy()
    if df_after.empty:
        return None

    # Determine direction automatically using first ~6 minutes
    window_probe = df_after.iloc[:6]
    up_probe = (window_probe['high'].max() - df_after['low'].iloc[0])
    dn_probe = (df_after['high'].iloc[0] - window_probe['low'].min())
    if direction_mode == "auto":
        direction = "bullish" if up_probe >= dn_probe else "bearish"
    else:
        direction = direction_mode

    # Baseline at 14:30: low for bullish, high for bearish
    baseline_time = df_after.index[0]
    baseline_price = df_after['low'].iloc[0] if direction == "bullish" else df_after['high'].iloc[0]

    def is_local_trough(i: int) -> bool:
        lo = df_after['low'].iloc[i]
        L = max(0, i - local_trough_width)
        R = min(len(df_after)-1, i + local_trough_width)
        return lo == df_after['low'].iloc[L:R+1].min()

    def is_local_peak(i: int) -> bool:
        hi = df_after['high'].iloc[i]
        L = max(0, i - local_trough_width)
        R = min(len(df_after)-1, i + local_trough_width)
        return hi == df_after['high'].iloc[L:R+1].max()

    # ---- Wave 1 ----
    if direction == "bullish":
        peak1_price = baseline_price
        peak1_time  = baseline_time
        pullback1_price = None
        pullback1_time  = None
        for i in range(1, len(df_after)):
            row = df_after.iloc[i]
            if row['high'] > peak1_price:
                peak1_price = row['high']
                peak1_time  = df_after.index[i]
            amp = max(1e-9, peak1_price - baseline_price)
            dd  = (peak1_price - row['low']) / amp
            dd_filter = (peak1_price - row['low']) >= atr_k * df_after['ATR'].iloc[i]
            if dd >= thr_wave1_dd and dd_filter and is_local_trough(i):
                pullback1_price = row['low']
                pullback1_time  = df_after.index[i]
                break
    else:  # bearish
        peak1_price = baseline_price  # here "peak" is running low
        peak1_time  = baseline_time
        pullback1_price = None
        pullback1_time  = None
        for i in range(1, len(df_after)):
            row = df_after.iloc[i]
            if row['low'] < peak1_price:
                peak1_price = row['low']
                peak1_time  = df_after.index[i]
            amp = max(1e-9, baseline_price - peak1_price)
            dd  = (row['high'] - peak1_price) / amp
            dd_filter = (row['high'] - peak1_price) >= atr_k * df_after['ATR'].iloc[i]
            if dd >= thr_wave1_dd and dd_filter and is_local_peak(i):
                pullback1_price = row['high']
                pullback1_time  = df_after.index[i]
                break

    if pullback1_time is None:
        return None

    # ---- Wave 2 ----
    if direction == "bullish":
        peak2_price = peak1_price
        peak2_time  = peak1_time
        pullback2_price = None
        pullback2_time  = None
        start_i = df_after.index.get_loc(pullback1_time) + 1
        for i in range(start_i, len(df_after)):
            row = df_after.iloc[i]
            if row['high'] > peak2_price:
                peak2_price = row['high']
                peak2_time  = df_after.index[i]
            amp2 = max(1e-9, peak2_price - baseline_price)
            dd2  = (peak2_price - row['low']) / amp2
            dd2_filter = (peak2_price - row['low']) >= atr_k * df_after['ATR'].iloc[i]
            if dd2 >= thr_wave2_dd and dd2_filter and is_local_trough(i):
                pullback2_price = row['low']; pullback2_time = df_after.index[i]; break
    else:
        peak2_price = peak1_price
        peak2_time  = peak1_time
        pullback2_price = None
        pullback2_time  = None
        start_i = df_after.index.get_loc(pullback1_time) + 1
        for i in range(start_i, len(df_after)):
            row = df_after.iloc[i]
            if row['low'] < peak2_price:
                peak2_price = row['low']; peak2_time = df_after.index[i]
            amp2 = max(1e-9, baseline_price - peak2_price)
            dd2  = (row['high'] - peak2_price) / amp2
            dd2_filter = (row['high'] - peak2_price) >= atr_k * df_after['ATR'].iloc[i]
            if dd2 >= thr_wave2_dd and dd2_filter and is_local_peak(i):
                pullback2_price = row['high']; pullback2_time = df_after.index[i]; break

    if pullback2_time is None:
        return None

    # Validation
    double_ok = (peak2_price > peak1_price) if direction == "bullish" else (peak2_price < peak1_price)

    res = WaveResult(
        direction=direction,
        baseline_price=float(baseline_price),
        baseline_time=str(baseline_time),
        peak1_price=float(peak1_price),
        peak1_time=str(peak1_time),
        pullback1_price=float(pullback1_price),
        pullback1_time=str(pullback1_time),
        peak2_price=float(peak2_price),
        peak2_time=str(peak2_time),
        pullback2_price=float(pullback2_price),
        pullback2_time=str(pullback2_time),
        wave1_amp_pips=round(abs(peak1_price - baseline_price) * 1e4, 1),
        wave2_amp_pips=round(abs(peak2_price - baseline_price) * 1e4, 1),
        double_wave=bool(double_ok),
        pullback1_ratio=round(abs(peak1_price - pullback1_price) / max(1e-9, abs(peak1_price - baseline_price)), 3),
        pullback2_ratio=round(abs(peak2_price - pullback2_price) / max(1e-9, abs(peak2_price - baseline_price)), 3),
    )
    return res

def fetch_prices_bern(conn, start_ts: pd.Timestamp, end_ts: pd.Timestamp) -> pd.DataFrame:
    q = f"""
        SELECT datetime, open, high, low, close
        FROM {PRICES_TABLE}
        WHERE datetime BETWEEN ? AND ?
        ORDER BY datetime
    """
    # ✅ FIX: pass Python datetime directly (no .to_pydatetime())
    df = conn.execute(q, [start_ts, end_ts]).df()
    if df.empty:
        return df
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert('Europe/Zurich')
    df = df.set_index('datetime').sort_index()
    return df

def plot_result(df, res: WaveResult, out_path: Path, title_prefix: str = "EUR/USD – double wave (math)"):
    plt.figure(figsize=(11,5))
    mids = (df['high'] + df['low'])/2.0
    plt.plot(df.index, mids, linewidth=2)

    # Markers
    def mark(t_str, p, label, color='C3'):
        if t_str:
            t = pd.to_datetime(t_str)
            if t.tzinfo is None: t = t.tz_localize('Europe/Zurich')
            plt.scatter([t], [p], zorder=5, color=color)
            plt.text(t, p, label, ha='left', va='bottom')

    plt.axvline(pd.to_datetime(res.baseline_time), linestyle='--', color='C0', alpha=0.6)
    mark(res.baseline_time, res.baseline_price, "Baseline", 'C0')
    mark(res.peak1_time, res.peak1_price, "Peak1", 'C1')
    mark(res.pullback1_time, res.pullback1_price, "Pullback1", 'C2')
    mark(res.peak2_time, res.peak2_price, "Wave2", 'C3')
    mark(res.pullback2_time, res.pullback2_price, "Pullback2", 'C4')

    ttl = f"{title_prefix} | {res.direction} | Wave1 {res.wave1_amp_pips}p / Wave2 {res.wave2_amp_pips}p"
    plt.title(ttl); plt.xlabel("Heure (Europe/Zurich)"); plt.ylabel("Mid price")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, help="YYYY-MM-DD (single day)")
    parser.add_argument("--start", type=str, help="YYYY-MM-DD (range start)")
    parser.add_argument("--end", type=str, help="YYYY-MM-DD (range end)")
    args = parser.parse_args()

    tz = pytz.timezone("Europe/Zurich")
    if args.date:
        d0 = tz.localize(datetime.strptime(args.date, "%Y-%m-%d"))
        start_ts = d0.replace(hour=13, minute=45, second=0, microsecond=0)
        end_ts   = d0.replace(hour=16, minute=30, second=0, microsecond=0)
        label = args.date
    else:
        if not (args.start and args.end):
            raise SystemExit("Specify --date or (--start and --end).")
        s0 = tz.localize(datetime.strptime(args.start, "%Y-%m-%d"))
        e0 = tz.localize(datetime.strptime(args.end, "%Y-%m-%d"))
        start_ts = s0.replace(hour=13, minute=45, second=0, microsecond=0)
        end_ts   = e0.replace(hour=16, minute=30, second=0, microsecond=0)
        label = f"{args.start}_{args.end}"

    # Fetch data
    conn = duckdb.connect(DB_PATH, read_only=True)
    df = fetch_prices_bern(conn, start_ts, end_ts)
    conn.close()
    if df.empty:
        print("No data returned for the window."); return

    # Detect (baseline at 14:30 within the day)
    hint_ts = start_ts.replace(hour=14, minute=30, second=0, microsecond=0)
    res = detect_double_wave_math(df, hint_ts, direction_mode=DIRECTION_MODE)
    out_dir = Path(PLOT_DIR); out_dir.mkdir(exist_ok=True, parents=True)

    if res is None:
        payload = {"date": label, "double_wave": False, "reason": "not_detected"}
        Path(OUT_JSON).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("No double wave detected.")
        return

    # Export JSON
    payload = asdict(res)
    Path(OUT_JSON).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved JSON → {OUT_JSON}")

    # Plot
    png_path = out_dir / f"double_wave_{label}.png"
    plot_result(df, res, png_path, title_prefix=f"EUR/USD – Double Wave (math) [{label}]")
    print(f"Saved plot → {png_path}")

if __name__ == "__main__":
    main()
