#!/usr/bin/env python3
"""
Session 131 - Calcul Amplifications DoubleWave_Cascade
Objectif: Calculer amp idéale pour les 4 DoubleWave_Cascade
et voir si elles sont cohérentes (contrairement aux Overlap)
"""

import json
import duckdb
from pathlib import Path
from datetime import datetime
import sys
import math

# Import utils
sys.path.insert(0, str(Path(__file__).parent / '../session129'))
from utils_timezone import ensure_bern_time

# Chemins
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "data" / "warehouse.duckdb"
PATTERNS_PATH = BASE_DIR / "scripts" / "session130" / "patterns_classified.json"

# Les 4 DoubleWave_Cascade
CASCADE_CASES = [
    "2023-03-07",
    "2023-03-10",
    "2023-07-12",
    "2025-04-04"
]

print("\n" + "="*80)
print("CALCUL AMPLIFICATIONS - 4 DOUBLEWAVE_CASCADE")
print("="*80)

# Charger patterns
with open(PATTERNS_PATH, 'r') as f:
    patterns_data = json.load(f)

doublewave_cascade = patterns_data['classified']['DoubleWave_Cascade']

# Connexion DB
conn = duckdb.connect(str(DB_PATH), read_only=True)

print(f"\n{'='*80}")
print(f"ANALYSE DES 4 CAS CASCADE")
print(f"{'='*80}")

results = []

for date_str in CASCADE_CASES:
    # Trouver le mouvement
    mvt = next((m for m in doublewave_cascade if m['date'] == date_str), None)
    
    if not mvt:
        print(f"\n⚠️  Mouvement {date_str} non trouvé")
        continue
    
    print(f"\n{'─'*80}")
    print(f"📅 {date_str}")
    print(f"{'─'*80}")
    
    impact_real = mvt['impact_pips']
    n_events = len(mvt.get('events', []))
    wave1 = mvt.get('wave1_pips', 0)
    wave2 = mvt.get('wave2_pips', 0)
    pullback = mvt.get('pullback_ratio', 0)
    
    print(f"Impact réel: {impact_real:.2f} pips")
    print(f"Nombre events: {n_events}")
    print(f"Wave1: {wave1:.2f} | Wave2: {wave2:.2f} | Pullback: {pullback:.3f}")
    
    if n_events == 0:
        print(f"⚠️  Aucun événement trouvé - skip")
        continue
    
    # Calculer scores
    events = mvt.get('events', [])
    total_score = 0
    events_with_score = 0
    
    print(f"\nÉvénements:")
    for i, evt in enumerate(events, 1):
        event_key = evt['event_key']
        country = evt['country']
        
        # Chercher score dans event_families
        query = """
        SELECT empirical_score
        FROM event_families
        WHERE event_key = ? 
        LIMIT 1
        """
        
        result = conn.execute(query, [event_key]).fetchone()
        
        if result and result[0] is not None:
            score = result[0]
            total_score += score
            events_with_score += 1
            print(f"  {i:2d}. {event_key:<50s} | {country:2s} | Score: {score:>7.2f}")
        else:
            print(f"  {i:2d}. {event_key:<50s} | {country:2s} | Score: N/A")
    
    if events_with_score == 0:
        print(f"\n⚠️  Aucun score trouvé - skip")
        continue
    
    # Calculer amplification idéale
    amp_ideal = impact_real / (total_score * math.sqrt(events_with_score))
    
    print(f"\n{'─'*40}")
    print(f"RÉSULTATS:")
    print(f"{'─'*40}")
    print(f"Score total:         {total_score:>10.2f}")
    print(f"Events avec score:   {events_with_score:>10d}")
    print(f"Amplification idéale: {amp_ideal:>10.6f}")
    
    results.append({
        'date': date_str,
        'impact': impact_real,
        'n_events': n_events,
        'n_events_scored': events_with_score,
        'total_score': total_score,
        'amp_ideal': amp_ideal,
        'wave1': wave1,
        'wave2': wave2,
        'pullback': pullback
    })

conn.close()

# Analyse comparative
print(f"\n{'='*80}")
print(f"ANALYSE COMPARATIVE CASCADE")
print(f"{'='*80}")

if not results:
    print(f"\n⚠️  Aucun résultat à comparer")
