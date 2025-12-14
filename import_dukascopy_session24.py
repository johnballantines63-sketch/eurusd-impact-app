#!/usr/bin/env python3
"""
Import données EURUSD M1 depuis Dukascopy (source institutionnelle)
Session 24 - Remplacement HistData/EODHD par des données de qualité
"""

import os
import io
import lzma
import struct
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

# Ajouter le path du projet
sys.path.insert(0, str(Path(__file__).parent))

# -------------------- PARAMÈTRES --------------------
SYMBOL = "EURUSD"       # format Dukascopy: ex. "EURUSD", "GBPUSD"
YEARS  = 3              # profondeur historique
OUT_CSV = f"{SYMBOL}_M1_last{YEARS}y_dukascopy.csv"

# Timeout & retry réseau
HTTP_TIMEOUT = 30  # Augmenté à 30s
MAX_RETRIES = 3

# ---------------------------------------------------
# Les fichiers tick Dukascopy sont horaires:
# https://datafeed.dukascopy.com/datafeed/{SYMBOL}/{YYYY}/{MM-1}/{DD}/{HH}h_ticks.bi5
# - MM est "zero-based": Janvier=0, Décembre=11
# - Chaque enregistrement (20 octets) = 5 x int32 big-endian:
#   [ms_from_hour, bid*1e5, ask*1e5, bid_vol, ask_vol]
# ---------------------------------------------------

def dukascopy_tick_url(symbol: str, dt_utc: datetime) -> str:
    year = dt_utc.year
    mon0 = dt_utc.month - 1  # zero-based
    day  = dt_utc.day
    hour = dt_utc.hour
    return f"https://datafeed.dukascopy.com/datafeed/{symbol}/{year}/{mon0:02d}/{day:02d}/{hour:02d}h_ticks.bi5"

def fetch_hour_ticks(symbol: str, dt_utc: datetime) -> pd.DataFrame | None:
    """Télécharge et décode 1h de ticks. Retourne DataFrame (UTC)."""
    url = dukascopy_tick_url(symbol, dt_utc)
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=HTTP_TIMEOUT)
            if r.status_code == 404 or len(r.content) == 0:
                return None  # plage fermée (weekend/ferié) ou pas de données
            r.raise_for_status()
            raw = lzma.decompress(r.content)
            # 20 bytes per record
            rec_size = 20
            n = len(raw) // rec_size
            if n == 0:
                return None
            data = np.frombuffer(raw, dtype=">i4")  # big-endian int32
            data = data.reshape((-1, 5))            # [ms, bid, ask, bvol, avol]
            ms   = data[:, 0].astype(np.int64)
            bid  = data[:, 1] / 100000.0
            ask  = data[:, 2] / 100000.0
            bvol = data[:, 3].astype(np.int64)
            avol = data[:, 4].astype(np.int64)

            # Timestamp absolu en UTC
            base = int(dt_utc.replace(minute=0, second=0, microsecond=0).timestamp() * 1000)
            t_ms = base + ms
            ts = pd.to_datetime(t_ms, unit="ms", utc=True)

            df = pd.DataFrame({
                "time": ts,
                "bid": bid,
                "ask": ask,
                "bid_vol": bvol,
                "ask_vol": avol,
            })
            return df
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                # Attendre un peu avant retry
                import time
                time.sleep(1)
    
    # Pas de warning pour 404 (normal weekend)
    if "404" not in str(last_err):
        print(f"[WARN] Échec {dt_utc:%Y-%m-%d %H:00}: {last_err}")
    return None

