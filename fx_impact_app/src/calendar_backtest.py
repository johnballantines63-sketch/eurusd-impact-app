
from __future__ import annotations
from typing import List, Optional
import pandas as pd, duckdb
from zoneinfo import ZoneInfo
from .config import get_db_path

def extract_day_events(con, day_local: pd.Timestamp, tz: str,
                       include_regex: Optional[str], countries: Optional[List[str]] = None) -> pd.DataFrame:
    TZ = ZoneInfo(tz)
    start_local = pd.Timestamp(day_local.date(), tz=TZ)
    end_local   = start_local + pd.Timedelta(days=1)
    start_utc, end_utc = start_local.tz_convert("UTC"), end_local.tz_convert("UTC")
    cols = {r[1] for r in con.execute("PRAGMA table_info('events')").fetchall()}
    sel = ["ts_utc"]
    for c in ["country","event_title","event_key","previous","estimate","forecast","unit","actual","value","result"]:
        if c in cols: sel.append(c)
    q = f"SELECT {', '.join(sel)} FROM events WHERE ts_utc BETWEEN ? AND ?"
    params = [start_utc.to_pydatetime(), end_utc.to_pydatetime()]
    if countries and "country" in cols:
        q += " AND country IN (" + ",".join(["?"]*len(countries)) + ")"; params += countries
    if include_regex:
        parts=[]
        if "event_key" in cols:   parts.append("regexp_matches(lower(event_key), ?)")
        if "event_title" in cols: parts.append("regexp_matches(lower(event_title), ?)")
        if parts: q += " AND (" + " OR ".join(parts) + ")"; params += [include_regex]*len(parts)
    q += " ORDER BY ts_utc"
    df = con.execute(q, params).df()
    if df.empty: return df
    if "estimate" in df.columns and df["estimate"].notna().any(): df["consensus"] = df["estimate"]
    elif "forecast" in df.columns and df["forecast"].notna().any(): df["consensus"] = df["forecast"]
    else: df["consensus"] = pd.NA
    if "actual" not in df.columns:
        for c in ("value","result"):
            if c in df.columns: df["actual"] = df[c]; break
        else: df["actual"] = pd.NA
    return df
