#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eodhd_compare_events_vs_db.py
=============================
But : Vérifier si EODHD (economic events) contient les mêmes events que ta DB.
- Récupère les events EODHD via API (JSON)
- Récupère les events DB (DuckDB) pour la même date (affichage Europe/Zurich par défaut)
- Normalise, convertit timezone, et compare par pays + proximité temporelle (± tolérance)
- Génère un rapport console + CSV des correspondances et divergences

Dépendances : requests, pandas, duckdb, python-dateutil (optionnel)
Usage simple (1 jour) :
  python eodhd_compare_events_vs_db.py \
    --api-token "XXXX" \
    --date 2025-09-11 \
    --countries USD,EU,DE \
    --db-path "/.../warehouse.duckdb" \
    --table events \
    --out compare_eodhd_vs_db_20250911.csv
"""

import argparse
import sys
import json
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta, timezone

import requests
import duckdb
import pandas as pd

DEFAULT_DB = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
DEFAULT_TABLE = "events"
DEFAULT_TZ = "Europe/Zurich"
DEFAULT_TS_COL = "ts_utc"
DEFAULT_EODHD_BASE = "https://eodhistoricaldata.com"

def parse_countries(csv_str: str) -> List[str]:
    return [c.strip() for c in csv_str.split(",") if c.strip()]

def to_int_importance(x) -> Optional[int]:
    """
    Mappe impact/importance en entier 1..3 si possible.
    Accepte : 1/2/3, 'low/medium/high', 'Low/Medium/High', '1.0' etc.
    """
    if x is None: return None
    if isinstance(x, (int, float)):
        try:
            n = int(x)
            if 1 <= n <= 5:  # on tronque à 3 si certains providers ont 5 niveaux
                return min(n, 3)
        except Exception:
            pass
    s = str(x).strip().lower()
    if s in ("1","low","lo"): return 1
    if s in ("2","med","medium"): return 2
    if s in ("3","hi","high","high-importance"): return 3
    # fallback None
    return None

def coalesce(d: dict, keys: List[str], default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default

def parse_eodhd_events(raw: List[dict], tz_display: str, countries_filter: Optional[List[str]]) -> pd.DataFrame:
    """
    Essaie d'être robuste aux variations de schéma EODHD (nom des champs).
    Champs cibles : ts_utc, ts_local, country, title, importance, actual/estimate/forecast (si dispo).
    """
    rows = []
    for ev in raw:
        # timestamp UTC : tenter plusieurs clés possibles
        # EODHD peut renvoyer 'date', 'datetime', 'timestamp', etc.
        ts_val = coalesce(ev, ["timestamp", "datetime", "date", "event_date"])
        ts_utc = None
        if ts_val is not None:
            # cas timestamp numérique (secondes) :
            try:
                # int or float as epoch seconds
                sec = int(float(ts_val))
                ts_utc = datetime.fromtimestamp(sec, tz=timezone.utc)
            except Exception:
                pass
            # cas ISO string :
            if ts_utc is None:
                try:
                    # pandas parse
                    ts_utc = pd.to_datetime(ts_val, utc=True).to_pydatetime()
                except Exception:
                    ts_utc = None

        country = coalesce(ev, ["country", "code", "ccy", "currency"])
        title = coalesce(ev, ["event", "title", "event_name", "name", "event_title"])
        importance = to_int_importance(coalesce(ev, ["importance", "impact", "priority", "importance_n"]))
        actual = coalesce(ev, ["actual", "value_actual", "release_actual"])
        estimate = coalesce(ev, ["estimate", "consensus", "value_consensus"])
        forecast = coalesce(ev, ["forecast", "value_forecast"])

        if ts_utc is None:
            # on garde quand même pour debug, mais sans timestamp on ne peut pas matcher
            continue

        rows.append({
            "ts_utc": ts_utc,
            "country": country,
            "event_title": title,
            "importance_n": importance,
            "actual": actual,
            "estimate": estimate,
            "forecast": forecast,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df["ts_local"] = df["ts_utc"].dt.tz_convert(tz_display)

    if countries_filter:
        df = df[df["country"].isin(countries_filter)].copy()

    return df.sort_values("ts_local")

def fetch_eodhd(api_token: str,
                date_from: str,
                date_to: str,
                countries: Optional[List[str]],
                base_url: str = DEFAULT_EODHD_BASE) -> List[dict]:
    """
    Appel API EODHD pour economic events. Le schéma exact peut varier selon le plan/endpoint.
    On tente /api/economic-events (si non dispo chez toi, passer --endpoint complet).
    """
    url = f"{base_url}/api/economic-events"
    params = {
        "api_token": api_token,
        "from": date_from,
        "to": date_to,
    }
    if countries:
        params["countries"] = ",".join(countries)

    resp = requests.get(url, params=params, timeout=30)
    try:
        data = resp.json()
    except Exception:
        print("EODHD response non-JSON:", resp.text[:500], file=sys.stderr)
        raise

    # data peut être {"events":[...]} ou directement une liste
    if isinstance(data, dict) and "events" in data:
        return data["events"]
    if isinstance(data, list):
        return data
    # inconnu : renvoyer brut pour debug
    print("Format EODHD inattendu, dump partiel:\n", json.dumps(data, indent=2)[:800], file=sys.stderr)
    return []

def load_db_events(db_path: str,
                   table: str,
                   date_str: str,
                   tz_display: str,
                   ts_col: str = DEFAULT_TS_COL,
                   countries: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Charge les events d'une journée (affichage tz), renvoie DataFrame avec ts_utc + ts_local + country + title + importance.
    """
    conn = duckdb.connect(db_path, read_only=True)
    q = f"""
    SELECT
      {ts_col} AS ts_utc,
      ({ts_col} AT TIME ZONE '{tz_display}') AS ts_local,
      country, event_title, importance_n, actual, estimate, forecast
    FROM {table}
    WHERE DATE_TRUNC('day', ({ts_col} AT TIME ZONE '{tz_display}'))
          = DATE_TRUNC('day', TIMESTAMP '{date_str}' AT TIME ZONE '{tz_display}')
    """
    params = []
    if countries:
        placeholders = ", ".join(["?"] * len(countries))
        q += f" AND country IN ({placeholders})"
        params.extend(countries)

    q += " ORDER BY ts_utc"
    df = conn.execute(q, params).df()
    conn.close()

    if df.empty:
        return df

    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    # DuckDB renvoie ts_local sans tz -> on force tz-aware proprement
    df["ts_local"] = pd.to_datetime(df["ts_local"], utc=True).dt.tz_convert(tz_display)

    return df

