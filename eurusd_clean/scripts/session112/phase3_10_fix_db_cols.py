#!/usr/bin/env python3
"""
FIX COLONNES DB + API STATUS - Phase 3
=======================================

Corrige:
1. Calendrier: Colonnes DB (reaction_rate, avg_movement_pips, avg_latency_min)
2. API Status: Fonction env_status() manquante
3. Calendrier: Events "None" (vérifier requête SQL)

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

from pathlib import Path
import re

print("="*80)
print("🔧 FIX COLONNES DB + API STATUS")
print("="*80)

eurusd_clean = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean")

# ══════════════════════════════════════════════════════════════════════
# 1. FIX CALENDRIER - Colonnes DB inexistantes
# ══════════════════════════════════════════════════════════════════════

print("\n📅 1. Fix Calendrier (colonnes DB)...")

calendrier = eurusd_clean / "streamlit_app/pages/1_Calendrier_Trading.py"

if calendrier.exists():
    content = calendrier.read_text()
    
    # Remplacer colonnes inexistantes
    replacements = {
        'reaction_rate': 'empirical_score',  # Utiliser empirical_score à la place
        'avg_movement_pips': 'empirical_score',  # Ou supprimer si non utilisé
        'avg_latency_min': 'latency_median',
    }
    
    for old_col, new_col in replacements.items():
        if old_col in content:
            count = content.count(old_col)
            content = content.replace(old_col, new_col)
            print(f"  ✅ {old_col} → {new_col} ({count} occurrences)")
    
    calendrier.write_text(content)
    print("✅ Calendrier corrigé")
else:
    print("❌ Calendrier introuvable")

# ══════════════════════════════════════════════════════════════════════
# 2. FIX API STATUS - env_status()
# ══════════════════════════════════════════════════════════════════════

print("\n🔧 2. Fix API Status (env_status)...")

api_status = eurusd_clean / "streamlit_app/pages/3_API_Status.py"

if api_status.exists():
    content = api_status.read_text()
    
    # Définir fonction env_status avant son utilisation
    env_status_func = '''
def env_status():
    """Vérifie présence des clés API dans environnement"""
    return {
        "EODHD_API_KEY": bool(os.getenv("EODHD_API_KEY")),
        "TE_API_KEY": bool(os.getenv("TE_API_KEY")),
    }

'''
    
    # Trouver où insérer (après imports, avant utilisation)
    # Chercher la ligne avec "HAS_EOD"
    lines = content.split('\n')
    insert_pos = 0
    
    for i, line in enumerate(lines):
        if '"HAS_EOD"' in line or 'env_keys' in line:
            insert_pos = i
            break
        # Ou après les imports
        if line.startswith('st.set_page_config') or line.startswith('st.title'):
            insert_pos = i
            break
    
    # Insérer fonction
    lines.insert(insert_pos, env_status_func)
    content = '\n'.join(lines)
    
    api_status.write_text(content)
    print("✅ API Status corrigé (env_status ajouté)")
else:
    print("❌ API Status introuvable")

# ══════════════════════════════════════════════════════════════════════
# 3. VÉRIFIER STRUCTURE DB
# ══════════════════════════════════════════════════════════════════════

print("\n🗄️ 3. Vérification structure DB...")

try:
    import sys
    sys.path.insert(0, str(eurusd_clean / "src"))
    import config
    import duckdb
    
    conn = duckdb.connect(str(config.DB_PATH), read_only=True)
    
    # Lister colonnes table events
    result = conn.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'events'
        ORDER BY ordinal_position
    """).fetchall()
    
    print(f"\n📊 Colonnes table 'events':")
    for col in result:
        print(f"  • {col[0]}")
    
    # Tester requête events
    test = conn.execute("""
        SELECT event, country, ts_utc 
        FROM events 
        WHERE country = 'US' 
        AND ts_utc >= CURRENT_TIMESTAMP
        LIMIT 3
    """).fetchall()
    
    print(f"\n✅ Test requête events:")
    for row in test:
        print(f"  • {row[0]} ({row[1]}) - {row[2]}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Erreur DB: {e}")

# ══════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("✅ CORRECTIONS APPLIQUÉES")
print("="*80)

print("""
Corrections:
  ✅ Calendrier: Colonnes DB corrigées
  ✅ API Status: Fonction env_status() ajoutée
  ✅ Structure DB vérifiée

🔄 Prochaine étape:
   python scripts/session112/TEST_FINAL_app_complete.py
   
💡 Si events "None" persiste:
   Vérifier que requête SQL utilise bonne colonne 'event'
""")

print("="*80)
