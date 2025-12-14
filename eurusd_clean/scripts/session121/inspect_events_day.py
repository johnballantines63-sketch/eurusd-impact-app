#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspect_events_day.py
---------------------
Inspecte rapidement une table d'événements pour un jour donné :
- colonnes présentes
- nombre d'events
- distinct countries
- dump 12:00–18:00 tz_display

Dépendances: duckdb, pandas
"""

import argparse
import duckdb
import pandas as pd

DEFAULT_DB = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
DEFAULT_TABLE = "events"
DEFAULT_TZ = "Europe/Zurich"
DEFAULT_TS_COL = "ts_utc"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", type=str, default=DEFAULT_DB)
    ap.add_argument("--table", type=str, default=DEFAULT_TABLE)
    ap.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
    ap.add_argument("--tz", type=str, default=DEFAULT_TZ)
    ap.add_argument("--ts-col", type=str, default=DEFAULT_TS_COL, help="colonne timestamp (UTC)")
    args = ap.parse_args()

    conn = duckdb.connect(args.db_path, read_only=True)

    print("== DESCRIBE ==")
    print(conn.execute(f"DESCRIBE {args.table};").df().to_string(index=False))

    q = f"""
    SELECT
      {args.ts_col} AS ts_utc,
      ( {args.ts_col} AT TIME ZONE '{args.tz}' ) AS ts_local,
      *
    FROM {args.table}
    WHERE DATE_TRUNC('day', ({args.ts_col} AT TIME ZONE '{args.tz}'))
          = DATE_TRUNC('day', TIMESTAMP '{args.date}' AT TIME ZONE '{args.tz}')
    ORDER BY ts_utc
    """
    df = conn.execute(q).df()
    conn.close()

    if df.empty:
        print("\nAucun event pour ce jour (avec ce ts_col).")
        return

    print(f"\nTotal events on {args.date}: {len(df)}")
    if "country" in df.columns:
        print("\nDistinct countries:", sorted(df["country"].dropna().unique().tolist()))
    else:
        print("\nColonne 'country' absente.")

    base = pd.Timestamp(args.date).tz_localize(args.tz)
    start_dump = base.replace(hour=12, minute=0, second=0)
    end_dump   = base.replace(hour=18, minute=0, second=0)
    df["ts_local"] = pd.to_datetime(df["ts_local"])
    audit = df[(df["ts_local"] >= start_dump) & (df["ts_local"] <= end_dump)]
    if audit.empty:
        print("\nAucun event entre 12:00 et 18:00.")
        return
    cols = [c for c in ["ts_utc","ts_local","country","importance_n","event_title","actual","estimate","forecast"] if c in audit.columns]
    print("\n=== Dump 12:00–18:00 ===")
    print(audit[cols].to_string(index=False))

if __name__ == "__main__":
    main()
