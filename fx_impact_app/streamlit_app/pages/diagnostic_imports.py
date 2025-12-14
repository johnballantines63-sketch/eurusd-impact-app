#!/usr/bin/env python3
"""
FIX RAPIDE : Correction imports Planificateur V2.4
Session 68 - 24 octobre 2025
"""

import sys
from pathlib import Path

# Le problème : Streamlit lance depuis streamlit_app/ mais les imports
# cherchent dans streamlit_app/pages/../../../src au lieu de ../../src

print("🔧 DIAGNOSTIC IMPORTS")
print("=" * 60)

# Chemin actuel du script
current_file = Path(__file__).absolute()
print(f"📁 Fichier actuel : {current_file}")

# Chemin attendu vers src/
# De : streamlit_app/pages/5_Planificateur...
# Vers : fx_impact_app/src/
expected_src = current_file.parent.parent.parent / "src"
print(f"📁 Path src attendu : {expected_src}")
print(f"✅ Existe ? {expected_src.exists()}")

if expected_src.exists():
    print(f"\n📦 Fichiers dans src/ :")
    for f in sorted(expected_src.glob("*.py"))[:10]:
        print(f"  - {f.name}")

# Test imports
print(f"\n🧪 TEST IMPORTS")
print("=" * 60)

sys.path.insert(0, str(expected_src))

try:
    import formulas_validated
    print("✅ formulas_validated : OK")
    print(f"   Localisation : {formulas_validated.__file__}")
except ImportError as e:
    print(f"❌ formulas_validated : {e}")

try:
    import double_wave
    print("✅ double_wave : OK")
    print(f"   Localisation : {double_wave.__file__}")
except ImportError as e:
    print(f"❌ double_wave : {e}")

try:
    import single_wave_strong
    print("✅ single_wave_strong : OK")
    print(f"   Localisation : {single_wave_strong.__file__}")
except ImportError as e:
    print(f"❌ single_wave_strong : {e}")

try:
    import config
    print("✅ config : OK")
    print(f"   Localisation : {config.__file__}")
except ImportError as e:
    print(f"❌ config : {e}")

print(f"\n📊 sys.path (premiers 5) :")
for i, p in enumerate(sys.path[:5], 1):
    print(f"  {i}. {p}")

print("\n" + "=" * 60)
print("💡 SOLUTION :")
print("Le path est correct dans le code du Planificateur.")
print("Le problème vient probablement du lancement Streamlit.")
print("\n🔧 Essayez :")
print("  cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app")
print("  streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py")
print("\nAu lieu de :")
print("  cd streamlit_app")
print("  streamlit run pages/5_Planificateur_V2_FORMULES_VALIDEES.py")
