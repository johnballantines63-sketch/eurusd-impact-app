# fx_impact_app/src/eodhd_client.py
from __future__ import annotations
import os
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests
import duckdb

EOD_BASE = "https://eodhd.com/api/economic-events"


# ---------------------------------------------------------------------
# Key helper
# ---------------------------------------------------------------------
def get_eod_key() -> str:
    """
    Récupère la clé EODHD depuis l'env (EODHD_API_KEY).
    Raise explicite si absente.
    """
    key = os.environ.get("EODHD_API_KEY")
    if not key or str(key).strip().lower() in {"none", "true", "false"}:
        raise RuntimeError("Missing EODHD_API_KEY.")
    return key.strip()


# ---------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------
def _to_ymd(x: Any) -> str:
    """Force un format YYYY-MM-DD sans composante horaire (évite 422 côté API)."""
    ts = pd.to_datetime(x, utc=True)
    return ts.strftime("%Y-%m-%d")


def fetch_calendar_json(
    d1: Any,
    d2: Any,
    countries: Optional[Iterable[str]] = None,
    importance: Optional[Iterable[int]] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Appelle /economic-events avec dates simples (YYYY-MM-DD).
    - countries: liste ISO (US, EU, JP, ...) -> jointes par virgule
    - importance: 1/2/3 -> jointes par virgule
    Retour: liste de dicts (brut).
    """
    key = api_key or get_eod_key()
    params = {
        "from": _to_ymd(d1),
        "to": _to_ymd(d2),
        "api_token": key,
        "fmt": "json",
    }
    if countries:
        cc = [str(c).strip().upper() for c in countries if str(c).strip()]
        if cc:
            params["countries"] = ",".join(cc)
    if importance:
        imps = [int(i) for i in importance]
        if imps:
            params["importance"] = ",".join(map(str, imps))

    r = requests.get(EOD_BASE, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):
        # certaines erreurs sont au format dict avec message
        if data.get("code") or data.get("message"):
            raise RuntimeError(f"EODHD returned error: {data}")
        data = [data]
    if not isinstance(data, list):
        raise RuntimeError("Unexpected EODHD payload (not a list).")
    return data


# ---------------------------------------------------------------------
# Normalize
# ---------------------------------------------------------------------
def _col(df: pd.DataFrame, *names: str) -> pd.Series:
    """Renvoie la première colonne existante parmi *names*, sinon une Series NA."""
    for n in names:
        if n in df.columns:
            return df[n]
    return pd.Series(pd.NA, index=df.index)


def _to_utc_series(s: pd.Series) -> pd.Series:
    """Parsage datetime -> tz-aware UTC (Compat DuckDB TIMESTAMP WITH TIME ZONE)."""
    if s is None:
        return pd.Series([], dtype="datetime64[ns, UTC]")
    out = pd.to_datetime(s, errors="coerce", utc=True)
    return out


def _importance_to_num(s: pd.Series) -> pd.Series:
    """
    Mappe le champ de priorité (impact/importance) vers une échelle 1..3.
    Accepte déjà du numérique, ou des strings (low/medium/high).
    """
    if s is None:
        return pd.Series(pd.NA, dtype="Float64")
    if pd.api.types.is_integer_dtype(s) or pd.api.types.is_float_dtype(s):
        return pd.to_numeric(s, errors="coerce").astype("Float64")
    m = {
        "low": 1, "1": 1, "l": 1,
        "medium": 2, "2": 2, "m": 2,
        "high": 3, "3": 3, "h": 3,
    }
    return (
        s.astype("string")
         .str.strip()
         .str.lower()
         .map(m)
         .astype("Float64")
    )


def calendar_to_events_df(items: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Normalise le JSON EODHD en un DataFrame aligné sur notre table `events`.
    Colonnes produites (si dispo):
      - ts_utc (datetime64[ns, UTC])
      - country (str, upper)
      - event_title (str), event_key (str), label (str), type (str)
      - estimate/forecast/previous/actual (Float64)
      - unit (str), importance_n (Int64)
    """
    if not items:
        return pd.DataFrame()

    raw = pd.DataFrame(items)

    # champs texte “titre”
    event_title = _col(raw, "event", "indicator", "title", "event_title")
    label = _col(raw, "label", "shortname", "short_name", "name")
    typ = _col(raw, "category", "type", "group", "event_group")

    # clé (id)
    key_src = _col(raw, "event_id", "id", "code")
    event_key = key_src.copy()
    if event_key.isna().all():
        base = (event_title.fillna("") + "||" + typ.fillna(""))
        event_key = (
            base.astype(str)
                .str.strip()
                .str.lower()
                .str.replace(r"\s+", " ", regex=True)
        )

    # pays
    country = _col(raw, "country", "country_code", "ccy", "currency")
    country = country.astype("string").str.upper()

    # timestamps
    ts = _col(raw, "date", "datetime", "timestamp", "releaseTime", "time")
    ts_utc = _to_utc_series(ts)

    # numeric values
    estimate = pd.to_numeric(_col(raw, "estimate", "estimated", "consensus"), errors="coerce")
    forecast = pd.to_numeric(_col(raw, "forecast", "forecasted"), errors="coerce")
    previous = pd.to_numeric(_col(raw, "previous", "prev"), errors="coerce")
    actual = pd.to_numeric(_col(raw, "actual", "value"), errors="coerce")

    unit = _col(raw, "unit", "unit_short", "units").astype("string")

    # importance
    imp_src = _col(raw, "importance", "impact", "priority", "importance_n")
    importance_n = _importance_to_num(imp_src).astype("Float64")

    df = pd.DataFrame({
        "ts_utc": ts_utc,
        "country": country,
        "event_title": event_title.astype("string"),
        "event_key": event_key.astype("string"),
        "label": label.astype("string"),
        "type": typ.astype("string"),
        "estimate": estimate.astype("Float64"),
        "forecast": forecast.astype("Float64"),
        "previous": previous.astype("Float64"),
        "actual": actual.astype("Float64"),
        "unit": unit.astype("string"),
        "importance_n": importance_n,
    })

    df = df.dropna(subset=["ts_utc"])
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------
# Upsert vers la table `events`
# ---------------------------------------------------------------------
_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS events (
  ts_utc TIMESTAMP WITH TIME ZONE,
  country VARCHAR,
  event_title VARCHAR,
  event_key VARCHAR,
  label VARCHAR,
  type VARCHAR,
  estimate DOUBLE,
  forecast DOUBLE,
  previous DOUBLE,
  actual DOUBLE,
  unit VARCHAR,
  importance_n BIGINT
);
"""

_DB_COLS = [
    "ts_utc","country","event_title","event_key","label","type",
    "estimate","forecast","previous","actual","unit","importance_n"
]


def upsert_events(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> int:
    """
    Insère/fusionne les lignes dans `events`.
    Clé d’upsert: (ts_utc, country, event_key)
      - Si event_key manquant -> on substitue une clé dérivée (event_title||type).
    Retourne le nombre de lignes sources passées à la MERGE.
    """
    if df.empty:
        return 0

    con.execute(_EVENTS_DDL)

    for c in _DB_COLS:
        if c not in df.columns:
            df[c] = pd.NA

    df = df[_DB_COLS].copy()
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df["country"] = df["country"].astype("string").str.upper()

    missing_key = df["event_key"].isna() | (df["event_key"].astype(str).str.strip() == "")
    if missing_key.any():
        fallback = (df["event_title"].fillna("") + "||" + df["type"].fillna("")).astype("string")
        df.loc[missing_key, "event_key"] = (
            fallback.str.lower().str.replace(r"\s+", " ", regex=True)
        )

    con.register("tmp_eodhd_events", df)
    con.execute(f"""
        MERGE INTO events AS e
        USING tmp_eodhd_events AS t
        ON  e.ts_utc = t.ts_utc
        AND coalesce(e.country,'') = coalesce(t.country,'')
        AND coalesce(e.event_key,'') = coalesce(t.event_key,'')
        WHEN MATCHED THEN UPDATE SET
            event_title = t.event_title,
            label       = t.label,
            type        = t.type,
            estimate    = t.estimate,
            forecast    = t.forecast,
            previous    = t.previous,
            actual      = t.actual,
            unit        = t.unit,
            importance_n= CAST(t.importance_n AS BIGINT)
        WHEN NOT MATCHED THEN INSERT ({", ".join(_DB_COLS)})
        VALUES ({", ".join("t."+c for c in _DB_COLS)});
    """)
    con.unregister("tmp_eodhd_events")
    return len(df)


def upsert_events_df(df: pd.DataFrame, db_path: str) -> int:
    """
    Wrapper pratique pour les pages Streamlit:
    ouvre la connexion, appelle upsert_events, ferme.
    """
    if df is None or df.empty:
        return 0
    with duckdb.connect(db_path) as con:
        return upsert_events(con, df)