else:
    print(f"\n{'Date':<12} | {'Impact':>8} | {'Events':>7} | {'Score':>10} | {'Amp Idéale':>12}")
    print("-"*12 + "+" + "-"*8 + "+" + "-"*7 + "+" + "-"*10 + "+" + "-"*12)
    
    for r in results:
        date = r['date']
        impact = r['impact']
        n_events = r['n_events_scored']
        score = r['total_score']
        amp = r['amp_ideal']
        
        print(f"   {date:<10} | {impact:>8.1f} | {n_events:>7} | {score:>10.1f} | {amp:>12.6f}")
    
    # Statistiques
    if len(results) > 1:
        amps = [r['amp_ideal'] for r in results]
        avg_amp = sum(amps) / len(amps)
        min_amp = min(amps)
        max_amp = max(amps)
        
        print(f"\n{'─'*80}")
        print(f"STATISTIQUES AMPLIFICATIONS CASCADE:")
        print(f"{'─'*80}")
        print(f"Moyenne:    {avg_amp:.6f}")
        print(f"Min:        {min_amp:.6f}")
        print(f"Max:        {max_amp:.6f}")
        print(f"Variabilité: {(max_amp/min_amp):.2f}x")
        
        # Comparer avec DoubleWave_Overlap standards
        overlap_avg = (0.0877 + 0.0999 + 0.1727) / 3  # Moyenne des 3 Overlap standards
        
        print(f"\n{'─'*80}")
        print(f"COMPARAISON AVEC DOUBLEWAVE_OVERLAP:")
        print(f"{'─'*80}")
        print(f"Cascade moyenne:      {avg_amp:.6f}")
        print(f"Overlap moyenne:      {overlap_avg:.6f} (3 cas standards)")
        print(f"Ratio Cascade/Overlap: {avg_amp/overlap_avg:.2f}x")
        
        print(f"\n{'='*80}")
        print(f"CONCLUSION CASCADE")
        print(f"{'='*80}")
        
        variability = max_amp / min_amp
        
        if variability < 1.5:
            print(f"""
✅ CASCADE: AMPLIFICATIONS STABLES (variabilité {variability:.2f}x < 1.5x)

→ Les DoubleWave_Cascade ont des amplifications cohérentes !

Amplification recommandée pour CASCADE: {avg_amp:.4f}

Les Cascade semblent être un pattern homogène avec amp stable.
""")
        elif variability < 2.5:
            print(f"""
⚠️  CASCADE: AMPLIFICATIONS MODÉRÉMENT VARIABLES (variabilité {variability:.2f}x)

→ Variabilité acceptable mais pas parfaite

Amplification recommandée pour CASCADE: {avg_amp:.4f} (±20%)

Considérer:
- Amp fixe moyenne
- OU légère modélisation par n_events/score
""")
        else:
            print(f"""
❌ CASCADE: AMPLIFICATIONS TRÈS VARIABLES (variabilité {variability:.2f}x > 2.5x)

→ Même les Cascade varient trop !

Les patterns DoubleWave nécessitent une modélisation plus sophistiquée.
""")

# SYNTHÈSE GLOBALE
print(f"\n{'='*80}")
print(f"SYNTHÈSE GLOBALE - DOUBLEWAVE")
print(f"{'='*80}")

if results:
    cascade_avg = sum(r['amp_ideal'] for r in results) / len(results)
    overlap_standards_avg = (0.0877 + 0.0999 + 0.1727) / 3
    overlap_sept11 = 0.012788
    
    print(f"""
RÉCAPITULATIF DES AMPLIFICATIONS:

1. DoubleWave_Cascade (4 cas):
   Moyenne: {cascade_avg:.4f}
   Min: {min(r['amp_ideal'] for r in results):.4f}
   Max: {max(r['amp_ideal'] for r in results):.4f}
   Variabilité: {max(r['amp_ideal'] for r in results)/min(r['amp_ideal'] for r in results):.2f}x

2. DoubleWave_Overlap standards (3 cas):
   Moyenne: {overlap_standards_avg:.4f}
   Min: 0.0877
   Max: 0.1727
   Variabilité: 1.97x

3. DoubleWave_Overlap superposition (11 sept):
   Amp unique: {overlap_sept11:.4f}
   Score exceptionnel: 651 points (vs 140-320 standards)

RECOMMANDATION FINALE:

- Cascade et Overlap standards ont des amp similaires (~0.10-0.12)
- Le 11 septembre est un CAS SPÉCIAL (superposition ECB+US)
- Option C (amp fixes) VALIDÉE avec distinction:
  
  • DoubleWave_Cascade:  amp = {cascade_avg:.4f}
  • DoubleWave_Overlap:   amp = {overlap_standards_avg:.4f}
  • Cas superposition:    amp = {overlap_sept11:.4f} (identifier via score >500)

OU

- Si variabilité Cascade aussi élevée → Modélisation nécessaire
- Implémenter Option A ou B pour tous les DoubleWave
""")

print(f"\n{'='*80}")
print(f"FIN DE L'ANALYSE CASCADE")
print(f"{'='*80}\n")
