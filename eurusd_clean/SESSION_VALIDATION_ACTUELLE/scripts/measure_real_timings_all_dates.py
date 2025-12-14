#!/usr/bin/env python3
"""
Mesure Timings Réels Toutes Dates
==================================

Objectif : Mesurer les timings réels (wave1, pullback, wave2) depuis les prix ou pattern détecté
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

# Dates à tester
TEST_DATES = [
    '2025-09-11',  # Clusters multiples (14:30 + 14:45)
    '2025-11-20',  # Un seul cluster (14:30)
    '2025-10-10',  # Clusters multiples
    '2025-06-23',  # Clusters multiples
    '2025-05-29',  # Clusters multiples
    '2025-11-26',  # Clusters multiples
]

print('='*100)
print('MESURE TIMINGS RÉELS TOUTES DATES')
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
        
        if pattern_type != 'DOUBLE_WAVE':
            print(f'ℹ️ Pas un DOUBLE_WAVE (type: {pattern_type})')
            results.append({
                'date': date_str,
                'pattern_type': pattern_type,
                'anchor_time': anchor_time.strftime('%H:%M') if anchor_time else None,
                'wave1_real': None,
                'pullback_real': None,
                'wave2_real': None,
                'source': None
            })
            continue
        
        print(f'📊 Pattern : {pattern_type}')
        print(f'   Anchor time : {anchor_time}')
        print()
        
        # Méthode 1 : Utiliser pattern détecté dans les prix
        pattern_real_result = None
        try:
            import sys
            sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'session120'))
            from double_wave_detector_rev12 import detect_for_date_duckdb_rev12
            
            pattern_date = anchor_time
            if pattern_date.tzinfo is not None:
                pattern_date = pattern_date.replace(tzinfo=None)
            
            pattern_real_result = detect_for_date_duckdb_rev12(
                db_path=str(DB_PATH),
                table='prices_finnhub_m1',
                date=pattern_date,
                tz='Europe/Zurich',
                baseline_mode='prev_close_14_29',
                minutes_after_hint=180,
                trading_window=True,
                debug=False,
                event_time=anchor_time
            )
        except Exception as e:
            print(f'⚠️ Erreur détection pattern: {e}')
        
        # Extraire timings réels
        wave1_real = None
        pullback_real = None
        wave2_real = None
        source = None
        
        if pattern_real_result and pattern_real_result.get('double_wave', False):
            # Utiliser timings du pattern détecté
            peak1_time = pattern_real_result.get('peak1_time')
            pullback1_time = pattern_real_result.get('pullback1_time')
            peak2_time = pattern_real_result.get('peak2_time')
            
            if peak1_time:
                wave1_real = pd.to_datetime(peak1_time)
            if pullback1_time:
                pullback_real = pd.to_datetime(pullback1_time)
            if peak2_time:
                wave2_real = pd.to_datetime(peak2_time)
            
            source = 'pattern_detected'
            
            print(f'✅ Timings depuis pattern détecté:')
            if wave1_real:
                print(f'   Wave1 : {wave1_real.strftime("%H:%M")}')
            if pullback_real:
                print(f'   Pullback : {pullback_real.strftime("%H:%M")}')
            if wave2_real:
                print(f'   Wave2 : {wave2_real.strftime("%H:%M")}')
        else:
            # Fallback : Utiliser timings depuis pattern_info (timings prédits actuels)
            wave1_pred = pattern_info.get('wave1_peak_time')
            pullback_pred = pattern_info.get('pullback_low_time')
            wave2_pred = pattern_info.get('wave2_peak_time')
            
            if wave1_pred:
                wave1_real = pd.to_datetime(wave1_pred)
            if pullback_pred:
                pullback_real = pd.to_datetime(pullback_pred)
            if wave2_pred:
                wave2_real = pd.to_datetime(wave2_pred)
            
            source = 'pattern_info_fallback'
            
            print(f'⚠️ Pattern non détecté, utilisation timings depuis pattern_info:')
            if wave1_real:
                print(f'   Wave1 : {wave1_real.strftime("%H:%M")}')
            if pullback_real:
                print(f'   Pullback : {pullback_real.strftime("%H:%M")}')
            if wave2_real:
                print(f'   Wave2 : {wave2_real.strftime("%H:%M")}')
        
        # Calculer écarts depuis anchor_time
        if wave1_real and anchor_time:
            delta_w1 = (wave1_real - anchor_time).total_seconds() / 60.0
            print(f'   → Wave1 : T+{delta_w1:.0f} min')
        if pullback_real and anchor_time:
            delta_pb = (pullback_real - anchor_time).total_seconds() / 60.0
            print(f'   → Pullback : T+{delta_pb:.0f} min')
        if wave2_real and anchor_time:
            delta_w2 = (wave2_real - anchor_time).total_seconds() / 60.0
            print(f'   → Wave2 : T+{delta_w2:.0f} min')
        
        results.append({
            'date': date_str,
            'pattern_type': pattern_type,
            'anchor_time': anchor_time.strftime('%H:%M') if anchor_time else None,
            'wave1_real': wave1_real.strftime('%H:%M') if wave1_real else None,
            'pullback_real': pullback_real.strftime('%H:%M') if pullback_real else None,
            'wave2_real': wave2_real.strftime('%H:%M') if wave2_real else None,
            'wave1_delta_min': (wave1_real - anchor_time).total_seconds() / 60.0 if wave1_real and anchor_time else None,
            'pullback_delta_min': (pullback_real - anchor_time).total_seconds() / 60.0 if pullback_real and anchor_time else None,
            'wave2_delta_min': (wave2_real - anchor_time).total_seconds() / 60.0 if wave2_real and anchor_time else None,
            'source': source
        })
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        print()

# Sauvegarder résultats
df_results = pd.DataFrame(results)
output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'real_timings_all_dates.csv'
output_file.parent.mkdir(parents=True, exist_ok=True)
df_results.to_csv(output_file, index=False)

print('='*100)
print('📊 RÉSUMÉ')
print('='*100)
print()

if not df_results.empty:
    print('Timings réels mesurés:')
    print('-'*100)
    for _, row in df_results.iterrows():
        if row['pattern_type'] == 'DOUBLE_WAVE':
            print(f"{row['date']} ({row['anchor_time']}):")
            print(f"  Wave1 : {row['wave1_real']} (T+{row['wave1_delta_min']:.0f} min)" if row['wave1_real'] else "  Wave1 : N/A")
            print(f"  Pullback : {row['pullback_real']} (T+{row['pullback_delta_min']:.0f} min)" if row['pullback_real'] else "  Pullback : N/A")
            print(f"  Wave2 : {row['wave2_real']} (T+{row['wave2_delta_min']:.0f} min)" if row['wave2_real'] else "  Wave2 : N/A")
            print(f"  Source : {row['source']}")
            print()

print(f'✅ Résultats sauvegardés : {output_file}')
print('='*100)
print('✅ MESURE TERMINÉE')
print('='*100)




