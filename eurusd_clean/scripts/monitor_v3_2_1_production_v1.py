#!/usr/bin/env python3
"""
Monitor V3.2.1 Production Performance
=====================================

Monitor production model performance and data quality:
- Correlation pred vs actual (rolling windows)
- Rank stability
- Distribution drift
- Comparison vs baseline V2.1

Usage:
  python3 scripts/monitor_v3_2_1_production_v1.py
  python3 scripts/monitor_v3_2_1_production_v1.py --window 60
  python3 scripts/monitor_v3_2_1_production_v1.py --from 2024-01-01
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import duckdb
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

PRED_TABLE = "daily_risk_signal_v3_2_1"
VOL_VIEW = "daily_eurusd_volatility_v1"
V2_1_VIEW = "daily_pred_score_release_group_v1"  # Baseline V2.1


def connect_duckdb_with_retry(path: Path, read_only: bool, max_retries: int = 5, sleep_s: int = 3) -> duckdb.DuckDBPyConnection:
    for i in range(max_retries):
        try:
            return duckdb.connect(str(path), read_only=read_only)
        except Exception as e:
            if "lock" in str(e).lower() and i < max_retries - 1:
                print(f"⚠️  Lock détecté, attente {sleep_s}s... (tentative {i+1}/{max_retries})")
                time.sleep(sleep_s)
            else:
                raise
    raise RuntimeError("Unable to connect to DuckDB after retries")


def calculate_correlations(y_true, y_pred):
    """Calcule Pearson et Spearman."""
    df_clean = pd.DataFrame({'true': y_true, 'pred': y_pred}).dropna()
    if len(df_clean) < 2:
        return None, None
    
    if df_clean['true'].std() == 0 or df_clean['pred'].std() == 0:
        return None, None
    
    pearson = df_clean['true'].corr(df_clean['pred'])
    
    try:
        spearman, _ = spearmanr(df_clean['true'], df_clean['pred'])
        if np.isnan(spearman):
            spearman = None
    except:
        spearman = None
    
    return pearson, spearman


def monitor_correlation(conn, date_from: Optional[str], window_days: int = 30):
    """Corrélation glissante pred vs actual."""
    where_clause = f"WHERE s.date >= DATE '{date_from}'" if date_from else ""
    
    df = conn.execute(f"""
        SELECT
            s.date,
            s.pred_vol_pips,
            v.daily_volatility_pips_v1 AS actual_vol
        FROM {PRED_TABLE} s
        INNER JOIN {VOL_VIEW} v ON s.date = v.date
        {where_clause}
        ORDER BY s.date
    """).df()
    
    if df.empty:
        return None, None, None
    
    # Rolling correlations
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    rolling_corrs = []
    rolling_spear = []
    
    for i in range(window_days, len(df) + 1):
        window = df.iloc[i - window_days:i]
        pearson, spearman = calculate_correlations(window['actual_vol'], window['pred_vol_pips'])
        if pearson is not None:
            rolling_corrs.append(pearson)
        if spearman is not None:
            rolling_spear.append(spearman)
    
    # Overall correlation
    pearson_all, spearman_all = calculate_correlations(df['actual_vol'], df['pred_vol_pips'])
    
    return pearson_all, spearman_all, {
        'rolling_pearson_mean': np.mean(rolling_corrs) if rolling_corrs else None,
        'rolling_pearson_std': np.std(rolling_corrs) if rolling_corrs else None,
        'rolling_spearman_mean': np.mean(rolling_spear) if rolling_spear else None,
        'rolling_spearman_std': np.std(rolling_spear) if rolling_spear else None,
    }


def monitor_distribution(conn, date_from: Optional[str]):
    """Distribution drift check."""
    where_clause = f"WHERE date >= DATE '{date_from}'" if date_from else ""
    
    df = conn.execute(f"""
        SELECT
            date,
            pred_vol_pips
        FROM {PRED_TABLE}
        {where_clause}
        ORDER BY date
    """).df()
    
    if df.empty:
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Split into halves
    n = len(df)
    first_half = df.iloc[:n//2]['pred_vol_pips']
    second_half = df.iloc[n//2:]['pred_vol_pips']
    
    return {
        'first_half_mean': first_half.mean(),
        'first_half_std': first_half.std(),
        'second_half_mean': second_half.mean(),
        'second_half_std': second_half.std(),
        'drift_ratio': (second_half.mean() - first_half.mean()) / (first_half.mean() + 1e-6),
    }


def monitor_vs_baseline(conn, date_from: Optional[str]):
    """Compare V3.2.1 vs V2.1 baseline."""
    where_clause = f"WHERE s.date >= DATE '{date_from}'" if date_from else ""
    
    df = conn.execute(f"""
        SELECT
            s.date,
            s.pred_vol_pips AS pred_v3_2_1,
            v.daily_volatility_pips_v1 AS actual_vol,
            v2.pred_daily_release_top20_sum_top2 AS score_v2_1
        FROM {PRED_TABLE} s
        INNER JOIN {VOL_VIEW} v ON s.date = v.date
        LEFT JOIN {V2_1_VIEW} v2 ON s.date = v2.date
        {where_clause}
        ORDER BY s.date
    """).df()
    
    if df.empty or df['score_v2_1'].isna().all():
        return None
    
    # Correlations
    pearson_v3, spearman_v3 = calculate_correlations(df['actual_vol'], df['pred_v3_2_1'])
    
    # V2.1 baseline (log1p transform for fair comparison)
    df_v2_clean = df.dropna(subset=['score_v2_1', 'actual_vol'])
    if len(df_v2_clean) >= 2:
        pearson_v2, spearman_v2 = calculate_correlations(
            df_v2_clean['actual_vol'],
            np.log1p(df_v2_clean['score_v2_1'])
        )
    else:
        pearson_v2, spearman_v2 = None, None
    
    return {
        'pearson_v3_2_1': pearson_v3,
        'spearman_v3_2_1': spearman_v3,
        'pearson_v2_1': pearson_v2,
        'spearman_v2_1': spearman_v2,
        'delta_pearson': pearson_v3 - pearson_v2 if (pearson_v3 is not None and pearson_v2 is not None) else None,
        'delta_spearman': spearman_v3 - spearman_v2 if (spearman_v3 is not None and spearman_v2 is not None) else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Monitor V3.2.1 production performance")
    parser.add_argument("--from", dest="date_from", type=str, default=None,
                       help="Start date YYYY-MM-DD (default: all available)")
    parser.add_argument("--window", type=int, default=30,
                       help="Rolling window days for correlation (default: 30)")
    args = parser.parse_args()
    
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)
    
    try:
        conn = connect_duckdb_with_retry(DB_PATH, read_only=True)
    except Exception as e:
        print(f"❌ DuckDB connect failed: {e}")
        sys.exit(1)
    
    try:
        print("=" * 110)
        print("MONITOR: V3.2.1 PRODUCTION PERFORMANCE")
        print("=" * 110)
        print(f"DB: {DB_PATH}")
        print(f"Prediction table: {PRED_TABLE}")
        print(f"Date filter: {args.date_from or 'all'}")
        print(f"Rolling window: {args.window} days")
        print()
        
        # 1. Basic stats
        print("📊 BASIC STATS")
        print("-" * 110)
        df_stats = conn.execute(f"""
            SELECT
                COUNT(*) AS n_predictions,
                MIN(date) AS min_date,
                MAX(date) AS max_date,
                COUNT(DISTINCT model_version) AS n_versions
            FROM {PRED_TABLE}
            {f"WHERE date >= DATE '{args.date_from}'" if args.date_from else ""}
        """).df()
        print(df_stats.to_string(index=False))
        print()
        
        # 2. Correlation pred vs actual
        print("📈 CORRELATION: PRED vs ACTUAL")
        print("-" * 110)
        pearson_all, spearman_all, rolling = monitor_correlation(conn, args.date_from, args.window)
        
        if pearson_all is not None:
            print(f"Overall Pearson:  {pearson_all:.4f}")
            print(f"Overall Spearman: {spearman_all:.4f}")
        else:
            print("⚠️  Cannot calculate correlation (insufficient data)")
        
        if rolling:
            if rolling['rolling_pearson_mean'] is not None:
                print(f"\nRolling {args.window}d window:")
                print(f"  Pearson:  {rolling['rolling_pearson_mean']:.4f} ± {rolling['rolling_pearson_std']:.4f}")
                print(f"  Spearman: {rolling['rolling_spearman_mean']:.4f} ± {rolling['rolling_spearman_std']:.4f}")
        print()
        
        # 3. Distribution drift
        print("📊 DISTRIBUTION DRIFT")
        print("-" * 110)
        drift = monitor_distribution(conn, args.date_from)
        if drift:
            print(f"First half:  mean={drift['first_half_mean']:.2f}, std={drift['first_half_std']:.2f}")
            print(f"Second half: mean={drift['second_half_mean']:.2f}, std={drift['second_half_std']:.2f}")
            print(f"Drift ratio: {drift['drift_ratio']:.2%}")
            if abs(drift['drift_ratio']) > 0.20:
                print("⚠️  WARNING: Significant distribution drift detected (>20%)")
        else:
            print("⚠️  Cannot calculate drift (insufficient data)")
        print()
        
        # 4. Comparison vs baseline V2.1
        print("🔄 COMPARISON vs BASELINE V2.1")
        print("-" * 110)
        baseline = monitor_vs_baseline(conn, args.date_from)
        if baseline:
            print(f"V3.2.1 Pearson:  {baseline['pearson_v3_2_1']:.4f}" if baseline['pearson_v3_2_1'] else "V3.2.1 Pearson:  N/A")
            print(f"V3.2.1 Spearman: {baseline['spearman_v3_2_1']:.4f}" if baseline['spearman_v3_2_1'] else "V3.2.1 Spearman: N/A")
            print(f"V2.1 Pearson:    {baseline['pearson_v2_1']:.4f}" if baseline['pearson_v2_1'] else "V2.1 Pearson:    N/A")
            print(f"V2.1 Spearman:   {baseline['spearman_v2_1']:.4f}" if baseline['spearman_v2_1'] else "V2.1 Spearman:   N/A")
            if baseline['delta_spearman'] is not None:
                print(f"\nDelta Spearman: {baseline['delta_spearman']:+.4f}")
                if baseline['delta_spearman'] > 0:
                    print("✅ V3.2.1 outperforms V2.1")
                else:
                    print("⚠️  V3.2.1 underperforms V2.1")
        else:
            print("⚠️  Cannot compare (V2.1 baseline data unavailable)")
        print()
        
        # 5. Recent predictions (last 10 days)
        print("📅 RECENT PREDICTIONS (last 10 days)")
        print("-" * 110)
        df_recent = conn.execute(f"""
            SELECT
                s.date,
                s.pred_vol_pips,
                v.daily_volatility_pips_v1 AS actual_vol,
                ABS(s.pred_vol_pips - v.daily_volatility_pips_v1) AS error
            FROM {PRED_TABLE} s
            LEFT JOIN {VOL_VIEW} v ON s.date = v.date
            ORDER BY s.date DESC
            LIMIT 10
        """).df()
        print(df_recent.to_string(index=False))
        print()
        
        print("=" * 110)
        print("✅ Monitoring completed")
        print("=" * 110)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()

