#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myfxbook_auto_update_rev3.py
----------------------------
Version intégrée avec get_or_refresh_session() depuis myfxbook_session_utils.
"""

import argparse
from datetime import datetime
from typing import Optional, List, Tuple
import pandas as pd
import requests
import duckdb
from bs4 import BeautifulSoup
from pathlib import Path

from myfxbook_session_utils import get_or_refresh_session

# -----------------------------
# Defaults
# -----------------------------
DEFAULT_DB = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
DEFAULT_DATA_DIR = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data"
DEFAULT_TZ = "Europe/Zurich"


# -----------------------------
# Utils
# -----------------------------
def log(msg: str, log_file: Optional[str] = None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def last_business_days(n: int, tz: str) -> List[pd.Timestamp]:
    today = pd.Timestamp.utcnow().tz_convert(tz).normalize()
    days = []
    d = today
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= pd.Timedelta(days=1)
    return sorted(days)


def clean_space(s):
    if not s:
        return None
    import re
    return re.sub(r"\s+", " ", str(s)).strip()


def to_int_importance(val):
    if val is None:
        return None
    s = str(val).lower().strip()
    if s in ["1", "low"]: return 1
    if s in ["2", "medium", "med"]: return 2
    if s in ["3", "high", "hi"]: return 3
    return None


def ensure_cols(df):
    cols = ["ts_utc", "ts_local", "country", "event_title", "impact", "actual", "forecast", "previous", "unit", "source"]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]


# -----------------------------
# Fetchers
# -----------------------------
def fetch_myfxbook_day(session_id: str, day: pd.Timestamp, tz: str) -> pd.DataFrame:
    url = "https://www.myfxbook.com/api/get-economic-calendar.json"
    try:
        r = requests.get(url, params={"session": session_id}, timeout=25)
        js = r.json()
    except Exception:
        return pd.DataFrame()
    if not js or js.get("error"):
        return pd.DataFrame()

    rows = []
    for ev in js.get("calendar", []):
        try:
            ts_val = ev.get("timestamp") or ev.get("date")
            if not ts_val:
                continue
            if len(str(int(ts_val))) > 10:
                ts_utc = pd.to_datetime(int(ts_val), unit="ms", utc=True)
            else:
                ts_utc = pd.to_datetime(int(ts_val), unit="s", utc=True)
        except Exception:
            continue

        ts_local = ts_utc.tz_convert(tz)
        if ts_local.date() != day.date():
            continue

        rows.append({
            "ts_utc": ts_utc,
            "ts_local": ts_local,
            "country": clean_space(ev.get("country") or ev.get("currency")),
            "event_title": clean_space(ev.get("title") or ev.get("event")),
            "impact": to_int_importance(ev.get("impact")),
            "actual": clean_space(ev.get("actual")),
            "forecast": clean_space(ev.get("forecast")),
            "previous": clean_space(ev.get("previous")),
            "unit": clean_space(ev.get("unit")),
            "source": "myfxbook_api"
        })
    return ensure_cols(pd.DataFrame(rows)) if rows else pd.DataFrame()


def fetch_forexfactory_day(day: pd.Timestamp, tz: str) -> pd.DataFrame:
    url = f"https://www.forexfactory.com/calendar?day={day.strftime('%b%d.%Y')}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return pd.DataFrame()

    rows = []
    for tr in soup.find_all("tr"):
        tcell = tr.find(attrs={"class": "calendar__time"})
        if not tcell: continue
        t = clean_space(tcell.text)
        if not t or t == "All Day": continue

        country = clean_space(tr.find(attrs={"class": "calendar__currency"}).text if tr.find(attrs={"class": "calendar__currency"}) else None)
        title = clean_space(tr.find(attrs={"class": "calendar__event"}).text if tr.find(attrs={"class": "calendar__event"}) else None)
        impact = to_int_importance(clean_space(tr.find(attrs={"class": "calendar__impact"}).text if tr.find(attrs={"class": "calendar__impact"}) else None))
        actual = clean_space(tr.find(attrs={"class": "calendar__actual"}).text if tr.find(attrs={"class": "calendar__actual"}) else None)
        forecast = clean_space(tr.find(attrs={"class": "calendar__forecast"}).text if tr.find(attrs={"class": "calendar__forecast"}) else None)
        previous = clean_space(tr.find(attrs={"class": "calendar__previous"}).text if tr.find(attrs={"class": "calendar__previous"}) else None)

        import re
        m = re.match(r"(\d{1,2}):(\d{2})", t)
        if not m: continue
        hh, mm = int(m.group(1)), int(m.group(2))
        ts_local = day.tz_localize(tz).replace(hour=hh, minute=mm, second=0)
        ts_utc = ts_local.tz_convert("UTC")
        rows.append({
            "ts_utc": ts_utc,
            "ts_local": ts_local,
            "country": country,
            "event_title": title,
            "impact": impact,
            "actual": actual,
            "forecast": forecast,
            "previous": previous,
            "unit": None,
            "source": "forexfactory_html"
        })
    return ensure_cols(pd.DataFrame(rows)) if rows else pd.DataFrame()


# -----------------------------
# DB logic
# -----------------------------
def delete_day(conn, day, tz):
    conn.execute(f"""
    DELETE FROM events
    WHERE DATE_TRUNC('day', (ts_utc AT TIME ZONE '{tz}'))
          = DATE_TRUNC('day', TIMESTAMP '{day.strftime('%Y-%m-%d')}' AT TIME ZONE '{tz}');
    """)


def upsert_days(db_path: str, days: List[pd.Timestamp], tz: str, frames: List[pd.DataFrame]):
    conn = duckdb.connect(db_path)
    conn.execute("PRAGMA threads=4;")
    for d, df in zip(days, frames):
        delete_day(conn, d, tz)
        if df is not None and not df.empty:
            conn.register("df_day", df)
            conn.execute("""
            INSERT INTO events
            SELECT ts_utc, country, event_title,
                   NULL::VARCHAR AS event_key,
                   impact AS importance_n,
                   TRY_CAST(actual AS DOUBLE) AS actual,
                   TRY_CAST(previous AS DOUBLE) AS previous,
                   NULL::DOUBLE AS estimate,
                   TRY_CAST(forecast AS DOUBLE) AS forecast,
                   unit, NULL, NULL, NULL, NULL, NULL, NULL, NULL
            FROM df_day;
            """)
    conn.close()


# -----------------------------
# Main update
# -----------------------------
def auto_update(db_path, data_dir, session_id, email, password, tz, days_back, log_file):
    sid, sid_status = get_or_refresh_session(data_dir=data_dir, email=email, password=password, current_session=session_id)
    if sid_status == "login_failed":
        log("❌ Login Myfxbook échoué — fallback ForexFactory uniquement.", log_file)
    elif sid_status == "not_available":
        log("⚠️  Aucune session disponible — fallback ForexFactory uniquement.", log_file)
    else:
        log(f"✅ Session Myfxbook OK ({sid_status}).", log_file)

    days = last_business_days(days_back, tz)
    frames, total_rows = [], 0

    for d in days:
        log(f"📅 Collecte événements {d.date()} ...", log_file)
        df = fetch_myfxbook_day(sid, d, tz) if sid else pd.DataFrame()
        if df.empty:
            log("  Myfxbook vide → fallback ForexFactory.", log_file)
            df = fetch_forexfactory_day(d, tz)
        frames.append(df)
        total_rows += len(df)

    report_csv = str(Path(data_dir) / f"auto_update_report_{datetime.utcnow().strftime('%Y%m%d')}.csv")
    if any([not f.empty for f in frames]):
        pd.concat(frames).to_csv(report_csv, index=False)
        log(f"💾 Rapport généré : {report_csv}", log_file)
    else:
        log("⚠️  Aucun event collecté.", log_file)

    upsert_days(db_path, days, tz, frames)
    log(f"✅ Écriture DuckDB terminée ({len(days)} jours, {total_rows} lignes).", log_file)
    return report_csv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=DEFAULT_DB)
    ap.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    ap.add_argument("--session", type=str)
    ap.add_argument("--email", type=str)
    ap.add_argument("--password", type=str)
    ap.add_argument("--tz", default=DEFAULT_TZ)
    ap.add_argument("--days-back", type=int, default=5)
    args = ap.parse_args()

    log_file = str(Path(args.data_dir) / "auto_update_log.txt")
    log("=== AUTO UPDATE (Myfxbook→DuckDB) ===", log_file)

    auto_update(args.db_path, args.data_dir, args.session, args.email, args.password, args.tz, args.days_back, log_file)


if __name__ == "__main__":
    main()
