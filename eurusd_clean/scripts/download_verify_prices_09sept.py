"""
Télécharger les prix Dukascopy pour vérification
Période : 09.09.2025 02:00 → 10.09.2025 02:00
Export en CSV avec agrégation H1
"""
import sys
from pathlib import Path
import lzma
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import pytz

sys.path.insert(0, str(Path(__file__).parent.parent))

# Paramètres
SYMBOL = "EURUSD"
HTTP_TIMEOUT = 30
MAX_RETRIES = 3

def dukascopy_tick_url(symbol: str, dt_utc: datetime) -> str:
    """URL Dukascopy pour 1 heure de ticks."""
    year = dt_utc.year
    mon0 = dt_utc.month - 1  # zero-based
    day = dt_utc.day
    hour = dt_utc.hour
    return f"https://datafeed.dukascopy.com/datafeed/{symbol}/{year}/{mon0:02d}/{day:02d}/{hour:02d}h_ticks.bi5"

def fetch_hour_ticks(symbol: str, dt_utc: datetime) -> pd.DataFrame | None:
    """Télécharge et décode 1h de ticks en UTC strict."""
    url = dukascopy_tick_url(symbol, dt_utc)
    last_err = None
    
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=HTTP_TIMEOUT)
            if r.status_code == 404 or len(r.content) == 0:
                return None  # Weekend/fermé
            r.raise_for_status()
            
            raw = lzma.decompress(r.content)
            rec_size = 20
            n = len(raw) // rec_size
            if n == 0:
                return None
            
            data = np.frombuffer(raw, dtype=">i4")
            data = data.reshape((-1, 5))
            
            ms = data[:, 0].astype(np.int64)
            bid = data[:, 1] / 100000.0
            ask = data[:, 2] / 100000.0
            
            # Timestamp absolu UTC
            base = int(dt_utc.replace(minute=0, second=0, microsecond=0).timestamp() * 1000)
            t_ms = base + ms
            ts = pd.to_datetime(t_ms, unit="ms", utc=True)
            
            df = pd.DataFrame({
                "time": ts,
                "bid": bid,
                "ask": ask,
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
    
    # S'assurer UTC
    if df["time"].dt.tz is None:
        df["time"] = df["time"].dt.tz_localize('UTC')
    
    df["minute"] = df["time"].dt.floor("min")
    
    # OHLC sur BID
    o = df.groupby("minute")["bid"].first()
    h = df.groupby("minute")["bid"].max()
    l = df.groupby("minute")["bid"].min()
    c = df.groupby("minute")["bid"].last()
    v = df.groupby("minute").size()
    
    df_m1 = pd.DataFrame({
        "datetime": o.index,
        "open": o.values,
        "high": h.values,
        "low": l.values,
        "close": c.values,
        "volume": v.values
    })
    
    return df_m1

def aggregate_to_h1(df_m1: pd.DataFrame) -> pd.DataFrame:
    """Agrège M1 en H1."""
    if df_m1 is None or df_m1.empty:
        return pd.DataFrame()
    
    df = df_m1.copy()
    
    # S'assurer UTC
    if df["datetime"].dt.tz is None:
        df["datetime"] = df["datetime"].dt.tz_localize('UTC')
    
    df["hour"] = df["datetime"].dt.floor("H")
    
    # OHLC
    o = df.groupby("hour")["open"].first()
    h = df.groupby("hour")["high"].max()
    l = df.groupby("hour")["low"].min()
    c = df.groupby("hour")["close"].last()
    v = df.groupby("hour")["volume"].sum()
    
    df_h1 = pd.DataFrame({
        "datetime": o.index,
        "open": o.values,
        "high": h.values,
        "low": l.values,
        "close": c.values,
        "volume": v.values
    })
    
    return df_h1

def main():
    # Période : 09.09.2025 02:00 → 10.09.2025 02:00 (heure de Berne)
    tz_bern = pytz.timezone('Europe/Zurich')
    start_bern = tz_bern.localize(datetime(2025, 9, 9, 2, 0))
    end_bern = tz_bern.localize(datetime(2025, 9, 10, 2, 0))
    
    # Convertir en UTC
    start_utc = start_bern.astimezone(timezone.utc)
    end_utc = end_bern.astimezone(timezone.utc)
    
    print('='*80)
    print('TÉLÉCHARGEMENT PRIX DUKASCOPY POUR VÉRIFICATION')
    print('='*80)
    print(f'Période (Berne) : {start_bern.strftime("%Y-%m-%d %H:%M")} → {end_bern.strftime("%Y-%m-%d %H:%M")}')
    print(f'Période (UTC)   : {start_utc.strftime("%Y-%m-%d %H:%M")} → {end_utc.strftime("%Y-%m-%d %H:%M")}')
    print()
    
    # Télécharger toutes les heures
    all_m1 = []
    current = start_utc.replace(minute=0, second=0, microsecond=0)
    
    while current < end_utc:
        print(f'Téléchargement {current.strftime("%Y-%m-%d %H:00")} UTC...', end=' ')
        df_ticks = fetch_hour_ticks(SYMBOL, current)
        
        if df_ticks is not None and not df_ticks.empty:
            df_m1 = aggregate_to_m1(df_ticks)
            if not df_m1.empty:
                all_m1.append(df_m1)
                print(f'✅ {len(df_m1)} bougies M1')
            else:
                print('⚠️  Aucune bougie M1')
        else:
            print('❌ Données non disponibles')
        
        current += timedelta(hours=1)
    
    if not all_m1:
        print('❌ Aucune donnée téléchargée')
        return
    
    # Concaténer toutes les bougies M1
    df_m1_all = pd.concat(all_m1, ignore_index=True)
    df_m1_all = df_m1_all.sort_values('datetime').reset_index(drop=True)
    
    # Convertir en heure de Berne
    df_m1_all['datetime_bern'] = df_m1_all['datetime'].dt.tz_convert('Europe/Zurich')
    
    # Agrégation H1
    df_h1 = aggregate_to_h1(df_m1_all)
    df_h1['datetime_bern'] = df_h1['datetime'].dt.tz_convert('Europe/Zurich')
    
    print()
    print(f'✅ Total : {len(df_m1_all)} bougies M1, {len(df_h1)} bougies H1')
    print()
    
    # Sauvegarder en CSV
    output_dir = Path(__file__).parent.parent / 'data' / 'verification'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # CSV M1
    csv_m1 = output_dir / 'prices_m1_09sept_verification.csv'
    df_m1_export = df_m1_all[['datetime_bern', 'open', 'high', 'low', 'close', 'volume']].copy()
    df_m1_export['datetime_bern'] = df_m1_export['datetime_bern'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_m1_export.to_csv(csv_m1, index=False)
    print(f'✅ M1 sauvegardé : {csv_m1}')
    
    # CSV H1
    csv_h1 = output_dir / 'prices_h1_09sept_verification.csv'
    df_h1_export = df_h1[['datetime_bern', 'open', 'high', 'low', 'close', 'volume']].copy()
    df_h1_export['datetime_bern'] = df_h1_export['datetime_bern'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_h1_export.to_csv(csv_h1, index=False)
    print(f'✅ H1 sauvegardé : {csv_h1}')
    
    print()
    print('='*80)
    print('RÉSUMÉ H1 (09.09.2025 05:00-10:00)')
    print('='*80)
    df_h1_around = df_h1[(df_h1['datetime_bern'] >= tz_bern.localize(datetime(2025, 9, 9, 5, 0))) &
                         (df_h1['datetime_bern'] <= tz_bern.localize(datetime(2025, 9, 9, 10, 0)))]
    
    for _, row in df_h1_around.iterrows():
        dt_bern = row['datetime_bern']
        marker = ''
        if dt_bern.hour == 6 and abs(row['high'] - 1.17748) < 0.0001:
            marker = ' ✅ CORRECT'
        elif dt_bern.hour == 8 and abs(row['high'] - 1.17791) < 0.0001:
            marker = ' ✅ CORRECT (PIC)'
        elif dt_bern.hour == 8:
            marker = f' ❌ ATTENDU 1.17791, TROUVÉ {row["high"]:.5f}'
        print(f'  {dt_bern.strftime("%H:%M")} : high={row["high"]:.5f}, close={row["close"]:.5f}{marker}')

if __name__ == '__main__':
    main()


