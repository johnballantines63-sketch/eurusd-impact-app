# fx_impact_app/scripts/check_price_coverage.py
from __future__ import annotations
import argparse
import pandas as pd
import duckdb

def main():
    ap = argparse.ArgumentParser(description="Vérifie la couverture prices_1m_v autour d'un événement.")
    ap.add_argument("--event-ts", required=True, help='UTC ex: "2025-10-01 14:15"')
    ap.add_argument("--window-min", type=int, default=120, help="± minutes (défaut 120)")
    ap.add_argument("--db", default=None, help="DuckDB path (défaut: config.get_db_path())")
    args = ap.parse_args()

    from fx_impact_app.src.config import get_db_path
    db_path = args.db or get_db_path()

    event_ts = pd.to_datetime(args.event_ts)  # naïf -> UTC plus bas
    if event_ts.tzinfo is None:
        event_ts = event_ts.tz_localize("UTC")
    event_ts = event_ts.tz_convert("UTC").tz_localize(None)  # ts_utc de la vue est naïf UTC

    start = event_ts - pd.Timedelta(minutes=args.window_min)
    end   = event_ts + pd.Timedelta(minutes=args.window_min)

    with duckdb.connect(db_path) as con:
        cov = con.execute("""
            SELECT COUNT(*) AS n_have,
                   MIN(ts_utc) AS first,
                   MAX(ts_utc) AS last
            FROM prices_1m_v
            WHERE ts_utc BETWEEN ? AND ?
        """, [start, end]).df().iloc[0].to_dict()

        total = int((end - start).total_seconds() // 60) + 1
        n_have = int(cov["n_have"] or 0)
        print(f"Fenêtre: [{start} .. {end}] -> total minutes théoriques: {total}")
        print(f"Couverture: {n_have}/{total} (manquantes: {total - n_have})")
        print({"first": cov["first"], "last": cov["last"]})

if __name__ == "__main__":
    main()
