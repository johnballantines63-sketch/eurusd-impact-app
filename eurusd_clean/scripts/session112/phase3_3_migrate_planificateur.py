#!/usr/bin/env python3
"""
MIGRATION PLANIFICATEUR V2 - Phase 3
=====================================

Migre 5_Planificateur_V2_FORMULES_VALIDEES_session72_fix_importance.py
vers nouvelle structure.

C'EST LE PLANIFICATEUR VALIDÉ !

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 3
"""

from pathlib import Path
import re

print("="*80)
print("🎯 MIGRATION PLANIFICATEUR V2 VALIDÉ")
print("="*80)

# Chemins
source = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES_session72_fix_importance.py")
target = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/streamlit_app/pages/2_Planificateur_V2.py")

print(f"\n📋 Source: {source.name}")
print(f"📋 Cible: pages/2_Planificateur_V2.py")

if not source.exists():
    print(f"\n❌ Source introuvable")
    exit(1)

# Confirmation
proceed = input("\n👉 Migrer Planificateur V2 validé ? (oui/non): ").strip().lower()

if proceed != "oui":
    print("\n❌ Annulé")
    exit(0)

# Lire
content = source.read_text()

print("\n🔧 Adaptations...")

# 1. Fix imports - remplacer toute la section d'import
import_section = '''import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Imports nouvelle structure eurusd_clean
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from core import formulas_validated
import config

# Utilise config pour DB
DB_PATH = config.DB_PATH
'''

# Remplacer depuis "import streamlit" jusqu'à la fin des imports
content = re.sub(
    r'import streamlit.*?(?=\n\n# |st\.set_page_config)',
    import_section.strip() + '\n\n',
    content,
    flags=re.DOTALL
)

# 2. Remplacer références DB
content = re.sub(
    r'DB_PATH\s*=\s*.*?warehouse\.duckdb["\']',
    'DB_PATH = config.DB_PATH',
    content
)

# 3. Remplacer prices_1m par prices_bern
content = content.replace('FROM prices_1m', 'FROM prices_bern')
content = content.replace('prices_1m', 'prices_bern')

# 4. Remplacer imports formulas
content = content.replace(
    'from formulas_validated import',
    'from core.formulas_validated import'
)

# Écrire
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(content)

print(f"✅ Planificateur V2 migré")
print(f"   Taille: {target.stat().st_size / 1024:.1f} KB")

print("\n" + "="*80)
print("✅ MIGRATION PLANIFICATEUR TERMINÉE")
print("="*80)
print("\n📋 Utilise:")
print("  • Formules validées Session 51-55")
print("  • Vue prices_bern (timezone correcte)")
print("  • Config centralisé")
