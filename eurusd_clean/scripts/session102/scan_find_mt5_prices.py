#!/usr/bin/env python3
"""
SCAN LARGE - Trouver le prix MT5 1.16816
=========================================

Scanne toute la journée du 11 septembre pour trouver où se trouve
le prix de départ MT5 attendu : 1.16816

Auteur : André Valentin
Date   : 31 octobre 2025 - Session 103
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import duckdb
import importlib.util

print("=" * 80)
print("SCAN LARGE - Recherche prix MT5 1.16816")
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

# Prix recherchés
PRICE_MT5_START = 1.16816
PRICE_MT5_PEAK = 1.17378
TOLERANCE = 0.00005  # 0.5 pips

print(f"🔍 Recherche des prix MT5 dans la DB :")
print(f"   Départ attendu : {PRICE_MT5_START}")
print(f"   Pic attendu    : {PRICE_MT5_PEAK}")
print(f"   Tolérance      : ±{TOLERANCE} ({TOLERANCE*10000:.1f} pips)")
print()

# Scanner TOUTE la journée du 11 septembre
query = """
SELECT datetime, close
FROM prices_1m
WHERE DATE(datetime) = '2025-09-11'
ORDER BY datetime
"""

print("📊 Chargement TOUS les prix du 11 septembre 2025...")
with duckdb.connect(str(db_path), read_only=True) as conn:
    prices_all = conn.execute(query).fetchdf()

print(f"✅ {len(prices_all)} prix chargés")
print()

# Chercher prix proche de 1.16816
matches_start = prices_all[abs(prices_all['close'] - PRICE_MT5_START) < TOLERANCE]
matches_peak = prices_all[abs(prices_all['close'] - PRICE_MT5_PEAK) < TOLERANCE]

print("=" * 80)
print("RÉSULTATS - Prix Départ MT5 (1.16816)")
print("=" * 80)
print()

if len(matches_start) > 0:
    print(f"✅ TROUVÉ {len(matches_start)} correspondance(s) :")
    print()
    for idx, row in matches_start.iterrows():
        dt = row['datetime']
        price = row['close']
        ecart = abs(price - PRICE_MT5_START) * 10000
        print(f"   {dt} : {price:.5f} (écart: {ecart:.2f} pips)")
else:
    print("❌ PRIX 1.16816 INTROUVABLE dans toute la journée !")
    print()
    print("   Causes possibles :")
    print("   - DB provient d'un broker différent")
    print("   - Données DB incorrectes")
    print("   - Mauvaise date (pas le bon 11 septembre ?)")

print()
print("=" * 80)
print("RÉSULTATS - Prix Pic MT5 (1.17378)")
print("=" * 80)
print()

if len(matches_peak) > 0:
    print(f"✅ TROUVÉ {len(matches_peak)} correspondance(s) :")
    print()
    for idx, row in matches_peak.iterrows():
        dt = row['datetime']
        price = row['close']
        ecart = abs(price - PRICE_MT5_PEAK) * 10000
        print(f"   {dt} : {price:.5f} (écart: {ecart:.2f} pips)")
else:
    print("❌ PRIX 1.17378 INTROUVABLE dans toute la journée !")

print()
print("=" * 80)
print("ANALYSE RANGE PRIX")
print("=" * 80)
print()

price_min = prices_all['close'].min()
price_max = prices_all['close'].max()
price_range = (price_max - price_min) * 10000

print(f"Range journée 11 septembre :")
print(f"   Min  : {price_min:.5f}")
print(f"   Max  : {price_max:.5f}")
print(f"   Range: {price_range:.1f} pips")
print()

# Vérifier si les prix MT5 sont DANS le range
if price_min <= PRICE_MT5_START <= price_max:
    print(f"   Prix départ MT5 (1.16816) : DANS le range ✅")
else:
    print(f"   Prix départ MT5 (1.16816) : HORS range ❌")
    print(f"      → Confirme broker différent ou données incorrectes")

if price_min <= PRICE_MT5_PEAK <= price_max:
    print(f"   Prix pic MT5 (1.17378)    : DANS le range ✅")
else:
    print(f"   Prix pic MT5 (1.17378)    : HORS range ❌")
    print(f"      → Confirme broker différent ou données incorrectes")

print()
print("=" * 80)
