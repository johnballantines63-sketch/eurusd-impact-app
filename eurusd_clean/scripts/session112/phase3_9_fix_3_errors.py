#!/usr/bin/env python3
"""
FIX 3 ERREURS FINALES - Phase 3
================================

Corrige les 3 dernières erreurs:
1. Calendrier: empirical_impact → empirical_score
2. Planificateur: Connexions DB multiples
3. API Status: get_eod_key() non définie

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

from pathlib import Path
import re

print("="*80)
print("🔧 FIX 3 ERREURS FINALES")
print("="*80)

eurusd_clean = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean")

# ══════════════════════════════════════════════════════════════════════
# 1. FIX CALENDRIER - empirical_impact
# ══════════════════════════════════════════════════════════════════════

print("\n📅 1. Fix Calendrier Trading (empirical_impact)...")

calendrier = eurusd_clean / "streamlit_app/pages/1_Calendrier_Trading.py"

if calendrier.exists():
    content = calendrier.read_text()
    
    # Remplacer empirical_impact par empirical_score partout
    count = content.count('empirical_impact')
    content = content.replace('empirical_impact', 'empirical_score')
    
    calendrier.write_text(content)
    print(f"✅ Calendrier corrigé ({count} occurrences)")
else:
    print("❌ Calendrier introuvable")

# ══════════════════════════════════════════════════════════════════════
# 2. FIX PLANIFICATEUR - Connexions DB
# ══════════════════════════════════════════════════════════════════════

print("\n🎯 2. Fix Planificateur V2 (connexions DB)...")

planif = eurusd_clean / "streamlit_app/pages/2_Planificateur_V2.py"

if planif.exists():
    content = planif.read_text()
    
    # Chercher la fonction get_db_connection
    # Remplacer read_only=True par read_only=False pour éviter conflits
    # OU mieux : utiliser une connexion partagée
    
    # Pattern pour trouver get_db_connection
    old_pattern = r'def get_db_connection\(\):[^}]+return duckdb\.connect\(str\(db_path\), read_only=True\)'
    
    new_func = '''def get_db_connection():
    """Connexion DB partagée (sans read_only pour éviter conflits)"""
    db_path = DB_PATH
    if not db_path.exists():
        raise FileNotFoundError(f"DB introuvable: {db_path}")
    # Sans read_only pour éviter conflits multi-connexions
    return duckdb.connect(str(db_path))'''
    
    content = re.sub(old_pattern, new_func, content, flags=re.DOTALL)
    
    # Aussi remplacer toutes les occurrences directes
    content = content.replace('duckdb.connect(str(db_path), read_only=True)', 'duckdb.connect(str(db_path))')
    content = content.replace('duckdb.connect(str(DB_PATH), read_only=True)', 'duckdb.connect(str(DB_PATH))')
    
    planif.write_text(content)
    print("✅ Planificateur corrigé (connexions DB)")
else:
    print("❌ Planificateur introuvable")

# ══════════════════════════════════════════════════════════════════════
# 3. FIX API STATUS - get_eod_key()
# ══════════════════════════════════════════════════════════════════════

print("\n🔧 3. Fix API Status (get_eod_key)...")

api_status = eurusd_clean / "streamlit_app/pages/3_API_Status.py"

if api_status.exists():
    content = api_status.read_text()
    
    # Remplacer get_eod_key() par os.getenv("EODHD_API_KEY")
    content = content.replace('get_eod_key()', 'os.getenv("EODHD_API_KEY")')
    
    # Même chose pour get_te_key si présent
    content = content.replace('get_te_key()', 'os.getenv("TE_API_KEY")')
    
    api_status.write_text(content)
    print("✅ API Status corrigé (clés API)")
else:
    print("❌ API Status introuvable")

# ══════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("✅ 3 CORRECTIONS APPLIQUÉES")
print("="*80)

print("""
Corrections:
  ✅ Calendrier: empirical_impact → empirical_score
  ✅ Planificateur: Connexions DB sans read_only
  ✅ API Status: get_eod_key() → os.getenv()

🔄 Prochaine étape:
   python scripts/session112/TEST_FINAL_app_complete.py
""")

print("="*80)
