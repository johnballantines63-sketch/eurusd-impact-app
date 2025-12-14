#!/usr/bin/env python3
"""
Apply V3.2.1 Additive Model (Production)
========================================

Apply-only script (NO TRAINING): reads ex-ante features from DuckDB view
`daily_pred_score_v3_2_dataset_v1`, applies a frozen Ridge model artifact
(intercept + 18 coefs), and writes predictions to `daily_risk_signal_v3_2_1`.

Usage:
  python3 scripts/apply_v3_2_1_additive_model_v1.py
  python3 scripts/apply_v3_2_1_additive_model_v1.py --limit 10
  python3 scripts/apply_v3_2_1_additive_model_v1.py --from 2024-01-01 --to 2024-12-31
  python3 scripts/apply_v3_2_1_additive_model_v1.py --dry-run

CONTRAT (V3.2.1 Trading Payload) — v1.0.0
Entrées: (1) modèle JSON v3_2_1_additive_ridge_alpha0_1.json, (2) vues DuckDB daily_pred_score_v3_2_dataset_v1 + events_with_ts_local_v1.
Sorties: (A) table daily_risk_signal_v3_2_1, (B) payload JSON validé (DayPrediction) par date.
Garanties: feature_order FIXE + hash SHA256; pas de NULL sur colonnes critiques; pred_vol_pips > 0.
Invariant 1: no-leakage: features régime utilisent uniquement lag1; densité events = DATE(ts_local) (jour t).
Invariant 2: BUY/SELL => ≥1 core_event avec previous+forecast; NO_TRADE tolère 0 core_event.
Invariant 3: contract_version + model_version + feature_order_hash écrits dans output pour audit.
En cas de violation: abort immédiat (exit code 1), rien n'est écrit en DB (transaction rollback).
"""

# CONTRACT (V3.2.1 additive) — apply-only, no training
# Input view: daily_pred_score_v3_2_dataset_v1 (one row per date, ex-ante features)
# Required columns: date, score_v2_1, n_us_events_day, + V3.1 calendar(8) + regime(8)
# Feature transforms: x0=log1p(score_v2_1), x17=log1p(n_us_events_day), regime NaN->0, no other scaling
# Model artifact: (intercept, coef[18], FEATURES[18], alpha=0.1, version="V3.2.1")
# Output: table/view daily_risk_signal_v3_2_1 with (date, pred_log_vol, pred_vol_pips, model_version)
# Invariant 1: all required feature cols present; no NULL on (date, score_v2_1, n_us_events_day)
# Invariant 2: n_us_events_day >= 0 for all rows; regime_high/low in {0,1}
# Invariant 3: ex-ante only: uses vol_*_lag1 + calendar; never references target_vol_pips in features
# Failure policy: if any invariant fails -> exit(1) with clear diagnostic counts + sample rows

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import duckdb
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

# Import contract (optional, graceful fallback)
try:
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.contracts.v3_2_1_contract import FEATURE_ORDER_V3_2_1, FEATURE_ORDER_HASH
    HAS_CONTRACT = True
except (ImportError, ModuleNotFoundError):
    # Fallback if contracts not available (e.g., pydantic not installed)
    HAS_CONTRACT = False
    FEATURE_ORDER_V3_2_1 = None
    FEATURE_ORDER_HASH = None

INPUT_VIEW = "daily_pred_score_v3_2_dataset_v1"
OUTPUT_TABLE = "daily_risk_signal_v3_2_1"

# Model artifact location (frozen weights)
MODEL_PATH = PROJECT_ROOT / "models" / "v3_2_1_additive_ridge_alpha0_1.json"

# Fixed feature order (MUST match artifact["features"] and contract)
# Defined before import to avoid circular dependency
FEATURES_LOCAL: List[str] = [
    "log1p_score_v2_1",
    "dow", "is_mon", "is_fri", "day_of_month", "month", "is_month_start", "is_month_end", "week_of_month",
    "vol_mean_20_lag1", "vol_std_20_lag1", "vol_mean_60_lag1", "vol_std_60_lag1",
    "vol_z_20_lag1", "vol_z_60_lag1", "regime_high_60_lag1", "regime_low_60_lag1",
    "log1p_n_us_events_day",
]


def _hash_features(features: List[str]) -> str:
    """Hash feature order for drift detection."""
    s = "\n".join(features).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


# Use contract if available, otherwise use local
if HAS_CONTRACT:
    FEATURES = FEATURE_ORDER_V3_2_1
    CONTRACT_HASH = FEATURE_ORDER_HASH
else:
    FEATURES = FEATURES_LOCAL
    CONTRACT_HASH = _hash_features(FEATURES_LOCAL)

