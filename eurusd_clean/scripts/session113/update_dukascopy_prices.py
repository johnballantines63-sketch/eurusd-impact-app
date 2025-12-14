"""
MISE À JOUR PRIX DUKASCOPY - Session 113
=========================================

Import incrémental : seulement depuis la dernière date en DB.

SÉCURITÉ:
- Détecte automatiquement dernière date
- Importe seulement ce qui manque
- Gère timezone UTC → Bern +02:00

Session 113 - André Valentin
"""
import sys
from pathlib import Path
import lzma
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import DB_PATH

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
    tv = df.groupby("minute")["bid"].size()
    
    out = pd.DataFrame({
        "time": o.index,
        "open": o.values,
        "high": h.values,
        "low": l.values,
        "close": c.values,
        "volume": tv.values.astype(int),
    })
    return out.sort_values("time").reset_index(drop=True)

def daterange_hours(start_utc: datetime, end_utc: datetime):
    """Générateur d'heures UTC."""
    t = start_utc.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    while t < end_utc:
        yield t
        t += timedelta(hours=1)

print("=" * 80)
print("MISE À JOUR PRIX DUKASCOPY")
print("=" * 80)

conn = duckdb.connect(str(DB_PATH))

# Détecter dernière date en DB
last_date = conn.execute("""
    SELECT MAX(datetime) FROM prices_1m
""").fetchone()[0]

if last_date is None:
    print("\n❌ Table prices_1m vide !")
    print("   Utiliser import_dukascopy_UTC_fixed_session25.py pour import complet")
    conn.close()
    sys.exit(1)

print(f"\n📊 État actuel:")
print(f"   Dernière date en DB: {last_date}")

# Calculer période à importer
# Convertir last_date en datetime UTC
if isinstance(last_date, str):
    last_dt = pd.to_datetime(last_date, utc=True)
else:
    last_dt = pd.Timestamp(last_date).tz_convert('UTC')

# Commencer 1 heure après dernière date (sécurité)
start_utc = (last_dt + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
end_utc = datetime.now(timezone.utc)

days_to_import = (end_utc - start_utc).days + 1

print(f"   Période manquante: {start_utc.date()} → {end_utc.date()}")
print(f"   Jours à importer: {days_to_import}")

if days_to_import <= 0:
    print("\n✅ Données à jour !")
    conn.close()
    sys.exit(0)

response = input("\nConfirmer l'import ? (oui/non): ")
if response.lower() != 'oui':
    print("❌ Annulé")
    conn.close()
    sys.exit(1)

# Import
print(f"\n🚀 Import en cours...")
print("-" * 80)

all_m1 = []
hours = list(daterange_hours(start_utc, end_utc))
total_hours = len(hours)

for i, h_utc in enumerate(hours, 1):
    df_ticks = fetch_hour_ticks(SYMBOL, h_utc)
    if df_ticks is None:
        continue
    
    df_m1 = aggregate_to_m1(df_ticks)
    if not df_m1.empty:
        all_m1.append(df_m1)
    
    if i % 50 == 0:
        progress = (i / total_hours) * 100
        print(f"  [{i:4d}/{total_hours:4d}] {progress:5.1f}% - {h_utc.date()}")

if not all_m1:
    print("\n⚠️  Aucune donnée téléchargée (weekend ?)")
    conn.close()
    sys.exit(0)

df = pd.concat(all_m1, ignore_index=True)
df = df.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)

print(f"\n✅ Téléchargement terminé: {len(df):,} nouvelles lignes")

# Convertir pour DuckDB (garder en UTC avec timezone info)
df_insert = df.copy()
# Garder en UTC (ne pas convertir en Europe/Zurich)
# Les données sont déjà en UTC depuis fetch_hour_ticks
df_insert["datetime"] = df_insert["time"]  # Déjà en UTC avec timezone
df_insert = df_insert[["datetime", "open", "high", "low", "close", "volume"]]

# Compter avant
n_before = conn.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]

# Insérer (anti-doublon)
conn.register("new_prices", df_insert)
conn.execute("""
    INSERT INTO prices_1m (datetime, open, high, low, close, volume)
    SELECT n.datetime, n.open, n.high, n.low, n.close, n.volume
    FROM new_prices n
    WHERE NOT EXISTS (
        SELECT 1 FROM prices_1m p
        WHERE p.datetime = n.datetime
    )
""")
conn.unregister("new_prices")

# Compter après
n_after = conn.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
n_inserted = n_after - n_before

# Stats finales
stats = conn.execute("""
    SELECT 
        COUNT(*) as total,
        MIN(datetime) as min_date,
        MAX(datetime) as max_date
    FROM prices_1m
""").fetchone()

conn.close()

print("\n" + "=" * 80)
print("MISE À JOUR TERMINÉE")
print("=" * 80)

print(f"\n📊 RÉSULTATS:")
print(f"   Lignes téléchargées: {len(df):,}")
print(f"   Lignes insérées: {n_inserted:,}")
print(f"   Total en DB: {stats[0]:,}")
print(f"   Plage: {stats[1]} → {stats[2]}")

print("\n✅ Prix à jour !")
print("\n🚀 PROCHAINE ÉTAPE:")
print("   python scripts/session113/calculate_empirical_scores.py")

print("=" * 80)
