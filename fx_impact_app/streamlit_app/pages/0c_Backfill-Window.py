# fx_impact_app/streamlit_app/pages/0c_Backfill-Window.py
# -----------------------------------------------------------
# Backfill de prix intraday autour d'un événement
# - Vérifie la couverture de la fenêtre ±N minutes
# - Télécharge en tranches (EODHD) avec diagnostics détaillés
# - Fallback automatique EURUSD si EURUSD.FOREX est vide
# - Insertion dedup dans prices_1m (datetime, close)
# - Vue prices_1m_v (ts_utc, close)
# -----------------------------------------------------------

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Optional

import duckdb
import pandas as pd
import requests
import streamlit as st
from zoneinfo import ZoneInfo

# ---------------------------- Utilitaires TZ ----------------------------

def _to_utc_aware(ts: pd.Timestamp | str) -> pd.Timestamp:
    """Retourne un Timestamp aware UTC (naïf -> UTC, aware -> converti UTC)."""
    t = pd.to_datetime(ts, errors="raise")
    if t.tzinfo is None:
        return t.tz_localize("UTC")
    return t.tz_convert("UTC")

def _local_to_utc_naive(s: str, tz_name: str) -> pd.Timestamp:
    """
    Parse une chaîne locale 'YYYY-MM-DD HH:MM' en tz_name et renvoie un Timestamp UTC *naïf*.
    Robuste si la chaîne est déjà aware/UTC.
    """
    t = pd.to_datetime(s, errors="raise")
    if t.tzinfo is None:
        t = t.tz_localize(ZoneInfo(tz_name))
    t = t.tz_convert("UTC")
    return t.tz_localize(None)

def _fmt(ts: Optional[pd.Timestamp]) -> Optional[str]:
    if ts is None or pd.isna(ts):
        return None
    return pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def _epoch_s(ts: pd.Timestamp) -> int:
    ts_utc = _to_utc_aware(ts)
    return int(ts_utc.timestamp())

# ---------------------- Accès DB + structures --------------------------

