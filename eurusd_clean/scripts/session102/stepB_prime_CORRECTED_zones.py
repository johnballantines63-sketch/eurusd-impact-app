#!/usr/bin/env python3
"""
ÉTAPE B' : CALIBRATION PAR ZONES (MÉTHODOLOGIE CORRECTE)
=========================================================

CORRECTION : Suivre la VRAIE méthodologie de validation

Méthode :
1. Calculer impact avec amp=2.5 (baseline)
2. Stratégie prédit amp_optimal selon zones
3. Recalculer impact avec amp_optimal
4. Comparer ERREUR EN PIPS vs baseline

Zones basées sur OBSERVATIONS réelles (pas arbitraire)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.model_selection import LeaveOneOut

print("=" * 80)
print("ÉTAPE B' : CALIBRATION PAR ZONES (CORRIGÉ)")
print("=" * 80)
print()

# ============================================================================
# CHARGER DONNÉES
# ============================================================================

data_dir = Path(__file__).parent / "data"
df = pd.read_csv(data_dir / "step5_analyse_finale_CORRECTED.csv")
df['event_date'] = pd.to_datetime(df['event_date'])

print(f"✅ Chargé {len(df)} observations")
print()

# ============================================================================
# BASELINE (amp=2.5 fixe)
# ============================================================================

print("=" * 80)
print("BASELINE (amp=2.5 fixe)")
print("=" * 80)
print()

df['erreur_baseline_pips'] = np.abs(df['impact_real'] - df['impact_predit'])
mae_baseline_pips = df['erreur_baseline_pips'].mean()

print(f"MAE baseline : {mae_baseline_pips:.2f} pips")
print()

# ============================================================================
# OBSERVER ZONES DANS LES DONNÉES
# ============================================================================

print("=" * 80)
print("ÉTAPE 1 : OBSERVER DONNÉES RÉELLES")
print("=" * 80)
print()

# Catégories
df['surprise_cat'] = pd.cut(df['max_surprise'], 
                             bins=[0, 10, 40, 250],
                             labels=['Faible', 'Moyen', 'Fort'])

df['r2_cat'] = pd.cut(df['r_squared'], 
                      bins=[0, 0.3, 0.6, 1.0],
                      labels=['Faible', 'Modéré', 'Fort'])

df['duration_cat'] = pd.cut(df['duration_hours'], 
                             bins=[0, 5, 15, 50],
                             labels=['Court', 'Moyen', 'Long'])

print("Amp parfaite moyenne par SURPRISE :")
for cat in ['Faible', 'Moyen', 'Fort']:
    subset = df[df['surprise_cat'] == cat]
    if len(subset) > 0:
        print(f"   {cat:10s} (N={len(subset):2d}) : {subset['amp_parfaite'].mean():.3f}")
print()

print("Amp parfaite moyenne par R² :")
for cat in ['Faible', 'Modéré', 'Fort']:
    subset = df[df['r2_cat'] == cat]
    if len(subset) > 0:
        print(f"   {cat:10s} (N={len(subset):2d}) : {subset['amp_parfaite'].mean():.3f}")
print()

print("Amp parfaite moyenne par DURÉE :")
for cat in ['Court', 'Moyen', 'Long']:
    subset = df[df['duration_cat'] == cat]
    if len(subset) > 0:
        print(f"   {cat:10s} (N={len(subset):2d}) : {subset['amp_parfaite'].mean():.3f}")
print()

# ============================================================================
# DÉFINIR STRATÉGIES AVEC LOO (RIGOUREUX)
# ============================================================================

print("=" * 80)
print("ÉTAPE 2 : DÉFINIR STRATÉGIES")
print("=" * 80)
print()

def strategy_baseline(row, df_train):
    """Baseline : toujours 2.5 (pas 1.0 !)"""
    return 2.5

def strategy_mean(row, df_train):
    """Moyenne observée dans train"""
    mean_amp = (df_train['impact_real'] / df_train['impact_predit'] * 2.5).mean()
    return mean_amp

def strategy_surprise(row, df_train):
    """Stratégie basée sur surprise (LOO : calculer sur train)"""
    if row['max_surprise'] < 10:
        subset = df_train[df_train['max_surprise'] < 10]
    elif row['max_surprise'] < 40:
        subset = df_train[(df_train['max_surprise'] >= 10) & (df_train['max_surprise'] < 40)]
    else:
        subset = df_train[df_train['max_surprise'] >= 40]
    
    if len(subset) > 0:
        amp_mean = (subset['impact_real'] / subset['impact_predit'] * 2.5).mean()
        return amp_mean
    else:
        return 2.5

def strategy_r2(row, df_train):
    """Stratégie basée sur R² (LOO)"""
    if row['r_squared'] < 0.3:
        subset = df_train[df_train['r_squared'] < 0.3]
    elif row['r_squared'] < 0.6:
        subset = df_train[(df_train['r_squared'] >= 0.3) & (df_train['r_squared'] < 0.6)]
    else:
        subset = df_train[df_train['r_squared'] >= 0.6]
    
    if len(subset) > 0:
        amp_mean = (subset['impact_real'] / subset['impact_predit'] * 2.5).mean()
        return amp_mean
    else:
        return 2.5

def strategy_duration(row, df_train):
    """Stratégie basée sur durée (LOO)"""
    if row['duration_hours'] < 5:
        subset = df_train[df_train['duration_hours'] < 5]
    elif row['duration_hours'] < 15:
        subset = df_train[(df_train['duration_hours'] >= 5) & (df_train['duration_hours'] < 15)]
    else:
        subset = df_train[df_train['duration_hours'] >= 15]
    
    if len(subset) > 0:
        amp_mean = (subset['impact_real'] / subset['impact_predit'] * 2.5).mean()
        return amp_mean
    else:
        return 2.5

def strategy_combined(row, df_train):
    """Combinaison R² + Durée"""
    # Sweet spot
    if 0.3 <= row['r_squared'] <= 0.6 and 5 <= row['duration_hours'] <= 15:
        subset = df_train[
            (df_train['r_squared'] >= 0.3) & (df_train['r_squared'] <= 0.6) &
            (df_train['duration_hours'] >= 5) & (df_train['duration_hours'] <= 15)
        ]
    # Zone risque
    elif row['r_squared'] > 0.7 and row['duration_hours'] < 5:
        subset = df_train[
            (df_train['r_squared'] > 0.7) & (df_train['duration_hours'] < 5)
        ]
    # Autres
    else:
        subset = df_train[
            ~((df_train['r_squared'] >= 0.3) & (df_train['r_squared'] <= 0.6) &
              (df_train['duration_hours'] >= 5) & (df_train['duration_hours'] <= 15)) &
            ~((df_train['r_squared'] > 0.7) & (df_train['duration_hours'] < 5))
        ]
    
    if len(subset) > 0:
        amp_mean = (subset['impact_real'] / subset['impact_predit'] * 2.5).mean()
        return amp_mean
    else:
        return 2.5

strategies = {
    'Baseline (2.5)': strategy_baseline,
    'Mean Train': strategy_mean,
    'Surprise': strategy_surprise,
    'R²': strategy_r2,
    'Durée': strategy_duration,
    'R² + Durée': strategy_combined
}

print("Stratégies à tester :")
for i, name in enumerate(strategies.keys(), 1):
    print(f"   {i}. {name}")
print()

# ============================================================================
# TESTER STRATÉGIES AVEC LOO (MÉTHODOLOGIE CORRECTE)
# ============================================================================

print("=" * 80)
print("ÉTAPE 3 : TESTER STRATÉGIES (LOO + PIPS)")
print("=" * 80)
print()

results_strategies = {}

for strategy_name, strategy_func in strategies.items():
    errors_pips = []
    
    loo = LeaveOneOut()
    
    for train_idx, test_idx in loo.split(df):
        df_train = df.iloc[train_idx]
        df_test = df.iloc[test_idx]
        
        row_test = df_test.iloc[0]
        
        # Prédire amp selon stratégie
        amp_pred = strategy_func(row_test, df_train)
        
        # MÉTHODOLOGIE CORRECTE : Recalculer impact
        impact_base = row_test['impact_predit']
        impact_pred = impact_base / 2.5 * amp_pred
        impact_real = row_test['impact_real']
        
        # Erreur en PIPS
        error_pips = np.abs(impact_real - impact_pred)
        errors_pips.append(error_pips)
    
    errors_pips = np.array(errors_pips)
    mae = errors_pips.mean()
    
    results_strategies[strategy_name] = {
        'mae': mae,
        'errors': errors_pips
    }
    
    print(f"{strategy_name:25s} : MAE = {mae:.2f} pips")

print()

# ============================================================================
# CLASSEMENT
# ============================================================================

print("=" * 80)
print("CLASSEMENT STRATÉGIES")
print("=" * 80)
print()

sorted_strategies = sorted(results_strategies.items(), key=lambda x: x[1]['mae'])

print("Classement (MAE en pips) :")
for i, (name, result) in enumerate(sorted_strategies, 1):
    mae = result['mae']
    improvement = ((mae_baseline_pips - mae) / mae_baseline_pips) * 100
    
    status = "✅✅" if improvement > 15 else "✅" if improvement > 5 else "⚠️" if improvement > 0 else "❌"
    print(f"   {i}. {status} {name:25s} : MAE={mae:.2f} pips ({improvement:+.1f}%)")

print()

best_name, best_result = sorted_strategies[0]
best_mae = best_result['mae']
best_improvement = ((mae_baseline_pips - best_mae) / mae_baseline_pips) * 100

print(f"🏆 MEILLEURE STRATÉGIE : {best_name}")
print(f"   MAE : {best_mae:.2f} pips")
print(f"   Amélioration : {best_improvement:+.1f}%")
print()

if best_improvement > 15:
    print("✅✅ AMÉLIORATION SIGNIFICATIVE")
elif best_improvement > 10:
    print("✅ AMÉLIORATION BONNE")
elif best_improvement > 5:
    print("⚠️ AMÉLIORATION FAIBLE")
else:
    print("❌ PAS D'AMÉLIORATION")

print()

# ============================================================================
# SAUVEGARDER
# ============================================================================

df_results = df[['event_date', 'r_squared', 'duration_hours', 'max_surprise', 
                 'impact_predit', 'impact_real', 'erreur_baseline_pips']].copy()

for strategy_name, result in results_strategies.items():
    col_name = f"error_{strategy_name.replace(' ', '_').replace('(', '').replace(')', '').lower()}_pips"
    df_results[col_name] = result['errors']

df_results.to_csv(data_dir / "stepB_prime_CORRECTED_results.csv", index=False)
print(f"✅ Résultats : stepB_prime_CORRECTED_results.csv")
print()

# ============================================================================
# GRAPHIQUES
# ============================================================================

print("=" * 80)
print("GÉNÉRATION GRAPHIQUES")
print("=" * 80)
print()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Calibration Zones : Méthodologie Correcte (PIPS)', fontsize=16)

# Graph 1 : Comparaison MAE
strategy_names = [name for name, _ in sorted_strategies]
strategy_maes = [result['mae'] for _, result in sorted_strategies]

colors = ['green' if mae < mae_baseline_pips else 'orange' for mae in strategy_maes]
axes[0, 0].barh(strategy_names, strategy_maes, color=colors, alpha=0.7)
axes[0, 0].axvline(mae_baseline_pips, color='r', linestyle='--', alpha=0.5, label='Baseline')
axes[0, 0].set_xlabel('MAE (pips)')
axes[0, 0].set_title('Comparaison Stratégies')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3, axis='x')

# Graph 2 : Baseline vs Best
axes[0, 1].scatter(df['erreur_baseline_pips'], best_result['errors'], alpha=0.6, s=100)
axes[0, 1].plot([0, df['erreur_baseline_pips'].max()], 
                [0, df['erreur_baseline_pips'].max()], 
                'r--', alpha=0.5, label='Pas de gain')
axes[0, 1].set_xlabel('Erreur Baseline (pips)')
axes[0, 1].set_ylabel(f'Erreur {best_name} (pips)')
axes[0, 1].set_title(f'Amélioration : {best_improvement:+.1f}%')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Graph 3 : Distribution erreurs
axes[1, 0].hist([df['erreur_baseline_pips'], best_result['errors']], 
                bins=15, alpha=0.7, label=['Baseline', best_name])
axes[1, 0].axvline(mae_baseline_pips, color='blue', linestyle='--', alpha=0.7)
axes[1, 0].axvline(best_mae, color='orange', linestyle='--', alpha=0.7)
axes[1, 0].set_xlabel('Erreur (pips)')
axes[1, 0].set_ylabel('Fréquence')
axes[1, 0].set_title('Distribution Erreurs')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Graph 4 : Amélioration vs baseline
improvements = [(mae_baseline_pips - result['mae']) / mae_baseline_pips * 100 
                for _, result in sorted_strategies]
colors_imp = ['green' if imp > 0 else 'red' for imp in improvements]

axes[1, 1].barh(strategy_names, improvements, color=colors_imp, alpha=0.7)
axes[1, 1].axvline(0, color='black', linestyle='-', linewidth=0.5)
axes[1, 1].set_xlabel('Amélioration (%)')
axes[1, 1].set_title('Amélioration vs Baseline')
axes[1, 1].grid(True, alpha=0.3, axis='x')

plt.tight_layout()
graph_path = data_dir / "stepB_prime_CORRECTED_zones.png"
plt.savefig(graph_path, dpi=150)
print(f"✅ Graphiques : {graph_path}")
print()

# ============================================================================
# CONCLUSIONS
# ============================================================================

print("=" * 80)
print("CONCLUSIONS ÉTAPE B' (CORRIGÉ)")
print("=" * 80)
print()

print(f"1. MÉTHODE : LOO + Calcul impact + PIPS (CORRECT)")
print()

print(f"2. RÉSULTATS :")
print(f"   Baseline      : {mae_baseline_pips:.2f} pips")
print(f"   Meilleur      : {best_mae:.2f} pips ({best_name})")
print(f"   Amélioration  : {best_improvement:+.1f}%")
print()

print(f"3. COMPARAISON COMPLÈTE :")
print(f"   Étape A (Formule quadratique)  : +2.7%")
print(f"   Étape B (ML - LR)              : (à voir)")
print(f"   Étape B' (Zones)               : {best_improvement:+.1f}%")
print()

if best_improvement > 10:
    print("✅ RECOMMANDATION : Utiliser stratégie par zones")
    print(f"   Intégrer '{best_name}' dans Planificateur")
elif best_improvement > 5:
    print("⚠️ RECOMMANDATION : Amélioration faible")
    print("   Considérer si simplicité valorisée")
else:
    print("❌ RECOMMANDATION : Rester sur baseline (amp=2.5)")

print()
print("4. PROCHAINE ÉTAPE :")
print("   → C : Analyser cas extrême 2024-11-13 (amp=3.42)")

print()
print("=" * 80)
print("✅ ÉTAPE B' TERMINÉE (CORRIGÉ)")
print("=" * 80)
