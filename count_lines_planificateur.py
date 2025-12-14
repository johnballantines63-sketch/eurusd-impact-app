#!/usr/bin/env python3
"""Script pour compter lignes et fonctions du planificateur"""

import re

filepath = "fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')
    
    # Compter lignes
    total_lines = len(lines)
    
    # Compter fonctions
    function_pattern = re.compile(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', re.MULTILINE)
    functions = function_pattern.findall(content)
    
    # Compter classes
    class_pattern = re.compile(r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.MULTILINE)
    classes = class_pattern.findall(content)
    
    print(f"📏 NOMBRE TOTAL DE LIGNES: {total_lines}")
    print(f"🔧 NOMBRE DE FONCTIONS: {len(functions)}")
    print(f"📦 NOMBRE DE CLASSES: {len(classes)}")
    print(f"📊 TAILLE FICHIER: {len(content):,} caractères")
    print(f"💰 TOKENS ESTIMÉS: ~{len(content) // 4:,}")
    
    print("\n📋 LISTE DES FONCTIONS:")
    for i, func in enumerate(functions, 1):
        print(f"  {i:2d}. {func}")
