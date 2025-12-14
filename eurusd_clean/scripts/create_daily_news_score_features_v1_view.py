#!/usr/bin/env python3
"""
Création de la vue daily_news_score_features_v1
===============================================

Vue journalière FEATURE-READY pour modèles / dashboards.

Basée sur:
- daily_news_score_robust_v1

Objectif:
- Exposer uniquement les métriques robustes retenues
- Servir de base officielle pour SCORE_SPEC_V2
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

BASE_VIEW = "daily_news_score_robust_v1"
VIEW_NAME = "daily_news_score_features_v1"

CREATE_VIEW_SQL = f"""
CREATE OR REPLACE VIEW {VIEW_NAME} AS
SELECT
    date,

    -- 🎯 Métriques principales (robustes)
    daily_sum_ts_country_max,
    daily_top20_sum,

    -- 🔬 Indices de concentration
    top1_share_pct,
    top5_share_pct,

    -- 🧱 Structure des événements
    n_ts_country_groups,
    n_events,
    n_extreme,
    n_high,
    n_medium,
    n_low,

    -- 🧪 Debug / référence historique
    daily_sum_score

FROM {BASE_VIEW}
ORDER BY date;
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
        print("🔧 Création de la vue feature-ready...")
        conn.execute(CREATE_VIEW_SQL)
        print(f" ✅ Vue {VIEW_NAME} créée / remplacée\n")

        print("📊 Sanity-check : nombre de jours")
        df_count = conn.execute(f"SELECT COUNT(*) AS n FROM {VIEW_NAME}").df()
        n = int(df_count.iloc[0]["n"])
        print(f" → {n} jours dans {VIEW_NAME}\n")

        print("📊 Aperçu des features (TOP 10 par daily_top20_sum)")
        df_preview = conn.execute(f"""
            SELECT
                date,
                ROUND(daily_top20_sum, 2) AS daily_top20_sum,
                ROUND(daily_sum_ts_country_max, 2) AS daily_sum_ts_country_max,
                ROUND(top5_share_pct, 1) AS top5_share_pct,
                n_extreme,
                n_events
            FROM {VIEW_NAME}
            ORDER BY daily_top20_sum DESC
            LIMIT 10
        """).df()
        print(df_preview.to_string(index=False))
        print()

        print("📊 Statistiques globales sur les features")
        df_stats = conn.execute(f"""
            SELECT
                ROUND(AVG(daily_sum_ts_country_max), 2) AS avg_sum_robust,
                ROUND(MEDIAN(daily_sum_ts_country_max), 2) AS p50_sum_robust,
                ROUND(AVG(daily_top20_sum), 2) AS avg_top20_sum,
                ROUND(MEDIAN(daily_top20_sum), 2) AS p50_top20_sum,
                ROUND(AVG(top5_share_pct), 1) AS avg_top5_share,
                ROUND(AVG(n_extreme), 1) AS avg_n_extreme
            FROM {VIEW_NAME}
        """).df()
        print(df_stats.to_string(index=False))
        print()

        print("=" * 100)
        print(f"✅ Vue {VIEW_NAME} prête pour SCORE_SPEC_V2 / modèles")
        print("=" * 100)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

