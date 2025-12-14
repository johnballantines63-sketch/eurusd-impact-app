#!/usr/bin/env python3
"""
Session 131 - Recherche TOUS les DoubleWave
Objectif: Trouver tous les DoubleWave_Overlap et DoubleWave_Cascade
pour valider le workflow sur plusieurs cas
"""

import json
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).parent.parent.parent
PATTERNS_PATH = BASE_DIR / "scripts" / "session130" / "patterns_classified.json"

print("\n" + "="*80)
print("RECHERCHE DE TOUS LES DOUBLEWAVE (2023-2025)")
print("="*80)

# Charger les patterns
with open(PATTERNS_PATH, 'r') as f:
    data = json.load(f)

print(f"\nTotal mouvements analysés: {data['metadata']['total_movements']}")

# Accéder aux patterns classifiés
classified = data.get('classified', {})

doublewave_overlap = classified.get('DoubleWave_Overlap', [])
doublewave_cascade = classified.get('DoubleWave_Cascade', [])

print(f"\n{'='*80}")
print(f"RÉSULTATS PAR TYPE")
print(f"{'='*80}")
print(f"DoubleWave_Overlap:  {len(doublewave_overlap)}")
print(f"DoubleWave_Cascade:  {len(doublewave_cascade)}")
print(f"TOTAL DoubleWave:    {len(doublewave_overlap) + len(doublewave_cascade)}")

# Analyser DoubleWave_Overlap
if doublewave_overlap:
    print(f"\n{'='*80}")
    print(f"DOUBLEWAVE_OVERLAP - {len(doublewave_overlap)} CAS")
    print(f"{'='*80}")
    
    print(f"\n{'Date':<12} | {'Impact':>8} | {'Events':>7} | {'Direction':>10} | {'Wave1':>8} | {'Wave2':>8} | {'Pullback':>9}")
    print("-"*12 + "+" + "-"*8 + "+" + "-"*7 + "+" + "-"*10 + "+" + "-"*8 + "+" + "-"*8 + "+" + "-"*9)
    
    for mvt in sorted(doublewave_overlap, key=lambda x: x['date']):
        date = mvt['date']
        impact = mvt.get('impact_pips', 0)
        n_events = len(mvt.get('events', []))
        direction = mvt.get('direction', 'N/A')
        wave1 = mvt.get('wave1_pips', 0)
        wave2 = mvt.get('wave2_pips', 0)
        pullback = mvt.get('pullback_ratio', 0)
        
        print(f"{date:<12} | {impact:>8.1f} | {n_events:>7} | {direction:>10} | {wave1:>8.1f} | {wave2:>8.1f} | {pullback:>9.3f}")
    
    # Statistiques
    impacts = [mvt.get('impact_pips', 0) for mvt in doublewave_overlap]
    print(f"\n{'='*80}")
    print(f"STATISTIQUES DOUBLEWAVE_OVERLAP")
    print(f"{'='*80}")
    print(f"Impact moyen: {sum(impacts)/len(impacts):.1f} pips")
    print(f"Impact min:   {min(impacts):.1f} pips")
    print(f"Impact max:   {max(impacts):.1f} pips")
    
    n_events_list = [len(mvt.get('events', [])) for mvt in doublewave_overlap]
    print(f"\nNombre événements moyen: {sum(n_events_list)/len(n_events_list):.1f}")
    print(f"Nombre événements min:   {min(n_events_list)}")
    print(f"Nombre événements max:   {max(n_events_list)}")

# Analyser DoubleWave_Cascade
if doublewave_cascade:
    print(f"\n{'='*80}")
    print(f"DOUBLEWAVE_CASCADE - {len(doublewave_cascade)} CAS")
    print(f"{'='*80}")
    
    print(f"\n{'Date':<12} | {'Impact':>8} | {'Events':>7} | {'Direction':>10} | {'Wave1':>8} | {'Wave2':>8} | {'Pullback':>9}")
    print("-"*12 + "+" + "-"*8 + "+" + "-"*7 + "+" + "-"*10 + "+" + "-"*8 + "+" + "-"*8 + "+" + "-"*9)
    
    for mvt in sorted(doublewave_cascade, key=lambda x: x['date']):
        date = mvt['date']
        impact = mvt.get('impact_pips', 0)
        n_events = len(mvt.get('events', []))
        direction = mvt.get('direction', 'N/A')
        wave1 = mvt.get('wave1_pips', 0)
        wave2 = mvt.get('wave2_pips', 0)
        pullback = mvt.get('pullback_ratio', 0)
        
        print(f"{date:<12} | {impact:>8.1f} | {n_events:>7} | {direction:>10} | {wave1:>8.1f} | {wave2:>8.1f} | {pullback:>9.3f}")
    
    # Statistiques
    impacts = [mvt.get('impact_pips', 0) for mvt in doublewave_cascade]
    print(f"\n{'='*80}")
    print(f"STATISTIQUES DOUBLEWAVE_CASCADE")
    print(f"{'='*80}")
    print(f"Impact moyen: {sum(impacts)/len(impacts):.1f} pips")
    print(f"Impact min:   {min(impacts):.1f} pips")
    print(f"Impact max:   {max(impacts):.1f} pips")
    
    n_events_list = [len(mvt.get('events', [])) for mvt in doublewave_cascade]
    print(f"\nNombre événements moyen: {sum(n_events_list)/len(n_events_list):.1f}")
    print(f"Nombre événements min:   {min(n_events_list)}")
    print(f"Nombre événements max:   {max(n_events_list)}")

