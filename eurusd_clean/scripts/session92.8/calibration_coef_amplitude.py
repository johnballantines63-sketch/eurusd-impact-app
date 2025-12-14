#!/usr/bin/env python3
"""
CALIBRATION COEFFICIENT AMPLITUDE - 4 DATES
============================================

Calibre le coefficient amplitude pour optimiser MAE sur 4 dates.

Méthodologie :
1. Calcul coefficient optimal sur 11.09 (cas référence)
2. Test coef optimal sur 3 autres dates
3. Grid search pour trouver coef optimal global (4 dates)
4. Comparaison avec coef actuel (0.100 Session 92.13)

Session : 92.14
Date : 29 octobre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Dict

# Ajouter paths
root = Path(__file__).parent.parent.parent.parent
src_path = root / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

# Imports
from formulas_validated import calculate_adjusted_empirical_score, calculate_impact_d, calculate_amplification_extended
from amplitude_analysis import analyze_price_trend_complete

print("=" * 80)
print("🔬 CALIBRATION COEFFICIENT AMPLITUDE")
print("=" * 80)
print()

# ════════════════════════════════════════════════════════════════
# DONNÉES TEST (identiques au script précédent)
# ════════════════════════════════════════════════════════════════

TEST_CASES = [
    {
        'date': '2025-09-11',
        'impact_real': 51.7,
        'impact_base': 59.8,
        'score_v2': -0.287,
        'trend': 'BAISSIER',
        'amplitude': 29.1,
        'duration': 24.0,
        'note': 'Cas référence Session 92.13'
    },
    {
        'date': '2025-01-15',
        'impact_real': 49.9,
        'impact_base': 49.0,
        'score_v2': 0.450,
        'trend': 'HAUSSIER',
        'amplitude': 45.2,
        'duration': 24.0,
        'note': 'Cas validé'
    },
    {
        'date': '2025-05-13',
        'impact_real': 34.0,
        'impact_base': 126.5,
        'score_v2': 0.000,
        'trend': 'NEUTRE',
        'amplitude': 0.0,
        'duration': 0.0,
        'note': 'Outlier surprise -108.5%'
    },
    {
        'date': '2025-07-15',
        'impact_real': 24.6,
        'impact_base': 89.7,
        'score_v2': 0.000,
        'trend': 'HAUSSIER',
        'amplitude': 15.8,
        'duration': 0.0,
        'note': 'Outlier géopolitique'
    }
]

COEF_CURRENT = 0.100  # Session 92.13

# ════════════════════════════════════════════════════════════════
# FONCTIONS
# ════════════════════════════════════════════════════════════════

def calculate_impact_with_coef(impact_base: float, score_v2: float, coef: float) -> float:
    """Calcule impact avec coefficient donné"""
    adjustment = 1.0 + (score_v2 * coef)
    return impact_base * adjustment


def calculate_optimal_coef_single_case(impact_base: float, impact_real: float, score_v2: float) -> float:
    """
    Calcule coefficient optimal pour un cas donné
    
    Formule :
    impact_real = impact_base × (1 + score_v2 × coef)
    
    Résolution :
    coef = (impact_real/impact_base - 1) / score_v2
    """
    if score_v2 == 0:
        return None  # Pas de tendance, coefficient indéterminé
    
    ratio = impact_real / impact_base
    coef = (ratio - 1.0) / score_v2
    
    return coef


def calculate_mae_with_coef(test_cases: List[Dict], coef: float) -> float:
    """Calcule MAE sur tous les cas avec coefficient donné"""
    errors = []
    
    for case in test_cases:
        impact_pred = calculate_impact_with_coef(
            case['impact_base'],
            case['score_v2'],
            coef
        )
        error = abs(impact_pred - case['impact_real'])
        errors.append(error)
    
    return np.mean(errors)


def grid_search_optimal_coef(test_cases: List[Dict], coef_range: tuple, num_points: int = 100) -> Dict:
    """
    Grid search pour trouver coefficient optimal
    
    Args:
        test_cases: Liste des cas test
        coef_range: (min, max) pour la recherche
        num_points: Nombre de points à tester
    
    Returns:
        dict avec coef_optimal, mae_optimal, résultats détaillés
    """
    coef_min, coef_max = coef_range
    coefs = np.linspace(coef_min, coef_max, num_points)
    
    results = []
    
    for coef in coefs:
        mae = calculate_mae_with_coef(test_cases, coef)
        results.append({
            'coef': coef,
            'mae': mae
        })
    
    # Trouver optimal
    results_df = pd.DataFrame(results)
    idx_optimal = results_df['mae'].idxmin()
    optimal = results_df.iloc[idx_optimal]
    
    return {
        'coef_optimal': optimal['coef'],
        'mae_optimal': optimal['mae'],
        'results': results_df
    }


# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : COEFFICIENT OPTIMAL CAS RÉFÉRENCE (11.09)
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📊 ÉTAPE 1 : COEFFICIENT OPTIMAL CAS RÉFÉRENCE (11.09)")
print("=" * 80)
print()

ref_case = TEST_CASES[0]

print(f"📌 CAS RÉFÉRENCE : {ref_case['date']}")
print(f"   Impact base : {ref_case['impact_base']:.1f} pips")
print(f"   Impact réel : {ref_case['impact_real']:.1f} pips")
print(f"   Score V2 : {ref_case['score_v2']:.3f}")
print(f"   Tendance : {ref_case['trend']} ({ref_case['duration']:.0f}h, {ref_case['amplitude']:.1f} pips)")
print()

coef_optimal_ref = calculate_optimal_coef_single_case(
    ref_case['impact_base'],
    ref_case['impact_real'],
    ref_case['score_v2']
)

print(f"🎯 COEFFICIENT OPTIMAL (11.09) : {coef_optimal_ref:.3f}")
print(f"   Coefficient actuel (S92.13) : {COEF_CURRENT:.3f}")
print(f"   Écart : {(coef_optimal_ref - COEF_CURRENT):.3f} ({(coef_optimal_ref/COEF_CURRENT - 1)*100:+.1f}%)")
print()

# Vérification
impact_pred = calculate_impact_with_coef(ref_case['impact_base'], ref_case['score_v2'], coef_optimal_ref)
print(f"✅ VÉRIFICATION :")
print(f"   Impact prédit (coef {coef_optimal_ref:.3f}) : {impact_pred:.1f} pips")
print(f"   Impact réel : {ref_case['impact_real']:.1f} pips")
print(f"   Erreur : {abs(impact_pred - ref_case['impact_real']):.1f} pips")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : TEST COEF OPTIMAL SUR AUTRES DATES
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📊 ÉTAPE 2 : TEST COEF OPTIMAL SUR 3 AUTRES DATES")
print("=" * 80)
print()

print(f"📌 TEST COEFFICIENT {coef_optimal_ref:.3f} (optimal 11.09)")
print()

results_optimal_ref = []

for case in TEST_CASES:
    # Avec coef actuel (0.100)
    impact_current = calculate_impact_with_coef(
        case['impact_base'],
        case['score_v2'],
        COEF_CURRENT
    )
    error_current = abs(impact_current - case['impact_real'])
    
    # Avec coef optimal ref (11.09)
    impact_optimal = calculate_impact_with_coef(
        case['impact_base'],
        case['score_v2'],
        coef_optimal_ref
    )
    error_optimal = abs(impact_optimal - case['impact_real'])
    
    improvement = error_current - error_optimal
    
    results_optimal_ref.append({
        'date': case['date'],
        'impact_real': case['impact_real'],
        'impact_current': impact_current,
        'impact_optimal': impact_optimal,
        'error_current': error_current,
        'error_optimal': error_optimal,
        'improvement': improvement
    })

df_optimal_ref = pd.DataFrame(results_optimal_ref)

print(f"{'Date':<12} {'Réel':>6} {'Cur':>6} {'Opt':>6} {'Err.Cur':>8} {'Err.Opt':>9} {'Amélio.':>8}")
print("-" * 80)
for _, row in df_optimal_ref.iterrows():
    print(f"{row['date']:<12} {row['impact_real']:>6.1f} {row['impact_current']:>6.1f} {row['impact_optimal']:>6.1f} "
          f"{row['error_current']:>8.1f} {row['error_optimal']:>9.1f} {row['improvement']:>+7.1f}")
print()

mae_current = df_optimal_ref['error_current'].mean()
mae_optimal_ref = df_optimal_ref['error_optimal'].mean()
improvement_mae = mae_current - mae_optimal_ref

print(f"📊 MAE COMPARAISON")
print(f"   MAE coef actuel ({COEF_CURRENT:.3f}) : {mae_current:.2f} pips")
print(f"   MAE coef optimal ({coef_optimal_ref:.3f}) : {mae_optimal_ref:.2f} pips")
print(f"   Amélioration : {improvement_mae:+.2f} pips ({improvement_mae/mae_current*100:+.1f}%)")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : GRID SEARCH COEFFICIENT OPTIMAL GLOBAL
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📊 ÉTAPE 3 : GRID SEARCH COEFFICIENT OPTIMAL GLOBAL (4 DATES)")
print("=" * 80)
print()

print("🔍 Recherche coefficient optimal sur 4 dates...")
print(f"   Range : 0.000 - 1.000")
print(f"   Points testés : 200")
print()

grid_result = grid_search_optimal_coef(TEST_CASES, coef_range=(0.0, 1.0), num_points=200)

coef_optimal_global = grid_result['coef_optimal']
mae_optimal_global = grid_result['mae_optimal']

print(f"🎯 RÉSULTATS GRID SEARCH")
print(f"   Coefficient optimal global : {coef_optimal_global:.3f}")
print(f"   MAE optimal : {mae_optimal_global:.2f} pips")
print()

# Comparaison 3 coefficients
print("📊 COMPARAISON 3 COEFFICIENTS")
print()

mae_current = calculate_mae_with_coef(TEST_CASES, COEF_CURRENT)
mae_ref = calculate_mae_with_coef(TEST_CASES, coef_optimal_ref)
mae_global = calculate_mae_with_coef(TEST_CASES, coef_optimal_global)

print(f"   1. Coef actuel ({COEF_CURRENT:.3f})       : MAE {mae_current:.2f} pips")
print(f"   2. Coef optimal 11.09 ({coef_optimal_ref:.3f}) : MAE {mae_ref:.2f} pips ({(mae_ref-mae_current):+.2f})")
print(f"   3. Coef optimal global ({coef_optimal_global:.3f}) : MAE {mae_global:.2f} pips ({(mae_global-mae_current):+.2f})")
print()

# Meilleur coefficient
best_coef = coef_optimal_global
best_mae = mae_global

if mae_ref < best_mae:
    best_coef = coef_optimal_ref
    best_mae = mae_ref

print(f"🏆 MEILLEUR COEFFICIENT : {best_coef:.3f}")
print(f"   MAE : {best_mae:.2f} pips")
print(f"   Amélioration vs actuel : {(mae_current - best_mae):+.2f} pips ({(mae_current - best_mae)/mae_current*100:+.1f}%)")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 4 : TEST DÉTAILLÉ MEILLEUR COEFFICIENT
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print(f"📊 ÉTAPE 4 : TEST DÉTAILLÉ COEFFICIENT {best_coef:.3f}")
print("=" * 80)
print()

results_best = []

for case in TEST_CASES:
    impact_pred = calculate_impact_with_coef(
        case['impact_base'],
        case['score_v2'],
        best_coef
    )
    error = abs(impact_pred - case['impact_real'])
    error_pct = (error / case['impact_real']) * 100
    
    results_best.append({
        'date': case['date'],
        'impact_real': case['impact_real'],
        'impact_pred': impact_pred,
        'error': error,
        'error_pct': error_pct,
        'score_v2': case['score_v2'],
        'trend': case['trend'],
        'note': case['note']
    })

df_best = pd.DataFrame(results_best)

print(f"{'Date':<12} {'Réel':>6} {'Prédit':>7} {'Erreur':>7} {'Err %':>6} {'Score V2':>9} {'Tendance':<10}")
print("-" * 90)
for _, row in df_best.iterrows():
    print(f"{row['date']:<12} {row['impact_real']:>6.1f} {row['impact_pred']:>7.1f} {row['error']:>7.1f} "
          f"{row['error_pct']:>6.1f} {row['score_v2']:>9.3f} {row['trend']:<10}")
print()

# Statistiques
mae_best = df_best['error'].mean()
rmse_best = np.sqrt((df_best['error'] ** 2).mean())
max_error = df_best['error'].max()
min_error = df_best['error'].min()

print("📊 STATISTIQUES FINALES")
print(f"   MAE : {mae_best:.2f} pips")
print(f"   RMSE : {rmse_best:.2f} pips")
print(f"   Erreur max : {max_error:.1f} pips ({df_best.loc[df_best['error'].idxmax(), 'date']})")
print(f"   Erreur min : {min_error:.1f} pips ({df_best.loc[df_best['error'].idxmin(), 'date']})")
print()

# ════════════════════════════════════════════════════════════════
# DÉCISION FINALE
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("🎯 DÉCISION FINALE")
print("=" * 80)
print()

improvement_pct = ((mae_current - best_mae) / mae_current) * 100

if best_mae < mae_current and improvement_pct > 5:
    print("✅ RECOMMANDATION : ADOPTER NOUVEAU COEFFICIENT")
    print()
    print(f"   Coefficient recommandé : {best_coef:.3f}")
    print(f"   Coefficient actuel : {COEF_CURRENT:.3f}")
    print(f"   Changement : {(best_coef - COEF_CURRENT):+.3f} ({(best_coef/COEF_CURRENT - 1)*100:+.1f}%)")
    print()
    print(f"   MAE actuel : {mae_current:.2f} pips")
    print(f"   MAE nouveau : {best_mae:.2f} pips")
    print(f"   Amélioration : {(mae_current - best_mae):+.2f} pips ({improvement_pct:+.1f}%)")
    print()
    print("   Action : Mettre à jour COEF_AMPLITUDE_ADJUSTMENT dans formulas_validated_v2.py")
    
elif best_mae < mae_current:
    print("⚠️ RECOMMANDATION : AMÉLIORATION MARGINALE")
    print()
    print(f"   Amélioration : {improvement_pct:+.1f}% (< 5% seuil)")
    print(f"   Coefficient actuel {COEF_CURRENT:.3f} reste acceptable")
    print()
    print("   Action : Garder coefficient actuel ou tester sur plus de dates")

else:
    print("❌ RECOMMANDATION : GARDER COEFFICIENT ACTUEL")
    print()
    print(f"   Coefficient actuel {COEF_CURRENT:.3f} est optimal")
    print()
    print("   Action : Aucun changement nécessaire")

print()
print("=" * 80)
print("CALIBRATION TERMINÉE")
print("=" * 80)
