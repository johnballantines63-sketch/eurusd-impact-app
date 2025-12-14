"""
Investigation 11 Septembre 2025
================================

Comprendre pourquoi le cas référence a MAE 45.8 pips au lieu de ~0
"""

import json
from pathlib import Path

# Charger résultats validation
results_file = Path(__file__).parent / 'validation_results.json'

with open(results_file, 'r') as f:
    data = json.load(f)

# Trouver 11 septembre 2025
sept11 = None
for result in data['results']:
    if result['date'] == '2025-09-11':
        sept11 = result
        break

if sept11 is None:
    print("❌ 11 septembre 2025 non trouvé")
else:
    print("\n" + "="*80)
    print("RÉSULTAT 11 SEPTEMBRE 2025")
    print("="*80)
    print()
    
    print(f"Date: {sept11['date']}")
    print(f"Status: {sept11['status']}")
    print()
    
    print("AMPLITUDES:")
    print(f"  Réel total: {sept11['actual']:.1f} pips")
    print(f"  Wave1 réel: {sept11['wave1_real']:.1f} pips")
    print(f"  Wave2 réel: {sept11['wave2_real']:.1f} pips")
    print()
    
    if sept11['predicted'] is not None:
        print("PRÉDICTIONS:")
        print(f"  Prédit total: {sept11['predicted']:.1f} pips")
        print(f"  MAE: {sept11['mae']:.1f} pips")
        print()
        
        if 'wave1_predicted' in sept11:
            print(f"  Wave1 prédit: {sept11.get('wave1_predicted', 'N/A')}")
        if 'wave2_predicted' in sept11:
            print(f"  Wave2 prédit: {sept11.get('wave2_predicted', 'N/A')}")
        print()
    
    if 'num_events_w1' in sept11:
        print("ÉVÉNEMENTS:")
        print(f"  Wave1: {sept11.get('num_events_w1', 0)} événements")
        print(f"  Wave2: {sept11.get('num_events_w2', 0)} événements")
        print(f"  Total: {sept11.get('num_events_total', 0)} événements")
        print()
    
    if 'calculation_details' in sept11:
        print("DÉTAILS CALCULS:")
        details = sept11['calculation_details']
        print(json.dumps(details, indent=2))
    
    print()
    print("="*80)
    print("COMPARAISON ATTENDU vs OBTENU")
    print("="*80)
    print()
    print("ATTENDU (Session 120 - Rev12):")
    print("  Total: 85.4 pips (Wave1: 33.7, Wave2: 51.7)")
    print("  MAE vs MT5 (56.2): 4.5 pips")
    print()
    print("OBTENU:")
    print(f"  Total réel: {sept11['actual']:.1f} pips")
    print(f"  Total prédit: {sept11['predicted']:.1f} pips" if sept11['predicted'] else "  Pas de prédiction")
    print(f"  MAE: {sept11['mae']:.1f} pips" if sept11['mae'] else "  Pas de MAE")
    print()
    
    # Vérifier cohérence
    expected_total = 85.4
    diff = abs(sept11['actual'] - expected_total)
    
    if diff < 1:
        print("✅ Amplitude réelle cohérente avec Rev12")
    else:
        print(f"⚠️  Amplitude réelle DIFFÉRENTE de Rev12 (écart {diff:.1f} pips)")
        print("   → Possible différence de calcul ou de baseline")
    print()
    
    # Analyser pourquoi prédiction si faible
    if sept11['predicted'] is not None:
        ratio = sept11['predicted'] / sept11['actual']
        print(f"RATIO prédit/réel: {ratio:.1%}")
        print()
        
        if ratio < 0.5:
            print("⚠️  SOUS-ESTIMATION MAJEURE (< 50%)")
            print()
            print("CAUSES POSSIBLES:")
            print("  1. Événements EODHD manquants ou incomplets")
            print("  2. Valeurs actual/forecast/previous incorrectes")
            print("  3. Surprise non calculée correctement")
            print("  4. Paramètres amplification trop faibles")
            print("  5. Assignment events aux waves incorrect")
