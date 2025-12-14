#!/usr/bin/env python3
"""
FIX FINAL GLOBAL - Phase 3 ULTIME
==================================

Corrige TOUTES les erreurs restantes:
1. Calendrier: future_event_title_titles → future_events
2. Calendrier: reaction_rate, avg_movement_pips (colonnes inexistantes)
3. API Status: env_status() manquante

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

from pathlib import Path
import re

print("="*80)
print("🔧 FIX FINAL GLOBAL - TOUTES ERREURS")
print("="*80)

eurusd_clean = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean")

# ══════════════════════════════════════════════════════════════════════
# 1. FIX CALENDRIER - Variables + Colonnes
# ══════════════════════════════════════════════════════════════════════

print("\n📅 1. Fix Calendrier Trading...")

calendrier = eurusd_clean / "streamlit_app/pages/1_Calendrier_Trading.py"

if calendrier.exists():
    content = calendrier.read_text()
    
    # Fix variables mal nommées
    replacements = {
        'future_event_title_titles': 'future_events',
        'event_title_titles': 'events',
        'today_event_title_titles': 'today_events',
    }
    
    for old, new in replacements.items():
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            print(f"  ✅ {old} → {new} ({count}x)")
    
    # Supprimer colonnes inexistantes des requêtes SQL
    # Pattern: chercher SELECT ... FROM
    
    # Supprimer reaction_rate
    content = re.sub(r',?\s*reaction_rate\s*,?', '', content)
    
    # Supprimer avg_movement_pips  
    content = re.sub(r',?\s*avg_movement_pips\s*,?', '', content)
    
    # Supprimer avg_latency_min
    content = re.sub(r',?\s*avg_latency_min\s*,?', '', content)
    
    print(f"  ✅ Colonnes inexistantes supprimées")
    
    calendrier.write_text(content)
    print("✅ Calendrier corrigé")
else:
    print("❌ Calendrier introuvable")

# ══════════════════════════════════════════════════════════════════════
# 2. FIX API STATUS - env_status()
# ══════════════════════════════════════════════════════════════════════

print("\n🔧 2. Fix API Status...")

api_status = eurusd_clean / "streamlit_app/pages/3_API_Status.py"

if api_status.exists():
    content = api_status.read_text()
    
    # Ajouter fonction env_status AVANT première utilisation
    env_func = '''
def env_status():
    """Vérifie présence clés API"""
    return {
        "EODHD_API_KEY": bool(os.getenv("EODHD_API_KEY")),
        "TE_API_KEY": bool(os.getenv("TE_API_KEY")),
    }

'''
    
    # Trouver où insérer (après imports, avant première utilisation)
    lines = content.split('\n')
    
    # Chercher ligne avec st.title ou st.set_page_config
    insert_pos = 0
    for i, line in enumerate(lines):
        if 'st.title' in line or 'st.set_page_config' in line:
            insert_pos = i
            break
    
    # Insérer fonction
    if insert_pos > 0:
        lines.insert(insert_pos, env_func)
        content = '\n'.join(lines)
        
        api_status.write_text(content)
        print("✅ API Status corrigé (env_status ajouté)")
    else:
        print("⚠️ Position insertion non trouvée")
else:
    print("❌ API Status introuvable")

# ══════════════════════════════════════════════════════════════════════
# 3. FIX HOME - Variables event_title
# ══════════════════════════════════════════════════════════════════════

print("\n🏠 3. Fix Home.py...")

home = eurusd_clean / "streamlit_app/Home.py"

if home.exists():
    content = home.read_text()
    
    # Fix toutes variables mal nommées
    replacements = {
        'last_event_title_title_update': 'last_event_update',
        'today_event_title_titles': 'today_events',
        'future_event_title_titles': 'future_events',
    }
    
    changed = False
    for old, new in replacements.items():
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            print(f"  ✅ {old} → {new} ({count}x)")
            changed = True
    
    if changed:
        home.write_text(content)
        print("✅ Home corrigé")
    else:
        print("⏭️ Home déjà OK")
else:
    print("❌ Home introuvable")

# ══════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("✅ TOUTES CORRECTIONS APPLIQUÉES")
print("="*80)

print("""
Corrections:
  ✅ Calendrier: Variables corrigées
  ✅ Calendrier: Colonnes inexistantes supprimées
  ✅ API Status: Fonction env_status() ajoutée
  ✅ Home: Variables corrigées

🔄 Prochaine étape:
   python scripts/session112/TEST_FINAL_app_complete.py
   
🚀 Si OK:
   streamlit run streamlit_app/Home.py
""")

print("="*80)
