#!/usr/bin/env python3

"""

Backtest V8 Predictions - Validation End-to-End

Objectif:

- Valider la fiabilité du moteur V8 avant intégration UI.

- Rejouer les prédictions sur dates historiques et comparer aux mouvements réels.

Inputs:

- outputs/direction_router_test/patterns_detected.csv

- outputs/direction_router_test/movements_historical.csv

- DB DuckDB events (warehouse.duckdb)

Outputs:

- outputs/backtest_v8/detailed_results.csv

- outputs/backtest_v8/summary.csv

- outputs/backtest_v8/by_cluster.csv

- outputs/backtest_v8/by_pattern.csv

- outputs/backtest_v8/by_year.csv

SAFE criteria (indicatifs):

- Direction accuracy global > 55-60%

- Aucun cluster core < 50%

- MAPE impact sur forts/moyens < 35-40%

- No drift >10% entre 2022-23 et 2024-25

"""

import sys

from pathlib import Path

from datetime import timedelta

from typing import Dict, Tuple, Optional, List

import numpy as np

import pandas as pd

import duckdb

# =============================================================================

# Paths

# =============================================================================

SCRIPT_DIR = Path(__file__).parent

PATTERNS_FILE = SCRIPT_DIR / "outputs" / "direction_router_test" / "patterns_detected.csv"

MOVEMENTS_FILE = SCRIPT_DIR / "outputs" / "direction_router_test" / "movements_historical.csv"

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

OUTPUT_DIR = SCRIPT_DIR / "outputs" / "backtest_v8"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================

# Imports moteur

# =============================================================================

sys.path.insert(0, str(SCRIPT_DIR))

from direction_router_v6 import (

    load_direction_router_dependencies,

    CORE_FAMILIES_V6,

    map_event_to_family,

    V8_MIN_STATS_DATE,

    V8_MAX_STATS_DATE,

)

from integrate_direction_first_leg import calculate_cluster_impact_with_direction

# =============================================================================

# Utils

# =============================================================================

COUNTRIES_ALLOWED = ("US", "EU", "GB", "DE")

def load_inputs() -> Tuple[pd.DataFrame, pd.DataFrame]:

    if not PATTERNS_FILE.exists():

        raise FileNotFoundError(f"patterns_detected.csv introuvable: {PATTERNS_FILE}")

    if not MOVEMENTS_FILE.exists():

        raise FileNotFoundError(f"movements_historical.csv introuvable: {MOVEMENTS_FILE}")

    patterns_df = pd.read_csv(PATTERNS_FILE)

    movements_df = pd.read_csv(MOVEMENTS_FILE)

    # parse timestamps

    if "movement_start_time" in patterns_df.columns:

        patterns_df["movement_start_time"] = pd.to_datetime(

            patterns_df["movement_start_time"], utc=True, errors="coerce"

        )

    movements_df["movement_start_time"] = pd.to_datetime(

        movements_df["movement_start_time"], utc=True, errors="coerce"

    )

    movements_df["peak_time"] = pd.to_datetime(

        movements_df["peak_time"], utc=True, errors="coerce"

    )

    movements_df["movement_end_time"] = pd.to_datetime(

        movements_df["movement_end_time"], utc=True, errors="coerce"

    )

    return patterns_df, movements_df

def load_events_for_date(conn: duckdb.DuckDBPyConnection, date_str: str) -> pd.DataFrame:

    day_start = pd.Timestamp(date_str).tz_localize("UTC")

    day_end = day_start + timedelta(days=1)

    query = """

    SELECT

        ts_utc,

        country,

        event_title,

        event_key,

        actual,

        estimate,

        previous,

        forecast,

        importance_n

    FROM events

    WHERE ts_utc >= ? AND ts_utc < ?

      AND country IN ('US', 'EU', 'GB', 'DE')

      AND actual IS NOT NULL

      AND estimate IS NOT NULL

    ORDER BY ts_utc

    """

    df = conn.execute(query, [day_start, day_end]).df()

    return df

def pick_real_movement(movements_df: pd.DataFrame, date_str: str, min_peak: float = 40.0):

    day_moves = movements_df[

        (movements_df["date"] == date_str) &

        (movements_df["peak_pips"] >= min_peak)

    ].copy()

    if len(day_moves) == 0:

        return None

    # plus fort mouvement du jour

    idx = day_moves["peak_pips"].idxmax()

    return day_moves.loc[idx]

def safe_div(a, b):

    return np.nan if b == 0 or pd.isna(b) else a / b

# =============================================================================

# Main backtest

# =============================================================================

