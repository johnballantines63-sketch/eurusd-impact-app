#!/usr/bin/env python3
"""
detect_double_wave.py
---------------------
Détecte des "double waves" haussières (Low0→High1→Low2→High3) sur données M1.
- Connexion DuckDB OU chargement CSV.
- Extraction pivots type ZigZag.
- Filtrage selon amplitudes/durées (paramétrables).
- Export CSV des détections + résumé console.

Exemple:
python detect_double_wave.py \
  --db-path /path/warehouse.duckdb \
  --sql "SELECT ts, close as price, volume FROM eurusd_m1 WHERE ts BETWEEN '2024-09-10' AND '2024-09-12' ORDER BY ts" \
  --w1-min-pips 30 --ext-min-pips 55 --zz-min-pips 10

Auteur: ChatGPT pour André VALENTIN
Date: 2025-11-06
"""
import argparse, sys, math, os
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# --- Utils --------------------------------------------------------------------

PIP = 0.0001

def ensure_datetime_index(df, col='ts'):
    if not isinstance(df.index, pd.DatetimeIndex):
        df[col] = pd.to_datetime(df[col], utc=True)
        df.set_index(col, inplace=True)
    df.sort_index(inplace=True)
    return df

def atr(series_high, series_low, series_close, n=14):
    # True range
    prev_close = series_close.shift(1)
    tr = pd.concat([
        (series_high - series_low).abs(),
        (series_high - prev_close).abs(),
        (series_low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()

# --- ZigZag Pivots ------------------------------------------------------------

def zigzag_pivots(prices: pd.Series, zz_threshold_pips: float):
    """Retourne liste de pivots (type, time, price) avec seuil 'zz_threshold_pips'."""
    zz = zz_threshold_pips * PIP
    piv = []
    if prices.empty:
        return piv
    last_ext_idx = prices.index[0]
    last_ext = prices.iloc[0]
    dirn = 0  # 0 inconnu, +1 up, -1 down
    for t, p in prices.items():
        if dirn >= 0:
            if p >= last_ext:
                last_ext = p; last_ext_idx = t
            elif (last_ext - p) >= zz:
                piv.append(("H", last_ext_idx, float(last_ext)))
                dirn = -1
                last_ext = p; last_ext_idx = t
        if dirn <= 0:
            if p <= last_ext:
                last_ext = p; last_ext_idx = t
            elif (p - last_ext) >= zz:
                piv.append(("L", last_ext_idx, float(last_ext)))
                dirn = +1
                last_ext = p; last_ext_idx = t
    # Terminer sur dernier extrême
    piv.append(("H" if dirn >= 0 else "L", last_ext_idx, float(last_ext)))
    return piv

# --- Détection Double Wave ----------------------------------------------------

def detect_double_waves(prices: pd.Series,
                        zz_min_pips=10.0,
                        w1_min_pips=30.0,
                        w1_max_min=10,
                        pb_max_min=12,
                        retr_min=0.25,
                        retr_max=0.70,
                        w2_max_min=30,
                        ext_min_pips=55.0,
                        alpha=0.6):
    """Renvoie DataFrame de patterns détectés."""
    piv = zigzag_pivots(prices, zz_min_pips)
    rows = []
    for i in range(len(piv)-3):
        t0type, t0, p0 = piv[i]
        t1type, t1, p1 = piv[i+1]
        t2type, t2, p2 = piv[i+2]
        t3type, t3, p3 = piv[i+3]
        # pattern haussier L-H-L-H
        if (t0type, t1type, t2type, t3type) != ("L","H","L","H"):
            continue
        wave1 = p1 - p0
        if wave1 < w1_min_pips*PIP:
            continue
        dur_w1 = (t1 - t0).total_seconds()/60.0
        if dur_w1 > w1_max_min:
            continue
        retr = (p1 - p2) / max(wave1, 1e-12)
        if retr < retr_min or retr > retr_max:
            continue
        dur_pb = (t2 - t1).total_seconds()/60.0
        if dur_pb > pb_max_min:
            continue
        if not (p3 > p1):
            continue
        dur_w2 = (t3 - t2).total_seconds()/60.0
        if dur_w2 > w2_max_min:
            continue
        wave2 = p3 - p2
        ext_tot = p3 - p0
        if not (ext_tot >= ext_min_pips*PIP or wave2 >= alpha*wave1):
            continue
        rows.append({
            "low0_time": t0,
            "high1_time": t1,
            "low2_time": t2,
            "high3_time": t3,
            "low0": p0, "high1": p1, "low2": p2, "high3": p3,
            "wave1_pips": (p1-p0)/PIP,
            "retr_pct": 100.0*retr,
            "wave2_pips": (p3-p2)/PIP,
            "ext_total_pips": (p3-p0)/PIP,
            "dur_w1_min": dur_w1,
            "dur_pb_min": dur_pb,
            "dur_w2_min": dur_w2
        })
    return pd.DataFrame(rows)

# --- IO (DuckDB / CSV) --------------------------------------------------------

def load_prices(db_path=None, sql=None, csv_path=None, price_col='price'):
    if db_path and sql:
        try:
            import duckdb  # import local pour rendre le script portable
        except Exception as e:
            raise RuntimeError("duckdb n'est pas disponible. Installe-le ou utilise --csv-path.") from e
        con = duckdb.connect(db_path)
        df = con.execute(sql).fetch_df()
        con.close()
    elif csv_path:
        df = pd.read_csv(csv_path)
    else:
        raise ValueError("Spécifie --db-path et --sql, ou bien --csv-path.")
    if 'ts' not in df.columns or price_col not in df.columns:
        raise ValueError("Les colonnes exigées sont: ts, {price_col}".format(price_col=price_col))
    df = ensure_datetime_index(df, 'ts')
    # nettoyer
    df = df[[price_col]].rename(columns={price_col:'close'}).dropna()
    return df

# --- CLI ----------------------------------------------------------------------

def parse_args():
    ap = argparse.ArgumentParser(description="Détection de Double Wave sur EUR/USD M1")
    ap.add_argument("--db-path", type=str, help="Chemin du fichier DuckDB")
    ap.add_argument("--sql", type=str, help="Requête SQL renvoyant ts, price[, volume]")
    ap.add_argument("--csv-path", type=str, help="Chemin CSV alternatif avec colonnes ts, price")
    ap.add_argument("--price-col", type=str, default="price")
    # Params
    ap.add_argument("--zz-min-pips", type=float, default=10.0)
    ap.add_argument("--w1-min-pips", type=float, default=30.0)
    ap.add_argument("--w1-max-min", type=int, default=10)
    ap.add_argument("--pb-max-min", type=int, default=12)
    ap.add_argument("--retr-min", type=float, default=0.25)
    ap.add_argument("--retr-max", type=float, default=0.70)
    ap.add_argument("--w2-max-min", type=int, default=30)
    ap.add_argument("--ext-min-pips", type=float, default=55.0)
    ap.add_argument("--alpha", type=float, default=0.6)
    ap.add_argument("--out-csv", type=str, default="double_waves.csv")
    return ap.parse_args()

def main():
    args = parse_args()
    df = load_prices(
        db_path=args.db_path, sql=args.sql,
        csv_path=args.csv_path, price_col=args.price_col
    )
    detections = detect_double_waves(
        df['close'],
        zz_min_pips=args.zz_min_pips,
        w1_min_pips=args.w1_min_pips,
        w1_max_min=args.w1_max_min,
        pb_max_min=args.pb_max_min,
        retr_min=args.retr_min,
        retr_max=args.retr_max,
        w2_max_min=args.w2_max_min,
        ext_min_pips=args.ext_min_pips,
        alpha=args.alpha
    )
    if detections.empty:
        print("Aucun double wave détecté avec ces paramètres.")
    else:
        print(f"{len(detections)} double wave(s) détecté(s). Exemples:\n")
        print(detections.head(10).to_string(index=False))
    detections.to_csv(args.out_csv, index=False)
    print(f"\nRésultats sauvegardés → {args.out_csv}")

if __name__ == "__main__":
    main()
