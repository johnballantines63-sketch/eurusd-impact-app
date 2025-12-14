#!/usr/bin/env python3
"""
Diagnostic cutoff 2024-07-01 (chute Spearman V2)
=================================================

Analyse pourquoi le cutoff 2024-07-01 a une chute importante de Spearman.
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

V1_VIEW = "daily_pred_score_robust_v1"
V2_VIEW = "daily_pred_score_release_group_v1"
RELEASE_GROUP_VIEW = "events_with_release_group_v1"
PRED_SCORE_VIEW = "events_with_pred_score_v1"

CUTOFF = "2024-07-01"


def main():
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        print("=" * 100)
        print("DIAGNOSTIC CUTOFF 2024-07-01")
        print("=" * 100)
        print()
        
        # 1. Jours où le ranking change le plus (V2 vs V1)
        print("📊 Top 30 jours avec le plus grand delta de ranking (V2 MAX vs V1):")
        df_ranks = conn.execute(f"""
            WITH v1_ranked AS (
                SELECT
                    date,
                    pred_daily_top20_sum,
                    ROW_NUMBER() OVER (ORDER BY pred_daily_top20_sum DESC) AS rank_v1
                FROM {V1_VIEW}
                WHERE date > '{CUTOFF}'
            ),
            v2_ranked AS (
                SELECT
                    date,
                    pred_daily_release_top20_sum_max,
                    ROW_NUMBER() OVER (ORDER BY pred_daily_release_top20_sum_max DESC) AS rank_v2
                FROM {V2_VIEW}
                WHERE date > '{CUTOFF}'
            )
            SELECT
                v1.date,
                v1.pred_daily_top20_sum AS v1_score,
                v1.rank_v1,
                v2.pred_daily_release_top20_sum_max AS v2_score,
                v2.rank_v2,
                ABS(v2.rank_v2 - v1.rank_v1) AS rank_delta
            FROM v1_ranked v1
            INNER JOIN v2_ranked v2 ON v1.date = v2.date
            ORDER BY rank_delta DESC
            LIMIT 30
        """).df()
        print(df_ranks.to_string(index=False))
        print()
        
        # 2. Pour les jours avec pire delta, lister les top release_groups
        print("📊 Top release_groups pour les 10 jours avec pire delta:")
        worst_dates = df_ranks.head(10)['date'].tolist()
        dates_str = "', '".join([str(d) for d in worst_dates])
        
        df_releases = conn.execute(f"""
            WITH release_scores AS (
                SELECT
                    r.release_group_id_v1,
                    r.release_family_v1,
                    DATE(r.ts_local) AS date,
                    MAX(p.score_pred_v1) AS score_release_max,
                    SUM(p.score_pred_v1) AS score_release_sum
                FROM {RELEASE_GROUP_VIEW} r
                INNER JOIN {PRED_SCORE_VIEW} p
                    ON r.ts_local = p.ts_local
                    AND r.country = p.country
                    AND r.event_key = p.event_key
                WHERE p.score_pred_v1 IS NOT NULL
                    AND DATE(r.ts_local) IN ('{dates_str}')
                GROUP BY 
                    r.release_group_id_v1,
                    r.release_family_v1,
                    DATE(r.ts_local)
            )
            SELECT
                date,
                release_family_v1,
                COUNT(*) AS n_events_in_release,
                ROUND(MAX(score_release_max), 2) AS max_score,
                ROUND(MAX(score_release_sum), 2) AS sum_score
            FROM release_scores
            GROUP BY date, release_family_v1
            ORDER BY date, max_score DESC
        """).df()
        print(df_releases.to_string(index=False))
        print()
        
        # 3. Comparaison distribution scores V1 vs V2 pour ce cutoff
        print("📊 Distribution des scores (V1 vs V2 MAX) pour cutoff 2024-07-01:")
        df_dist = conn.execute(f"""
            SELECT
                'V1' AS version,
                COUNT(*) AS n_days,
                ROUND(MIN(pred_daily_top20_sum), 2) AS min_score,
                ROUND(MEDIAN(pred_daily_top20_sum), 2) AS p50_score,
                ROUND(MAX(pred_daily_top20_sum), 2) AS max_score,
                ROUND(STDDEV(pred_daily_top20_sum), 2) AS std_score
            FROM {V1_VIEW}
            WHERE date > '{CUTOFF}'
            UNION ALL
            SELECT
                'V2_MAX' AS version,
                COUNT(*) AS n_days,
                ROUND(MIN(pred_daily_release_top20_sum_max), 2) AS min_score,
                ROUND(MEDIAN(pred_daily_release_top20_sum_max), 2) AS p50_score,
                ROUND(MAX(pred_daily_release_top20_sum_max), 2) AS max_score,
                ROUND(STDDEV(pred_daily_release_top20_sum_max), 2) AS std_score
            FROM {V2_VIEW}
            WHERE date > '{CUTOFF}'
        """).df()
        print(df_dist.to_string(index=False))
        print()
        
        print("=" * 100)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()

