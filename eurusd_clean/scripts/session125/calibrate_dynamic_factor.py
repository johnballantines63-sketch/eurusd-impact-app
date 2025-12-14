#!/usr/bin/env python3
"""
SESSION 125 - CALIBRATION FACTEUR DYNAMIQUE (CORRIGÉ)
======================================================
Calibre formule amp = slope × R² + intercept sur 17 dates
"""
import pandas as pd
import numpy as np
from scipy.stats import linregress
from pathlib import Path
import matplotlib.pyplot as plt
import json

print("="*80)
print("SESSION 125 - CALIBRATION FACTEUR DYNAMIQUE")
print("="*80)
print()

# Charger CSV Session 107
csv_path = Path(__file__).parents[2] / "VALIDATED_BACKUP_20251110_161850" / "02_DETECTION_INVERSION" / "s107_phase3_combined_calibration.csv"
df = pd.read_csv(csv_path)

print(f"✅ {len(df)} dates chargées du CSV Session 107")
print()

# Extraire colonnes pertinentes
X = df['r2_inversion'].values
y = df['amp_optimal'].values

# Régression linéaire
slope, intercept, r_value, p_value, std_err = linregress(X, y)
r2_regression = r_value ** 2

print("="*80)
print("FORMULE CALIBRÉE")
print("="*80)
print()
print(f"   amp = {slope:.4f} × R² + {intercept:.4f}")
print()
print(f"   R² régression  : {r2_regression:.4f}")
print(f"   P-value        : {p_value:.6f}")
print(f"   Erreur std     : {std_err:.4f}")
print()

# Statistiques R²_inversion
print("="*80)
print("STATISTIQUES R²_INVERSION (17 DATES)")
print("="*80)
print()
print(f"   Moyenne : {X.mean():.4f}")
print(f"   Médiane : {np.median(X):.4f}")
print(f"   Min     : {X.min():.4f}")
print(f"   Max     : {X.max():.4f}")
print(f"   Std     : {X.std():.4f}")
print()

# Statistiques amp_optimal
print("="*80)
print("STATISTIQUES AMP_OPTIMAL (17 DATES)")
print("="*80)
print()
print(f"   Moyenne : {y.mean():.4f}")
print(f"   Médiane : {np.median(y):.4f}")
print(f"   Min     : {y.min():.4f}")
print(f"   Max     : {y.max():.4f}")
print(f"   Std     : {y.std():.4f}")
print()

# Prédictions avec formule
df['amp_predicted'] = slope * df['r2_inversion'] + intercept
df['amp_error'] = abs(df['amp_predicted'] - df['amp_optimal'])

# MAE et RMSE
mae_amp = df['amp_error'].mean()
rmse_amp = np.sqrt((df['amp_error']**2).mean())

print("="*80)
print("VALIDATION FORMULE (17 DATES)")
print("="*80)
print()
print(f"   MAE  : {mae_amp:.4f} (amp)")
print(f"   RMSE : {rmse_amp:.4f} (amp)")
print()

# Cas 11 septembre
case_11sept = df[df['date'] == '2025-09-11'].iloc[0]
r2_11sept = case_11sept['r2_inversion']
amp_11sept_optimal = case_11sept['amp_optimal']
amp_11sept_predicted = slope * r2_11sept + intercept
error_11sept = abs(amp_11sept_predicted - amp_11sept_optimal)

print("="*80)
print("CAS RÉFÉRENCE : 11 SEPTEMBRE 2025")
print("="*80)
print()
print(f"   R² inversion       : {r2_11sept:.4f}")
print(f"   Amp optimal        : {amp_11sept_optimal:.4f}")
print(f"   Amp prédit         : {amp_11sept_predicted:.4f}")
print(f"   Erreur amp         : {error_11sept:.4f}")
print()

# Impact avec facteur dynamique
impact_real_11sept = case_11sept['impact_real']
impact_pred_baseline = case_11sept['impact_pred_baseline']
impact_pred_optimal = case_11sept['impact_pred_optimal']
impact_pred_dynamic = (impact_pred_baseline / 2.5) * amp_11sept_predicted

print("="*80)
print("IMPACT 11 SEPTEMBRE (AVEC FACTEUR DYNAMIQUE)")
print("="*80)
print()
print(f"   Impact réel MT5       : {impact_real_11sept:.2f} pips")
print(f"   Impact baseline (2.5) : {impact_pred_baseline:.2f} pips")
print(f"   Impact optimal        : {impact_pred_optimal:.2f} pips")
print(f"   Impact dynamique      : {impact_pred_dynamic:.2f} pips")
print()
print(f"   MAE baseline  : {abs(impact_pred_baseline - impact_real_11sept):.2f} pips")
print(f"   MAE optimal   : {abs(impact_pred_optimal - impact_real_11sept):.2f} pips")
print(f"   MAE dynamique : {abs(impact_pred_dynamic - impact_real_11sept):.2f} pips")
print()

