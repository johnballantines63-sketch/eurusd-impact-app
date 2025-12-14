#!/usr/bin/env python3
"""
Analyse de la composition du score journalier pour une date donnée
===================================================================

Objectif:
- Lister les top événements par score_impact_v1 pour une date
- Analyser la répartition par country et event_key
- Détecter les duplications potentielles (même ts_utc/country)
- Calculer la contribution du top 1 / top 5 / top 20 au score total

Usage:
    python3 scripts/explain_day_score_composition.py --date 2024-08-15
    python3 scripts/explain_day_score_composition.py --date 2025-04-03
"""

import sys
from pathlib import Path
import duckdb
import argparse

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

VIEW_NAME = "events_with_canonical_impact_scored_bucketed_v1"


def analyze_date(date_str: str, top_n: int = 20):
    """Analyse la composition du score pour une date donnée."""
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)

    conn = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        # 1) Vérifier que la date existe
        df_check = conn.execute(f"""
            SELECT COUNT(*) AS n
            FROM {VIEW_NAME}
            WHERE DATE(ts_utc) = DATE(?)
        """, [date_str]).df()
        
        n_events = int(df_check.iloc[0]["n"])
        if n_events == 0:
            print(f"❌ Aucun événement trouvé pour la date {date_str}")
            return
        
        print("=" * 100)
        print(f"ANALYSE COMPOSITION SCORE JOURNALIER - {date_str}")
        print("=" * 100)
        print(f"Nombre total d'événements : {n_events}")
        print()

        # 2) Score journalier total
        df_total = conn.execute(f"""
            SELECT
                SUM(score_impact_v1) AS total_score,
                MAX(score_impact_v1) AS max_score,
                AVG(score_impact_v1) AS avg_score,
                COUNT(*) AS n_events,
                COUNT(CASE WHEN score_bucket_v1 = 'EXTREME' THEN 1 END) AS n_extreme,
                COUNT(CASE WHEN score_bucket_v1 = 'HIGH' THEN 1 END) AS n_high,
                COUNT(CASE WHEN score_bucket_v1 = 'MEDIUM' THEN 1 END) AS n_medium,
                COUNT(CASE WHEN score_bucket_v1 = 'LOW' THEN 1 END) AS n_low
            FROM {VIEW_NAME}
            WHERE DATE(ts_utc) = DATE(?)
        """, [date_str]).df()
        
        total_score = float(df_total.iloc[0]["total_score"])
        print("📊 Score journalier global")
        print(df_total.to_string(index=False))
        print()

        # 3) Top N événements par score
        print(f"🏆 Top {top_n} événements par score_impact_v1")
        df_top = conn.execute(f"""
            SELECT
                ts_utc,
                country,
                event_key,
                event_title,
                importance_n,
                surprise_pct,
                impact_unified_pips,
                impact_unified_direction,
                score_impact_v1,
                score_bucket_v1
            FROM {VIEW_NAME}
            WHERE DATE(ts_utc) = DATE(?)
            ORDER BY score_impact_v1 DESC
            LIMIT ?
        """, [date_str, top_n]).df()
        
        print(df_top.to_string(index=False))
        print()

        # 4) Contribution du top 1 / top 5 / top 20
        print("📈 Contribution cumulative au score total")
        df_contrib = conn.execute(f"""
            WITH ranked AS (
                SELECT
                    score_impact_v1,
                    ROW_NUMBER() OVER (ORDER BY score_impact_v1 DESC) AS rn
                FROM {VIEW_NAME}
                WHERE DATE(ts_utc) = DATE(?)
            )
            SELECT
                SUM(CASE WHEN rn <= 1 THEN score_impact_v1 END) AS top1_score,
                SUM(CASE WHEN rn <= 5 THEN score_impact_v1 END) AS top5_score,
                SUM(CASE WHEN rn <= 20 THEN score_impact_v1 END) AS top20_score,
                SUM(score_impact_v1) AS total_score
            FROM ranked
        """, [date_str]).df()
        
        row = df_contrib.iloc[0]
        total = float(row["total_score"])
        top1 = float(row["top1_score"]) if row["top1_score"] is not None else 0.0
        top5 = float(row["top5_score"]) if row["top5_score"] is not None else 0.0
        top20 = float(row["top20_score"]) if row["top20_score"] is not None else 0.0
        
        print(f"   Top 1  : {top1:.2f} ({100*top1/total:.1f}% du total)")
        print(f"   Top 5  : {top5:.2f} ({100*top5/total:.1f}% du total)")
        print(f"   Top 20 : {top20:.2f} ({100*top20/total:.1f}% du total)")
        print(f"   Total  : {total:.2f}")
        print()

        # 5) Répartition par country
        print("🌍 Répartition par pays")
        df_country = conn.execute(f"""
            SELECT
                country,
                COUNT(*) AS n_events,
                COUNT(CASE WHEN score_bucket_v1 = 'EXTREME' THEN 1 END) AS n_extreme,
                SUM(score_impact_v1) AS sum_score,
                ROUND(AVG(score_impact_v1), 2) AS avg_score,
                ROUND(MAX(score_impact_v1), 2) AS max_score
            FROM {VIEW_NAME}
            WHERE DATE(ts_utc) = DATE(?)
            GROUP BY country
            ORDER BY sum_score DESC
        """, [date_str]).df()
        print(df_country.to_string(index=False))
        print()

        # 6) Répartition par event_key (top 10)
        print("📋 Répartition par type d'événement (TOP 10)")
        df_event_key = conn.execute(f"""
            SELECT
                event_key,
                COUNT(*) AS n_events,
                COUNT(CASE WHEN score_bucket_v1 = 'EXTREME' THEN 1 END) AS n_extreme,
                SUM(score_impact_v1) AS sum_score,
                ROUND(AVG(score_impact_v1), 2) AS avg_score,
                ROUND(MAX(score_impact_v1), 2) AS max_score
            FROM {VIEW_NAME}
            WHERE DATE(ts_utc) = DATE(?)
            GROUP BY event_key
            ORDER BY sum_score DESC
            LIMIT 10
        """, [date_str]).df()
        print(df_event_key.to_string(index=False))
        print()

        # 7) Diagnostic duplicats (même ts_utc + country)
        print("🔍 Diagnostic duplicats potentiels (même ts_utc + country)")
        df_dups = conn.execute(f"""
            WITH grouped AS (
                SELECT
                    ts_utc,
                    country,
                    COUNT(*) AS n_duplicates,
                    STRING_AGG(DISTINCT event_key, ', ') AS event_keys,
                    SUM(score_impact_v1) AS sum_score_dups
                FROM {VIEW_NAME}
                WHERE DATE(ts_utc) = DATE(?)
                GROUP BY ts_utc, country
                HAVING COUNT(*) > 1
            )
            SELECT
                ts_utc,
                country,
                n_duplicates,
                event_keys,
                ROUND(sum_score_dups, 2) AS sum_score
            FROM grouped
            ORDER BY n_duplicates DESC, sum_score DESC
            LIMIT 10
        """, [date_str]).df()
        
        if df_dups.empty:
            print("   ✅ Aucun doublon détecté (ts_utc + country unique)")
        else:
            print(f"   ⚠️  {len(df_dups)} groupes de doublons détectés")
            print(df_dups.to_string(index=False))
        print()

        # 8) Volatilité du jour (si disponible)
        print("📊 Volatilité réalisée du jour")
        df_vol = conn.execute(f"""
            SELECT
                date,
                daily_volatility_pips_v1,
                close_to_close_pips,
                range_pips
            FROM daily_eurusd_volatility_v1
            WHERE date = DATE(?)
        """, [date_str]).df()
        
        if df_vol.empty:
            print("   ⚠️  Volatilité non disponible pour cette date")
        else:
            print(df_vol.to_string(index=False))
        print()

        print("=" * 100)
        print("✅ Analyse terminée")
        print("=" * 100)

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Analyse la composition du score journalier pour une date donnée"
    )
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date à analyser (format: YYYY-MM-DD)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Nombre d'événements top à afficher (défaut: 20)",
    )
    
    args = parser.parse_args()
    analyze_date(args.date, args.top_n)


if __name__ == "__main__":
    main()