def nearest_match(source_ts: pd.Timestamp,
                  df: pd.DataFrame,
                  tol_min: int,
                  country: Optional[str] = None) -> Optional[Tuple[int, float]]:
    """
    Trouve la ligne 'la plus proche' en minutes dans df (par ts_local), optionnellement même pays.
    Retourne (index, delta_min) ou None si rien dans la tolérance.
    """
    if df.empty:
        return None
    cand = df.copy()
    if country is not None and "country" in cand.columns:
        cand = cand[cand["country"] == country]
        if cand.empty:
            return None
    # delta absolu en minutes
    delta = (cand["ts_local"] - source_ts).abs().dt.total_seconds() / 60.0
    min_idx = delta.idxmin()
    min_val = float(delta.loc[min_idx])
    if min_val <= tol_min:
        return int(min_idx), round(min_val, 2)
    return None

def compare_day(api_token: str,
                date_str: str,
                countries: List[str],
                db_path: str,
                table: str,
                tz_display: str,
                ts_col: str,
                tol_min: int,
                base_url: str,
                out_csv: Optional[str] = None):
    # 1) EODHD fetch
    raw = fetch_eodhd(api_token, date_str, date_str, countries, base_url=base_url)
    df_eod = parse_eodhd_events(raw, tz_display, countries)
    print(f"EODHD events fetched: {len(df_eod)}")

    # 2) DB fetch
    df_db = load_db_events(db_path, table, date_str, tz_display, ts_col, countries)
    print(f"DB events loaded:     {len(df_db)}")

    # 3) Matching (2 sens)
    rows = []
    used_db = set()
    used_eod = set()

    # 3a) EODHD -> DB
    for i, r in df_eod.reset_index(drop=True).iterrows():
        m = nearest_match(r["ts_local"], df_db, tol_min, r.get("country"))
        if m is not None:
            j, dmin = m
            used_eod.add(i); used_db.add(j)
            rows.append({
                "side": "MATCH_EODHD→DB",
                "eod_ts_local": r["ts_local"],
                "eod_ts_utc": r["ts_utc"],
                "eod_country": r.get("country"),
                "eod_title": r.get("event_title"),
                "eod_importance": r.get("importance_n"),
                "db_ts_local": df_db.loc[j, "ts_local"],
                "db_ts_utc": df_db.loc[j, "ts_utc"],
                "db_country": df_db.loc[j, "country"] if "country" in df_db.columns else None,
                "db_title": df_db.loc[j, "event_title"] if "event_title" in df_db.columns else None,
                "db_importance": df_db.loc[j, "importance_n"] if "importance_n" in df_db.columns else None,
                "delta_min": dmin
            })
        else:
            rows.append({
                "side": "ONLY_IN_EODHD",
                "eod_ts_local": r["ts_local"],
                "eod_ts_utc": r["ts_utc"],
                "eod_country": r.get("country"),
                "eod_title": r.get("event_title"),
                "eod_importance": r.get("importance_n"),
                "db_ts_local": None,
                "db_ts_utc": None,
                "db_country": None,
                "db_title": None,
                "db_importance": None,
                "delta_min": None
            })

    # 3b) DB -> EODHD (ceux non utilisés)
    for j, r in df_db.reset_index(drop=True).iterrows():
        if j in used_db: 
            continue
        m = nearest_match(r["ts_local"], df_eod, tol_min, r.get("country"))
        if m is not None:
            i, dmin = m
            if i in used_eod:
                # déjà matché dans 3a (cas rare), on skip
                continue
            rows.append({
                "side": "MATCH_DB→EODHD",
                "eod_ts_local": df_eod.loc[i, "ts_local"],
                "eod_ts_utc": df_eod.loc[i, "ts_utc"],
                "eod_country": df_eod.loc[i, "country"] if "country" in df_eod.columns else None,
                "eod_title": df_eod.loc[i, "event_title"] if "event_title" in df_eod.columns else None,
                "eod_importance": df_eod.loc[i, "importance_n"] if "importance_n" in df_eod.columns else None,
                "db_ts_local": r["ts_local"],
                "db_ts_utc": r["ts_utc"],
                "db_country": r.get("country"),
                "db_title": r.get("event_title"),
                "db_importance": r.get("importance_n"),
                "delta_min": dmin
            })
        else:
            rows.append({
                "side": "ONLY_IN_DB",
                "eod_ts_local": None,
                "eod_ts_utc": None,
                "eod_country": None,
                "eod_title": None,
                "eod_importance": None,
                "db_ts_local": r["ts_local"],
                "db_ts_utc": r["ts_utc"],
                "db_country": r.get("country"),
                "db_title": r.get("event_title"),
                "db_importance": r.get("importance_n"),
                "delta_min": None
            })

    df_cmp = pd.DataFrame(rows).sort_values(["side", "db_ts_local", "eod_ts_local"])

    # Résumé
    c_only_eod = (df_cmp["side"] == "ONLY_IN_EODHD").sum()
    c_only_db  = (df_cmp["side"] == "ONLY_IN_DB").sum()
    c_match    = (df_cmp["side"].str.startswith("MATCH")).sum()
    print("\n==== SUMMARY ====")
    print(f"Matches:        {c_match}")
    print(f"Only in EODHD:  {c_only_eod}")
    print(f"Only in DB:     {c_only_db}")

    if out_csv:
        df_cmp.to_csv(out_csv, index=False)
        print(f"Saved report → {out_csv}")
    else:
        # print petit aperçu
        print("\nSample rows:")
        print(df_cmp.head(20).to_string(index=False))

