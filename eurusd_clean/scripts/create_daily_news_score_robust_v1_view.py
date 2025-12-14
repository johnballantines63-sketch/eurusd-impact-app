#!/usr/bin/env python3
"""
Création de la vue daily_news_score_robust_v1
==============================================

Vue journalière avec métriques robustes anti-duplication.

Basée sur:
- events_with_canonical_impact_scored_bucketed_v1

Métriques ajoutées:
- daily_sum_score : SUM(score_impact_v1) [actuel, conservé]
- daily_sum_ts_country_max : SUM(MAX par ts_utc+country) [anti-dup]
- daily_top5_sum, daily_top20_sum : somme des Top-K scores
- top1_share, top5_share : part du top score dans le total
- n_ts_country_groups : nombre de groupes (ts_utc, country) uniques
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

BASE_VIEW = "events_with_canonical_impact_scored_bucketed_v1"
VIEW_NAME = "daily_news_score_robust_v1"

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
WITH base AS (
    SELECT
        DATE(ts_utc) AS date,
        ts_utc,
        country,
        score_impact_v1,
        score_bucket_v1,
        impact_unified_pips
    FROM {BASE_VIEW}
),
-- Agrégation par timestamp-country (anti-duplication)
ts_country_max AS (
    SELECT
        date,
        ts_utc,
        country,
        MAX(score_impact_v1) AS max_score_per_group
    FROM base
    GROUP BY date, ts_utc, country
),
-- Score journalier standard (SUM de tous les événements)
daily_sum AS (
    SELECT
        date,
        SUM(score_impact_v1) AS daily_sum_score,
        COUNT(*) AS n_events,
        COUNT(CASE WHEN score_bucket_v1 = 'EXTREME' THEN 1 END) AS n_extreme,
        COUNT(CASE WHEN score_bucket_v1 = 'HIGH' THEN 1 END) AS n_high,
        COUNT(CASE WHEN score_bucket_v1 = 'MEDIUM' THEN 1 END) AS n_medium,
        COUNT(CASE WHEN score_bucket_v1 = 'LOW' THEN 1 END) AS n_low
    FROM base
    GROUP BY date
),
-- Score anti-duplication (SUM des MAX par groupe ts_utc+country)
daily_sum_robust AS (
    SELECT
        date,
        SUM(max_score_per_group) AS daily_sum_ts_country_max,
        COUNT(*) AS n_ts_country_groups
    FROM ts_country_max
    GROUP BY date
),
-- Top-K scores du jour
ranked_scores AS (
    SELECT
        date,
        score_impact_v1,
        ROW_NUMBER() OVER (PARTITION BY date ORDER BY score_impact_v1 DESC) AS rn
    FROM base
),
top_scores AS (
    SELECT
        date,
        MAX(CASE WHEN rn = 1 THEN score_impact_v1 END) AS top1_score,
        SUM(CASE WHEN rn <= 5 THEN score_impact_v1 END) AS daily_top5_sum,
        SUM(CASE WHEN rn <= 20 THEN score_impact_v1 END) AS daily_top20_sum
    FROM ranked_scores
    GROUP BY date
)
-- Jointure finale
SELECT
    d.date,
    -- Métriques standard (conservées)
    d.daily_sum_score,
    d.n_events,
    d.n_extreme,
    d.n_high,
    d.n_medium,
    d.n_low,
    -- Métriques robustes anti-duplication
    COALESCE(r.daily_sum_ts_country_max, 0.0) AS daily_sum_ts_country_max,
    COALESCE(r.n_ts_country_groups, 0) AS n_ts_country_groups,
    -- Top-K scores
    COALESCE(t.top1_score, 0.0) AS top1_score,
    COALESCE(t.daily_top5_sum, 0.0) AS daily_top5_sum,
    COALESCE(t.daily_top20_sum, 0.0) AS daily_top20_sum,
    -- Indices de concentration
    CASE 
        WHEN d.daily_sum_score > 0 THEN ROUND(100.0 * COALESCE(t.top1_score, 0.0) / d.daily_sum_score, 1)
        ELSE 0.0
    END AS top1_share_pct,
    CASE 
        WHEN d.daily_sum_score > 0 THEN ROUND(100.0 * COALESCE(t.daily_top5_sum, 0.0) / d.daily_sum_score, 1)
        ELSE 0.0
    END AS top5_share_pct
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
    print(f"DB : {DB_PATH}")
    print()

    conn = duckdb.connect(str(DB_PATH), read_only=False)

    try:
        # 1) Création / remplacement de la vue
        print("🔧 Création de la vue robuste...")
        conn.execute(CREATE_VIEW_SQL)
        print(f" ✅ Vue {VIEW_NAME} créée / remplacée\n")

        # 2) Sanity-check : nombre de jours
        print("📊 Sanity-check : nombre de jours dans la vue")
        df_count = conn.execute(f"SELECT COUNT(*) AS n FROM {VIEW_NAME}").df()
        n = int(df_count.iloc[0]["n"])
        print(f" → {n} jours dans {VIEW_NAME}\n")

        # 3) Comparaison des métriques sur quelques jours
        print("📊 Comparaison daily_sum_score vs daily_sum_ts_country_max (TOP 10 par daily_sum_score)")
        df_comparison = conn.execute(f"""
            SELECT
                date,
                ROUND(daily_sum_score, 2) AS daily_sum_score,
                ROUND(daily_sum_ts_country_max, 2) AS daily_sum_ts_country_max,
                n_events,
                n_ts_country_groups,
                ROUND(top1_share_pct, 1) AS top1_share_pct,
                ROUND(top5_share_pct, 1) AS top5_share_pct,
                n_extreme
            FROM {VIEW_NAME}
            ORDER BY daily_sum_score DESC
            LIMIT 10
        """).df()
        print(df_comparison.to_string(index=False))
        print()

        # 4) Stats globales sur les métriques robustes
        print("📊 Statistiques globales sur les métriques robustes")
        df_stats = conn.execute(f"""
            SELECT
                ROUND(AVG(daily_sum_score), 2) AS avg_daily_sum_score,
                ROUND(MEDIAN(daily_sum_score), 2) AS p50_daily_sum_score,
                ROUND(AVG(daily_sum_ts_country_max), 2) AS avg_daily_sum_robust,
                ROUND(MEDIAN(daily_sum_ts_country_max), 2) AS p50_daily_sum_robust,
                ROUND(AVG(n_events), 1) AS avg_n_events,
                ROUND(AVG(n_ts_country_groups), 1) AS avg_n_groups,
                ROUND(AVG(top1_share_pct), 1) AS avg_top1_share,
                ROUND(AVG(top5_share_pct), 1) AS avg_top5_share
            FROM {VIEW_NAME}
        """).df()
        print(df_stats.to_string(index=False))
        print()

        # 5) Cas extrêmes : jours avec forte différence entre sum et robust
        print("📊 TOP 10 jours avec la plus forte différence (daily_sum_score - daily_sum_ts_country_max)")
        df_diff = conn.execute(f"""
            SELECT
                date,
                ROUND(daily_sum_score, 2) AS daily_sum_score,
                ROUND(daily_sum_ts_country_max, 2) AS daily_sum_ts_country_max,
                ROUND(daily_sum_score - daily_sum_ts_country_max, 2) AS diff,
                n_events,
                n_ts_country_groups,
                n_extreme
            FROM {VIEW_NAME}
            WHERE daily_sum_score > daily_sum_ts_country_max
            ORDER BY (daily_sum_score - daily_sum_ts_country_max) DESC
            LIMIT 10
        """).df()
        print(df_diff.to_string(index=False))
        print()

        print("=" * 100)
        print(f"✅ Vue {VIEW_NAME} prête pour les analyses robustes")
        print("=" * 100)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

