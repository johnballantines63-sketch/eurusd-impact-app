#!/usr/bin/env python3
"""
Script d'analyse du planificateur
Extrait toutes les fonctions et leur localisation
"""

import re

filepath = "fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"📏 LIGNES TOTALES: {len(lines)}")
print(f"📊 TAILLE: {sum(len(line) for line in lines):,} caractères")
print()

# Analyser chaque ligne
functions = []
in_function = None
function_start = None

for i, line in enumerate(lines, 1):
    # Détecter début de fonction
    if line.strip().startswith('def '):
        match = re.match(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)', line)
        if match:
            func_name = match.group(1)
            params = match.group(2)
            
            # Fermer fonction précédente si existe
            if in_function:
                functions.append({
                    'name': in_function,
                    'start': function_start,
                    'end': i - 1,
                    'lines': i - 1 - function_start + 1
                })
            
            in_function = func_name
            function_start = i

# Fermer dernière fonction
if in_function:
    functions.append({
        'name': in_function,
        'start': function_start,
        'end': len(lines),
        'lines': len(lines) - function_start + 1
    })

print(f"🔧 FONCTIONS TROUVÉES: {len(functions)}")
print()
print("=" * 80)
print()

# Classer par catégorie
categories = {
    'CALCUL_IMPACT': [],
    'CALCUL_LATENCE_TTR': [],
    'DIRECTION': [],
    'GROUPEMENT': [],
    'TIMELINE': [],
    'FIBONACCI': [],
    'BACKTEST': [],
    'PREDICTION': [],
    'DATABASE': [],
    'UI_DISPLAY': [],
    'AUTRES': []
}

for func in functions:
    name = func['name'].lower()
    
    if 'impact' in name:
        categories['CALCUL_IMPACT'].append(func)
    elif 'latency' in name or 'ttr' in name:
        categories['CALCUL_LATENCE_TTR'].append(func)
    elif 'direction' in name:
        categories['DIRECTION'].append(func)
    elif 'group' in name or 'cluster' in name:
        categories['GROUPEMENT'].append(func)
    elif 'timeline' in name:
        categories['TIMELINE'].append(func)
    elif 'fibonacci' in name:
        categories['FIBONACCI'].append(func)
    elif 'backtest' in name or 'real' in name or 'measure' in name:
        categories['BACKTEST'].append(func)
    elif 'predict' in name:
        categories['PREDICTION'].append(func)
    elif 'load' in name or 'get_future' in name or 'db' in name:
        categories['DATABASE'].append(func)
    elif 'create' in name or 'display' in name or 'chart' in name:
        categories['UI_DISPLAY'].append(func)
    else:
        categories['AUTRES'].append(func)

# Afficher par catégorie
for cat_name, funcs in categories.items():
    if funcs:
        print(f"📂 {cat_name} ({len(funcs)} fonctions)")
        print("-" * 80)
        for func in funcs:
            print(f"  • {func['name']:<40} lignes {func['start']:4d}-{func['end']:4d} ({func['lines']:3d} lignes)")
        print()

print("=" * 80)
print()
print("🎯 FONCTIONS DE CALCUL D'IMPACT À EXAMINER EN PRIORITÉ:")
print("-" * 80)
for func in categories['CALCUL_IMPACT'] + categories['PREDICTION']:
    print(f"  ⚠️ {func['name']:<40} lignes {func['start']:4d}-{func['end']:4d}")
print()
