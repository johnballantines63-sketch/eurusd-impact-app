#!/usr/bin/env python3
"""
Création de la vue event_priors_rolling_v1
===========================================

Vue avec priors rolling (expanding mean + shrinkage) pour chaque événement.

Basée sur:
- events_with_ts_local_v1 (pour ts_local, country, event_key, importance_n)
- events_with_canonical_impact_v1 (pour impact_unified_pips historique)

Règles:
- Rolling strict < t (window functions avec frame)
- Shrinkage avec m=20 vers global_mean
- Hiérarchie: (event_key, country) > event_key > country > global
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

EVENTS_VIEW = "events_with_ts_local_v1"
IMPACT_VIEW = "events_with_canonical_impact_v1"
VIEW_NAME = "event_priors_rolling_v1"

M_SHRINKAGE = 20  # pseudo-count pour shrinkage

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
WITH events_dedup AS (
    -- Déduplication côté events (un seul event par ts_local+country+event_key)
    SELECT
        ts_local, country, event_key, importance_n
    FROM (
        SELECT
            ts_local, country, event_key, importance_n,
            ROW_NUMBER() OVER (PARTITION BY ts_local, country, event_key ORDER BY event_title) AS rn
        FROM {EVENTS_VIEW}
    )
    WHERE rn = 1
),
impact_dedup AS (
    -- Déduplication côté impact (un seul impact par ts_utc+country+event_key)
    SELECT
        ts_utc, country, event_key, impact_unified_pips
    FROM (
        SELECT
            ts_utc, country, event_key, impact_unified_pips,
            ROW_NUMBER() OVER (PARTITION BY ts_utc, country, event_key ORDER BY ts_utc) AS rn
        FROM {IMPACT_VIEW}
    )
    WHERE rn = 1
),
base AS (
    SELECT
        e.ts_local,
        e.country,
        e.event_key,
        e.importance_n,
        ei.impact_unified_pips
    FROM events_dedup e
    LEFT JOIN impact_dedup ei
        ON e.ts_local = ei.ts_utc
        AND e.country = ei.country
        AND e.event_key = ei.event_key
    -- ⚠️ IMPORTANT: On inclut TOUS les événements (même sans impact_unified_pips)
    -- pour garantir que les priors sont calculables ex-ante pour tous
),
-- Calculs rolling avec frame strict < t
rolling_stats AS (
    SELECT
        ts_local,
        country,
        event_key,
        importance_n,
        impact_unified_pips,
        -- Global stats (toutes observations < t)
        AVG(impact_unified_pips) OVER (
            ORDER BY ts_local
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS global_mean_past,
        COUNT(impact_unified_pips) OVER (
            ORDER BY ts_local
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS global_n_past,
        -- Event key stats (< t)
        AVG(impact_unified_pips) OVER (
            PARTITION BY event_key
            ORDER BY ts_local
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS event_key_mean_past,
        COUNT(impact_unified_pips) OVER (
            PARTITION BY event_key
            ORDER BY ts_local
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS event_key_n_past,
        -- Country stats (< t)
        AVG(impact_unified_pips) OVER (
            PARTITION BY country
            ORDER BY ts_local
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS country_mean_past,
        COUNT(impact_unified_pips) OVER (
            PARTITION BY country
            ORDER BY ts_local
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS country_n_past,
        -- Event key + Country stats (< t)
        AVG(impact_unified_pips) OVER (
            PARTITION BY event_key, country
            ORDER BY ts_local
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS ekc_mean_past,
        COUNT(impact_unified_pips) OVER (
            PARTITION BY event_key, country
            ORDER BY ts_local
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS ekc_n_past
    FROM base
)
-- Shrinkage avec m={M_SHRINKAGE}
SELECT
    ts_local,
    country,
    event_key,
    importance_n,
    impact_unified_pips,
    -- Shrinkage: shrunk_mean = (n * mean + m * global_mean) / (n + m)
    CASE
        WHEN ekc_n_past > 0 AND global_mean_past IS NOT NULL THEN
            (ekc_n_past * ekc_mean_past + {M_SHRINKAGE} * global_mean_past) / (ekc_n_past + {M_SHRINKAGE})
        ELSE NULL
    END AS prior_ekc_pips,
    CASE
        WHEN event_key_n_past > 0 AND global_mean_past IS NOT NULL THEN
            (event_key_n_past * event_key_mean_past + {M_SHRINKAGE} * global_mean_past) / (event_key_n_past + {M_SHRINKAGE})
        ELSE NULL
    END AS prior_event_key_pips,
    CASE
        WHEN country_n_past > 0 AND global_mean_past IS NOT NULL THEN
            (country_n_past * country_mean_past + {M_SHRINKAGE} * global_mean_past) / (country_n_past + {M_SHRINKAGE})
        ELSE NULL
    END AS prior_country_pips,
    -- Prior final (hiérarchie)
    COALESCE(
        CASE
            WHEN ekc_n_past > 0 AND global_mean_past IS NOT NULL THEN
                (ekc_n_past * ekc_mean_past + {M_SHRINKAGE} * global_mean_past) / (ekc_n_past + {M_SHRINKAGE})
            ELSE NULL
        END,
        CASE
            WHEN event_key_n_past > 0 AND global_mean_past IS NOT NULL THEN
                (event_key_n_past * event_key_mean_past + {M_SHRINKAGE} * global_mean_past) / (event_key_n_past + {M_SHRINKAGE})
            ELSE NULL
        END,
        CASE
            WHEN country_n_past > 0 AND global_mean_past IS NOT NULL THEN
                (country_n_past * country_mean_past + {M_SHRINKAGE} * global_mean_past) / (country_n_past + {M_SHRINKAGE})
            ELSE NULL
        END,
        global_mean_past
    ) AS prior_final_pips,
    -- N past (pour debug)
    ekc_n_past,
    event_key_n_past,
    country_n_past,
    global_n_past,
    global_mean_past
FROM rolling_stats
ORDER BY ts_local;
"""


