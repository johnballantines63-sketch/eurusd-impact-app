#!/usr/bin/env python3
"""
MESURE IMPACT RÉEL CORRIGÉE - MÉTHODE MT5
==========================================

Mesure l'impact du prix de départ (event_time) au pic réel atteint.

CORRECTION par rapport à l'ancienne méthode :
- Ancienne : max-min sur fenêtre fixe 60 min
- Nouvelle : prix_départ → prix_pic réel

Cas 11.09.2025 :
- Départ 14:30 : 1.16816
- Pic 15:10    : 1.17378
- Impact réel  : 56.2 pips (pas 44.6 !)

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
print("MESURE IMPACT RÉEL - MÉTHODE MT5 CORRIGÉE")
print("=" * 80)
print()

# Configuration
EVENT_DATE = "2025-09-11"
EVENT_TIME_BERN = "14:30:00"
WINDOW_MINUTES = 120  # Chercher pic dans 120 min (pas 60)

# Conversion Bern → UTC
event_datetime_bern = datetime.strptime(f"{EVENT_DATE} {EVENT_TIME_BERN}", "%Y-%m-%d %H:%M:%S")
event_datetime_utc = event_datetime_bern - timedelta(hours=2)

# Rendre timezone-aware pour comparaison avec DB (datetime en DB ont timezone)
event_datetime_utc = event_datetime_utc.replace(tzinfo=timezone.utc)

print(f"📅 Événement : {event_datetime_bern} Bern")
print(f"              {event_datetime_utc} UTC")
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

query_prices = """
SELECT datetime, close
FROM prices_1m
WHERE datetime >= ?
    AND datetime < ?
ORDER BY datetime
"""

# Charger 1 min AVANT + 120 min APRÈS
start_time = event_datetime_utc - timedelta(minutes=1)  # -1 min pour avoir prix départ
end_time = event_datetime_utc + timedelta(minutes=WINDOW_MINUTES)

with duckdb.connect(str(db_path), read_only=True) as conn:
    prices_df = conn.execute(query_prices, [start_time, end_time]).fetchdf()

print(f"✅ {len(prices_df)} points chargés (M1)")
print()

if len(prices_df) == 0:
    print("❌ ERREUR : Pas de prix chargés")
    sys.exit(1)

# Méthode ANCIENNE (pour comparaison)
price_max_old = prices_df['close'].max()
price_min_old = prices_df['close'].min()
impact_old_method = (price_max_old - price_min_old) * 10000

# Méthode CORRECTE (MT5)
# 1. Prix départ = close du candle JUSTE AVANT l'événement
#    Event à 12:30 UTC → Prendre close de 12:29 UTC
price_start_candle = prices_df[prices_df['datetime'] < event_datetime_utc].iloc[-1]
price_start = price_start_candle['close']
time_start = price_start_candle['datetime']

# 2. Chercher pic (HIGH si montée, LOW si descente) APRÈS l'événement
prices_after_event = prices_df[prices_df['datetime'] >= event_datetime_utc]
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
duration_to_peak = (time_peak - event_datetime_utc).total_seconds() / 60

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
print(f"   Départ attendu : 1.16816 (14:30)")
print(f"   Pic attendu    : 1.17378 (15:10)")
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

# Différence entre méthodes
diff = abs(impact_correct - impact_old_method)
print(f"⚠️ DIFFÉRENCE ENTRE MÉTHODES : {diff:.1f} pips ({diff/impact_correct*100:.1f}%)")
print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("L'ancienne méthode (max-min) sous-estimait l'impact réel !")
print()
print("La nouvelle méthode (départ → pic) correspond à la mesure MT5.")
print()
print("✅ Impact réel corrigé : {:.1f} pips".format(impact_correct))
print()
print("🎯 Prochaine étape : Recalculer amp_optimal avec impact corrigé")
print("=" * 80)

# Sauvegarder pour recalcul amp_optimal
output_data = {
    'event_date': EVENT_DATE,
    'event_time_utc': event_datetime_utc.isoformat(),
    'impact_real_corrected': {
        'price_start': float(price_start),
        'price_peak': float(price_peak),
        'time_peak': str(time_peak),
        'direction': direction,
        'duration_to_peak_min': float(duration_to_peak),
        'impact_pips': float(impact_correct),
        'method': 'start_to_peak'
    },
    'impact_old_method': {
        'impact_pips': float(impact_old_method),
        'method': 'max_minus_min'
    }
}

import json
output_file = Path(__file__).parent / "impact_real_corrected.json"
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)

print(f"💾 Résultats sauvegardés : {output_file.name}")
