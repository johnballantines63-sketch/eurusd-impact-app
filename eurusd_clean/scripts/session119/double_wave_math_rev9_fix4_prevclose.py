#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Double Wave Detector (rev 9 FIX4 — baseline = 14:29 CLOSE)
=========================================================
- Baseline = CLOSE de la bougie 14:29 (Europe/Zurich)
- Wave2: règle Break-then-Trough (cassure de Peak1 avant pullback)
- Pas de fenêtres fixes, fin par retracements (% + ATR)
"""

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pytz
from pathlib import Path

# ------------------ CONFIG ------------------
DB_PATH = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
PRICES_TABLE = "prices_bern"
THR_WAVE1_DD = 0.30
THR_WAVE2_DD = 0.20
ATR_K = 0.50
ATR_LEN = 14
LOCAL_WIDTH = 2
BREAK_EPS_PIPS = 1.5   # tolérance cassure Peak1
DIRECTION_MODE = "auto"
BASELINE_BACK_TOL_MIN = 5  # si 14:29 manquant, on prend le dernier close <=14:29 dans cette tolérance (minutes)
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

def atr1m(df, n=14):
    hl = df['high'] - df['low']
    hc = (df['high'] - df['close'].shift()).abs()
    lc = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()

def fetch_prices(conn, start_ts, end_ts):
    q = f"SELECT datetime, open, high, low, close FROM {PRICES_TABLE} WHERE datetime BETWEEN ? AND ? ORDER BY datetime"
    df = conn.execute(q, [start_ts, end_ts]).df()
    if df.empty:
        return df
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert('Europe/Zurich')
    df = df.set_index('datetime').sort_index()
    return df

def is_local_trough(df, i, width):
    lo = df['low'].iloc[i]
    L, R = max(0, i - width), min(len(df)-1, i + width)
    return lo == df['low'].iloc[L:R+1].min()

def is_local_peak(df, i, width):
    hi = df['high'].iloc[i]
    L, R = max(0, i - width), min(len(df)-1, i + width)
    return hi == df['high'].iloc[L:R+1].max()

def choose_direction(df_after):
    probe = df_after.iloc[:6]
    up_probe = probe['high'].max() - df_after['low'].iloc[0]
    dn_probe = df_after['high'].iloc[0] - probe['low'].min()
    return "bullish" if up_probe >= dn_probe else "bearish"

def get_baseline_prev_close(df, hint_ts, back_tol_min=5):
    """
    Baseline = CLOSE de 14:29:00; si manquant, chercher le dernier close <=14:29 dans une tolérance de back_tol_min.
    Retourne (baseline_price, baseline_time, idx_start_after_hint)
    """
    # trouver l'index le plus proche de 14:30
    i_hint = df.index.get_indexer([hint_ts], method='nearest')[0]
    # trouver la ligne strictement avant 14:30
    prior_slice = df.loc[:hint_ts - pd.Timedelta(seconds=1)]
    if prior_slice.empty:
        return None, None, None
    # viser 14:29 exact si présent, sinon dernier <=14:29 dans la fenêtre
    target_1429 = hint_ts - pd.Timedelta(minutes=1)
    # restreindre la fenêtre de recherche
    window_start = hint_ts - pd.Timedelta(minutes=back_tol_min+1)
    candidates = prior_slice.loc[window_start:target_1429]
    if candidates.empty:
        # fallback: prendre le dernier avant 14:30
        row = prior_slice.iloc[-1]
        t = prior_slice.index[-1]
        return float(row['close']), t, i_hint
    # idéalement prendre l'index le plus proche de 14:29 par le haut
    if target_1429 in candidates.index:
        t = target_1429
    else:
        # dernier timestamp <= 14:29
        t = candidates.index[-1]
    return float(df.loc[t, 'close']), t, i_hint

def detect_double_wave(df, hint_ts):
    df = df.sort_index().copy()
    df['ATR'] = atr1m(df, n=ATR_LEN)
    if df.empty:
        return None

    # Baseline = 14:29 CLOSE
    baseline_price, baseline_time, i_hint = get_baseline_prev_close(df, hint_ts, BASELINE_BACK_TOL_MIN)
    if baseline_time is None:
        return None

    # Série après 14:30 pour suivre la dynamique
    df_after = df.iloc[i_hint:].copy()
    if df_after.empty:
        return None

    direction = choose_direction(df_after)

    # ---- Wave 1 ----
    peak1_price = baseline_price
    peak1_time = baseline_time
    pullback1_price = None
    pullback1_time = None

    for i in range(len(df_after)):
        row = df_after.iloc[i]
        if direction == "bullish":
            if row['high'] > peak1_price:
                peak1_price = row['high']; peak1_time = df_after.index[i]
            amp = max(1e-9, peak1_price - baseline_price)
            dd = (peak1_price - row['low']) / amp if amp > 0 else 0.0
            dd_filter = (peak1_price - row['low']) >= ATR_K * df_after['ATR'].iloc[i]
            if amp > 0 and dd >= THR_WAVE1_DD and dd_filter and is_local_trough(df_after, i, LOCAL_WIDTH):
                pullback1_price = row['low']; pullback1_time = df_after.index[i]; break
        else:
            if row['low'] < peak1_price:
                peak1_price = row['low']; peak1_time = df_after.index[i]
            amp = max(1e-9, baseline_price - peak1_price)
            dd = (row['high'] - peak1_price) / amp if amp > 0 else 0.0
            dd_filter = (row['high'] - peak1_price) >= ATR_K * df_after['ATR'].iloc[i]
            if amp > 0 and dd >= THR_WAVE1_DD and dd_filter and is_local_peak(df_after, i, LOCAL_WIDTH):
                pullback1_price = row['high']; pullback1_time = df_after.index[i]; break

    if pullback1_time is None:
        return None

    # ---- Wave 2 (Break-then-Trough) ----
    peak2_price = peak1_price
    peak2_time = peak1_time
    pullback2_price = None
    pullback2_time = None
    start_i = df_after.index.get_loc(pullback1_time) + 1
    has_broken_peak1 = False

    for i in range(start_i, len(df_after)):
        row = df_after.iloc[i]
        if direction == "bullish":
            if row['high'] > peak2_price:
                peak2_price = row['high']; peak2_time = df_after.index[i]
            if not has_broken_peak1:
                if (peak2_price - peak1_price) * 1e4 >= BREAK_EPS_PIPS:
                    has_broken_peak1 = True
                else:
                    continue
            amp2 = max(1e-9, peak2_price - baseline_price)
            dd2 = (peak2_price - row['low']) / amp2 if amp2 > 0 else 0.0
            dd2_filter = (peak2_price - row['low']) >= ATR_K * df_after['ATR'].iloc[i]
            if amp2 > 0 and dd2 >= THR_WAVE2_DD and dd2_filter and is_local_trough(df_after, i, LOCAL_WIDTH):
                pullback2_price = row['low']; pullback2_time = df_after.index[i]; break
        else:
            if row['low'] < peak2_price:
                peak2_price = row['low']; peak2_time = df_after.index[i]
            if not has_broken_peak1:
                if (peak1_price - peak2_price) * 1e4 >= BREAK_EPS_PIPS:
                    has_broken_peak1 = True
                else:
                    continue
            amp2 = max(1e-9, baseline_price - peak2_price)
            dd2 = (row['high'] - peak2_price) / amp2 if amp2 > 0 else 0.0
            dd2_filter = (row['high'] - peak2_price) >= ATR_K * df_after['ATR'].iloc[i]
            if amp2 > 0 and dd2 >= THR_WAVE2_DD and dd2_filter and is_local_peak(df_after, i, LOCAL_WIDTH):
                pullback2_price = row['high']; pullback2_time = df_after.index[i]; break

    if pullback2_time is None:
        return None

    double_ok = (peak2_price > peak1_price) if direction == "bullish" else (peak2_price < peak1_price)

    return WaveResult(
        direction=direction,
        baseline_price=float(baseline_price), baseline_time=str(baseline_time),
        peak1_price=float(peak1_price), peak1_time=str(peak1_time),
        pullback1_price=float(pullback1_price), pullback1_time=str(pullback1_time),
        peak2_price=float(peak2_price), peak2_time=str(peak2_time),
        pullback2_price=float(pullback2_price), pullback2_time=str(pullback2_time),
        wave1_amp_pips=round(abs(peak1_price - baseline_price)*1e4, 1),
        wave2_amp_pips=round(abs(peak2_price - baseline_price)*1e4, 1),
        double_wave=bool(double_ok),
        pullback1_ratio=round(abs(peak1_price - pullback1_price)/max(1e-9, abs(peak1_price - baseline_price)),3),
        pullback2_ratio=round(abs(peak2_price - pullback2_price)/max(1e-9, abs(peak2_price - baseline_price)),3)
    )

def plot_result(df, res, out_path):
    plt.figure(figsize=(11,5))
    mids = (df['high'] + df['low'])/2
    plt.plot(df.index, mids, linewidth=2)
    def mark(t_str, p, label, color='C3'):
        if not t_str: return
        t = pd.to_datetime(t_str)
        if t.tzinfo is None: t = t.tz_localize('Europe/Zurich')
        plt.scatter([t],[p], zorder=5, color=color)
        plt.text(t, p, label, ha='left', va='bottom', fontsize=8)
    plt.axvline(pd.to_datetime(res.baseline_time), linestyle='--', color='C0', alpha=0.6)
    mark(res.baseline_time, res.baseline_price, 'Baseline(14:29 close)', 'C0')
    mark(res.peak1_time, res.peak1_price, 'Peak1', 'C1')
    mark(res.pullback1_time, res.pullback1_price, 'Pullback1', 'C2')
    mark(res.peak2_time, res.peak2_price, 'Peak2', 'C3')
    mark(res.pullback2_time, res.pullback2_price, 'Pullback2', 'C4')
    plt.title(f"Double Wave math | {res.direction} | W1 {res.wave1_amp_pips}p / W2 {res.wave2_amp_pips}p | double={res.double_wave}")
    plt.tight_layout(); plt.savefig(out_path, dpi=150); plt.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
    args = parser.parse_args()
    tz = pytz.timezone("Europe/Zurich")
    d0 = tz.localize(datetime.strptime(args.date, "%Y-%m-%d"))
    start_ts = d0.replace(hour=13, minute=45)
    end_ts   = d0.replace(hour=16, minute=30)
    hint_ts  = d0.replace(hour=14, minute=30)
    conn = duckdb.connect(DB_PATH, read_only=True)
    df = fetch_prices(conn, start_ts, end_ts); conn.close()
    if df.empty:
        print("⚠️ Aucun prix trouvé pour cette date."); return
    res = detect_double_wave(df, hint_ts)
    if res is None:
        print("Aucun pattern détecté."); return
    out_dir = Path("plots_double_wave_math"); out_dir.mkdir(exist_ok=True, parents=True)
    out_json = Path("double_wave_results.json"); out_json.write_text(json.dumps(asdict(res), indent=2), encoding='utf-8')
    png = out_dir / f"double_wave_{args.date}.png"; plot_result(df, res, png)
    print("✅ Résultats →", out_json); print("✅ Plot →", png)

if __name__ == "__main__":
    main()
