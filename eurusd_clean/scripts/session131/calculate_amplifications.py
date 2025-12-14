#!/usr/bin/env python3
"""
Session 131 - Calcul Amplifications 3 nouveaux DoubleWave
Objectif: Calculer amp idéale et comparer avec 11 septembre (0.016)
pour décider si Option C (amp fixes) tient toujours
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

# Cas à tester
TEST_CASES = [
    "2025-09-11",  # Référence
    "2023-02-03",
    "2023-03-22", 
    "2025-02-03"
]

print("\n" + "="*80)
print("CALCUL AMPLIFICATIONS - 3 NOUVEAUX DOUBLEWAVE_OVERLAP")
print("="*80)

# Charger patterns
with open(PATTERNS_PATH, 'r') as f:
    patterns_data = json.load(f)

doublewave_overlap = patterns_data['classified']['DoubleWave_Overlap']

# Connexion DB
conn = duckdb.connect(str(DB_PATH), read_only=True)

print(f"\n{'='*80}")
print(f"ANALYSE DES 4 CAS")
print(f"{'='*80}")

results = []

for date_str in TEST_CASES:
    # Trouver le mouvement
    mvt = next((m for m in doublewave_overlap if m['date'] == date_str), None)
    
    if not mvt:
        print(f"\n⚠️  Mouvement {date_str} non trouvé")
        continue
    
    print(f"\n{'─'*80}")
    print(f"📅 {date_str}" + (" ✅ RÉFÉRENCE" if date_str == "2025-09-11" else ""))
    print(f"{'─'*80}")
    
    impact_real = mvt['impact_pips']
    n_events = len(mvt.get('events', []))
    
    print(f"Impact réel: {impact_real:.2f} pips")
    print(f"Nombre events: {n_events}")
    
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
        'is_reference': date_str == "2025-09-11"
    })

conn.close()

# Analyse comparative
print(f"\n{'='*80}")
print(f"ANALYSE COMPARATIVE DES AMPLIFICATIONS")
print(f"{'='*80}")

if not results:
    print(f"\n⚠️  Aucun résultat à comparer")
else:
    print(f"\n{'Date':<12} | {'Impact':>8} | {'Events':>7} | {'Score':>10} | {'Amp Idéale':>12} | {'vs Ref':>10}")
    print("-"*12 + "+" + "-"*8 + "+" + "-"*7 + "+" + "-"*10 + "+" + "-"*12 + "+" + "-"*10)
    
    ref_amp = None
    for r in results:
        if r['is_reference']:
            ref_amp = r['amp_ideal']
    
    for r in results:
        marker = "✅" if r['is_reference'] else "  "
        date = r['date']
        impact = r['impact']
        n_events = r['n_events_scored']
        score = r['total_score']
        amp = r['amp_ideal']
        
        if ref_amp and not r['is_reference']:
            ratio = (amp / ref_amp - 1) * 100
            vs_ref = f"{ratio:+.1f}%"
        else:
            vs_ref = "REF"
        
        print(f"{marker} {date:<10} | {impact:>8.1f} | {n_events:>7} | {score:>10.1f} | {amp:>12.6f} | {vs_ref:>10}")
    
    # Statistiques
    if len(results) > 1:
        amps = [r['amp_ideal'] for r in results]
        avg_amp = sum(amps) / len(amps)
        min_amp = min(amps)
        max_amp = max(amps)
        
        print(f"\n{'─'*80}")
        print(f"STATISTIQUES AMPLIFICATIONS:")
        print(f"{'─'*80}")
        print(f"Moyenne:    {avg_amp:.6f}")
        print(f"Min:        {min_amp:.6f}  ({(min_amp/ref_amp-1)*100:+.1f}% vs ref)" if ref_amp else f"Min: {min_amp:.6f}")
        print(f"Max:        {max_amp:.6f}  ({(max_amp/ref_amp-1)*100:+.1f}% vs ref)" if ref_amp else f"Max: {max_amp:.6f}")
        print(f"Variabilité: {(max_amp/min_amp):.2f}x")
        
        print(f"\n{'='*80}")
        print(f"CONCLUSION")
        print(f"{'='*80}")
        
        variability = max_amp / min_amp
        
        if variability < 1.5:
            print(f"""
✅ AMPLIFICATIONS STABLES (variabilité {variability:.2f}x < 1.5x)

→ Option C (amplifications fixes par pattern) VALIDÉE

Les amplifications varient peu entre les différents DoubleWave_Overlap.
Une amplification fixe ~{avg_amp:.4f} pour ce pattern est justifiée.

Recommandation:
1. Garder amp fixe par pattern
2. Documenter les cas validés
3. Implémenter pipeline avec amp fixes
""")
        elif variability < 2.5:
            print(f"""
⚠️  AMPLIFICATIONS MODÉRÉMENT VARIABLES (variabilité {variability:.2f}x)

→ Option C possible MAIS avec réserves

Les amplifications varient modérément. Considérer:
- Option C avec amp moyenne par pattern
- OU modélisation légère (ex: ajustement par n_events)

Recommandation:
1. Analyser si variabilité corrélée à score ou n_events
2. Décider entre amp fixe ou ajustement simple
3. Tester sur plus de cas si incertain
""")
        else:
            print(f"""
❌ AMPLIFICATIONS TRÈS VARIABLES (variabilité {variability:.2f}x > 2.5x)

→ Option C (amp fixes) NON VALIDÉE

Les amplifications varient trop pour utiliser une valeur fixe.
Modélisation nécessaire.

Recommandation:
1. Implémenter Option A (abaisser seuil Jaccard)
2. OU Option B (K-means clustering)
3. Chercher facteurs explicatifs (R², score, composition)
""")

print(f"\n{'='*80}")
print(f"FIN DE L'ANALYSE")
print(f"{'='*80}\n")
