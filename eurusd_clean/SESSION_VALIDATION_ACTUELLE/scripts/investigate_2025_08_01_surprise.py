#!/usr/bin/env python3
"""
Investigation Surprise 2025-08-01
==================================

Objectif : Comprendre pourquoi l'amplification est encore élevée pour 2025-08-01
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor
from core.formulas_validated import calculate_amplification_extended

print('='*100)
print('INVESTIGATION SURPRISE 2025-08-01')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=True)

result = executor.execute_complete_pipeline('2025-08-01')

if result.get('success'):
    cluster_info = result.get('results', {}).get('etape3_cluster_info', {})
    cluster = cluster_info.get('cluster', {})
    events = cluster.get('events', pd.DataFrame())
    
    print('='*100)
    print('ÉVÉNEMENTS DU CLUSTER')
    print('='*100)
    print()
    
    if not events.empty:
        max_surprise = 0.0
        
        # Afficher tous les événements
        print('='*100)
        print('TOUS LES ÉVÉNEMENTS')
        print('='*100)
        print()
        
        for _, event in events.iterrows():
            # Utiliser event_title ou label ou event_key pour le nom
            event_name = event.get('event_title') or event.get('label') or event.get('event_key') or 'Unknown'
            actual = event.get('actual')
            estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
            forecast = event.get('forecast')
            previous = event.get('previous')
            
            print(f'Événement : {event_name}')
            print(f'  Event Key: {event.get("event_key", "N/A")}')
            print(f'  Actual: {actual}')
            print(f'  Estimate: {estimate}')
            print(f'  Forecast: {forecast}')
            print(f'  Previous: {previous}')
            
            if actual is not None and estimate is not None and estimate != 0:
                surprise = abs(actual - estimate) / abs(estimate) * 100
                max_surprise = max(max_surprise, surprise)
                print(f'  Surprise: {surprise:.1f}%')
            else:
                print(f'  ⚠️ Impossible de calculer surprise (actual={actual}, estimate={estimate})')
            print()
        
        print('='*100)
        print('SURPRISE MAXIMALE')
        print('='*100)
        print(f'Surprise max : {max_surprise:.1f}%')
        print()
        
        # Calculer amplification
        amplification = calculate_amplification_extended(max_surprise)
        print(f'Amplification calculée : {amplification:.3f}x')
        print()
        
        # Vérifier zone
        if max_surprise < 200:
            print(f'Zone : 4a (100-200%)')
            print(f'Formule : 1.0 + (surprise - 100) / 100 * 1.0, plafond 3x')
            expected = min(1.0 + (max_surprise - 100) / 100 * 1.0, 3.0)
            print(f'Amplification attendue : {expected:.3f}x')
        else:
            print(f'Zone : 4b (> 200%)')
            print(f'Formule : 5.5 + 0.371 * log10(surprise - 199), plafond 10x')
            import math
            expected = min(5.5 + 0.371 * math.log10(max_surprise - 199), 10.0)
            print(f'Amplification attendue : {expected:.3f}x')
        print()
        
        if abs(amplification - expected) < 0.001:
            print('✅ Amplification correcte')
        else:
            print(f'❌ Amplification incorrecte (attendu {expected:.3f}x, obtenu {amplification:.3f}x)')
        
        # Vérifier si amplification est trop élevée
        final_pred = result.get('final_prediction', {})
        impact_base = final_pred.get('impact_base', 0)
        real_impact = 188.40  # Depuis CSV
        amplification_needed = real_impact / impact_base if impact_base > 0 else 0
        
        print()
        print('='*100)
        print('COMPARAISON')
        print('='*100)
        print(f'Impact base : {impact_base:.2f} pips')
        print(f'Réel mesuré : {real_impact:.2f} pips')
        print(f'Amplification nécessaire : {amplification_needed:.3f}x')
        print(f'Amplification prédite : {amplification:.3f}x')
        print(f'Ratio : {amplification / amplification_needed:.1f}x trop élevée')
        print()
        
        if amplification > amplification_needed * 2:
            print('⚠️ Amplification prédite beaucoup trop élevée')
            print('   → Même avec correction Zone 4a, Zone 4b est trop agressive pour ce cas')
else:
    print(f'❌ Erreur: {result.get("error")}')

