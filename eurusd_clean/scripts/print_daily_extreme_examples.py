#!/usr/bin/env python3
"""
Exemples concrets de jours avec événements EXTREME
==================================================

Affiche des dates concrètes avec :
- Nombre d'événements EXTREME
- Score journalier
- Volatilité réalisée

Utile pour documentation / UI / exemples.
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

VOL_VIEW = "daily_eurusd_volatility_v1"
SCORE_VIEW = "daily_news_score_v1"


def main():
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)

    print("=" * 100)
    print("EXEMPLES CONCRETS - JOURS AVEC ÉVÉNEMENTS EXTREME")
    print("=" * 100)
    print()

    conn = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        # 1) Top 10 jours avec le plus d'événements EXTREME
        print("🏆 Top 10 jours par nombre d'événements EXTREME")
        df_top_extreme = conn.execute(f"""
            SELECT
                v.date,
                s.n_extreme,
                s.n_high,
                s.n_medium,
                s.n_low,
                s.n_events,
                ROUND(s.daily_news_score_v1, 2) AS daily_news_score,
                ROUND(v.daily_volatility_pips_v1, 1) AS daily_volatility_pips,
                ROUND(v.close_to_close_pips, 1) AS close_to_close_pips
            FROM {VOL_VIEW} v
            JOIN {SCORE_VIEW} s
                ON v.date = s.date
            WHERE s.n_extreme > 0
            ORDER BY s.n_extreme DESC, s.daily_news_score_v1 DESC
            LIMIT 10
        """).df()
        print(df_top_extreme.to_string(index=False))
        print()

        # 2) Top 10 jours EXTREME par volatilité réalisée
        print("📈 Top 10 jours avec EXTREME par volatilité réalisée")
        df_top_vol = conn.execute(f"""
            SELECT
                v.date,
                s.n_extreme,
                s.n_high,
                s.n_events,
                ROUND(s.daily_news_score_v1, 2) AS daily_news_score,
                ROUND(v.daily_volatility_pips_v1, 1) AS daily_volatility_pips,
                ROUND(v.close_to_close_pips, 1) AS close_to_close_pips
            FROM {VOL_VIEW} v
            JOIN {SCORE_VIEW} s
                ON v.date = s.date
            WHERE s.n_extreme > 0
            ORDER BY v.daily_volatility_pips_v1 DESC
            LIMIT 10
        """).df()
        print(df_top_vol.to_string(index=False))
        print()

        # 3) Exemples de jours avec 1 seul EXTREME (cas "propre")
        print("🎯 Exemples de jours avec exactement 1 événement EXTREME")
        df_single_extreme = conn.execute(f"""
            SELECT
                v.date,
                s.n_extreme,
                s.n_high,
                s.n_medium,
                s.n_low,
                s.n_events,
                ROUND(s.daily_news_score_v1, 2) AS daily_news_score,
                ROUND(v.daily_volatility_pips_v1, 1) AS daily_volatility_pips,
                ROUND(v.close_to_close_pips, 1) AS close_to_close_pips
            FROM {VOL_VIEW} v
            JOIN {SCORE_VIEW} s
                ON v.date = s.date
            WHERE s.n_extreme = 1
            ORDER BY v.daily_volatility_pips_v1 DESC
            LIMIT 10
        """).df()
        print(df_single_extreme.to_string(index=False))
        print()

        # 4) Exemples de jours avec 2+ EXTREME (journées "chargées")
        print("⚡ Exemples de jours avec 2+ événements EXTREME (journées chargées)")
        df_multi_extreme = conn.execute(f"""
            SELECT
                v.date,
                s.n_extreme,
                s.n_high,
                s.n_medium,
                s.n_low,
                s.n_events,
                ROUND(s.daily_news_score_v1, 2) AS daily_news_score,
                ROUND(v.daily_volatility_pips_v1, 1) AS daily_volatility_pips,
                ROUND(v.close_to_close_pips, 1) AS close_to_close_pips
            FROM {VOL_VIEW} v
            JOIN {SCORE_VIEW} s
                ON v.date = s.date
            WHERE s.n_extreme >= 2
            ORDER BY s.n_extreme DESC, v.daily_volatility_pips_v1 DESC
            LIMIT 10
        """).df()
        print(df_multi_extreme.to_string(index=False))
        print()

        print("=" * 100)
        print("✅ Exemples générés")
        print("=" * 100)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

