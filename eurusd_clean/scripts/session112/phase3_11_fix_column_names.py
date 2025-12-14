#!/usr/bin/env python3
"""
FIX NOMS COLONNES DB - Phase 3 FINAL
=====================================

Remplace dans TOUS les fichiers:
- event → event_title
- importance_eod → importance_n

Car la DB utilise ces noms de colonnes.

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

from pathlib import Path
import re

print("="*80)
print("🔧 FIX NOMS COLONNES DB - GLOBAL")
print("="*80)

eurusd_clean = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean")

files_to_fix = [
    eurusd_clean / "streamlit_app/Home.py",
    eurusd_clean / "streamlit_app/pages/1_Calendrier_Trading.py",
    eurusd_clean / "streamlit_app/pages/2_Planificateur_V2.py",
    eurusd_clean / "streamlit_app/pages/3_API_Status.py",
]

total_fixes = 0

for file_path in files_to_fix:
    if not file_path.exists():
        print(f"⏭️ {file_path.name} (n'existe pas)")
        continue
    
    print(f"\n📄 {file_path.name}...")
    
    content = file_path.read_text()
    original = content
    
    # Remplacements dans requêtes SQL et code Python
    # ATTENTION : Ne remplacer que dans contexte SQL/DB
    
    # 1. Dans SELECT clauses
    content = re.sub(
        r'\bSELECT\s+.*?\bfrom\s+events',
        lambda m: m.group(0).replace(', event,', ', event_title,')
                             .replace(' event,', ' event_title,')
                             .replace('SELECT event,', 'SELECT event_title,'),
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # 2. Références directes dans WHERE, ORDER BY, etc.
    patterns = [
        (r'\bevents\.event\b', 'events.event_title'),
        (r'\be\.event\b', 'e.event_title'),
        (r'importance_eod', 'importance_n'),
    ]
    
    for pattern, replacement in patterns:
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            print(f"  ✅ {pattern} → {replacement} ({count} occurrences)")
            total_fixes += count
    
    # 3. Dans DataFrames pandas (colonnes)
    # df['event'] → df['event_title']
    content = content.replace("['event']", "['event_title']")
    content = content.replace('["event"]', '["event_title"]')
    
    # 4. Dans f-strings et format
    content = re.sub(r"f['\"].*?{.*?event.*?}.*?['\"]", 
                     lambda m: m.group(0).replace('event', 'event_title'), 
                     content)
    
    if content != original:
        file_path.write_text(content)
        print(f"  💾 Fichier mis à jour")
    else:
        print(f"  ⏭️ Aucun changement")

print("\n" + "="*80)
print("✅ CORRECTIONS TERMINÉES")
print("="*80)

print(f"""
📊 Total modifications: {total_fixes}

Colonnes corrigées:
  ✅ event → event_title
  ✅ importance_eod → importance_n

🔄 Prochaine étape:
   1. python scripts/session112/DIAGNOSTIC_db.py
   2. python scripts/session112/TEST_FINAL_app_complete.py
""")

print("="*80)