# Sélectionner candidats pour tests
print(f"\n{'='*80}")
print(f"CANDIDATS POUR VALIDATION WORKFLOW")
print(f"{'='*80}")

candidates = []

# Critères sélection:
# 1. DoubleWave_Overlap avec 5-25 events (complexité moyenne à élevée)
# 2. Impact 30-70 pips (ni trop petit ni trop grand)
# 3. Différentes dates pour diversité

for mvt in doublewave_overlap:
    n_events = len(mvt.get('events', []))
    impact = mvt.get('impact_pips', 0)
    
    if 5 <= n_events <= 25 and 30 <= impact <= 70:
        candidates.append({
            'date': mvt['date'],
            'pattern': 'DoubleWave_Overlap',
            'impact': impact,
            'n_events': n_events,
            'direction': mvt.get('direction', 'N/A'),
            'pullback_ratio': mvt.get('pullback_ratio', 0),
            'wave1': mvt.get('wave1_pips', 0),
            'wave2': mvt.get('wave2_pips', 0),
            'priority': 'REFERENCE' if mvt['date'] == '2025-09-11' else 'HIGH'
        })

for mvt in doublewave_cascade:
    n_events = len(mvt.get('events', []))
    impact = mvt.get('impact_pips', 0)
    
    if 3 <= n_events <= 15 and 30 <= impact <= 70:
        candidates.append({
            'date': mvt['date'],
            'pattern': 'DoubleWave_Cascade',
            'impact': impact,
            'n_events': n_events,
            'direction': mvt.get('direction', 'N/A'),
            'pullback_ratio': mvt.get('pullback_ratio', 0),
            'wave1': mvt.get('wave1_pips', 0),
            'wave2': mvt.get('wave2_pips', 0),
            'priority': 'HIGH'
        })

# Trier par priorité puis impact
candidates.sort(key=lambda x: (x['priority'] != 'REFERENCE', x['priority'] != 'HIGH', -x['impact']))

if candidates:
    print(f"\n{len(candidates)} candidats identifiés:")
    print(f"\n{'Date':<12} | {'Pattern':<20} | {'Impact':>8} | {'Events':>7} | {'Priority':>10}")
    print("-"*12 + "+" + "-"*20 + "+" + "-"*8 + "+" + "-"*7 + "+" + "-"*10)
    
    for cand in candidates:
        marker = "✅" if cand['priority'] == 'REFERENCE' else "  "
        print(f"{marker} {cand['date']:<10} | {cand['pattern']:<20} | {cand['impact']:>8.1f} | {cand['n_events']:>7} | {cand['priority']:>10}")
    
    # Sélectionner 3-4 cas différents
    test_cases = []
    reference_case = None
    
    for cand in candidates:
        if cand['priority'] == 'REFERENCE':
            reference_case = cand
        elif len(test_cases) < 3:
            test_cases.append(cand)
    
    print(f"\n{'='*80}")
    print(f"RECOMMANDATION POUR VALIDATION WORKFLOW")
    print(f"{'='*80}")
    
    if reference_case:
        print(f"\n✅ CAS RÉFÉRENCE (déjà validé Session 115):")
        print(f"   {reference_case['date']} - {reference_case['pattern']}")
        print(f"   Impact: {reference_case['impact']:.1f} pips | Events: {reference_case['n_events']}")
    
    print(f"\n🎯 NOUVEAUX CAS À TESTER:")
    for i, case in enumerate(test_cases, 1):
        print(f"\n   {i}. {case['date']} - {case['pattern']}")
        print(f"      Impact: {case['impact']:.1f} pips | Events: {case['n_events']}")
        print(f"      Wave1: {case['wave1']:.1f} pips | Wave2: {case['wave2']:.1f} pips")
        print(f"      Pullback: {case['pullback_ratio']:.3f}")
    
    print(f"\n{'='*80}")
    print(f"PROCHAINES ÉTAPES")
    print(f"{'='*80}")
    print(f"""
1. Calculer amplification idéale pour chaque nouveau cas:
   - Extraire événements et calculer scores
   - Appliquer formule: amp_ideal = impact / (score_total × √n_events)
   
2. Comparer amplifications:
   - Si similaires (±20%) → Option C validée (amp fixes)
   - Si très différentes (>50%) → Besoin modélisation
   
3. Chercher clusters similaires pour chaque cas:
   - Appliquer même workflow Session 130
   - Vérifier si patterns vraiment uniques ou récurrents
   
4. Décision finale sur modélisation:
   - 3+ cas validés → workflow reproductible
   - Amplifications stables → amp fixes par pattern
   - Amplifications variables → modélisation nécessaire
""")
else:
    print(f"\n⚠️  Aucun candidat trouvé avec les critères de sélection")
    print(f"    Il y a seulement {len(doublewave_overlap)} DoubleWave_Overlap")
    print(f"    et {len(doublewave_cascade)} DoubleWave_Cascade dans le dataset")

print(f"\n{'='*80}")
print(f"FIN DE LA RECHERCHE")
print(f"{'='*80}\n")
