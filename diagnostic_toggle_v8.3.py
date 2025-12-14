#!/usr/bin/env python3
"""
Script de diagnostic pour identifier pourquoi le toggle séquentiel n'apparaît pas
"""

import sys
import os

# Ajouter les paths nécessaires
project_root = "/Users/andrevalentin/Projects/eurusd_news_impact_calculator"
sys.path.insert(0, os.path.join(project_root, "fx_impact_app/src"))
sys.path.insert(0, os.path.join(project_root, "fx_impact_app/streamlit_app/components"))

print("=" * 70)
print("🔍 DIAGNOSTIC TOGGLE SÉQUENTIEL v8.3")
print("=" * 70)

# Test 1 : Vérifier existence des fichiers
print("\n📁 TEST 1 : Vérification des fichiers")
print("-" * 70)

files_to_check = [
    "fx_impact_app/src/sequence_multi_event_timeline.py",
    "fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py",
    "fx_impact_app/streamlit_app/components/__init__.py"
]

all_files_exist = True
for file_path in files_to_check:
    full_path = os.path.join(project_root, file_path)
    exists = os.path.exists(full_path)
    status = "✅" if exists else "❌"
    print(f"{status} {file_path}")
    if exists:
        size = os.path.getsize(full_path)
        print(f"   Taille : {size:,} octets")
    else:
        all_files_exist = False

# Test 2 : Tester les imports
print("\n🔧 TEST 2 : Test des imports")
print("-" * 70)

try:
    from sequence_multi_event_timeline import (
        sequence_multi_event_timeline,
        calculate_sequential_metrics,
        calculate_phase_backtest_error,
        calculate_sequential_mae
    )
    print("✅ Import sequence_multi_event_timeline : SUCCÈS")
    print(f"   - sequence_multi_event_timeline : {type(sequence_multi_event_timeline)}")
    print(f"   - calculate_sequential_metrics : {type(calculate_sequential_metrics)}")
except ImportError as e:
    print(f"❌ Import sequence_multi_event_timeline : ÉCHEC")
    print(f"   Erreur : {e}")

try:
    from streamlit_sequential_ui import (
        display_sequential_timeline,
        display_backtest_comparison
    )
    print("✅ Import streamlit_sequential_ui : SUCCÈS")
    print(f"   - display_sequential_timeline : {type(display_sequential_timeline)}")
    print(f"   - display_backtest_comparison : {type(display_backtest_comparison)}")
except ImportError as e:
    print(f"❌ Import streamlit_sequential_ui : ÉCHEC")
    print(f"   Erreur : {e}")

# Test 3 : Vérifier le fichier principal
print("\n📄 TEST 3 : Analyse du fichier principal")
print("-" * 70)

main_file = os.path.join(project_root, "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
if os.path.exists(main_file):
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"✅ Fichier trouvé : {len(content)} caractères, {content.count(chr(10))} lignes")
    
    # Chercher les imports
    if "from sequence_multi_event_timeline import" in content:
        print("✅ Import sequence_multi_event_timeline trouvé dans le code")
    else:
        print("❌ Import sequence_multi_event_timeline ABSENT du code")
    
    if "from streamlit_sequential_ui import" in content:
        print("✅ Import streamlit_sequential_ui trouvé dans le code")
    else:
        print("❌ Import streamlit_sequential_ui ABSENT du code")
    
    # Chercher le toggle
    if "Activer le Mode Timeline Séquentielle" in content:
        print("✅ Toggle 'Activer le Mode Timeline Séquentielle' trouvé dans le code")
        # Trouver la ligne
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if "Activer le Mode Timeline Séquentielle" in line:
                print(f"   Ligne {i} : {line.strip()}")
    else:
        print("❌ Toggle 'Activer le Mode Timeline Séquentielle' ABSENT du code")
    
    # Chercher SEQUENTIAL_MODE_AVAILABLE
    if "SEQUENTIAL_MODE_AVAILABLE" in content:
        print("✅ Variable SEQUENTIAL_MODE_AVAILABLE trouvée dans le code")
        # Compter occurrences
        count = content.count("SEQUENTIAL_MODE_AVAILABLE")
        print(f"   Occurrences : {count}")
    else:
        print("❌ Variable SEQUENTIAL_MODE_AVAILABLE ABSENTE du code")
    
    # Chercher le try/except d'import
    if "try:" in content and "except ImportError" in content:
        print("✅ Bloc try/except trouvé (gestion imports)")
    else:
        print("⚠️ Aucun bloc try/except pour gérer les imports")

else:
    print(f"❌ Fichier principal non trouvé : {main_file}")

# Test 4 : Vérifier la structure du code
print("\n🔍 TEST 4 : Recherche de la section toggle")
print("-" * 70)

if os.path.exists(main_file):
    with open(main_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Chercher "Analyse Multi-Événements Complète"
    section_found = False
    for i, line in enumerate(lines, 1):
        if "Analyse Multi-Événements Complète" in line:
            section_found = True
            print(f"✅ Section trouvée ligne {i}")
            print(f"\nContexte (lignes {max(1, i-5)} à {min(len(lines), i+20)}) :")
            print("-" * 70)
            for j in range(max(0, i-6), min(len(lines), i+20)):
                marker = ">>>" if j == i-1 else "   "
                print(f"{marker} {j+1:4d} | {lines[j].rstrip()}")
            break
    
    if not section_found:
        print("❌ Section 'Analyse Multi-Événements Complète' non trouvée")

# Résumé final
print("\n" + "=" * 70)
print("📊 RÉSUMÉ DU DIAGNOSTIC")
print("=" * 70)

if all_files_exist:
    print("✅ Tous les fichiers requis existent")
else:
    print("❌ Il manque des fichiers requis")

print("\n💡 RECOMMANDATIONS :")
print("-" * 70)
print("1. Vérifier que les imports sont bien AVANT la section 'Analyse Multi-Événements'")
print("2. Vérifier que le toggle est bien dans le bloc 'if SEQUENTIAL_MODE_AVAILABLE:'")
print("3. Ajouter des st.write() de debug juste avant le toggle pour voir ce qui bloque")
print("4. Redémarrer Streamlit avec 'streamlit cache clear' puis relancer")
print("\n" + "=" * 70)
