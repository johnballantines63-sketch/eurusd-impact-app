#!/usr/bin/env python3
"""
Création de la vue events_with_ts_local_v1
===========================================

Vue alias propre pour éviter le nom toxique "ts_utc" alors que c'est en fait
du temps local (Europe/Zurich).

Basée sur:
- events_with_canonical_impact_scored_bucketed_v1

Objectif:
- Exposer ts_local = ts_utc pour arrêter de "penser UTC" partout
- Clarifier la sémantique réelle des timestamps
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

BASE_VIEW = "events_with_canonical_impact_scored_bucketed_v1"
VIEW_NAME = "events_with_ts_local_v1"

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
SELECT
    ts_utc AS ts_local,  -- ⚠️ Alias: ts_utc est en fait en Europe/Zurich (voir TIMEZONE_NOTE.md)
    ts_utc,  -- Conservé pour compatibilité
    country,
    event_key,
    event_title,
    importance_n,
    actual,
    estimate,
    forecast,
    previous,
    surprise_pct,
    impact_unified_pips,
    impact_unified_direction,
    impact_unified_time_to_peak_minutes,
    impact_unified_start_price,
    impact_unified_peak_price,
    impact_unified_quality,
    score_impact_v1,
    score_impact_signed_v1,
    score_bucket_v1
FROM {BASE_VIEW}
ORDER BY ts_local;
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
        print("🔧 Création de la vue avec alias ts_local...")
        conn.execute(CREATE_VIEW_SQL)
        print(f" ✅ Vue {VIEW_NAME} créée / remplacée\n")

        print("📊 Sanity-check : nombre de lignes")
        df_count = conn.execute(f"SELECT COUNT(*) AS n FROM {VIEW_NAME}").df()
        n = int(df_count.iloc[0]["n"])
        print(f" → {n} lignes dans {VIEW_NAME}\n")

        print("📊 Aperçu (TOP 5)")
        df_preview = conn.execute(f"""
            SELECT
                ts_local,
                country,
                event_key,
                ROUND(impact_unified_pips, 1) AS impact_unified_pips,
                score_bucket_v1
            FROM {VIEW_NAME}
            ORDER BY ts_local DESC
            LIMIT 5
        """).df()
        print(df_preview.to_string(index=False))
        print()

        print("=" * 100)
        print(f"✅ Vue {VIEW_NAME} prête (ts_local = ts_utc, sémantique clarifiée)")
        print("=" * 100)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

