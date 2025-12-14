#!/usr/bin/env python3
"""
Analyse 12:30 UTC (= 14:30 CEST Berne) sur HistData MT
"""

import pandas as pd

csv_file = "HISTDATA_COM_MT_EURUSD_M1202509/DAT_MT_EURUSD_M1_202509.csv"

print("🔍 Analyse 12:30 UTC (14:30 heure de Berne)")
print("=" * 80)

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

# Phase 1: 12:30-12:45 UTC (= 14:30-14:45 Berne)
phase1 = df[
    (df['datetime'] >= '2025-09-11 12:30:00') &
    (df['datetime'] < '2025-09-11 12:45:00')
]

if phase1.empty:
    print("❌ Aucune donnée pour 12:30 UTC")
else:
    print(f"\n📊 PHASE 1 (12:30-12:45 UTC = 14:30-14:45 CEST Berne):")
    print(f"   Lignes: {len(phase1)}")
    
    print(f"\n   📋 Détail minute par minute:")
    for idx, row in phase1.iterrows():
        utc_time = row['datetime'].strftime('%H:%M')
        berne_hour = (row['datetime'].hour + 2) % 24
        berne_min = row['datetime'].minute
        berne_time = f"{berne_hour:02d}:{berne_min:02d}"
        print(f"      {utc_time} UTC ({berne_time} Berne) | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f}")
    
    # Calculer mouvement
    start_price = phase1.iloc[0]['close']
    high_price = phase1['high'].max()
    low_price = phase1['low'].min()
    
    move_up = (high_price - start_price) * 10000
    move_down = (start_price - low_price) * 10000
    phase1_pips = max(move_up, move_down)
    
    print(f"\n   💰 Calcul mouvement:")
    print(f"      Prix départ: {start_price:.5f}")
    print(f"      Prix HIGH: {high_price:.5f}")
    print(f"      Prix LOW: {low_price:.5f}")
    print(f"      Mouvement UP: {move_up:.2f} pips")
    print(f"      Mouvement DOWN: {move_down:.2f} pips")
    print(f"      ➡️ PHASE 1: {phase1_pips:.2f} pips")
    
    print(f"\n   🎯 Comparaison:")
    print(f"      Attendu (graphiques André): ~56-67 pips")
    print(f"      Obtenu (HistData 12:30 UTC): {phase1_pips:.2f} pips")
    
    if 40 <= phase1_pips <= 80:
        print(f"\n      ✅ ✅ ✅ TROUVÉ ! C'EST LE BON MOMENT ! ✅ ✅ ✅")
    else:
        print(f"\n      ❌ Toujours pas le bon mouvement")

# Regarder aussi 15:10 Berne = 13:10 UTC
print(f"\n" + "=" * 80)
print(f"📊 Prix à 13:10 UTC (15:10 Berne):")

price_1510 = df[df['datetime'] == '2025-09-11 13:10:00']
if not price_1510.empty:
    row = price_1510.iloc[0]
    print(f"   {row['datetime']} | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f}")
    print(f"\n   Attendu selon André: ~1.17378")
    print(f"   Obtenu HistData: {row['close']:.5f}")
else:
    print("   Données non disponibles")

# Mouvement total 12:30 → 13:10 (40 minutes)
print(f"\n" + "=" * 80)
print(f"📊 MOUVEMENT TOTAL 12:30 → 13:10 UTC (14:30 → 15:10 Berne):")

window_40min = df[
    (df['datetime'] >= '2025-09-11 12:30:00') &
    (df['datetime'] <= '2025-09-11 13:10:00')
]

if not window_40min.empty:
    start = window_40min.iloc[0]['close']
    end = window_40min.iloc[-1]['close']
    high_40 = window_40min['high'].max()
    low_40 = window_40min['low'].min()
    
    total_movement = max(
        (high_40 - start) * 10000,
        (start - low_40) * 10000
    )
    
    print(f"   Prix 12:30 (14:30 Berne): {start:.5f}")
    print(f"   Prix 13:10 (15:10 Berne): {end:.5f}")
    print(f"   Mouvement total: {total_movement:.2f} pips")
    print(f"\n   Attendu selon André: ~56-67 pips")
    
    if 50 <= total_movement <= 70:
        print(f"   ✅ ✅ ✅ PARFAIT ! ON A TROUVÉ ! ✅ ✅ ✅")
    else:
        print(f"   Écart: {abs(total_movement - 56):.2f} pips")
