#!/usr/bin/env python3
"""
MIGRATION API STATUS - Phase 3
===============================

Migre API Status.py vers nouvelle structure.

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 3
"""

from pathlib import Path
import re

print("="*80)
print("🔧 MIGRATION API STATUS")
print("="*80)

# Chemins
source = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/99_API_Status.py")
target = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/streamlit_app/pages/3_API_Status.py")

print(f"\n📋 Source: {source.name}")
print(f"📋 Cible: pages/3_API_Status.py")

if not source.exists():
    print(f"\n❌ Source introuvable")
    exit(1)

# Confirmation
proceed = input("\n👉 Migrer API Status ? (oui/non): ").strip().lower()

if proceed != "oui":
    print("\n❌ Annulé")
    exit(0)

# Lire
content = source.read_text()

print("\n🔧 Adaptations...")

# 1. Adapter imports
import_section = '''import streamlit as st
import duckdb
import sys
from pathlib import Path
from datetime import datetime
import os

# Imports nouvelle structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
import config

# DB via config
DB_PATH = config.DB_PATH
'''

# Remplacer imports
content = re.sub(
    r'import streamlit.*?(?=\n\n# |st\.set_page_config)',
    import_section.strip() + '\n\n',
    content,
    flags=re.DOTALL
)

# 2. Remplacer chemins DB
content = re.sub(
    r'DB_PATH\s*=\s*.*?warehouse\.duckdb["\']',
    'DB_PATH = config.DB_PATH',
    content
)

# 3. Remplacer prices_1m par prices_bern
content = content.replace('FROM prices_1m', 'FROM prices_bern')
content = content.replace('prices_1m', 'prices_bern')

# 4. Ajouter note
header = '''"""
API Status & Smoke Tests
=========================

Version 4.0 - Nouvelle structure eurusd_clean

Tests:
- Connexion DB
- Clés API (EODHD, TradingEconomics)
- Structure tables
- Vue prices_bern
"""

'''

content = header + content

# Écrire
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(content)

print(f"✅ API Status migré")
print(f"   Taille: {target.stat().st_size / 1024:.1f} KB")

print("\n" + "="*80)
print("✅ MIGRATION API STATUS TERMINÉE")
print("="*80)
