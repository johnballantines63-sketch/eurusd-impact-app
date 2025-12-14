"""
RECHERCHE DE TOUTES LES FORMULES TTR

Objectif : Trouver tous les calculs de TTR dans le code (comme on a trouvé 4 formules d'impact)
"""

import os
import re
from pathlib import Path

base_dir = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")

# Fichiers clés à analyser
files_to_check = [
    "fx_impact_app/streamlit_app/pages/4_Planificateur_STABLE_0159_PERFECT.py",
    "fx_impact_app/src/sequence_multi_event_timeline_v87.py",
    "fx_impact_app/src/forecaster_mvp.py",
    "fx_impact_app/src/latency_analyzer.py",
]

# Patterns à chercher
patterns = [
    r'ttr[_\s]*=',  # Assignations TTR
    r'time[_\s]*to[_\s]*reversal',  # Mentions explicites
    r'latency.*\*\s*[\d.]+',  # Multiplications de latency
    r'ttr_median.*\*\s*[\d.]+',  # Multiplications de ttr_median
    r'def.*ttr',  # Fonctions contenant ttr
    r'calculate.*ttr',  # Fonctions de calcul
]

print("=" * 80)
print("🔍 RECHERCHE FORMULES TTR DANS LE CODE")
print("=" * 80)

formulas_found = {}

for file_path in files_to_check:
    full_path = base_dir / file_path
    
    if not full_path.exists():
        print(f"\n❌ Fichier non trouvé : {file_path}")
        continue
    
    print(f"\n\n📄 {file_path}")
    print("-" * 80)
    
    with open(full_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    matches = []
    
    for line_num, line in enumerate(lines, 1):
        line_lower = line.lower()
        
        # Chercher tous les patterns
        for pattern in patterns:
            if re.search(pattern, line_lower):
                matches.append({
                    'line_num': line_num,
                    'content': line.strip(),
                    'pattern': pattern
                })
                break  # Ne compter qu'une fois par ligne
    
    if matches:
        print(f"\n✅ Trouvé {len(matches)} lignes pertinentes :")
        
        for match in matches[:30]:  # Limiter à 30 lignes
            print(f"\n   L{match['line_num']}: {match['content'][:120]}")
        
        if len(matches) > 30:
            print(f"\n   ... et {len(matches) - 30} autres lignes")
        
        formulas_found[file_path] = matches
    else:
        print("   ⚠️  Aucune mention de TTR trouvée")

# Résumé
print("\n\n" + "=" * 80)
print("📊 RÉSUMÉ")
print("=" * 80)

total_matches = sum(len(m) for m in formulas_found.values())
print(f"\n✅ Total : {total_matches} lignes pertinentes dans {len(formulas_found)} fichiers")

for file_path, matches in formulas_found.items():
    print(f"\n   {Path(file_path).name} : {len(matches)} lignes")

# Extraire les formules potentielles
print("\n\n" + "=" * 80)
print("🔬 FORMULES POTENTIELLES DÉTECTÉES")
print("=" * 80)

for file_path, matches in formulas_found.items():
    print(f"\n📄 {Path(file_path).name}")
    print("-" * 40)
    
    # Filtrer les lignes avec calculs
    formula_lines = [m for m in matches if '=' in m['content'] and ('*' in m['content'] or '+' in m['content'] or '-' in m['content'])]
    
    if formula_lines:
        for match in formula_lines[:10]:
            print(f"   L{match['line_num']}: {match['content']}")
    else:
        print("   Aucune formule de calcul détectée")

print("\n" + "=" * 80)
