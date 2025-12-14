#!/usr/bin/env python3
"""
Dédupliquer résultats scanner - ne garder qu'un mouvement par timestamp
"""

import json
from pathlib import Path

input_file = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121/single_wave_candidates_rev12.json'
output_file = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121/single_wave_candidates_rev12_dedup.json'

# Charger résultats
with open(input_file, 'r') as f:
    data = json.load(f)

candidates = data['candidates']

print("="*80)
print("DÉDUPLICATION RÉSULTATS SCANNER")
print("="*80 + "\n")
print(f"Candidats bruts: {len(candidates)}\n")

# Dédupliquer par (date, time, impact_pips, direction)
seen = set()
dedup_candidates = []

for candidate in candidates:
    # Clé unique : date + time + impact + direction
    key = (
        candidate['date'],
        candidate['time'],
        candidate['impact_pips'],
        candidate['direction']
    )
    
    if key not in seen:
        seen.add(key)
        dedup_candidates.append(candidate)

print(f"Candidats dédupliqués: {len(dedup_candidates)}\n")

# Recompter par type
fort_count = sum(1 for c in dedup_candidates if c['pattern_type'] == 'fort')
intermediate_count = sum(1 for c in dedup_candidates if c['pattern_type'] == 'intermediate')
extended_count = sum(1 for c in dedup_candidates if c['pattern_type'] == 'extended')

print("="*80)
print("DISTRIBUTION APRÈS DÉDUPLICATION")
print("="*80)
print(f"Total: {len(dedup_candidates)}")
print(f"  - Single Fort:        {fort_count}")
print(f"  - Single Intermediate: {intermediate_count}")
print(f"  - Extended:           {extended_count}")
print("="*80 + "\n")

# Afficher cas dédupliqués
print("CAS UNIQUES DÉTECTÉS:")
print("="*80 + "\n")

for candidate in sorted(dedup_candidates, key=lambda x: (x['date'], x['time'])):
    pattern = candidate['pattern_type'].upper()
    emoji = "🟢" if pattern == 'FORT' else ("🟡" if pattern == 'INTERMEDIATE' else "🔵")
    pullback_str = f"Pullback {candidate['pullback_ratio']:4.1f}%" if candidate.get('pullback_ratio', 0) > 0 else "No pullback"
    
    print(f"{emoji} {candidate['date']} {candidate['time']} | "
          f"{pattern:12s} | {candidate['impact_pips']:5.1f} pips | "
          f"{pullback_str}")

# Sauvegarder version dédupliquée
output_data = {
    'scan_date': data['scan_date'],
    'methodology': data['methodology'],
    'period': data['period'],
    'deduplication': True,
    'summary': {
        'total_candidates': len(dedup_candidates),
        'fort_count': fort_count,
        'intermediate_count': intermediate_count,
        'extended_count': extended_count
    },
    'candidates': dedup_candidates
}

with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\n✅ Résultats dédupliqués sauvegardés: {output_file}")
