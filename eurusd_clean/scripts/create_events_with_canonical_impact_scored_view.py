#!/usr/bin/env python3
"""
Création de la vue scored events_with_canonical_impact_scored_v1
================================================================

Basée sur:
- events_with_canonical_impact_v1 (vue canonique)

Ajoute:
- score_impact_v1          : score scalaire (magnitude)
- score_impact_signed_v1   : score avec signe (UP/DOWN)
- colonnes intermédiaires pour debugging (base, poids, facteur surprise)
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

BASE_VIEW = "events_with_canonical_impact_v1"
VIEW_NAME = "events_with_canonical_impact_scored_v1"

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
SELECT
    v.*,

    -- Base: impact en pips, compressé par log
    ln(1.0 + v.impact_unified_pips) AS impact_score_base,

    -- Poids d'importance (1 à 5, normalisé sur [0.2, 1.0])
    COALESCE(v.importance_n, 1)::DOUBLE / 5.0 AS importance_weight,

    -- Surprise en valeur absolue, cappée à 5
    LEAST(ABS(COALESCE(v.surprise_pct, 0.0)), 5.0) AS surprise_abs_capped,

    -- Facteur multiplicatif de surprise (ex: 0% -> 1.0, 2% -> 1.2, 5%+ -> 1.5)
    1.0 + 0.1 * LEAST(ABS(COALESCE(v.surprise_pct, 0.0)), 5.0) AS surprise_factor,

    -- Score scalaire (magnitude uniquement)
    ln(1.0 + v.impact_unified_pips)
        * (COALESCE(v.importance_n, 1)::DOUBLE / 5.0)
        * (1.0 + 0.1 * LEAST(ABS(COALESCE(v.surprise_pct, 0.0)), 5.0))
        AS score_impact_v1,

    -- Score signé (UP vs DOWN)
    CASE
        WHEN v.impact_unified_direction = 1 THEN
            ln(1.0 + v.impact_unified_pips)
                * (COALESCE(v.importance_n, 1)::DOUBLE / 5.0)
                * (1.0 + 0.1 * LEAST(ABS(COALESCE(v.surprise_pct, 0.0)), 5.0))
        WHEN v.impact_unified_direction = -1 THEN
            - ln(1.0 + v.impact_unified_pips)
                * (COALESCE(v.importance_n, 1)::DOUBLE / 5.0)
                * (1.0 + 0.1 * LEAST(ABS(COALESCE(v.surprise_pct, 0.0)), 5.0))
        ELSE NULL
    END AS score_impact_signed_v1

FROM {BASE_VIEW} v
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
        print("🔧 Création de la vue scored...")
        conn.execute(CREATE_VIEW_SQL)
        print(f"   ✅ Vue {VIEW_NAME} créée / remplacée\n")

        # 2) Sanity-check rapide : nombre de lignes
        print("📊 Sanity-check : nombre de lignes dans la vue")
        df_count = conn.execute(f"SELECT COUNT(*) AS n FROM {VIEW_NAME}").df()
        n = int(df_count.iloc[0]["n"])
        print(f"   → {n} lignes dans {VIEW_NAME}\n")

        # 3) Distribution du score
        print("📊 Distribution globale de score_impact_v1")
        # DuckDB utilise MEDIAN() et on calcule les autres percentiles via des sous-requêtes
        df_stats = conn.execute(f"""
            SELECT
                ROUND(MIN(score_impact_v1), 3) AS min_score,
                ROUND((SELECT score_impact_v1 FROM {VIEW_NAME} ORDER BY score_impact_v1 LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * 0.25 AS INTEGER) FROM {VIEW_NAME})), 3) AS p25_score,
                ROUND(MEDIAN(score_impact_v1), 3) AS p50_score,
                ROUND((SELECT score_impact_v1 FROM {VIEW_NAME} ORDER BY score_impact_v1 LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * 0.75 AS INTEGER) FROM {VIEW_NAME})), 3) AS p75_score,
                ROUND(MAX(score_impact_v1), 3) AS max_score,
                ROUND(AVG(score_impact_v1), 3) AS avg_score
            FROM {VIEW_NAME}
        """).df()
        print(df_stats.to_string(index=False))
        print()

        # 4) Top 10 événements par score
        print("📊 Top 10 événements par score_impact_v1")
        df_top = conn.execute(f"""
            SELECT
                ts_utc,
                country,
                event_key,
                importance_n,
                surprise_pct,
                impact_unified_pips,
                impact_unified_direction,
                score_impact_v1
            FROM {VIEW_NAME}
            ORDER BY score_impact_v1 DESC
            LIMIT 10
        """).df()
        print(df_top.to_string(index=False))
        print()

        print("=" * 80)
        print(f"✅ Vue {VIEW_NAME} prête pour analyses & modèles")
        print("=" * 80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