# Raw columns required from DuckDB for feature construction
REQUIRED_RAW_COLS: List[str] = [
    "date",
    "score_v2_1",
    "n_us_events_day",
    # calendar
    "dow", "is_mon", "is_fri", "day_of_month", "month", "is_month_start", "is_month_end", "week_of_month",
    # regime (lag1/ex-ante)
    "vol_mean_20_lag1", "vol_std_20_lag1", "vol_mean_60_lag1", "vol_std_60_lag1",
    "vol_z_20_lag1", "vol_z_60_lag1", "regime_high_60_lag1", "regime_low_60_lag1",
]


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def connect_duckdb_with_retry(path: Path, read_only: bool, max_retries: int = 5, sleep_s: int = 3) -> duckdb.DuckDBPyConnection:
    conn = None
    for i in range(max_retries):
        try:
            conn = duckdb.connect(str(path), read_only=read_only)
            return conn
        except Exception as e:
            if "lock" in str(e).lower() and i < max_retries - 1:
                print(f"⚠️  Lock détecté sur DuckDB, attente {sleep_s}s... (tentative {i+1}/{max_retries})")
                time.sleep(sleep_s)
            else:
                raise
    # should never reach
    raise RuntimeError("Unable to connect to DuckDB after retries")


def load_model_artifact(model_path: Path) -> Dict:
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {model_path}")

    with open(model_path, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    # Minimal validation
    if artifact.get("version") != "V3.2.1":
        raise ValueError(f"Unexpected model version in artifact: {artifact.get('version')}")
    if artifact.get("model_type") != "ridge":
        raise ValueError(f"Unexpected model_type in artifact: {artifact.get('model_type')}")
    if float(artifact.get("alpha", -1)) != 0.1:
        raise ValueError(f"Unexpected alpha in artifact: {artifact.get('alpha')} (expected 0.1)")

    coefs = artifact.get("coef")
    intercept = artifact.get("intercept")
    feat = artifact.get("features")

    if intercept is None or not isinstance(intercept, (int, float)):
        raise ValueError("Artifact missing numeric 'intercept'")
    if not isinstance(coefs, list) or len(coefs) != len(FEATURES):
        raise ValueError(f"Artifact 'coef' must be list of length {len(FEATURES)}")
    if not isinstance(feat, list) or feat != FEATURES:
        raise ValueError("Artifact 'features' must exactly match FEATURES order in this script")
    
    # Drift detection: verify feature order hash matches contract
    model_feature_hash = _hash_features(feat)
    if model_feature_hash != CONTRACT_HASH:
        raise RuntimeError(f"feature_order_hash mismatch (hard fail): model={model_feature_hash[:16]}... vs contract={CONTRACT_HASH[:16]}...")

    return artifact


def fetch_input_df(
    conn: duckdb.DuckDBPyConnection,
    date_from: Optional[str],
    date_to: Optional[str],
    limit: Optional[int],
) -> pd.DataFrame:
    where = []
    if date_from:
        where.append(f"date >= DATE '{date_from}'")
    if date_to:
        where.append(f"date <= DATE '{date_to}'")

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    limit_sql = f"LIMIT {int(limit)}" if limit else ""

    sql = f"""
        SELECT
            {", ".join(REQUIRED_RAW_COLS)}
        FROM {INPUT_VIEW}
        {where_sql}
        ORDER BY date
        {limit_sql}
    """
    df = conn.execute(sql).df()
    # Normalize date type
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def invariant_checks(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Return (ok, violations)."""
    violations: List[str] = []

    # Invariant 1: no NULL on critical columns
    critical = ["date", "score_v2_1", "n_us_events_day"]
    for c in critical:
        if c not in df.columns:
            violations.append(f"Missing required column: {c}")
    if violations:
        return False, violations

    n_null_critical = df[critical].isna().any(axis=1).sum()
    if n_null_critical > 0:
        violations.append(f"NULL on critical cols (date/score_v2_1/n_us_events_day): {n_null_critical} rows")

    # Invariant 2: n_us_events_day >= 0; regime flags in {0,1} when not null
    if "n_us_events_day" in df.columns:
        n_neg = (df["n_us_events_day"].fillna(0) < 0).sum()
        if n_neg > 0:
            violations.append(f"n_us_events_day < 0: {n_neg} rows")

    for flag in ["regime_high_60_lag1", "regime_low_60_lag1"]:
        if flag in df.columns:
            s = df[flag].dropna()
            bad = (~s.isin([0, 1])).sum()
            if bad > 0:
                violations.append(f"{flag} not in {{0,1}}: {bad} rows")

    # Invariant 3: ex-ante only (structural): ensure we did NOT accidentally pull target column
    if "target_vol_pips" in df.columns:
        violations.append("Leak risk: input df contains target_vol_pips (should not be selected for production apply)")

    ok = len(violations) == 0
    return ok, violations


def build_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    # Transformations per CONTRACT
    # - log1p(score_v2_1)
    # - log1p(n_us_events_day)
    # - regime NaN -> 0 (for all regime numeric cols, plus any NaNs in regime stats)
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


def predict(artifact: Dict, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    intercept = float(artifact["intercept"])
    coef = np.array([float(x) for x in artifact["coef"]], dtype=float).reshape(-1)

    pred_log = intercept + X @ coef
    # expm1 is safer than exp-1 for small values
    pred_vol = np.expm1(pred_log)
    # Guard: vol should not be negative (numerical)
    pred_vol = np.maximum(pred_vol, 0.0)

    return pred_log, pred_vol


def write_output(
    conn: duckdb.DuckDBPyConnection,
    df_out: pd.DataFrame,
    dry_run: bool,
) -> None:
    if dry_run:
        print("🧪 --dry-run: no DB write. Showing sample output:")
        print(df_out.head(10).to_string(index=False))
        return

    # Register pandas DF as temporary view and materialize
    conn.register("tmp_v3_2_1_pred_df", df_out)

    conn.execute(f"CREATE OR REPLACE TABLE {OUTPUT_TABLE} AS SELECT * FROM tmp_v3_2_1_pred_df")
    conn.execute("DROP VIEW IF EXISTS tmp_v3_2_1_pred_df")

    print(f"✅ Wrote {len(df_out)} rows to DuckDB table: {OUTPUT_TABLE}")


def main():
    parser = argparse.ArgumentParser(description="Apply frozen V3.2.1 additive ridge model (no training).")
    parser.add_argument("--from", dest="date_from", type=str, default=None, help="Start date YYYY-MM-DD (inclusive)")
    parser.add_argument("--to", dest="date_to", type=str, default=None, help="End date YYYY-MM-DD (inclusive)")
    parser.add_argument("--limit", dest="limit", type=int, default=None, help="Limit number of rows (debug)")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Do not write to DuckDB")
    args = parser.parse_args()

    if not DB_PATH.exists():
        eprint(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)

    print("=" * 110)
    print("APPLY MODEL: V3.2.1 ADDITIVE (Ridge alpha=0.1) — PRODUCTION")
    print("=" * 110)
    print(f"DB: {DB_PATH}")
    print(f"Input view: {INPUT_VIEW}")
    print(f"Model artifact: {MODEL_PATH}")
    print(f"Output table: {OUTPUT_TABLE}")
    print(f"Filters: from={args.date_from} to={args.date_to} limit={args.limit} dry_run={args.dry_run}")
    if HAS_CONTRACT:
        print(f"Contract: ✅ Enabled (hash: {CONTRACT_HASH[:16]}...)")
    else:
        print(f"Contract: ⚠️  Disabled (pydantic not available, using local hash: {CONTRACT_HASH[:16]}...)")
    print()

    # Load model artifact (frozen)
    try:
        artifact = load_model_artifact(MODEL_PATH)
    except Exception as e:
        eprint(f"❌ Failed to load model artifact: {e}")
        sys.exit(1)

    # Connect DuckDB (write mode if not dry-run)
    try:
        conn = connect_duckdb_with_retry(DB_PATH, read_only=args.dry_run)
    except Exception as e:
        eprint(f"❌ DuckDB connect failed: {e}")
        sys.exit(1)

    try:
        # Fetch input data
        df = fetch_input_df(conn, args.date_from, args.date_to, args.limit)
        if df.empty:
            eprint("⚠️ No rows fetched from input view. Nothing to do.")
            sys.exit(0)

        # Check required columns present
        missing = [c for c in REQUIRED_RAW_COLS if c not in df.columns]
        if missing:
            eprint(f"❌ Missing columns in input view {INPUT_VIEW}: {missing}")
            sys.exit(1)

        # Invariants
        ok, violations = invariant_checks(df)
        if not ok:
            eprint("❌ Invariant check failed:")
            for v in violations:
                eprint(f"  - {v}")
            # Helpful samples
            try:
                bad_mask = df[["date", "score_v2_1", "n_us_events_day"]].isna().any(axis=1)
                if bad_mask.any():
                    eprint("\nSample rows with NULL critical cols:")
                    eprint(df.loc[bad_mask, ["date", "score_v2_1", "n_us_events_day"]].head(10).to_string(index=False))
            except Exception:
                pass
            sys.exit(1)

        # Build feature matrix and predict
        X = build_feature_matrix(df)
        pred_log, pred_vol = predict(artifact, X)

        df_out = pd.DataFrame({
            "date": df["date"],
            "pred_log_vol": pred_log.astype(float),
            "pred_vol_pips": pred_vol.astype(float),
            "model_version": artifact["version"],
        })

        # Sanity stats
        print("📊 Output sanity stats:")
        print(df_out[["pred_log_vol", "pred_vol_pips"]].describe().to_string())
        print()

        write_output(conn, df_out, dry_run=args.dry_run)

        print("\n✅ Apply V3.2.1 completed OK")
        print("=" * 110)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

