# fx_impact_app/scripts/audit_suite.py
from __future__ import annotations
import os, sys, platform, traceback
from pathlib import Path
from datetime import datetime, timezone
import duckdb
import pandas as pd

# -----------------------------
# Local helpers
# -----------------------------
def now_iso() -> str:
    # ISO UTC avec suffixe Z (pas de DeprecationWarning)
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def section(title: str) -> None:
    print("\n" + title)
    print("=" * len(title))

# -----------------------------
# DB path (V5) + fallback
# -----------------------------
ROOT = Path(__file__).resolve().parents[2]
try:
    from fx_impact_app.src.config import get_db_path
    DB = get_db_path()
except Exception:
    DB = (ROOT / "fx_impact_app" / "data" / "warehouse.duckdb").as_posix()

# -----------------------------
# Tuning (utilise db_tuning si dispo)
# -----------------------------
def _tune_via_module(con: duckdb.DuckDBPyConnection, mem_gb=4, threads=2, max_temp_gb=50):
    try:
        from fx_impact_app.src.db_tuning import tune
        tune(con, mem_gb=mem_gb, threads=threads, max_temp_gb=max_temp_gb)
    except Exception:
        # Fallback minimal compatible DuckDB 1.4.x
        try:
            con.execute(f"PRAGMA threads={threads}")
        except Exception:
            pass
        try:
            tmp = Path(DB).with_suffix(".tmp")
            tmp.mkdir(exist_ok=True)
            con.execute(f"PRAGMA temp_directory='{tmp.as_posix()}'")
        except Exception:
            pass
        try:
            con.execute(f"PRAGMA max_temp_directory_size='{max_temp_gb}GiB'")
        except Exception:
            pass
        # memory_limit non lisible/paramétrable de façon portable sur 1.4.x ⇒ on ignore

def show_settings(con: duckdb.DuckDBPyConnection) -> dict[str, str]:
    out = {}
    for p in ["threads", "memory_limit", "temp_directory", "max_temp_directory_size", "preserve_insertion_order"]:
        try:
            out[p] = con.execute(f"PRAGMA {p}").fetchone()[0]
        except Exception:
            out[p] = "N/A"
    return out

# -----------------------------
# Prix : créer/rafraîchir les vues normalisées *_v
# -----------------------------
PRICE_BASES = ["prices_1m", "prices_5m", "prices_m15", "prices_m30", "prices_1h", "prices_h4"]

def table_exists(con: duckdb.DuckDBPyConnection, name: str) -> bool:
    q = """
      SELECT 1
      FROM information_schema.tables
      WHERE lower(table_name)=lower(?)
      LIMIT 1
    """
    return con.execute(q, [name]).fetchone() is not None

def cols_lower(con: duckdb.DuckDBPyConnection, table: str) -> list[str]:
    q = """
      SELECT lower(column_name)
      FROM information_schema.columns
      WHERE lower(table_name)=lower(?)
    """
    return [r[0] for r in con.execute(q, [table]).fetchall()]

def ensure_price_view(con: duckdb.DuckDBPyConnection, base: str) -> str | None:
    """Crée/replace <base>_v(ts_utc, close) si <base>(datetime, close) existe."""
    if not table_exists(con, base):
        return None
    cl = cols_lower(con, base)
    if "datetime" not in cl or "close" not in cl:
        return None
    view = f"{base}_v"
    con.execute(f"""
        CREATE OR REPLACE VIEW {view} AS
        SELECT CAST(datetime AS TIMESTAMP) AS ts_utc, close
        FROM {base}
        WHERE datetime IS NOT NULL
        ORDER BY datetime
    """)
    return view

def bounds_for_view(con: duckdb.DuckDBPyConnection, view: str) -> dict | None:
    try:
        return con.execute(
            f"SELECT min(ts_utc) AS min_ts, max(ts_utc) AS max_ts, count(*) AS n FROM {view}"
        ).df().to_dict(orient="records")[0]
    except Exception:
        return None

# -----------------------------
# Forecaster (smoke test)
# -----------------------------
def smoke_forecast(con: duckdb.DuckDBPyConnection) -> tuple[dict, list[dict]]:
    from fx_impact_app.src.forecaster_mvp import ForecastRequest, forecast
    req = ForecastRequest(event_family="NFP", actual=250, consensus=180, horizons=[15, 30, 60])
    stats, diags = forecast(req)
    stats_out = []
    for s in stats:
        stats_out.append({"h": s.horizon, "n": s.n, "p_up": s.p_up, "mfe_med": s.mfe_med, "mfe_p80": s.mfe_p80})
    return diags, stats_out

# -----------------------------
# Screener (échantillon ancrages 90j FOMC)
# -----------------------------
FOMC_REGEX = (
    r"(?i)(fomc|federal reserve|fed funds|federal funds|target rate|"
    r"rate decision|interest rate|policy statement|press conference|"
    r"dot plot|economic projections|summary of economic projections|sep|minutes)"
)

