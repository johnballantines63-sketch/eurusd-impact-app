#!/usr/bin/env python3
"""
COPIE MODULES MANQUANTS - Phase 3 Fix
======================================

Copie les modules nécessaires depuis fx_impact_app/src vers eurusd_clean/src/core

Modules:
- forecaster_mvp.py
- scoring_engine.py
- event_families.py
- double_wave.py

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

from pathlib import Path
import shutil

print("="*80)
print("📦 COPIE MODULES MANQUANTS")
print("="*80)

# Chemins
source_dir = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src")
target_dir = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/src/core")

# Modules à copier
modules = [
    "forecaster_mvp.py",
    "scoring_engine.py",
    "event_families.py",
    "double_wave.py",
]

print("\n📋 Modules à copier:")
for module in modules:
    source = source_dir / module
    if source.exists():
        size_kb = source.stat().st_size / 1024
        print(f"  ✅ {module} ({size_kb:.1f} KB)")
    else:
        print(f"  ❌ {module} (introuvable)")

# Confirmation
proceed = input("\n👉 Copier ces modules ? (oui/non): ").strip().lower()

if proceed != "oui":
    print("\n❌ Annulé")
    exit(0)

# ══════════════════════════════════════════════════════════════════════
# COPIE
# ══════════════════════════════════════════════════════════════════════

print("\n🔧 Copie en cours...")

copied = 0
for module in modules:
    source = source_dir / module
    target = target_dir / module
    
    if source.exists():
        try:
            shutil.copy2(source, target)
            print(f"✅ {module} copié")
            copied += 1
        except Exception as e:
            print(f"❌ {module}: {e}")
    else:
        print(f"⚠️ {module} introuvable, skip")

# ══════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("✅ COPIE TERMINÉE")
print("="*80)

print(f"""
📊 Résultat: {copied}/{len(modules)} modules copiés

📁 Emplacement: eurusd_clean/src/core/

🔄 Prochaine étape:
   Relancer: python scripts/session112/TEST_FINAL_app_complete.py
""")

print("="*80)
