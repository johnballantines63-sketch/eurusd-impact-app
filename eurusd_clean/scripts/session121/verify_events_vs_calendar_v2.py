#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_events_vs_calendar_v2.py
--------------------------------
Vérifie la présence d'événements dans DuckDB autour d'heures cibles (Europe/Zurich).
Paramétrable: table/colonnes, filtre pays, filtre titre (--like), tolérance en minutes.

Dépendances: duckdb, pandas
"""

import argparse
from typing import List
import duckdb
import pandas as pd

DEFAULT_DB = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
DEFAULT_TABLE = "events"
DEFAULT_TZ = "Europe/Zurich"

def parse_times(times: List[str]) -> List[str]:
    out = []
    for t in times:
        t = t.strip().replace("h", ":")
        hh, mm = map(int, t.split(":"))
        out.append(f"{hh:02d}:{mm:02d}")
    return out

def within_window(ts: pd.Timestamp, center: pd.Timestamp, tol_min: int) -> bool:
    return abs((ts - center).total_seconds()) <= tol_min * 60

def main():
    ap = argparse.ArgumentParser(description="Vérifie les events DuckDB autour d'heures cibles (Europe/Zurich)")
    ap.add_argument("--db-path", type=str, default=DEFAULT_DB)
    ap.add_argument("--table", type=str, default=DEFAULT_TABLE)
    ap.add_argument("--date", type=str, required=True, help="YYYY-MM-DD (jour Europe/Zurich à afficher)")
    ap.add_argument("--times", nargs="+", default=["13:30", "14:45", "15:00"])
    ap.add_argument("--tol", type=int, default=10, help="Tolérance ± minutes")
    ap.add_argument("--tz", type=str, default=DEFAULT_TZ, help="Timezone d'affichage (ex: Europe/Zurich, UTC)")

    # Colonnes personnalisables
    ap.add_argument("--ts-col", type=str, default="ts_utc", help="Nom de la colonne timestamp (UTC)")
    ap.add_argument("--country-col", type=str, default="country")
    ap.add_argument("--importance-col", type=str, default="importance_n")
    ap.add_argument("--title-col", type=str, default="event_title")
    ap.add_argument("--actual-col", type=str, default="actual")
    ap.add_argument("--estimate-col", type=str, default="estimate")
    ap.add_argument("--forecast-col", type=str, default="forecast")
    ap.add_argument("--importance-min", type=int, default=1)

    # Filtres
    ap.add_argument("--countries", nargs="+", default=["USD"])
    ap.add_argument("--like", type=str, help="Filtre de titre (substring, insensible à la casse)")
    ap.add_argument("--list", action="store_true", help="Lister tous les events 12:30–16:30 (Europe/Zurich)")

    args = ap.parse_args()
    times_hhmm = parse_times(args.times)

    conn = duckdb.connect(args.db_path, read_only=True)

    # Construire la requête dynamique
    tz_out = args.tz
    q = f"""
    WITH base AS (
      SELECT
        {args.ts_col} AS ts_utc,
        {args.country_col} AS country,
        {args.importance_col} AS importance_n,
        {args.title_col} AS event_title,
        {args.actual_col} AS actual,
        {args.estimate_col} AS estimate,
        {args.forecast_col} AS forecast,
        ({args.ts_col} AT TIME ZONE '{tz_out}') AS ts_local
      FROM {args.table}
    )
    SELECT *
    FROM base
    WHERE DATE_TRUNC('day', ts_local) = DATE_TRUNC('day', TIMESTAMP '{args.date}' AT TIME ZONE '{tz_out}')
    """
    params = []
    if args.countries:
        placeholders = ", ".join(["?"] * len(args.countries))
        q += f" AND country IN ({placeholders})"
        params.extend(args.countries)
    if args.importance_min is not None:
        q += " AND importance_n >= ?"
        params.append(args.importance_min)

    df = conn.execute(q, params).df()
    conn.close()

    print("="*90)
    print(f"DATE (affichage)  : {args.date} ({tz_out})")
    print(f"TABLE             : {args.table}")
    print(f"TS column (UTC)   : {args.ts_col}")
    print(f"COUNTRIES filter  : {', '.join(args.countries)}")
    print(f"IMPORTANCE >=     : {args.importance_min}")
    if args.like:
        print(f"TITLE contains    : {args.like} (case-insensitive)")
    print(f"TARGET TIMES      : {', '.join(times_hhmm)}  ±{args.tol} min")
    print("="*90)

    if df.empty:
        print("AUCUN événement trouvé pour cette date/params.")
        return

    # Conversion pandas
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df["ts_local"] = pd.to_datetime(df["ts_local"])

    # Filtre titre si demandé
    if args.like:
        mask = df["event_title"].astype(str).str.contains(args.like, case=False, na=False)
        df = df[mask]

    if df.empty:
        print("AUCUN événement trouvé après filtre de titre.")
        return

    # Ciblage des heures
    base = pd.Timestamp(args.date).tz_localize(tz_out)
    targets = [base.replace(hour=int(t.split(':')[0]), minute=int(t.split(':')[1]), second=0) for t in times_hhmm]

    def within(ts, center, tol):
        return abs((ts - center).total_seconds()) <= tol * 60

    for target, label in zip(targets, times_hhmm):
        cand = df[df["ts_local"].apply(lambda t: within(t, target, args.tol))].copy()
        print(f"\n--- Target {label} ({target}) ---")
        if cand.empty:
            print("MISSING: aucun event dans la fenêtre.")
        else:
            cand["delta_min"] = cand["ts_local"].apply(lambda t: round((t - target).total_seconds()/60.0, 1))
            cand = cand.sort_values("delta_min")
            print(cand[[
                "ts_utc","ts_local","country","importance_n","event_title","actual","estimate","forecast","delta_min"
            ]].to_string(index=False))

    if args.list:
        print("\n=== LIST (12:30–16:30 tz_display) ===")
        start_dump = base.replace(hour=12, minute=30, second=0)
        end_dump   = base.replace(hour=16, minute=30, second=0)
        audit = df[(df["ts_local"] >= start_dump) & (df["ts_local"] <= end_dump)].copy()
        if audit.empty:
            print("Aucun event dans cette plage.")
        else:
            print(audit[[
                "ts_utc","ts_local","country","importance_n","event_title"
            ]].sort_values("ts_local").to_string(index=False))

if __name__ == "__main__":
    main()
