#!/usr/bin/env python3
"""
Ajoute des messages de debug visibles dans l'interface Streamlit
"""

import os
from datetime import datetime

project_root = "/Users/andrevalentin/Projects/eurusd_news_impact_calculator"
target_file = os.path.join(project_root, "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")

print("=" * 70)
print("🔧 AJOUT DEBUG STREAMLIT v8.3")
print("=" * 70)

# Backup
backup_file = target_file + f".bak_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Backup créé : {os.path.basename(backup_file)}")

# Modification 1 : Ajouter debug après le bloc d'import
old_block_1 = """except ImportError as e:
    SEQUENTIAL_MODE_AVAILABLE = False
    import traceback
    print(f"❌ Import séquentiel échoué: {e}")
    print(traceback.format_exc())


st.set_page_config(page_title="Planificateur Multi-Événements", page_icon="📅", layout="wide")"""

new_block_1 = """except ImportError as e:
    SEQUENTIAL_MODE_AVAILABLE = False
    import traceback
    print(f"❌ Import séquentiel échoué: {e}")
    print(traceback.format_exc())


st.set_page_config(page_title="Planificateur Multi-Événements", page_icon="📅", layout="wide")

# ═══════════════════════════════════════════════════════════════
# 🔍 DEBUG MODE SÉQUENTIEL (TEMPORAIRE)
# ═══════════════════════════════════════════════════════════════
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Debug Mode Séquentiel")
if SEQUENTIAL_MODE_AVAILABLE:
    st.sidebar.success(f"✅ AVAILABLE = True")
else:
    st.sidebar.error(f"❌ AVAILABLE = False")
st.sidebar.caption(f"Python: {sys.version.split()[0]}")
# ═══════════════════════════════════════════════════════════════"""

if old_block_1 in content:
    content = content.replace(old_block_1, new_block_1)
    print("✅ Debug #1 ajouté : Sidebar avec statut SEQUENTIAL_MODE_AVAILABLE")
else:
    print("⚠️ Modification #1 impossible : bloc introuvable")

# Modification 2 : Ajouter debug juste avant le toggle
old_block_2 = """            st.divider()
            st.header("🎲 Analyse Multi-Événements Complète")
            
            # ═══════════════════════════════════════════════════════════
            # 🆕 NOUVEAU v8.3 : TOGGLE TIMELINE SÉQUENTIELLE
            # ═══════════════════════════════════════════════════════════
            
            if SEQUENTIAL_MODE_AVAILABLE:"""

new_block_2 = """            st.divider()
            st.header("🎲 Analyse Multi-Événements Complète")
            
            # ═══════════════════════════════════════════════════════════
            # 🔍 DEBUG TEMPORAIRE
            # ═══════════════════════════════════════════════════════════
            st.info(f"🔍 **DEBUG:** SEQUENTIAL_MODE_AVAILABLE = {SEQUENTIAL_MODE_AVAILABLE}")
            st.info(f"🔍 **DEBUG:** Type = {type(SEQUENTIAL_MODE_AVAILABLE)}")
            # ═══════════════════════════════════════════════════════════
            
            # ═══════════════════════════════════════════════════════════
            # 🆕 NOUVEAU v8.3 : TOGGLE TIMELINE SÉQUENTIELLE
            # ═══════════════════════════════════════════════════════════
            
            if SEQUENTIAL_MODE_AVAILABLE:"""

if old_block_2 in content:
    content = content.replace(old_block_2, new_block_2)
    print("✅ Debug #2 ajouté : Messages avant le toggle")
else:
    print("⚠️ Modification #2 impossible : bloc introuvable")

# Modification 3 : Ajouter else visible si SEQUENTIAL_MODE_AVAILABLE = False
old_block_3 = """            if SEQUENTIAL_MODE_AVAILABLE:
                st.markdown("---")
                
                col_toggle, col_info = st.columns([3, 1])"""

new_block_3 = """            if SEQUENTIAL_MODE_AVAILABLE:
                st.markdown("---")
                
                col_toggle, col_info = st.columns([3, 1])"""

# Pas de modification ici, on veut juste voir le debug

# Sauvegarder
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Fichier sauvegardé")

# Vérification
print("\n" + "=" * 70)
print("🔍 VÉRIFICATION")
print("=" * 70)

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Chercher les debug
debug_count = 0
for i, line in enumerate(lines, 1):
    if '🔍 DEBUG' in line or '🔍 Debug' in line:
        debug_count += 1
        print(f"Ligne {i}: {line.rstrip()}")

if debug_count > 0:
    print(f"\n✅ {debug_count} lignes de debug ajoutées")
else:
    print("\n⚠️ Aucune ligne de debug trouvée")

print("\n" + "=" * 70)
print("✅ PATCH TERMINÉ")
print("=" * 70)
print("\n📋 PROCHAINES ÉTAPES :")
print("1. Redémarrer Streamlit complètement (Ctrl+C puis relancer)")
print("2. Aller sur page Planificateur Multi-Événements")
print("3. Vérifier SIDEBAR (en haut à gauche) pour le statut")
print("4. Charger des événements et vérifier les messages 🔍 DEBUG")
print("5. Nous dire ce qui s'affiche !")
print("\n💡 Si AVAILABLE = False dans Streamlit, il y a un problème d'environnement")
print("💡 Si AVAILABLE = True mais toggle absent, c'est un problème de logique de code")
