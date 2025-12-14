#!/usr/bin/env python3
"""
Debug Calcul Prédiction
========================

Objectif : Comprendre pourquoi la prédiction finale est si faible pour 2025-05-29 et 2025-06-23
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

PROBLEMATIC_DATES = [
    '2025-06-23',  # Impact base = nan, prédit = 15.50, réel = 88.60
    '2025-05-29',  # Impact base = 71.17, amplification = 5.740x, base×amp = 408.49, prédit = 15.00, réel = 74.40
]

print('='*100)
print('DEBUG CALCUL PRÉDICTION')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=True)

for date_str in PROBLEMATIC_DATES:
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
        
        # Extraire toutes les valeurs intermédiaires
        impact_base = final_pred.get('impact_base', 0.0)
        amplification = final_pred.get('amplification_predite', 1.0)
        impact_predicted = final_pred.get('prediction_finale', 0.0)
        amplification_method = final_pred.get('amplification_method', 'unknown')
        
        # Vérifier stratégie hybride
        prediction_method = final_pred.get('prediction_method', 'unknown')
        
        # Extraire pattern info
        pattern_type = pattern_info.get('pattern_type', 'UNKNOWN') if pattern_info else 'UNKNOWN'
        pattern_impact = pattern_info.get('pattern_impact', 0.0) if pattern_info else 0.0
        pattern_confidence = pattern_info.get('confidence', 0.0) if pattern_info else 0.0
        
        # Calculer impact_formules
        impact_formules = impact_base * amplification if pd.notna(impact_base) else 0.0
        
        print('📊 VALEURS INTERMÉDIAIRES')
        print('-'*100)
        print(f'Impact base : {impact_base:.2f} pips' if pd.notna(impact_base) else 'Impact base : NaN')
        print(f'Amplification : {amplification:.3f}x ({amplification_method})')
        print(f'Impact formules (base × amp) : {impact_formules:.2f} pips')
        print()
        
        print('📊 PATTERN')
        print('-'*100)
        print(f'Pattern type : {pattern_type}')
        print(f'Pattern impact : {pattern_impact:.2f} pips')
        print(f'Pattern confidence : {pattern_confidence:.1f}%')
        print()
        
        print('📊 PRÉDICTION FINALE')
        print('-'*100)
        print(f'Impact prédit final : {impact_predicted:.2f} pips')
        print(f'Méthode prédiction : {prediction_method}')
        print()
        
        # Analyser pourquoi la prédiction est faible
        print('🔍 ANALYSE')
        print('-'*100)
        
        if pd.isna(impact_base):
            print('❌ PROBLÈME 1 : Impact base est NaN')
            print('   → Le calcul d\'impact base a échoué')
            print('   → Vérifier étape 8.1 (calcul impact base)')
            print()
        else:
            if impact_formules > impact_predicted * 2:
                print(f'⚠️ PROBLÈME 2 : Impact formules ({impact_formules:.2f}) >> Impact prédit ({impact_predicted:.2f})')
                print(f'   → La stratégie hybride a réduit la prédiction')
                print()
                
                if prediction_method == 'pattern':
                    print(f'   → Méthode utilisée : Pattern ({pattern_impact:.2f} pips)')
                    print(f'   → Pattern confidence : {pattern_confidence:.1f}%')
                    if pattern_impact < impact_formules * 0.5:
                        print(f'   ⚠️ Pattern impact ({pattern_impact:.2f}) est beaucoup plus faible que formules ({impact_formules:.2f})')
                        print(f'      → Le pattern détecté sous-estime le mouvement')
                elif prediction_method == 'formulas':
                    print(f'   → Méthode utilisée : Formules')
                    print(f'   ⚠️ Mais impact prédit ({impact_predicted:.2f}) ≠ impact formules ({impact_formules:.2f})')
                    print(f'      → Il y a peut-être des ajustements S/R ou patterns appliqués')
                else:
                    print(f'   → Méthode utilisée : {prediction_method}')
        
        # Vérifier ajustements
        sr_adjustment = final_pred.get('sr_adjustment_pct', 0.0)
        pattern_adjustment = final_pred.get('pattern_adjustment_pct', 0.0)
        
        if sr_adjustment != 0 or pattern_adjustment != 0:
            print()
            print('📊 AJUSTEMENTS')
            print('-'*100)
            print(f'Ajustement S/R : {sr_adjustment:.1f}%')
            print(f'Ajustement pattern : {pattern_adjustment:.1f}%')
            print()
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        continue

print('='*100)
print('✅ DEBUG TERMINÉ')
print('='*100)




