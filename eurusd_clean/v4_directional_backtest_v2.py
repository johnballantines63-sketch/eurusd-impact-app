#!/usr/bin/env python3
"""
V4 Directional Backtest V2 (prob_up vs truth_dir)

Adds:
- Threshold sweep & auto-selection (train set)
- Optional logit clipping and temperature scaling
- Optional temporal split (train/test) by date
- Better diagnostics (AUC, Brier, logloss, calibration bins)

Usage examples:
  python3 v4_directional_backtest_v2.py --db data/warehouse.duckdb --csv outputs/v4_scores_panel_*.csv --years 3
  python3 v4_directional_backtest_v2.py --db data/warehouse.duckdb --csv outputs/v4_scores_panel_*.csv --years 3 --sweep-thresholds
  python3 v4_directional_backtest_v2.py --db data/warehouse.duckdb --csv outputs/v4_scores_panel_*.csv --years 3 --split-date 2024-01-01 --sweep-thresholds
  python3 v4_directional_backtest_v2.py --db data/warehouse.duckdb --csv outputs/v4_scores_panel_*.csv --years 3 --temp 1.8 --clip-logit 8 --sweep-thresholds
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import duckdb
import numpy as np
import pandas as pd

EPS = 1e-12


def _to_date_str(x) -> str:
    return pd.to_datetime(x).strftime("%Y-%m-%d")


def sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-z))


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, EPS, 1.0 - EPS)
    return np.log(p / (1.0 - p))


def apply_prob_transform(p: np.ndarray, clip_logit: Optional[float] = None, temp: float = 1.0) -> np.ndarray:
    l = logit(p)
    if clip_logit is not None:
        l = np.clip(l, -float(clip_logit), float(clip_logit))
    if temp <= 0:
        raise ValueError("--temp must be > 0")
    l = l / float(temp)
    return sigmoid(l)


def brier_score(y_true: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((p - y_true) ** 2))


def log_loss(y_true: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(p, EPS, 1.0 - EPS)
    return float(-np.mean(y_true * np.log(p) + (1 - y_true) * np.log(1 - p)))


def auc_rank(y_true: np.ndarray, p: np.ndarray) -> float:
    y = y_true.astype(int)
    pos = p[y == 1]
    neg = p[y == 0]
    n_pos, n_neg = len(pos), len(neg)
    if n_pos == 0 or n_neg == 0:
        return float("nan")

    order = np.argsort(p)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(p) + 1, dtype=float)

    sorted_p = p[order]
    i = 0
    while i < len(sorted_p):
        j = i + 1
        while j < len(sorted_p) and sorted_p[j] == sorted_p[i]:
            j += 1
        if j - i > 1:
            avg_rank = float(np.mean(ranks[order[i:j]]))
            ranks[order[i:j]] = avg_rank
        i = j

    r_pos = ranks[y == 1].sum()
    auc = (r_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def confusion(y_true: np.ndarray, p: np.ndarray, thr: float) -> Tuple[int, int, int, int]:
    yhat = (p >= thr).astype(int)
    tn = int(np.sum((y_true == 0) & (yhat == 0)))
    fp = int(np.sum((y_true == 0) & (yhat == 1)))
    fn = int(np.sum((y_true == 1) & (yhat == 0)))
    tp = int(np.sum((y_true == 1) & (yhat == 1)))
    return tn, fp, fn, tp


def metrics_at_threshold(y_true: np.ndarray, p: np.ndarray, thr: float) -> Dict[str, float]:
    tn, fp, fn, tp = confusion(y_true, p, thr)
    acc = (tp + tn) / max(1, (tp + tn + fp + fn))
    tpr = tp / max(1, (tp + fn))
    tnr = tn / max(1, (tn + fp))
    bacc = 0.5 * (tpr + tnr) if (tp + fn) > 0 and (tn + fp) > 0 else float("nan")
    return {
        "threshold": float(thr),
        "accuracy": float(acc),
        "balanced_accuracy": float(bacc),
        "tpr": float(tpr),
        "tnr": float(tnr),
        "tn": float(tn),
        "fp": float(fp),
        "fn": float(fn),
        "tp": float(tp),
        "youden_j": float(tpr + tnr - 1.0),
    }


def calibration_bins(y_true: np.ndarray, p: np.ndarray, n_bins: int = 6) -> pd.DataFrame:
    df = pd.DataFrame({"p": p, "y": y_true.astype(int)})
    try:
        df["bin"] = pd.qcut(df["p"], q=min(n_bins, max(2, df["p"].nunique())), duplicates="drop")
    except Exception:
        df["bin"] = pd.cut(df["p"], bins=n_bins)
    out = (
        df.groupby("bin", observed=True)
        .agg(n=("y", "size"), mean_p=("p", "mean"), frac_up=("y", "mean"))
        .reset_index()
        .sort_values("bin")
    )
    return out


@dataclass
class SplitData:
    train_idx: np.ndarray
    test_idx: np.ndarray
    split_date: Optional[str]


def temporal_split(date_strs: List[str], split_date: Optional[str]) -> SplitData:
    if split_date is None:
        idx = np.arange(len(date_strs))
        return SplitData(train_idx=idx, test_idx=idx, split_date=None)
    split_dt = pd.to_datetime(split_date)
    dates = pd.to_datetime(pd.Series(date_strs))
    train_idx = np.where(dates < split_dt)[0]
    test_idx = np.where(dates >= split_dt)[0]
    return SplitData(train_idx=train_idx, test_idx=test_idx, split_date=split_date)


def select_threshold(y_true: np.ndarray, p: np.ndarray, grid: np.ndarray, criterion: str) -> Tuple[float, pd.DataFrame]:
    rows = [metrics_at_threshold(y_true, p, float(thr)) for thr in grid]
    df = pd.DataFrame(rows)
    if criterion == "balanced_accuracy":
        df = df.sort_values(["balanced_accuracy", "youden_j", "accuracy"], ascending=False)
    elif criterion == "youden":
        df = df.sort_values(["youden_j", "balanced_accuracy", "accuracy"], ascending=False)
    elif criterion == "accuracy":
        df = df.sort_values(["accuracy", "balanced_accuracy", "youden_j"], ascending=False)
    else:
        raise ValueError(f"Unknown criterion: {criterion}")
    return float(df.iloc[0]["threshold"]), df


def load_scores_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = {"date_local", "prob_up"} - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}. Found: {df.columns.tolist()}")
    df["date_local"] = df["date_local"].apply(_to_date_str)
    df["prob_up"] = pd.to_numeric(df["prob_up"], errors="coerce")
    df = df.dropna(subset=["prob_up"]).copy()
    return df


def load_truth_duckdb(db_path: Path) -> pd.DataFrame:
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        truth = conn.execute(
            """SELECT date_local, direction AS truth_dir
                 FROM daily_pattern_truth_v4"""
        ).df()
    finally:
        conn.close()
    truth["date_local"] = truth["date_local"].apply(_to_date_str)
    truth = truth[truth["truth_dir"].isin([1, -1])].copy()
    truth["y"] = (truth["truth_dir"] == 1).astype(int)
    return truth[["date_local", "truth_dir", "y"]]


def apply_year_window(df: pd.DataFrame, years: float) -> pd.DataFrame:
    if years <= 0:
        return df
    max_date = pd.to_datetime(df["date_local"]).max()
    cutoff = max_date - pd.Timedelta(days=float(years) * 365.0)
    return df[pd.to_datetime(df["date_local"]) >= cutoff].copy()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, type=str)
    ap.add_argument("--csv", required=True, type=str)
    ap.add_argument("--years", default=3.0, type=float)
    ap.add_argument("--threshold", default=0.5, type=float)
    ap.add_argument("--sweep-thresholds", action="store_true")
    ap.add_argument("--criterion", default="balanced_accuracy", choices=["balanced_accuracy", "youden", "accuracy"])
    ap.add_argument("--split-date", default=None, type=str, help="YYYY-MM-DD (train < split, test >= split)")
    ap.add_argument("--temp", default=1.0, type=float)
    ap.add_argument("--clip-logit", default=None, type=float)
    ap.add_argument("--bins", default=6, type=int)
    ap.add_argument("--print-top", default=10, type=int)
    args = ap.parse_args()

    db_path = Path(args.db)
    csv_path = Path(args.csv)

    scores = apply_year_window(load_scores_csv(csv_path), args.years)
    truth = apply_year_window(load_truth_duckdb(db_path), args.years)

    df = scores.merge(truth, on="date_local", how="inner").sort_values("date_local").reset_index(drop=True)
    if df.empty:
        raise SystemExit("No matched rows between CSV and daily_pattern_truth_v4 in the selected window.")

    p_raw = df["prob_up"].to_numpy(float)
    p = apply_prob_transform(p_raw, clip_logit=args.clip_logit, temp=args.temp)
    y = df["y"].to_numpy(int)

    split = temporal_split(df["date_local"].tolist(), args.split_date)
    train_idx, test_idx = split.train_idx, split.test_idx
    if len(test_idx) == 0:
        raise SystemExit(f"Split produced empty TEST set (split-date={args.split_date}).")

    thr = float(args.threshold)
    sweep_df = None
    if args.sweep_thresholds:
        if len(train_idx) == 0:
            raise SystemExit("Split produced empty TRAIN set; cannot sweep thresholds.")
        grid = np.linspace(0.05, 0.95, 181)
        thr, sweep_df = select_threshold(y[train_idx], p[train_idx], grid, args.criterion)

    y_test = y[test_idx]
    p_test = p[test_idx]

    tn, fp, fn, tp = confusion(y_test, p_test, thr)
    acc = (tp + tn) / max(1, (tp + tn + fp + fn))
    tpr = tp / max(1, (tp + fn))
    tnr = tn / max(1, (tn + fp))
    bacc = 0.5 * (tpr + tnr) if (tp + fn) > 0 and (tn + fp) > 0 else float("nan")

    brier = brier_score(y_test, p_test)
    ll = log_loss(y_test, p_test)
    auc = auc_rank(y_test, p_test)

    window_str = f"last {args.years:.1f}y"
    split_str = f" | split @ {args.split_date} (train <, test >=)" if args.split_date else ""
    transform = []
    if args.clip_logit is not None:
        transform.append(f"clip_logit={args.clip_logit:g}")
    if args.temp != 1.0:
        transform.append(f"temp={args.temp:g}")
    transform_str = (" | " + ", ".join(transform)) if transform else ""

    print("=" * 80)
    print(f"V4 Directional Backtest V2 (prob_up vs truth_dir) | {window_str}{split_str}{transform_str}")
    print("=" * 80)
    print(f"Rows matched: {len(df)}")
    if args.split_date:
        print(f"Train rows:   {len(train_idx)} | Test rows: {len(test_idx)}")
    print(f"Pos (up): {int((y_test==1).sum())} | Neg (down): {int((y_test==0).sum())}")
    print()
    if args.sweep_thresholds and sweep_df is not None:
        best = sweep_df.iloc[0].to_dict()
        print(f"Threshold (selected on TRAIN via {args.criterion}): {thr:.3f}")
        print(f"  TRAIN best: bacc={best.get('balanced_accuracy', float('nan')):.4f} (TPR={best.get('tpr', float('nan')):.4f}, TNR={best.get('tnr', float('nan')):.4f}), acc={best.get('accuracy', float('nan')):.4f}")
    else:
        print(f"Threshold: {thr:.3f}")
    print(f"Accuracy (TEST):          {acc:.4f}")
    print(f"Balanced accuracy (TEST): {bacc:.4f} (TPR={tpr:.4f}, TNR={tnr:.4f})")
    print(f"Brier score (TEST):       {brier:.6f}")
    print(f"Log loss (TEST):          {ll:.6f}")
    print(f"AUC (rank, TEST):         {auc:.4f}")
    print()
    print("Confusion matrix (TEST) [tn fp; fn tp]:")
    print(np.array([[tn, fp],[fn, tp]]))
    print()

    cal = calibration_bins(y_test, p_test, n_bins=max(2, int(args.bins)))
    print("Calibration (quantile bins, TEST):")
    print(cal.to_string(index=False))
    print()

    if args.print_top and args.print_top > 0:
        df_test = df.iloc[test_idx].copy()
        df_test["prob_up_tx"] = p_test
        df_test["conf"] = np.abs(df_test["prob_up_tx"] - 0.5)
        df_test = df_test.sort_values("conf", ascending=False).head(int(args.print_top))
        cols = [c for c in ["date_local","truth_dir","prob_up","prob_up_tx","kernel_size","kernel_releases","score_0_100"] if c in df_test.columns]
        print(f"Top {int(args.print_top)} most confident (TEST):")
        print(df_test[cols].to_string(index=False))
        print()

    if args.sweep_thresholds and sweep_df is not None:
        print("Top 10 thresholds on TRAIN:")
        print(sweep_df.head(10)[["threshold","balanced_accuracy","tpr","tnr","accuracy","youden_j"]].to_string(index=False))
        print()


if __name__ == "__main__":
    main()
