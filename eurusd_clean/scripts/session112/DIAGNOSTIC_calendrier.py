#!/usr/bin/env python3
"""
DIAGNOSTIC COMPLET CALENDRIER
==============================

Trouve TOUTES les lignes problématiques.
"""

from pathlib import Path
import re

calendrier = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/streamlit_app/pages/1_Calendrier_Trading.py")

content = calendrier.read_text()
lines = content.split('\n')

print("="*80)
print("🔍 DIAGNOSTIC CALENDRIER TRADING")
print("="*80)

# 1. Chercher .fetchone()[0]
print("\n1️⃣ Recherche .fetchone()[0] :")
for i, line in enumerate(lines, 1):
    if '.fetchone()[0]' in line:
        print(f"   Ligne {i}: {line.strip()}")

# 2. Chercher .fetchall()[0]
print("\n2️⃣ Recherche .fetchall()[0] :")
for i, line in enumerate(lines, 1):
    if '.fetchall()[0]' in line:
        print(f"   Ligne {i}: {line.strip()}")

# 3. Chercher fonction cassée
print("\n3️⃣ Fonction load_precomputed_stats_from_db :")
if 'def load_precomputed_stats_from_db' in content:
    print("   ✅ Trouvée")
    if 'event_families' in content:
        print("   ⚠️ Utilise table 'event_families' (peut ne pas exister)")
    if 'empirical_score, empirical_score' in content:
        print("   ❌ ERREUR: Colonnes dupliquées dans SELECT")
else:
    print("   ❌ Non trouvée")

# 4. Chercher variables event_title
print("\n4️⃣ Variables mal nommées :")
problematic_vars = [
    'future_event_title_titles',
    'event_title_titles',
    'high_event_title_titles',
    'today_event_title_titles'
]
for var in problematic_vars:
    if var in content:
        count = content.count(var)
        print(f"   ⚠️ {var}: {count} occurrences")

# 5. Compter lignes code
print("\n5️⃣ Statistiques :")
print(f"   Total lignes: {len(lines)}")
print(f"   Imports: {len([l for l in lines if l.strip().startswith('import ') or l.strip().startswith('from ')])}")

print("\n" + "="*80)
print("FIN DIAGNOSTIC")
print("="*80)
