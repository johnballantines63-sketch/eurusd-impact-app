#!/usr/bin/env python3
"""
VÉRIFICATION MANUELLE : Tendance 11.09.2025
===========================================
Vérifie si on capte la vraie tendance (4 sept) ou juste bruit (10 sept)
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
from datetime import datetime, timedelta

# Setup
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

import importlib.util
spec_config = importlib.util.spec_from_file_location(
    "config", 
    project_root / "eurusd_clean" / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

print("="*80)
print("VÉRIFICATION MANUELLE : 11.09.2025")
print("="*80)
print()

# Charger prix 4-11 septembre
conn = duckdb.connect(str(db_path), read_only=True)

query = """
SELECT 
    datetime,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime >= '2025-09-04 00:00:00'::TIMESTAMP
  AND datetime <= '2025-09-11 14:30:00'::TIMESTAMP
ORDER BY datetime ASC
"""

df = conn.execute(query).fetchdf()
conn.close()

print(f"✅ {len(df)} bougies chargées (4-11 sept)")
print()

# Analyser par jour
df['datetime'] = pd.to_datetime(df['datetime'])
df['date'] = df['datetime'].dt.date
df['close_pips'] = df['close'] * 10000

# Stats par jour
print("="*80)
print("STATISTIQUES PAR JOUR")
print("="*80)
print()

daily_stats = df.groupby('date').agg({
    'high': 'max',
    'low': 'min',
    'close': ['first', 'last']
}).reset_index()

daily_stats.columns = ['date', 'high', 'low', 'open', 'close']
daily_stats['amplitude_pips'] = (daily_stats['high'] - daily_stats['low']) * 10000
daily_stats['move_pips'] = (daily_stats['close'] - daily_stats['open']) * 10000

print(daily_stats.to_string(index=False))
print()

# Trouver HIGH absolu et LOW absolu
idx_max = df['high'].idxmax()
idx_min = df['low'].idxmin()

high_max = df.loc[idx_max]
low_min = df.loc[idx_min]

print("="*80)
print("EXTREMA ABSOLUS (4-11 SEPT)")
print("="*80)
print()

print(f"📊 HIGH ABSOLU :")
print(f"   Date/Heure : {high_max['datetime']}")
print(f"   Prix       : {high_max['high']:.5f}")
print(f"   Pips       : {high_max['high']*10000:.1f}")
print()

print(f"📊 LOW ABSOLU :")
print(f"   Date/Heure : {low_min['datetime']}")
print(f"   Prix       : {low_min['low']:.5f}")
print(f"   Pips       : {low_min['low']*10000:.1f}")
print()

# Amplitude totale
amplitude_totale = (high_max['high'] - low_min['low']) * 10000

print(f"📊 AMPLITUDE TOTALE (4-11 sept) : {amplitude_totale:.1f} pips")
print()

# Tendance dominante
if high_max['datetime'] < low_min['datetime']:
    print("🔍 TENDANCE DOMINANTE : HIGH → LOW (Baissière)")
    print(f"   De {high_max['datetime']} à {low_min['datetime']}")
else:
    print("🔍 TENDANCE DOMINANTE : LOW → HIGH (Haussière)")
    print(f"   De {low_min['datetime']} à {high_max['datetime']}")

print()

# Comparer avec détection script
print("="*80)
print("COMPARAISON AVEC DÉTECTION SCRIPT")
print("="*80)
print()

print("📊 SCRIPT Phase 2C a détecté :")
print("   Point inversion : 2025-09-10 07:01")
print("   Durée           : 29.5h")
print("   Amplitude       : 66.6 pips")
print()

print("📊 RÉALITÉ (analyse manuelle) :")
if high_max['datetime'] < low_min['datetime']:
    print(f"   Point début     : {high_max['datetime']} (HIGH)")
    duration = (pd.to_datetime('2025-09-11 12:30:00') - high_max['datetime']).total_seconds() / 3600
else:
    print(f"   Point début     : {low_min['datetime']} (LOW)")
    duration = (pd.to_datetime('2025-09-11 12:30:00') - low_min['datetime']).total_seconds() / 3600

print(f"   Durée           : {duration:.1f}h")
print(f"   Amplitude       : {amplitude_totale:.1f} pips")
print()

# Graphique ASCII simple des closes par jour
print("="*80)
print("ÉVOLUTION PRIX CLOSE PAR JOUR")
print("="*80)
print()

closes_by_day = df.groupby('date')['close'].last()
for date, close in closes_by_day.items():
    pips = close * 10000
    bar = "█" * int((pips - 11600) / 2)  # Normalisation simple
    print(f"{date} | {close:.5f} ({pips:7.1f} pips) | {bar}")

print()
print("="*80)
print("CONCLUSION")
print("="*80)
print()

if duration > 50:
    print("✅ Tendance LONGUE détectée manuellement (>50h)")
    print("❌ Script a détecté une durée COURTE (29.5h)")
    print("⚠️  Le script capte un parasite récent, pas la vraie tendance !")
else:
    print("✅ Script semble cohérent avec analyse manuelle")
