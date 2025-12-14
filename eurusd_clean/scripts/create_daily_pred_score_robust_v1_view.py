#!/usr/bin/env python3
"""
Création de la vue daily_pred_score_robust_v1
==============================================

Vue journalière avec métriques robustes du score prédictif ex-ante.

Basée sur:
- events_with_pred_score_v1

Métriques (anti-dup + anti-dilution):
- pred_daily_sum : SUM(score_pred_v1)
- pred_daily_sum_ts_country_max : anti-duplication
- pred_daily_top5_sum, pred_daily_top20_sum : anti-dilution
- pred_top1_share_pct, pred_top5_share_pct : concentration
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

BASE_VIEW = "events_with_pred_score_v1"
VIEW_NAME = "daily_pred_score_robust_v1"

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
WITH base AS (
    SELECT
        DATE(ts_local) AS date,
        ts_local,
        country,
        score_pred_v1
    FROM {BASE_VIEW}
    WHERE score_pred_v1 IS NOT NULL
),
-- Agrégation par timestamp-country (anti-duplication)
ts_country_max AS (
    SELECT
        date,
        ts_local,
        country,
        MAX(score_pred_v1) AS max_score_per_group
    FROM base
    GROUP BY date, ts_local, country
),
-- Score journalier standard (SUM de tous les événements)
daily_sum AS (
    SELECT
        date,
        SUM(score_pred_v1) AS pred_daily_sum,
        COUNT(*) AS n_events
    FROM base
    GROUP BY date
),
-- Score anti-duplication (SUM des MAX par groupe ts_local+country)
daily_sum_robust AS (
    SELECT
        date,
        SUM(max_score_per_group) AS pred_daily_sum_ts_country_max,
        COUNT(*) AS n_ts_country_groups
    FROM ts_country_max
    GROUP BY date
),
-- Top-K scores du jour
ranked_scores AS (
    SELECT
        date,
        score_pred_v1,
        ROW_NUMBER() OVER (PARTITION BY date ORDER BY score_pred_v1 DESC) AS rn
    FROM base
),
top_scores AS (
    SELECT
        date,
        MAX(CASE WHEN rn = 1 THEN score_pred_v1 END) AS top1_score,
        SUM(CASE WHEN rn <= 5 THEN score_pred_v1 END) AS pred_daily_top5_sum,
        SUM(CASE WHEN rn <= 20 THEN score_pred_v1 END) AS pred_daily_top20_sum
    FROM ranked_scores
    GROUP BY date
)
-- Jointure finale
SELECT
    d.date,
    -- Métriques standard
    d.pred_daily_sum,
    d.n_events,
    -- Métriques robustes anti-duplication
    COALESCE(r.pred_daily_sum_ts_country_max, 0.0) AS pred_daily_sum_ts_country_max,
    COALESCE(r.n_ts_country_groups, 0) AS n_ts_country_groups,
    -- Top-K scores
    COALESCE(t.top1_score, 0.0) AS pred_top1_score,
    COALESCE(t.pred_daily_top5_sum, 0.0) AS pred_daily_top5_sum,
    COALESCE(t.pred_daily_top20_sum, 0.0) AS pred_daily_top20_sum,
    -- Indices de concentration
    CASE 
        WHEN d.pred_daily_sum > 0 THEN ROUND(100.0 * COALESCE(t.top1_score, 0.0) / d.pred_daily_sum, 1)
        ELSE 0.0
    END AS pred_top1_share_pct,
    CASE 
        WHEN d.pred_daily_sum > 0 THEN ROUND(100.0 * COALESCE(t.pred_daily_top5_sum, 0.0) / d.pred_daily_sum, 1)
        ELSE 0.0
    END AS pred_top5_share_pct
FROM daily_sum d
LEFT JOIN daily_sum_robust r ON d.date = r.date
LEFT JOIN top_scores t ON d.date = t.date
ORDER BY d.date;
"""


def main():
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)

    print("=" * 100)
    print(f"CRÉATION / MISE À JOUR DE LA VUE {VIEW_NAME}")
    print("=" * 100)
    print(f"DB : {DB_PATH}\n")

    conn = duckdb.connect(str(DB_PATH), read_only=False)

    try:
        print("🔧 Création de la vue journalière robuste...")
        conn.execute(CREATE_VIEW_SQL)
        print(f" ✅ Vue {VIEW_NAME} créée / remplacée\n")

        # Sanity checks
        print("📊 Sanity-check : nombre de jours")
        df_count = conn.execute(f"SELECT COUNT(*) AS n FROM {VIEW_NAME}").df()
        n = int(df_count.iloc[0]["n"])
        print(f" → {n} jours dans {VIEW_NAME}\n")

        print("📊 Statistiques globales")
        df_stats = conn.execute(f"""
            SELECT
                ROUND(AVG(pred_daily_sum), 2) AS avg_pred_daily_sum,
                ROUND(MEDIAN(pred_daily_sum), 2) AS p50_pred_daily_sum,
                ROUND(AVG(pred_daily_sum_ts_country_max), 2) AS avg_pred_sum_robust,
                ROUND(MEDIAN(pred_daily_sum_ts_country_max), 2) AS p50_pred_sum_robust,
                ROUND(AVG(pred_daily_top20_sum), 2) AS avg_pred_top20_sum,
                ROUND(MEDIAN(pred_daily_top20_sum), 2) AS p50_pred_top20_sum
            FROM {VIEW_NAME}
        """).df()
        print(df_stats.to_string(index=False))
        print()

        print("📊 Top 10 jours par pred_daily_top20_sum")
        df_top = conn.execute(f"""
            SELECT
                date,
                ROUND(pred_daily_sum, 2) AS pred_daily_sum,
                ROUND(pred_daily_sum_ts_country_max, 2) AS pred_sum_robust,
                ROUND(pred_daily_top20_sum, 2) AS pred_top20_sum,
                n_events,
                n_ts_country_groups
            FROM {VIEW_NAME}
            ORDER BY pred_daily_top20_sum DESC
            LIMIT 10
        """).df()
        print(df_top.to_string(index=False))
        print()

        print("=" * 100)
        print(f"✅ Vue {VIEW_NAME} prête (métriques robustes prédictives)")
        print("=" * 100)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

