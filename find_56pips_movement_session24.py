#!/usr/bin/env python3
"""
Trouver le vrai mouvement de 56 pips dans les données HistData
"""

import pandas as pd
import sys

csv_file = "HISTDATA_COM_MT_EURUSD_M1202509/DAT_MT_EURUSD_M1_202509.csv"

print("🔍 Recherche du mouvement de 56 pips dans HistData MT...")

# Lire le CSV
df = pd.read_csv(csv_file, 
                sep=',',
                names=['date', 'time', 'open', 'high', 'low', 'close', 'volume'],
                header=None)

df['datetime_str'] = df['date'] + ' ' + df['time']
df['datetime'] = pd.to_datetime(df['datetime_str'], format='%Y.%m.%d %H:%M', utc=True)
df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']].copy()

for col in ['open', 'high', 'low', 'close', 'volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Filtrer 11 septembre
sept11 = df[df['datetime'].dt.date == pd.to_datetime('2025-09-11').date()].copy()

print(f"\n📊 11 septembre : {len(sept11)} lignes")
print(f"   Période: {sept11.iloc[0]['datetime']} → {sept11.iloc[-1]['datetime']}")

# Chercher le prix 1.16816
target_price = 1.16816
tolerance = 0.00005

print(f"\n🎯 Recherche du prix {target_price} (±{tolerance})...")

matches = sept11[
    (sept11['close'].between(target_price - tolerance, target_price + tolerance)) |
    (sept11['open'].between(target_price - tolerance, target_price + tolerance)) |
    (sept11['high'].between(target_price - tolerance, target_price + tolerance)) |
    (sept11['low'].between(target_price - tolerance, target_price + tolerance))
]

if not matches.empty:
    print(f"\n✅ Prix trouvé à {len(matches)} moments:")
    for idx, row in matches.head(10).iterrows():
        print(f"   {row['datetime']} | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f}")
else:
    print(f"\n❌ Prix {target_price} introuvable")
    print(f"\n📊 Échantillon de prix autour de 14:30-15:30:")
    sample = sept11[
        (sept11['datetime'] >= '2025-09-11 14:00:00') &
        (sept11['datetime'] <= '2025-09-11 16:00:00')
    ]
    for idx, row in sample.head(20).iterrows():
        print(f"   {row['datetime']} | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f}")

# Scanner tous les mouvements de 15 minutes pour trouver ~56 pips
print(f"\n🔍 Scan de tous les mouvements 15min pour trouver ~50-70 pips...")

max_movement = 0
max_period = None
max_details = None

for i in range(len(sept11) - 14):
    window = sept11.iloc[i:i+15]
    
    start_price = window.iloc[0]['close']
    high_price = window['high'].max()
    low_price = window['low'].min()
    
    move_up = (high_price - start_price) * 10000
    move_down = (start_price - low_price) * 10000
    movement = max(move_up, move_down)
    
    if movement > max_movement:
        max_movement = movement
        max_period = window.iloc[0]['datetime']
        max_details = {
            'start': start_price,
            'high': high_price,
            'low': low_price,
            'move_up': move_up,
            'move_down': move_down
        }

print(f"\n🎯 PLUS GRAND MOUVEMENT 15min sur le 11 septembre:")
print(f"   Début: {max_period}")
print(f"   Mouvement: {max_movement:.2f} pips")
print(f"   Prix départ: {max_details['start']:.5f}")
print(f"   HIGH: {max_details['high']:.5f}")
print(f"   LOW: {max_details['low']:.5f}")

if 50 <= max_movement <= 70:
    print(f"\n   ✅ TROUVÉ! C'est peut-être le bon mouvement!")
else:
    print(f"\n   ⚠️ Même le plus grand mouvement ({max_movement:.2f} pips) est loin de 56 pips")

# Chercher aussi des mouvements sur 30-40 minutes
print(f"\n🔍 Scan des mouvements 30min (au cas où)...")

max_movement_30 = 0
max_period_30 = None

for i in range(len(sept11) - 29):
    window = sept11.iloc[i:i+30]
    
    start_price = window.iloc[0]['close']
    high_price = window['high'].max()
    low_price = window['low'].min()
    
    movement = max((high_price - start_price) * 10000, (start_price - low_price) * 10000)
    
    if movement > max_movement_30:
        max_movement_30 = movement
        max_period_30 = window.iloc[0]['datetime']

print(f"\n🎯 PLUS GRAND MOUVEMENT 30min:")
print(f"   Début: {max_period_30}")
print(f"   Mouvement: {max_movement_30:.2f} pips")
