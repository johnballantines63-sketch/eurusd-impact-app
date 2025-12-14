#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myfxbook_auto_update_rev4.py
----------------------------
Import HISTORIQUE COMPLET (jours ouvrables uniquement) des événements macro
dans DuckDB en s'appuyant d'abord sur l'API Myfxbook (session auto-gérée),
avec fallback ForexFactory si nécessaire.

- Parcourt les X DERNIERS MOIS (--months-back, défaut 12)
- Jours ouvrables uniquement (lun–ven, selon le fuseau local fourni)
- Barre de progression (tqdm)
- Sauvegarde CSV résumé & log texte
- Écrit proprement dans DuckDB (table `events`) en supprimant/injectant JOUR PAR JOUR

Dépendances : requests, pandas, duckdb, beautifulsoup4, tqdm
"""

import argparse
import sys
import re
from datetime import datetime
from typing import Optional, List, Tuple

import requests
import pandas as pd
import duckdb
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path

# Module utilitaire de session (fourni séparément)
from myfxbook_session_utils import get_or_refresh_session

# -----------------------------
# Defaults (paths / tz)
# -----------------------------
DEFAULT_DB = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
DEFAULT_DATA_DIR = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data"
DEFAULT_TZ = "Europe/Zurich"


# -----------------------------
# Logging util
# -----------------------------
def log(msg: str, log_file: Optional[str] = None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


# -----------------------------
# Dates util
# -----------------------------
def business_days_in_last_months(months_back: int, tz: str) -> List[pd.Timestamp]:
    """
    Renvoie la liste triée de tous les jours ouvrables (lun–ven) des `months_back` derniers mois
    jusqu'à aujourd'hui (inclus), dans le fuseau horaire `tz`.
    """
    now_local = pd.Timestamp.utcnow().tz_convert(tz)
    end_date = now_local.normalize()
    start_date = (end_date - pd.DateOffset(months=months_back)).normalize()

    days = []
    d = start_date
    while d <= end_date:
        if d.weekday() < 5:  # Mon-Fri
            days.append(d)
        d += pd.Timedelta(days=1)
    return days


# -----------------------------
# Helpers
# -----------------------------
def clean_space(s):
    if s is None:
        return None
    return re.sub(r"\s+", " ", str(s)).strip()


def to_int_importance(val):
    if val is None:
        return None
    s = str(val).lower().strip()
    if s in ["1", "low", "lo"]: return 1
    if s in ["2", "medium", "med"]: return 2
    if s in ["3", "high", "hi", "high-importance", "high impact"]: return 3
    try:
        n = int(float(s))
        return min(max(n, 1), 3)
    except Exception:
        return None


def ensure_cols(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["ts_utc", "ts_local", "country", "event_title", "impact",
            "actual", "forecast", "previous", "unit", "source"]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]


def normalize_df(df: pd.DataFrame, tz: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    out["ts_utc"] = pd.to_datetime(out["ts_utc"], utc=True)
    out["ts_local"] = pd.to_datetime(out["ts_local"], utc=True).dt.tz_convert(tz)
    for c in ["country","event_title","unit","source","actual","forecast","previous"]:
        out[c] = out[c].astype("string").fillna(pd.NA)
    out["impact"] = out["impact"].astype("Int64")
    return ensure_cols(out)


# -----------------------------
# Fetchers
# -----------------------------
def fetch_myfxbook_day(session_id: str, day: pd.Timestamp, tz: str) -> pd.DataFrame:
    url = "https://www.myfxbook.com/api/get-economic-calendar.json"
    try:
        r = requests.get(url, params={"session": session_id}, timeout=30)
        js = r.json()
    except Exception:
        return pd.DataFrame()
    if not js or js.get("error"):
        return pd.DataFrame()

    rows = []
    for ev in js.get("calendar", []):
        try:
            ts_val = ev.get("timestamp") or ev.get("date")
            if ts_val is None:
                continue
            if len(str(int(ts_val))) > 10:
                ts_utc = pd.to_datetime(int(ts_val), unit="ms", utc=True)
            else:
                ts_utc = pd.to_datetime(int(ts_val), unit="s", utc=True)
        except Exception:
            # support ISO-like
            try:
                ts_utc = pd.to_datetime(ev.get("date"), utc=True)
            except Exception:
                continue

        ts_local = ts_utc.tz_convert(tz)
        if ts_local.date() != day.date():
            continue

        rows.append({
            "ts_utc": ts_utc,
            "ts_local": ts_local,
            "country": clean_space(ev.get("country") or ev.get("currency")),
            "event_title": clean_space(ev.get("title") or ev.get("event") or ev.get("name")),
            "impact": to_int_importance(ev.get("impact") or ev.get("importance")),
            "actual": clean_space(ev.get("actual")),
            "forecast": clean_space(ev.get("forecast")),
            "previous": clean_space(ev.get("previous")),
            "unit": clean_space(ev.get("unit")),
            "source": "myfxbook_api"
        })
    if not rows:
        return pd.DataFrame()
    return ensure_cols(pd.DataFrame(rows).sort_values("ts_local"))


def fetch_forexfactory_day(day: pd.Timestamp, tz: str) -> pd.DataFrame:
    try:
        url = f"https://www.forexfactory.com/calendar?day={day.strftime('%b%d.%Y')}"
        r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        time_cell = tr.find(attrs={"class": re.compile("time|calendar__time")})
        if not time_cell:
            continue
        t_time = clean_space(time_cell.get_text())
        if not t_time or t_time.lower() == "all day":
            continue
        country_cell = tr.find(attrs={"class": re.compile("currency|flag")})
        country = clean_space(country_cell.get_text()) if country_cell else None
        title_cell = tr.find(attrs={"class": re.compile("event|calendar__event")})
        title = clean_space(title_cell.get_text()) if title_cell else None
        impact_cell = tr.find(attrs={"class": re.compile("impact|calendar__impact")})
        impact_txt = clean_space(impact_cell.get_text()) if impact_cell else None

        actual_cell = tr.find(attrs={"class": re.compile("actual")})
        forecast_cell = tr.find(attrs={"class": re.compile("forecast")})
        previous_cell = tr.find(attrs={"class": re.compile("previous")})
        actual = clean_space(actual_cell.get_text()) if actual_cell else None
        forecast = clean_space(forecast_cell.get_text()) if forecast_cell else None
        previous = clean_space(previous_cell.get_text()) if previous_cell else None

        m = re.match(r"(\d{1,2}):(\d{2})", t_time or "")
        if not m:
            continue
        hh, mm = int(m.group(1)), int(m.group(2))
        ts_local = day.tz_localize(tz).replace(hour=hh, minute=mm, second=0)
        ts_utc = ts_local.tz_convert("UTC")

        rows.append({
            "ts_utc": ts_utc,
            "ts_local": ts_local,
            "country": country,
            "event_title": title,
            "impact": to_int_importance(impact_txt),
            "actual": actual,
            "forecast": forecast,
            "previous": previous,
            "unit": None,
            "source": "forexfactory_html"
        })

    if not rows:
        return pd.DataFrame()
    return ensure_cols(pd.DataFrame(rows).sort_values("ts_local"))


# -----------------------------
# DB write
# -----------------------------
def delete_day(conn, day: pd.Timestamp, tz: str):
    q = f"""
    DELETE FROM events
    WHERE DATE_TRUNC('day', (ts_utc AT TIME ZONE '{tz}'))
          = DATE_TRUNC('day', TIMESTAMP '{day.strftime('%Y-%m-%d')}' AT TIME ZONE '{tz}');
    """
    conn.execute(q)


def upsert_days(db_path: str, days: List[pd.Timestamp], tz: str, frames: List[pd.DataFrame]):
    conn = duckdb.connect(db_path)
    conn.execute("PRAGMA threads=4;")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS events (
      ts_utc TIMESTAMP WITH TIME ZONE,
      country VARCHAR,
      event_title VARCHAR,
      event_key VARCHAR,
      importance_n BIGINT,
      actual DOUBLE,
      previous DOUBLE,
      estimate DOUBLE,
      forecast DOUBLE,
      unit VARCHAR,
      type VARCHAR,
      label VARCHAR,
      comparison VARCHAR,
      period VARCHAR,
      change DOUBLE,
      change_percentage DOUBLE,
      event_type VARCHAR
    );
    """)
    for d, df in zip(days, frames):
        delete_day(conn, d, tz)
        if df is None or df.empty:
            continue
        conn.register("df_day", df)
        conn.execute("""
        INSERT INTO events
        SELECT
          ts_utc,
          country,
          event_title,
          NULL::VARCHAR AS event_key,
          impact AS importance_n,
          TRY_CAST(actual AS DOUBLE) AS actual,
          TRY_CAST(previous AS DOUBLE) AS previous,
          NULL::DOUBLE AS estimate,
          TRY_CAST(forecast AS DOUBLE) AS forecast,
          unit,
          NULL::VARCHAR AS type,
          NULL::VARCHAR AS label,
          NULL::VARCHAR AS comparison,
          NULL::VARCHAR AS period,
          NULL::DOUBLE AS change,
          NULL::DOUBLE AS change_percentage,
          NULL::VARCHAR AS event_type
        FROM df_day;
        """)
    conn.close()


