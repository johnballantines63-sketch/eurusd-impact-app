#!/usr/bin/env python3
"""
Création de la vue events_with_pred_score_v1
=============================================

Vue avec score prédictif ex-ante (score_pred_v1) pour chaque événement.

Basée sur:
- events_with_ts_local_v1 (métadonnées événement)
- event_priors_rolling_v1 (priors historiques)

Formule V1:
- importance_component = COALESCE(importance_n, 1) / 5.0
- prior_component = LN(1 + COALESCE(prior_final_pips, 0.0))
- score_pred_v1 = importance_component * prior_component
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

EVENTS_VIEW = "events_with_ts_local_v1"
PRIORS_VIEW = "event_priors_rolling_v1"
VIEW_NAME = "events_with_pred_score_v1"

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
SELECT
    e.ts_local,
    e.ts_utc,  -- Conservé pour compatibilité
    e.country,
    e.event_key,
    e.event_title,
    e.importance_n,
    -- ⚠️ actual retiré (post-release, risque de leakage accidentel)
    e.estimate,
    e.forecast,
    e.previous,
    -- Priors
    p.prior_final_pips,
    p.prior_ekc_pips,
    p.prior_event_key_pips,
    p.prior_country_pips,
    p.ekc_n_past,
    p.event_key_n_past,
    p.country_n_past,
    p.global_n_past,
    -- Composantes du score
    COALESCE(e.importance_n, 1) / 5.0 AS importance_component,
    LN(1.0 + COALESCE(p.prior_final_pips, 0.0)) AS prior_component,
    -- Score prédictif ex-ante
    (COALESCE(e.importance_n, 1) / 5.0) * LN(1.0 + COALESCE(p.prior_final_pips, 0.0)) AS score_pred_v1
FROM {EVENTS_VIEW} e
LEFT JOIN {PRIORS_VIEW} p
    ON e.ts_local = p.ts_local
    AND e.country = p.country
    AND e.event_key = p.event_key
ORDER BY e.ts_local;
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
        print("🔧 Création de la vue avec score prédictif...")
        conn.execute(CREATE_VIEW_SQL)
        print(f" ✅ Vue {VIEW_NAME} créée / remplacée\n")

        # Sanity checks
        print("📊 Sanity-check : nombre de lignes")
        df_count = conn.execute(f"SELECT COUNT(*) AS n FROM {VIEW_NAME}").df()
        n = int(df_count.iloc[0]["n"])
        print(f" → {n} lignes dans {VIEW_NAME}\n")

        print("📊 Distribution du score_pred_v1")
        df_stats = conn.execute(f"""
            SELECT
                COUNT(*) AS n_total,
                COUNT(score_pred_v1) AS n_with_score,
                ROUND(MIN(score_pred_v1), 3) AS min_score,
                ROUND(MEDIAN(score_pred_v1), 3) AS p50_score,
                ROUND(MAX(score_pred_v1), 3) AS max_score
            FROM {VIEW_NAME}
            WHERE score_pred_v1 IS NOT NULL
        """).df()
        print(df_stats.to_string(index=False))
        print()

        print("📊 Top 10 événements par score_pred_v1 (dernières dates)")
        df_top = conn.execute(f"""
            SELECT
                ts_local,
                country,
                event_key,
                importance_n,
                ROUND(prior_final_pips, 2) AS prior_final_pips,
                ROUND(importance_component, 3) AS importance_component,
                ROUND(prior_component, 3) AS prior_component,
                ROUND(score_pred_v1, 3) AS score_pred_v1
            FROM {VIEW_NAME}
            WHERE score_pred_v1 IS NOT NULL
            ORDER BY ts_local DESC, score_pred_v1 DESC
            LIMIT 10
        """).df()
        print(df_top.to_string(index=False))
        print()

        print("=" * 100)
        print(f"✅ Vue {VIEW_NAME} prête (score prédictif ex-ante)")
        print("=" * 100)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

