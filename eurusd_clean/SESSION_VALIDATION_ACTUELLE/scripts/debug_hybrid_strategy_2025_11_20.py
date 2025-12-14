#!/usr/bin/env python3
"""
Debug Stratégie Hybride - 2025-11-20
======================================

Objectif : Comprendre pourquoi prédiction = 1562.98 pips au lieu de ~1420 pips attendu
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

print('='*100)
print('DEBUG STRATÉGIE HYBRIDE - 2025-11-20')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=True)

# Exécuter pipeline avec verbose pour voir tous les logs
result = executor.execute_complete_pipeline('2025-11-20')

if not result.get('success'):
    print(f'❌ Erreur: {result.get("error")}')
    sys.exit(1)

final_pred = result.get('final_prediction', {})
pattern_info = final_pred.get('pattern_info', {})

print()
print('='*100)
print('ANALYSE DÉTAILLÉE')
print('='*100)
print()

# Extraire toutes les valeurs
impact_base = final_pred.get('impact_base', 0)
amplification_predite = final_pred.get('amplification_predite', 1.0)
prediction_finale = final_pred.get('prediction_finale', 0)
prediction_method = final_pred.get('prediction_method', 'unknown')
pattern_type = pattern_info.get('pattern_type', 'NONE')
pattern_direction = pattern_info.get('direction', 'UNKNOWN')

# Calculer impact_formules attendu
# Note: adjustment_factor n'est pas dans final_prediction, on doit le recalculer ou l'estimer
impact_formules_attendu = impact_base * amplification_predite

# Pattern impact
pattern_impact = pattern_info.get('wave2_peak_pips_absolute', 0)
if pattern_impact == 0:
    pattern_impact = pattern_info.get('wave2_pips', 0)

print(f'📊 VALEURS CALCULÉES')
print('-'*100)
print(f'Impact base : {impact_base:.2f} pips')
print(f'Amplification prédite : {amplification_predite:.3f}x')
print(f'Impact formules attendu (sans adjustment) : {impact_formules_attendu:.2f} pips')
print()

print(f'📈 PATTERN DÉTECTÉ')
print('-'*100)
print(f'Pattern type : {pattern_type}')
print(f'Pattern direction : {pattern_direction}')
print(f'Pattern impact (wave2_peak_pips_absolute) : {pattern_info.get("wave2_peak_pips_absolute", 0):.2f} pips')
print(f'Pattern impact (wave2_pips) : {pattern_info.get("wave2_pips", 0):.2f} pips')
print(f'Pattern impact utilisé : {pattern_impact:.2f} pips')
print()

print(f'🎯 PRÉDICTION FINALE')
print('-'*100)
print(f'Prédiction finale : {prediction_finale:.2f} pips')
print(f'Méthode utilisée : {prediction_method}')
print()

# Analyser la logique
print(f'🔍 ANALYSE LOGIQUE STRATÉGIE HYBRIDE')
print('-'*100)

if pattern_type == 'DOUBLE_WAVE':
    print(f'Pattern DOUBLE_WAVE détecté')
    print(f'→ Stratégie : Toujours utiliser formules (stratégie hybride désactivée)')
    print(f'→ Prédiction attendue : impact_formules = impact_base × amplification × adjustment_factor')
    print(f'→ Prédiction réelle : {prediction_finale:.2f} pips')
    print()
    
    # Calculer adjustment_factor nécessaire pour obtenir cette prédiction
    if impact_base > 0 and amplification_predite > 0:
        adjustment_factor_calcule = prediction_finale / (impact_base * amplification_predite)
        print(f'📐 CALCUL ADJUSTMENT_FACTOR')
        print(f'   Pour obtenir {prediction_finale:.2f} pips :')
        print(f'   adjustment_factor = {prediction_finale:.2f} / ({impact_base:.2f} × {amplification_predite:.3f})')
        print(f'   adjustment_factor = {adjustment_factor_calcule:.3f}')
        print()
        
        if adjustment_factor_calcule > 1.5:
            print(f'   ⚠️ ADJUSTMENT_FACTOR TRÈS ÉLEVÉ ({adjustment_factor_calcule:.3f})')
            print(f'   → Vérifier ajustements Support/Résistance et Patterns Finnhub')
        elif adjustment_factor_calcule < 0.5:
            print(f'   ⚠️ ADJUSTMENT_FACTOR TRÈS FAIBLE ({adjustment_factor_calcule:.3f})')
        else:
            print(f'   ✅ ADJUSTMENT_FACTOR raisonnable ({adjustment_factor_calcule:.3f})')
    
    # Vérifier si pattern_impact est utilisé par erreur
    ecart_pattern_vs_formules = abs(pattern_impact - impact_formules_attendu)
    print()
    print(f'📊 COMPARAISON PATTERN vs FORMULES')
    print(f'   Pattern impact : {pattern_impact:.2f} pips')
    print(f'   Formules impact (sans adjustment) : {impact_formules_attendu:.2f} pips')
    print(f'   Écart : {ecart_pattern_vs_formules:.2f} pips')
    print()
    
    if abs(prediction_finale - pattern_impact) < abs(prediction_finale - impact_formules_attendu):
        print(f'   ⚠️ PROBLÈME : Prédiction plus proche de pattern_impact que de impact_formules')
        print(f'   → La stratégie hybride utilise peut-être pattern au lieu de formules !')
    else:
        print(f'   ✅ Prédiction plus proche de impact_formules (stratégie correcte)')
        
elif pattern_type == 'SINGLE_WAVE_STRONG' or pattern_type == 'SINGLE_WAVE':
    print(f'Pattern SINGLE_WAVE détecté')
    print(f'→ Stratégie hybride activée')
    ecart_absolu = abs(pattern_impact - impact_formules_attendu)
    print(f'→ Écart absolu : {ecart_absolu:.2f} pips')
    if ecart_absolu < 10 or pattern_impact == 0:
        print(f'→ Utilise : Formules (écart < 10 pips)')
    else:
        print(f'→ Utilise : Pattern (écart >= 10 pips)')
else:
    print(f'Pattern {pattern_type} détecté')
    print(f'→ Stratégie hybride standard')
    ecart_absolu = abs(pattern_impact - impact_formules_attendu) if pattern_impact > 0 else 0
    print(f'→ Écart absolu : {ecart_absolu:.2f} pips')
    if ecart_absolu < 10 or pattern_impact == 0:
        print(f'→ Utilise : Formules (écart < 10 pips)')
    else:
        print(f'→ Utilise : Pattern (écart >= 10 pips)')

print()

# Vérifier les ajustements
print(f'🔧 AJUSTEMENTS APPLIQUÉS')
print('-'*100)
# Les ajustements ne sont pas dans final_prediction, on doit les déduire
if impact_base > 0 and amplification_predite > 0:
    adjustment_factor = prediction_finale / (impact_base * amplification_predite)
    print(f'Adjustment factor calculé : {adjustment_factor:.3f}')
    print(f'   (1.0 = aucun ajustement, >1.0 = augmentation, <1.0 = réduction)')
    print()
    
    if adjustment_factor > 1.2:
        print(f'   ⚠️ Ajustements très positifs (+{(adjustment_factor-1)*100:.1f}%)')
        print(f'   → Possible : Support/Résistance ou Patterns Finnhub très favorables')
    elif adjustment_factor < 0.8:
        print(f'   ⚠️ Ajustements très négatifs ({(adjustment_factor-1)*100:.1f}%)')
        print(f'   → Possible : Support/Résistance ou Patterns Finnhub défavorables')
    else:
        print(f'   ✅ Ajustements modérés ({(adjustment_factor-1)*100:.1f}%)')

print()




