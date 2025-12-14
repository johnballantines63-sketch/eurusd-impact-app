#!/usr/bin/env python3
"""
Vérification : Détection Début Mouvement 2025-04-10

Objectif : Vérifier si la détection du début du mouvement est correcte
Le graphique montre un mouvement fort à 14:30, pas à 15:39

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import pytz
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

date_str = '2025-04-10'

print("="*100)
print(f"VÉRIFICATION : DÉTECTION DÉBUT MOUVEMENT {date_str}")
print("="*100)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Charger prix autour de 14:30
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
    print("❌ Aucune donnée de prix")
    exit(1)

df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
df_prices = df_prices.set_index('datetime')

# Baseline : 13:30 (avant les événements)
baseline_time = TZ_BERN.localize(
    datetime.combine(pd.to_datetime(date_str).date(), datetime.min.time().replace(hour=13, minute=30))
)

prices_at_baseline = df_prices[df_prices.index >= baseline_time]

if prices_at_baseline.empty:
    print("❌ Pas de données après 13:30")
    exit(1)

baseline_price = prices_at_baseline.iloc[0]['open']

print(f"Baseline : {baseline_time.strftime('%H:%M')} @ {baseline_price:.5f}")
print()

# Analyser chaque bougie pour trouver le début du mouvement
print("="*100)
print("ANALYSE BOUGIE PAR BOUGIE (13:30-16:00)")
print("="*100)
print()

print(f"{'Heure':<8} {'Open':<12} {'High':<12} {'Low':<12} {'Close':<12} {'Mvt UP':<12} {'Mvt DOWN':<12} {'Mvt MAX':<12}")
print("-"*100)

# ⚠️ NOUVEAU : Détecter le début du mouvement FORT (REF-035)
# Stratégie : Identifier le pic maximum, puis remonter pour trouver le début (≥30% du pic)

max_high = prices_at_baseline['high'].max()
min_low = prices_at_baseline['low'].min()

high_pips = (max_high - baseline_price) * 10000
low_pips = (baseline_price - min_low) * 10000

if high_pips > low_pips and high_pips >= 10.0:  # Seuil minimum 10 pips
    peak_time = prices_at_baseline[prices_at_baseline['high'] == max_high].index[0]
    direction = 'UP'
    max_pips = high_pips
elif low_pips >= 10.0:
    low_time = prices_at_baseline[prices_at_baseline['low'] == min_low].index[0]
    peak_time = low_time
    direction = 'DOWN'
    max_pips = low_pips
else:
    peak_time = None
    max_pips = 0.0
    direction = None

# Calculer seuil = 30% du pic maximum
threshold_pips = max_pips * 0.30 if max_pips > 0 else 0.0

# Remonter depuis le pic pour trouver le début
movement_start_detected = None
movement_start_pips = 0.0

if peak_time is not None:
    df_before_peak = prices_at_baseline[prices_at_baseline.index <= peak_time]
    movement_start_detected = peak_time
    movement_start_pips = max_pips
    
    for idx in reversed(df_before_peak.index):
        row = df_before_peak.loc[idx]
        
        if direction == 'UP':
            current_pips = (row['high'] - baseline_price) * 10000
            if current_pips < threshold_pips:
                next_idx = df_before_peak.index[df_before_peak.index > idx]
                if len(next_idx) > 0:
                    movement_start_detected = next_idx[0]
                    movement_start_pips = (df_before_peak.loc[movement_start_detected]['high'] - baseline_price) * 10000
                else:
                    movement_start_detected = idx
                    movement_start_pips = current_pips
                break
        else:
            current_pips = (baseline_price - row['low']) * 10000
            if current_pips < threshold_pips:
                next_idx = df_before_peak.index[df_before_peak.index > idx]
                if len(next_idx) > 0:
                    movement_start_detected = next_idx[0]
                    movement_start_pips = (baseline_price - df_before_peak.loc[movement_start_detected]['low']) * 10000
                else:
                    movement_start_detected = idx
                    movement_start_pips = current_pips
                break

# Afficher toutes les bougies pour référence
for idx, row in prices_at_baseline.iterrows():
    high_pips = (row['high'] - baseline_price) * 10000
    low_pips = (baseline_price - row['low']) * 10000
    mvt_max = max(high_pips, low_pips)
    
    time_str = idx.strftime('%H:%M')
    print(f"{time_str:<8} {row['open']:>11.5f} {row['high']:>11.5f} {row['low']:>11.5f} {row['close']:>11.5f} {high_pips:>11.2f} {low_pips:>11.2f} {mvt_max:>11.2f}")

print()

# Trouver le pic maximum
max_high = prices_at_baseline['high'].max()
min_low = prices_at_baseline['low'].min()

impact_up = (max_high - baseline_price) * 10000
impact_down = (baseline_price - min_low) * 10000
impact_max = max(impact_up, impact_down)

peak_time = prices_at_baseline[prices_at_baseline['high'] == max_high].index[0] if impact_up > impact_down else prices_at_baseline[prices_at_baseline['low'] == min_low].index[0]

print("="*100)
print("RÉSULTATS")
print("="*100)
print()

if movement_start_detected:
    print(f"✅ Début mouvement détecté : {movement_start_detected.strftime('%H:%M')} ({movement_start_pips:.1f} pips)")
else:
    print("❌ Début mouvement non détecté (seuil 5 pips)")
print()

print(f"Pic maximum : {peak_time.strftime('%H:%M')} ({impact_max:.1f} pips)")
print()

# Vérifier événements à 14:30
print("="*100)
print("ÉVÉNEMENTS À 14:30")
print("="*100)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

query_events = f"""
SELECT 
    e.ts_utc,
    e.event_key,
    e.country,
    e.importance_n,
    e.actual,
    e.estimate
