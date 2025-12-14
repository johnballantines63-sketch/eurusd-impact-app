#!/usr/bin/env python3
"""
MESURE IMPACT RÉEL CORRIGÉE - MÉTHODE MT5 + TIMEZONE FIX
=========================================================

Mesure l'impact du prix de départ (event_time) au pic réel atteint.

CORRECTION TIMEZONE (Session 86) :
==================================
- prices_1m.datetime : +02:00 (Bern/Zurich)
- events.ts_utc : +02:00 (Bern/Zurich)
- → MÊME TIMEZONE, PAS de conversion UTC

Événement 14:30 Bern → Chercher prix 14:30+02:00 directement

Cas 11.09.2025 :
- Événement : 14:30 Bern
- Départ : close 14:29 Bern
- Pic attendu : 1.17378
- Impact attendu : 56.2 pips

Auteur : André Valentin
Date   : 31 octobre 2025 - Session 103
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import duckdb
import importlib.util
import pandas as pd
import numpy as np

print("=" * 80)
print("MESURE IMPACT RÉEL - MÉTHODE MT5 + TIMEZONE FIX SESSION 86")
print("=" * 80)
print()

# Configuration
EVENT_DATE = "2025-09-11"
EVENT_TIME_BERN = "14:30:00"  # Heure BERN (pas besoin conversion)
WINDOW_MINUTES = 120  # Chercher pic dans 120 min

# TIMEZONE FIX (Session 86) : Pas de conversion UTC !
# Les timestamps DB sont déjà en Bern +02:00
event_datetime_bern = datetime.strptime(f"{EVENT_DATE} {EVENT_TIME_BERN}", "%Y-%m-%d %H:%M:%S")

print(f"📅 Événement : {event_datetime_bern} Bern")
print(f"   (Timestamps DB en +02:00, pas de conversion)")
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

# Charger prix AVANT événement pour avoir prix départ
# + prix APRÈS pour trouver pic
print(f"📊 Chargement prix (1 min avant + {WINDOW_MINUTES} min après)...")
print(f"   Prix départ = close du candle précédent (14:29 Bern)")
print()

# Query avec +02:00 EXPLICITE (Session 86)
query_prices = f"""
SELECT datetime, close
FROM prices_1m
WHERE datetime >= '{EVENT_DATE} {EVENT_TIME_BERN}+02:00'::TIMESTAMP - INTERVAL '1 minute'
  AND datetime < '{EVENT_DATE} {EVENT_TIME_BERN}+02:00'::TIMESTAMP + INTERVAL '{WINDOW_MINUTES} minutes'
