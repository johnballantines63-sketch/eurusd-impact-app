#!/usr/bin/env python3
"""
Vérification : Direction Mouvement 2025-04-10

Objectif : Vérifier la direction du mouvement (UP ou DOWN)
Le graphique montre une chute (DOWN) à 14:30

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
import pytz
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

date_str = '2025-04-10'

print("="*100)
print(f"VÉRIFICATION : DIRECTION MOUVEMENT {date_str}")
print("="*100)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Charger prix autour de 14:00-16:00
query_prices = f"""
SELECT datetime, open, high, low, close
FROM prices_finnhub_m1
WHERE DATE(datetime) = '{date_str}'
  AND datetime >= '{date_str} 13:00:00'
  AND datetime <= '{date_str} 16:00:00'
ORDER BY datetime ASC
"""

df_prices = conn.execute(query_prices).df()
conn.close()

if df_prices.empty:
    print("❌ Aucune donnée")
    exit(1)

df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
df_prices = df_prices.set_index('datetime')

# Baseline : 14:00
baseline_time = TZ_BERN.localize(
    datetime.combine(pd.to_datetime(date_str).date(), datetime.min.time().replace(hour=14, minute=0))
)

prices_at_baseline = df_prices[df_prices.index >= baseline_time]

if prices_at_baseline.empty:
    print("❌ Pas de données après 14:00")
    exit(1)

baseline_price = prices_at_baseline.iloc[0]['open']

print(f"Baseline : {baseline_time.strftime('%H:%M')} @ {baseline_price:.5f}")
print()

# Analyser mouvement
max_high = prices_at_baseline['high'].max()
min_low = prices_at_baseline['low'].min()

impact_up = (max_high - baseline_price) * 10000
impact_down = (baseline_price - min_low) * 10000
impact_max = max(impact_up, impact_down)

print(f"Max High : {max_high:.5f} → Impact UP : {impact_up:.2f} pips")
print(f"Min Low : {min_low:.5f} → Impact DOWN : {impact_down:.2f} pips")
print(f"Impact MAX : {impact_max:.2f} pips")
print()

if impact_down > impact_up:
    print("✅ Direction : DOWN (chute)")
    low_time = prices_at_baseline[prices_at_baseline['low'] == min_low].index[0]
    print(f"Pic DOWN à : {low_time.strftime('%H:%M')}")
    
    # Trouver début du mouvement DOWN
    threshold_pips = impact_down * 0.30
    
    print()
    print(f"Seuil début (30% de {impact_down:.1f} pips) : {threshold_pips:.1f} pips")
    print()
    
    # Analyser bougies avant le pic
    df_before = prices_at_baseline[prices_at_baseline.index <= low_time]
    
    print("Bougies avant pic (remontée depuis pic) :")
    print(f"{'Heure':<8} {'Low':<12} {'Mvt DOWN':<12} {'< Seuil ?':<10}")
    print("-"*50)
    
    movement_start = None
    
    for idx in reversed(df_before.index):
        row = df_before.loc[idx]
        current_pips = (baseline_price - row['low']) * 10000
        below_threshold = current_pips < threshold_pips
        
        if below_threshold and movement_start is None:
            movement_start = idx
            marker = "✅ DÉBUT"
        else:
            marker = ""
        
        print(f"{idx.strftime('%H:%M'):<8} {row['low']:>11.5f} {current_pips:>11.2f} {'OUI' if below_threshold else 'NON':<10} {marker}")
    
    if movement_start:
        print()
        print(f"✅ Début mouvement DOWN détecté : {movement_start.strftime('%H:%M')}")
else:
    print("Direction : UP (hausse)")

print()