FROM events e
WHERE DATE(e.ts_utc) = '{date_str}'
  AND EXTRACT(HOUR FROM e.ts_utc) = 14
  AND EXTRACT(MINUTE FROM e.ts_utc) = 30
  AND e.country = 'US'
  AND e.importance_n = 3
ORDER BY e.ts_utc
"""

df_events = conn.execute(query_events).df()
conn.close()

if not df_events.empty:
    print(f"✅ {len(df_events)} événements US HIGH à 14:30")
    print()
    for _, event in df_events.iterrows():
        event_key = str(event['event_key'])[:60]
        print(f"  - {event_key}")
else:
    print("❌ Aucun événement US HIGH à 14:30")
    print()

# Vérifier coïncidence
if movement_start_detected:
    anchor_time_1430 = TZ_BERN.localize(
        datetime.combine(pd.to_datetime(date_str).date(), datetime.min.time().replace(hour=14, minute=30))
    )
    
    window_start = movement_start_detected - pd.Timedelta(minutes=15)
    window_end = movement_start_detected + pd.Timedelta(minutes=15)
    
    coincidence = (window_start <= anchor_time_1430 <= window_end)
    diff_minutes = abs((movement_start_detected - anchor_time_1430).total_seconds() / 60)
    
    print("="*100)
    print("COÏNCIDENCE")
    print("="*100)
    print()
    print(f"Début mouvement : {movement_start_detected.strftime('%H:%M')}")
    print(f"Anchor time 14:30 : {anchor_time_1430.strftime('%H:%M')}")
    print(f"Fenêtre coïncidence : {window_start.strftime('%H:%M')} - {window_end.strftime('%H:%M')} (±15 min)")
    print()
    
    if coincidence:
        print("✅ COÏNCIDENCE : Anchor time dans fenêtre ±15 min")
    else:
        print(f"❌ PAS DE COÏNCIDENCE : Différence de {diff_minutes:.0f} minutes")
    print()

print("="*100)
print("CLARIFICATION")
print("="*100)
print()
print("1. Colonne 'Mouvement' :")
print("   → Représente le DÉBUT du mouvement (première bougie avec mouvement ≥5 pips)")
print()
print("2. 'Coïncidence' :")
print("   → Vérifie si l'anchor_time du cluster est dans une fenêtre de ±15 minutes")
print("   → autour du début du mouvement réel")
print("   → Coïncidence = anchor_time entre (mouvement - 15 min) et (mouvement + 15 min)")
print()

