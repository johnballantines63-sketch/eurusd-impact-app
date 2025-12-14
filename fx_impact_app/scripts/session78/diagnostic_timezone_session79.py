#!/usr/bin/env python3
"""
DIAGNOSTIC TIMEZONE - SESSION 79
================================

Analyse le problème de timezone qui cause 0 événements.

Date : 25 octobre 2025
Session : 79
"""

import pandas as pd
import dateutil.parser
import pytz
from pathlib import Path
from datetime import timedelta

ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT_DIR / "data" / "movements_strong_session75_v3.csv"

print("\n" + "="*70)
print("DIAGNOSTIC TIMEZONE - SESSION 79")
print("="*70 + "\n")

# Charger dataset
df = pd.read_csv(DATASET_PATH)

# Prendre un exemple
row = df[df['date'] == '2024-12-18'].iloc[0]

print("📋 EXEMPLE : 2024-12-18 19:36")
print("-"*70)
print(f"datetime brut : {row['datetime']}")
print()

# Parser
dt_parsed = dateutil.parser.parse(row['datetime'])
print(f"Après dateutil.parser.parse():")
print(f"  datetime : {dt_parsed}")
print(f "  timezone : {dt_parsed.tzinfo}")
print(f"  UTC offset : {dt_parsed.strftime('%z')}")
print()

# Méthode INCORRECTE (script actuel)
tz_berne = pytz.timezone('Europe/Zurich')
dt_berne_incorrect = dt_parsed.astimezone(tz_berne)
print(f"❌ Méthode INCORRECTE (script actuel):")
print(f"  astimezone(Berne) : {dt_berne_incorrect}")
print(f"  UTC offset : {dt_berne_incorrect.strftime('%z')}")
print()

# Méthode CORRECTE
dt_utc = dt_parsed.astimezone(pytz.UTC)
print(f"✅ Méthode CORRECTE:")
print(f"  astimezone(UTC) : {dt_utc}")
print(f"  UTC offset : {dt_utc.strftime('%z')}")
print()

# Fenêtre ±15 min
window = 15
start_incorrect = dt_berne_incorrect - timedelta(minutes=window)
end_incorrect = dt_berne_incorrect + timedelta(minutes=window)

start_correct = dt_utc - timedelta(minutes=window)
end_correct = dt_utc + timedelta(minutes=window)

print(f"📊 FENÊTRE ±{window} MIN")
print("-"*70)
print(f"❌ INCORRECT (script actuel):")
print(f"  Start : {start_incorrect}")
print(f"  End   : {end_incorrect}")
print()
print(f"✅ CORRECT:")
print(f"  Start : {start_correct}")
print(f"  End   : {end_correct}")
print()

print("🔍 ANALYSE")
print("-"*70)
print("Le dataset contient DÉJÀ les timezones (+01:00 ou +02:00)")
print("dateutil.parser les parse correctement")
print("Mais le script convertit ENCORE en Berne → DOUBLE CONVERSION ❌")
print()
print("SOLUTION : Convertir directement en UTC pour query DB")
print()

print("="*70)
print("✅ DIAGNOSTIC TERMINÉ")
print("="*70 + "\n")
