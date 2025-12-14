#!/usr/bin/env python3
"""
Backfill de l'impact canonique (impact_unified_pips) dans event_impacts_v2
=========================================================================

Objectif
--------
- Ajouter les colonnes "impact_unified_*" dans event_impacts_v2 (si absentes)
- Calculer l'impact canonique via measure_impact_from_finnhub(..., use_unified=True)
- Mettre à jour la table pour tous les événements qui n'ont pas encore été backfillés

Définition canonique
--------------------
Voir:
- docs/IMPACT_SPEC_V1.md
- docs/RAPPORT_AUDIT_IMPACT_V2_FINAL.md

La métrique "impact_unified_pips" correspond à:
- baseline = event_open
- horizon  = 120 minutes
- calcul via src/core/impact_unified.py (calculate_impact_unified)
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

# Import du calcul d'impact via la façade existante
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from core.price_loader_finnhub import measure_impact_from_finnhub  # noqa: E402


def ensure_unified_columns(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Ajoute les colonnes impact_unified_* dans event_impacts_v2 si elles n'existent pas.
    """
    print("🔧 Vérification / création des colonnes impact_unified_* dans event_impacts_v2...")

    conn.execute("""
        ALTER TABLE event_impacts_v2
        ADD COLUMN IF NOT EXISTS impact_unified_pips DOUBLE;
    """)
    conn.execute("""
        ALTER TABLE event_impacts_v2
        ADD COLUMN IF NOT EXISTS impact_unified_direction INTEGER;
    """)
    conn.execute("""
        ALTER TABLE event_impacts_v2
        ADD COLUMN IF NOT EXISTS impact_unified_time_to_peak_minutes DOUBLE;
    """)
    conn.execute("""
        ALTER TABLE event_impacts_v2
        ADD COLUMN IF NOT EXISTS impact_unified_start_price DOUBLE;
    """)
    conn.execute("""
        ALTER TABLE event_impacts_v2
        ADD COLUMN IF NOT EXISTS impact_unified_peak_price DOUBLE;
    """)
    conn.execute("""
        ALTER TABLE event_impacts_v2
        ADD COLUMN IF NOT EXISTS impact_unified_quality VARCHAR;
    """)

    print("   ✅ Colonnes OK\n")


def fetch_pending_rows(
    conn: duckdb.DuckDBPyConnection,
    limit: Optional[int] = None,
    country: Optional[str] = None,
) -> pd.DataFrame:
    """
    Récupère les lignes d'event_impacts_v2 à backfiller (impact_unified_pips IS NULL).
    """
    query = """
        SELECT ts_utc, country
        FROM event_impacts_v2
        WHERE impact_unified_pips IS NULL
    """
    params = []

    if country:
        query += " AND country = ?"
        params.append(country)

    query += " ORDER BY ts_utc"
    if limit:
        query += f" LIMIT {limit}"

    df = conn.execute(query, params).df()
    return df


def backfill_batch(
    conn: duckdb.DuckDBPyConnection,
    df_pending: pd.DataFrame,
    dry_run: bool = False,
    verbose: bool = True,
) -> None:
    """
    Backfill d'un batch de lignes (df_pending) en calculant impact_unified_*.
    """
    if df_pending.empty:
        print("   Rien à backfiller (0 ligne).")
        return

    print(f"🔄 Backfill de {len(df_pending)} événement(s)...\n")

    updated = 0
    skipped = 0

    for row in df_pending.itertuples(index=False):
        ts_utc = getattr(row, "ts_utc")
        country = getattr(row, "country")

        # Conversion en datetime Python
        event_ts = pd.to_datetime(ts_utc)
        event_dt = event_ts.to_pydatetime()

        if verbose:
            print(f"   📅 {event_dt} | {country} ... ", end="", flush=True)

        # Appel de la façade unifiée (IMPACT_SPEC_V1)
        # Passer la connexion existante pour éviter les conflits DuckDB
        result = measure_impact_from_finnhub(
            db_path=DB_PATH,
            event_timestamp=event_dt,
            lookback_minutes=5,
            lookahead_minutes=120,
            debug=False,
            use_unified=True,
            conn=conn,  # Utiliser la connexion existante
        )

        if not result or result.get("impact_pips") is None:
            if verbose:
                print("⚠️ aucun résultat (measure_impact_from_finnhub → None)")
            skipped += 1
            continue

        impact_pips = float(result["impact_pips"])
        direction = int(result.get("direction", 0))
        start_price = float(result.get("start_price", 0.0))
        peak_price = float(result.get("peak_price", 0.0))
        time_to_peak = float(result.get("time_to_peak_minutes", 0.0))
        quality = str(result.get("measurement_quality", ""))

        if verbose:
            print(f"OK → {impact_pips:.1f} pips (dir={direction}, quality={quality})")

        if dry_run:
            continue

        conn.execute(
            """
            UPDATE event_impacts_v2
            SET
                impact_unified_pips = ?,
                impact_unified_direction = ?,
                impact_unified_time_to_peak_minutes = ?,
                impact_unified_start_price = ?,
                impact_unified_peak_price = ?,
                impact_unified_quality = ?
            WHERE ts_utc = ? AND country = ?
            """,
            [
                impact_pips,
                direction,
                time_to_peak,
                start_price,
                peak_price,
                quality,
                ts_utc,
                country,
            ],
        )
        updated += 1

    print()
    print(f"   ✅ Backfill terminé : {updated} ligne(s) mise(s) à jour, {skipped} ignorée(s)\n")


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill impact_unified_pips dans event_impacts_v2 "
                    "via measure_impact_from_finnhub(..., use_unified=True)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Nombre maximum de lignes à traiter (défaut: toutes).",
    )
    parser.add_argument(
        "--country",
        type=str,
        default=None,
        help="Filtrer sur un pays (ex: US).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ne pas écrire dans la DB, juste simuler.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Mode silencieux (moins de logs).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)

    print("=" * 80)
    print("BACKFILL IMPACT UNIFIÉ (IMPACT_SPEC_V1) DANS event_impacts_v2")
    print("=" * 80)
    print(f"DB : {DB_PATH}")
    print(f"Limit : {args.limit}")
    print(f"Country : {args.country or 'ALL'}")
    print(f"Dry-run : {args.dry_run}")
    print()

    conn = duckdb.connect(str(DB_PATH), read_only=False)

    try:
        ensure_unified_columns(conn)

        df_pending = fetch_pending_rows(
            conn,
            limit=args.limit,
            country=args.country,
        )

        if df_pending.empty:
            print("✅ Aucun événement à backfiller (impact_unified_pips déjà rempli partout ?).")
            return

        backfill_batch(
            conn,
            df_pending,
            dry_run=args.dry_run,
            verbose=not args.quiet,
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()
