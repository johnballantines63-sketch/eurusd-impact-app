#!/usr/bin/env python3
"""
Vérifier Utilisation Random Forest
===================================

Objectif : Vérifier si le Random Forest est utilisé dans les cas de test
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
    '2025-08-01',
]

print('='*100)
print('VÉRIFICATION UTILISATION RANDOM FOREST')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

results = []

for date_str in TEST_DATES:
    print(f'📅 {date_str}...', end=' ', flush=True)
    
    try:
        result = executor.execute_complete_pipeline(date_str)
        
        if not result.get('success'):
            print(f'❌ Erreur')
            continue
        
        final_pred = result.get('final_prediction', {})
        
        # Vérifier la méthode d'amplification utilisée
        # Note: La méthode n'est pas directement dans final_prediction
        # Il faut vérifier dans les logs ou dans les résultats intermédiaires
        
        # Extraire informations
        impact_base = final_pred.get('impact_base', 0.0)
        amplification = final_pred.get('amplification_predite', 1.0)
        impact_predicted = final_pred.get('prediction_finale', 0.0)
        
        # Vérifier si RF a été utilisé en regardant les résultats de l'étape 4
        results_data = result.get('results', {})
        identical_clusters = results_data.get('etape4_identical_clusters', [])
        num_clusters = len(identical_clusters) if identical_clusters else 0
        
        # Vérifier la surprise maximale
        pattern_info = final_pred.get('pattern_info', {})
        
        # Estimer si RF a été utilisé
        # RF est utilisé si :
        # 1. Surprise <= 100% (pas de formule Session 88)
        # 2. num_clusters >= 5
        # 3. amplification_method = 'random_forest'
        
        # Pour l'instant, on ne peut que vérifier les conditions
        rf_eligible = num_clusters >= 5
        
        results.append({
            'date': date_str,
            'num_clusters_identiques': num_clusters,
            'rf_eligible': rf_eligible,
            'impact_base': impact_base,
            'amplification': amplification,
            'impact_predicted': impact_predicted
        })
        
        status = '✅ RF éligible' if rf_eligible else '⚠️ RF non éligible'
        print(f'{status} ({num_clusters} clusters)')
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        continue

# Résumé
print()
print('='*100)
print('📊 RÉSUMÉ')
print('='*100)
print()

df_results = pd.DataFrame(results)

if not df_results.empty:
    rf_eligible_count = len(df_results[df_results['rf_eligible'] == True])
    rf_non_eligible_count = len(df_results[df_results['rf_eligible'] == False])
    
    print(f'Total dates : {len(df_results)}')
    print(f'✅ RF éligible (≥ 5 clusters) : {rf_eligible_count} ({rf_eligible_count/len(df_results)*100:.1f}%)')
    print(f'⚠️ RF non éligible (< 5 clusters) : {rf_non_eligible_count} ({rf_non_eligible_count/len(df_results)*100:.1f}%)')
    print()
    
    print('Détails par date :')
    print('-'*100)
    for _, row in df_results.iterrows():
        status = '✅' if row['rf_eligible'] else '⚠️'
        print(f"{status} {row['date']} : {row['num_clusters_identiques']} clusters identiques, amplification = {row['amplification']:.3f}x")
    
    print()
    print('⚠️ NOTE : Pour savoir si RF a réellement été utilisé, vérifier les logs du pipeline')
    print('   ou ajouter amplification_method dans final_prediction')

print('='*100)
print('✅ VÉRIFICATION TERMINÉE')
print('='*100)




