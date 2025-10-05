# fx_impact_app/scripts/ingest_eodhd_calendar.py
from __future__ import annotations
import argparse, os
from datetime import date, datetime
import pandas as pd
from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.eodhd_client import (
    fetch_calendar_json as eod_fetch,
    calendar_to_events_df as eod_norm,
    upsert_events as eod_upsert,
)

def d(s: str) -> str:
    return pd.Timestamp(s).date().isoformat()

def main():
    ap = argparse.ArgumentParser(description="Ingest EODHD economic calendar into DuckDB.")
    ap.add_argument("--from", dest="d1", default=date.today().isoformat(), help="YYYY-MM-DD")
    ap.add_argument("--to",   dest="d2", default=date.today().isoformat(), help="YYYY-MM-DD")
    ap.add_argument("--countries", nargs="*", default=None, help="Ex: US EA EU GB ... (optionnel)")
    ap.add_argument("--importance", default=None, help="low|medium|high (optionnel)")
    ap.add_argument("--api-key", dest="api_key", default=os.environ.get("EODHD_API_KEY"))
    args = ap.parse_args()

    if not args.api_key:
        raise SystemExit("Missing EODHD_API_KEY (env var or --api-key).")

    d1, d2 = d(args.d1), d(args.d2)
    items = eod_fetch(d1, d2, countries=args.countries, importance=args.importance, api_key=args.api_key)
    print(f"Fetched raw items: {len(items)}")

    df = eod_norm(items)
    print(f"Normalized rows: {len(df)}")
    if df.empty:
        print("Nothing to upsert (empty).")
        return

    db = get_db_path()
    n = eod_upsert(df, db_path=db)
    print(f"Upserted rows into events: {n} (DB={db})")

if __name__ == "__main__":
    main()
