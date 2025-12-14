#!/usr/bin/env python3
"""
Création de la vue events_with_canonical_impact_scored_bucketed_v1
==================================================================

Basée sur:
- events_with_canonical_impact_scored_v1

Ajoute:
- score_bucket_v1 : {LOW, MEDIUM, HIGH, EXTREME} selon SCORE_SPEC_V1
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

BASE_VIEW = "events_with_canonical_impact_scored_v1"
VIEW_NAME = "events_with_canonical_impact_scored_bucketed_v1"

# Seuils figés selon SCORE_SPEC_V1
P50 = 2.326
P75 = 2.845
P90 = 3.286

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
SELECT
    s.*,
    CASE
        WHEN s.score_impact_v1 < {P50} THEN 'LOW'
        WHEN s.score_impact_v1 < {P75} THEN 'MEDIUM'
        WHEN s.score_impact_v1 < {P90} THEN 'HIGH'
        ELSE 'EXTREME'
    END AS score_bucket_v1
FROM {BASE_VIEW} s
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
        print("🔧 Création de la vue bucketée...")
        conn.execute(CREATE_VIEW_SQL)
        print(f"   ✅ Vue {VIEW_NAME} créée / remplacée\n")

        # 2) Sanity-check rapide : nombre de lignes
        print("📊 Sanity-check : nombre de lignes dans la vue")
        df_count = conn.execute(f"SELECT COUNT(*) AS n FROM {VIEW_NAME}").df()
        n = int(df_count.iloc[0]["n"])
        print(f"   → {n} lignes dans {VIEW_NAME}\n")

        # 3) Distribution par bucket
        print("📊 Distribution par score_bucket_v1")
        df_buckets = conn.execute(f"""
            SELECT
                score_bucket_v1,
                COUNT(*) AS n,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct,
                ROUND(AVG(score_impact_v1), 3) AS avg_score,
                ROUND(MEDIAN(score_impact_v1), 3) AS p50_score,
                ROUND(AVG(impact_unified_pips), 1) AS avg_impact,
                ROUND(MEDIAN(impact_unified_pips), 1) AS p50_impact,
                ROUND(MAX(impact_unified_pips), 1) AS max_impact
            FROM {VIEW_NAME}
            GROUP BY score_bucket_v1
            ORDER BY
                CASE score_bucket_v1
                    WHEN 'LOW' THEN 1
                    WHEN 'MEDIUM' THEN 2
                    WHEN 'HIGH' THEN 3
                    WHEN 'EXTREME' THEN 4
                    ELSE 5
                END
        """).df()
        print(df_buckets.to_string(index=False))
        print()

        print("=" * 80)
        print(f"✅ Vue {VIEW_NAME} prête (avec score_bucket_v1)")
        print("=" * 80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
