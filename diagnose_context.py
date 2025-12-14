#!/usr/bin/env python3
"""
Diagnostic du contexte autour de la section backtest
"""

from pathlib import Path
import re

TARGET_FILE = Path("fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")

def analyze_context():
    print("=" * 80)
    print("🔍 DIAGNOSTIC CONTEXTE BACKTEST")
    print("=" * 80)
    
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n📄 Fichier : {len(lines)} lignes\n")
    
    # Trouver le backtest
    backtest_start = None
    for i, line in enumerate(lines):
        if "🎯 Backtest" in line:
            backtest_start = i
            break
    
    if backtest_start is None:
        print("❌ Backtest non trouvé")
        return
    
    print(f"✅ Backtest trouvé à la ligne {backtest_start + 1}\n")
    
    # Analyser 20 lignes AVANT le backtest
    print("=" * 80)
    print("📋 CONTEXTE AVANT LE BACKTEST (20 lignes)")
    print("=" * 80)
    
    start = max(0, backtest_start - 20)
    for i in range(start, backtest_start):
        indent = len(lines[i]) - len(lines[i].lstrip())
        indent_str = f"[{indent:2d}]"
        content = lines[i].rstrip()[:70]
        print(f"{i+1:4d} {indent_str} {content}")
    
    # Ligne du backtest
    print("\n" + "=" * 80)
    print(f"🎯 LIGNE BACKTEST ({backtest_start + 1})")
    print("=" * 80)
    indent = len(lines[backtest_start]) - len(lines[backtest_start].lstrip())
    print(f"{backtest_start+1:4d} [{indent:2d}] {lines[backtest_start].rstrip()}")
    
    # Analyser structure de blocs
    print("\n" + "=" * 80)
    print("🏗️  STRUCTURE DES BLOCS")
    print("=" * 80)
    
    # Compter try/if/for/with ouverts
    open_blocks = []
    for i in range(max(0, backtest_start - 100), backtest_start):
        line = lines[i].strip()
        indent = len(lines[i]) - len(lines[i].lstrip())
        
        # Détecter ouverture de bloc
        if line.startswith('if ') or line.startswith('elif '):
            open_blocks.append(('if', indent, i+1))
        elif line.startswith('try:'):
            open_blocks.append(('try', indent, i+1))
        elif line.startswith('for ') or line.startswith('while '):
            open_blocks.append(('loop', indent, i+1))
        elif line.startswith('with '):
            open_blocks.append(('with', indent, i+1))
        
        # Détecter fermeture
        elif line.startswith('except') or line.startswith('finally'):
            # Ferme le try correspondant
            for j in range(len(open_blocks)-1, -1, -1):
                if open_blocks[j][0] == 'try':
                    open_blocks.pop(j)
                    break
    
    # Filtrer les blocs qui englobent le backtest
    backtest_indent = len(lines[backtest_start]) - len(lines[backtest_start].lstrip())
    relevant_blocks = [b for b in open_blocks if b[1] < backtest_indent]
    
    print(f"\nBlocs ouverts englobant le backtest (indent < {backtest_indent}):\n")
    if len(relevant_blocks) == 0:
        print("   ✅ Aucun bloc ouvert (contexte propre)")
    else:
        for block_type, block_indent, line_num in relevant_blocks:
            print(f"   - {block_type:<8} [indent {block_indent:2d}] ligne {line_num}")
            print(f"     → {lines[line_num-1].strip()[:60]}")
    
    # Recommandation d'indentation
    print("\n" + "=" * 80)
    print("💡 RECOMMANDATION")
    print("=" * 80)
    
    if len(relevant_blocks) == 0:
        print(f"\n✅ Indentation correcte : {backtest_indent} espaces")
        print(f"   Le backtest est dans un contexte propre")
    else:
        print(f"\n⚠️  Contexte complexe détecté : {len(relevant_blocks)} bloc(s) ouvert(s)")
        print(f"   Indentation actuelle : {backtest_indent} espaces")
        print(f"   → Le backtest doit être dans un bloc `if`, `try`, ou autre")
        print(f"   → Chaque ligne du backtest doit avoir {backtest_indent} espaces")
    
    # Trouver la fin du backtest
    end_marker = None
    for i in range(backtest_start, min(len(lines), backtest_start + 500)):
        if "# === FIN SECTIONS CLASSIQUES ===" in lines[i]:
            end_marker = i
            break
    
    if end_marker:
        print(f"\n📍 Fin des sections classiques : ligne {end_marker + 1}")
        print(f"   Section backtest : lignes {backtest_start + 1} à {end_marker}")
        print(f"   → {end_marker - backtest_start} lignes à remplacer")

if __name__ == "__main__":
    analyze_context()
