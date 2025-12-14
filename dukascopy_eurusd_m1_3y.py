import os
import io
import lzma
import struct
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

# -------------------- PARAMÈTRES --------------------
SYMBOL = "EURUSD"       # format Dukascopy: ex. "EURUSD", "GBPUSD"
YEARS  = 3              # profondeur historique
OUT_CSV = f"{SYMBOL}_M1_last{YEARS}y_dukascopy.csv"

# Timeout & retry réseau
HTTP_TIMEOUT = 20
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
    for _ in range(MAX_RETRIES):
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
    # Optionnel: log si nécessaire
    print(f"[WARN] Échec {url}: {last_err}")
    return None

def aggregate_to_m1(df_ticks: pd.DataFrame) -> pd.DataFrame:
    """Agrège des ticks BID/ASK en bougies M1 (BID OHLC + spread moyen en points)."""
    if df_ticks is None or df_ticks.empty:
        return pd.DataFrame()

    df = df_ticks.copy()
    df["minute"] = df["time"].dt.floor("T")  # floor à la minute

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
        "TickVolume": tv.values.astype(int),
        "Spread": spr.values.round(2),
    })
    out = out.sort_values("time").reset_index(drop=True)
    return out

def daterange_hours(start_utc: datetime, end_utc: datetime):
    t = start_utc.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    while t < end_utc:
        yield t
        t += timedelta(hours=1)

def main():
    end_utc = datetime.now(timezone.utc)
    start_utc = end_utc - timedelta(days=int(365.25 * YEARS))

    all_m1 = []

    print(f"⏬ Téléchargement ticks {SYMBOL} de {start_utc:%Y-%m-%d} à {end_utc:%Y-%m-%d} (UTC) ...")
    hours = list(daterange_hours(start_utc, end_utc))

    for i, h_utc in enumerate(hours, 1):
        df_ticks = fetch_hour_ticks(SYMBOL, h_utc)
        if df_ticks is None:
            continue
        df_m1 = aggregate_to_m1(df_ticks)
        if not df_m1.empty:
            all_m1.append(df_m1)

        # petit état d’avancement
        if i % 200 == 0:
            print(f"  • {i}/{len(hours)} heures traitées...")

    if not all_m1:
        raise RuntimeError("Aucune minute générée — possible absence de données ou problème réseau.")

    df = pd.concat(all_m1, ignore_index=True)
    df = df.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)

    # colonnes au format demandé
    df["Date"] = df["time"].dt.strftime("%Y.%m.%d")
    df["Time"] = df["time"].dt.strftime("%H:%M:%S")
    out = df[["Date","Time","open","high","low","close","TickVolume","Spread"]]

    out.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"✅ Terminé : {len(out):,} lignes écrites dans {OUT_CSV}")

if __name__ == "__main__":
    main()
