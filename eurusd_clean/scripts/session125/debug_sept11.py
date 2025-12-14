#!/usr/bin/env python3
"""
DEBUG 11 SEPTEMBRE - Où est le cluster CPI ?
"""
import duckdb
import pandas as pd
from pathlib import Path
import pytz

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
TZ_BERN = pytz.timezone('Europe/Zurich')

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("DEBUG 11 SEPTEMBRE 2025")
print("="*80)
print()

# 1. Charger TOUS événements 11 septembre (pas juste HIGH)
print("1️⃣ TOUS ÉVÉNEMENTS 11 SEPTEMBRE :")
df_all_events = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance
    FROM economic_events
    WHERE datetime_utc >= '2025-09-11 00:00:00'
      AND datetime_utc <= '2025-09-11 23:59:59'
    ORDER BY datetime_utc
""").df()

df_all_events['datetime_utc'] = pd.to_datetime(df_all_events['datetime_utc'], utc=True)
df_all_events['datetime_bern'] = df_all_events['datetime_utc'].dt.tz_convert(TZ_BERN)

print(f"Total événements : {len(df_all_events)}")
print()

# Filtrer HIGH uniquement
df_high = df_all_events[df_all_events['importance'] == 'HIGH'].copy()
print(f"Événements HIGH : {len(df_high)}")
print()

# Afficher par heure Bern
print("📊 Événements HIGH par heure (Bern) :")
for hour in sorted(df_high['datetime_bern'].dt.hour.unique()):
    events_hour = df_high[df_high['datetime_bern'].dt.hour == hour]
    print(f"\n   {hour:02d}h00-{hour:02d}h59 : {len(events_hour)} événements")
    for _, e in events_hour.iterrows():
        print(f"      {e['datetime_bern'].strftime('%H:%M')} - {e['event_name'][:50]:50s} ({e['country']})")

# 2. Mapper avec scores empiriques
print()
print("="*80)
print("2️⃣ MAPPING AVEC SCORES EMPIRIQUES")
print("="*80)
print()

df_scores = pd.read_csv(SCORES_PATH)
df_high_scored = df_high.merge(
    df_scores[['event_name', 'country', 'empirical_score', 'sample_size']],
    on=['event_name', 'country'],
    how='left'
)

print("📊 Événements HIGH avec scores :")
measurable = df_high_scored[df_high_scored['sample_size'].notna() & (df_high_scored['sample_size'] > 0)]
no_score = df_high_scored[df_high_scored['sample_size'].isna() | (df_high_scored['sample_size'] == 0)]

print(f"\n✅ Avec score empirique : {len(measurable)}")
for _, e in measurable.iterrows():
    print(f"   {e['datetime_bern'].strftime('%H:%M')} - {e['event_name'][:40]:40s} - Score: {e['empirical_score']:.2f}")

print(f"\n❌ Sans score empirique : {len(no_score)}")
for _, e in no_score.iterrows():
    print(f"   {e['datetime_bern'].strftime('%H:%M')} - {e['event_name'][:40]:40s} - {e['country']}")

# 3. Charger prix 11 septembre
print()
print("="*80)
print("3️⃣ MOUVEMENTS PRIX 11 SEPTEMBRE")
print("="*80)
print()

df_prices = conn.execute("""
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= '2025-09-11 00:00:00'
      AND datetime <= '2025-09-11 23:59:59'
    ORDER BY datetime
""").df()

df_prices['datetime'] = pd.to_datetime(df_prices['datetime'], utc=True).dt.tz_convert(TZ_BERN)
df_prices.set_index('datetime', inplace=True)

print(f"Prix chargés : {len(df_prices)} minutes")
print()

# Calculer mouvements par heure
print("📊 Amplitude max par heure (60 min rolling) :")
for hour in range(0, 24):
    hour_start = pd.Timestamp(f'2025-09-11 {hour:02d}:00:00', tz=TZ_BERN)
    hour_end = hour_start + pd.Timedelta(hours=1)
    
    prices_hour = df_prices[(df_prices.index >= hour_start) & (df_prices.index < hour_end)]
    
    if len(prices_hour) > 0:
        max_high = prices_hour['high'].max()
        min_low = prices_hour['low'].min()
        amplitude = (max_high - min_low) * 10000
        
        if amplitude > 20:  # Seuil 20 pips pour affichage
            print(f"   {hour:02d}h00-{hour:02d}h59 : {amplitude:.1f} pips")

# 4. Focus 14h00-15h00 (période critique)
print()
print("="*80)
print("4️⃣ FOCUS 14h00-15h00 (CPI + ECB)")
print("="*80)
print()

focus_start = pd.Timestamp('2025-09-11 14:00:00', tz=TZ_BERN)
focus_end = pd.Timestamp('2025-09-11 15:00:00', tz=TZ_BERN)

prices_focus = df_prices[(df_prices.index >= focus_start) & (df_prices.index < focus_end)]

print("📊 Mouvements minute par minute (14h00-15h00) :")
print()

baseline = prices_focus.iloc[0]['close']
print(f"   Baseline 14:00 : {baseline:.5f}")
print()

for idx, row in prices_focus.iterrows():
    time_str = idx.strftime('%H:%M')
    impact_from_baseline = (row['close'] - baseline) * 10000
    
    # Amplitude 1 minute
    amplitude_1m = (row['high'] - row['low']) * 10000
    
    if abs(impact_from_baseline) > 10 or amplitude_1m > 10:
        print(f"   {time_str} : Close {row['close']:.5f} ({impact_from_baseline:+.1f} pips) | Amplitude: {amplitude_1m:.1f} pips")

# 5. Détecter spikes avec différents seuils
print()
print("="*80)
print("5️⃣ SPIKES 14h00-15h00 (différents seuils)")
print("="*80)
print()

for threshold in [20, 30, 35, 40, 50]:
    print(f"Seuil {threshold} pips :")
    
    for i in range(len(prices_focus) - 60):
        window = prices_focus.iloc[i:i+60]
        max_high = window['high'].max()
        min_low = window['low'].min()
        amplitude = (max_high - min_low) * 10000
        
        if amplitude >= threshold:
            start_time = window.index[0].strftime('%H:%M')
            print(f"   Spike {start_time} : {amplitude:.1f} pips")
            break
    else:
        print(f"   Aucun spike ≥ {threshold} pips")
    
    print()

conn.close()

print("="*80)
print("DEBUG TERMINÉ")
print("="*80)