def main():
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)

    print("=" * 100)
    print(f"CRÉATION / MISE À JOUR DE LA VUE {VIEW_NAME}")
    print("=" * 100)
    print(f"DB : {DB_PATH}")
    print(f"M (shrinkage) : {M_SHRINKAGE}")
    print()

    conn = duckdb.connect(str(DB_PATH), read_only=False)

    try:
        print("🔧 Création de la vue avec priors rolling...")
        conn.execute(CREATE_VIEW_SQL)
        print(f" ✅ Vue {VIEW_NAME} créée / remplacée\n")

        # Sanity checks
        print("📊 Sanity-check : nombre de lignes")
        df_count = conn.execute(f"SELECT COUNT(*) AS n FROM {VIEW_NAME}").df()
        n = int(df_count.iloc[0]["n"])
        print(f" → {n} lignes dans {VIEW_NAME}\n")

        print("📊 Vérification : premières dates (doivent avoir prior NULL)")
        df_first = conn.execute(f"""
            SELECT
                ts_local,
                country,
                event_key,
                prior_final_pips,
                global_n_past
            FROM {VIEW_NAME}
            ORDER BY ts_local
            LIMIT 5
        """).df()
        print(df_first.to_string(index=False))
        print()

        print("📊 Vérification : lignes récentes avec priors")
        df_recent = conn.execute(f"""
            SELECT
                ts_local,
                country,
                event_key,
                ROUND(prior_final_pips, 2) AS prior_final_pips,
                ekc_n_past,
                event_key_n_past,
                country_n_past,
                global_n_past
            FROM {VIEW_NAME}
            WHERE prior_final_pips IS NOT NULL
            ORDER BY ts_local DESC
            LIMIT 5
        """).df()
        print(df_recent.to_string(index=False))
        print()

        print("📊 Statistiques sur les priors")
        df_stats = conn.execute(f"""
            SELECT
                COUNT(*) AS n_total,
                COUNT(prior_final_pips) AS n_with_prior,
                ROUND(AVG(prior_final_pips), 2) AS avg_prior,
                ROUND(MEDIAN(prior_final_pips), 2) AS p50_prior,
                ROUND(MAX(prior_final_pips), 2) AS max_prior
            FROM {VIEW_NAME}
            WHERE prior_final_pips IS NOT NULL
        """).df()
        print(df_stats.to_string(index=False))
        print()

        print("=" * 100)
        print(f"✅ Vue {VIEW_NAME} prête (rolling strict < t, shrinkage m={M_SHRINKAGE})")
        print("=" * 100)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

