#!/usr/bin/env python3
"""
VÉRIFICATION TIMEZONE - Comparaison 14:30 vs 16:30 Bern
========================================================

Compare les prix trouvés à :
- 14:30 Bern (12:30 UTC) : ce qu'on cherche actuellement
- 16:30 Bern (14:30 UTC) : hypothèse décalage +2h

Objectif : Voir où se trouve le prix MT5 1.16816

Auteur : André Valentin
Date   : 31 octobre 2025 - Session 103
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import duckdb
import importlib.util

print("=" * 80)
print("VÉRIFICATION TIMEZONE - Comparaison 14:30 vs 16:30 Bern")
print("=" * 80)
print()

# Config
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

# Prix MT5 attendu
PRICE_MT5_START = 1.16816
PRICE_MT5_PEAK = 1.17378

print("🎯 PRIX MT5 ATTENDUS :")
print(f"   Départ : {PRICE_MT5_START}")
print(f"   Pic    : {PRICE_MT5_PEAK}")
print()
print("=" * 80)

# ═══════════════════════════════════════════════════════════════
# TEST 1 : 14:30 Bern = 12:30 UTC (ce qu'on cherche actuellement)
# ═══════════════════════════════════════════════════════════════

print()
print("TEST 1 : Événement à 14:30 Bern (12:30 UTC)")
print("-" * 80)
print()

time_1430_bern = datetime(2025, 9, 11, 14, 30, 0)
time_1430_utc = time_1430_bern - timedelta(hours=2)  # 12:30 UTC
time_1430_utc = time_1430_utc.replace(tzinfo=timezone.utc)

print(f"📅 14:30 Bern = {time_1430_utc}")
print()

# Charger prix -1 min et +10 min
start_time = time_1430_utc - timedelta(minutes=1)
end_time = time_1430_utc + timedelta(minutes=10)

query = """
SELECT datetime, close
FROM prices_1m
WHERE datetime >= ?
    AND datetime < ?
ORDER BY datetime
"""

with duckdb.connect(str(db_path), read_only=True) as conn:
    prices_1430 = conn.execute(query, [start_time, end_time]).fetchdf()

print(f"✅ {len(prices_1430)} prix chargés")
print()
print("Prix autour de 14:30 Bern (12:30 UTC) :")
print("-" * 80)
for idx, row in prices_1430.iterrows():
    dt = row['datetime']  # Déjà avec timezone dans DB
    price = row['close']
    
    # Calculer écart avec prix MT5
    ecart_start = abs(price - PRICE_MT5_START) * 10000
    ecart_peak = abs(price - PRICE_MT5_PEAK) * 10000
    
    marker = ""
    if ecart_start < 1:
        marker = " ← ✅ MATCH PRIX DÉPART MT5"
    elif ecart_peak < 1:
        marker = " ← ✅ MATCH PRIX PIC MT5"
    
    print(f"{dt} : {price:.5f} (écart départ: {ecart_start:.1f} pips){marker}")

# ═══════════════════════════════════════════════════════════════
# TEST 2 : 16:30 Bern = 14:30 UTC (hypothèse décalage +2h)
# ═══════════════════════════════════════════════════════════════

print()
print()
print("TEST 2 : Hypothèse décalage - Événement à 16:30 Bern (14:30 UTC)")
print("-" * 80)
print()

time_1630_bern = datetime(2025, 9, 11, 16, 30, 0)
time_1630_utc = time_1630_bern - timedelta(hours=2)  # 14:30 UTC
time_1630_utc = time_1630_utc.replace(tzinfo=timezone.utc)

print(f"📅 16:30 Bern = {time_1630_utc}")
print()

# Charger prix -1 min et +10 min
start_time = time_1630_utc - timedelta(minutes=1)
end_time = time_1630_utc + timedelta(minutes=10)

with duckdb.connect(str(db_path), read_only=True) as conn:
    prices_1630 = conn.execute(query, [start_time, end_time]).fetchdf()

print(f"✅ {len(prices_1630)} prix chargés")
print()
print("Prix autour de 16:30 Bern (14:30 UTC) :")
print("-" * 80)
for idx, row in prices_1630.iterrows():
    dt = row['datetime']  # Déjà avec timezone dans DB
    price = row['close']
    
    # Calculer écart avec prix MT5
    ecart_start = abs(price - PRICE_MT5_START) * 10000
    ecart_peak = abs(price - PRICE_MT5_PEAK) * 10000
    
    marker = ""
    if ecart_start < 1:
        marker = " ← ✅ MATCH PRIX DÉPART MT5"
    elif ecart_peak < 1:
        marker = " ← ✅ MATCH PRIX PIC MT5"
    
    print(f"{dt} : {price:.5f} (écart départ: {ecart_start:.1f} pips){marker}")

# ═══════════════════════════════════════════════════════════════
# CONCLUSION
# ═══════════════════════════════════════════════════════════════

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()

# Chercher prix proche de 1.16816 dans les deux datasets
match_1430 = prices_1430[abs(prices_1430['close'] - PRICE_MT5_START) < 0.00001]
match_1630 = prices_1630[abs(prices_1630['close'] - PRICE_MT5_START) < 0.00001]

if len(match_1430) > 0:
    print("✅ Prix MT5 départ (1.16816) TROUVÉ à 14:30 Bern (12:30 UTC)")
    print("   → Pas de problème timezone, DB correcte")
elif len(match_1630) > 0:
    print("✅ Prix MT5 départ (1.16816) TROUVÉ à 16:30 Bern (14:30 UTC)")
    print("   → PROBLÈME TIMEZONE : Timestamps DB décalés de +2h")
    print("   → Les timestamps DB sont en HEURE LOCALE (Bern), pas UTC !")
else:
    print("❌ Prix MT5 départ (1.16816) NON TROUVÉ dans aucun des deux moments")
    print("   → Problème plus complexe (broker différent ? données incorrectes ?)")

print()
print("=" * 80)