# -----------------------------
# Main (historical only)
# -----------------------------
def run_historical(db_path: str,
                   data_dir: str,
                   session_id: Optional[str],
                   email: Optional[str],
                   password: Optional[str],
                   tz: str,
                   months_back: int,
                   log_file: Optional[str] = None):

    # Gestion de session via utilitaire centralisé
    sid, status = get_or_refresh_session(
        data_dir=data_dir,
        email=email,
        password=password,
        current_session=session_id
    )
    if status == "login_failed":
        log("❌ Login Myfxbook échoué — fallback ForexFactory uniquement pour tout l'historique.", log_file)
    elif status == "not_available":
        log("⚠️ Aucune session disponible — fallback ForexFactory uniquement pour tout l'historique.", log_file)
    else:
        log(f"✅ Session Myfxbook OK ({status}).", log_file)

    # Génère la liste des jours ouvrables dans la fenêtre demandée
    days = business_days_in_last_months(months_back, tz)
    frames = []
    total_rows = 0

    # Progress bar
    for d in tqdm(days, desc="Import historique (jours ouvrables)"):
        df = pd.DataFrame()
        if sid:
            df = fetch_myfxbook_day(sid, d, tz)
        if df is None or df.empty:
            df = fetch_forexfactory_day(d, tz)
        df = normalize_df(df, tz)
        frames.append(df)
        total_rows += (0 if df is None else len(df))

    # Rapport CSV & log
    today_tag = pd.Timestamp.utcnow().strftime("%Y%m%d")
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    report_csv = str(Path(data_dir) / f"myfxbook_history_import_{today_tag}.csv")
    if any([not f.empty for f in frames]):
        pd.concat(frames, ignore_index=True).sort_values(["ts_local","country","event_title"]).to_csv(report_csv, index=False)
        log(f"💾 Rapport CSV → {report_csv}", log_file)
    else:
        log("⚠️ Aucun événement collecté, pas de CSV généré.", log_file)

    # Écriture dans DuckDB (delete+insert par jour)
    upsert_days(db_path, days, tz, frames)
    log(f"✅ Import historique terminé. Jours traités : {len(days)}. Lignes totales : {total_rows}.", log_file)

    return report_csv, days, total_rows


