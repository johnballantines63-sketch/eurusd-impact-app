#!/usr/bin/env python3
"""
Diagnostic approfondi du système de timeline séquentielle
"""

import sys
import os
from pathlib import Path

project_root = "/Users/andrevalentin/Projects/eurusd_news_impact_calculator"
os.chdir(project_root)

print("=" * 80)
print("🔬 DIAGNOSTIC APPROFONDI - TIMELINE SÉQUENTIELLE v8.3")
print("=" * 80)

# ========== TEST 1 : Vérifier les fichiers ==========
print("\n📁 TEST 1 : Fichiers requis")
print("-" * 80)

files_check = {
    'sequence_multi_event_timeline.py': 'fx_impact_app/src/sequence_multi_event_timeline.py',
    'streamlit_sequential_ui.py': 'fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py',
    '__init__.py (components)': 'fx_impact_app/streamlit_app/components/__init__.py',
    'Page principale': 'fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py'
}

for name, path in files_check.items():
    full_path = os.path.join(project_root, path)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        print(f"✅ {name}: {size:,} octets")
    else:
        print(f"❌ {name}: FICHIER MANQUANT")

# ========== TEST 2 : Lire le contenu de sequence_multi_event_timeline.py ==========
print("\n📄 TEST 2 : Contenu de sequence_multi_event_timeline.py")
print("-" * 80)

seq_file = os.path.join(project_root, 'fx_impact_app/src/sequence_multi_event_timeline.py')
if os.path.exists(seq_file):
    with open(seq_file, 'r', encoding='utf-8') as f:
        seq_content = f.read()
    
    # Extraire les définitions de fonctions
    import re
    functions = re.findall(r'^def (\w+)\s*\(', seq_content, re.MULTILINE)
    
    print(f"Nombre de lignes : {len(seq_content.splitlines())}")
    print(f"Nombre de fonctions : {len(functions)}")
    print("\nFonctions définies :")
    for func in functions:
        print(f"  ✅ {func}")
    
    # Vérifier les fonctions requises
    print("\nVérification des imports attendus :")
    required = ['sequence_multi_event_timeline', 'calculate_sequential_metrics', 
                'calculate_phase_backtest_error', 'calculate_sequential_mae']
    for req in required:
        if req in functions:
            print(f"  ✅ {req} : EXISTE")
        else:
            print(f"  ❌ {req} : MANQUANT")
else:
    print("❌ Fichier sequence_multi_event_timeline.py non trouvé")

# ========== TEST 3 : Tester les imports en direct ==========
print("\n🔧 TEST 3 : Test d'import en direct")
print("-" * 80)

sys.path.insert(0, os.path.join(project_root, 'fx_impact_app/src'))
sys.path.insert(0, os.path.join(project_root, 'fx_impact_app/streamlit_app/components'))

print("Chemin Python étendu:")
print(f"  - {os.path.join(project_root, 'fx_impact_app/src')}")
print(f"  - {os.path.join(project_root, 'fx_impact_app/streamlit_app/components')}")

print("\n🧪 Tentative d'import sequence_multi_event_timeline...")
try:
    import sequence_multi_event_timeline as seq_module
    print("✅ Import du module réussi")
    
    # Lister tous les attributs du module
    attrs = [a for a in dir(seq_module) if not a.startswith('_')]
    print(f"\n📋 Attributs exportés par le module ({len(attrs)}) :")
    for attr in attrs:
        obj = getattr(seq_module, attr)
        obj_type = type(obj).__name__
        print(f"  - {attr} : {obj_type}")
    
    # Vérifier les fonctions spécifiques
    print("\n🔍 Vérification des fonctions attendues :")
    for func_name in ['sequence_multi_event_timeline', 'calculate_sequential_metrics', 
                      'calculate_phase_backtest_error', 'calculate_sequential_mae']:
        if hasattr(seq_module, func_name):
            func = getattr(seq_module, func_name)
            print(f"  ✅ {func_name} : {type(func).__name__}")
        else:
            print(f"  ❌ {func_name} : MANQUANT")
    
except ImportError as e:
    print(f"❌ Import échoué: {e}")
    import traceback
    print("\n📋 Traceback complet :")
    print(traceback.format_exc())

print("\n🧪 Tentative d'import streamlit_sequential_ui...")
try:
    import streamlit_sequential_ui as ui_module
    print("✅ Import du module réussi")
    
    # Lister fonctions
    attrs = [a for a in dir(ui_module) if not a.startswith('_')]
    print(f"\n📋 Attributs exportés ({len(attrs)}) :")
    for attr in attrs:
        obj = getattr(ui_module, attr)
        obj_type = type(obj).__name__
        print(f"  - {attr} : {obj_type}")
    