def aggregate_to_m1(df_ticks: pd.DataFrame) -> pd.DataFrame:
    """Agrège des ticks BID/ASK en bougies M1 (BID OHLC + spread moyen + volume)."""
    if df_ticks is None or df_ticks.empty:
        return pd.DataFrame()

    df = df_ticks.copy()
    df["minute"] = df["time"].dt.floor("min")  # floor à la minute

    # OHLC sur BID
    o = df.groupby("minute")["bid"].first()
    h = df.groupby("minute")["bid"].max()
    l = df.groupby("minute")["bid"].min()
    c = df.groupby("minute")["bid"].last()

    # Volume tick = nombre de ticks par minute
    tv = df.groupby("minute")["bid"].size()

    # Spread moyen (en points, 1 point = 0.0001 sur EURUSD)
    spread_pts = (df["ask"] - df["bid"]) / 0.0001
    spr = spread_pts.groupby(df["minute"]).mean()

    out = pd.DataFrame({
        "time": o.index,
        "open": o.values,
        "high": h.values,
        "low":  l.values,
        "close": c.values,
        "volume": tv.values.astype(int),  # Renommé 'volume' au lieu de 'TickVolume'
        "spread": spr.values.round(2),     # Renommé 'spread' en minuscule
    })
    out = out.sort_values("time").reset_index(drop=True)
    return out

def daterange_hours(start_utc: datetime, end_utc: datetime):
    t = start_utc.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    while t < end_utc:
        yield t
        t += timedelta(hours=1)

def import_to_database(df: pd.DataFrame, db_path: str):
    """Importe dans la table prices_1m de DuckDB"""
    import duckdb
    
    print(f"\n💾 Import dans {db_path}...")
    
    with duckdb.connect(db_path) as con:
        con.execute("SET TimeZone='UTC'")
        
        # Compter lignes avant
        n_before = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
        print(f"   Lignes avant: {n_before:,}")
        
        # Vérifier structure table
        cols_info = con.execute("PRAGMA table_info('prices_1m')").df()
        existing_cols = set(cols_info["name"].str.lower())
        
        print(f"   Colonnes table: {existing_cols}")
        
        # Adapter selon structure
        if existing_cols == {"datetime", "close"}:
            # Table simple
            df_insert = df[["time", "close"]].copy()
            df_insert = df_insert.rename(columns={"time": "datetime"})
            insert_cols = "(datetime, close)"
            select_cols = "n.datetime, n.close"
        else:
            # Table complète
            df_insert = df.copy()
            df_insert = df_insert.rename(columns={"time": "datetime"})
            insert_cols = "(datetime, open, high, low, close, volume)"
            select_cols = "n.datetime, n.open, n.high, n.low, n.close, n.volume"
        
        # Enregistrer temporairement
        con.register("new_prices", df_insert)
        
        # Insérer (anti-doublon)
        con.execute(f"""
            INSERT INTO prices_1m {insert_cols}
            SELECT {select_cols}
            FROM new_prices n
            WHERE NOT EXISTS (
                SELECT 1 FROM prices_1m p
                WHERE p.datetime = n.datetime
            )
        """)
        
        con.unregister("new_prices")
        
        # Compter après
        n_after = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
        n_inserted = n_after - n_before
        
        print(f"   Lignes après: {n_after:,}")
        print(f"   Lignes insérées: {n_inserted:,}")
        
        # Stats
        stats = con.execute("""
            SELECT 
                COUNT(*) as total,
                MIN(datetime) as min_date,
                MAX(datetime) as max_date
            FROM prices_1m
        """).df().iloc[0]
        
        print(f"\n📊 Statistiques prices_1m:")
        print(f"   Total: {stats['total']:,} lignes")
        print(f"   Min: {stats['min_date']}")
        print(f"   Max: {stats['max_date']}")
        
        return n_inserted

