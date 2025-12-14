#!/usr/bin/env python3
"""
Création de la vue canonique events_with_canonical_impact_v1
=============================================================

Vue basée sur:
- table events (fondamental)
- table event_impacts_v2 (impact_unified_*)

Objectif:
- Fournir un dataset unique, propre et prêt pour le scoring / les modèles.
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"


VIEW_NAME = "events_with_canonical_impact_v1"


CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
SELECT
    e.ts_utc,
    e.country,
    e.event_key,
    e.event_title,
    e.importance_n,
    e.actual,
    e.estimate,
    e.forecast,
    e.previous,
    e.unit,
    e.type,
    e.label,
    e.comparison,
    e.period,
    e.change,
    e.change_percentage,
    e.event_type,
    
    -- Surprise depuis event_impacts_v2 (si disponible)
    ei.surprise_pct,
    
    -- Impact canonique (IMPACT_SPEC_V1)
    ei.impact_unified_pips,
    ei.impact_unified_direction,
    CASE
        WHEN ei.impact_unified_direction = 1 THEN  ei.impact_unified_pips
        WHEN ei.impact_unified_direction = -1 THEN -ei.impact_unified_pips
        ELSE NULL
    END AS impact_unified_signed_pips,
    ei.impact_unified_time_to_peak_minutes,
    ei.impact_unified_start_price,
    ei.impact_unified_peak_price,
    ei.impact_unified_quality

FROM events e
LEFT JOIN event_impacts_v2 ei
    ON e.ts_utc = ei.ts_utc
   AND e.country = ei.country

-- On ne garde que les événements pour lesquels on dispose d'un impact canonique
WHERE ei.impact_unified_pips IS NOT NULL
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
        print("🔧 Création de la vue...")
        conn.execute(CREATE_VIEW_SQL)
        print(f"   ✅ Vue {VIEW_NAME} créée / remplacée\n")

        # 2) Sanity-check rapide : nombre de lignes
        print("📊 Sanity-check : nombre de lignes dans la vue")
        df_count = conn.execute(f"SELECT COUNT(*) AS n FROM {VIEW_NAME}").df()
        n = int(df_count.iloc[0]["n"])
        print(f"   → {n} lignes dans {VIEW_NAME}\n")

        # 3) Distribution par pays (top 10)
        print("📊 Distribution par pays (TOP 10)")
        df_by_country = conn.execute(f"""
            SELECT
                country,
                COUNT(*) AS n,
                ROUND(AVG(impact_unified_pips), 1) AS avg_unified,
                ROUND(MEDIAN(impact_unified_pips), 1) AS p50_unified,
                ROUND(MAX(impact_unified_pips), 1) AS max_unified
            FROM {VIEW_NAME}
            GROUP BY country
            ORDER BY n DESC
            LIMIT 10
        """).df()
        print(df_by_country.to_string(index=False))
        print()

        # 4) Aperçu des plus gros impacts
        print("📊 Top 10 événements par impact_unified_pips")
        df_top = conn.execute(f"""
            SELECT
                ts_utc,
                event_key,
                country,
                impact_unified_pips,
                impact_unified_direction,
                impact_unified_time_to_peak_minutes,
                impact_unified_quality
            FROM {VIEW_NAME}
            ORDER BY impact_unified_pips DESC
            LIMIT 10
        """).df()
        print(df_top.to_string(index=False))
        print()

        print("=" * 80)
        print(f"✅ Vue {VIEW_NAME} prête pour le scoring / les modèles")
        print("=" * 80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
