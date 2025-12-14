#!/usr/bin/env python3
"""
Pipeline post-mise à jour DB
============================

Enchaîne automatiquement :
1. Détection complète des mouvements/patterns (workflow correct)
2. Reconstruction des clusters événements (step2_movements_with_clusters.csv)
3. Rafraîchissement des caches cluster/pattern
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from datetime import timedelta
from typing import List

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import config  # noqa: E402
from core.event_utils import normalize_event_keys_list  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SESSION137_DIR = PROJECT_ROOT / "scripts" / "session137"
DETECTION_SCRIPT = SESSION137_DIR / "extract_all_patterns_real_metrics_correct_workflow.py"
ALL_PATTERNS_CSV = SESSION137_DIR / "all_patterns_real_metrics_correct_workflow.csv"
STEP2_OUTPUT = SESSION137_DIR / "step2_movements_with_clusters.csv"
CACHE_SCRIPT = PROJECT_ROOT / "scripts" / "cache_refresh.py"
FINNHUB_PATTERNS_SCRIPT = PROJECT_ROOT / "scripts" / "finnhub_detect_patterns.py"
FINNHUB_SR_SCRIPT = PROJECT_ROOT / "scripts" / "finnhub_support_resistance.py"

WINDOW_MINUTES = 30


def run_subprocess(script: Path) -> None:
    if not script.exists():
        raise FileNotFoundError(f"Script introuvable : {script}")
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{script.name} a échoué :\n{result.stderr or result.stdout}")
    print(result.stdout.strip())


def rebuild_clusters(window_minutes: int = WINDOW_MINUTES) -> None:
    if not ALL_PATTERNS_CSV.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {ALL_PATTERNS_CSV}")

    df_movements = pd.read_csv(ALL_PATTERNS_CSV)
    df_movements["movement_datetime"] = pd.to_datetime(
        df_movements["movement_datetime"],
        utc=True,
        errors="coerce",
    ).dt.tz_convert("Europe/Zurich")
    df_movements = df_movements.dropna(subset=["movement_datetime"]).reset_index(drop=True)
    df_movements["movement_datetime_utc"] = df_movements["movement_datetime"].dt.tz_convert("UTC")

    conn = duckdb.connect(str(config.DB_PATH), read_only=True)
    query = """
        SELECT 
            e.ts_utc,
            e.event_key,
            e.importance_n,
            COALESCE(ef.empirical_score, 0) AS empirical_score
        FROM events e
        LEFT JOIN event_families ef
            ON e.event_key = ef.event_key AND e.country = ef.country
        WHERE e.ts_utc BETWEEN ? AND ?
          AND e.event_key IS NOT NULL
    """

    rows: List[dict] = []
    for row in df_movements.itertuples():
        start = row.movement_datetime_utc - pd.Timedelta(minutes=window_minutes)
        end = row.movement_datetime_utc + pd.Timedelta(minutes=window_minutes)
        df_events = conn.execute(query, [start.to_pydatetime(), end.to_pydatetime()]).df()

        if df_events.empty:
            event_keys_list: List[str] = []
            total_score = 0.0
            num_events = 0
        else:
            event_keys_list = [ek for ek in df_events["event_key"].astype(str).tolist() if ek]
            normalized = normalize_event_keys_list(event_keys_list)
            event_keys_list = [ek for ek in normalized if ek]
            total_score = float(df_events["empirical_score"].fillna(0).sum())
            num_events = int(len(event_keys_list))

        rows.append(
            {
                "movement_id": row.movement_id,
                "movement_datetime": row.movement_datetime,
                "impact_pips": row.impact_pips,
                "direction": row.direction,
                "num_events": num_events,
                "total_score": total_score,
                "event_keys": ",".join(sorted(event_keys_list)),
            }
        )

    conn.close()

    df_clusters = pd.DataFrame(rows)
    df_clusters.to_csv(STEP2_OUTPUT, index=False)
    print(f"✅ Clusters régénérés : {STEP2_OUTPUT}")


def main():
    print("=== PIPELINE POST-MISE À JOUR ===")
    print("1/5 Détection patterns Finnhub…")
    try:
        run_subprocess(FINNHUB_PATTERNS_SCRIPT)
    except Exception as e:
        print(f"⚠️  Détection patterns Finnhub échouée (non bloquant) : {e}")

    print("2/5 Import Support/Résistance Finnhub…")
    try:
        run_subprocess(FINNHUB_SR_SCRIPT)
    except Exception as e:
        print(f"⚠️  Import Support/Résistance échoué (non bloquant) : {e}")

    print("3/5 Détection complète des patterns…")
    run_subprocess(DETECTION_SCRIPT)

    print("4/5 Reconstruction des clusters…")
    rebuild_clusters()

    print("5/5 Rafraîchissement des caches…")
    run_subprocess(CACHE_SCRIPT)

    print("✅ Pipeline terminé")


if __name__ == "__main__":
    main()

