#!/usr/bin/env python3
"""
Script de validation des corrections Session 42
Vérifie que les 2 corrections sont bien appliquées
"""
import re

filepath = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Compter définitions
def_count = len(re.findall(r'def load_precomputed_stats_from_db', content))

# Compter appels  
call_count = len(re.findall(r'load_precomputed_stats_from_db\(\)', content))

# Double clé
has_double_key = "stats_dict[family_db.replace('_', ' ')] = stats" in content

# Pré-chargement
has_preload = "if 'preloaded' not in st.session_state:" in content

# Lignes totales
total_lines = len(content.split('\n'))

print('=' * 60)
print('📊 VALIDATION CORRECTIONS SESSION 42')
print('=' * 60)
print()
print(f'📄 Fichier: 4_Planificateur_STABLE_0159_PERFECT.py')
print(f'📏 Lignes totales: {total_lines}')
print()
print('🔍 CORRECTION #1 : Ordre de définition')
print('-' * 60)
print(f'  Définitions fonction: {def_count}')
print(f'  Appels fonction: {call_count}')
print(f'  Status: {"✅ OK (pas de duplication)" if def_count == 1 else "❌ KO (duplication !)"}')
print()
print('🔍 CORRECTION #2 : Double clé Current Account')
print('-' * 60)
print(f'  Double clé présente: {"✅ OUI" if has_double_key else "❌ NON"}')
print(f'  Status: {"✅ OK" if has_double_key else "❌ KO"}')
print()
print('🔍 PRÉ-CHARGEMENT : Bloc au démarrage')
print('-' * 60)
print(f'  Bloc preloaded présent: {"✅ OUI" if has_preload else "❌ NON"}')
print(f'  Status: {"✅ OK" if has_preload else "❌ KO"}')
print()
print('=' * 60)
print('📋 RÉCAPITULATIF')
print('=' * 60)
all_ok = def_count == 1 and has_double_key and has_preload
print(f'  Correction #1 (ordre):       {"✅" if def_count == 1 else "❌"}')
print(f'  Correction #2 (double clé):  {"✅" if has_double_key else "❌"}')
print(f'  Pré-chargement:              {"✅" if has_preload else "❌"}')
print()
if all_ok:
    print('🎉 TOUTES LES CORRECTIONS SESSION 42 VALIDÉES !')
    print('✅ Le fichier est prêt pour le test Streamlit')
    exit(0)
else:
    print('⚠️  Problèmes détectés dans le fichier')
    exit(1)
print('=' * 60)
