#!/usr/bin/env python3
"""
Chercher où enriched_events est créé et event_title perdu
"""
from pathlib import Path

calendrier = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/streamlit_app/pages/1_Calendrier_Trading.py")
lines = calendrier.read_text().split('\n')

print("="*80)
print("🔍 CHERCHE enriched_events.append")
print("="*80)

for i, line in enumerate(lines, 1):
    if 'enriched_events.append' in line:
        print(f"\n📍 Ligne {i}")
        # Afficher contexte (10 lignes avant et après)
        start = max(0, i-10)
        end = min(len(lines), i+20)
        
        for j in range(start, end):
            marker = " >>> " if j == i-1 else "     "
            print(f"{marker}{j+1:4d} | {lines[j]}")

print("\n" + "="*80)
