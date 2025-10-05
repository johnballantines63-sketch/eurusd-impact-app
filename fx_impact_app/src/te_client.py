# fx_impact_app/src/te_client.py
from __future__ import annotations
import requests
import pandas as pd
from typing import Any, Dict, List, Optional
from .config import get_te_key as _get_te_key_config

TE_BASE = "https://api.tradingeconomics.com/calendar"

def get_te_key(key_in: Optional[str] = None) -> str:
    if key_in:
        return key_in
    k = _get_te_key_config()
    if not k:
        raise RuntimeError("Missing TE_API_KEY.")
    return key_in
    env = load_env_keys()
    k = env.get("TE_API_KEY")
    if not k:
        raise RuntimeError("Missing TE_API_KEY.")
    return k

def _to_date_str(x) -> str:
    ts = pd.Timestamp(x)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC")
    return ts.date().isoformat()

def fetch_calendar_json(
    d1, d2, *, countries: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    importance: Optional[List[int]] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    # NB: selon ton plan, /calendar peut retourner 403 → on laisse une erreur claire côté appelant.
    key = get_te_key(api_key)
    params = {
        "format": "json",
        "d1": _to_date_str(d1),
        "d2": _to_date_str(d2),
        "c": key,
    }
    if countries:
        params["country"] = ",".join(countries)
    if categories:
        params["category"] = ",".join(categories)
    if importance:
        params["importance"] = ",".join(str(i) for i in importance)

    r = requests.get(TE_BASE, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    return data

def calendar_to_events_df(items: List[Dict[str, Any]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=[
            "ts_utc","country","event_title","event_key",
            "importance_n","previous","estimate","forecast",
            "actual","unit","type"
        ])
    df = pd.json_normalize(items)

    def pick(*cols):
        for c in cols:
            if c in df.columns:
                return df[c]
        return pd.Series([None]*len(df))

    # TE a souvent "DateUtc" ou "Date" ISO
    ts = pick("DateUtc","Date","DateISO","date")
    ts = pd.to_datetime(ts, utc=True, errors="coerce")

    out = pd.DataFrame({
        "ts_utc": ts,
        "country": pick("Country","country").astype("string"),
        "event_title": pick("Event","Title","event").astype("string"),
        "event_key": pick("Event","Title","event").astype("string").str.lower(),
        "importance_n": pd.to_numeric(pick("Importance","importance","ImportanceValue"), errors="coerce"),
        "previous": pd.to_numeric(pick("Previous","previous"), errors="coerce"),
        "estimate": pd.to_numeric(pick("Estimate","estimate"), errors="coerce"),
        "forecast": pd.to_numeric(pick("Forecast","forecast"), errors="coerce"),
        "actual": pd.to_numeric(pick("Actual","actual"), errors="coerce"),
        "unit": pick("Unit","unit").astype("string"),
        "type": pick("Category","category","Type","type").astype("string"),
    })
    out = out.dropna(subset=["ts_utc"]).sort_values("ts_utc").reset_index(drop=True)
    return out

def upsert_events(con, df: pd.DataFrame) -> int:
    # on réutilise la même logique que eodhd
    if df is None or df.empty:
        return 0
    con.execute("""
    CREATE TABLE IF NOT EXISTS events AS
    SELECT CAST(NULL AS TIMESTAMP WITH TIME ZONE) AS ts_utc,
           CAST(NULL AS VARCHAR) AS country,
           CAST(NULL AS VARCHAR) AS event_title,
           CAST(NULL AS VARCHAR) AS event_key,
           CAST(NULL AS BIGINT) AS importance_n,
           CAST(NULL AS DOUBLE) AS previous,
           CAST(NULL AS DOUBLE) AS estimate,
           CAST(NULL AS DOUBLE) AS forecast,
           CAST(NULL AS DOUBLE) AS actual,
           CAST(NULL AS VARCHAR) AS unit,
           CAST(NULL AS VARCHAR) AS type
    WHERE FALSE
    """)
    inserted = 0
    for _, row in df.iterrows():
        con.execute("""
          INSERT INTO events
          SELECT ?,?,?,?,?,?,?,?,?,?,?
          WHERE NOT EXISTS (
            SELECT 1 FROM events
            WHERE ts_utc = ? AND COALESCE(country,'') = COALESCE(?, '')
              AND COALESCE(event_title,'') = COALESCE(?, '')
          )
        """, [
            row.get("ts_utc"), row.get("country"), row.get("event_title"), row.get("event_key"),
            row.get("importance_n"), row.get("previous"), row.get("estimate"), row.get("forecast"),
            row.get("actual"), row.get("unit"), row.get("type"),
            row.get("ts_utc"), row.get("country"), row.get("event_title")
        ])
        inserted += con.execute("SELECT changes()").fetchone()[0]
    return int(inserted)
