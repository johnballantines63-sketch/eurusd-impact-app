#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myfxbook_auto_update_rev5.py
----------------------------
Import HISTORIQUE COMPLET (jours ouvrables uniquement) des événements macro
dans DuckDB en s'appuyant EXCLUSIVEMENT sur l'API Myfxbook.
⚠️ Mode strict : si la connexion Myfxbook échoue (session invalide), le script s'arrête immédiatement.
AUCUN fallback n'est déclenché.

- Période paramétrable par années : --start-year, --end-year
- Jours ouvrables uniquement (lun–ven, selon le fuseau local fourni)
- Barre de progression (tqdm)
- Sauvegarde CSV résumé & log texte
- Écrit proprement dans DuckDB (table `events`) en supprimant/injectant JOUR PAR JOUR

Dépendances : requests, pandas, duckdb, tqdm
"""

import argparse
import sys
import re
from datetime import datetime
from typing import Optional, List

import requests
import pandas as pd
import duckdb
from tqdm import tqdm
from pathlib import Path

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
def business_days_between(start_year: int, end_year: int, tz: str) -> List[pd.Timestamp]:
    """
    Renvoie la liste triée de tous les jours ouvrables (lun–ven)
    entre le 1er janvier `start_year` et le 31 décembre `end_year` (inclus),
    dans le fuseau horaire `tz`.
    """
    start_date = pd.Timestamp(year=start_year, month=1, day=1, tz=tz)
    end_date = pd.Timestamp(year=end_year, month=12, day=31, tz=tz)
    days = []
    d = start_date.normalize()
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
# Myfxbook API
# -----------------------------
def verify_session(session_id: str) -> bool:
    """
    Vérifie la session via l'endpoint 'verify.json'.
    Retourne True si la session est valide, False sinon.
    """
    url = "https://www.myfxbook.com/api/verify.json"
    try:
        r = requests.get(url, params={"session": session_id}, timeout=20)
        js = r.json()
        return bool(js and (js.get("error") is False))
    except Exception:
        return False


def fetch_myfxbook_calendar(session_id: str) -> dict:
    """
    Récupère le calendrier brut (tous événements servis par l'API).
    """
    url = "https://www.myfxbook.com/api/get-economic-calendar.json"
    r = requests.get(url, params={"session": session_id}, timeout=30)
    r.raise_for_status()
    js = r.json()
    if not js or js.get("error"):
        raise RuntimeError(f"Myfxbook error: {js.get('message') if isinstance(js, dict) else 'unknown'}")
    return js


def filter_calendar_for_day(js: dict, day: pd.Timestamp, tz: str) -> pd.DataFrame:
    rows = []
    for ev in js.get("calendar", []):
        # timestamp (ms ou s) ou date ISO
        ts_utc = None
        ts_val = ev.get("timestamp") or ev.get("date")
        if ts_val is None:
            continue
        try:
            if isinstance(ts_val, (int, float)) or str(ts_val).isdigit():
                ts_int = int(ts_val)
                if len(str(ts_int)) > 10:
                    ts_utc = pd.to_datetime(ts_int, unit="ms", utc=True)
                else:
                    ts_utc = pd.to_datetime(ts_int, unit="s", utc=True)
            else:
                ts_utc = pd.to_datetime(ts_val, utc=True)
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
    conn.execute("""    CREATE TABLE IF NOT EXISTS events (
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
        conn.execute("""        INSERT INTO events
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
# Main (historical strict)
# -----------------------------
def run_historical_strict(db_path: str,
                          data_dir: str,
                          session_id: str,
                          tz: str,
                          start_year: int,
                          end_year: int,
                          log_file: Optional[str] = None):
    # 1) Vérification stricte de la session
    if not session_id:
        log("❌ Aucun --session fourni. Ce mode exige une session Myfxbook valide.", log_file)
        sys.exit(2)
    if not verify_session(session_id):
        log("❌ Erreur Myfxbook : session invalide ou expirée.", log_file)
        log("⛔ Import interrompu (aucun fallback activé).", log_file)
        sys.exit(3)
    log("✅ Session Myfxbook validée. Import démarré.", log_file)

    # 2) Génère liste jours ouvrables
    days = business_days_between(start_year, end_year, tz)
    log(f"📅 Fenêtre : {start_year}-01-01 → {end_year}-12-31 | Jours ouvrables : {len(days)}", log_file)

    # 3) Récupère calendrier global une fois, puis filtre par jour
    try:
        cal_json = fetch_myfxbook_calendar(session_id)
    except Exception as e:
        log(f"❌ Échec fetch calendrier Myfxbook : {e}", log_file)
        log("⛔ Import interrompu.", log_file)
        sys.exit(4)

    frames = []
    total_rows = 0

    for d in tqdm(days, desc="Import historique (jours ouvrables)"):
        df_day = filter_calendar_for_day(cal_json, d, tz)
        df_day = normalize_df(df_day, tz)
        frames.append(df_day)
        total_rows += (0 if df_day is None else len(df_day))

    # 4) Rapport CSV & log
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    today_tag = pd.Timestamp.utcnow().strftime("%Y%m%d")
    report_csv = str(Path(data_dir) / f"myfxbook_history_import_{start_year}_{end_year}_{today_tag}.csv")
    if any([not f.empty for f in frames]):
        pd.concat(frames, ignore_index=True).sort_values(["ts_local","country","event_title"]).to_csv(report_csv, index=False)
        log(f"💾 Rapport CSV → {report_csv}", log_file)
    else:
        log("⚠️ Aucun événement collecté, pas de CSV généré.", log_file)

    # 5) Écriture DB
    upsert_days(db_path, days, tz, frames)
    log(f"✅ Import historique terminé. Jours traités : {len(days)}. Lignes totales : {total_rows}.", log_file)

    return report_csv, days, total_rows


def main():
    ap = argparse.ArgumentParser(description="Import HISTORIQUE COMPLET STRICT (Myfxbook→DuckDB). Stoppe si session invalide.")
    ap.add_argument("--db-path", type=str, default=DEFAULT_DB)
    ap.add_argument("--data-dir", type=str, default=DEFAULT_DATA_DIR)
    ap.add_argument("--session", type=str, required=True, help="Myfxbook session id (obligatoire en mode strict)")
    ap.add_argument("--tz", type=str, default=DEFAULT_TZ)
    ap.add_argument("--start-year", type=int, required=True)
    ap.add_argument("--end-year", type=int, required=True)
    args = ap.parse_args()

    log_file = str(Path(args.data_dir) / "myfxbook_history_import_strict.log")

    log("=== IMPORT HISTORIQUE COMPLET STRICT (Myfxbook→DuckDB) ===", log_file)
    log(f"DB         : {args.db_path}", log_file)
    log(f"DATA DIR   : {args.data_dir}", log_file)
    log(f"TZ         : {args.tz}", log_file)
    log(f"YEARS      : {args.start_year} → {args.end_year}", log_file)

    report_csv, days, total_rows = run_historical_strict(
        db_path=args.db_path,
        data_dir=args.data_dir,
        session_id=args.session,
        tz=args.tz,
        start_year=args.start_year,
        end_year=args.end_year,
        log_file=log_file
    )

    log("✅ Fin d'exécution.", log_file)
    if days:
        log(f"Jours couverts : {days[0].date()} → {days[-1].date()}", log_file)
    log(f"Total lignes collectées : {total_rows}", log_file)
    if report_csv:
        log(f"Rapport : {report_csv}", log_file)


if __name__ == "__main__":
    main()
