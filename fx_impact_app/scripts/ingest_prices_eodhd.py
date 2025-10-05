# fx_impact_app/scripts/ingest_prices_eodhd.py
from __future__ import annotations
import argparse
import os
from dataclasses import dataclass
from typing import Tuple

import duckdb
import pandas as pd
import requests


@dataclass
class IntradayWindow:
    symbol: str
    start_utc: pd.Timestamp
    end_utc: pd.Timestamp


# -------------------------------
# Helpers
# -------------------------------
def _env_key() -> str:
    k = os.getenv("EODHD_API_KEY", "").strip()
    if not k:
        raise RuntimeError("Missing EODHD_API_KEY in environment (ou .env).")
    return k


def _to_epoch_seconds(ts: pd.Timestamp) -> int:
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return int(ts.timestamp())


def _normalize_intraday_json(obj) -> pd.DataFrame:
    """
    Mappe la réponse intraday EODHD -> DataFrame [datetime(UTC aware), close(float)] triée & dédupliquée.
    """
    df = pd.DataFrame(obj)
    if df.empty:
        return df

    # Datetime
    if "timestamp" in df.columns:
        dt = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    elif "datetime" in df.columns:
        dt = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
    else:
        raise RuntimeError("Payload intraday inattendu: pas de 'timestamp' ni 'datetime'.")

    # Close
    close_col = None
    for c in ("close", "c", "Close", "CLOSE"):
        if c in df.columns:
            close_col = c
            break
    if close_col is None:
        raise RuntimeError("Payload intraday inattendu: pas de colonne 'close'.")

    out = pd.DataFrame(
        {"datetime": dt, "close": pd.to_numeric(df[close_col], errors="coerce")}
    ).dropna(subset=["datetime", "close"])

    out = (
        out.sort_values("datetime", kind="stable")
           .drop_duplicates(subset=["datetime"], keep="last")
           .reset_index(drop=True)
    )
    return out


# -------------------------------
# DuckDB storage (compat toujours présent)
# -------------------------------
def _prices_1m_schema(con: duckdb.DuckDBPyConnection):
    try:
        info = con.execute("PRAGMA table_info('prices_1m')").df()
        if info.empty:
            return None
        return [r["name"] for _, r in info.iterrows()]
    except Exception:
        return None


def _ensure_storage(con: duckdb.DuckDBPyConnection) -> str:
    """
    - Crée si besoin:
        * prices_1m (si absente) — mais on ne force pas son schéma; on détecte ensuite.
        * prices_1m_compat (toujours, 2 colonnes: datetime, close)
    - (Re)crée la vue prices_1m_v comme union normalisée des deux.
    - Retourne le nom de la table d'insertion:
        * 'prices_1m' si elle a exactement (datetime, close)
        * sinon 'prices_1m_compat'
    """
    con.execute("SET TimeZone='UTC'")

    # S'assurer que la compat existe toujours
    con.execute("""
        CREATE TABLE IF NOT EXISTS prices_1m_compat (
            datetime TIMESTAMPTZ,
            close DOUBLE
        )
    """)
    try:
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_1m_compat_dt ON prices_1m_compat(datetime)")
    except Exception:
        pass

    # Créer prices_1m si absente (au cas où) — schéma minimal 2 colonnes
    if _prices_1m_schema(con) is None:
        con.execute("""
            CREATE TABLE prices_1m (
                datetime TIMESTAMPTZ,
                close DOUBLE
            )
        """)
        try:
            con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_1m_dt ON prices_1m(datetime)")
        except Exception:
            pass

    # Déterminer table d'insertion
    cols = _prices_1m_schema(con) or []
    wanted = {"datetime", "close"}
    target = "prices_1m" if set(c.lower() for c in cols) == wanted else "prices_1m_compat"

    # (Re)créer la vue (union des deux tables, quelle que soit leur présence/contenu)
    con.execute("""
      CREATE OR REPLACE VIEW prices_1m_v AS
      SELECT CAST(datetime AS TIMESTAMP) AS ts_utc, close
      FROM prices_1m
      WHERE datetime IS NOT NULL
      UNION ALL
      SELECT CAST(datetime AS TIMESTAMP) AS ts_utc, close
      FROM prices_1m_compat
      WHERE datetime IS NOT NULL
      ORDER BY ts_utc
    """)

    return target


