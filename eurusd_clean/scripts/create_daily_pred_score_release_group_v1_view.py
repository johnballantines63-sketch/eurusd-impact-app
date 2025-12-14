#!/usr/bin/env python3
"""
Création de la vue daily_pred_score_release_group_v1
=====================================================

Agrège score_pred_v1 par release_group avant d'agréger par jour.

Étapes:
1. Joindre events_with_pred_score_v1 et events_with_release_group_v1
2. Calculer score_pred_release = MAX(score_pred_v1) par release_group_id_v1
3. Agréger par jour: pred_daily_release_sum, pred_daily_release_top20_sum, etc.
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

PRED_SCORE_VIEW = "events_with_pred_score_v1"
RELEASE_GROUP_VIEW = "events_with_release_group_v1"
VIEW_NAME = "daily_pred_score_release_group_v1"


def create_view(conn):
    """Crée la vue daily_pred_score_release_group_v1."""
    print(f"🔧 Création vue {VIEW_NAME}...")
    
    CREATE_VIEW_SQL = f"""
    CREATE OR REPLACE VIEW {VIEW_NAME} AS
    WITH release_events_ranked AS (
        -- Joindre pred_score et release_group + ranking intra-release
        SELECT
            r.release_group_id_v1,
            r.release_family_v1,
            DATE(r.ts_local) AS date,
            r.country,
            r.ts_local,
            p.score_pred_v1,
            ROW_NUMBER() OVER (
                PARTITION BY r.release_group_id_v1 
                ORDER BY p.score_pred_v1 DESC
            ) AS rn_in_release
        FROM {RELEASE_GROUP_VIEW} r
        INNER JOIN {PRED_SCORE_VIEW} p
            ON r.ts_local = p.ts_local
            AND r.country = p.country
            AND r.event_key = p.event_key
        WHERE p.score_pred_v1 IS NOT NULL
    ),
    release_scores AS (
        -- Calculer les 3 variantes d'agrégation intra-release
        SELECT
            release_group_id_v1,
            release_family_v1,
            date,
            country,
            ts_local,
            -- Variante 1: MAX
            MAX(score_pred_v1) AS score_release_max,
            -- Variante 2: SUM
            SUM(score_pred_v1) AS score_release_sum,
            -- Variante 3: TOP2-SUM
            SUM(CASE WHEN rn_in_release <= 2 THEN score_pred_v1 ELSE 0 END) AS score_release_top2
        FROM release_events_ranked
        GROUP BY 
            release_group_id_v1,
            release_family_v1,
            date,
            country,
            ts_local
    ),
    daily_release_ranked_max AS (
        SELECT
            date,
            release_group_id_v1,
            score_release_max,
            ROW_NUMBER() OVER (PARTITION BY date ORDER BY score_release_max DESC) AS rn_max
        FROM release_scores
    ),
    daily_release_ranked_sum AS (
        SELECT
            date,
            release_group_id_v1,
            score_release_sum,
            ROW_NUMBER() OVER (PARTITION BY date ORDER BY score_release_sum DESC) AS rn_sum
        FROM release_scores
    ),
    daily_release_ranked_top2 AS (
        SELECT
            date,
            release_group_id_v1,
            score_release_top2,
            ROW_NUMBER() OVER (PARTITION BY date ORDER BY score_release_top2 DESC) AS rn_top2
        FROM release_scores
    )
    SELECT
        rs.date,
        -- Métriques MAX (V2 actuel)
        SUM(rs.score_release_max) AS pred_daily_release_sum_max,
        SUM(CASE WHEN rn_max.rn_max <= 20 THEN rs.score_release_max END) AS pred_daily_release_top20_sum_max,
        -- Métriques SUM
        SUM(rs.score_release_sum) AS pred_daily_release_sum_sum,
        SUM(CASE WHEN rn_sum.rn_sum <= 20 THEN rs.score_release_sum END) AS pred_daily_release_top20_sum_sum,
        -- Métriques TOP2
        SUM(rs.score_release_top2) AS pred_daily_release_sum_top2,
        SUM(CASE WHEN rn_top2.rn_top2 <= 20 THEN rs.score_release_top2 END) AS pred_daily_release_top20_sum_top2,
        -- Nombre de release groups
        COUNT(DISTINCT rs.release_group_id_v1) AS n_release_groups
    FROM release_scores rs
    LEFT JOIN daily_release_ranked_max rn_max
        ON rs.release_group_id_v1 = rn_max.release_group_id_v1 AND rs.date = rn_max.date
    LEFT JOIN daily_release_ranked_sum rn_sum
        ON rs.release_group_id_v1 = rn_sum.release_group_id_v1 AND rs.date = rn_sum.date
    LEFT JOIN daily_release_ranked_top2 rn_top2
        ON rs.release_group_id_v1 = rn_top2.release_group_id_v1 AND rs.date = rn_top2.date
    GROUP BY rs.date
    ORDER BY rs.date
    """
    
    conn.execute(CREATE_VIEW_SQL)
    print(f"  ✅ Vue {VIEW_NAME} créée\n")


def sanity_checks(conn):
    """Vérifications de cohérence."""
    print("=" * 100)
    print("SANITY CHECKS")
    print("=" * 100)
    
    # 1. Nombre de dates
    n_dates = conn.execute(f"SELECT COUNT(DISTINCT date) FROM {VIEW_NAME}").fetchone()[0]
    print(f"📊 Nombre de dates: {n_dates}")
    
    # 2. Distribution des métriques (3 variantes)
    print("\n📊 Statistiques descriptives (3 variantes):")
    df_stats = conn.execute(f"""
        SELECT
            COUNT(*) AS n_days,
            ROUND(AVG(pred_daily_release_top20_sum_max), 2) AS avg_top20_max,
            ROUND(AVG(pred_daily_release_top20_sum_sum), 2) AS avg_top20_sum,
            ROUND(AVG(pred_daily_release_top20_sum_top2), 2) AS avg_top20_top2,
            ROUND(AVG(n_release_groups), 1) AS avg_n_release_groups
        FROM {VIEW_NAME}
    """).df()
    print(df_stats.to_string(index=False))
    
    # 3. Top 10 jours par chaque variante
    print("\n📊 Top 10 jours par variante MAX:")
    df_top_max = conn.execute(f"""
        SELECT
            date,
            ROUND(pred_daily_release_top20_sum_max, 2) AS top20_max,
            n_release_groups
        FROM {VIEW_NAME}
        ORDER BY pred_daily_release_top20_sum_max DESC
        LIMIT 10
    """).df()
    print(df_top_max.to_string(index=False))
    
    print("\n📊 Top 10 jours par variante SUM:")
    df_top_sum = conn.execute(f"""
        SELECT
            date,
            ROUND(pred_daily_release_top20_sum_sum, 2) AS top20_sum,
            n_release_groups
        FROM {VIEW_NAME}
        ORDER BY pred_daily_release_top20_sum_sum DESC
        LIMIT 10
    """).df()
    print(df_top_sum.to_string(index=False))
    
    print("\n📊 Top 10 jours par variante TOP2:")
    df_top_top2 = conn.execute(f"""
        SELECT
            date,
            ROUND(pred_daily_release_top20_sum_top2, 2) AS top20_top2,
            n_release_groups
        FROM {VIEW_NAME}
        ORDER BY pred_daily_release_top20_sum_top2 DESC
        LIMIT 10
    """).df()
    print(df_top_top2.to_string(index=False))
    
    print("\n" + "=" * 100)


def main():
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    try:
        print("=" * 100)
        print("CRÉATION DAILY_PRED_SCORE_RELEASE_GROUP_V1")
        print("=" * 100)
        print(f"DB : {DB_PATH}\n")
        
        # Créer vue
        create_view(conn)
        
        # Sanity checks
        sanity_checks(conn)
        
        print("\n✅ Vue daily_pred_score_release_group_v1 prête")
        print("=" * 100)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
