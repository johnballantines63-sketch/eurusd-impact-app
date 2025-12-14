#!/usr/bin/env python3
"""Trouver l'emplacement exact du backtest"""

from pathlib import Path

FILE_PATH = Path('fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py')

print("🔍 LOCALISATION BACKTEST")
print("=" * 60)

with open(FILE_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Trouver ligne du backtest
backtest_line = None
for i, line in enumerate(lines):
    if "🎯 Backtest : Prédiction vs Réalité" in line:
        backtest_line = i
        break

if backtest_line is None:
    print("❌ Backtest non trouvé")
else:
    print(f"✅ Backtest trouvé à la ligne {backtest_line + 1}\n")
    
    # Afficher contexte (20 lignes avant)
    print("📋 Contexte AVANT (20 lignes):")
    print("-" * 60)
    for i in range(max(0, backtest_line - 20), backtest_line):
        print(f"{i+1:4d}: {lines[i].rstrip()}")
    
    print("\n" + "=" * 60)
    print(f">>> LIGNE {backtest_line + 1}: BACKTEST ICI <<<")
    print("=" * 60)
    
    # Afficher début du backtest
    print("\n📋 Début du backtest (10 lignes):")
    print("-" * 60)
    for i in range(backtest_line, min(len(lines), backtest_line + 10)):
        print(f"{i+1:4d}: {lines[i].rstrip()}")

print("\n💡 Vérifier:")
print("   1. Est-ce dans le flux principal (après if len(predictions) > 1) ?")
print("   2. Indentation correcte ?")
print("   3. Pas dans un 'if use_sequential:' ?")
