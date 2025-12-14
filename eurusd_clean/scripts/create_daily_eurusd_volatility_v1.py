#!/usr/bin/env python3
"""
Création de la vue daily_eurusd_volatility_v1
=============================================

Basée sur:
- prices_finnhub_m1 (EURUSD, Bern time)

Définitions VOL_SPEC_V1:
- day_open  : premier prix du jour
- day_close : dernier prix du jour
- day_high  : max(high)
- day_low   : min(low)
- range_pips           = (day_high - day_low) * 10000
- close_to_close_pips  = ABS(day_close - day_open) * 10000
- daily_volatility_pips_v1 = range_pips
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

VIEW_NAME = "daily_eurusd_volatility_v1"

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
WITH daily_prices AS (
    SELECT
        DATE(datetime) AS date,
        datetime,
        open,
        high,
        low,
        close,
        ROW_NUMBER() OVER (PARTITION BY DATE(datetime) ORDER BY datetime ASC) AS rn_first,
        ROW_NUMBER() OVER (PARTITION BY DATE(datetime) ORDER BY datetime DESC) AS rn_last
    FROM prices_finnhub_m1
),
first_last AS (
    SELECT
        date,
        MAX(CASE WHEN rn_first = 1 THEN open END) AS day_open,
        MAX(CASE WHEN rn_last = 1 THEN close END) AS day_close,
        MAX(high) AS day_high,
        MIN(low) AS day_low
    FROM daily_prices
    GROUP BY date
)
SELECT
    date,
    day_open,
    day_close,
    day_high,
    day_low,
    (day_high - day_low) * 10000.0 AS range_pips,
    ABS(day_close - day_open) * 10000.0 AS close_to_close_pips,
    (day_high - day_low) * 10000.0 AS daily_volatility_pips_v1
FROM first_last
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
        print("🔧 Création de la vue daily volatility...")
        conn.execute(CREATE_VIEW_SQL)
        print(f"   ✅ Vue {VIEW_NAME} créée / remplacée\n")

        # 2) Sanity-check : nombre de jours + quelques stats
        print("📊 Sanity-check : nombre de jours et stats de range_pips")
        df_stats = conn.execute(f"""
            SELECT
                COUNT(*) AS n_days,
                ROUND(MIN(range_pips), 1) AS min_range,
                ROUND((SELECT range_pips FROM {VIEW_NAME} ORDER BY range_pips LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * 0.25 AS INTEGER) FROM {VIEW_NAME})), 1) AS p25_range,
                ROUND(MEDIAN(range_pips), 1) AS p50_range,
                ROUND((SELECT range_pips FROM {VIEW_NAME} ORDER BY range_pips LIMIT 1 OFFSET (SELECT CAST(COUNT(*) * 0.75 AS INTEGER) FROM {VIEW_NAME})), 1) AS p75_range,
                ROUND(MAX(range_pips), 1) AS max_range,
                ROUND(AVG(range_pips), 1) AS avg_range
            FROM {VIEW_NAME}
        """).df()
        print(df_stats.to_string(index=False))
        print()

        # 3) Aperçu de quelques jours extrêmes
        print("📊 Top 5 jours les plus volatils (range_pips)")
        df_top = conn.execute(f"""
            SELECT
                date,
                range_pips,
                close_to_close_pips,
                day_high,
                day_low
            FROM {VIEW_NAME}
            ORDER BY range_pips DESC
            LIMIT 5
        """).df()
        print(df_top.to_string(index=False))
        print()

        print("=" * 80)
        print(f"✅ Vue {VIEW_NAME} prête pour les analyses quotidiennes")
        print("=" * 80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