def main():
    ap = argparse.ArgumentParser(description="Compare EODHD economic events vs DuckDB events (by date).")
    ap.add_argument("--api-token", required=True, help="EODHD API token")
    ap.add_argument("--date", help="YYYY-MM-DD (single day)")
    ap.add_argument("--start", help="YYYY-MM-DD (batch start)")
    ap.add_argument("--end", help="YYYY-MM-DD (batch end)")
    ap.add_argument("--countries", default="USD,EU,DE", help="Comma-separated (ex: USD,EU,DE)")
    ap.add_argument("--db-path", default=DEFAULT_DB)
    ap.add_argument("--table", default=DEFAULT_TABLE)
    ap.add_argument("--ts-col", default=DEFAULT_TS_COL)
    ap.add_argument("--tz", default=DEFAULT_TZ)
    ap.add_argument("--tol", type=int, default=10, help="tolerance minutes for matching")
    ap.add_argument("--base-url", default=DEFAULT_EODHD_BASE, help="Base URL for EODHD (override if needed)")
    ap.add_argument("--out", help="CSV output path (if single day)")
    args = ap.parse_args()

    countries = parse_countries(args.countries)

    if args.date:
        compare_day(
            api_token=args.api_token,
            date_str=args.date,
            countries=countries,
            db_path=args.db_path,
            table=args.table,
            tz_display=args.tz,
            ts_col=args.ts_col,
            tol_min=args.tol,
            base_url=args.base_url,
            out_csv=args.out
        )
        return

    if not (args.start and args.end):
        print("Specify --date or (--start AND --end).")
        sys.exit(1)

    # Batch mode: loop days
    d0 = pd.Timestamp(args.start)
    d1 = pd.Timestamp(args.end)
    d = d0
    while d <= d1:
        out_csv = None
        if args.out:
            # e.g., out="cmp_%Y%m%d.csv"
            out_csv = d.strftime(args.out)
        print(f"\n=== {d.date()} ===")
        compare_day(
            api_token=args.api_token,
            date_str=d.strftime("%Y-%m-%d"),
            countries=countries,
            db_path=args.db_path,
            table=args.table,
            tz_display=args.tz,
            ts_col=args.ts_col,
            tol_min=args.tol,
            base_url=args.base_url,
            out_csv=out_csv
        )
        d += pd.Timedelta(days=1)

if __name__ == "__main__":
    main()
