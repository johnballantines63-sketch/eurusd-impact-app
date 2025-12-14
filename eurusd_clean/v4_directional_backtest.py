#!/usr/bin/env python3
"""
V4 Directional Backtest (prob_up vs truth_dir)

- Reads a scoring CSV (must include: date_local, prob_up)
- Joins with DuckDB truth table: daily_pattern_truth_v4 (date_local, direction)
- Computes: accuracy, balanced accuracy, brier, logloss, AUC (rank), confusion matrix
- Optional calibration table (quantile bins)

Usage:
  python3 v4_directional_backtest.py \
    --db data/warehouse.duckdb \
    --csv outputs/v4_scores_panel_20251214_080122.csv \
    --years 3

Notes:
- truth_dir uses daily_pattern_truth_v4.direction in {-1,+1}. Others are ignored.
- prob_up is clipped to [1e-9, 1-1e-9] for logloss stability.
"""

import argparse
from datetime import date, timedelta

import duckdb
import numpy as np
import pandas as pd


def _to_date_series(s: pd.Series) -> pd.Series:
    """Parse to python date (YYYY-MM-DD)."""
    dt = pd.to_datetime(s, errors="coerce")
    return dt.dt.date


def compute_auc_rank(y: np.ndarray, p: np.ndarray) -> float:
    """AUC via rank statistic; returns nan if only one class."""
    if not ((y == 1).any() and (y == 0).any()):
        return float("nan")
    ranks = pd.Series(p).rank(method="average").to_numpy()
    r_pos = ranks[y == 1].sum()
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    return float((r_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def calibration_table(df: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    """Quantile-bin calibration: mean prob vs empirical freq."""
    if df["prob_up"].nunique() < 2:
        return pd.DataFrame(
            {"n": [len(df)], "mean_p": [df["prob_up"].mean()], "frac_up": [df["y"].mean()]}
        )
    q = min(bins, int(df["prob_up"].nunique()))
    df = df.copy()
    df["bin"] = pd.qcut(df["prob_up"], q=q, duplicates="drop")
    return (
        df.groupby("bin", observed=True)
        .agg(n=("y", "size"), mean_p=("prob_up", "mean"), frac_up=("y", "mean"))
        .reset_index()
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="V4 Directional Backtest (prob_up vs truth_dir)")
    ap.add_argument("--db", required=True, help="DuckDB path (e.g., data/warehouse.duckdb)")
    ap.add_argument("--csv", required=True, help="Scoring CSV path (must have date_local, prob_up)")
    ap.add_argument("--years", type=float, default=3.0, help="Lookback window in years (default: 3)")
    ap.add_argument("--threshold", type=float, default=0.5, help="Decision threshold for prob_up (default: 0.5)")
    ap.add_argument("--no-calibration", action="store_true", help="Disable calibration table output")
    ap.add_argument("--calib-bins", type=int, default=10, help="Calibration bins (default: 10)")
    ap.add_argument("--min-matched", type=int, default=30, help="Warn if matched rows < this (default: 30)")
    args = ap.parse_args()

    # Load scores CSV
    scores = pd.read_csv(args.csv)
    if "date_local" not in scores.columns or "prob_up" not in scores.columns:
        raise SystemExit(f"CSV must include columns date_local and prob_up. Found: {scores.columns.tolist()}")

    scores["date_local"] = _to_date_series(scores["date_local"])
    scores = scores.dropna(subset=["date_local"])
    scores = scores[["date_local", "prob_up"]].copy()
    scores["prob_up"] = pd.to_numeric(scores["prob_up"], errors="coerce")
    scores = scores.dropna(subset=["prob_up"])

    # Load truth from DuckDB
    conn = duckdb.connect(args.db, read_only=True)
    truth = conn.execute(
        """
        SELECT
          CAST(date_local AS DATE) AS date_local,
          CAST(direction AS INTEGER) AS truth_dir
        FROM daily_pattern_truth_v4
        WHERE direction IN (-1, 1)
        """
    ).df()
    conn.close()

    truth["date_local"] = _to_date_series(truth["date_local"])
    truth = truth.dropna(subset=["date_local"])

    # Filter last N years
    cutoff = (date.today() - timedelta(days=int(args.years * 365.25)))
    scores = scores[scores["date_local"] >= cutoff]
    truth = truth[truth["date_local"] >= cutoff]

    # Join
    df = scores.merge(truth, on="date_local", how="inner")

    print("================================================================================")
    print(f"V4 Directional Backtest (prob_up vs truth_dir) | last {args.years}y")
    print("================================================================================")
    print(f"CSV rows in window:   {len(scores)}")
    print(f"Truth rows in window: {len(truth)}")
    print(f"Rows matched:         {len(df)}")
    if len(df) == 0:
        print("❌ No matches after join. Likely a date mismatch or your truth table lacks those dates.")
        return 2
    if len(df) < args.min_matched:
        print(f"⚠️  Warning: matched rows < {args.min_matched}. Metrics may be noisy.")

    # Build y / p
    y = (df["truth_dir"].astype(int) == 1).astype(int).to_numpy()
    p = df["prob_up"].astype(float).clip(1e-9, 1 - 1e-9).to_numpy()
    pred = (p >= float(args.threshold)).astype(int)

    tp = int(((pred == 1) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())

    n = max(1, (tp + tn + fp + fn))
    acc = (tp + tn) / n

    tpr = tp / max(1, (tp + fn))
    tnr = tn / max(1, (tn + fp))
    bacc = (tpr + tnr) / 2 if ((tp + fn) > 0 and (tn + fp) > 0) else float("nan")

    brier = float(np.mean((p - y) ** 2))
    logloss = float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
    auc = compute_auc_rank(y, p)

    print()
    print(f"Pos (truth up): {int((y == 1).sum())} | Neg (truth down): {int((y == 0).sum())}")
    print()
    print(f"Threshold:          {args.threshold:.3f}")
    print(f"Accuracy:           {acc:.4f}")
    print(f"Balanced accuracy:  {bacc:.4f}  (TPR={tpr:.4f}, TNR={tnr:.4f})")
    print(f"Brier score:        {brier:.6f}")
    print(f"Log loss:           {logloss:.6f}")
    print(f"AUC (rank):         {auc:.4f}")
    print()
    print("Confusion matrix [tn fp; fn tp]:")
    print(np.array([[tn, fp], [fn, tp]]))

    if not args.no_calibration:
        df_cal = df.copy()
        df_cal["y"] = y
        cal = calibration_table(df_cal, bins=int(args.calib_bins))
        print("\nCalibration (quantile bins):")
        with pd.option_context("display.max_rows", 200, "display.width", 140):
            print(cal.to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