def main():
    ap = argparse.ArgumentParser(description="Import HISTORIQUE COMPLET (jours ouvrables) Myfxbook→DuckDB, avec fallback ForexFactory.")
    ap.add_argument("--db-path", type=str, default=DEFAULT_DB)
    ap.add_argument("--data-dir", type=str, default=DEFAULT_DATA_DIR)
    ap.add_argument("--session", type=str, help="Myfxbook session id (optionnel)")
    ap.add_argument("--email", type=str, help="Myfxbook email (optionnel, pour renouveler session)")
    ap.add_argument("--password", type=str, help="Myfxbook password (optionnel, pour renouveler session)")
    ap.add_argument("--tz", type=str, default=DEFAULT_TZ)
    ap.add_argument("--months-back", type=int, default=12, help="Nombre de mois d'historique à importer (défaut 12)")
    args = ap.parse_args()

    log_file = str(Path(args.data_dir) / "myfxbook_history_import.log")

    log("=== IMPORT HISTORIQUE COMPLET (Myfxbook→DuckDB) ===", log_file)
    log(f"DB          : {args.db_path}", log_file)
    log(f"DATA DIR    : {args.data_dir}", log_file)
    log(f"TZ          : {args.tz}", log_file)
    log(f"MONTHS BACK : {args.months_back}", log_file)

    report_csv, days, total_rows = run_historical(
        db_path=args.db_path,
        data_dir=args.data_dir,
        session_id=args.session,
        email=args.email,
        password=args.password,
        tz=args.tz,
        months_back=args.months_back,
        log_file=log_file
    )

    log("✅ Fin d'exécution.", log_file)
    log(f"Jours couverts : {days[0].date()} → {days[-1].date()}" if days else "Aucun jour", log_file)
    log(f"Total lignes collectées : {total_rows}", log_file)
    if report_csv:
        log(f"Rapport : {report_csv}", log_file)


if __name__ == "__main__":
    main()
