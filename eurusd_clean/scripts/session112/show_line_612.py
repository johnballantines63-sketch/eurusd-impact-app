#!/usr/bin/env python3
"""
Afficher contexte ligne 612
"""
from pathlib import Path

calendrier = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/streamlit_app/pages/1_Calendrier_Trading.py")
lines = calendrier.read_text().split('\n')

print("="*80)
print("CONTEXTE LIGNE 612")
print("="*80)

# Afficher lignes 600-620
for i in range(599, min(620, len(lines))):
    marker = " >>> " if i == 611 else "     "
    print(f"{marker}{i+1:4d} | {lines[i]}")

print("="*80)
