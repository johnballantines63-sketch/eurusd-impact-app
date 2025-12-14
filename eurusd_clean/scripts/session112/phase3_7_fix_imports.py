#!/usr/bin/env python3
"""
FIX IMPORTS PAGES - Phase 3
============================

Corrige les imports dans les 3 pages problématiques:
1. Calendrier Trading: Ajoute from core import ...
2. Planificateur V2: Ajoute from core import ...
3. API Status: Remplace get_db_path() par config.DB_PATH

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

from pathlib import Path
import re

print("="*80)
print("🔧 FIX IMPORTS PAGES")
print("="*80)

eurusd_clean = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean")

# ══════════════════════════════════════════════════════════════════════
# 1. FIX CALENDRIER TRADING
# ══════════════════════════════════════════════════════════════════════

print("\n📅 1. Fix Calendrier Trading...")

calendrier = eurusd_clean / "streamlit_app/pages/1_Calendrier_Trading.py"

if calendrier.exists():
    content = calendrier.read_text()
    
    # Remplacer imports
    content = content.replace(
        'from forecaster_mvp import ForecastEngine',
        'from core.forecaster_mvp import ForecastEngine'
    )
    content = content.replace(
        'from scoring_engine import ScoringEngine',
        'from core.scoring_engine import ScoringEngine'
    )
    content = content.replace(
        'from event_families import',
        'from core.event_families import'
    )
    
    # Remplacer get_db_path() par config.DB_PATH
    content = content.replace('get_db_path()', 'config.DB_PATH')
    content = content.replace('from config import get_db_path', '# from config import get_db_path')
    
    calendrier.write_text(content)
    print("✅ Calendrier Trading corrigé")
else:
    print("❌ Calendrier introuvable")

# ══════════════════════════════════════════════════════════════════════
# 2. FIX PLANIFICATEUR V2
# ══════════════════════════════════════════════════════════════════════

print("\n🎯 2. Fix Planificateur V2...")

planif = eurusd_clean / "streamlit_app/pages/2_Planificateur_V2.py"

if planif.exists():
    content = planif.read_text()
    
    # Remplacer import double_wave
    content = content.replace(
        'from double_wave import',
        'from core.double_wave import'
    )
    
    planif.write_text(content)
    print("✅ Planificateur V2 corrigé")
else:
    print("❌ Planificateur introuvable")

# ══════════════════════════════════════════════════════════════════════
# 3. FIX API STATUS
# ══════════════════════════════════════════════════════════════════════

print("\n🔧 3. Fix API Status...")

api_status = eurusd_clean / "streamlit_app/pages/3_API_Status.py"

if api_status.exists():
    content = api_status.read_text()
    
    # Remplacer get_db_path()
    content = content.replace('db = get_db_path()', 'db = config.DB_PATH')
    content = content.replace('get_db_path()', 'config.DB_PATH')
    
    api_status.write_text(content)
    print("✅ API Status corrigé")
else:
    print("❌ API Status introuvable")

# ══════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("✅ CORRECTIONS APPLIQUÉES")
print("="*80)

print("""
Modifications:
  ✅ Calendrier: from core.forecaster_mvp import ...
  ✅ Planificateur: from core.double_wave import ...
  ✅ API Status: config.DB_PATH au lieu de get_db_path()

🔄 Prochaine étape:
   1. Copier modules: python scripts/session112/phase3_6_copy_missing_modules.py
   2. Tester: python scripts/session112/TEST_FINAL_app_complete.py
""")

print("="*80)
