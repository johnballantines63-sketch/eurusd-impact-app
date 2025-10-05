# fx_impact_app/scripts/ingest_prices_csv.py
from __future__ import annotations
import argparse
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import duckdb

# -----------------------------
# Timestamp helpers
# -----------------------------
def to_utc_aware(s: pd.Series, assume_tz: str | None = None) -> pd.Series:
    dt = pd.to_datetime(s, errors="coerce")
    if dt.isna().any():
        bad = int(dt.isna().sum())
        raise ValueError(f"{bad} invalid timestamp(s) in 'datetime' column.")

    try:
        has_tz = dt.dt.tz is not None
    except Exception:
        has_tz = False

    if not has_tz:
        if assume_tz:
            dt = dt.dt.tz_localize(ZoneInfo(assume_tz)).dt.tz_convert("UTC")
        else:
            dt = dt.dt.tz_localize("UTC")
    else:
        dt = dt.dt.tz_convert("UTC")

    return dt

def to_utc_naive(s: pd.Series, assume_tz: str | None = None) -> pd.Series:
    return to_utc_aware(s, assume_tz=assume_tz).dt.tz_convert("UTC").dt.tz_localize(None)

# -----------------------------
# CSV reading
# -----------------------------
def read_prices_csv(path: Path, dt_col: str | None, px_col: str | None,
                    assume_tz: str | None) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, sep=None, engine="python")
    except UnicodeDecodeError:
        df = pd.read_csv(path, sep=None, engine="python", encoding="latin-1")

    df.columns = [str(c).strip().lower() for c in df.columns]

    if not dt_col:
        for cand in ("datetime", "timestamp", "time", "date"):
            if cand in df.columns:
                dt_col = cand
                break
    if not px_col:
        for cand in ("close", "price", "last", "c"):
            if cand in df.columns:
                px_col = cand
                break

    if not dt_col or dt_col not in df.columns:
        raise RuntimeError(f"Datetime column not found. Columns: {list(df.columns)}")

    if not px_col or px_col not in df.columns:
        num_cols = [c for c in df.columns if c != dt_col and pd.api.types.is_numeric_dtype(df[c])]
        if num_cols:
            px_col = num_cols[0]
        else:
            raise RuntimeError(f"Price column not found. Columns: {list(df.columns)}")

    df = df[[dt_col, px_col]].rename(columns={dt_col: "datetime", px_col: "close"})

    if pd.api.types.is_object_dtype(df["close"]):
        df["close"] = df["close"].astype(str).str.replace(",", ".", regex=False)

    df["datetime"] = to_utc_aware(df["datetime"], assume_tz=assume_tz)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    n_before = len(df)
    df = df.dropna(subset=["datetime", "close"])
    df = (
        df.sort_values("datetime", kind="stable")
          .drop_duplicates(subset=["datetime"], keep="last")
          .reset_index(drop=True)
    )

    print("=== Lecture CSV ===")
    print(f"Fichier         : {path}")
    print(f"Colonnes brutes : {list(df.columns)} (après normalisation)")
    print(f"Lignes utiles   : {len(df)} (avant: {n_before})")
    print("Aperçu:")
    print(df.head(5).to_string(index=False))
    return df

# -----------------------------
# DuckDB objects
# -----------------------------
def table_columns(con: duckdb.DuckDBPyConnection, name: str) -> list[str]:
    try:
        info = con.execute(f"PRAGMA table_info('{name}')").df()
        return [str(c) for c in info["name"].tolist()]
    except Exception:
        return []

def choose_price_column(cols: list[str]) -> str | None:
    for cand in ("close", "c", "price", "last"):
        if cand in cols:
            return cand
    return None

