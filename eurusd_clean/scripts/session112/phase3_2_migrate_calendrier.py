#!/usr/bin/env python3
"""
MIGRATION CALENDRIER TRADING - Phase 3
=======================================

Migre Calendrier-Trading.py vers nouvelle structure.

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 3
"""

from pathlib import Path
import shutil
import re

print("="*80)
print("📅 MIGRATION CALENDRIER TRADING")
print("="*80)

# Chemins
source = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
target = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/streamlit_app/pages/1_Calendrier_Trading.py")

print(f"\n📋 Source: {source.name}")
print(f"📋 Cible: pages/1_Calendrier_Trading.py")

if not source.exists():
    print(f"\n❌ Source introuvable: {source}")
    exit(1)

# Confirmation
proceed = input("\n👉 Migrer Calendrier Trading ? (oui/non): ").strip().lower()

if proceed != "oui":
    print("\n❌ Migration annulée")
    exit(0)

# Lire source
content = source.read_text()

# ══════════════════════════════════════════════════════════════════════
# ADAPTATIONS
# ══════════════════════════════════════════════════════════════════════

print("\n🔧 Adaptations...")

# 1. Adapter imports
new_imports = '''import streamlit as st
import sys
from pathlib import Path

# Imports nouvelle structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
import config

# Autres imports
'''

# Remplacer section imports
content = re.sub(
    r'import streamlit as st.*?(?=\n\n)',
    new_imports.strip(),
    content,
    flags=re.DOTALL
)

# 2. Remplacer chemins DB
content = content.replace(
    'DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"',
    'DB_PATH = config.DB_PATH'
)

# 3. Remplacer prices_1m par prices_bern
content = content.replace('FROM prices_1m', 'FROM prices_bern')
content = content.replace('prices_1m', 'prices_bern')

# 4. Ajouter note en haut
header = '''"""
Calendrier Trading - Événements futurs avec scores
===================================================

Version 4.0 - Nouvelle structure eurusd_clean
Utilise vue prices_bern (timezone correcte)

Affiche événements à venir triés par score de tradabilité.
"""

'''

content = header + content

# Écrire cible
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(content)

print(f"✅ Calendrier migré")
print(f"   Taille: {target.stat().st_size / 1024:.1f} KB")

print("\n" + "="*80)
print("✅ MIGRATION CALENDRIER TERMINÉE")
print("="*80)
