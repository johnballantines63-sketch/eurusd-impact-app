#!/usr/bin/env python3
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

import duckdb
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Build a clean panel CSV from daily_pattern_truth_v4"
    )
    parser.add_argument("--db", required=True, help="Path to DuckDB database")
    parser.add_argument("--years", type=float, default=3.0, help="Lookback window in years")
    parser.add_argument("--out", default="data/panel_from_truth.csv", help="Output CSV path")
    parser.add_argument(
        "--require-impact",
        action="store_true",
        help="Keep only days with impact_mfe_pips > 0",
    )
    args = parser.parse_args()

    cutoff_date = (
        datetime.now(timezone.utc).date() - timedelta(days=int(args.years * 365))
    ).isoformat()

    conn = duckdb.connect(args.db, read_only=True)

    query = """
    SELECT
        date_local
    FROM daily_pattern_truth_v4
    WHERE date_local >= ?
    """

    if args.require_impact:
        query += " AND impact_mfe_pips IS NOT NULL AND impact_mfe_pips > 0"

    query += " ORDER BY date_local"

    df = conn.execute(query, [cutoff_date]).df()
    conn.close()

    if df.empty:
        raise RuntimeError("No dates found for given criteria")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(out_path, index=False)

    print("=" * 80)
    print("PANEL FROM TRUTH BUILT")
    print("=" * 80)
    print(f"DB:              {args.db}")
    print(f"Years lookback:  {args.years}")
    print(f"Dates exported:  {len(df)}")
    print(f"First date:      {df['date_local'].iloc[0]}")
    print(f"Last date:       {df['date_local'].iloc[-1]}")
    print(f"Output:          {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
