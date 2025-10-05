from __future__ import annotations
import argparse, os
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

import requests
import pandas as pd
import duckdb

# ---------- time helpers ----------
def _to_utc_aware(ts: str | pd.Timestamp) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        return t.tz_localize("UTC")
    return t.tz_convert("UTC")

def _utc_naive(ts: pd.Timestamp) -> pd.Timestamp:
    return ts.tz_convert("UTC").tz_localize(None)

def _epoch_seconds(t: pd.Timestamp) -> int:
    return int(t.tz_convert("UTC").timestamp())

# ---------- DuckDB storage & coverage ----------
def ensure_storage(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS prices_1m (
            datetime TIMESTAMPTZ,
            close DOUBLE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            volume DOUBLE,
            symbol VARCHAR,
            source VARCHAR
        )
    """)
    con.execute("""
        CREATE OR REPLACE VIEW prices_1m_v AS
        SELECT CAST(datetime AS TIMESTAMP) AS ts_utc, close
        FROM prices_1m
        WHERE datetime IS NOT NULL
        ORDER BY ts_utc
    """)

def coverage(con: duckdb.DuckDBPyConnection,
             start_utc: pd.Timestamp,
             end_utc: pd.Timestamp) -> Dict[str, Any]:
    row = con.execute("""
        WITH g AS (
          SELECT "range" AS ts_utc
          FROM range(?, ?, INTERVAL 1 MINUTE)
        )
        SELECT
          COUNT(*) AS n_total,
          SUM(CASE WHEN p.ts_utc IS NOT NULL THEN 1 ELSE 0 END) AS n_have,
          SUM(CASE WHEN p.ts_utc IS NULL THEN 1 ELSE 0 END)  AS n_missing,
          MIN(CASE WHEN p.ts_utc IS NULL THEN g.ts_utc END)  AS first_missing,
          MAX(CASE WHEN p.ts_utc IS NULL THEN g.ts_utc END)  AS last_missing
        FROM g
        LEFT JOIN prices_1m_v p ON p.ts_utc = g.ts_utc
    """, [_utc_naive(start_utc), _utc_naive(end_utc)]).df().iloc[0].to_dict()

    for k in ("first_missing", "last_missing"):
        if isinstance(row.get(k), pd.Timestamp):
            row[k] = str(row[k])
    row["start_utc"] = str(_utc_naive(start_utc))
    row["end_utc"]   = str(_utc_naive(end_utc))
    row["pct_missing"] = round(
        100.0 * float(row["n_missing"]) / float(row["n_total"]), 1
    ) if row["n_total"] else 0.0
    return row

def upsert_prices(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> Tuple[int, int]:
    n_before = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
    con.register("new_px", df)
    con.execute("""
        INSERT INTO prices_1m (datetime, close)
        SELECT datetime, close
        FROM new_px n
        WHERE NOT EXISTS (
            SELECT 1 FROM prices_1m p WHERE p.datetime = n.datetime
        )
    """)
    con.unregister("new_px")
    n_after = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
    return n_before, (n_after - n_before)

# ---------- EODHD fetch ----------
@dataclass
class ChunkLog:
    chunk: int
    start: str
    end: str
    rows: int
    status: int
    url: str
    body_excerpt: Optional[str] = None

def fetch_intraday_eodhd(symbol: str,
                         start_utc: pd.Timestamp,
                         end_utc: pd.Timestamp,
                         api_key: str) -> pd.DataFrame:
    url = f"https://eodhd.com/api/intraday/{symbol}"
    params = {
        "interval": "1m",
        "from": _epoch_seconds(start_utc),
        "to": _epoch_seconds(end_utc),
        "fmt": "json",
        "api_token": api_key,
    }
    r = requests.get(url, params=params, timeout=30)
    try:
        data = r.json()
    except Exception:
        data = None
    if r.status_code != 200:
        raise RuntimeError(f"EODHD {symbol} failed: {r.status_code} — {r.text[:200]}")
    if not isinstance(data, list) or len(data) == 0:
        return pd.DataFrame(columns=["datetime", "close"])

    df = pd.DataFrame(data)
    dt_col = next((c for c in df.columns if c.lower() in ("datetime", "timestamp", "date", "time", "t")), None)
    px_col = next((c for c in df.columns if c.lower() in ("close", "c", "price", "last")), None)
    if not dt_col or not px_col:
        raise RuntimeError(f"Intraday payload unexpected columns: {list(df.columns)}")

    if str(dt_col).lower() == "t":
        df["datetime"] = pd.to_datetime(df["t"], unit="s", utc=True)
    else:
        df["datetime"] = pd.to_datetime(df[dt_col], errors="coerce")
        if df["datetime"].dt.tz is None:
            df["datetime"] = df["datetime"].dt.tz_localize("UTC")
        else:
            df["datetime"] = df["datetime"].dt.tz_convert("UTC")

    df["close"] = pd.to_numeric(df[px_col], errors="coerce")
    df = df.dropna(subset=["datetime", "close"]).sort_values("datetime").drop_duplicates(subset=["datetime"])
    return df[["datetime", "close"]]

def backfill_chunks(symbol: str,
                    start_utc: pd.Timestamp,
                    end_utc: pd.Timestamp,
                    api_key: str,
                    chunk_minutes: int = 30) -> Tuple[pd.DataFrame, List[ChunkLog]]:
    logs: List[ChunkLog] = []
    parts: List[pd.DataFrame] = []
    cur = start_utc
    i = 0
    while cur < end_utc:
        i += 1
        nxt = min(cur + pd.Timedelta(minutes=chunk_minutes), end_utc)
        try:
            df = fetch_intraday_eodhd(symbol, cur, nxt, api_key)
            rows = len(df); status = 200; excerpt = None
        except Exception as e:
            df = pd.DataFrame(columns=["datetime", "close"])
            rows = 0; status = 500; excerpt = str(e)[:200]
        logs.append(ChunkLog(
            chunk=i,
            start=str(_utc_naive(cur)),
            end=str(_utc_naive(nxt)),
            rows=rows,
            status=status,
            url=f"https://eodhd.com/api/intraday/{symbol}?interval=1m&from={_epoch_seconds(cur)}&to={_epoch_seconds(nxt)}&fmt=json&api_token=***",
            body_excerpt=excerpt
        ))
        if rows > 0:
            parts.append(df)
        cur = nxt

    if parts:
        out = pd.concat(parts, ignore_index=True).sort_values("datetime").drop_duplicates(subset=["datetime"])
        return out, logs
    return pd.DataFrame(columns=["datetime", "close"]), logs

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Vérifie la couverture 1m et backfill via EODHD si besoin.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--center", type=str, help='Centre (UTC si naïf), ex: "2025-10-01 14:15"')
    g.add_argument("--start", type=str, help='Début (UTC si naïf), ex: "2025-10-02 12:00"')
    ap.add_argument("--end", type=str, help='Fin (UTC si naïf) si --start est utilisé')
    ap.add_argument("--window-min", type=int, default=120, help="Valeur ±N minutes autour de --center (total=2N)")
    ap.add_argument("--symbol", type=str, default="EURUSD.FOREX", help="Symbole EODHD intraday")
    ap.add_argument("--chunk-minutes", type=int, default=30, help="Taille de tranche (minutes)")
    ap.add_argument("--db", type=str, default=None, help="Chemin DuckDB (défaut: config.get_db_path())")
    args = ap.parse_args()

    # Fenêtre: center ± window_min  (donc 2N minutes au total)
    if args.center:
        center = _to_utc_aware(args.center)
        start_utc = center - pd.Timedelta(minutes=args.window_min)
        end_utc   = center + pd.Timedelta(minutes=args.window_min)
    else:
        if not args.end:
            ap.error("--end est requis quand --start est fourni")
        start_utc = _to_utc_aware(args.start)
        end_utc   = _to_utc_aware(args.end)

    api_key = os.getenv("EODHD_API_KEY") or ""
    from fx_impact_app.src.config import get_db_path
    db_path = args.db or get_db_path()

    print(f"DB: {db_path}")
    print(f"Symbol: {args.symbol}")
    print(f"Window UTC: [{start_utc} .. {end_utc}]")
    print(f"Chunk minutes: {args.chunk_minutes}")
    if not api_key.strip():
        print("⚠️  EODHD_API_KEY manquante dans l’environnement.")
        return

    with duckdb.connect(db_path) as con:
        ensure_storage(con)

        before = coverage(con, start_utc, end_utc)
        print("\nAvant backfill — couverture:")
        print(pd.Series(before).to_string())

        df, logs = backfill_chunks(args.symbol, start_utc, end_utc, api_key, args.chunk_minutes)
        fetched = len(df); inserted = 0
        if fetched > 0:
            _, inserted = upsert_prices(con, df)

        if logs:
            print("\nDétail des tranches:")
            for l in logs:
                print(pd.Series({
                    "chunk": l.chunk, "start": l.start, "end": l.end,
                    "rows": l.rows, "status": l.status, "url": l.url,
                    "body_excerpt": l.body_excerpt
                }).to_string())
                print("-" * 40)

        print(f"\nBackfill terminé — récupérées: {fetched} / insérées: {inserted}")

        after = coverage(con, start_utc, end_utc)
        print("\nAprès backfill — couverture:")
        print(pd.Series(after).to_string())

if __name__ == "__main__":
    main()
