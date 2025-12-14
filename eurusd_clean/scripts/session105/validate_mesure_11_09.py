#!/usr/bin/env python3
"""
SESSION 105 - VALIDATION MESURE 11.09.2025
===========================================

COPIE EXACTE de la méthodologie Session 102 qui MARCHAIT

Auteur : André Valentin
Date   : 2 novembre 2025
Phase  : 3.1.1 (CRITIQUE)
"""

import sys
from pathlib import Path
import duckdb
import importlib.util
import pytz
from datetime import datetime

print("=" * 80)
print("SESSION 105 - VALIDATION MESURE 11.09.2025")
print("=" * 80)
print()

# Configuration
EVENT_DATE = "2025-09-11"
EVENT_TIME_DB = "12:30:00"  # Timestamp DANS LA DB
WINDOW_MINUTES = 120

# Valeur attendue
EXPECTED_IMPACT = 56.8
TOLERANCE = 2.0

print(f"📅 Date événement : {EVENT_DATE}")
print(f"⏰ Heure DB : {EVENT_TIME_DB}+02:00")
print(f"🎯 Impact attendu : {EXPECTED_IMPACT} pips (±{TOLERANCE})")
print()

# Config DB (méthode importlib - pas besoin venv)
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

print(f"📂 Database : {db_path}")
print()

# Query EXACTE de Session 102 (celle qui MARCHAIT !)
query_prices = f"""
SELECT datetime, close
FROM prices_1m
WHERE datetime >= '{EVENT_DATE} {EVENT_TIME_DB}+02:00'::TIMESTAMP - INTERVAL '1 minute'
  AND datetime < '{EVENT_DATE} {EVENT_TIME_DB}+02:00'::TIMESTAMP + INTERVAL '{WINDOW_MINUTES} minutes'
ORDER BY datetime
"""

print("📊 Chargement prix...")

try:
    with duckdb.connect(str(db_path), read_only=True) as conn:
        prices_df = conn.execute(query_prices).fetchdf()
except Exception as e:
    print(f"❌ ERREUR DATABASE : {e}")
    sys.exit(1)

print(f"✅ {len(prices_df)} candles extraites")
print(f"   Période : {prices_df['datetime'].min()} → {prices_df['datetime'].max()}")
print()

if len(prices_df) < 10:
    print(f"❌ ERREUR : Pas assez de données")
    sys.exit(1)

# Trouver prix départ (candle AVANT événement)
bern_tz = pytz.timezone('Europe/Zurich')
event_dt = bern_tz.localize(
    datetime.strptime(f"{EVENT_DATE} {EVENT_TIME_DB}", "%Y-%m-%d %H:%M:%S")
)

print(f"🎯 Event datetime : {event_dt}")
print()

price_start_candle = prices_df[prices_df['datetime'] < event_dt].iloc[-1]
price_start = price_start_candle['close']
time_start = price_start_candle['datetime']

print(f"📍 Prix départ : {price_start:.5f} (candle {time_start})")
print()

# Chercher pics APRÈS événement
prices_after = prices_df[prices_df['datetime'] >= event_dt]

if len(prices_after) == 0:
    print(f"❌ ERREUR : Aucun prix après événement")
    print(f"   Dernier prix : {prices_df['datetime'].max()}")
    print(f"   Event        : {event_dt}")
    sys.exit(1)

price_max = prices_after['close'].max()
price_min = prices_after['close'].min()
idx_max = prices_after['close'].idxmax()
idx_min = prices_after['close'].idxmin()

# Direction = plus grand mouvement
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
print("RÉSULTATS MESURE")
print("=" * 80)
print()
print(f"Direction      : {direction}")
print(f"Prix départ    : {price_start:.5f}")
print(f"Prix pic       : {price_peak:.5f} à {time_peak}")
print(f"Durée au pic   : {duration:.1f} min")
print(f"Impact mesuré  : {impact:.1f} pips")
print()

# Validation
error = abs(impact - EXPECTED_IMPACT)

print("=" * 80)
print("VALIDATION")
print("=" * 80)
print()
print(f"Impact mesuré  : {impact:.1f} pips")
print(f"Impact attendu : {EXPECTED_IMPACT} pips")
print(f"Écart          : {error:.1f} pips")
print(f"Tolérance      : ±{TOLERANCE} pips")
print()

if error <= TOLERANCE:
    print("✅✅✅ VALIDATION RÉUSSIE !")
    print()
    print(f"Écart de {error:.1f} pips dans la tolérance")
    print()
    print("🎯 MÉTHODE VALIDÉE - Prêt pour Phase 3.2")
    
    # Sauvegarder
    import json
    output = {
        'date': EVENT_DATE,
        'method': 'session_102_exact_copy',
        'impact_pips': float(impact),
        'direction': direction,
        'price_start': float(price_start),
        'price_peak': float(price_peak),
        'duration_minutes': float(duration),
        'validation': 'PASSED',
        'error_pips': float(error)
    }
    
    output_file = Path(__file__).parent / 'validation_11_09_SUCCESS.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print(f"💾 Résultat : {output_file.name}")
    print()
    
    sys.exit(0)
else:
    print("❌❌❌ VALIDATION ÉCHOUÉE !")
    print()
    print(f"Écart de {error:.1f} pips > tolérance {TOLERANCE} pips")
    print()
    print("⚠️  BLOCAGE - Impossible de continuer")
    sys.exit(1)
