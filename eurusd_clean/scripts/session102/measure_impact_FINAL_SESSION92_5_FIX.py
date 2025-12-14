#!/usr/bin/env python3
"""
MESURE IMPACT RÉEL - TIMESTAMPS CORRECTS SESSION 92.5
======================================================

Utilise les bons timestamps comme Session 92.5 :
- Événement 14:30 Bern = 12:30:00+02:00 dans DB
- Pas 14:30:00+02:00 (qui serait 16:30 Bern) !

Auteur : André Valentin
Date   : 31 octobre 2025 - Session 103
"""

import sys
from pathlib import Path
import duckdb
import importlib.util
import pytz

print("=" * 80)
print("MESURE IMPACT RÉEL - TIMESTAMPS CORRECTS (SESSION 92.5)")
print("=" * 80)
print()

# Configuration
EVENT_DATE = "2025-09-11"
EVENT_TIME_DB = "12:30:00"  # Timestamp DANS LA DB (pas heure locale !)
WINDOW_MINUTES = 120

print(f"📅 Événement 14:30 Bern stocké dans DB comme : {EVENT_TIME_DB}+02:00")
print(f"   (12:30 en timezone +02:00 = 14:30 heure locale Bern)")
print()

# Config DB
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

spec_config = importlib.util.spec_from_file_location(
    "config",
    project_root / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
Config = config_module.Config

config = Config()
db_path = config.get_db_path()

# Query avec BON timestamp
query_prices = f"""
SELECT datetime, close
FROM prices_1m
WHERE datetime >= '{EVENT_DATE} {EVENT_TIME_DB}+02:00'::TIMESTAMP - INTERVAL '1 minute'
  AND datetime < '{EVENT_DATE} {EVENT_TIME_DB}+02:00'::TIMESTAMP + INTERVAL '{WINDOW_MINUTES} minutes'
ORDER BY datetime
"""

print("📊 Chargement prix...")
print()

with duckdb.connect(str(db_path), read_only=True) as conn:
    prices_df = conn.execute(query_prices).fetchdf()

print(f"✅ {len(prices_df)} points chargés")
print()

if len(prices_df) == 0:
    print("❌ ERREUR : Pas de prix chargés")
    sys.exit(1)

# Afficher premiers prix
print("🔍 PREMIERS PRIX (validation timestamp) :")
print("-" * 80)
for i in range(min(5, len(prices_df))):
    row = prices_df.iloc[i]
    print(f"   {row['datetime']} : {row['close']:.5f}")
print()

# Trouver prix départ (candle avant événement)
bern_tz = pytz.timezone('Europe/Zurich')
event_dt = bern_tz.localize(
    __import__('datetime').datetime.strptime(f"{EVENT_DATE} {EVENT_TIME_DB}", "%Y-%m-%d %H:%M:%S")
)

# Prix départ = candle -1 min
price_start_candle = prices_df[prices_df['datetime'] < event_dt].iloc[-1]
price_start = price_start_candle['close']
time_start = price_start_candle['datetime']

# Chercher pic après événement
prices_after = prices_df[prices_df['datetime'] >= event_dt]
price_max = prices_after['close'].max()
price_min = prices_after['close'].min()
idx_max = prices_after['close'].idxmax()
idx_min = prices_after['close'].idxmin()

# Direction
if abs(price_max - price_start) > abs(price_min - price_start):
    direction = "UP"
    price_peak = price_max
    time_peak = prices_after.loc[idx_max, 'datetime']
    impact = (price_peak - price_start) * 10000
else:
    direction = "DOWN"
    price_peak = price_min
    time_peak = prices_after.loc[idx_min, 'datetime']
    impact = (price_start - price_peak) * 10000

duration = (time_peak - event_dt).total_seconds() / 60

print("=" * 80)
print("RÉSULTATS")
print("=" * 80)
print()
print(f"Prix départ    : {price_start:.5f} (candle {time_start})")
print(f"Prix pic       : {price_peak:.5f} à {time_peak}")
print(f"Direction      : {direction}")
print(f"Durée au pic   : {duration:.1f} min")
print(f"Impact mesuré  : {impact:.1f} pips")
print()

print("📊 VALIDATION MT5 :")
print(f"   Départ attendu : 1.16816")
print(f"   Pic attendu    : 1.17378")
print(f"   Impact attendu : 56.2 pips")
print()

ecart_start = abs(price_start - 1.16816) * 10000
ecart_peak = abs(price_peak - 1.17378) * 10000
ecart_impact = abs(impact - 56.2)

print(f"   Départ mesuré  : {price_start:.5f} (écart: {ecart_start:.1f} pips)")
print(f"   Pic mesuré     : {price_peak:.5f} (écart: {ecart_peak:.1f} pips)")
print(f"   Impact mesuré  : {impact:.1f} pips (écart: {ecart_impact:.1f} pips)")
print()

if ecart_impact < 5:
    print("✅✅✅ VALIDATION RÉUSSIE !")
    print("   → Timestamps corrects")
    print("   → DB correcte")
else:
    print("⚠️ Écart important")
    print(f"   Possible broker différent")

print()
print("=" * 80)

# Sauvegarder
import json
output = {
    'event_date': EVENT_DATE,
    'event_time_db': EVENT_TIME_DB,
    'timestamp_fix': 'session_92.5',
    'impact_pips': float(impact),
    'price_start': float(price_start),
    'price_peak': float(price_peak),
    'duration_min': float(duration)
}

output_file = Path(__file__).parent / "impact_validated_session92.5_fix.json"
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

print(f"💾 Résultats : {output_file.name}")
