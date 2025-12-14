"""
Debug simple : Vérifier les prix autour de 14:29 pour le 20.11.2025
==========================================================================
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'

print("=" * 80)
print("🔍 DEBUG SIMPLE : PRIX AUTOUR DE 14:29 - 20.11.2025")
print("=" * 80)
print()

# Date cible
target_date = datetime(2025, 11, 20)
timezone_str = 'Europe/Zurich'

print(f"📅 Date analysée : {target_date.strftime('%Y-%m-%d')}")
print()

# Charger les prix
conn = duckdb.connect(str(DB_PATH), read_only=True)

query_prices = """
SELECT 
    datetime as ts,
    open,
    high,
    low,
    close
FROM prices_bern
WHERE DATE(datetime) = ?
  AND EXTRACT(HOUR FROM datetime) >= 14
  AND EXTRACT(HOUR FROM datetime) < 16
ORDER BY datetime
"""

df_prices = conn.execute(query_prices, [target_date.strftime('%Y-%m-%d')]).df()

if df_prices.empty:
    print("❌ Aucun prix trouvé pour cette période")
    conn.close()
    sys.exit(1)

# Convertir en datetime avec timezone
df_prices['datetime'] = pd.to_datetime(df_prices['ts'])
if df_prices['datetime'].dt.tz is None:
    df_prices['datetime'] = df_prices['datetime'].dt.tz_localize('UTC').dt.tz_convert(timezone_str)
else:
    df_prices['datetime'] = df_prices['datetime'].dt.tz_convert(timezone_str)

df_prices = df_prices.set_index('datetime')

print(f"✅ {len(df_prices)} bougies de prix chargées (14h-16h)")
print(f"   Période : {df_prices.index.min()} à {df_prices.index.max()}")
print()

# Vérifier le mouvement explosif à 14:29
print("1️⃣ VÉRIFICATION MOUVEMENT EXPLOSIF À 14:29")
print("-" * 80)

# Chercher les bougies autour de 14:29
candles_1429 = df_prices[
    (df_prices.index.hour == 14) & 
    (df_prices.index.minute >= 28) &
    (df_prices.index.minute <= 30)
]

if not candles_1429.empty:
    print(f"   ✅ {len(candles_1429)} bougie(s) autour de 14:29 trouvée(s)")
    print()
    
    for idx, candle in candles_1429.iterrows():
        candle_range = (candle['high'] - candle['low']) * 10000
        candle_change = (candle['close'] - candle['open']) * 10000
        
        print(f"   📊 Bougie {idx.strftime('%H:%M')} :")
        print(f"      Open: {candle['open']:.5f}")
        print(f"      High: {candle['high']:.5f}")
        print(f"      Low: {candle['low']:.5f}")
        print(f"      Close: {candle['close']:.5f}")
        print(f"      Range: {candle_range:.1f} pips")
        print(f"      Change: {candle_change:+.1f} pips")
        
        if candle_range >= 15.0:
            print(f"      ✅ MOUVEMENT EXPLOSIF DÉTECTÉ ({candle_range:.1f} pips >= 15)")
            
            # Calculer le mouvement depuis la bougie précédente
            prev_idx = df_prices.index.get_loc(idx) - 1
            if prev_idx >= 0:
                prev_candle = df_prices.iloc[prev_idx]
                if candle['close'] > prev_candle['close']:
                    direction = 'UP'
                    baseline = prev_candle['low']
                    peak = candle['high']
                    impact = (peak - baseline) * 10000
                else:
                    direction = 'DOWN'
                    baseline = prev_candle['high']
                    peak = candle['low']
                    impact = (baseline - peak) * 10000
                
                print(f"      Direction: {direction}")
                print(f"      Baseline (bougie précédente): {baseline:.5f}")
                print(f"      Impact depuis baseline: {impact:.1f} pips")
        else:
            print(f"      ⚠️  Mouvement trop faible ({candle_range:.1f} pips < 15)")
        print()
else:
    print("   ❌ Aucune bougie à 14:29 trouvée")
    print("   → Vérifier les données de prix dans la DB")
    print()

# Vérifier toutes les bougies avec mouvement >= 15 pips
print("2️⃣ TOUS LES MOUVEMENTS EXPLOSIFS (>= 15 pips en 1 minute)")
print("-" * 80)

explosive_candles = []
for i in range(len(df_prices)):
    candle = df_prices.iloc[i]
    candle_range = (candle['high'] - candle['low']) * 10000
    
    if candle_range >= 15.0:
        explosive_candles.append({
            'time': df_prices.index[i],
            'range': candle_range,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close']
        })

if explosive_candles:
    print(f"   ✅ {len(explosive_candles)} bougie(s) explosive(s) trouvée(s)")
    print()
    for candle in explosive_candles:
        print(f"   💥 {candle['time'].strftime('%H:%M')} : {candle['range']:.1f} pips")
        print(f"      Open: {candle['open']:.5f}, High: {candle['high']:.5f}, Low: {candle['low']:.5f}, Close: {candle['close']:.5f}")
else:
    print("   ❌ Aucune bougie explosive trouvée (>= 15 pips)")
    print("   → Le mouvement à 14:29 n'est peut-être pas assez fort")
    print()

# Vérifier les événements
print("3️⃣ ÉVÉNEMENTS AUTOUR DE 14H-16H")
print("-" * 80)

query_events = """
SELECT 
    datetime_utc as ts_utc,
    event_name as event_key,
    country
FROM economic_events
WHERE DATE(datetime_utc) = ?
  AND country IN ('US', 'DE', 'EU')
ORDER BY datetime_utc
"""

df_events = conn.execute(query_events, [target_date.strftime('%Y-%m-%d')]).df()

if not df_events.empty:
    df_events['ts_bern'] = pd.to_datetime(df_events['ts_utc']).dt.tz_localize('UTC').dt.tz_convert(timezone_str)
    
    events_cluster = df_events[
        (df_events['ts_bern'].dt.hour >= 14) & 
        (df_events['ts_bern'].dt.hour < 16)
    ]
    
    print(f"   ✅ {len(events_cluster)} événement(s) autour de 14h-16h")
    print()
    
    if not events_cluster.empty:
        print("   Événements :")
        for idx, event in events_cluster.iterrows():
            print(f"      {event['ts_bern'].strftime('%H:%M')} | {event['country']:2s} | {event['event_key']}")
        
        cluster_anchor_time = events_cluster['ts_bern'].min()
        print()
        print(f"   📍 Heure du cluster (premier événement) : {cluster_anchor_time.strftime('%H:%M')}")
    else:
        print("   ⚠️  Aucun événement trouvé autour de 14h-16h")
else:
    print("   ❌ Aucun événement trouvé pour cette date")

conn.close()

print()
print("=" * 80)
print("✅ DEBUG TERMINÉ")
print("=" * 80)


