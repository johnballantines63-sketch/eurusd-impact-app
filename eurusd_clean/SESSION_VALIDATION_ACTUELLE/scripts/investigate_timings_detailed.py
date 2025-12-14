#!/usr/bin/env python3
"""
Investigation Détaillée des Timings
====================================

Objectif : Vérifier en détail les timings pour comprendre les erreurs
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

# Dates DOUBLE_WAVE à vérifier
TEST_DATES = [
    '2025-09-11',
    '2025-11-20',
    '2025-10-10',
    '2025-06-23',
    '2025-05-29',
    '2025-11-26',
]

print('='*100)
print('INVESTIGATION DÉTAILLÉE DES TIMINGS')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

for date_str in TEST_DATES:
    print('='*100)
    print(f'📅 INVESTIGATION : {date_str}')
    print('='*100)
    print()
    
    try:
        result_pipeline = executor.execute_complete_pipeline(date_str)
        
        if not result_pipeline.get('success'):
            print(f'❌ Erreur: {result_pipeline.get("error")}')
            continue
        
        final_pred = result_pipeline.get('final_prediction', {})
        pattern_info = final_pred.get('pattern_info', {})
        cluster_info = result_pipeline.get('results', {}).get('etape3_cluster_info', {})
        cluster = cluster_info.get('cluster', {})
        anchor_time = cluster.get('anchor_time')
        
        pattern_type = pattern_info.get('pattern_type', 'NONE')
        timings_predicted = pattern_info.get('timings_predicted', False)
        
        print(f'Pattern : {pattern_type}')
        print(f'Anchor time : {anchor_time}')
        print(f'Timings prédits : {timings_predicted}')
        print()
        
        if pattern_type == 'DOUBLE_WAVE' and timings_predicted:
            # Timings Session 64 attendus : T+5, T+11, T+15, T+40
            anchor_time_dt = pd.to_datetime(anchor_time)
            
            wave1_peak_time = pattern_info.get('wave1_peak_time')
            pullback_low_time = pattern_info.get('pullback_low_time')
            wave2_peak_time = pattern_info.get('wave2_peak_time')
            stabilization_time = pattern_info.get('stabilization_time')
            
            print(f'⏱️ TIMINGS PRÉDITS (Session 64)')
            print('-'*100)
            
            if wave1_peak_time:
                wave1_dt = pd.to_datetime(wave1_peak_time)
                minutes_from_anchor = (wave1_dt - anchor_time_dt).total_seconds() / 60.0
                error_wave1 = abs(minutes_from_anchor - 5.0)
                print(f'Wave1 peak : {wave1_dt.strftime("%H:%M")} (T+{minutes_from_anchor:.1f} min) - Erreur : {error_wave1:.2f} min (attendu T+5)')
            
            if pullback_low_time:
                pullback_dt = pd.to_datetime(pullback_low_time)
                minutes_from_anchor = (pullback_dt - anchor_time_dt).total_seconds() / 60.0
                error_pullback = abs(minutes_from_anchor - 11.0)
                print(f'Pullback low : {pullback_dt.strftime("%H:%M")} (T+{minutes_from_anchor:.1f} min) - Erreur : {error_pullback:.2f} min (attendu T+11)')
            
            if wave2_peak_time:
                wave2_dt = pd.to_datetime(wave2_peak_time)
                minutes_from_anchor = (wave2_dt - anchor_time_dt).total_seconds() / 60.0
                error_wave2 = abs(minutes_from_anchor - 15.0)
                print(f'Wave2 peak : {wave2_dt.strftime("%H:%M")} (T+{minutes_from_anchor:.1f} min) - Erreur : {error_wave2:.2f} min (attendu T+15)')
            
            if stabilization_time:
                stab_dt = pd.to_datetime(stabilization_time)
                minutes_from_anchor = (stab_dt - anchor_time_dt).total_seconds() / 60.0
                error_stab = abs(minutes_from_anchor - 40.0)
                print(f'Stabilization : {stab_dt.strftime("%H:%M")} (T+{minutes_from_anchor:.1f} min) - Erreur : {error_stab:.2f} min (attendu T+40)')
            
            print()
            
            # Vérifier si tous les timings sont parfaits
            errors = []
            if wave1_peak_time:
                errors.append(error_wave1)
            if pullback_low_time:
                errors.append(error_pullback)
            if wave2_peak_time:
                errors.append(error_wave2)
            if stabilization_time:
                errors.append(error_stab)
            
            if errors:
                max_error = max(errors)
                if max_error < 0.01:
                    print(f'✅ TOUS LES TIMINGS PARFAITS (erreur max: {max_error:.2f} min)')
                elif max_error < 1.0:
                    print(f'✅ TIMINGS EXCELLENTS (erreur max: {max_error:.2f} min)')
                else:
                    print(f'⚠️ CERTAINS TIMINGS ONT DES ERREURS (erreur max: {max_error:.2f} min)')
                    print(f'   → Vérifier pourquoi wave2_peak_time ne correspond pas à T+15')
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        print()

print('='*100)
print('✅ INVESTIGATION TERMINÉE')
print('='*100)




