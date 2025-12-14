#!/usr/bin/env python3
"""
Investigation Chemins Timings
==============================

Objectif : Vérifier quel chemin est pris pour chaque date (timings prédits vs pattern réel)
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

# Dates à tester
TEST_DATES = [
    '2025-09-11',
    '2025-11-20',
    '2025-10-10',
    '2025-06-23',
    '2025-05-29',
    '2025-11-26',
]

print('='*100)
print('INVESTIGATION CHEMINS TIMINGS')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

results = []

for date_str in TEST_DATES:
    print('='*100)
    print(f'📅 DATE : {date_str}')
    print('='*100)
    print()
    
    try:
        result = executor.execute_complete_pipeline(date_str)
        
        if not result.get('success'):
            print(f'❌ Erreur: {result.get("error")}')
            continue
        
        final_pred = result.get('final_prediction', {})
        pattern_info = final_pred.get('pattern_info', {})
        cluster_info = result.get('results', {}).get('etape3_cluster_info', {})
        cluster = cluster_info.get('cluster', {})
        anchor_time = cluster.get('anchor_time')
        
        pattern_type = pattern_info.get('pattern_type', 'NONE')
        timings_predicted = pattern_info.get('timings_predicted', False)
        wave2_peak_time = pattern_info.get('wave2_peak_time')
        
        print(f'📊 INFORMATIONS')
        print('-'*100)
        print(f'Pattern : {pattern_type}')
        print(f'Anchor time : {anchor_time}')
        print(f'Timings prédits : {timings_predicted}')
        print(f'Wave2 peak time : {wave2_peak_time}')
        print()
        
        if pattern_type == 'DOUBLE_WAVE':
            # Calculer timing attendu (T+15)
            expected_time = anchor_time + pd.Timedelta(minutes=15)
            
            if wave2_peak_time:
                error_min = abs((wave2_peak_time - expected_time).total_seconds() / 60.0)
                
                print(f'🔍 ANALYSE TIMING')
                print('-'*100)
                print(f'Timing attendu (T+15) : {expected_time.strftime("%H:%M")}')
                print(f'Timing utilisé : {wave2_peak_time.strftime("%H:%M")}')
                print(f'Erreur : {error_min:.1f} min')
                print()
                
                if error_min < 1:
                    print('✅ PARFAIT (erreur < 1 min)')
                    status = 'PARFAIT'
                elif error_min < 5:
                    print('✅ EXCELLENT (erreur < 5 min)')
                    status = 'EXCELLENT'
                else:
                    print(f'❌ ERREUR IMPORTANTE ({error_min:.1f} min)')
                    print()
                    print('🔍 DIAGNOSTIC')
                    print('-'*100)
                    if timings_predicted:
                        print('  ⚠️ timings_predicted=True mais erreur importante')
                        print('  → Problème : wave2_peak_time n\'utilise pas T+15')
                    else:
                        print('  ⚠️ timings_predicted=False')
                        print('  → Problème : Code utilise pattern réel au lieu de timings prédits')
                    status = 'ERREUR'
            else:
                print('⚠️ wave2_peak_time est None')
                status = 'NONE'
        else:
            print('ℹ️ Pas un DOUBLE_WAVE')
            status = 'N/A'
        
        results.append({
            'date': date_str,
            'pattern_type': pattern_type,
            'timings_predicted': timings_predicted,
            'wave2_peak_time': wave2_peak_time.strftime('%H:%M') if wave2_peak_time else None,
            'status': status
        })
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        print()

# Résumé
print('='*100)
print('📊 RÉSUMÉ')
print('='*100)
print()

df_results = pd.DataFrame(results)

if not df_results.empty:
    print('Résultats par date:')
    print('-'*100)
    for _, row in df_results.iterrows():
        if row['pattern_type'] == 'DOUBLE_WAVE':
            timings_note = '✅ Prédits' if row['timings_predicted'] else '❌ Détectés'
            print(f"{row['date']} : {row['wave2_peak_time']} - {timings_note} - {row['status']}")
    print()
    
    # Statistiques
    double_wave = df_results[df_results['pattern_type'] == 'DOUBLE_WAVE']
    if not double_wave.empty:
        timings_pred = len(double_wave[double_wave['timings_predicted'] == True])
        timings_detected = len(double_wave[double_wave['timings_predicted'] == False])
        
        print('Statistiques:')
        print('-'*100)
        print(f'Dates DOUBLE_WAVE : {len(double_wave)}')
        print(f'  Avec timings prédits : {timings_pred} ({timings_pred/len(double_wave)*100:.1f}%)')
        print(f'  Avec timings détectés : {timings_detected} ({timings_detected/len(double_wave)*100:.1f}%)')
        print()

print('='*100)
print('✅ INVESTIGATION TERMINÉE')
print('='*100)




