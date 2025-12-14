"""
Double Wave Detector — rev11 (CORRECTED: cherche pic MAXIMUM)
==============================================================
DIFFÉRENCE vs rev10: Ne s'arrête plus au premier pullback valide,
mais cherche le pic MAXIMUM puis valide le pullback final.

CORRECTION CIBLÉE (ligne ~180-220):
- Wave2 track pic maximum TANT QUE progression
- S'arrête après stagnation + pullback confirmé
- Valide pullback APRÈS avoir trouvé vrai peak

Basé sur rev10 avec modification algorithme Wave2.
"""

# Import tout le code rev10
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# Importer toutes les fonctions utilitaires rev10
from double_wave_detector_rev10 import (
    atr1m, to_pips, is_local_trough, is_local_peak,
    choose_direction, dynamic_thresholds, pick_baseline,
    load_ohlc_1m_duckdb, detect_for_date_duckdb,
    WaveDetection, asdict,
    DEFAULT_TZ, DEFAULT_BASELINE_MODE, BREAK_EPS_PIPS,
    LOCAL_WIDTH, MAX_IDLE_BARS, SCAN_MINUTES_AFTER_HINT
)

import pandas as pd
import numpy as np
from typing import Optional, Dict
from datetime import datetime


def detect_double_wave_on_df_rev11(
    df: pd.DataFrame,
    date_label: str,
    symbol: str = "EURUSD",
    tz: str = DEFAULT_TZ,
    baseline_mode: str = DEFAULT_BASELINE_MODE,
    minutes_after_hint: int = SCAN_MINUTES_AFTER_HINT,
    max_idle_bars: int = MAX_IDLE_BARS,
    local_width: int = LOCAL_WIDTH
) -> Optional[Dict]:
    """
    REV11: Cherche pic MAXIMUM pour Wave2 (pas premier pic valide)
    
    ALGORITHME CORRIGÉ:
    1. Wave1: identique rev10
    2. Wave2: Continue à tracker peak maximum jusqu'à stagnation confirmée
    3. Pullback: Validé APRÈS avoir trouvé vrai peak maximum
    """
    if df.empty:
        return None

    df = df.sort_index().copy()
    assert {'open','high','low','close'}.issubset(df.columns)
    assert df.index.tz is not None

    # ATR & regime (identique rev10)
    df['ATR'] = atr1m(df)
    day_atr_median = float(df['ATR'].median()) if not df['ATR'].empty else 0.0

    # Hint & baseline (identique rev10)
    hint_ts = df.index[0].replace(hour=14, minute=30, second=0, microsecond=0)
    baseline_price, baseline_time = pick_baseline(df, hint_ts, mode=baseline_mode)
    if baseline_time is None:
        return None

    # Slice & direction (identique rev10)
    end_ts = hint_ts + pd.Timedelta(minutes=minutes_after_hint)
    df_after = df.loc[hint_ts:end_ts].copy()
    if df_after.empty:
        return None

    direction = choose_direction(df_after)
    highs, lows = df_after['high'], df_after['low']

    # Thresholds (identique rev10)
    atr0 = float(df_after['ATR'].iloc[0]) if not df_after['ATR'].empty else day_atr_median
    w1_min_dd, w2_min_dd, atr_k = dynamic_thresholds(day_atr_median, atr0)

    # ---- Wave 1 (IDENTIQUE rev10) ----
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

    # ---- Wave 2 (CORRIGÉ REV11: cherche pic MAXIMUM) ----
    peak2_price = peak1_price
    peak2_time  = peak1_time
    pullback2_price = None
    pullback2_time = None

    start_i = df_after.index.get_loc(pullback1_time) + 1
    has_broken_peak1 = False
    idle = 0
    last_peak_update_i = start_i  # Track dernière mise à jour peak

    # PHASE 1: Trouver pic MAXIMUM (continue jusqu'à stagnation)
    for i in range(start_i, len(df_after)):
        ts = df_after.index[i]

        if direction == "bullish":
            if highs.iloc[i] > peak2_price:
                peak2_price = highs.iloc[i]
                peak2_time = ts
                last_peak_update_i = i
                idle = 0
                if to_pips(peak2_price - peak1_price) >= BREAK_EPS_PIPS:
                    has_broken_peak1 = True
            else:
                idle += 1
        else:
            if lows.iloc[i] < peak2_price:
                peak2_price = lows.iloc[i]
                peak2_time = ts
                last_peak_update_i = i
                idle = 0
                if to_pips(peak1_price - peak2_price) >= BREAK_EPS_PIPS:
                    has_broken_peak1 = True
            else:
                idle += 1

        # Si stagnation > max_idle_bars, pic maximum trouvé
        if idle >= max_idle_bars and has_broken_peak1:
            break

    if not has_broken_peak1:
        return None

    # PHASE 2: Valider pullback APRÈS peak maximum
    # Chercher pullback significatif APRÈS last_peak_update
    for i in range(last_peak_update_i + 1, len(df_after)):
        ts = df_after.index[i]
        atr_i = float(df_after['ATR'].iloc[i])

        if direction == "bullish":
            amp2 = max(1e-9, peak2_price - baseline_price)
            dd2 = (peak2_price - lows.iloc[i]) / amp2 if amp2>0 else 0.0
            dd2_filter = (peak2_price - lows.iloc[i]) >= atr_k * atr_i
            if amp2>0 and dd2 >= w2_min_dd and dd2_filter and is_local_trough(lows, i, local_width):
                pullback2_price = lows.iloc[i]
                pullback2_time = ts
                break
        else:
            amp2 = max(1e-9, baseline_price - peak2_price)
            dd2 = (highs.iloc[i] - peak2_price) / amp2 if amp2>0 else 0.0
            dd2_filter = (highs.iloc[i] - peak2_price) >= atr_k * atr_i
            if amp2>0 and dd2 >= w2_min_dd and dd2_filter and is_local_peak(highs, i, local_width):
                pullback2_price = highs.iloc[i]
                pullback2_time = ts
                break

    if pullback2_time is None:
        return None

    # Validation & métriques (identique rev10)
    double_ok = (peak2_price > peak1_price) if direction=="bullish" else (peak2_price < peak1_price)

    w1_pips = round(to_pips(abs(peak1_price - baseline_price)), 1)
    w2_pips = round(to_pips(abs(peak2_price - baseline_price)), 1)
    r1 = round(abs(peak1_price - pullback1_price) / max(1e-9, abs(peak1_price - baseline_price)), 3)
    r2 = round(abs(peak2_price - pullback2_price) / max(1e-9, abs(peak2_price - baseline_price)), 3)

    # Confidence (identique rev10)
    conf = 50.0
    if double_ok: conf += 20
    dt1 = (pd.Timestamp(peak1_time) - pd.Timestamp(baseline_time)).total_seconds()/60.0
    dt2 = (pd.Timestamp(peak2_time) - pd.Timestamp(pullback1_time)).total_seconds()/60.0
    if 5 <= dt1 <= 20: conf += 5
    if 5 <= dt2 <= 30: conf += 10
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


# Wrapper DuckDB pour rev11
def detect_for_date_duckdb_rev11(
    db_path: str, table: str, date: datetime,
    tz: str = DEFAULT_TZ,
    baseline_mode: str = DEFAULT_BASELINE_MODE,
    minutes_after_hint: int = SCAN_MINUTES_AFTER_HINT,
    trading_window: bool = True
) -> Optional[Dict]:
    """Rev11 avec chargement DuckDB"""
    ts = pd.Timestamp(date, tz=tz)
    if trading_window:
        start_dt = ts.replace(hour=13, minute=0, second=0, microsecond=0)
        end_dt   = ts.replace(hour=16, minute=30, second=0, microsecond=0)
    else:
        start_dt = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt   = ts.replace(hour=23, minute=59, second=59, microsecond=0)

    df = load_ohlc_1m_duckdb(db_path, table, tz, start_dt, end_dt)
    if df.empty: return None
    
    return detect_double_wave_on_df_rev11(
        df, date_label=ts.strftime("%Y-%m-%d"), symbol="EURUSD", tz=tz,
        baseline_mode=baseline_mode, minutes_after_hint=minutes_after_hint
    )


if __name__ == "__main__":
    print("Rev11: Utiliser test_double_wave_rev11.py pour tester")
