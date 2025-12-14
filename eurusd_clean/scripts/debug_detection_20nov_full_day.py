"""
Debug : Vérifier TOUTES les données de prix pour le 20.11.2025
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
print("🔍 DEBUG : TOUTES LES DONNÉES DE PRIX - 20.11.2025")
print("=" * 80)
print()

# Date cible
target_date = datetime(2025, 11, 20)
timezone_str = 'Europe/Zurich'

# Charger TOUS les prix de la journée
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
ORDER BY datetime
"""

df_prices = conn.execute(query_prices, [target_date.strftime('%Y-%m-%d')]).df()

if df_prices.empty:
    print("❌ Aucun prix trouvé pour cette date")
    conn.close()
    sys.exit(1)

# Convertir en datetime avec timezone
df_prices['datetime'] = pd.to_datetime(df_prices['ts'])
if df_prices['datetime'].dt.tz is None:
    df_prices['datetime'] = df_prices['datetime'].dt.tz_localize('UTC').dt.tz_convert(timezone_str)
else:
    df_prices['datetime'] = df_prices['datetime'].dt.tz_convert(timezone_str)

df_prices = df_prices.set_index('datetime')

print(f"✅ {len(df_prices)} bougies de prix chargées pour toute la journée")
print(f"   Période : {df_prices.index.min()} à {df_prices.index.max()}")
print()

# Chercher tous les mouvements explosifs (>= 15 pips en 1 minute)
print("1️⃣ TOUS LES MOUVEMENTS EXPLOSIFS (>= 15 pips en 1 minute)")
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
    print()

# Chercher les plus grands mouvements (top 10)
print("2️⃣ TOP 10 DES PLUS GRANDS MOUVEMENTS (par range)")
print("-" * 80)

df_prices['range_pips'] = (df_prices['high'] - df_prices['low']) * 10000
top_ranges = df_prices.nlargest(10, 'range_pips')

for idx, row in top_ranges.iterrows():
    print(f"   {idx.strftime('%H:%M')} : {row['range_pips']:.1f} pips")
    print(f"      Open: {row['open']:.5f}, High: {row['high']:.5f}, Low: {row['low']:.5f}, Close: {row['close']:.5f}")

print()

# Vérifier le mouvement à 16:00
print("3️⃣ VÉRIFICATION MOUVEMENT À 16:00")
print("-" * 80)

idx_1600 = None
for i, ts in enumerate(df_prices.index):
    if ts.hour == 16 and ts.minute == 0:
        idx_1600 = i
        break

if idx_1600 is not None:
    print(f"   ✅ Bougie à 16:00 trouvée (index {idx_1600})")
    candle_1600 = df_prices.iloc[idx_1600]
    print(f"      Open: {candle_1600['open']:.5f}, High: {candle_1600['high']:.5f}, Low: {candle_1600['low']:.5f}, Close: {candle_1600['close']:.5f}")
    print(f"      Range: {candle_1600['range_pips']:.1f} pips")
    print()
    
    # Analyser le mouvement progressif depuis 16:00
    baseline_price_1600 = candle_1600['low']
    
    for window_minutes in [5, 10, 15, 20, 30, 60]:
        end_idx = min(idx_1600 + window_minutes, len(df_prices) - 1)
        segment = df_prices.iloc[idx_1600:end_idx + 1]
        
        peak_price = segment['high'].max()
        peak_time = segment['high'].idxmax()
        
        impact_pips = (peak_price - baseline_price_1600) * 10000
        
        print(f"   📊 Fenêtre {window_minutes} minutes (16:00 → {segment.index[-1].strftime('%H:%M')}) :")
        print(f"      Baseline (16:00 low): {baseline_price_1600:.5f}")
        print(f"      Pic: {peak_price:.5f} à {peak_time.strftime('%H:%M')}")
        print(f"      Impact: {impact_pips:.1f} pips")
        print()
else:
    print("   ⚠️  Pas de bougie à 16:00")
    print("   → Vérifier si les données sont complètes")
    print()

# Vérifier les données autour de 14:29 en détail
print("4️⃣ DÉTAIL DES BOUGIES AUTOUR DE 14:29")
print("-" * 80)

candles_1429 = df_prices[
    (df_prices.index.hour == 14) & 
    (df_prices.index.minute >= 25) &
    (df_prices.index.minute <= 35)
]

if not candles_1429.empty:
    print(f"   ✅ {len(candles_1429)} bougie(s) autour de 14:29 trouvée(s)")
    print()
    for idx, candle in candles_1429.iterrows():
        print(f"   {idx.strftime('%H:%M')} : Range = {candle['range_pips']:.1f} pips")
        print(f"      Open: {candle['open']:.5f}, High: {candle['high']:.5f}, Low: {candle['low']:.5f}, Close: {candle['close']:.5f}")
        print(f"      Change: {(candle['close'] - candle['open']) * 10000:+.1f} pips")
        print()
else:
    print("   ❌ Aucune bougie autour de 14:29 trouvée")
    print()

conn.close()

print("=" * 80)
print("✅ DEBUG TERMINÉ")
print("=" * 80)
print()
print("💡 CONCLUSION :")
print("   Si aucun mouvement explosif n'est trouvé à 14:29, il y a deux possibilités :")
print("   1. Les données dans la DB ne sont pas à jour ou incorrectes")
print("   2. Le mouvement visible sur MT5 est sur plusieurs bougies (progressif)")
print("   3. Le mouvement à 14:29 sur MT5 est peut-être sur une autre date")
print()


