#!/usr/bin/env python3
"""
Ranking des événements par impact canonique
============================================

Affiche un ranking des événements par impact_unified_pips.
Permet de filtrer par pays, type d'événement, etc.
"""

import sys
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"


def rank_events(
    conn: duckdb.DuckDBPyConnection,
    limit: int = 20,
    country: Optional[str] = None,
    event_key_filter: Optional[str] = None,
    min_impact: Optional[float] = None,
) -> pd.DataFrame:
    """
    Génère un ranking des événements par impact_unified_pips.
    
    Args:
        conn: Connexion DuckDB
        limit: Nombre d'événements à retourner
        country: Filtrer par pays (ex: 'US')
        event_key_filter: Filtrer par type d'événement (ex: 'non farm payrolls')
        min_impact: Impact minimal (pips)
    
    Returns:
        DataFrame avec les événements triés par impact décroissant
    """
    query = """
        SELECT 
            ts_utc,
            event_key,
            country,
            impact_unified_pips,
            impact_unified_direction,
            impact_unified_quality,
            impact_unified_time_to_peak_minutes
        FROM event_impacts_v2
        WHERE impact_unified_pips IS NOT NULL
    """
    params = []
    
    if country:
        query += " AND country = ?"
        params.append(country)
    
    if event_key_filter:
        query += " AND LOWER(event_key) LIKE ?"
        params.append(f"%{event_key_filter.lower()}%")
    
    if min_impact is not None:
        query += " AND impact_unified_pips >= ?"
        params.append(min_impact)
    
    query += " ORDER BY impact_unified_pips DESC LIMIT ?"
    params.append(limit)
    
    df = conn.execute(query, params).df()
    return df


def display_ranking(df: pd.DataFrame, title: str = "RANKING") -> None:
    """Affiche le ranking de manière lisible."""
    if df.empty:
        print("Aucun événement trouvé.")
        return
    
    print("=" * 100)
    print(f"{title}")
    print("=" * 100)
    print(f"{'#':<4} {'Date':<20} {'Événement':<35} {'Pays':<4} {'Impact':<10} {'Dir':<4} {'TTR':<6} {'Qualité':<8}")
    print("-" * 100)
    
    for idx, row in df.iterrows():
        direction_emoji = "⬆️" if row['impact_unified_direction'] == 1 else "⬇️"
        date_str = str(row['ts_utc'])[:19]  # YYYY-MM-DD HH:MM:SS
        event_key_short = row['event_key'][:33] + "..." if len(row['event_key']) > 35 else row['event_key']
        
        print(f"{idx+1:<4} {date_str:<20} {event_key_short:<35} {row['country']:<4} "
              f"{row['impact_unified_pips']:>8.1f} {direction_emoji:<4} "
              f"{row['impact_unified_time_to_peak_minutes']:>5.0f} {row['impact_unified_quality']:<8}")
    
    print("=" * 100)
    print()


def parse_args():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ranking des événements par impact_unified_pips"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Nombre d'événements à afficher (défaut: 20)",
    )
    parser.add_argument(
        "--country",
        type=str,
        default=None,
        help="Filtrer par pays (ex: US)",
    )
    parser.add_argument(
        "--event-key",
        type=str,
        default=None,
        help="Filtrer par type d'événement (ex: 'non farm payrolls')",
    )
    parser.add_argument(
        "--min-impact",
        type=float,
        default=None,
        help="Impact minimal en pips (ex: 50.0)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Construire le titre
        title_parts = ["TOP", str(args.limit), "ÉVÉNEMENTS PAR IMPACT UNIFIÉ"]
        if args.country:
            title_parts.append(f"(Pays: {args.country})")
        if args.event_key:
            title_parts.append(f"(Type: {args.event_key})")
        if args.min_impact:
            title_parts.append(f"(Min: {args.min_impact} pips)")
        title = " ".join(title_parts)
        
        df = rank_events(
            conn,
            limit=args.limit,
            country=args.country,
            event_key_filter=args.event_key,
            min_impact=args.min_impact,
        )
        
        display_ranking(df, title=title)
        
        # Stats rapides
        if not df.empty:
            print(f"📊 Stats : Moyenne = {df['impact_unified_pips'].mean():.1f} pips | "
                  f"Médiane = {df['impact_unified_pips'].median():.1f} pips | "
                  f"Max = {df['impact_unified_pips'].max():.1f} pips")
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