def _ensure_view_prices_1m_v(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE OR REPLACE VIEW prices_1m_v AS
        SELECT CAST(datetime AS TIMESTAMP) AS ts_utc, close
        FROM prices_1m
        WHERE datetime IS NOT NULL
        ORDER BY ts_utc
    """)

def _ensure_prices_table_if_missing(con: duckdb.DuckDBPyConnection) -> None:
    exists = con.execute("""
        SELECT COUNT(*)::INT AS n
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = 'prices_1m'
    """).fetchone()[0]
    if not exists:
        con.execute("""
            CREATE TABLE prices_1m (
                datetime TIMESTAMPTZ,
                close DOUBLE
            )
        """)

def _upsert_prices(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> tuple[int, int]:
    n_before = con.execute("SELECT COUNT(*)::INT FROM prices_1m").fetchone()[0]
    con.register("df_new_prices", df[["datetime", "close"]])
    con.execute("""
        INSERT INTO prices_1m (datetime, close)
        SELECT datetime, close
        FROM df_new_prices n
        WHERE NOT EXISTS (
            SELECT 1 FROM prices_1m p WHERE p.datetime = n.datetime
        )
    """)
    con.unregister("df_new_prices")
    n_after = con.execute("SELECT COUNT(*)::INT FROM prices_1m").fetchone()[0]
    return n_before, n_after - n_before

# ------------------------------ Couverture -----------------------------

@dataclass
class Coverage:
    n_total: int
    n_have: int
    n_missing: int
    first_missing: Any
    last_missing: Any
    pct_missing: float
    start_utc: str
    end_utc: str

def _coverage(con: duckdb.DuckDBPyConnection, center_utc: pd.Timestamp, window_min: int) -> Coverage:
    start = (_to_utc_aware(center_utc) - pd.Timedelta(minutes=window_min)).floor("T")
    end   = (_to_utc_aware(center_utc) + pd.Timedelta(minutes=window_min)).floor("T")
    s = _fmt(start); e = _fmt(end)
    sql = f"""
    WITH g AS (
      SELECT "range" AS ts_utc
      FROM range(TIMESTAMP '{s}', TIMESTAMP '{e}', INTERVAL 1 MINUTE)
    )
    SELECT
      COUNT(*) AS n_total,
      SUM(CASE WHEN p.ts_utc IS NOT NULL THEN 1 ELSE 0 END) AS n_have,
      SUM(CASE WHEN p.ts_utc IS NULL THEN 1 ELSE 0 END)  AS n_missing,
      MIN(CASE WHEN p.ts_utc IS NULL THEN g.ts_utc END)  AS first_missing,
      MAX(CASE WHEN p.ts_utc IS NULL THEN g.ts_utc END)  AS last_missing
    FROM g
    LEFT JOIN prices_1m_v p
      ON p.ts_utc = g.ts_utc
    """
    row = con.execute(sql).df().iloc[0].to_dict()
    n_total   = int(row["n_total"])
    n_have    = int(row["n_have"] or 0)
    n_missing = int(row["n_missing"] or 0)
    pct = float(round((n_missing / n_total * 100.0), 1)) if n_total else 0.0
    return Coverage(
        n_total=n_total,
        n_have=n_have,
        n_missing=n_missing,
        first_missing=row.get("first_missing"),
        last_missing=row.get("last_missing"),
        pct_missing=pct,
        start_utc=s,
        end_utc=e,
    )

# ------------------------- Fetch EODHD + chunks ------------------------

def fetch_eodhd(symbol: str, start_utc: pd.Timestamp, end_utc: pd.Timestamp, api_key: str) -> tuple[pd.DataFrame, dict]:
    url = f"https://eodhd.com/api/intraday/{symbol}"
    params = {
        "interval": "1m",
        "from": _epoch_s(start_utc),
        "to": _epoch_s(end_utc),
        "fmt": "json",
        "api_token": api_key,
    }
    meta: dict[str, Any] = {"symbol": symbol}
    try:
        r = requests.get(url, params=params, timeout=30)
        meta.update({"status": r.status_code, "url": r.url})
        r.raise_for_status()
        try:
            data = r.json()
        except ValueError:
            meta["body_excerpt"] = (r.text or "")[:300]
            return pd.DataFrame(columns=["datetime", "close"]), meta

        if isinstance(data, dict) and "errors" in data:
            meta["errors"] = data.get("errors")
            return pd.DataFrame(columns=["datetime", "close"]), meta

        if not isinstance(data, list) or not data:
            meta["body_excerpt"] = str(data)[:300]
            return pd.DataFrame(columns=["datetime", "close"]), meta

        df = pd.DataFrame(data)

        # datetime
        if "datetime" in df.columns:
            dt = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
        elif "timestamp" in df.columns:
            dt = pd.to_datetime(df["timestamp"], unit="s", errors="coerce", utc=True)
        elif "t" in df.columns:
            dt = pd.to_datetime(df["t"], unit="s", errors="coerce", utc=True)
        else:
            meta["note"] = "Aucune colonne datetime/timestamp/t"
            return pd.DataFrame(columns=["datetime", "close"]), meta

        # close
        px = None
        for cand in ("close", "c", "adjusted_close"):
            if cand in df.columns:
                px = pd.to_numeric(df[cand], errors="coerce")
                break
        if px is None:
            meta["note"] = "Aucune colonne close/c/adjusted_close"
            return pd.DataFrame(columns=["datetime", "close"]), meta

        out = pd.DataFrame({"datetime": dt, "close": px}).dropna(subset=["datetime", "close"])
        return out.sort_values("datetime", kind="stable"), meta

    except requests.HTTPError as e:
        meta.update({"http_error": str(e)})
        try:
            meta["body_excerpt"] = (e.response.text or "")[:300]  # type: ignore[attr-defined]
        except Exception:
            pass
        return pd.DataFrame(columns=["datetime", "close"]), meta
    except Exception as e:
        meta.update({"exception": str(e)})
        return pd.DataFrame(columns=["datetime", "close"]), meta


def fetch_chunked(symbol: str, start_utc: pd.Timestamp, end_utc: pd.Timestamp, api_key: str,
                  chunk_minutes: int = 30, progress=None, record_chunks: list | None = None,
                  force_fallback: bool = True) -> pd.DataFrame:
    """
    Télécharge en tranches; tente EURUSD si EURUSD.FOREX renvoie vide.
    Logue *toutes* les tentatives, y compris fallback vide.
    """
    frames: list[pd.DataFrame] = []
    cur = _to_utc_aware(start_utc).floor("T")
    end_utc = _to_utc_aware(end_utc).floor("T")

    i = 0
    n_chunks = max(1, int((end_utc - cur).total_seconds() // (chunk_minutes * 60)) + 1)
    while cur < end_utc:
        i += 1
        nxt = min(end_utc, cur + pd.Timedelta(minutes=chunk_minutes))

        df, meta = fetch_eodhd(symbol, cur, nxt, api_key)

        # Fallback explicite
        fb_info = {}
        if force_fallback and symbol.endswith(".FOREX") and df.empty:
            fb_symbol = symbol.replace(".FOREX", "")
            df_fb, meta_fb = fetch_eodhd(fb_symbol, cur, nxt, api_key)
            fb_info = {
                "fallback_tried": True,
                "fallback_symbol": fb_symbol,
                "fallback_status": meta_fb.get("status"),
                "fallback_rows": int(len(df_fb)),
            }
            if not df_fb.empty:
                df, meta = df_fb, {**meta, "fallback": fb_symbol, **{f"fb_{k}": v for k, v in meta_fb.items() if k != "url"}}

        # Log tranche (FIX: on lit bien meta[k], pas 'v')
        if record_chunks is not None:
            keys = ("status", "url", "errors", "http_error", "exception", "body_excerpt", "note")
            rec = {
                "chunk": i,
                "start": _fmt(cur),
                "end": _fmt(nxt),
                "rows": int(len(df)),
                **{k: meta[k] for k in keys if k in meta},
                **fb_info,
            }
            record_chunks.append(rec)

        if not df.empty:
            frames.append(df)

        if progress:
            progress.progress(min(i / n_chunks, 1.0))
        cur = nxt

    if not frames:
        return pd.DataFrame(columns=["datetime", "close"])
    out = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["datetime"], keep="last")
    return out.sort_values("datetime", kind="stable")

# ------------------------------- UI -----------------------------------

st.set_page_config(page_title="Backfill de fenêtre (±N minutes)", page_icon="⏱️", layout="wide")
st.title("⏱️ Backfill de fenêtre (±N minutes) autour d'un événement")

from fx_impact_app.src.config import get_db_path
db_path = get_db_path()

colA, colB, colC = st.columns([1.2, 1.2, 1.2])
with colA:
    symbol = st.text_input("Symbole", value="EURUSD.FOREX")
with colB:
    tz_name = st.selectbox("Fuseau (local)", ["Europe/Zurich", "UTC", "Europe/Paris", "America/New_York"], index=0)
with colC:
    window_min = st.number_input("± Fenêtre (minutes)", min_value=15, max_value=240, value=120, step=15)

colD, colE, colF = st.columns([1.2, 1.2, 1])
with colD:
    default_local = pd.Timestamp.now(tz=ZoneInfo(tz_name)).strftime("%Y-%m-%d %H:%M")
    center_local_str = st.text_input("Centre (local, YYYY-MM-DD HH:MM)", value=default_local)
with colE:
    delay_min = st.number_input("Décaler la fin à (now - X min)", min_value=0, max_value=60, value=20, step=5,
                                help="Recadre la fin de la fenêtre pour éviter le délai provider (souvent ~15–20 min).")
with colF:
    force_fallback = st.checkbox("Essayer EURUSD si .FOREX vide", value=True)

# Centre UTC
try:
    center_utc = _local_to_utc_naive(center_local_str, tz_name)
except Exception as e:
    center_utc = None
    st.error(f"Horodatage invalide: {e}")

st.caption(f"DB: {db_path}")

# Affiche couverture avant backfill
if center_utc is not None:
    with duckdb.connect(db_path) as con:
        con.execute("PRAGMA threads=2")
        con.execute("PRAGMA preserve_insertion_order=false")
        _ensure_prices_table_if_missing(con)
        _ensure_view_prices_1m_v(con)
        before = _coverage(con, center_utc, window_min)
        st.subheader("Couverture actuelle (avant backfill)")
        st.json(asdict(before))

# -------------------------- Action Backfill ---------------------------

run = st.button("📥 Backfill maintenant (EODHD)")
chunks_log: list[dict[str, Any]] = []

if run and center_utc is not None:
    api_key = os.getenv("EODHD_API_KEY", "").strip()
    st.info(f"Clé EODHD détectée: {'✅' if bool(api_key) else '❌'}")

    start_req = (_to_utc_aware(center_utc) - pd.Timedelta(minutes=window_min)).floor("T")
    end_req   = (_to_utc_aware(center_utc) + pd.Timedelta(minutes=window_min)).floor("T")
    now_utc   = pd.Timestamp.now(tz=ZoneInfo("UTC")).floor("T")
    end_eff   = min(end_req, now_utc - pd.Timedelta(minutes=int(delay_min))) if delay_min > 0 else end_req
    info_block = {
        "api_key_present": bool(api_key),
        "start_utc": _fmt(start_req),
        "end_utc_requested": _fmt(end_req),
        "end_utc_effective": _fmt(end_eff),
        "chunk_minutes": 30,
    }

    # Si la fin effective est <= début, on informe et on log
    if end_eff <= start_req:
        info_block["note"] = "Fenêtre recadrée trop près du présent (délai). Ajuste le centre ou baisse delay_min."
        st.warning("Fenêtre trop courte après recadrage (now - délai). Baisse 'Décaler la fin' ou choisis un centre plus ancien.")
        st.json(info_block)
    else:
        st.write("Téléchargement EODHD par tranches…")
        prog = st.progress(0.0)

        try:
            df_ticks = fetch_chunked(
                symbol=symbol,
                start_utc=start_req,
                end_utc=end_eff,
                api_key=api_key,
                chunk_minutes=30,
                progress=prog,
                record_chunks=chunks_log,
                force_fallback=force_fallback,
            )

            with duckdb.connect(db_path) as con:
                con.execute("PRAGMA threads=2")
                con.execute("PRAGMA preserve_insertion_order=false")
                _ensure_prices_table_if_missing(con)
                _ensure_view_prices_1m_v(con)

                if not df_ticks.empty:
                    df_ticks = df_ticks.assign(
                        datetime=lambda d: pd.to_datetime(d["datetime"], utc=True)
                    )[["datetime", "close"]]

                n_before, n_ins = (0, 0)
                if not df_ticks.empty:
                    n_before, n_ins = _upsert_prices(con, df_ticks)

                after = _coverage(con, center_utc, window_min)

            st.subheader("Couverture après backfill")
            st.json(asdict(after))

            if df_ticks.empty:
                st.warning("L’API a retourné 0 ligne sur ces tranches. Causes probables: fenêtre trop récente (délai), symbole muet, "
                           "ou absence de données côté provider sur ce créneau.")
            st.success(f"Backfill terminé — récupérées: {len(df_ticks)} / insérées: {n_ins}")

        except Exception as e:
            info_block["error"] = str(e)
            st.error(f"Backfill échoué: {e}")

        # Diagnostics détaillés
        with st.expander("Diagnostics"):
            st.markdown("**Paramètres & Info**")
            st.json(info_block)
            st.markdown("**Tranches téléchargées**")
            st.json(chunks_log or [])
