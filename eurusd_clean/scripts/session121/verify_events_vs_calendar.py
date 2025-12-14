#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vérification des événements dans DuckDB par rapport à des heures cibles (Myfxbook)
- Convertit events.ts_utc -> ts_bern (Europe/Zurich)
- Filtre par pays (ex: US) et importance (ex: 2/3)
- Cherche autour d'heures cibles (± tolérance en minutes)
- Affiche un rapport "FOUND / MISSING" + dump des événements du créneau

Dépendances: duckdb, pandas, python-dateutil (facultatif)
"""

import argparse
from datetime import datetime, timedelta
from typing import List
import duckdb
import pandas as pd

DEFAULT_DB = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
DEFAULT_TZ = "Europe/Zurich"

def parse_times(times: List[str]) -> List[str]:
    parsed = []
    for t in times:
        t = t.strip().replace("h", ":")
        hh, mm = map(int, t.split(":"))
        parsed.append(f"{hh:02d}:{mm:02d}")
    return parsed

def fetch_events_for_date(conn, date_str: str, countries: List[str], importance_min: int, tz_out: str = DEFAULT_TZ):
    d0 = pd.Timestamp(date_str).tz_localize("UTC")
    d1 = d0 + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    q = f"""
    SELECT ts_utc, country, event_title, importance_n, actual, estimate, forecast,
           (ts_utc AT TIME ZONE '{tz_out}') AS ts_bern
    FROM events
    WHERE ts_utc BETWEEN ? AND ?
      AND country IN ({','.join(['?']*len(countries))})
      AND importance_n >= ?
    ORDER BY ts_utc
    """

    params = [d0.to_pydatetime(), d1.to_pydatetime(), *countries, importance_min]
    df = conn.execute(q, params).df()

    if df.empty:
        return df

    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df["ts_bern"] = pd.to_datetime(df["ts_bern"])
    return df

def within_window(ts: pd.Timestamp, center: pd.Timestamp, tol_min: int) -> bool:
    return abs((ts - center).total_seconds()) <= tol_min * 60

def build_targets(date_str: str, tz_out: str, times_hhmm: List[str]) -> List[pd.Timestamp]:
    base = pd.Timestamp(date_str).tz_localize(tz_out)
    return [base.replace(hour=int(h.split(':')[0]), minute=int(h.split(':')[1]), second=0) for h in times_hhmm]

def report(df, date_str, times_hhmm, tol_min, countries, importance_min, tz_out):
    print("="*80)
    print(f"DATE              : {date_str} ({tz_out})")
    print(f"COUNTRIES         : {', '.join(countries)}")
    print(f"IMPORTANCE MIN    : {importance_min}")
    print(f"TARGET TIMES      : {', '.join(times_hhmm)}  ±{tol_min} min")
    print("="*80)

    if df.empty:
        print("AUCUN événement trouvé ce jour-là pour ces critères.")
        return

    targets = build_targets(date_str, tz_out, times_hhmm)

    for target, label in zip(targets, times_hhmm):
        cand = df[df["ts_bern"].apply(lambda t: within_window(t, target, tol_min))].copy()

        print(f"\n--- Ciblage {label} ({target}) ---")
        if cand.empty:
            print("MISSING: aucun event dans la fenêtre.")
        else:
            cand["delta_min"] = cand["ts_bern"].apply(lambda t: round((t - target).total_seconds()/60.0, 1))
            cand = cand.sort_values("delta_min")
            print(cand[["ts_utc", "ts_bern", "country", "importance_n", "event_title", "actual", "estimate", "forecast", "delta_min"]].to_string(index=False))

    print("\n=== DUMP 12:30–16:30 (Bern) pour audit ===")
    start_dump = pd.Timestamp(date_str).tz_localize(tz_out).replace(hour=12, minute=30, second=0)
    end_dump = pd.Timestamp(date_str).tz_localize(tz_out).replace(hour=16, minute=30, second=0)
    audit = df[(df["ts_bern"] >= start_dump) & (df["ts_bern"] <= end_dump)].copy()
    if audit.empty:
        print("Aucun event dans cette plage.")
    else:
        print(audit[["ts_utc", "ts_bern", "country", "importance_n", "event_title"]].to_string(index=False))

def main():
    ap = argparse.ArgumentParser(description="Vérifie la présence d'événements DB autour d'heures cibles (Europe/Zurich).")
    ap.add_argument("--db-path", type=str, default=DEFAULT_DB, help="Chemin DuckDB")
    ap.add_argument("--date", required=True, help="Date cible (YYYY-MM-DD)")
    ap.add_argument("--times", nargs="+", default=["13:30", "14:45", "15:00"], help="Heures Bern à vérifier")
    ap.add_argument("--tol", type=int, default=10, help="Tolérance ± minutes")
    ap.add_argument("--countries", nargs="+", default=["USD"], help="Liste des pays")
    ap.add_argument("--importance-min", type=int, default=1, help="Seuil importance_n")
    ap.add_argument("--tz", type=str, default=DEFAULT_TZ, help="Timezone d'affichage")

    args = ap.parse_args()
    times_hhmm = parse_times(args.times)

    conn = duckdb.connect(args.db_path, read_only=True)
    try:
        df = fetch_events_for_date(conn, args.date, args.countries, args.importance_min, tz_out=args.tz)
    finally:
        conn.close()

    report(df, args.date, times_hhmm, args.tol, args.countries, args.importance_min, args.tz)

if __name__ == "__main__":
    main()