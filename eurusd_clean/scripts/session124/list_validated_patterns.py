"""
Lister les 17 Patterns Validés
===============================
"""

import json
from pathlib import Path

results_file = Path(__file__).parent / 'validation_results.json'

with open(results_file, 'r') as f:
    data = json.load(f)

validated = [r for r in data['results'] if r['status'] == 'validated']

print("\n" + "="*80)
print(f"PATTERNS VALIDÉS: {len(validated)}/149")
print("="*80)
print()

for i, r in enumerate(validated, 1):
    print(f"{i:2d}. {r['date']} | Réel: {r['actual']:5.1f} pips | Prédit: {r['predicted']:5.1f} pips | MAE: {r['mae']:5.2f}")

print()
print("="*80)
print("11 SEPTEMBRE DANS LES VALIDÉS ?")
print("="*80)
print()

sept11_validated = [r for r in validated if r['date'] == '2025-09-11']

if sept11_validated:
    r = sept11_validated[0]
    print("✅ OUI, 11 septembre validé !")
    print()
    print(f"Réel: {r['actual']:.1f} pips")
    print(f"Prédit: {r['predicted']:.1f} pips")
    print(f"MAE: {r['mae']:.2f} pips")
    print(f"Events W1: {r.get('num_events_w1', 0)}")
    print(f"Events W2: {r.get('num_events_w2', 0)}")
else:
    print("❌ NON, 11 septembre toujours 'no_events' ou 'events_not_assignable'")
    
    # Chercher son statut
    sept11_all = [r for r in data['results'] if r['date'] == '2025-09-11']
    if sept11_all:
        r = sept11_all[0]
        print()
        print(f"Statut actuel: {r['status']}")
        if 'num_events_total' in r:
            print(f"Events trouvés: {r.get('num_events_total', 0)}")
