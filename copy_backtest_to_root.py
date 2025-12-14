#!/usr/bin/env python3
"""
Copie backtest_multi_events_phases_FIXED.py à la racine
"""
from pathlib import Path
import shutil

PROJECT_ROOT = Path("/Users/andrevalentin/Projects/eurusd_news_impact_calculator")

print("📁 Recherche backtest_multi_events_phases_FIXED.py...")

# Chercher dans plusieurs emplacements
search_paths = [
    PROJECT_ROOT / "backtest_multi_events_phases_FIXED.py",
    PROJECT_ROOT / "scripts python" / "backtest_multi_events_phases_FIXED.py",
    PROJECT_ROOT / "scripts" / "backtest_multi_events_phases_FIXED.py",
]

source = None
for path in search_paths:
    if path.exists():
        source = path
        print(f"✅ Trouvé : {path}")
        break

if source is None:
    print("❌ Fichier backtest_multi_events_phases_FIXED.py introuvable !")
    print("\n📂 Où est-il ? Copiez-le manuellement à la racine :")
    print(f"   {PROJECT_ROOT}/")
    exit(1)

# Destination : racine du projet
dest = PROJECT_ROOT / "backtest_multi_events_phases_FIXED.py"

if dest.exists():
    print(f"⚠️ Fichier existe déjà : {dest}")
    print("Écrasement...")

# Copier
shutil.copy2(source, dest)

print(f"✅ Copié : {dest}")
print("\n🎯 Test du backtest :")
print(f"   cd {PROJECT_ROOT}")
print("   python3 backtest_multi_events_phases_FIXED.py")
print("\n📊 Résultats attendus :")
print("   - MAE : 14.2 min")
print("   - Impact moyen : 124.5 pips")
print("   - 33% < 5 min")