def main():

    print("📥 Chargement inputs...")

    patterns_df, movements_df = load_inputs()

    print(f"Patterns dates: {len(patterns_df)}")

    print(f"Movements: {len(movements_df)}")

    print("\n🔌 Connexion DB...")

    conn = duckdb.connect(str(DB_PATH), read_only=True)

    print("\n📊 Chargement stats_map V8...")

    stats_map, alpha_map = load_direction_router_dependencies(

        db_path=DB_PATH,

        min_date=V8_MIN_STATS_DATE,

        max_date=V8_MAX_STATS_DATE,

        horizon="1h",

        alpha_file=None

    )

    print(f"Stats keys: {len(stats_map)}")

    results = []

    n_skipped = 0

    n_no_real_move = 0

    n_no_core = 0

    print("\n🚀 Backtest sur dates patterns_detected...")

    for _, row in patterns_df.iterrows():

        date_str = str(row["date"])

        movement_start_time = row.get("movement_start_time", None)

        if pd.isna(movement_start_time):

            movement_start_time = None

        # 1) events du jour

        events_df = load_events_for_date(conn, date_str)

        if len(events_df) == 0:

            continue

        # 2) familles + core

        events_df["family"] = events_df["event_key"].apply(map_event_to_family)

        core_df = events_df[events_df["family"].isin(CORE_FAMILIES_V6)].copy()

        if len(core_df) == 0:

            n_no_core += 1

            continue

        # colonnes minimales si absentes

        if "empirical_score" not in core_df.columns:

            core_df["empirical_score"] = 10.0

        if "latency_median" not in core_df.columns:

            core_df["latency_median"] = 2.0

        # 3) prédiction V8

        pred = calculate_cluster_impact_with_direction(

            cluster_events=core_df,

            stats_map=stats_map,

            alpha_map=alpha_map,

            trigger_z=1.0,

            theta=0.05,

            first_leg_mode=True,

            use_linear_formula=True,

            core_families=CORE_FAMILIES_V6,

            movement_start_time=movement_start_time,

            conn=conn

        )

        if pred.get("skipped", False):

            n_skipped += 1

            continue

        # 4) mouvement réel associé

        real_move = pick_real_movement(movements_df, date_str, min_peak=40.0)

        if real_move is None:

            n_no_real_move += 1

            continue

        impact_pred = float(pred.get("impact_pips", np.nan))

        direction_pred = pred.get("direction_first_leg", "UNKNOWN")

        pattern_pred = pred.get("pattern_type", None)

        impact_real = float(real_move["peak_pips"])

        direction_real = str(real_move["direction"])

        # legs réels (multi-wave) via patterns_detected

        leg1_real = row.get("leg1_amp_pips", np.nan)

        leg2_real = row.get("leg2_amp_pips", np.nan)

        total_real = row.get("total_amp_pips", np.nan)

        leg1_pred = np.nan

        leg2_pred = np.nan

        total_pred = np.nan

        if pred.get("leg1") and pred.get("leg2"):

            leg1_pred = float(pred["leg1"].get("amp_pips", np.nan))

            leg2_pred = float(pred["leg2"].get("amp_pips", np.nan))

            total_pred = impact_pred

        res = {

            "date": date_str,

            "year": date_str[:4],

            "cluster_type_cache": row.get("cluster_type", None),

            "pattern_type_cache": row.get("pattern_type", None),

            "direction_cache": row.get("direction_first_leg", None),

            "pattern_type_pred": pattern_pred,

            "direction_pred": direction_pred,

            "impact_pred": impact_pred,

            "trigger_strength_pred": float(pred.get("trigger_strength", np.nan)),

            "has_trigger_pred": bool(pred.get("has_trigger", False)),

            "direction_score_pred": float(pred.get("direction_score", np.nan)),

            "direction_real": direction_real,

            "impact_real": impact_real,

            "movement_class_real": real_move.get("movement_class", None),

            "leg1_pred": leg1_pred,

            "leg2_pred": leg2_pred,

            "total_pred": total_pred,

            "leg1_real": leg1_real,

            "leg2_real": leg2_real,

            "total_real": total_real,

        }

        results.append(res)

    conn.close()

    results_df = pd.DataFrame(results)

    print("\n✅ Backtest terminé.")

    print(f"Dates évaluées: {len(results_df)}")

    print(f"Skips moteur: {n_skipped}")

    print(f"Sans mouvement réel >=40p: {n_no_real_move}")

    print(f"Sans core events: {n_no_core}")

    if len(results_df) == 0:

        print("❌ Aucun résultat exploitable. Vérifier inputs/DB.")

        return

    # =============================================================================

    # Metrics

    # =============================================================================

    results_df["direction_correct"] = results_df["direction_pred"] == results_df["direction_real"]

    results_df["impact_abs_err"] = (results_df["impact_real"] - results_df["impact_pred"]).abs()

    results_df["impact_pct_err"] = results_df.apply(

        lambda r: safe_div(r["impact_abs_err"], r["impact_real"]), axis=1

    ) * 100.0

    # hit rate impact

    results_df["impact_hit"] = results_df["impact_real"] >= 0.7 * results_df["impact_pred"]

    # ratios legs

    mw_df = results_df[results_df["leg1_pred"].notna()].copy()

    if len(mw_df) > 0:

        mw_df["leg1_ratio_pred"] = mw_df.apply(

            lambda r: safe_div(r["leg1_pred"], r["total_pred"]), axis=1

        )

        mw_df["leg1_ratio_real"] = mw_df.apply(

            lambda r: safe_div(r["leg1_real"], r["total_real"]), axis=1

        )

        mw_df["leg1_ratio_abs_err"] = (mw_df["leg1_ratio_real"] - mw_df["leg1_ratio_pred"]).abs()

    else:

        mw_df = pd.DataFrame()

    # global summary

    summary = {

        "N_dates": len(results_df),

        "direction_accuracy_pct": results_df["direction_correct"].mean() * 100.0,

        "impact_hit_rate_pct": results_df["impact_hit"].mean() * 100.0,

        "impact_MAE_pips": results_df["impact_abs_err"].mean(),

        "impact_MAPE_pct": results_df["impact_pct_err"].mean(),

        "N_multiwave": len(mw_df),

        "leg1_ratio_MAE": mw_df["leg1_ratio_abs_err"].mean() if len(mw_df) else np.nan,

        "period_min": results_df["year"].min(),

        "period_max": results_df["year"].max(),

    }

    summary_df = pd.DataFrame([summary])

    # by cluster

    by_cluster = results_df.groupby("cluster_type_cache").agg(

        N=("date", "count"),

        direction_acc_pct=("direction_correct", lambda x: x.mean() * 100.0),

        impact_hit_pct=("impact_hit", lambda x: x.mean() * 100.0),

        impact_MAE=("impact_abs_err", "mean"),

        impact_MAPE=("impact_pct_err", "mean"),

    ).reset_index()

    # by pattern

    by_pattern = results_df.groupby("pattern_type_cache").agg(

        N=("date", "count"),

        direction_acc_pct=("direction_correct", lambda x: x.mean() * 100.0),

        impact_hit_pct=("impact_hit", lambda x: x.mean() * 100.0),

        impact_MAE=("impact_abs_err", "mean"),

        impact_MAPE=("impact_pct_err", "mean"),

    ).reset_index()

    # by year

    by_year = results_df.groupby("year").agg(

        N=("date", "count"),

        direction_acc_pct=("direction_correct", lambda x: x.mean() * 100.0),

        impact_hit_pct=("impact_hit", lambda x: x.mean() * 100.0),

        impact_MAE=("impact_abs_err", "mean"),

        impact_MAPE=("impact_pct_err", "mean"),

    ).reset_index()

    # drift check 22-23 vs 24-25

    early = results_df[results_df["year"].isin(["2022", "2023"])]

    late = results_df[results_df["year"].isin(["2024", "2025"])]

    if len(early) and len(late):

        drift_dir = abs(early["direction_correct"].mean() - late["direction_correct"].mean()) * 100.0

        drift_impact = abs(early["impact_pct_err"].mean() - late["impact_pct_err"].mean())

    else:

        drift_dir = np.nan

        drift_impact = np.nan

    print("\n📌 METRICS GLOBALES")

    print(summary_df.to_string(index=False))

    print("\n📌 BY CLUSTER")

    print(by_cluster.to_string(index=False))

    print("\n📌 BY PATTERN")

    print(by_pattern.to_string(index=False))

    print("\n📌 BY YEAR")

    print(by_year.to_string(index=False))

    print("\n📌 DRIFT 2022-23 vs 2024-25")

    print(f"Direction drift: {drift_dir:.2f}%")

    print(f"Impact MAPE drift: {drift_impact:.2f} pts")

    # =============================================================================

    # Save outputs

    # =============================================================================

    results_df.to_csv(OUTPUT_DIR / "detailed_results.csv", index=False)

    summary_df.to_csv(OUTPUT_DIR / "summary.csv", index=False)

    by_cluster.to_csv(OUTPUT_DIR / "by_cluster.csv", index=False)

    by_pattern.to_csv(OUTPUT_DIR / "by_pattern.csv", index=False)

    by_year.to_csv(OUTPUT_DIR / "by_year.csv", index=False)

    print(f"\n💾 Outputs écrits dans: {OUTPUT_DIR}")

if __name__ == "__main__":

    main()

