#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myfxbook_auto_update_rev6_auto_login.py
---------------------------------------
Import HISTORIQUE COMPLET (jours ouvrables uniquement) des événements macro
dans DuckDB en s'appuyant sur l'API Myfxbook.

✅ Auto-login & auto-refresh de session :
   - Accepte --session (raw ou encodée) ou --email/--password
   - Si la session est invalide, tente une reconnexion automatique
   - Sauvegarde/relit les identifiants & la session dans data/myfxbook_session.json

✅ Mode strict côté source :
   - AUCUN fallback vers d'autres sources : Myfxbook uniquement
   - Si connexion impossible après tentative d'auto-login → arrêt proprement

🧰 Prérequis : requests, pandas, duckdb, tqdm
"""

import argparse
import sys
import re
import json
import urllib.parse
from datetime import datetime
from typing import Optional, List, Tuple

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
}

SESSION_STORE = "myfxbook_session.json"  # stocké sous data_dir


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
    Vérifie la session via 'verify.json', avec tolérance :
    - essaie session RAW, puis URL-encodée
    - si verify échoue, tente un GET calendrier ; si OK => session acceptée
    """
    url_verify = "https://www.myfxbook.com/api/verify.json"
    url_cal = "https://www.myfxbook.com/api/get-economic-calendar.json"

    # Préparer variantes de session
    raw = session_id.strip()
    enc = urllib.parse.quote_plus(raw)

    # 1) verify (raw)
    try:
        r = requests.get(url_verify, params={"session": raw}, headers=HEADERS, timeout=20, allow_redirects=True)
        js = r.json()
        if js and js.get("error") is False:
            return True
    except Exception:
        pass

    # 2) verify (encoded)
    try:
        r = requests.get(url_verify, params={"session": enc}, headers=HEADERS, timeout=20, allow_redirects=True)
        js = r.json()
        if js and js.get("error") is False:
            return True
    except Exception:
        pass

    # 3) Calendrier direct comme arbitre final
    try:
        r = requests.get(url_cal, params={"session": raw}, headers=HEADERS, timeout=25, allow_redirects=True)
        js = r.json()
        if js and js.get("error") is False and isinstance(js.get("calendar"), list):
            return True
    except Exception:
        pass
    try:
        r = requests.get(url_cal, params={"session": enc}, headers=HEADERS, timeout=25, allow_redirects=True)
        js = r.json()
        if js and js.get("error") is False and isinstance(js.get("calendar"), list):
            return True
    except Exception:
        pass

    return False


