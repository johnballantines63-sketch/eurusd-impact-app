#!/usr/bin/env python3
"""
Création de la vue daily_news_score_v1
======================================

Basée sur:
- events_with_canonical_impact_scored_bucketed_v1

Agrège les scores d'événements par date (jour calendaire).

Colonnes:
- date
- n_events : nombre total d'événements du jour
- sum_score_impact_v1 : somme des scores
- max_score_impact_v1 : score max du jour
- avg_score_impact_v1 : moyenne des scores
- n_low, n_medium, n_high, n_extreme : comptage par bucket
- daily_news_score_v1 : score global du jour (somme pour V1)
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

BASE_VIEW = "events_with_canonical_impact_scored_bucketed_v1"
VIEW_NAME = "daily_news_score_v1"

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
SELECT
    DATE(ts_utc) AS date,
    
    -- Comptage global
    COUNT(*) AS n_events,
    
    -- Agrégations de score_impact_v1
    SUM(score_impact_v1) AS sum_score_impact_v1,
    MAX(score_impact_v1) AS max_score_impact_v1,
    AVG(score_impact_v1) AS avg_score_impact_v1,
    MEDIAN(score_impact_v1) AS p50_score_impact_v1,
    
    -- Comptage par bucket
    COUNT(CASE WHEN score_bucket_v1 = 'LOW' THEN 1 END) AS n_low,
    COUNT(CASE WHEN score_bucket_v1 = 'MEDIUM' THEN 1 END) AS n_medium,
    COUNT(CASE WHEN score_bucket_v1 = 'HIGH' THEN 1 END) AS n_high,
    COUNT(CASE WHEN score_bucket_v1 = 'EXTREME' THEN 1 END) AS n_extreme,
    
    -- Score global journalier (somme pour V1)
    SUM(score_impact_v1) AS daily_news_score_v1

FROM {BASE_VIEW}
GROUP BY DATE(ts_utc)
ORDER BY date
;
"""


def main():
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)

    print("=" * 80)
    print(f"CRÉATION / MISE À JOUR DE LA VUE {VIEW_NAME}")
    print("=" * 80)
    print(f"DB : {DB_PATH}")
    print()

    conn = duckdb.connect(str(DB_PATH), read_only=False)

    try:
        # 1) Création / remplacement de la vue
        print("🔧 Création de la vue daily news score...")
        conn.execute(CREATE_VIEW_SQL)
        print(f"   ✅ Vue {VIEW_NAME} créée / remplacée\n")

        # 2) Sanity-check : nombre de jours + stats
        print("📊 Sanity-check : nombre de jours et stats de daily_news_score_v1")
        df_stats = conn.execute(f"""
            SELECT
                COUNT(*) AS n_days,
                ROUND(MIN(daily_news_score_v1), 2) AS min_score,
                ROUND((SELECT daily_news_score_v1 FROM {VIEW_NAME} ORDER BY daily_news_score_v1 LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * 0.25 AS INTEGER) FROM {VIEW_NAME})), 2) AS p25_score,
                ROUND(MEDIAN(daily_news_score_v1), 2) AS p50_score,
                ROUND((SELECT daily_news_score_v1 FROM {VIEW_NAME} ORDER BY daily_news_score_v1 LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * 0.75 AS INTEGER) FROM {VIEW_NAME})), 2) AS p75_score,
                ROUND(MAX(daily_news_score_v1), 2) AS max_score,
                ROUND(AVG(daily_news_score_v1), 2) AS avg_score
            FROM {VIEW_NAME}
        """).df()
        print(df_stats.to_string(index=False))
        print()

        # 3) Stats sur nombre d'événements
        print("📊 Stats sur nombre d'événements par jour")
        df_events = conn.execute(f"""
            SELECT
                ROUND(MIN(n_events), 0) AS min_events,
                ROUND(MEDIAN(n_events), 0) AS p50_events,
                ROUND((SELECT n_events FROM {VIEW_NAME} ORDER BY n_events LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * 0.75 AS INTEGER) FROM {VIEW_NAME})), 0) AS p75_events,
                ROUND(MAX(n_events), 0) AS max_events,
                ROUND(AVG(n_events), 1) AS avg_events
            FROM {VIEW_NAME}
        """).df()
        print(df_events.to_string(index=False))
        print()

        # 4) Top 10 jours par score journalier
        print("📊 Top 10 jours par daily_news_score_v1")
        df_top = conn.execute(f"""
            SELECT
                date,
                n_events,
                ROUND(sum_score_impact_v1, 2) AS sum_score,
                ROUND(max_score_impact_v1, 2) AS max_score,
                n_low,
                n_medium,
                n_high,
                n_extreme,
                ROUND(daily_news_score_v1, 2) AS daily_news_score
            FROM {VIEW_NAME}
            ORDER BY daily_news_score_v1 DESC
            LIMIT 10
        """).df()
        print(df_top.to_string(index=False))
        print()

        print("=" * 80)
        print(f"✅ Vue {VIEW_NAME} prête pour l'analyse prédictive")
        print("=" * 80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
