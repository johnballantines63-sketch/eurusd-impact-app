#!/usr/bin/env python3
"""
Mesure Impact Réel Correcte
============================

Objectif : Mesurer l'impact réel en utilisant le bon pic selon le pattern :
- DOUBLE_WAVE : Utiliser wave2_peak_pips_absolute (pic 2)
- SINGLE_WAVE : Utiliser wave1_peak_pips_absolute (pic unique)
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import pytz

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

# Dates à mesurer
TEST_DATES = [
    '2025-09-11',
    '2025-08-01',
    '2025-11-20',
    '2025-10-10',
    '2025-06-23',
    '2025-01-15',
    '2025-05-29',
    '2024-09-11',
    '2025-02-12',
    '2025-11-26',
]

print('='*100)
print('MESURE IMPACT RÉEL CORRECTE')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

results = []

for date_str in TEST_DATES:
    print('='*100)
    print(f'📅 MESURE : {date_str}')
    print('='*100)
    print()
    
    try:
        # 1. Exécuter pipeline pour obtenir pattern
        result_pipeline = executor.execute_complete_pipeline(date_str)
        
        if not result_pipeline.get('success'):
            print(f'❌ Erreur pipeline: {result_pipeline.get("error")}')
            results.append({
                'date': date_str,
                'success': False,
                'error': result_pipeline.get('error', 'Unknown')
            })
            continue
        
        final_pred = result_pipeline.get('final_prediction', {})
        pattern_info = final_pred.get('pattern_info', {})
        cluster_info = result_pipeline.get('results', {}).get('etape3_cluster_info', {})
        cluster = cluster_info.get('cluster', {})
        anchor_time = cluster.get('anchor_time')
        
        pattern_type = pattern_info.get('pattern_type', 'NONE')
        wave1_pips = pattern_info.get('wave1_pips', 0.0)
        wave2_pips = pattern_info.get('wave2_pips', 0.0)
        wave1_peak_pips_absolute = pattern_info.get('wave1_peak_pips_absolute', 0.0)
        wave2_peak_pips_absolute = pattern_info.get('wave2_peak_pips_absolute', 0.0)
        baseline_price = pattern_info.get('baseline_price', 0.0)
        
        print(f'Pattern détecté : {pattern_type}')
        print(f'Anchor time : {anchor_time}')
        print()
        
        # 2. Déterminer impact réel selon pattern
        if pattern_type == 'DOUBLE_WAVE':
            # Pour DOUBLE_WAVE : utiliser wave2_peak_pips_absolute (pic 2)
            impact_real = wave2_peak_pips_absolute
            peak_used = 'wave2_peak_pips_absolute'
            print(f'✅ DOUBLE_WAVE détecté')
            print(f'   Wave1 : {wave1_pips:.2f} pips')
            print(f'   Wave2 : {wave2_pips:.2f} pips')
            print(f'   Wave2 peak (absolute) : {wave2_peak_pips_absolute:.2f} pips')
            print(f'   → Impact réel = Wave2 peak (absolute) = {impact_real:.2f} pips')
            
        elif pattern_type in ['SINGLE_WAVE_STRONG', 'SINGLE_WAVE_STANDARD']:
            # Pour SINGLE_WAVE : utiliser wave1_peak_pips_absolute (pic unique)
            impact_real = wave1_peak_pips_absolute if wave1_peak_pips_absolute > 0 else wave2_peak_pips_absolute
            peak_used = 'wave1_peak_pips_absolute'
            print(f'✅ {pattern_type} détecté')
            print(f'   Wave1 peak (absolute) : {wave1_peak_pips_absolute:.2f} pips')
            print(f'   → Impact réel = Wave1 peak (absolute) = {impact_real:.2f} pips')
            
        else:
            # Fallback : utiliser wave2_peak_pips_absolute ou wave1_peak_pips_absolute
            impact_real = wave2_peak_pips_absolute if wave2_peak_pips_absolute > 0 else wave1_peak_pips_absolute
            peak_used = 'fallback'
            print(f'⚠️ Pattern {pattern_type} : Utilisation fallback')
            print(f'   → Impact réel = {impact_real:.2f} pips')
        
        # 3. Obtenir peak_time depuis pattern_info
        peak_time = pattern_info.get('peak2_time') if pattern_type == 'DOUBLE_WAVE' else pattern_info.get('peak1_time')
        if peak_time is None:
            peak_time = pattern_info.get('wave2_peak_time') if pattern_type == 'DOUBLE_WAVE' else pattern_info.get('wave1_peak_time')
        
        # 4. Obtenir peak_price depuis pattern_info ou calculer
        peak_price = pattern_info.get('peak2_price') if pattern_type == 'DOUBLE_WAVE' else pattern_info.get('peak1_price')
        if peak_price is None or peak_price == 0:
            # Calculer depuis baseline + impact
            if baseline_price and baseline_price > 0:
                direction = pattern_info.get('pattern_direction', 1)
                if direction == 1:  # UP
                    peak_price = baseline_price + (impact_real / 10000)
                else:  # DOWN
                    peak_price = baseline_price - (impact_real / 10000)
            else:
                peak_price = 0.0
        
        # 5. Obtenir direction
        direction = pattern_info.get('pattern_direction', 1)
        if direction == 1:
            direction_str = 'UP'
        elif direction == -1:
            direction_str = 'DOWN'
        else:
            direction_str = 'UNKNOWN'
        
        print()
        print(f'📊 RÉSULTAT FINAL')
        print('-'*100)
        print(f'Impact réel : {impact_real:.2f} pips')
        print(f'Peak utilisé : {peak_used}')
        print(f'Peak time : {peak_time}')
        print(f'Peak price : {peak_price:.5f}' if peak_price and peak_price > 0 else 'Peak price : N/A')
        print(f'Direction : {direction_str}')
        print()
        
        # Enregistrer résultat
        results.append({
            'date': date_str,
            'success': True,
            'pattern_type': pattern_type,
            'anchor_time': str(anchor_time),
            'impact_real_pips': impact_real,
            'baseline_price': baseline_price if baseline_price else 0.0,
            'peak_price': peak_price if peak_price else 0.0,
            'peak_time': str(peak_time) if peak_time else None,
            'direction': direction,
            'wave1_pips': wave1_pips if wave1_pips else 0.0,
            'wave2_pips': wave2_pips if wave2_pips else 0.0,
            'wave1_peak_pips_absolute': wave1_peak_pips_absolute if wave1_peak_pips_absolute else 0.0,
            'wave2_peak_pips_absolute': wave2_peak_pips_absolute if wave2_peak_pips_absolute else 0.0,
            'peak_used': peak_used
        })
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        results.append({
            'date': date_str,
            'success': False,
            'error': str(e)
        })
        print()

# Créer DataFrame et sauvegarder
df_results = pd.DataFrame(results)

# Créer CSV avec format correct
df_csv = df_results[df_results['success'] == True].copy()
df_csv = df_csv[[
    'date',
    'anchor_time',
    'pattern_type',
    'impact_real_pips',
    'baseline_price',
    'peak_price',
    'peak_time',
    'direction',
    'wave1_pips',
    'wave2_pips',
    'wave1_peak_pips_absolute',
    'wave2_peak_pips_absolute',
    'peak_used'
]].copy()

# Ajouter colonnes pour compatibilité
df_csv['event_time'] = df_csv['anchor_time'].apply(lambda x: pd.to_datetime(x).strftime('%H:%M') if pd.notna(x) else '14:30')
df_csv['timezone'] = 'Europe/Zurich'
df_csv['notes'] = df_csv.apply(
    lambda row: f"{row['pattern_type']} - Pic utilisé: {row['peak_used']}", axis=1
)

# Réorganiser colonnes
df_csv = df_csv[[
    'date',
    'event_time',
    'timezone',
    'impact_real_pips',
    'baseline_price',
    'peak_price',
    'peak_time',
    'direction',
    'pattern_type',
    'wave1_pips',
    'wave2_pips',
    'wave1_peak_pips_absolute',
    'wave2_peak_pips_absolute',
    'peak_used',
    'notes'
]]

# Sauvegarder
output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'impacts_reels_mesures_CORRECT.csv'
output_file.parent.mkdir(parents=True, exist_ok=True)
df_csv.to_csv(output_file, index=False)

print('='*100)
print('📊 RÉSUMÉ')
print('='*100)
print()

df_success = df_results[df_results['success'] == True]

if not df_success.empty:
    print(f'✅ Dates mesurées avec succès : {len(df_success)}/{len(TEST_DATES)}')
    print()
    
    print(f'📋 DÉTAILS PAR DATE')
    print('-'*100)
    for _, row in df_success.iterrows():
        print(f'{row["date"]} ({row["pattern_type"]}) : {row["impact_real_pips"]:.2f} pips (pic utilisé: {row["peak_used"]})')
    print()

print(f'💾 CSV sauvegardé : {output_file}')
print()
print('='*100)
print('✅ MESURE TERMINÉE')
print('='*100)
