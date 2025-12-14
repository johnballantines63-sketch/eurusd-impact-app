#!/usr/bin/env python3
"""Script pour afficher les lignes autour de 2170"""

file_path = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Nombre total de lignes: {len(lines)}")
print(f"\nLignes 2165-2175:")
print("=" * 80)

for i in range(2164, min(2176, len(lines))):
    line_num = i + 1
    line_content = lines[i].rstrip('\n')
    marker = " ← ERREUR" if line_num == 2170 else ""
    print(f"{line_num:4d}: {line_content}{marker}")