def validate_september_11(df: pd.DataFrame):
    """Valide le 11 septembre dans les données Dukascopy"""
    print(f"\n{'=' * 80}")
    print("🔍 VALIDATION: 11 SEPTEMBRE 2025 (DUKASCOPY)")
    print("=" * 80)
    
    # Filtrer 14:30 UTC (attention, pas CEST!)
    # 14:30 heure de Berne (CEST) = 12:30 UTC
    phase1 = df[
        (df['time'] >= '2025-09-11 12:30:00') &
        (df['time'] < '2025-09-11 12:45:00')
    ]
    
    if phase1.empty:
        print("❌ Aucune donnée pour 12:30 UTC (14:30 Berne)")
        return False
    
    print(f"\n📊 Phase 1 (12:30-12:45 UTC = 14:30-14:45 Berne):")
    print(f"   Lignes: {len(phase1)}")
    
    # Afficher détail
    print(f"\n   📋 Détail minute par minute:")
    for _, row in phase1.head(15).iterrows():
        print(f"      {row['time']} | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f}")
    
    # Calculer mouvement
    start_price = phase1.iloc[0]['close']
    high_price = phase1['high'].max()
    low_price = phase1['low'].min()
    
    move_up = (high_price - start_price) * 10000
    move_down = (start_price - low_price) * 10000
    phase1_pips = max(move_up, move_down)
    
    print(f"\n   💰 Mouvement calculé:")
    print(f"      Prix départ: {start_price:.5f}")
    print(f"      Prix HIGH: {high_price:.5f}")
    print(f"      Prix LOW: {low_price:.5f}")
    print(f"      Mouvement: {phase1_pips:.2f} pips")
    
    print(f"\n   🎯 Attendu (MT5 André): ~600+ pips")
    
    if phase1_pips >= 400:
        print(f"   ✅ VALIDATION OK! Dukascopy capture le mouvement!")
        return True
    else:
        print(f"   ⚠️ Mouvement sous-estimé")
        return False

def main():
    print("=" * 80)
    print("🚀 SESSION 24 - IMPORT DUKASCOPY")
    print("=" * 80)
    print(f"\nSource: Dukascopy (institutionnel, haute qualité)")
    print(f"Symbol: {SYMBOL}")
    print(f"Période: {YEARS} dernières années")
    
    end_utc = datetime.now(timezone.utc)
    start_utc = end_utc - timedelta(days=int(365.25 * YEARS))

    all_m1 = []

    print(f"\n⬇️ Téléchargement ticks {SYMBOL} de {start_utc:%Y-%m-%d} à {end_utc:%Y-%m-%d} (UTC) ...")
    hours = list(daterange_hours(start_utc, end_utc))
    total_hours = len(hours)

    for i, h_utc in enumerate(hours, 1):
        df_ticks = fetch_hour_ticks(SYMBOL, h_utc)
        if df_ticks is None:
            continue
        df_m1 = aggregate_to_m1(df_ticks)
        if not df_m1.empty:
            all_m1.append(df_m1)

        # État d'avancement
        if i % 200 == 0:
            progress = (i / total_hours) * 100
            print(f"  • {i:,}/{total_hours:,} heures ({progress:.1f}%)...")

    if not all_m1:
        raise RuntimeError("❌ Aucune minute générée – problème réseau ou période invalide.")

    df = pd.concat(all_m1, ignore_index=True)
    df = df.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)

    print(f"\n✅ Téléchargement terminé: {len(df):,} lignes")

    # Sauvegarder CSV
    df_csv = df.copy()
    df_csv["Date"] = df_csv["time"].dt.strftime("%Y.%m.%d")
    df_csv["Time"] = df_csv["time"].dt.strftime("%H:%M:%S")
    out_csv = df_csv[["Date","Time","open","high","low","close","volume","spread"]]
    out_csv.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"✅ CSV sauvegardé: {OUT_CSV} ({len(out_csv):,} lignes)")

    # Valider 11 septembre
    validate_september_11(df)

    # Importer dans DB
    from fx_impact_app.src.config import get_db_path
    db_path = get_db_path()
    n_inserted = import_to_database(df, db_path)

    print(f"\n{'=' * 80}")
    print("🎉 IMPORT TERMINÉ!")
    print("=" * 80)
    print(f"Total lignes Dukascopy: {len(df):,}")
    print(f"Nouvelles lignes en DB: {n_inserted:,}")
    print(f"\n➡️ Prochaine étape: Vérifier 11 septembre dans la DB")

if __name__ == "__main__":
    main()
