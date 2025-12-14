#!/usr/bin/env python3
"""
Step 4 audit runner for V4 scoring.

Runs the end-to-end pipeline for a grid of:
- after-min windows
- split dates

For each (after_min, split_date):
1) Build event scores + fit kernel weights (WRITE mode)
2) Score ALL dates in daily_pattern_truth_v4 (READONLY mode) -> CSV
3) Run v4_directional_backtest_v3.py:
   - sweep temps on TRAIN (criterion: logloss|brier)
   - sweep thresholds on TRAIN (criterion: youden|balanced_accuracy|accuracy)
   - report metrics on TEST

Outputs a summary CSV with key metrics.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple


def run_cmd(cmd: List[str], cwd: Optional[Path] = None) -> str:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    out = p.stdout or ""
    if p.returncode != 0:
        raise RuntimeError(
            f"Command failed ({p.returncode}): {' '.join(shlex.quote(c) for c in cmd)}\n\n{out}"
        )
    return out


def parse_grid(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def discover_dates_from_truth(python_bin: str, db: Path) -> List[str]:
    """
    Return all distinct date_local from daily_pattern_truth_v4 ordered.
    Uses a tiny inline python snippet to avoid tool deps.
    """
    snippet = r"""
import duckdb
conn = duckdb.connect(r'{db}', read_only=True)
df = conn.execute("SELECT DISTINCT date_local FROM daily_pattern_truth_v4 ORDER BY date_local").df()
conn.close()
for d in df['date_local'].astype(str).tolist():
    print(d)
