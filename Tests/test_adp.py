# Tests/test_adp.py
from __future__ import annotations

import argparse
from typing import List
import duckdb
import pandas as pd

# --- DB path (V5) + fallback -------------------------------------------------
try:
    from fx_impact_app.src.config import get_db_path  # type: ignore
except Exception:
    from pathlib import Path
    def get_db_path() -> str:
        return (Path(__file__).resolve().parents[1] / "fx_impact_app" / "data" / "warehouse.duckdb").as_posix()

# --- Time helpers -------------------------------------------------------------
def to_naive_utc(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    else:
        t = t.tz_convert("UTC")
    return t.tz_localize(None)

def day_bounds_utc(date_str: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """[start, end) UTC, end exclusive (next day 00:00)."""
    start = to_naive_utc(f"{date_str} 00:00:00")
    end   = to_naive_utc(pd.Timestamp(date_str) + pd.Timedelta(days=1))
    return start, end

def fmt_local(ts_utc: pd.Timestamp, tz: str) -> str:
    if pd.isna(ts_utc):
        return ""
    return (pd.Timestamp(ts_utc)
            .tz_localize("UTC")
            .tz_convert(tz)
            .strftime("%Y-%m-%d %H:%M:%S %Z"))

# --- Query builder ------------------------------------------------------------
TEXT_COL_CANDIDATES: List[str] = ["event_title", "event_key", "type", "label"]

def build_select(cols_present: set[str]) -> list[str]:
    sel = ["CAST(ts_utc AS TIMESTAMP) AS ts_utc"]
    for c in ["country","event_title","event_key","type","label","estimate","forecast","previous","actual","unit","importance_n"]:
        if c in cols_present:
            sel.append(c)
    return sel

def build_where(cols_present: set[str], countries: list[str] | None) -> tuple[str, list]:
    where = ["ts_utc >= ? AND ts_utc < ?"]
    params: list = []

    # Countries filter
    if countries and "country" in cols_present:
        where.append("upper(country) IN (" + ",".join(["?"] * len(countries)) + ")")
        params += [c.upper() for c in countries]

    # ADP search across available text cols
    text_cols = [c for c in TEXT_COL_CANDIDATES if c in cols_present]
    if text_cols:
        like_block = " OR ".join([f"lower(coalesce({c},'')) LIKE ?" for c in text_cols])
        where.append("(" + like_block + ")")
        params += ["%adp%"] * len(text_cols)

    return " AND ".join(where), params

# --- Main ---------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Lister les événements ADP d’un jour (UTC) dans `events`.")
    ap.add_argument("--date", "-d", default=pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d"),
                    help="Jour UTC au format YYYY-MM-DD (défaut: aujourd'hui UTC)")
    ap.add_argument("--tz", default="Europe/Zurich", help="Fuseau d’affichage pour ts_local")
    ap.add_argument("--country", "-c", action="append",
                    help="Filtre pays (répéter l’option pour plusieurs). Ex: -c US -c EU")
    ap.add_argument("--csv", help="Chemin CSV d’export (optionnel)")
    args = ap.parse_args()

    db = get_db_path()
    start, end = day_bounds_utc(args.date)

    con = duckdb.connect(db)

    # Vérif existence table
    has_events = con.execute("""
        SELECT 1
        FROM information_schema.tables
        WHERE lower(table_name)='events'
        LIMIT 1
    """).fetchone()
    if not has_events:
        con.close()
        raise SystemExit("❌ Table `events` introuvable. Insère d’abord des événements via 0_Live-Calendar-Forecast.")

    # Colonnes présentes
    cols_present = {r[1].lower() for r in con.execute("PRAGMA table_info('events')").fetchall()}

    sel = build_select(cols_present)
    where_sql, extra_params = build_where(cols_present, args.country)
    sql = f"""
        SELECT {', '.join(sel)}
        FROM events
        WHERE {where_sql}
        ORDER BY ts_utc
    """
    params = [start.to_pydatetime(), end.to_pydatetime()] + extra_params
    df = con.execute(sql, params).df()
    con.close()

    print(f"DB: {db}")
    print(f"Fenêtre UTC: [{start} .. {end})")
    print(f"Filtre pays: {args.country or '(aucun)'}")
    print(f"Colonnes présentes: {sorted(cols_present)}")
    print(f"Résultats: {len(df)} ligne(s)\n")

    if df.empty:
        print("❌ Aucune ligne ADP dans `events` pour ce jour/filtre.")
        print("   Astuce: Ouvre la page Streamlit 0_Live-Calendar-Forecast, sélectionne la date, 'Récupérer' puis 'Insérer',")
        print("           puis relance ce test.")
        return

    # ts_local en post-traitement
    df["ts_local"] = df["ts_utc"].apply(lambda t: fmt_local(t, args.tz))
    # Réordonner colonnes si dispo
    order = [c for c in ["ts_local","ts_utc","country","event_title","label","type","event_key","estimate","forecast","previous","actual","unit","importance_n"] if c in df.columns]
    df = df[order]

    # Affichage
    with pd.option_context("display.max_rows", 200, "display.max_columns", None, "display.width", 200):
        print(df.to_string(index=False))

    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"\n💾 Exporté: {args.csv}")

if __name__ == "__main__":
    main()
