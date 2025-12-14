"""
Explorer Structure Pattern JSON
================================
"""

import json
from pathlib import Path

patterns_file = Path(__file__).parent / 'double_waves_rev12.json'

with open(patterns_file, 'r') as f:
    patterns = json.load(f)

sept11 = [p for p in patterns if p['date'] == '2025-09-11'][0]

print("\n" + "="*80)
print("STRUCTURE PATTERN 11 SEPTEMBRE")
print("="*80)
print()

print("Clés disponibles:")
for key in sept11.keys():
    value = sept11[key]
    if isinstance(value, (int, float)):
        print(f"  {key:30s} : {value}")
    else:
        print(f"  {key:30s} : {value}")

print()
print("="*80)
print("VALEURS CRITIQUES")
print("="*80)
print()

# Afficher valeurs importantes
for key in ['date', 'actual', 'wave1_amp_pips', 'wave2_amp_pips', 
            'peak1_time', 'peak2_time', 'direction', 'confidence']:
    if key in sept11:
        print(f"{key:20s} : {sept11[key]}")

print()
print("="*80)
print("COMPARAISON")
print("="*80)
print()

print("Rev12 validation (Session 120):")
print("  Wave2 = 51.7 pips (impact cluster CPI)")
print("  Impact MT5 = 56.2 pips")
print()

if 'actual' in sept11:
    print(f"Pattern JSON:")
    print(f"  actual = {sept11['actual']} pips")
    print()
    
    if 'wave1_amp_pips' in sept11 and 'wave2_amp_pips' in sept11:
        total = sept11['wave1_amp_pips'] + sept11['wave2_amp_pips']
        print(f"  wave1_amp_pips = {sept11['wave1_amp_pips']:.1f} pips")
        print(f"  wave2_amp_pips = {sept11['wave2_amp_pips']:.1f} pips")
        print(f"  Total (W1+W2) = {total:.1f} pips")
        print()
        
        if abs(sept11['actual'] - total) < 1:
            print("→ actual = wave1 + wave2 (amplitude totale pattern)")
        elif abs(sept11['actual'] - sept11['wave2_amp_pips']) < 1:
            print("→ actual = wave2_amp_pips uniquement")
        else:
            print(f"→ actual ({sept11['actual']:.1f}) ne correspond ni à W2 ni à W1+W2")