""".format(db=str(db))
    out = run_cmd([python_bin, "-c", snippet])
    dates = [ln.strip() for ln in out.splitlines() if ln.strip()]
    # Defensive: keep YYYY-MM-DD only
    dates = [d for d in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)]
    return dates


def score_dates_csv(
    python_bin: str,
    build_script: Path,
    db: Path,
    years: int,
    after_min: int,
    dates_csv: str,
    out_dir: Path,
) -> Path:
    """
    Runs build_v4_scoring.py --score-dates in READONLY mode for a list of dates.
    Returns the newest v4_scores_panel_*.csv produced in out_dir.
    """
    # Ensure out_dir exists
    out_dir.mkdir(parents=True, exist_ok=True)

    before = set(out_dir.glob("v4_scores_panel_*.csv"))

    run_cmd(
        [
            python_bin,
            str(build_script),
            "--db",
            str(db),
            "--years",
            str(int(years)),
            "--after-min",
            str(int(after_min)),
            "--score-dates",
            "--readonly",
            "--dates",
            dates_csv,
        ]
    )

    after = set(out_dir.glob("v4_scores_panel_*.csv"))
    new_files = sorted(list(after - before), key=lambda p: p.stat().st_mtime)
    if not new_files:
        # fallback: pick newest
        candidates = sorted(list(after), key=lambda p: p.stat().st_mtime)
        if not candidates:
            raise RuntimeError(f"No v4_scores_panel_*.csv found in {out_dir}")
        return candidates[-1]
    return new_files[-1]


def build_event_scores_and_weights(
    python_bin: str,
    build_script: Path,
    db: Path,
    years: int,
    after_min: int,
) -> None:
    """
    Runs:
      --build-event-scores
      --fit-kernel-weights
    in WRITE mode, for the given years/after_min.
    """
    run_cmd(
        [
            python_bin,
            str(build_script),
            "--db",
            str(db),
            "--years",
            str(int(years)),
            "--after-min",
            str(int(after_min)),
            "--build-event-scores",
        ]
    )
    run_cmd(
        [
            python_bin,
            str(build_script),
            "--db",
            str(db),
            "--years",
            str(int(years)),
            "--after-min",
            str(int(after_min)),
            "--fit-kernel-weights",
        ]
    )


@dataclass
class BacktestResult:
    rows_matched: int
    train_rows: int
    test_rows: int
    split_date: str
    years: int
    after_min: int
    chosen_temp: Optional[float]
    chosen_threshold: Optional[float]
    test_accuracy: Optional[float]
    test_bacc: Optional[float]
    test_auc: Optional[float]
    test_logloss: Optional[float]
    test_brier: Optional[float]
    raw_output_path: Optional[str]


def parse_backtest_output(txt: str) -> dict:
    """
    Parse key lines from v4_directional_backtest_v3.py output.
    """
    out = {}
    # Rows matched: 658
    m = re.search(r"Rows matched:\s+(\d+)", txt)
    if m:
        out["rows_matched"] = int(m.group(1))
    # Train rows:   209 | Test rows: 449
    m = re.search(r"Train rows:\s+(\d+)\s+\|\s+Test rows:\s+(\d+)", txt)
    if m:
        out["train_rows"] = int(m.group(1))
        out["test_rows"] = int(m.group(2))
    # Temp (selected on TRAIN via logloss): 0.6
    m = re.search(r"Temp \(selected on TRAIN via [^)]+\):\s*([0-9.]+)", txt)
    if m:
        out["chosen_temp"] = float(m.group(1))
    # Threshold (selected on TRAIN via youden): 0.475
    m = re.search(r"Threshold \(selected on TRAIN via [^)]+\):\s*([0-9.]+)", txt)
    if m:
        out["chosen_threshold"] = float(m.group(1))
    # Accuracy (TEST):          0.6971
    m = re.search(r"Accuracy \(TEST\):\s+([0-9.]+)", txt)
    if m:
        out["test_accuracy"] = float(m.group(1))
    # Balanced accuracy (TEST): 0.6972
    m = re.search(r"Balanced accuracy \(TEST\):\s+([0-9.]+)", txt)
    if m:
        out["test_bacc"] = float(m.group(1))
    # AUC (rank, TEST):         0.7750
    m = re.search(r"AUC \(rank, TEST\):\s+([0-9.]+)", txt)
    if m:
        out["test_auc"] = float(m.group(1))
    # Log loss (TEST):          0.570600
    m = re.search(r"Log loss \(TEST\):\s+([0-9.]+)", txt)
    if m:
        out["test_logloss"] = float(m.group(1))
    # Brier score (TEST):       0.198267
    m = re.search(r"Brier score \(TEST\):\s+([0-9.]+)", txt)
    if m:
        out["test_brier"] = float(m.group(1))
    return out


def run_backtest(
    python_bin: str,
    backtest_script: Path,
    db: Path,
    csv_path: Path,
    years: int,
    split_date: str,
    sweep_temps: bool,
    temp_criterion: str,
    temp: Optional[float],
    clip_logit: Optional[float],
    sweep_thresholds: bool,
    thr_criterion: str,
    save_logs_dir: Optional[Path],
    after_min: int,
) -> BacktestResult:
    cmd = [
        python_bin,
        str(backtest_script),
        "--db",
        str(db),
        "--csv",
        str(csv_path),
        "--years",
        str(int(years)),
        "--split-date",
        split_date,
        "--criterion",
        thr_criterion,
    ]
    if clip_logit is not None:
        cmd += ["--clip-logit", str(float(clip_logit))]

    if sweep_temps:
        cmd += ["--sweep-temps", "--temp-criterion", temp_criterion]
    elif temp is not None:
        cmd += ["--temp", str(float(temp))]

    if sweep_thresholds:
        cmd += ["--sweep-thresholds"]

    txt = run_cmd(cmd)
    parsed = parse_backtest_output(txt)

    raw_path = None
    if save_logs_dir is not None:
        save_logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        raw_path = str(save_logs_dir / f"backtest_after{after_min}_split{split_date}_{stamp}.log")
        Path(raw_path).write_text(txt, encoding="utf-8")

    return BacktestResult(
        rows_matched=parsed.get("rows_matched", 0),
        train_rows=parsed.get("train_rows", 0),
        test_rows=parsed.get("test_rows", 0),
        split_date=split_date,
        years=int(years),
        after_min=int(after_min),
        chosen_temp=parsed.get("chosen_temp"),
        chosen_threshold=parsed.get("chosen_threshold"),
        test_accuracy=parsed.get("test_accuracy"),
        test_bacc=parsed.get("test_bacc"),
        test_auc=parsed.get("test_auc"),
        test_logloss=parsed.get("test_logloss"),
        test_brier=parsed.get("test_brier"),
        raw_output_path=raw_path,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, type=str, help="Path to DuckDB")
    ap.add_argument("--build", required=True, type=str, help="Path to research/build_v4_scoring.py")
    ap.add_argument("--backtest", required=True, type=str, help="Path to v4_directional_backtest_v3.py")
    ap.add_argument("--python", default="python3", type=str, help="Python executable (default: python3)")
    ap.add_argument("--years", default=3, type=int, help="Window years (int)")
    ap.add_argument("--after-grid", required=True, type=str, help="Comma grid for after-min, e.g. 60,120,240")
    ap.add_argument("--split-grid", required=True, type=str, help="Comma grid for split dates YYYY-MM-DD,...")
    ap.add_argument("--clip-logit", default=None, type=float, help="clip_logit for backtest calibration")
    ap.add_argument("--sweep-temps", action="store_true", help="Select temp on TRAIN (grid)")
    ap.add_argument("--temp-criterion", default="logloss", choices=["logloss", "brier"], help="Temp selection metric (TRAIN)")
    ap.add_argument("--temp", default=None, type=float, help="Fixed temp (if not sweeping)")
    ap.add_argument("--sweep-thresholds", action="store_true", help="Select threshold on TRAIN (grid)")
    ap.add_argument("--thr-criterion", default="youden", choices=["youden", "balanced_accuracy", "accuracy"], help="Threshold selection criterion (TRAIN)")
    ap.add_argument("--out-dir", default="outputs", type=str, help="Output dir (default: outputs)")
    ap.add_argument("--save-logs", action="store_true", help="Save raw backtest logs into outputs/")
    args = ap.parse_args()

    db = Path(args.db).expanduser().resolve()
    build_script = Path(args.build).expanduser().resolve()
    backtest_script = Path(args.backtest).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    logs_dir = (out_dir / "audit_logs") if args.save_logs else None

    after_grid = [int(x) for x in parse_grid(args.after_grid)]
    split_grid = parse_grid(args.split_grid)

    # Dates to score: from truth table (so scoring/backtest are aligned)
    dates = discover_dates_from_truth(args.python, db)
    if not dates:
        raise RuntimeError("No dates found in daily_pattern_truth_v4.")
    dates_csv = ",".join(dates)

    summary_rows: List[dict] = []

    for after_min in after_grid:
        print(f"\n=== PIPELINE after-min={after_min} ===")

        # Step A: rebuild empirical scores + weights for this after_min
        build_event_scores_and_weights(
            python_bin=args.python,
            build_script=build_script,
            db=db,
            years=args.years,
            after_min=after_min,
        )

        # Step B: score dates -> a panel csv
        scored_csv = score_dates_csv(
            python_bin=args.python,
            build_script=build_script,
            db=db,
            years=args.years,
            after_min=after_min,
            dates_csv=dates_csv,
            out_dir=out_dir,
        )
        print(f"Scored panel: {scored_csv}")

        # Step C: run backtest per split date
        for split_date in split_grid:
            print(f"--- Backtest split={split_date} ---")
            res = run_backtest(
                python_bin=args.python,
                backtest_script=backtest_script,
                db=db,
                csv_path=scored_csv,
                years=args.years,
                split_date=split_date,
                sweep_temps=args.sweep_temps,
                temp_criterion=args.temp_criterion,
                temp=args.temp,
                clip_logit=args.clip_logit,
                sweep_thresholds=args.sweep_thresholds,
                thr_criterion=args.thr_criterion,
                save_logs_dir=logs_dir,
                after_min=after_min,
            )
            summary_rows.append(
                {
                    "after_min": res.after_min,
                    "years": res.years,
                    "split_date": res.split_date,
                    "rows_matched": res.rows_matched,
                    "train_rows": res.train_rows,
                    "test_rows": res.test_rows,
                    "chosen_temp": res.chosen_temp,
                    "chosen_threshold": res.chosen_threshold,
                    "test_accuracy": res.test_accuracy,
                    "test_bacc": res.test_bacc,
                    "test_auc": res.test_auc,
                    "test_logloss": res.test_logloss,
                    "test_brier": res.test_brier,
                    "panel_csv": str(scored_csv),
                    "raw_log": res.raw_output_path,
                }
            )

    # Write summary
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary_path = out_dir / f"audit_step4_summary_{stamp}.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)

    print("\n✅ Summary written:", summary_path)


if __name__ == "__main__":
    main()