def fetch_myfxbook_calendar(session_id: str) -> dict:
    """
    Récupère le calendrier brut (tous événements servis par l'API).
    """
    url = "https://www.myfxbook.com/api/get-economic-calendar.json"
    r = requests.get(url, params={"session": session_id}, headers=HEADERS, timeout=30)
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
# Session storage (JSON)
# -----------------------------
def session_store_path(data_dir: str) -> Path:
    p = Path(data_dir) / SESSION_STORE
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_session_from_store(data_dir: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    p = session_store_path(data_dir)
    if not p.exists():
        return None, None, None
    try:
        js = json.loads(p.read_text(encoding="utf-8"))
        return js.get("session"), js.get("email"), js.get("password")
    except Exception:
        return None, None, None


def save_session_to_store(data_dir: str, session_id: str, email: Optional[str], password: Optional[str]):
    p = session_store_path(data_dir)
    payload = {"session": session_id, "email": email, "password": password}
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def login_myfxbook(email: str, password: str) -> Optional[str]:
    url = "https://www.myfxbook.com/api/login.json"
    try:
        r = requests.get(url, params={"email": email, "password": password}, headers=HEADERS, timeout=20)
        js = r.json()
        if js and js.get("error") is False and js.get("session"):
            # Décoder la session qui est souvent URL-encodée
            return urllib.parse.unquote_plus(js["session"])
    except Exception:
        pass
    return None


def get_or_refresh_session(data_dir: str,
                           session_arg: Optional[str],
                           email: Optional[str],
                           password: Optional[str],
                           log_file: Optional[str]) -> Optional[str]:
    """
    - Si session_arg fourni → normalise, vérifie → OK ? on garde, sinon tentative de login
    - Sinon : charge depuis le store → OK ? on garde, sinon tentative de login
    - Si login OK → on sauvegarde et on retourne la nouvelle session
    - Si tout échoue → None
    """
    # 1) Si la session est fournie en arg
    if session_arg:
        candidate = session_arg.strip()
        if verify_session(candidate):
            save_session_to_store(data_dir, candidate, email, password)
            log("✅ Session fournie valide.", log_file)
            return candidate
        log("⚠️ Session fournie invalide, tentative d'auto-login…", log_file)

    # 2) Sinon : tenter depuis le store
    stored_sess, stored_email, stored_pwd = load_session_from_store(data_dir)
    if stored_sess:
        candidate = stored_sess.strip()
        if verify_session(candidate):
            log("✅ Session stockée valide.", log_file)
            return candidate
        else:
            log("⚠️ Session stockée expirée.", log_file)
            if not email: email = stored_email
            if not password: password = stored_pwd

    # 3) Tentative de login si on a email/pwd
    if email and password:
        new_session = login_myfxbook(email, password)
        if new_session and verify_session(new_session):
            save_session_to_store(data_dir, new_session, email, password)
            log("✅ Auto-login Myfxbook réussi.", log_file)
            return new_session
        else:
            log("❌ Auto-login Myfxbook échoué.", log_file)

    # 4) Échec total
    return None


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
# Main (historical strict, auto-login)
# -----------------------------
def run_historical(db_path: str,
                   data_dir: str,
                   session_arg: Optional[str],
                   email: Optional[str],
                   password: Optional[str],
                   tz: str,
                   start_year: int,
                   end_year: int,
                   log_file: Optional[str] = None):

    # 1) Obtenir une session valide (session arg → store → auto-login)
    session_id = get_or_refresh_session(
        data_dir=data_dir,
        session_arg=session_arg,
        email=email,
        password=password,
        log_file=log_file
    )
    if not session_id:
        log("❌ Impossible d'obtenir une session Myfxbook valide.", log_file)
        log("⛔ Import interrompu (source strict Myfxbook).", log_file)
        sys.exit(3)

    log("✅ Session Myfxbook OK. Import démarré.", log_file)

    # 2) Génère liste jours ouvrables
    days = business_days_between(start_year, end_year, tz)
    log(f"📅 Fenêtre : {start_year}-01-01 → {end_year}-12-31 | Jours ouvrables : {len(days)}", log_file)

    # 3) Récupère calendrier brut (une fois), puis filtre par jour
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
    ap = argparse.ArgumentParser(description="Import HISTORIQUE COMPLET (Myfxbook→DuckDB) avec auto-login et arrêt strict si impossible.")
    ap.add_argument("--db-path", type=str, default=DEFAULT_DB)
    ap.add_argument("--data-dir", type=str, default=DEFAULT_DATA_DIR)
    ap.add_argument("--session", type=str, help="Myfxbook session id (raw ou encodée)")
    ap.add_argument("--email", type=str, help="Myfxbook email (pour auto-login si session invalide/absente)")
    ap.add_argument("--password", type=str, help="Myfxbook password (pour auto-login si session invalide/absente)")
    ap.add_argument("--tz", type=str, default=DEFAULT_TZ)
    ap.add_argument("--start-year", type=int, required=True)
    ap.add_argument("--end-year", type=int, required=True)
    args = ap.parse_args()

    log_file = str(Path(args.data_dir) / "myfxbook_history_import_rev6.log")

    log("=== IMPORT HISTORIQUE COMPLET (Myfxbook→DuckDB) — rev6 auto-login ===", log_file)
    log(f"DB         : {args.db_path}", log_file)
    log(f"DATA DIR   : {args.data_dir}", log_file)
    log(f"TZ         : {args.tz}", log_file)
    log(f"YEARS      : {args.start_year} → {args.end_year}", log_file)

    report_csv, days, total_rows = run_historical(
        db_path=args.db_path,
        data_dir=args.data_dir,
        session_arg=args.session,
        email=args.email,
        password=args.password,
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
