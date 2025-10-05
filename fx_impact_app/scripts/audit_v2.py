# fx_impact_app/scripts/audit_v2.py
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
from datetime import datetime, timezone, date
import pandas as pd
import duckdb

# --- projet / imports internes
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fx_impact_app.src.config import get_db_path
from fx_impact_app.src.eodhd_client import (
    fetch_calendar_json as eod_fetch,
    calendar_to_events_df as eod_norm,
)

# --- petits utils
def _utc_day_range(d: date):
    start = pd.Timestamp(d, tz="UTC")
    end   = (start + pd.Timedelta(days=1))
    # pour DuckDB on passe en tz-naive UTC
    return start.tz_convert("UTC").tz_localize(None), end.tz_convert("UTC").tz_localize(None)

def _local_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def _try_pragma(con: duckdb.DuckDBPyConnection, name: str) -> str:
    try:
        return con.execute(f"PRAGMA {name}").fetchone()[0]
    except Exception:
        return "N/A"

def detect_family_row(row: pd.Series) -> str|None:
    s = " ".join([
        str(row.get("event_title") or ""),
        str(row.get("label") or ""),
        str(row.get("type") or ""),
        str(row.get("event_key") or ""),
    ]).lower()

    if any(k in s for k in ["nonfarm", "non-farm", "nfp", "payroll"]):
        return "NFP"
    if "cpi" in s or "consumer price" in s or "inflation" in s:
        return "CPI"
    if any(k in s for k in ["fomc", "federal reserve", "fed funds", "rate decision", "press conference", "minutes", "sep", "dot plot"]):
        return "FOMC"
    return None

