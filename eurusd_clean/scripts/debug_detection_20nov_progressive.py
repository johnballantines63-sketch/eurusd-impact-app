"""
Debug : Vérifier les mouvements progressifs autour de 14:29
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
print("🔍 DEBUG : MOUVEMENTS PROGRESSIFS AUTOUR DE 14:29 - 20.11.2025")
print("=" * 80)
print()

# Date cible
target_date = datetime(2025, 11, 20)
timezone_str = 'Europe/Zurich'

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

# Convertir en datetime avec timezone
df_prices['datetime'] = pd.to_datetime(df_prices['ts'])
if df_prices['datetime'].dt.tz is None:
    df_prices['datetime'] = df_prices['datetime'].dt.tz_localize('UTC').dt.tz_convert(timezone_str)
else:
    df_prices['datetime'] = df_prices['datetime'].dt.tz_convert(timezone_str)

df_prices = df_prices.set_index('datetime')

print(f"✅ {len(df_prices)} bougies de prix chargées (14h-16h)")
print()

# Chercher le mouvement progressif à partir de 14:29
print("1️⃣ MOUVEMENT PROGRESSIF À PARTIR DE 14:29")
print("-" * 80)

# Trouver l'index de 14:29
idx_1429 = None
for i, ts in enumerate(df_prices.index):
    if ts.hour == 14 and ts.minute == 29:
        idx_1429 = i
        break

if idx_1429 is None:
    print("   ❌ Bougie à 14:29 non trouvée")
    conn.close()
    sys.exit(1)

print(f"   📍 Index de 14:29 : {idx_1429}")
print()

# Analyser les mouvements progressifs sur différentes fenêtres
windows = [5, 10, 15, 20, 30, 60]  # minutes

for window_minutes in windows:
    end_idx = min(idx_1429 + window_minutes, len(df_prices) - 1)
    
    segment = df_prices.iloc[idx_1429:end_idx + 1]
    
    baseline_price = df_prices.iloc[idx_1429]['low']  # Utiliser le low de 14:29 comme baseline
    peak_price = segment['high'].max()
    peak_time = segment['high'].idxmax()
    
    impact_pips = (peak_price - baseline_price) * 10000
    
    print(f"   📊 Fenêtre {window_minutes} minutes (14:29 → {segment.index[-1].strftime('%H:%M')}) :")
    print(f"      Baseline (14:29 low): {baseline_price:.5f}")
    print(f"      Pic: {peak_price:.5f} à {peak_time.strftime('%H:%M')}")
    print(f"      Impact: {impact_pips:.1f} pips")
    print()

# Vérifier aussi le mouvement depuis 14:28 (une minute avant)
print("2️⃣ MOUVEMENT PROGRESSIF À PARTIR DE 14:28")
print("-" * 80)

idx_1428 = idx_1429 - 1
if idx_1428 >= 0:
    baseline_price_1428 = df_prices.iloc[idx_1428]['low']
    
    for window_minutes in [5, 10, 15, 20, 30, 60]:
        end_idx = min(idx_1428 + window_minutes, len(df_prices) - 1)
        
        segment = df_prices.iloc[idx_1428:end_idx + 1]
        
        peak_price = segment['high'].max()
        peak_time = segment['high'].idxmax()
        
        impact_pips = (peak_price - baseline_price_1428) * 10000
        
        print(f"   📊 Fenêtre {window_minutes} minutes (14:28 → {segment.index[-1].strftime('%H:%M')}) :")
        print(f"      Baseline (14:28 low): {baseline_price_1428:.5f}")
        print(f"      Pic: {peak_price:.5f} à {peak_time.strftime('%H:%M')}")
        print(f"      Impact: {impact_pips:.1f} pips")
        print()

# Vérifier le mouvement depuis 14:30 (heure du cluster)
print("3️⃣ MOUVEMENT PROGRESSIF À PARTIR DE 14:30 (HEURE DU CLUSTER)")
print("-" * 80)

idx_1430 = idx_1429 + 1
if idx_1430 < len(df_prices):
    baseline_price_1430 = df_prices.iloc[idx_1430]['low']
    
    for window_minutes in [5, 10, 15, 20, 30, 60]:
        end_idx = min(idx_1430 + window_minutes, len(df_prices) - 1)
        
        segment = df_prices.iloc[idx_1430:end_idx + 1]
        
        peak_price = segment['high'].max()
        peak_time = segment['high'].idxmax()
        
        impact_pips = (peak_price - baseline_price_1430) * 10000
        
        print(f"   📊 Fenêtre {window_minutes} minutes (14:30 → {segment.index[-1].strftime('%H:%M')}) :")
        print(f"      Baseline (14:30 low): {baseline_price_1430:.5f}")
        print(f"      Pic: {peak_price:.5f} à {peak_time.strftime('%H:%M')}")
        print(f"      Impact: {impact_pips:.1f} pips")
        print()

# Vérifier le mouvement détecté à 16:00
print("4️⃣ VÉRIFICATION MOUVEMENT À 16:00")
print("-" * 80)

idx_1600 = None
for i, ts in enumerate(df_prices.index):
    if ts.hour == 16 and ts.minute == 0:
        idx_1600 = i
        break

if idx_1600 is not None:
    baseline_price_1600 = df_prices.iloc[idx_1600]['low']
    
    # Analyser sur 30 minutes
    end_idx = min(idx_1600 + 30, len(df_prices) - 1)
    segment = df_prices.iloc[idx_1600:end_idx + 1]
    
    peak_price = segment['high'].max()
    peak_time = segment['high'].idxmax()
    
    impact_pips = (peak_price - baseline_price_1600) * 10000
    
    print(f"   📊 Mouvement à 16:00 (30 minutes) :")
    print(f"      Baseline (16:00 low): {baseline_price_1600:.5f}")
    print(f"      Pic: {peak_price:.5f} à {peak_time.strftime('%H:%M')}")
    print(f"      Impact: {impact_pips:.1f} pips")
    print()
else:
    print("   ⚠️  Pas de bougie à 16:00 dans cette période")
    print()

conn.close()

print("=" * 80)
print("✅ DEBUG TERMINÉ")
print("=" * 80)