def ensure_fallback_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS prices_1m_2c (
            datetime TIMESTAMPTZ,
            close    DOUBLE
        )
    """)
    try:
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_1m_2c_dt ON prices_1m_2c(datetime)")
    except Exception:
        pass

def create_or_replace_view(con: duckdb.DuckDBPyConnection,
                           have_main: bool,
                           main_px_col: str | None,
                           have_fallback: bool) -> None:
    # Build the UNION (with source rank to dedup preferring main, then fallback)
    parts = []
    if have_main and main_px_col:
        parts.append(f"""
            SELECT
              (datetime AT TIME ZONE 'UTC') AS ts_utc,
              CAST({main_px_col} AS DOUBLE) AS close,
              0 AS src
            FROM prices_1m
            WHERE datetime IS NOT NULL
        """)
    if have_fallback:
        parts.append("""
            SELECT
              (datetime AT TIME ZONE 'UTC') AS ts_utc,
              CAST(close AS DOUBLE) AS close,
              1 AS src
            FROM prices_1m_2c
            WHERE datetime IS NOT NULL
        """)

    if not parts:
        # No sources yet: create an empty view to avoid errors
        con.execute("""
          CREATE OR REPLACE VIEW prices_1m_v AS
          SELECT CAST(NULL AS TIMESTAMP) AS ts_utc, CAST(NULL AS DOUBLE) AS close
          WHERE FALSE
        """)
        return

    union_sql = " \nUNION ALL\n ".join(parts)

    con.execute(f"""
      CREATE OR REPLACE VIEW prices_1m_v AS
      WITH unioned AS (
        {union_sql}
      ),
      ranked AS (
        SELECT
          ts_utc, close,
          ROW_NUMBER() OVER (PARTITION BY ts_utc ORDER BY src ASC) AS rn
        FROM unioned
      )
      SELECT ts_utc, close
      FROM ranked
      WHERE rn = 1
      ORDER BY ts_utc
    """)

def ensure_tables_and_view(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("SET TimeZone='UTC'")

    # Detect existing main table
    main_cols = table_columns(con, "prices_1m")
    have_main = len(main_cols) > 0
    main_px_col = choose_price_column(main_cols) if have_main else None

    # Always ensure fallback exists (we may need it)
    ensure_fallback_table(con)

    # Build view using whatever sources are available
    create_or_replace_view(con, have_main, main_px_col, have_fallback=True)

# -----------------------------
# UPSERT logic
# -----------------------------
def try_insert_main(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> bool:
    main_cols = table_columns(con, "prices_1m")
    if not main_cols:
        # No main table → create minimal one (2 cols)
        con.execute("""
            CREATE TABLE prices_1m (
                datetime TIMESTAMPTZ,
                close    DOUBLE
            )
        """)
        try:
            con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_1m_dt ON prices_1m(datetime)")
        except Exception:
            pass
        main_cols = ["datetime", "close"]

    # Need a close-like column in main, else add one
    if "close" not in main_cols:
        try:
            con.execute("ALTER TABLE prices_1m ADD COLUMN close DOUBLE")
            main_cols = table_columns(con, "prices_1m")
        except Exception:
            # Can't alter → give up on main insert
            return False

    con.register("new_prices_df", df)
    try:
        con.execute("""
            INSERT INTO prices_1m (datetime, close)
            SELECT n.datetime, n.close
            FROM new_prices_df n
            WHERE NOT EXISTS (
                SELECT 1 FROM prices_1m p WHERE p.datetime = n.datetime
            )
        """)
        return True
    except Exception as e:
        print(f"⚠️  Insert into prices_1m failed, will fallback. Reason: {e}")
        return False
    finally:
        con.unregister("new_prices_df")

def insert_fallback(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    con.register("new_prices_df", df)
    con.execute("""
        INSERT INTO prices_1m_2c (datetime, close)
        SELECT n.datetime, n.close
        FROM new_prices_df n
        WHERE NOT EXISTS (
            SELECT 1 FROM prices_1m_2c p WHERE p.datetime = n.datetime
        )
    """)
    con.unregister("new_prices_df")

def upsert_prices(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> tuple[int,int]:
    # Count BEFORE across both sources for a fair “inserted” figure
    n_before = con.execute("""
        SELECT COUNT(*) FROM (
          SELECT ts_utc FROM prices_1m_v
        )
    """).fetchone()[0]

    # Try main first; if it fails, fallback
    ok = try_insert_main(con, df)
    if not ok:
        insert_fallback(con, df)

    # Rebuild the view (schema may have evolved)
    ensure_tables_and_view(con)

    n_after = con.execute("""
        SELECT COUNT(*) FROM (
          SELECT ts_utc FROM prices_1m_v
        )
    """).fetchone()[0]
    return n_before, (n_after - n_before)

# -----------------------------
# CLI
# -----------------------------
def main():
    ap = argparse.ArgumentParser(description="Ingestion CSV → DuckDB prices (robuste) + vue prices_1m_v")
    ap.add_argument("csv_path", type=str, help="Chemin du CSV (doit contenir datetime & close)")
    ap.add_argument("--dt-col", type=str, default=None, help="Nom de colonne datetime (auto si omis)")
    ap.add_argument("--px-col", type=str, default=None, help="Nom de colonne prix (auto si omis)")
    ap.add_argument("--assume-tz", type=str, default=None,
                    help="Si datetimes sans TZ, préciser le fuseau (ex: 'Europe/Zurich'); sinon on suppose UTC.")
    ap.add_argument("--db", type=str, default=None, help="Chemin DuckDB (défaut: config.get_db_path())")
    args = ap.parse_args()

    from fx_impact_app.src.config import get_db_path
    db_path = args.db or get_db_path()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV introuvable: {csv_path}")

    df = read_prices_csv(
        csv_path,
        dt_col=args.dt_col,
        px_col=args.px_col,
        assume_tz=args.assume_tz,
    )
    if df.empty:
        print("❌ CSV lu mais aucune ligne exploitable (datetime/prix).")
        return

    with duckdb.connect(db_path) as con:
        con.execute("PRAGMA threads=2")
        con.execute("PRAGMA preserve_insertion_order=false")
        ensure_tables_and_view(con)
        n_before, n_ins = upsert_prices(con, df)

        stats_view = con.execute("""
            SELECT COUNT(*) AS n, min(ts_utc) AS min_ts, max(ts_utc) AS max_ts
            FROM prices_1m_v
        """).df().iloc[0].to_dict()

    print("\n✅ Ingestion terminée")
    print(f"DB                : {db_path}")
    print(f"Lignes lues       : {len(df)}")
    print(f"Lignes insérées   : {n_ins} (mesuré sur la vue unifiée)")
    print(f"prices_1m_v (vue) : {stats_view}")

if __name__ == "__main__":
    main()