def main():
    ap = argparse.ArgumentParser(description="Audit v2 — couverture données + live fetch + stats forecast")
    ap.add_argument("--d1", required=True, help="jour UTC début (YYYY-MM-DD)")
    ap.add_argument("--d2", required=True, help="jour UTC fin (YYYY-MM-DD)")
    ap.add_argument("-c", "--country", action="append", dest="countries", default=[], help="code pays (répétable)")
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--hist-years", type=int, default=3)
    args = ap.parse_args()

    d1 = pd.to_datetime(args.d1).date()
    d2 = pd.to_datetime(args.d2).date()
    countries = [c.upper() for c in args.countries] or []

    db = get_db_path()
    print("=== AUDIT V2 — FX Impact App ===")
    print(f"Run at: {_local_now_iso()}")
    print(f"DB Path: {db}")
    print()

    # 1) PRAGMA / ENV
    print("1) PRAGMA / ENV")
    print("===============")
    with duckdb.connect(db) as con:
        # léger tuning safe
        try:
            con.execute("PRAGMA preserve_insertion_order=false")
            con.execute("PRAGMA threads=2")
            con.execute("PRAGMA memory_limit='2GB'")
            tmpdir = (Path(db).with_suffix(".tmp")).as_posix()
            con.execute(f"PRAGMA temp_directory='{tmpdir}'")
            con.execute("PRAGMA max_temp_directory_size='48GB'")
        except Exception:
            pass
        settings = {
            "threads": _try_pragma(con, "threads"),
            "memory_limit": _try_pragma(con, "memory_limit"),
            "temp_directory": _try_pragma(con, "temp_directory"),
            "max_temp_directory_size": _try_pragma(con, "max_temp_directory_size"),
            "preserve_insertion_order": _try_pragma(con, "preserve_insertion_order"),
        }
    print(settings); print()

    # 2) TABLES
    print("2) TABLES")
    print("=========")
    with duckdb.connect(db) as con:
        tabs = con.execute("""
          SELECT table_schema, table_name, table_type
          FROM information_schema.tables
          WHERE table_schema='main'
          ORDER BY table_name
        """).df()
    print(tabs.to_string(index=False)); print()

    # 3) EVENTS — schéma & bornes
    print("3) EVENTS — Schéma & bornes")
    print("===========================")
    with duckdb.connect(db) as con:
        cols = con.execute("""
          SELECT column_name, data_type
          FROM information_schema.columns
          WHERE lower(table_name)='events'
          ORDER BY ordinal_position
        """).df()
        print(cols.to_string(index=False))
        try:
            rng = con.execute("""
              SELECT
                min(ts_utc) AS min_ts,
                max(ts_utc) AS max_ts,
                count(*)    AS n
              FROM events
            """).df().to_dict("records")
        except Exception:
            rng = []
    print(f"Bornes events: {rng}"); print()

    # 4) PRICES — vues normalisées & bornes
    print("4) PRICES — vues normalisées & bornes")
    print("=====================================")
    price_views = ["prices_1m_v","prices_5m_v","prices_m15_v","prices_m30_v","prices_1h_v","prices_h4_v"]
    with duckdb.connect(db) as con:
        for v in price_views:
            try:
                r = con.execute(f"""
                  SELECT min(ts_utc) AS min_ts, max(ts_utc) AS max_ts, count(*) AS n
                  FROM {v}
                """).df().to_dict("records")
                print(f"{v}: {r}")
            except Exception:
                pass
    print()

    # 5) LIVE FETCH — couverture & familles détectées (EODHD)
    print("5) LIVE FETCH — couverture & familles détectées (EODHD)")
    print("=======================================================")
    try:
        # fenêtre UTC [d1, d2]
        s, e = _utc_day_range(d1)
        if d2 != d1:
            # support multi-jour simple: on prend la journée d1 seulement dans cet audit
            pass
        raw = eod_fetch(s, e, countries=None, importance=None, api_key=os.getenv("EODHD_API_KEY"))
        print(f"EODHD: {len(raw)} éléments bruts.")
        df = eod_norm(raw) or pd.DataFrame()
        if not df.empty:
            # filtre pays si demandé
            if countries:
                df["country"] = df["country"].astype(str).str.upper()
                df = df[df["country"].isin(countries)]
            # familles
            df["family"] = df.apply(detect_family_row, axis=1)
            fam_counts = df["family"].value_counts(dropna=False).to_dict()
            print(f"Familles détectées: {fam_counts if fam_counts else {}}")
            print("\nAperçu (10 premières lignes filtrées pays):")
            cols = ["ts_utc","country","family","event_title","label","type","importance_n","estimate","forecast","previous","unit"]
            cols = [c for c in cols if c in df.columns]
            print(df.sort_values("ts_utc").head(10)[cols].to_string(index=False))
        else:
            print("Aucune ligne normalisée après fetch.")
    except Exception as e:
        print(f"Live fetch failed: {e}")
    print()

    # 6) FORECAST — stats rapides NFP/CPI/FOMC (si prix couvrent)
    print("6) FORECAST — stats par famille")
    print("===============================")
    try:
        from fx_impact_app.src.forecaster_mvp import ForecastRequest, forecast
        hist_to = pd.Timestamp.now(tz="UTC").tz_convert("UTC").tz_localize(None)
        hist_from = (hist_to - pd.DateOffset(years=int(args.hist_years))).tz_localize(None)

        fam_map = {
            "NFP": "(nonfarm|non-farm|nfp|payrolls|employment)",
            "CPI": "(\\bcpi\\b|consumer price|inflation)",
            "FOMC": "(fomc|federal reserve|fed funds|rate decision|press conference|minutes|sep|dot plot)"
        }

        with duckdb.connect(db) as con:
            max_price = con.execute("SELECT max(ts_utc) FROM prices_1m_v").fetchone()[0]
        if not pd.isna(max_price):
            hist_to = pd.Timestamp(max_price).tz_localize(None)

        for fam, regex in fam_map.items():
            req = ForecastRequest(
                event_family=fam,
                actual=0.0, consensus=0.0,
                country=(countries[0] if countries else "US"),
                window_before_min=60, window_after_min=15,
                horizons=[args.horizon],
                strict_decision=False,
            )
            stats, diags = forecast(req, time_from=hist_from, time_to=hist_to)
            out = [{"horizon": s.horizon, "n": s.n, "p_up": s.p_up, "mfe_med": s.mfe_med, "mfe_p80": s.mfe_p80} for s in stats]
            print(f"{fam}: {out} | price_max_ts={hist_to}")
    except Exception as e:
        print(f"Forecast stats failed: {e}")
    print()

    # 7) PRICES vs EVENTS — couverture (jour)
    print("7) PRICES vs EVENTS — couverture (jour)")
    print("=======================================")
    with duckdb.connect(db) as con:
        s, e = _utc_day_range(d1)
        n_ev = con.execute("""
          SELECT count(*) FROM events
          WHERE ts_utc >= ? AND ts_utc < ?
          """ , [s.to_pydatetime(), e.to_pydatetime()]).fetchone()[0]
        print(f"Events en base sur [{args.d1},{args.d2}]: {n_ev}")
        try:
            cov = con.execute("""
              SELECT min(ts_utc) AS min_ts, max(ts_utc) AS max_ts, count(*) AS n
              FROM prices_1m_v
              WHERE ts_utc >= ? - INTERVAL 12 HOUR
                AND ts_utc <  ? + INTERVAL 12 HOUR
            """, [s.to_pydatetime(), e.to_pydatetime()]).df().to_dict("records")
            print(f"Couverture prices_1m_v vs fenêtre d'événements: {cov}")
        except Exception:
            print("prices_1m_v indisponible.")
    print("\nDONE.")

if __name__ == "__main__":
    main()
