"""
EODHD CLIENT CORRIGÉ - Session 113
===================================

Version corrigée qui élimine les doublons "base" à l'import.

Session 113 - André Valentin
"""
from __future__ import annotations
import os
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests
import duckdb

EOD_BASE = "https://eodhd.com/api/economic-events"


def get_eod_key() -> str:
    """Récupère la clé EODHD depuis l'env (EODHD_API_KEY)."""
    key = os.environ.get("EODHD_API_KEY")
    if not key or str(key).strip().lower() in {"none", "true", "false"}:
        raise RuntimeError("Missing EODHD_API_KEY.")
    return key.strip()


def _to_ymd(x: Any) -> str:
    """Force un format YYYY-MM-DD."""
    ts = pd.to_datetime(x, utc=True)
    return ts.strftime("%Y-%m-%d")


def fetch_calendar_json(
    d1: Any,
    d2: Any,
    countries: Optional[Iterable[str]] = None,
    importance: Optional[Iterable[int]] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Appelle /economic-events EODHD."""
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
        if data.get("code") or data.get("message"):
            raise RuntimeError(f"EODHD returned error: {data}")
        data = [data]
    if not isinstance(data, list):
        raise RuntimeError("Unexpected EODHD payload (not a list).")
    return data


def _col(df: pd.DataFrame, *names: str) -> pd.Series:
    """Renvoie la première colonne existante."""
    for n in names:
        if n in df.columns:
            return df[n]
    return pd.Series(pd.NA, index=df.index)


def _to_utc_series(s: pd.Series) -> pd.Series:
    """Parsage datetime -> tz-aware UTC."""
    if s is None:
        return pd.Series([], dtype="datetime64[ns, UTC]")
    out = pd.to_datetime(s, errors="coerce", utc=True)
    return out


def _importance_to_num(s: pd.Series) -> pd.Series:
    """Mappe le champ de priorité vers 1..3."""
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
    """Normalise le JSON EODHD en DataFrame."""
    if not items:
        return pd.DataFrame()

    raw = pd.DataFrame(items)

    # Champs texte
    event_title = _col(raw, "event", "indicator", "title", "event_title")
    label = _col(raw, "label", "shortname", "short_name", "name")
    typ = _col(raw, "category", "type", "group", "event_group")

    # Clé
    key_src = _col(raw, "event_id", "id", "code")
    event_key = key_src.copy()
    
    if event_key.isna().all():
        def make_key(title, typ):
            t = str(title).strip() if pd.notna(title) else ""
            y = str(typ).strip() if pd.notna(typ) and str(typ).strip() else ""
            if t and y:
                return f"{t}_{y}"
            return t or y or "unknown"
        
        event_key = pd.Series([
            make_key(title, typ)
            for title, typ in zip(event_title, typ)
        ], index=event_title.index)
        
        event_key = (
            event_key.astype(str)
                .str.strip()
                .str.lower()
                .str.replace(r"\s+", " ", regex=True)
        )

    # Pays
    country = _col(raw, "country", "country_code", "ccy", "currency")
    country = country.astype("string").str.upper()

    # Timestamps
    ts = _col(raw, "date", "datetime", "timestamp", "releaseTime", "time")
    ts_utc = _to_utc_series(ts)

    # Numeric values
    estimate = pd.to_numeric(_col(raw, "estimate", "estimated", "consensus"), errors="coerce")
    forecast = pd.to_numeric(_col(raw, "forecast", "forecasted"), errors="coerce")
    previous = pd.to_numeric(_col(raw, "previous", "prev"), errors="coerce")
    actual = pd.to_numeric(_col(raw, "actual", "value"), errors="coerce")

    unit = _col(raw, "unit", "unit_short", "units").astype("string")
    
    # Extraire comparison (mom, yoy, qoq)
    comparison = _col(raw, "comparison").astype("string")

    # Importance
    imp_src = _col(raw, "importance", "impact", "priority", "importance_n")
    importance_n = _importance_to_num(imp_src).astype("Float64")
    
    # Nouveaux champs
    period = _col(raw, "period").astype("string")
    change = pd.to_numeric(_col(raw, "change"), errors="coerce").astype("Float64")
    change_percentage = pd.to_numeric(_col(raw, "change_percentage"), errors="coerce").astype("Float64")

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
        "comparison": comparison,
        "importance_n": importance_n,
        "period": period,
        "change": change,
        "change_percentage": change_percentage,
    })

    df = df.dropna(subset=["ts_utc"])

    # Enrichir event_key avec comparison
    for idx in df.index:
        comp = df.at[idx, 'comparison']
        if pd.notna(comp):
            comp_lower = str(comp).lower().strip()
            event_key_current = str(df.at[idx, 'event_key']).lower().strip()
            
            if comp_lower in ['mom', 'yoy', 'qoq']:
                if comp_lower not in event_key_current:
                    df.at[idx, 'event_key'] = f"{event_key_current}_{comp_lower}"
    
    # Supprimer les versions "base" si dérivés existent
    df['event_key_base'] = df['event_key'].str.replace(r'_(mom|yoy|qoq)$', '', regex=True)
    
    bases_with_derivatives = set()
    for base in df['event_key_base'].unique():
        group = df[df['event_key_base'] == base]
        has_derivatives = any(key.endswith(('_mom', '_yoy', '_qoq')) for key in group['event_key'])
        has_base = any(not key.endswith(('_mom', '_yoy', '_qoq')) for key in group['event_key'])
        if has_derivatives and has_base:
            bases_with_derivatives.add(base)
    
    if bases_with_derivatives:
        is_in_problematic_base = df['event_key_base'].isin(bases_with_derivatives)
        is_base_version = ~df['event_key'].str.endswith(('_mom', '_yoy', '_qoq'))
        mask_to_keep = ~(is_in_problematic_base & is_base_version)
        df = df[mask_to_keep].copy()
    
    df = df.drop(columns=['comparison', 'event_key_base'], errors='ignore')
    
    return df.reset_index(drop=True)


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
  importance_n BIGINT,
  period VARCHAR,
  change DOUBLE,
  change_percentage DOUBLE
);
"""

_DB_COLS = [
    "ts_utc","country","event_title","event_key","label","type",
    "estimate","forecast","previous","actual","unit","importance_n",
    "period","change","change_percentage"
]


def upsert_events(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> int:
    """Insère/fusionne les lignes dans `events`."""
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
        def make_fallback(title, typ):
            t = str(title).strip() if pd.notna(title) and str(title).strip() else ""
            y = str(typ).strip() if pd.notna(typ) and str(typ).strip() else ""
            if t and y:
                return f"{t}_{y}"
            return t or y or "unknown_event"
        
        fallback = pd.Series([
            make_fallback(title, typ)
            for title, typ in zip(df["event_title"], df["type"])
        ], index=df.index)
        
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
    """Wrapper pratique pour Streamlit."""
    if df is None or df.empty:
        return 0
    with duckdb.connect(db_path) as con:
        return upsert_events(con, df)


def fetch_and_import(
    start_date: str,
    end_date: str,
    db_path: str,
    countries: Optional[List[str]] = None,
    importance: Optional[List[int]] = None
) -> int:
    """Fetch EODHD + import en une seule fonction."""
    if countries is None:
        countries = ['US', 'EU', 'DE']
    
    print(f"Fetch EODHD: {start_date} → {end_date}")
    print(f"  Pays: {', '.join(countries) if countries else 'TOUS'}")
    print(f"  Importance: {importance}")
    
    raw_data = fetch_calendar_json(start_date, end_date, countries, importance)
    print(f"  Reçu: {len(raw_data)} événements bruts")
    
    df = calendar_to_events_df(raw_data)
    print(f"  Après nettoyage: {len(df)} événements")
    
    count = upsert_events_df(df, db_path)
    print(f"  Importé: {count} événements")
    
    return count
