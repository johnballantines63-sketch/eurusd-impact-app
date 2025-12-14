#!/usr/bin/env python3
"""
Pré-calcul des statistiques cluster/pattern
===========================================

Objectif : produire un cache exploitable instantanément par le calendrier
et le planificateur.

Entrées :
- scripts/session137/step2_movements_with_clusters.csv   (clusters + scores)
- scripts/session137/all_patterns_real_metrics_correct_workflow.csv  (patterns + métriques)

Sorties :
- data/cache_clusters.csv              (stats agrégées par cluster)
- data/cache_cluster_patterns.csv      (stats agrégées par cluster & pattern)

Usage :
    python3 scripts/cache_refresh.py
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
SESSION137_DIR = ROOT / "scripts" / "session137"
DATA_DIR = ROOT / "data"

STEP2_CSV = SESSION137_DIR / "step2_movements_with_clusters.csv"
PATTERNS_CSV = SESSION137_DIR / "all_patterns_real_metrics_correct_workflow.csv"

OUTPUT_CLUSTER = DATA_DIR / "cache_clusters.csv"
OUTPUT_CLUSTER_PATTERN = DATA_DIR / "cache_cluster_patterns.csv"


def normalize_event_keys(event_keys: str) -> str:
    """
    Transforme la liste d'events en signature normalisée
    """
    if pd.isna(event_keys) or not event_keys.strip():
        return ""
    items = [e.strip().lower() for e in event_keys.split(",") if e.strip()]
    items = sorted(dict.fromkeys(items))  # dédupliquer dans l'ordre
    return "|".join(items)


def safe_median(series: pd.Series) -> float:
    if series.dropna().empty:
        return np.nan
    return float(series.median())


def safe_mean(series: pd.Series) -> float:
    if series.dropna().empty:
        return np.nan
    return float(series.mean())


def ratio(series: pd.Series, value: str) -> float:
    if len(series) == 0:
        return np.nan
    return float((series == value).sum() / len(series))


def load_datasets() -> pd.DataFrame:
    if not STEP2_CSV.exists():
        raise FileNotFoundError(f"Introuvable : {STEP2_CSV}")
    if not PATTERNS_CSV.exists():
        raise FileNotFoundError(f"Introuvable : {PATTERNS_CSV}")

    df_clusters = pd.read_csv(STEP2_CSV)
    df_patterns = pd.read_csv(PATTERNS_CSV)

    df_clusters["movement_datetime"] = pd.to_datetime(
        df_clusters["movement_datetime"], utc=True, errors="coerce"
    )
    df_patterns["movement_datetime"] = pd.to_datetime(
        df_patterns["movement_datetime"], utc=True, errors="coerce"
    )
    if "event_time" in df_patterns.columns:
        df_patterns["event_time"] = pd.to_datetime(
            df_patterns["event_time"], utc=True, errors="coerce"
        )
    if "peak_time" in df_patterns.columns:
        df_patterns["peak_time"] = pd.to_datetime(
            df_patterns["peak_time"], utc=True, errors="coerce"
        )

    cluster_cols = df_clusters[
        ["movement_id", "event_keys", "num_events", "total_score"]
    ].rename(
        columns={"num_events": "cluster_num_events", "total_score": "cluster_total_score"}
    )

    merged = df_patterns.merge(cluster_cols, on="movement_id", how="left")

    merged["cluster_signature"] = merged["event_keys"].apply(normalize_event_keys)
    if "event_time" in merged.columns:
        merged["latency_minutes"] = (
            (merged["movement_datetime"] - merged["event_time"])
            .dt.total_seconds()
            .div(60.0)
        )
    else:
        merged["latency_minutes"] = np.nan
    merged["peak_minutes_from_start"] = pd.to_numeric(
        merged.get("peak_minutes_from_start"), errors="coerce"
    )

    return merged


def aggregate_clusters(df: pd.DataFrame) -> pd.DataFrame:
    def dominant(series: pd.Series) -> str:
        if series.dropna().empty:
            return ""
        return series.value_counts().idxmax()

    grouped = []
    for signature, grp in df.groupby("cluster_signature"):
        grouped.append(
            {
                "cluster_signature": signature,
                "n_samples": len(grp),
                "num_events_median": safe_median(grp.get("cluster_num_events", pd.Series())),
                "total_score_median": safe_median(grp.get("cluster_total_score", pd.Series())),
                "impact_median": safe_median(grp["impact_pips"]),
                "impact_mean": safe_mean(grp["impact_pips"]),
                "impact_std": float(grp["impact_pips"].std(ddof=0)) if len(grp) > 1 else 0.0,
                "latency_median": safe_median(grp["latency_minutes"]),
                "ttr_median": safe_median(grp["peak_minutes_from_start"]),
                "pullback_median": safe_median(grp.get("pullback_pips", pd.Series())),
                "dominant_pattern": dominant(grp["pattern_type"]),
                "dominant_direction": dominant(grp["direction"]),
                "ratio_up": ratio(grp["direction"], "UP"),
                "ratio_down": ratio(grp["direction"], "DOWN"),
            }
        )
    return pd.DataFrame(grouped).sort_values("n_samples", ascending=False)


def aggregate_cluster_patterns(df: pd.DataFrame) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    grouped = df.groupby(["cluster_signature", "pattern_type", "direction"])
    for (signature, pattern, direction), grp in grouped:
        records.append(
            {
                "cluster_signature": signature,
                "pattern_type": pattern,
                "direction": direction,
                "n_samples": len(grp),
                "impact_median": safe_median(grp["impact_pips"]),
                "latency_median": safe_median(grp["latency_minutes"]),
                "ttr_median": safe_median(grp["peak_minutes_from_start"]),
                "pullback_median": safe_median(grp.get("pullback_pips", pd.Series())),
            }
        )
    return pd.DataFrame(records).sort_values("n_samples", ascending=False)


def main():
    parser = argparse.ArgumentParser(description="Pré-calcul des stats clusters/patterns")
    parser.add_argument("--out-dir", type=Path, default=DATA_DIR, help="Répertoire de sortie")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print("📥 Chargement des datasets…")
    df = load_datasets()
    print(f"   → {len(df):,} mouvements fusionnés")

    print("📊 Agrégation par cluster…")
    cache_clusters = aggregate_clusters(df)
    cache_clusters.to_csv(args.out_dir / "cache_clusters.csv", index=False)
    print(f"   → {len(cache_clusters):,} clusters écrits dans cache_clusters.csv")

    print("📊 Agrégation par cluster & pattern…")
    cache_cluster_patterns = aggregate_cluster_patterns(df)
    cache_cluster_patterns.to_csv(args.out_dir / "cache_cluster_patterns.csv", index=False)
    print(f"   → {len(cache_cluster_patterns):,} lignes écrites dans cache_cluster_patterns.csv")

    print("✅ Cache pré-calculé. Intégrer désormais ces fichiers dans le calendrier / planificateur.")


if __name__ == "__main__":
    main()

