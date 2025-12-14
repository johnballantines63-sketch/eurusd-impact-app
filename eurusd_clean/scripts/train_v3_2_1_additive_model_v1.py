#!/usr/bin/env python3
"""
Train V3.2.1 Additive Model and Export Artifact
===============================================

Train a Ridge model on the full training set (or a specific cutoff) and export
the frozen artifact (intercept + coefs) for production use.

Usage:
  python3 scripts/train_v3_2_1_additive_model_v1.py --cutoff 2024-07-01
  python3 scripts/train_v3_2_1_additive_model_v1.py --cutoff 2024-07-01 --output models/my_model.json
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import duckdb
import pandas as pd
import numpy as np

# Try sklearn, fallback to numpy
try:
    from sklearn.linear_model import Ridge
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

DATASET_VIEW = "daily_pred_score_v3_2_dataset_v1"
DEFAULT_CUTOFF = "2024-07-01"  # Use data up to this date for training

# Fixed feature order (MUST match apply script)
FEATURES: List[str] = [
    "log1p_score_v2_1",
    "dow",
    "is_mon",
    "is_fri",
    "day_of_month",
    "month",
    "is_month_start",
    "is_month_end",
    "week_of_month",
    "vol_mean_20_lag1",
    "vol_std_20_lag1",
    "vol_mean_60_lag1",
    "vol_std_60_lag1",
    "vol_z_20_lag1",
    "vol_z_60_lag1",
    "regime_high_60_lag1",
    "regime_low_60_lag1",
    "log1p_n_us_events_day",
]


def ridge_fit_numpy(X_train, y_train, alpha=1.0):
    """Ridge regression via solution fermée (numpy)."""
    n, p = X_train.shape
    X_aug = np.column_stack([np.ones(n), X_train])
    I_aug = np.eye(p + 1)
    I_aug[0, 0] = 0  # Don't regularize intercept
    beta = np.linalg.solve(X_aug.T @ X_aug + alpha * I_aug, X_aug.T @ y_train)
    intercept = beta[0]
    coef = beta[1:]
    return intercept, coef


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


def build_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """Build feature matrix matching apply script logic."""
    df_feat = df.copy()

    # Calendar types (ensure numeric)
    cal_cols = ["dow", "is_mon", "is_fri", "day_of_month", "month", "is_month_start", "is_month_end", "week_of_month"]
    for c in cal_cols:
        df_feat[c] = pd.to_numeric(df_feat[c], errors="coerce")

    # Regime numeric cols -> fillna(0)
    regime_cols = [
        "vol_mean_20_lag1", "vol_std_20_lag1", "vol_mean_60_lag1", "vol_std_60_lag1",
        "vol_z_20_lag1", "vol_z_60_lag1", "regime_high_60_lag1", "regime_low_60_lag1"
    ]
    for c in regime_cols:
        df_feat[c] = pd.to_numeric(df_feat[c], errors="coerce").fillna(0.0)

    # score/log transforms
    df_feat["log1p_score_v2_1"] = np.log1p(pd.to_numeric(df_feat["score_v2_1"], errors="coerce"))
    df_feat["log1p_n_us_events_day"] = np.log1p(pd.to_numeric(df_feat["n_us_events_day"], errors="coerce").fillna(0.0))

    # Ensure no NaNs in final feature columns
    for f in FEATURES:
        if f not in df_feat.columns:
            raise KeyError(f"Feature column missing after construction: {f}")
        df_feat[f] = pd.to_numeric(df_feat[f], errors="coerce").fillna(0.0)

    X = df_feat[FEATURES].astype(float).to_numpy()
    return X


def main():
    parser = argparse.ArgumentParser(description="Train V3.2.1 additive Ridge model and export artifact.")
    parser.add_argument("--cutoff", type=str, default=DEFAULT_CUTOFF,
                       help=f"Training cutoff date YYYY-MM-DD (default: {DEFAULT_CUTOFF})")
    parser.add_argument("--alpha", type=float, default=0.1,
                       help="Ridge alpha (default: 0.1)")
    parser.add_argument("--output", type=str, default=None,
                       help="Output artifact path (default: models/v3_2_1_additive_ridge_alpha0_1.json)")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)

    cutoff_date = pd.to_datetime(args.cutoff).date()
    output_path = Path(args.output) if args.output else PROJECT_ROOT / "models" / "v3_2_1_additive_ridge_alpha0_1.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 110)
    print("TRAIN MODEL: V3.2.1 ADDITIVE (Ridge alpha=0.1)")
    print("=" * 110)
    print(f"DB: {DB_PATH}")
    print(f"Dataset view: {DATASET_VIEW}")
    print(f"Training cutoff: {args.cutoff}")
    print(f"Ridge alpha: {args.alpha}")
    print(f"Output artifact: {output_path}")
    print(f"Sklearn available: {HAS_SKLEARN}")
    print()

    # Connect DuckDB
    try:
        conn = connect_duckdb_with_retry(DB_PATH, read_only=True)
    except Exception as e:
        print(f"❌ DuckDB connect failed: {e}")
        sys.exit(1)

    try:
        # Load training data (all data <= cutoff)
        df = conn.execute(f"""
            SELECT *
            FROM {DATASET_VIEW}
            WHERE date <= DATE '{args.cutoff}'
            ORDER BY date
        """).df()
        df['date'] = pd.to_datetime(df['date']).dt.date

        if df.empty:
            print(f"❌ No training data found for cutoff {args.cutoff}")
            sys.exit(1)

        print(f"📊 Training data: {len(df)} rows")
        print(f"   Date range: {df['date'].min()} → {df['date'].max()}")
        print()

        # Build features and target
        X = build_feature_matrix(df)
        y = np.log1p(df['target_vol_pips'].values)

        print(f"📊 Features shape: {X.shape}")
        print(f"   Target shape: {y.shape}")
        print()

        # Train Ridge
        if HAS_SKLEARN:
            print("🔧 Training with sklearn.Ridge...")
            model = Ridge(alpha=args.alpha)
            model.fit(X, y)
            intercept = float(model.intercept_)
            coef = model.coef_.tolist()
        else:
            print("🔧 Training with numpy (closed-form)...")
            intercept, coef = ridge_fit_numpy(X, y, alpha=args.alpha)
            coef = coef.tolist()

        # Validate feature count
        if len(coef) != len(FEATURES):
            print(f"❌ Mismatch: {len(coef)} coefs vs {len(FEATURES)} features")
            sys.exit(1)

        # Create artifact
        artifact = {
            "version": "V3.2.1",
            "model_type": "ridge",
            "alpha": float(args.alpha),
            "intercept": float(intercept),
            "coef": [float(c) for c in coef],
            "features": FEATURES,
            "training_cutoff": args.cutoff,
            "n_train": len(df),
            "date_range": {
                "min": str(df['date'].min()),
                "max": str(df['date'].max()),
            },
        }

        # Save artifact
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)

        print(f"✅ Model artifact saved to: {output_path}")
        print()
        print("📊 Model summary:")
        print(f"   Intercept: {intercept:.6f}")
        print(f"   Coefs: {len(coef)} features")
        print(f"   Coef range: [{min(coef):.6f}, {max(coef):.6f}]")
        print()
        print("=" * 110)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

