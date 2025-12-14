#!/usr/bin/env python3
"""
Debug wave2_peak_pips_absolute
================================

Objectif : Comprendre pourquoi wave2_peak_pips_absolute = 15.00 au lieu de 74.40
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

DATE = '2025-05-29'

print('='*100)
print('DEBUG wave2_peak_pips_absolute')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=True)

result = executor.execute_complete_pipeline(DATE)

if result.get('success'):
    final_pred = result.get('final_prediction', {})
    pattern_info = final_pred.get('pattern_info', {})
    
    print('='*100)
    print('VALEURS FINALES')
    print('='*100)
    print()
    
    if pattern_info:
        print('Pattern info:')
        print(f'  wave1_pips: {pattern_info.get("wave1_pips", "N/A")}')
        print(f'  wave2_pips: {pattern_info.get("wave2_pips", "N/A")}')
        print(f'  wave1_peak_pips_absolute: {pattern_info.get("wave1_peak_pips_absolute", "N/A")}')
        print(f'  wave2_peak_pips_absolute: {pattern_info.get("wave2_peak_pips_absolute", "N/A")}')
        print(f'  wave1_amp_pips: {pattern_info.get("wave1_amp_pips", "N/A")}')
        print(f'  wave2_amp_pips: {pattern_info.get("wave2_amp_pips", "N/A")}')
        print()
    
    # Vérifier si pattern_real_result est accessible
    # Il n'est pas dans final_prediction, mais peut-être dans les logs ou résultats intermédiaires
    
    print('Vérification dans les logs du pipeline...')
    print('(Les valeurs intermédiaires ne sont pas stockées dans le résultat final)')
    print()