def anchors_sample(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    end = pd.Timestamp.now(tz="UTC").tz_convert("UTC").tz_localize(None)
    start = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=90)).tz_convert("UTC").tz_localize(None)

    # Événements FOMC dans la fenêtre
    q_ev = """
      SELECT CAST(ts_utc AS TIMESTAMP) AS ts_utc
      FROM events
      WHERE ts_utc BETWEEN ? AND ?
        AND regexp_matches(lower(coalesce(event_key,'')) || ' ' || lower(coalesce(event_title,'')), ?)
    """
    ev = con.execute(q_ev, [start, end, FOMC_REGEX]).df()
    if ev.empty:
        return pd.DataFrame(columns=["anchor_ts", "n_simul"])

    # Compte de simultanés ±30m
    q_anchors = """
      WITH ev AS (
        SELECT CAST(ts_utc AS TIMESTAMP) AS ts_utc
        FROM events
        WHERE ts_utc BETWEEN ? AND ?
          AND regexp_matches(lower(coalesce(event_key,'')) || ' ' || lower(coalesce(event_title,'')), ?)
      )
      SELECT a.ts_utc AS anchor_ts, COUNT(*) AS n_simul
      FROM ev a
      JOIN ev b
        ON b.ts_utc BETWEEN a.ts_utc - INTERVAL 30 MINUTE
                        AND a.ts_utc + INTERVAL 30 MINUTE
      GROUP BY 1
      ORDER BY anchor_ts DESC
      LIMIT 10
    """
    return con.execute(q_anchors, [start, end, FOMC_REGEX]).df()

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("=== AUDIT SUITE — FX Impact App (V5) ===")
    print(f"Run at: {now_iso()}")
    print(f"Python  : {platform.python_version()} ({platform.python_version()}) [{platform.platform()}]")
    print(f"DuckDB  : {duckdb.__version__}")
    print(f"pandas  : {pd.__version__}")
    print(f"Project : {ROOT.as_posix()}")
    print(f"DB Path : {DB}")

    # 1) PRAGMA / ENV
    section("1) PRAGMA / ENV")
    try:
        with duckdb.connect(DB) as con:
            _tune_via_module(con, mem_gb=4, threads=2, max_temp_gb=50)
            s = show_settings(con)
            for k in ["threads", "memory_limit", "temp_directory", "max_temp_directory_size", "preserve_insertion_order"]:
                print(f"{k:>28}: {s.get(k, 'N/A')}")
    except Exception as e:
        print("!! PRAGMA/ENV failed:")
        traceback.print_exc()

    # 2) TABLES
    section("2) TABLES")
    try:
        with duckdb.connect(DB) as con:
            df = con.execute("""
              SELECT table_schema, table_name, table_type
              FROM information_schema.tables
              ORDER BY 1,2
            """).df()
            if df.empty:
                print("(none)")
            else:
                print(df.to_string(index=False))
    except Exception:
        traceback.print_exc()

    # 3) EVENTS — Schéma & bornes
    section("3) EVENTS — Schéma & bornes")
    try:
        with duckdb.connect(DB) as con:
            schema = con.execute("""
              SELECT column_name, data_type
              FROM information_schema.columns
              WHERE lower(table_name)='events'
              ORDER BY ordinal_position
            """).df()
            print(schema.to_string(index=False))

            bounds = con.execute("""
              SELECT min(ts_utc) AS min_ts, max(ts_utc) AS max_ts, count(*) AS n FROM events
            """).df().to_dict(orient="records")
            print("Bornes events:", bounds)

            for name, rx in [("NFP", r"(?i)(nonfarm|non-farm|nfp|payrolls|employment)"),
                             ("CPI", r"(?i)\bcpi\b|consumer price"),
                             ("FOMC", FOMC_REGEX)]:
                n = con.execute("""
                  SELECT count(*) FROM events
                  WHERE regexp_matches(lower(coalesce(event_key,'')) || ' ' || lower(coalesce(event_title,'')), ?)
                """, [rx]).fetchone()[0]
                print(f"Count {name} :", n)
    except Exception:
        traceback.print_exc()

    # 4) PRICES — vues normalisées & bornes
    section("4) PRICES — vues normalisées & bornes")
    try:
        with duckdb.connect(DB) as con:
            any_view = False
            for base in PRICE_BASES:
                v = ensure_price_view(con, base)
                if v:
                    any_view = True
                    b = bounds_for_view(con, v)
                    print(f"{v}:", [b] if b else "(no bounds)")
            if not any_view:
                print("Aucune vue normalisée détectée (ex: prices_1m_v).")
    except Exception:
        traceback.print_exc()

    # 5) FORECAST — smoke test NFP
    section("5) FORECAST — smoke test NFP")
    try:
        with duckdb.connect(DB) as con:
            diags, stats = smoke_forecast(con)
            print("Diagnostics:", diags)
            print("Stats:", stats)
    except Exception:
        traceback.print_exc()

    # 6) SCREENER — anchors sample (90j, FOMC)
    section("6) SCREENER — anchors sample (90j, FOMC)")
    try:
        with duckdb.connect(DB) as con:
            # S'assurer qu'on a au moins la vue 1m (utile pour d'autres checks)
            ensure_price_view(con, "prices_1m")
            print("prices_1m_v:", [bounds_for_view(con, "prices_1m_v")])
            df = anchors_sample(con)
            if df.empty:
                print("No anchors in last 90d (with current filters).")
            else:
                print("Anchors sample (last 10):")
                # format propre : colonnes triées
                cols = ["anchor_ts", "n_simul"]
                print(df[cols].to_string(index=False))
    except Exception:
        traceback.print_exc()

    # 7) DONE
    section("7) DONE")
