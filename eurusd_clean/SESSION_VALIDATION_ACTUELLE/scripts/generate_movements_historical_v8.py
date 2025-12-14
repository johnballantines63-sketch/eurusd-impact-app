#!/usr/bin/env python3
"""
V8 - Génération MOVEMENTS_FILE historique (pré-2024) en mode STRICT V7-REPLAY.

On rejoue EXACTEMENT la logique V7 (scan_all_movements_independent.py) :
- calculate_historical_thresholds() (seuils percentiles historiques)
- detect_all_movements() (extrema locaux, début/fin, classification)
- Filtre peak_pips >= 10 pips

⚠️ SAFE : aucune modification de la logique V7, uniquement du replay + export.
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# PATHS / CONFIG
# -----------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent.parent.parent  # Ajuster si nécessaire

# DB utilisée en V7
DB_PATH = ROOT_DIR / "fx_impact_app" / "data" / "warehouse.duckdb"

# MOVEMENTS_FILE actuel (2024-2025) pour validation
MOVEMENTS_FILE_CURRENT = SCRIPT_DIR.parent / "outputs" / "all_movements_detected.csv"

OUT_DIR = SCRIPT_DIR / "outputs" / "direction_router_test"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_MOVEMENTS_HIST = OUT_DIR / "movements_historical.csv"

PAIR_PIP = 10000.0
MIN_MOVEMENT_PIPS = 10.0  # filtre V7

# -----------------------------------------------------------------------------
# Import logique V7
# -----------------------------------------------------------------------------
sys.path.insert(0, str(ROOT_DIR))  # pour src.core...
try:
    from src.core.movement_detection_robust import (
        detect_all_movements,
        calculate_historical_thresholds,
    )
except Exception as e:
    print("❌ Import V7 impossible. Vérifie PYTHONPATH.")
    print("   Erreur:", e)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Helpers tables/colonnes
# -----------------------------------------------------------------------------
def find_price_table(conn):
    tables = conn.execute("SHOW TABLES").df()["name"].tolist()
    for t in tables:
        tl = t.lower()
        if "prices" in tl and ("m1" in tl or "1m" in tl):
            return t
    for t in tables:
        if "prices" in t.lower():
            return t
    return None


def find_datetime_col(conn, table):
    cols = conn.execute(f"DESCRIBE {table}").df()
    names = cols["column_name"].tolist()
    print(f"   Colonnes disponibles dans {table}: {names}")

    for c in ["datetime", "date_time", "timestamp", "time", "ts_utc", "event_time", "event_datetime"]:
        if c in names:
            return c
    for c in names:
        cl = c.lower()
        if "time" in cl or "date" in cl:
            return c
    for _, row in cols.iterrows():
        t = str(row.get("column_type", "")).lower()
        if "timestamp" in t or "date" in t:
            return row["column_name"]
    return None


def load_prices_day(conn, prices_table, dt_col, date_str):
    q = f"""
    SELECT *
    FROM {prices_table}
    WHERE DATE({dt_col}) = '{date_str}'
    ORDER BY {dt_col} ASC
    """
    df = conn.execute(q).df()
    if df.empty:
        return df
    if dt_col != "datetime":
        df = df.rename(columns={dt_col: "datetime"})
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df = df.set_index("datetime")
    return df


def compute_thresholds(db_path: Path, table_name: str):
    # Signature V7 : calculate_historical_thresholds(db_path, years=5, min_samples=50, table_name='prices_bern')
    return calculate_historical_thresholds(db_path=db_path, table_name=table_name)

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main():
    print("=" * 80)
    print("GÉNÉRATION MOVEMENTS HISTORIQUES V8 — REPLAY V7 STRICT")
    print("=" * 80)
    print()

    print("📁 Chemins:")
    print(f"   SCRIPT_DIR: {SCRIPT_DIR}")
    print(f"   ROOT_DIR: {ROOT_DIR}")
    print(f"   DB_PATH: {DB_PATH}")
    print(f"   MOVEMENTS_FILE_CURRENT: {MOVEMENTS_FILE_CURRENT}")
    print(f"   OUT_MOVEMENTS_HIST: {OUT_MOVEMENTS_HIST}")
    print()

    if not DB_PATH.exists():
        print(f"❌ DB introuvable: {DB_PATH}")
        print("💡 Ajuste ROOT_DIR si besoin.")
        return

    conn = duckdb.connect(str(DB_PATH), read_only=True)

    prices_table = find_price_table(conn)
    if not prices_table:
        print("❌ Aucune table prix trouvée.")
        conn.close()
        return

    dt_col_prices = find_datetime_col(conn, prices_table)
    if not dt_col_prices:
        print(f"❌ Aucune colonne datetime trouvée dans {prices_table}")
        conn.close()
        return

    print(f"✅ prices_table: {prices_table} | datetime_col: {dt_col_prices}")

    # Dates disponibles dans prices
    df_dates = conn.execute(f"""
        SELECT DISTINCT DATE({dt_col_prices}) as date_hist
        FROM {prices_table}
        ORDER BY date_hist ASC
    """).df()

    print(f"📊 Analyse de {len(df_dates)} dates (prix)...")

    # Thresholds historiques V7
    print("🧮 Calcul thresholds historiques V7...")
    thresholds = compute_thresholds(DB_PATH, prices_table)
    print("   ✅ Thresholds calculés")
    print()

    all_movements_detected = []

    for idx, row in df_dates.iterrows():
        if (idx + 1) % 50 == 0:
            print(f"   Progression : {idx + 1}/{len(df_dates)} dates analysées...")

        date_str = pd.to_datetime(row["date_hist"]).strftime("%Y-%m-%d")
        df_prices = load_prices_day(conn, prices_table, dt_col_prices, date_str)

        if df_prices.empty or len(df_prices) < 60:
            continue

        day_start = df_prices.index[0]

        movements = detect_all_movements(
            df_prices=df_prices,
            event_time=day_start,
            baseline_time=day_start,
            thresholds=thresholds,
            window_hours=24.0,
        )

        for mov in movements:
            if mov.get("peak_pips", 0.0) >= MIN_MOVEMENT_PIPS:
                all_movements_detected.append({
                    "date": date_str,
                    "movement_start_time": mov.get("movement_start_time"),
                    "movement_start_pips": mov.get("movement_start_pips"),
                    "peak_time": mov.get("peak_time"),
                    "peak_pips": mov.get("peak_pips"),
                    "movement_end_time": mov.get("movement_end_time"),
                    "movement_class": mov.get("movement_class"),
                    "direction": mov.get("direction"),
                    "baseline_price": mov.get("baseline_price"),
                    "confidence": mov.get("confidence"),
                })

    conn.close()

    if not all_movements_detected:
        print("❌ Aucun movement détecté par V7.")
        return

    mv_df = pd.DataFrame(all_movements_detected)
    mv_df["movement_start_time"] = pd.to_datetime(mv_df["movement_start_time"], utc=True)
    mv_df["peak_time"] = pd.to_datetime(mv_df["peak_time"], utc=True)
    mv_df["movement_end_time"] = pd.to_datetime(mv_df["movement_end_time"], utc=True)

    mv_df.to_csv(OUT_MOVEMENTS_HIST, index=False)

    print("=" * 80)
    print("MOVEMENTS HISTORIQUES EXPORTÉS")
    print("=" * 80)
    print(f"💾 {OUT_MOVEMENTS_HIST}")
    print(f"📊 Lignes: {len(mv_df)}")
    print(f"   Période: {mv_df['movement_start_time'].min()} → {mv_df['movement_start_time'].max()}")
    print()

    # Validation 2024-2025
    if MOVEMENTS_FILE_CURRENT.exists():
        print("=" * 80)
        print("VALIDATION REPLAY V7 SUR 2024-2025")
        print("=" * 80)

        cur = pd.read_csv(MOVEMENTS_FILE_CURRENT)
        cur["movement_start_time"] = pd.to_datetime(cur["movement_start_time"], utc=True)

        mv_2425 = mv_df[mv_df["movement_start_time"].dt.year >= 2024]
        cur_2425 = cur[cur["movement_start_time"].dt.year >= 2024]

        print(f"Rebuild 2024-2025 : {len(mv_2425)} lignes")
        print(f"Current 2024-2025 : {len(cur_2425)} lignes")
        print()

        def stats(x):
            return {"n": len(x), "mean": float(np.mean(x)), "median": float(np.median(x))}

        col_rebuild = "peak_pips" if "peak_pips" in mv_2425.columns else "impact_pips"
        col_current = "peak_pips" if "peak_pips" in cur_2425.columns else "impact_pips"

        if col_rebuild in mv_2425.columns and col_current in cur_2425.columns:
            s1 = stats(mv_2425[col_rebuild])
            s2 = stats(cur_2425[col_current])

            print(f"Impact stats (rebuild: {col_rebuild}, current: {col_current}):")
            print(f"   Rebuild: n={s1['n']}, median={s1['median']:.2f}, mean={s1['mean']:.2f}")
            print(f"   Current: n={s2['n']}, median={s2['median']:.2f}, mean={s2['mean']:.2f}")
            print()

            drift = abs(s1["median"] - s2["median"]) / max(abs(s2["median"]), 1e-6)
            print(f"Drift median: {drift:.1%}")
            if drift < 0.10:
                print("✅ Drift < 10% → replay OK")
            else:
                print("⚠️ Drift >= 10% → vérifier filtres/params detect_all_movements")
        else:
            print("⚠️ Colonnes impact non trouvées pour comparaison.")
            print("   Rebuild cols:", mv_2425.columns.tolist())
            print("   Current cols:", cur_2425.columns.tolist())

        print()
    else:
        print("⚠️ MOVEMENTS_FILE actuel introuvable, validation skip.")

    print("=" * 80)
    print("✅ GÉNÉRATION TERMINÉE")
    print("=" * 80)
    print()
    print("Prochaines étapes:")
    print("1. Utiliser movements_historical.csv pour scan étendu")
    print("2. Lancer: python3 scan_patterns_historique_complet.py --min-date 2018-01-01 --max-date 2025-12-31")
    print()


if __name__ == "__main__":
    main()

