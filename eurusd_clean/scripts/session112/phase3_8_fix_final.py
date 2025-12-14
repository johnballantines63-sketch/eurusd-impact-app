#!/usr/bin/env python3
"""
FIX FINAL IMPORTS - Phase 3
============================

Corrige les derniers imports manquants:
1. Planificateur V2: Copie single_wave_strong.py + fix import
2. API Status: Ajoute from datetime import date

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

from pathlib import Path
import shutil

print("="*80)
print("🔧 FIX FINAL IMPORTS")
print("="*80)

eurusd_clean = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean")

# ══════════════════════════════════════════════════════════════════════
# 1. COPIER single_wave_strong.py
# ══════════════════════════════════════════════════════════════════════

print("\n📦 1. Copie single_wave_strong.py...")

source = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src/single_wave_strong.py")
target = eurusd_clean / "src/core/single_wave_strong.py"

if source.exists():
    shutil.copy2(source, target)
    size_kb = target.stat().st_size / 1024
    print(f"✅ single_wave_strong.py copié ({size_kb:.1f} KB)")
else:
    print(f"❌ Source introuvable")

# ══════════════════════════════════════════════════════════════════════
# 2. FIX IMPORT PLANIFICATEUR V2
# ══════════════════════════════════════════════════════════════════════

print("\n🎯 2. Fix import Planificateur V2...")

planif = eurusd_clean / "streamlit_app/pages/2_Planificateur_V2.py"

if planif.exists():
    content = planif.read_text()
    
    # Remplacer import
    content = content.replace(
        'from single_wave_strong import',
        'from core.single_wave_strong import'
    )
    
    planif.write_text(content)
    print("✅ Planificateur V2 corrigé")
else:
    print("❌ Planificateur introuvable")

# ══════════════════════════════════════════════════════════════════════
# 3. FIX IMPORT API STATUS (datetime.date)
# ══════════════════════════════════════════════════════════════════════

print("\n🔧 3. Fix import API Status...")

api_status = eurusd_clean / "streamlit_app/pages/3_API_Status.py"

if api_status.exists():
    content = api_status.read_text()
    
    # Trouver la ligne avec imports
    lines = content.split('\n')
    
    # Chercher ligne avec "from datetime import"
    found_datetime = False
    for i, line in enumerate(lines):
        if 'from datetime import datetime' in line and 'date' not in line:
            # Ajouter date à l'import
            lines[i] = line.replace('from datetime import datetime', 'from datetime import datetime, date')
            found_datetime = True
            break
        elif 'import datetime' in line and 'from datetime' not in line:
            # Si juste "import datetime", ajouter ligne
            lines.insert(i+1, 'from datetime import date')
            found_datetime = True
            break
    
    if not found_datetime:
        # Ajouter après imports existants
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                continue
            else:
                lines.insert(i, 'from datetime import datetime, date')
                break
    
    content = '\n'.join(lines)
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
  ✅ single_wave_strong.py copié
  ✅ Planificateur: from core.single_wave_strong import ...
  ✅ API Status: from datetime import date

🔄 Prochaine étape:
   python scripts/session112/TEST_FINAL_app_complete.py
""")

print("="*80)