# Objectif Session 125
objectif = 10.0
mae_dynamic = abs(impact_pred_dynamic - impact_real_11sept)
objectif_atteint = bool(mae_dynamic < objectif)

if objectif_atteint:
    print(f"   ✅✅✅ OBJECTIF ATTEINT : MAE {mae_dynamic:.2f} < {objectif} pips")
else:
    print(f"   ⚠️ OBJECTIF NON ATTEINT : MAE {mae_dynamic:.2f} >= {objectif} pips")
print()

# Amélioration
mae_baseline = abs(impact_pred_baseline - impact_real_11sept)
improvement_pct = ((mae_baseline - mae_dynamic) / mae_baseline * 100)
print(f"   📈 Amélioration vs baseline : {improvement_pct:.1f}%")
print()

# Graphique
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Graphique 1 : R² vs amp_optimal
ax1 = axes[0]
ax1.scatter(X, y, alpha=0.6, s=100, label='Données réelles')
x_line = np.linspace(X.min(), X.max(), 100)
y_line = slope * x_line + intercept
ax1.plot(x_line, y_line, 'r-', linewidth=2, label=f'y = {slope:.3f}x + {intercept:.3f}')
ax1.scatter([r2_11sept], [amp_11sept_optimal], color='green', s=200, marker='*', 
            label='11 septembre', zorder=5, edgecolor='black', linewidth=1.5)
ax1.set_xlabel('R² Inversion', fontsize=12)
ax1.set_ylabel('Facteur Amplification Optimal', fontsize=12)
ax1.set_title('Calibration Facteur Dynamique\n(17 dates, Session 102-107)', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.text(0.05, 0.95, f'R² = {r2_regression:.4f}\np = {p_value:.4f}', 
         transform=ax1.transAxes, fontsize=11, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Graphique 2 : Erreurs
ax2 = axes[1]
dates = df['date'].values
errors = df['amp_error'].values
colors = ['green' if d == '2025-09-11' else 'blue' for d in dates]
sizes = [200 if d == '2025-09-11' else 80 for d in dates]
ax2.scatter(range(len(dates)), errors, c=colors, s=sizes, alpha=0.6)
ax2.axhline(y=mae_amp, color='r', linestyle='--', linewidth=2, label=f'MAE = {mae_amp:.3f}')
ax2.set_xlabel('Index Date', fontsize=12)
ax2.set_ylabel('Erreur Amplification', fontsize=12)
ax2.set_title('Erreurs Prédiction Facteur\n(17 dates)', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
output_path = Path(__file__).parent / "calibration_facteur_dynamique.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"📊 Graphique sauvegardé : {output_path.name}")
print()

# Sauvegarder résultats (CORRECTION: bool → int)
results = {
    'formule': {
        'slope': float(slope),
        'intercept': float(intercept),
        'r2_regression': float(r2_regression),
        'p_value': float(p_value),
        'std_err': float(std_err)
    },
    'validation_17dates': {
        'mae_amp': float(mae_amp),
        'rmse_amp': float(rmse_amp)
    },
    'cas_11septembre': {
        'r2_inversion': float(r2_11sept),
        'amp_optimal': float(amp_11sept_optimal),
        'amp_predicted': float(amp_11sept_predicted),
        'error_amp': float(error_11sept),
        'impact_real': float(impact_real_11sept),
        'impact_baseline': float(impact_pred_baseline),
        'impact_optimal': float(impact_pred_optimal),
        'impact_dynamic': float(impact_pred_dynamic),
        'mae_baseline': float(mae_baseline),
        'mae_optimal': float(abs(impact_pred_optimal - impact_real_11sept)),
        'mae_dynamic': float(mae_dynamic),
        'objectif_atteint': int(objectif_atteint),  # CORRECTION: bool → int
        'improvement_pct': float(improvement_pct)
    }
}

results_path = Path(__file__).parent / "calibration_results.json"
with open(results_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"💾 Résultats sauvegardés : {results_path.name}")
print()

print("="*80)
print("CALIBRATION TERMINÉE ✅")
print("="*80)
print()
print(f"📐 Formule : amp = {slope:.4f} × R² + {intercept:.4f}")
print(f"🎯 MAE 11 sept : {mae_dynamic:.2f} pips")
print(f"✅ Objectif {'ATTEINT' if objectif_atteint else 'NON ATTEINT'}")
print(f"📈 Amélioration : {improvement_pct:.1f}%")