ORDER BY datetime
"""

with duckdb.connect(str(db_path), read_only=True) as conn:
    prices_df = conn.execute(query_prices).fetchdf()

print(f"✅ {len(prices_df)} points chargés (M1)")
print()

if len(prices_df) == 0:
    print("❌ ERREUR : Pas de prix chargés")
    sys.exit(1)

# Afficher premiers prix pour validation
print("🔍 VALIDATION TIMEZONE - Premiers prix chargés :")
print("-" * 80)
for i in range(min(5, len(prices_df))):
    row = prices_df.iloc[i]
    print(f"   {row['datetime']} : {row['close']:.5f}")
print()

# Méthode ANCIENNE (pour comparaison)
price_max_old = prices_df['close'].max()
price_min_old = prices_df['close'].min()
impact_old_method = (price_max_old - price_min_old) * 10000

# Méthode CORRECTE (MT5)
# 1. Prix départ = close du candle JUSTE AVANT l'événement
#    Event à 14:30 Bern → Prendre close de 14:29 Bern

# Créer datetime de référence avec timezone
import pytz
bern_tz = pytz.timezone('Europe/Zurich')
event_dt_bern = bern_tz.localize(event_datetime_bern)

# Trouver le candle juste avant
price_start_candle = prices_df[prices_df['datetime'] < event_dt_bern].iloc[-1]
price_start = price_start_candle['close']
time_start = price_start_candle['datetime']

# 2. Chercher pic (HIGH si montée, LOW si descente) APRÈS l'événement
prices_after_event = prices_df[prices_df['datetime'] >= event_dt_bern]
price_max = prices_after_event['close'].max()
price_min = prices_after_event['close'].min()
idx_max = prices_after_event['close'].idxmax()
idx_min = prices_after_event['close'].idxmin()

# Déterminer direction
if abs(price_max - price_start) > abs(price_min - price_start):
    # Mouvement haussier
    direction = "UP"
    price_peak = price_max
    time_peak = prices_after_event.loc[idx_max, 'datetime']
    impact_correct = (price_peak - price_start) * 10000
else:
    # Mouvement baissier
    direction = "DOWN"
    price_peak = price_min
    time_peak = prices_after_event.loc[idx_min, 'datetime']
    impact_correct = (price_start - price_peak) * 10000

# Durée jusqu'au pic (depuis event_time, pas depuis time_start qui est -1 min)
duration_to_peak = (time_peak - event_dt_bern).total_seconds() / 60

print("=" * 80)
print("RÉSULTATS")
print("=" * 80)
print()

print("🔴 MÉTHODE ANCIENNE (max-min sur fenêtre) :")
print(f"   Prix max       : {price_max_old:.5f}")
print(f"   Prix min       : {price_min_old:.5f}")
print(f"   Impact calculé : {impact_old_method:.1f} pips")
print()

print("✅ MÉTHODE CORRECTE (départ → pic) :")
print(f"   Prix départ    : {price_start:.5f} (candle {time_start})")
print(f"   Prix pic       : {price_peak:.5f} à {time_peak}")
print(f"   Direction      : {direction}")
print(f"   Durée au pic   : {duration_to_peak:.1f} min (depuis événement)")
print(f"   Impact mesuré  : {impact_correct:.1f} pips")
print()

# Validation MT5
print("📊 VALIDATION MT5 (selon tes graphiques) :")
print(f"   Départ attendu : 1.16816 (14:29 Bern)")
print(f"   Pic attendu    : 1.17378 (15:10 Bern)")
print(f"   Impact attendu : 56.2 pips")
print()

impact_mt5 = 56.2
ecart_vs_mt5 = abs(impact_correct - impact_mt5)
ecart_pct = (ecart_vs_mt5 / impact_mt5) * 100

print(f"   Impact mesuré  : {impact_correct:.1f} pips")
print(f"   Écart vs MT5   : {ecart_vs_mt5:.1f} pips ({ecart_pct:.1f}%)")

if ecart_pct < 5:
    print("   ✅ MÉTHODE VALIDÉE !")
else:
    print("   ⚠️ ÉCART IMPORTANT - VÉRIFIER")
    print()
    print("   Hypothèses :")
    print("   1. Broker différent (DB vs MT5)")
    print("   2. Prix MT5 ne correspond pas à ce moment précis")

print()

# Différence entre méthodes
diff = abs(impact_correct - impact_old_method)
print(f"⚠️ DIFFÉRENCE ENTRE MÉTHODES : {diff:.1f} pips ({diff/impact_correct*100:.1f}%)")
print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("✅ Impact réel corrigé (avec timezone fix Session 86)")
print()
print(f"Impact mesuré : {impact_correct:.1f} pips")
print()
print("🎯 Prochaine étape : Recalculer amp_optimal avec impact corrigé")
print("=" * 80)

# Sauvegarder pour recalcul amp_optimal
output_data = {
    'event_date': EVENT_DATE,
    'event_time_bern': EVENT_TIME_BERN,
    'timezone_fix_applied': 'session_86',
    'impact_real_corrected': {
        'price_start': float(price_start),
        'time_start': str(time_start),
        'price_peak': float(price_peak),
        'time_peak': str(time_peak),
        'direction': direction,
        'duration_to_peak_min': float(duration_to_peak),
        'impact_pips': float(impact_correct),
        'method': 'start_to_peak_timezone_fix_session86'
    },
    'impact_old_method': {
        'impact_pips': float(impact_old_method),
        'method': 'max_minus_min'
    }
}

import json
output_file = Path(__file__).parent / "impact_real_corrected_timezone_fix.json"
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)

print(f"💾 Résultats sauvegardés : {output_file.name}")
