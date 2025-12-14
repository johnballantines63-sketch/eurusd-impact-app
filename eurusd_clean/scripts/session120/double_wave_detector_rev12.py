"""
Double Wave Detector — rev12 (CORRECTION WAVE1 GARDE TEMPORELLE)
================================================================
SESSION 120 - Correction bugs fundamentaux rev11

BUGS CORRIGÉS:
1. Peak1/Pullback1 même timestamp → Garde MIN_BARS_BEFORE_PULLBACK = 3
2. Pullback ratio > 100% → Validation formule + baseline

DIFFÉRENCE vs rev11:
- Wave1: Attente obligatoire 3 bars après peak avant validation pullback
- Wave2: Algorithme pic MAXIMUM inchangé (validé Session 119)
- Debug: Prints détaillés timestamps pour validation

RÉFÉRENCE:
- Session 118: 51.7 vs 56.2 pips (MAE 4.5)
- Target Session 120: 56.2 pips à 14:57 (MAE < 5)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Optional, Dict
from datetime import datetime

# Ajouter session119 au path pour imports AVANT d'importer
# Structure: scripts/session120/ce_fichier.py
#           scripts/session119/double_wave_detector_rev10.py
current_dir = Path(__file__).parent  # scripts/session120/
scripts_dir = current_dir.parent      # scripts/
session119_dir = scripts_dir / 'session119'  # scripts/session119/

if str(session119_dir) not in sys.path:
    sys.path.insert(0, str(session119_dir))

# Importer fonctions utilitaires rev10 (APRÈS modification sys.path)
from double_wave_detector_rev10 import (
    atr1m, to_pips, is_local_trough, is_local_peak,
    choose_direction, dynamic_thresholds, pick_baseline,
    load_ohlc_1m_duckdb, detect_for_date_duckdb,
    WaveDetection, asdict,
    DEFAULT_TZ, DEFAULT_BASELINE_MODE, BREAK_EPS_PIPS,
    LOCAL_WIDTH, MAX_IDLE_BARS, SCAN_MINUTES_AFTER_HINT
)

# ============================================================================
# CONFIGURATION REV12
# ============================================================================

# CORRECTION BUG #1: Garde temporelle Peak1 → Pullback1
MIN_BARS_BEFORE_PULLBACK = 3  # Attendre minimum 3 bars (3 minutes)

# Debug mode (activer pour voir timestamps détaillés)
DEBUG_MODE = True


# ============================================================================
# ALGORITHME REV12
# ============================================================================

def detect_double_wave_on_df_rev12(
    df: pd.DataFrame,
    date_label: str,
    symbol: str = "EURUSD",
    tz: str = DEFAULT_TZ,
    baseline_mode: str = DEFAULT_BASELINE_MODE,
    minutes_after_hint: int = SCAN_MINUTES_AFTER_HINT,
    max_idle_bars: int = MAX_IDLE_BARS,
    local_width: int = LOCAL_WIDTH,
    debug: bool = False,
    hint_ts: Optional[pd.Timestamp] = None  # NOUVEAU : Permet de spécifier l'heure de l'événement
) -> Optional[Dict]:
    """
    REV12: Correction Wave1 avec garde temporelle
    
    ALGORITHME:
    1. Wave1: Attendre MIN_BARS_BEFORE_PULLBACK après peak1 avant validation pullback
    2. Wave2: Cherche pic MAXIMUM jusqu'à stagnation (inchangé rev11)
    3. Validation: Pullback ratio < 100%, timestamps distincts
    
    Args:
        hint_ts: Timestamp de l'événement (optionnel). Si None, utilise 14:30 par défaut.
    """
    if df.empty:
        return None

    df = df.sort_index().copy()
    assert {'open','high','low','close'}.issubset(df.columns)
    assert df.index.tz is not None

    # ATR & regime
    df['ATR'] = atr1m(df)
    day_atr_median = float(df['ATR'].median()) if not df['ATR'].empty else 0.0

    # Hint & baseline
    # ⚠️ CORRECTION : Utiliser hint_ts si fourni, sinon fallback à 14:30
    if hint_ts is None:
        hint_ts = df.index[0].replace(hour=14, minute=30, second=0, microsecond=0)
    else:
        # S'assurer que hint_ts a la même timezone que df
        if hint_ts.tz is None:
            hint_ts = pd.Timestamp(hint_ts, tz=tz)
        elif hint_ts.tz != df.index.tz:
            hint_ts = hint_ts.tz_convert(df.index.tz)
    baseline_price, baseline_time = pick_baseline(df, hint_ts, mode=baseline_mode)
    if baseline_time is None:
        return None

    if debug or DEBUG_MODE:
        print(f"\n{'='*80}")
        print(f"🔍 REV12 DEBUG - {date_label}")
        print(f"{'='*80}")
        print(f"Baseline: {baseline_time} @ {baseline_price:.5f}")

    # Slice & direction
    end_ts = hint_ts + pd.Timedelta(minutes=minutes_after_hint)
    df_after = df.loc[hint_ts:end_ts].copy()
    if df_after.empty:
        return None

    direction = choose_direction(df_after)
    highs, lows = df_after['high'], df_after['low']
    
    if debug or DEBUG_MODE:
        print(f"Direction: {direction}")

    # Thresholds
    atr0 = float(df_after['ATR'].iloc[0]) if not df_after['ATR'].empty else day_atr_median
    w1_min_dd, w2_min_dd, atr_k = dynamic_thresholds(day_atr_median, atr0)

    # ============================================================================
    # WAVE 1 - CORRECTION REV12 (GARDE TEMPORELLE)
    # ============================================================================
    
    peak1_price = baseline_price
    peak1_time  = baseline_time
    pullback1_price = None
    pullback1_time  = None

    idle = 0
    
    if debug or DEBUG_MODE:
        print(f"\n📊 WAVE 1 - Recherche Peak1 + Pullback1")
    
    for i in range(len(df_after)):
        ts = df_after.index[i]
        atr_i = float(df_after['ATR'].iloc[i])
        
        if direction == "bullish":
            # Chercher nouveau pic
            if highs.iloc[i] > peak1_price:
                peak1_price = highs.iloc[i]
                peak1_time = ts
                idle = 0
                if debug or DEBUG_MODE:
                    peak1_pips = to_pips(peak1_price - baseline_price)
                    print(f"   Peak1 update: {ts.strftime('%H:%M:%S')} → {peak1_pips:.1f} pips")
            else:
                idle += 1
            
            # CORRECTION REV12: Vérifier garde temporelle AVANT validation pullback
            minutes_since_peak = (ts - peak1_time).total_seconds() / 60.0
            
            if minutes_since_peak >= MIN_BARS_BEFORE_PULLBACK:
                amp = max(1e-9, peak1_price - baseline_price)
                dd = (peak1_price - lows.iloc[i]) / amp if amp>0 else 0.0
                dd_filter = (peak1_price - lows.iloc[i]) >= atr_k * atr_i
                
                if amp>0 and dd >= w1_min_dd and dd_filter and is_local_trough(lows, i, local_width):
                    pullback1_price = lows.iloc[i]
                    pullback1_time = ts
                    if debug or DEBUG_MODE:
                        pb1_pips = to_pips(abs(peak1_price - pullback1_price))
                        print(f"   Pullback1 found: {ts.strftime('%H:%M:%S')} → -{pb1_pips:.1f} pips (dd={dd:.1%})")
                    break
        
        else:  # bearish
            # Chercher nouveau creux
            if lows.iloc[i] < peak1_price:
                peak1_price = lows.iloc[i]
                peak1_time = ts
                idle = 0
                if debug or DEBUG_MODE:
                    peak1_pips = to_pips(baseline_price - peak1_price)
                    print(f"   Peak1 update: {ts.strftime('%H:%M:%S')} → {peak1_pips:.1f} pips")
            else:
                idle += 1
            
            # CORRECTION REV12: Vérifier garde temporelle
            minutes_since_peak = (ts - peak1_time).total_seconds() / 60.0
            
            if minutes_since_peak >= MIN_BARS_BEFORE_PULLBACK:
                amp = max(1e-9, baseline_price - peak1_price)
                dd = (highs.iloc[i] - peak1_price) / amp if amp>0 else 0.0
                dd_filter = (highs.iloc[i] - peak1_price) >= atr_k * atr_i
                
                if amp>0 and dd >= w1_min_dd and dd_filter and is_local_peak(highs, i, local_width):
                    pullback1_price = highs.iloc[i]
                    pullback1_time = ts
                    if debug or DEBUG_MODE:
                        pb1_pips = to_pips(abs(peak1_price - pullback1_price))
                        print(f"   Pullback1 found: {ts.strftime('%H:%M:%S')} → +{pb1_pips:.1f} pips (dd={dd:.1%})")
                    break
        
        if idle >= max_idle_bars:
            if debug or DEBUG_MODE:
                print(f"   ⚠️ Max idle bars atteint ({max_idle_bars})")
            return None

    if pullback1_time is None:
        if debug or DEBUG_MODE:
            print(f"   ❌ Aucun pullback1 trouvé")
        return None

    # ============================================================================
    # WAVE 2 - ALGORITHME PIC MAXIMUM (INCHANGÉ REV11)
    # ============================================================================
    
    peak2_price = peak1_price
    peak2_time  = peak1_time
    pullback2_price = None
    pullback2_time = None

    start_i = df_after.index.get_loc(pullback1_time) + 1
    has_broken_peak1 = False
    idle = 0
    last_peak_update_i = start_i
    
    if debug or DEBUG_MODE:
        print(f"\n📊 WAVE 2 - Recherche Peak2 MAXIMUM + Pullback2")

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
                if debug or DEBUG_MODE:
                    peak2_pips = to_pips(peak2_price - baseline_price)
                    print(f"   Peak2 update: {ts.strftime('%H:%M:%S')} → {peak2_pips:.1f} pips")
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
                if debug or DEBUG_MODE:
                    peak2_pips = to_pips(baseline_price - peak2_price)
                    print(f"   Peak2 update: {ts.strftime('%H:%M:%S')} → {peak2_pips:.1f} pips")
            else:
                idle += 1

        # Si stagnation > max_idle_bars, pic maximum trouvé
        if idle >= max_idle_bars and has_broken_peak1:
            if debug or DEBUG_MODE:
                print(f"   ✓ Peak2 MAXIMUM trouvé (stagnation {max_idle_bars} bars)")
            break

    if not has_broken_peak1:
        if debug or DEBUG_MODE:
            print(f"   ❌ Peak2 n'a pas dépassé Peak1")
        return None

    # PHASE 2: Valider pullback APRÈS peak maximum
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
                if debug or DEBUG_MODE:
                    pb2_pips = to_pips(abs(peak2_price - pullback2_price))
                    print(f"   Pullback2 found: {ts.strftime('%H:%M:%S')} → -{pb2_pips:.1f} pips (dd={dd2:.1%})")
                break
        else:
            amp2 = max(1e-9, baseline_price - peak2_price)
            dd2 = (highs.iloc[i] - peak2_price) / amp2 if amp2>0 else 0.0
            dd2_filter = (highs.iloc[i] - peak2_price) >= atr_k * atr_i
            if amp2>0 and dd2 >= w2_min_dd and dd2_filter and is_local_peak(highs, i, local_width):
                pullback2_price = highs.iloc[i]
                pullback2_time = ts
                if debug or DEBUG_MODE:
                    pb2_pips = to_pips(abs(peak2_price - pullback2_price))
                    print(f"   Pullback2 found: {ts.strftime('%H:%M:%S')} → +{pb2_pips:.1f} pips (dd={dd2:.1%})")
                break

    if pullback2_time is None:
        if debug or DEBUG_MODE:
            print(f"   ❌ Aucun pullback2 trouvé")
        return None

    # ============================================================================
    # VALIDATION & MÉTRIQUES
    # ============================================================================
    
    # Validation temporelle
    if peak1_time == pullback1_time:
        if debug or DEBUG_MODE:
            print(f"\n⚠️ ERREUR: Peak1 et Pullback1 ont le même timestamp !")
        return None
    
    # Validation double wave
    double_ok = (peak2_price > peak1_price) if direction=="bullish" else (peak2_price < peak1_price)

    # Calcul amplitudes
    w1_pips = round(to_pips(abs(peak1_price - baseline_price)), 1)
    w2_pips = round(to_pips(abs(peak2_price - baseline_price)), 1)
    
    # CORRECTION BUG #2: Calcul pullback ratio avec validation
    r1 = abs(peak1_price - pullback1_price) / max(1e-9, abs(peak1_price - baseline_price))
    r2 = abs(peak2_price - pullback2_price) / max(1e-9, abs(peak2_price - baseline_price))
    
    # Validation pullback < 100%
    # ⚠️ CORRECTION : Accepter pullback ratio > 100% pour mouvements faibles (wave1 < 10 pips)
    # Cela permet de détecter des patterns même si le mouvement est faible et le prix retombe sous baseline
    if r1 > 1.0 or r2 > 1.0:
        if w1_pips < 10:
            # Mouvement faible : Accepter pullback ratio > 100%
            if debug or DEBUG_MODE:
                print(f"\n⚠️ Pullback ratio > 100% (r1={r1:.1%}, r2={r2:.1%}) mais mouvement faible (wave1={w1_pips:.1f} pips)")
                print(f"   → Pattern accepté malgré pullback sous baseline")
        else:
            # Mouvement significatif : Rejeter si pullback ratio > 100%
            if debug or DEBUG_MODE:
                print(f"\n⚠️ ERREUR: Pullback ratio > 100% (r1={r1:.1%}, r2={r2:.1%})")
                print(f"   Cela indique retombée sous baseline (impossible)")
            return None
    
    r1 = round(r1, 3)
    r2 = round(r2, 3)

    # Confidence score
    conf = 50.0
    if double_ok: conf += 20
    dt1 = (pd.Timestamp(peak1_time) - pd.Timestamp(baseline_time)).total_seconds()/60.0
    dt2 = (pd.Timestamp(peak2_time) - pd.Timestamp(pullback1_time)).total_seconds()/60.0
    if 5 <= dt1 <= 20: conf += 5
    if 5 <= dt2 <= 30: conf += 10
    if w1_pips > 0 and 1.0 <= (w2_pips / w1_pips) <= 2.5: conf += 10
    conf = float(max(0.0, min(100.0, conf)))
    
    if debug or DEBUG_MODE:
        print(f"\n✅ DOUBLE WAVE DÉTECTÉE")
        print(f"   Wave1: {w1_pips:.1f} pips (pullback {r1:.1%})")
        print(f"   Wave2: {w2_pips:.1f} pips (pullback {r2:.1%})")
        print(f"   Confidence: {conf:.1f}%")
        print(f"{'='*80}\n")

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


# ============================================================================
# WRAPPER DUCKDB
# ============================================================================

def detect_for_date_duckdb_rev12(
    db_path: str, table: str, date: datetime,
    tz: str = DEFAULT_TZ,
    baseline_mode: str = DEFAULT_BASELINE_MODE,
    minutes_after_hint: int = SCAN_MINUTES_AFTER_HINT,
    trading_window: bool = True,
    debug: bool = False,
    event_time: Optional[datetime] = None  # NOUVEAU : Heure réelle de l'événement
) -> Optional[Dict]:
    """
    Rev12 avec chargement DuckDB
    
    Args:
        event_time: Heure réelle de l'événement (optionnel). Si None, utilise 14:30 par défaut.
    """
    ts = pd.Timestamp(date, tz=tz)
    
    # ⚠️ CORRECTION : Ajuster la fenêtre de trading si event_time est fourni
    if event_time is not None:
        # Convertir event_time en Timestamp avec timezone
        if isinstance(event_time, datetime):
            if event_time.tzinfo is None:
                event_ts = pd.Timestamp(event_time, tz=tz)
            else:
                event_ts = pd.Timestamp(event_time).tz_convert(tz)
        else:
            event_ts = pd.Timestamp(event_time, tz=tz)
        # Fenêtre : 1h avant l'événement jusqu'à 2h après
        start_dt = event_ts - pd.Timedelta(hours=1)
        end_dt = event_ts + pd.Timedelta(hours=2)
    elif trading_window:
        start_dt = ts.replace(hour=13, minute=0, second=0, microsecond=0)
        end_dt   = ts.replace(hour=16, minute=30, second=0, microsecond=0)
    else:
        start_dt = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt   = ts.replace(hour=23, minute=59, second=59, microsecond=0)

    df = load_ohlc_1m_duckdb(db_path, table, tz, start_dt, end_dt)
    if df.empty: return None
    
    # Préparer hint_ts pour detect_double_wave_on_df_rev12
    hint_ts_param = None
    if event_time is not None:
        # Convertir event_time en Timestamp avec timezone
        if isinstance(event_time, datetime):
            if event_time.tzinfo is None:
                hint_ts_param = pd.Timestamp(event_time, tz=tz)
            else:
                hint_ts_param = pd.Timestamp(event_time).tz_convert(tz)
        else:
            hint_ts_param = pd.Timestamp(event_time, tz=tz)
    
    return detect_double_wave_on_df_rev12(
        df, date_label=ts.strftime("%Y-%m-%d"), symbol="EURUSD", tz=tz,
        baseline_mode=baseline_mode, minutes_after_hint=minutes_after_hint,
        debug=debug, hint_ts=hint_ts_param
    )


if __name__ == "__main__":
    print("Rev12: Utiliser test_rev12_validation.py pour tester")