def _upsert_prices(con: duckdb.DuckDBPyConnection, df: pd.DataFrame, target_table: str) -> Tuple[int, int]:
    n_before = con.execute("SELECT COUNT(*) FROM prices_1m_v").fetchone()[0]

    con.register("new_prices_df", df)
    # Anti-doublon contre la vue (couvre les 2 tables)
    con.execute(f"""
        INSERT INTO {target_table} (datetime, close)
        SELECT n.datetime, n.close
        FROM new_prices_df n
        WHERE NOT EXISTS (
            SELECT 1 FROM prices_1m_v v
            WHERE v.ts_utc = CAST(n.datetime AS TIMESTAMP)
        )
    """)
    con.unregister("new_prices_df")

    n_after = con.execute("SELECT COUNT(*) FROM prices_1m_v").fetchone()[0]
    return n_before, (n_after - n_before)


# -------------------------------
# Fetch EODHD intraday
# -------------------------------
def _fetch_intraday(win: IntradayWindow, api_key: str) -> pd.DataFrame:
    frm = _to_epoch_seconds(win.start_utc)
    to  = _to_epoch_seconds(win.end_utc)

    url = f"https://eodhd.com/api/intraday/{win.symbol}"
    params = {
        "interval": "1m",
        "from": frm,               # UNIX seconds (entier)
        "to": to,                  # UNIX seconds (entier)
        "fmt": "json",
        "api_token": api_key,
    }

    # Log debug (montre bien les entiers)
    print(f"Request params: {params}")

    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(
            f"EODHD intraday request failed: {r.status_code} {r.reason}\n"
            f"URL: {r.url}\nBody: {r.text}"
        )
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON from EODHD.\nURL: {r.url}\nBody: {r.text[:500]}")

    return _normalize_intraday_json(data)


# -------------------------------
# CLI
# -------------------------------
def main():
    ap = argparse.ArgumentParser(description="Backfill intraday prices around an event using EODHD.")
    ap.add_argument("--symbol", required=True, help="Ex: EURUSD.FOREX")
    ap.add_argument("--event-ts", required=True, help='UTC, ex: "2025-10-01 14:15"')
    ap.add_argument("--window-min", type=int, default=180, help="± minutes (défaut 180 = ±3h)")
    ap.add_argument("--db", default=None, help="DuckDB path (défaut: config.get_db_path())")
    args = ap.parse_args()

    # DB path
    from fx_impact_app.src.config import get_db_path
    db_path = args.db or get_db_path()

    # Fenêtre UTC
    event_utc = pd.to_datetime(args.event_ts, utc=True)
    start_utc = event_utc - pd.Timedelta(minutes=args.window_min)
    end_utc   = event_utc + pd.Timedelta(minutes=args.window_min)

    print(f"DB: {db_path}")
    print(f"Symbol: {args.symbol}")
    print(f"Window UTC: [{start_utc} .. {end_utc}]")

    key = _env_key()
    win = IntradayWindow(symbol=args.symbol, start_utc=start_utc, end_utc=end_utc)

    df = _fetch_intraday(win, key)
    if df.empty:
        print("EODHD intraday returned 0 rows for this window.")
        return

    with duckdb.connect(db_path) as con:
        con.execute("PRAGMA threads=2")
        con.execute("PRAGMA preserve_insertion_order=false")

        target = _ensure_storage(con)
        n_before, n_ins = _upsert_prices(con, df, target)

        vstats = con.execute("""
            SELECT COUNT(*) AS n, min(ts_utc) AS min_ts, max(ts_utc) AS max_ts
            FROM prices_1m_v
        """).df().iloc[0].to_dict()

    print("\n✅ Ingestion terminée")
    print(f"Lignes récupérées : {len(df)}")
    print(f"Lignes avant ins. : {n_before}")
    print(f"Lignes insérées   : {n_ins}")
    print(f"prices_1m_v (vue) : {vstats}")


if __name__ == "__main__":
    main()