except ImportError as e:
    print(f"❌ Import échoué: {e}")
    import traceback
    print("\n📋 Traceback :")
    print(traceback.format_exc())

# ========== TEST 4 : Analyser le fichier principal ==========
print("\n📄 TEST 4 : Analyse du fichier principal")
print("-" * 80)

main_file = os.path.join(project_root, 'fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py')
with open(main_file, 'r', encoding='utf-8') as f:
    main_content = f.read()
    main_lines = main_content.splitlines()

# Trouver le bloc d'import
print("🔍 Recherche du bloc d'import...")
for i, line in enumerate(main_lines, 1):
    if 'from sequence_multi_event_timeline import' in line:
        print(f"\n✅ Bloc d'import trouvé ligne {i}:")
        # Afficher 15 lignes de contexte
        start = max(0, i - 3)
        end = min(len(main_lines), i + 12)
        for j in range(start, end):
            marker = ">>>" if j == i - 1 else "   "
            print(f"{marker} {j+1:4d} | {main_lines[j]}")
        break
else:
    print("❌ Bloc d'import non trouvé dans le fichier principal")

# Chercher SEQUENTIAL_MODE_AVAILABLE
print("\n🔍 Recherche de SEQUENTIAL_MODE_AVAILABLE...")
count = main_content.count('SEQUENTIAL_MODE_AVAILABLE')
print(f"Occurrences : {count}")

for i, line in enumerate(main_lines, 1):
    if 'SEQUENTIAL_MODE_AVAILABLE' in line:
        print(f"  Ligne {i}: {line.strip()}")

# Chercher le toggle
print("\n🔍 Recherche du toggle...")
for i, line in enumerate(main_lines, 1):
    if 'Activer le Mode Timeline Séquentielle' in line:
        print(f"✅ Toggle trouvé ligne {i}")
        # Contexte
        start = max(0, i - 5)
        end = min(len(main_lines), i + 5)
        for j in range(start, end):
            marker = ">>>" if j == i - 1 else "   "
            print(f"{marker} {j+1:4d} | {main_lines[j]}")
        break

# ========== TEST 5 : Simuler l'import comme Streamlit ==========
print("\n🔬 TEST 5 : Simulation import comme Streamlit")
print("-" * 80)

print("Exécution du bloc try/except exact du fichier principal...")

SEQUENTIAL_MODE_AVAILABLE = False

try:
    # Nettoyer les imports précédents
    if 'sequence_multi_event_timeline' in sys.modules:
        del sys.modules['sequence_multi_event_timeline']
    if 'streamlit_sequential_ui' in sys.modules:
        del sys.modules['streamlit_sequential_ui']
    
    # Essayer l'import tel quel dans le fichier
    from sequence_multi_event_timeline import sequence_multi_event_timeline
    from streamlit_sequential_ui import display_sequential_timeline
    
    SEQUENTIAL_MODE_AVAILABLE = True
    print("✅ Import réussi !")
    print(f"   sequence_multi_event_timeline : {type(sequence_multi_event_timeline)}")
    print(f"   display_sequential_timeline : {type(display_sequential_timeline)}")
    
except ImportError as e:
    print(f"❌ Import échoué: {e}")
    import traceback
    print("\n📋 Traceback :")
    traceback.print_exc()

print(f"\n📊 Résultat : SEQUENTIAL_MODE_AVAILABLE = {SEQUENTIAL_MODE_AVAILABLE}")

# ========== RÉSUMÉ ==========
print("\n" + "=" * 80)
print("📊 RÉSUMÉ DU DIAGNOSTIC")
print("=" * 80)

print("\n💡 RECOMMANDATIONS :")
print("-" * 80)

if SEQUENTIAL_MODE_AVAILABLE:
    print("✅ Les imports fonctionnent en standalone")
    print("⚠️ Le problème est donc dans l'environnement Streamlit")
    print("\n🔧 Solutions possibles :")
    print("1. Ajouter des print() de debug dans le fichier principal")
    print("2. Vérifier que Streamlit utilise le bon environnement Python")
    print("3. Forcer un rechargement complet : streamlit cache clear")
else:
    print("❌ Les imports échouent même en standalone")
    print("\n🔧 Actions requises :")
    print("1. Vérifier que les fichiers sont bien où ils doivent être")
    print("2. Vérifier le contenu des modules")
    print("3. Corriger les imports dans le fichier principal")

print("\n" + "=" * 80)
