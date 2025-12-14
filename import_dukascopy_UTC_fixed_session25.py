#!/usr/bin/env python3
"""
Import données EURUSD M1 depuis Dukascopy - VERSION CORRIGÉE UTC
Session 25 - Correction timezone pour garantir données en UTC strict
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
SYMBOL = "EURUSD"
YEARS  = 3
OUT_CSV = f"{SYMBOL}_M1_last{YEARS}y_dukascopy_UTC.csv"

HTTP_TIMEOUT = 30
MAX_RETRIES = 3

def dukascopy_tick_url(symbol: str, dt_utc: datetime) -> str:
    year = dt_utc.year
    mon0 = dt_utc.month - 1  # zero-based
    day  = dt_utc.day
    hour = dt_utc.hour
    return f"https://datafeed.dukascopy.com/datafeed/{symbol}/{year}/{mon0:02d}/{day:02d}/{hour:02d}h_ticks.bi5"

def fetch_hour_ticks(symbol: str, dt_utc: datetime) -> pd.DataFrame | None:
    """Télécharge et décode 1h de ticks. Retourne DataFrame (UTC strict)."""
    url = dukascopy_tick_url(symbol, dt_utc)
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=HTTP_TIMEOUT)
            if r.status_code == 404 or len(r.content) == 0:
                return None
            r.raise_for_status()
            raw = lzma.decompress(r.content)
            
            rec_size = 20
            n = len(raw) // rec_size
            if n == 0:
                return None
                
            data = np.frombuffer(raw, dtype=">i4")
            data = data.reshape((-1, 5))
            
            ms   = data[:, 0].astype(np.int64)
            bid  = data[:, 1] / 100000.0
            ask  = data[:, 2] / 100000.0
            bvol = data[:, 3].astype(np.int64)
            avol = data[:, 4].astype(np.int64)

            # CORRECTION: Créer timestamp en UTC explicite
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
                import time
                time.sleep(1)
    
    if "404" not in str(last_err):
        print(f"[WARN] Échec {dt_utc:%Y-%m-%d %H:00}: {last_err}")
    return None

def aggregate_to_m1(df_ticks: pd.DataFrame) -> pd.DataFrame:
    """Agrège ticks en M1 (BID OHLC)."""
    if df_ticks is None or df_ticks.empty:
        return pd.DataFrame()

    df = df_ticks.copy()
    
    # CORRECTION: S'assurer que time est en UTC
    if df["time"].dt.tz is None:
        df["time"] = df["time"].dt.tz_localize('UTC')
    elif str(df["time"].dt.tz) != 'UTC':
        df["time"] = df["time"].dt.tz_convert('UTC')
    
    df["minute"] = df["time"].dt.floor("min")

    # OHLC sur BID
    o = df.groupby("minute")["bid"].first()
    h = df.groupby("minute")["bid"].max()
    l = df.groupby("minute")["bid"].min()
    c = df.groupby("minute")["bid"].last()

    # Volume = nombre de ticks
    tv = df.groupby("minute")["bid"].size()

    # Spread moyen
    spread_pts = (df["ask"] - df["bid"]) / 0.0001
    spr = spread_pts.groupby(df["minute"]).mean()

    out = pd.DataFrame({
        "time": o.index,
        "open": o.values,
        "high": h.values,
        "low":  l.values,
        "close": c.values,
        "volume": tv.values.astype(int),
        "spread": spr.values.round(2),
    })
    out = out.sort_values("time").reset_index(drop=True)
    return out

def daterange_hours(start_utc: datetime, end_utc: datetime):
    t = start_utc.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    while t < end_utc:
        yield t
        t += timedelta(hours=1)

def import_to_database(df: pd.DataFrame, db_path: str):
    """Importe dans DuckDB en forçant UTC strict."""
    import duckdb
    
    print(f"\n💾 Import dans {db_path}...")
    
    with duckdb.connect(db_path) as con:
        # CORRECTION: Forcer UTC dans DuckDB
        con.execute("SET TimeZone='UTC'")
        
        n_before = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
        print(f"   Lignes avant: {n_before:,}")
        
        cols_info = con.execute("PRAGMA table_info('prices_1m')").df()
        existing_cols = set(cols_info["name"].str.lower())
        
        print(f"   Colonnes table: {existing_cols}")
        
        # CORRECTION: Convertir time en datetime sans timezone pour DuckDB
        df_insert = df.copy()
        
        # Enlever timezone (DuckDB stocke en UTC implicite)
        df_insert["datetime"] = df_insert["time"].dt.tz_localize(None)
        
        # Adapter colonnes
        if existing_cols == {"datetime", "close"}:
            df_insert = df_insert[["datetime", "close"]]
            insert_cols = "(datetime, close)"
            select_cols = "n.datetime, n.close"
        else:
            df_insert = df_insert[["datetime", "open", "high", "low", "close", "volume"]]
            insert_cols = "(datetime, open, high, low, close, volume)"
            select_cols = "n.datetime, n.open, n.high, n.low, n.close, n.volume"
        
        # Vérifier échantillon
        print(f"\n   📋 Échantillon données à insérer (3 premières lignes):")
        for idx, row in df_insert.head(3).iterrows():
            print(f"      {row['datetime']} | C={row['close']:.5f}")
        
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
        
        n_after = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
        n_inserted = n_after - n_before
        
        print(f"   Lignes après: {n_after:,}")
        print(f"   Lignes insérées: {n_inserted:,}")
        
        # Vérifier échantillon inséré
        print(f"\n   📋 Vérification échantillon en DB (11 sept 12:30-12:35 UTC):")
        check = con.execute("""
            SELECT datetime, open, high, low, close
            FROM prices_1m
            WHERE datetime >= '2025-09-11 12:30:00'
              AND datetime <= '2025-09-11 12:35:00'
            ORDER BY datetime
        """).df()
        
        if not check.empty:
            for idx, row in check.iterrows():
                print(f"      {row['datetime']} | O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f}")
        else:
            print("      ⚠️ Aucune donnée pour 11 sept 12:30 UTC")
        
        # Stats globales
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

def validate_september_11(df: pd.DataFrame) -> bool:
    """Valide mouvement 11 septembre 2025."""
    print("\n" + "=" * 80)
    print("🔍 VALIDATION 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    # Filtrer 12:30-12:45 UTC
    phase1 = df[(df['time'] >= '2025-09-11 12:30:00+00:00') & 
                (df['time'] < '2025-09-11 12:46:00+00:00')].copy()
    
    if phase1.empty:
        print("❌ Aucune donnée pour 12:30 UTC")
        return False
    
    print(f"\n📊 Phase 1 (12:30-12:45 UTC):")
    print(f"   Lignes: {len(phase1)}")
    
    # Détail minute par minute
    print(f"\n   📋 Détail minute par minute:")
    for _, row in phase1.head(15).iterrows():
        time_str = row['time'].strftime('%H:%M UTC')
        print(f"      {time_str} | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f}")
    
    # Calculer Phase 1 (12:30 → 12:35)
    phase1_5min = phase1[phase1['time'] < '2025-09-11 12:36:00+00:00']
    
    start_price = phase1_5min.iloc[0]['close']
    high_price = phase1_5min['high'].max()
    low_price = phase1_5min['low'].min()
    
    move_up = (high_price - start_price) * 10000
    move_down = (start_price - low_price) * 10000
    phase1_pips = max(move_up, move_down)
    
    print(f"\n   💰 Mouvement Phase 1 (12:30 → 12:35):")
    print(f"      Prix départ: {start_price:.5f}")
    print(f"      High: {high_price:.5f} (+{move_up:.2f} pips)")
    print(f"      Low:  {low_price:.5f} ({-move_down:.2f} pips)")
    print(f"      Mouvement: {phase1_pips:.2f} pips")
    
    print(f"\n   🎯 ATTENDU (MT5 André): 37.4 pips")
    
    diff = abs(phase1_pips - 37.4)
    
    if diff <= 5:
        print(f"   ✅ EXCELLENT! Écart de seulement {diff:.2f} pips")
        return True
    elif diff <= 10:
        print(f"   ⚠️ ACCEPTABLE. Écart de {diff:.2f} pips")
        return True
    else:
        print(f"   ❌ ÉCART IMPORTANT: {diff:.2f} pips")
        return False

def main():
    print("=" * 80)
    print("🚀 SESSION 25 - IMPORT DUKASCOPY (VERSION UTC CORRIGÉE)")
    print("=" * 80)
    print(f"\nSource: Dukascopy (institutionnel)")
    print(f"Symbol: {SYMBOL}")
    print(f"Période: {YEARS} dernières années")
    print(f"Timezone: UTC STRICT (correction appliquée)")
    
    end_utc = datetime.now(timezone.utc)
    start_utc = end_utc - timedelta(days=int(365.25 * YEARS))

    all_m1 = []

    print(f"\n⬇️ Téléchargement ticks {SYMBOL} de {start_utc:%Y-%m-%d} à {end_utc:%Y-%m-%d} (UTC)...")
    hours = list(daterange_hours(start_utc, end_utc))
    total_hours = len(hours)

    for i, h_utc in enumerate(hours, 1):
        df_ticks = fetch_hour_ticks(SYMBOL, h_utc)
        if df_ticks is None:
            continue
        df_m1 = aggregate_to_m1(df_ticks)
        if not df_m1.empty:
            all_m1.append(df_m1)

        if i % 200 == 0:
            progress = (i / total_hours) * 100
            print(f"  • {i:,}/{total_hours:,} heures ({progress:.1f}%)...")

    if not all_m1:
        raise RuntimeError("❌ Aucune minute générée")

    df = pd.concat(all_m1, ignore_index=True)
    df = df.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)

    print(f"\n✅ Téléchargement terminé: {len(df):,} lignes")

    # CSV
    df_csv = df.copy()
    df_csv["time_utc"] = df_csv["time"].dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    out_csv = df_csv[["time_utc","open","high","low","close","volume","spread"]]
    out_csv.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"✅ CSV sauvegardé: {OUT_CSV}")

    # Valider 11 septembre
    is_valid = validate_september_11(df)

    # Importer dans DB
    from fx_impact_app.src.config import get_db_path
    db_path = get_db_path()
    n_inserted = import_to_database(df, db_path)

    print(f"\n{'=' * 80}")
    print("🎉 IMPORT TERMINÉ!")
    print("=" * 80)
    print(f"Total lignes Dukascopy: {len(df):,}")
    print(f"Nouvelles lignes en DB: {n_inserted:,}")
    
    if is_valid:
        print(f"\n✅ Validation 11 septembre: RÉUSSIE")
        print(f"➡️ Prêt pour recalculer les 944 cas extrêmes et créer formule V4")
    else:
        print(f"\n⚠️ Validation 11 septembre: À VÉRIFIER")

if __name__ == "__main__":
    main()
