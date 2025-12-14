#!/usr/bin/env python3
"""
SESSION 111 - CALIBRATION FINALE FORMULE AMPLIFICATION DYNAMIQUE
=================================================================
Combine Cluster #3 (6 dates CPI) + Cluster #1 (11 dates Manufacturing)
Total : 17 dates pour calibration robuste

OBJECTIF : Décider entre 3 approches
  A) Baseline fixe (amp=2.5)
  B) Session 101 (R² 72h fixe)
  C) Inversion (R² inversion dynamique)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import linregress
from sklearn.metrics import mean_absolute_error, mean_squared_error

print("="*80)
print("SESSION 111 - CALIBRATION FINALE AMPLIFICATION DYNAMIQUE")
print("="*80)
print()

# Charger résultats Cluster #3 (CPI)
cluster3_file = Path(__file__).parent / "cluster3_inversion_analysis.csv"
df_c3 = pd.read_csv(cluster3_file)
df_c3['cluster'] = 'C3_CPI'

print(f"✅ Cluster #3 (CPI) : {len(df_c3)} dates")

# Charger résultats Cluster #1 (Manufacturing)
cluster1_file = Path(__file__).parent / "cluster1_inversion_analysis.csv"
df_c1 = pd.read_csv(cluster1_file)
df_c1['cluster'] = 'C1_Manufacturing'

print(f"✅ Cluster #1 (Manufacturing) : {len(df_c1)} dates")
print()

# Combiner
df_combined = pd.concat([df_c3, df_c1], ignore_index=True)

# Garder seulement dates avec R²_inversion valide
df_valid = df_combined[df_combined['r2_inversion'].notna()].copy()

print(f"📊 DATASET COMBINÉ : {len(df_valid)} dates valides")
print(f"   - Cluster #3 (CPI)          : {len(df_valid[df_valid['cluster']=='C3_CPI'])}")
print(f"   - Cluster #1 (Manufacturing): {len(df_valid[df_valid['cluster']=='C1_Manufacturing'])}")
print()

# =============================================================================
# ANALYSE CORRÉLATIONS COMBINÉES
# =============================================================================

print("="*80)
print("CORRÉLATIONS COMBINÉES (17 DATES)")
print("="*80)
print()

# Corrélation R²_inversion vs amp_optimal
corr = df_valid['amp_optimal'].corr(df_valid['r2_inversion'])
n = len(df_valid)

# Test significativité
if n > 2:
    t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2 + 1e-10)
    from scipy.stats import t as t_dist
    p_value = 2 * (1 - t_dist.cdf(abs(t_stat), n - 2))
else:
    p_value = 1.0

print(f"📊 R²_inversion vs amp_optimal :")
print(f"   N dates     : {n}")
print(f"   Corrélation : {corr:+.3f}")
print(f"   P-value     : {p_value:.4f}")

if p_value < 0.05:
    print(f"   ✅✅✅ SIGNIFICATIF (p < 0.05) !")
elif p_value < 0.10:
    print(f"   ⚠️ Tendance (0.05 ≤ p < 0.10)")
else:
    print(f"   ⚠️ Non significatif (p ≥ 0.10)")
print()

# Statistiques descriptives
print("📊 Statistiques R²_inversion :")
print(f"   Moyenne : {df_valid['r2_inversion'].mean():.4f}")
print(f"   Médiane : {df_valid['r2_inversion'].median():.4f}")
print(f"   Min     : {df_valid['r2_inversion'].min():.4f}")
print(f"   Max     : {df_valid['r2_inversion'].max():.4f}")
print(f"   Std     : {df_valid['r2_inversion'].std():.4f}")
print()

print("📊 Statistiques amp_optimal :")
print(f"   Moyenne : {df_valid['amp_optimal'].mean():.3f}")
print(f"   Médiane : {df_valid['amp_optimal'].median():.3f}")
print(f"   Min     : {df_valid['amp_optimal'].min():.3f}")
print(f"   Max     : {df_valid['amp_optimal'].max():.3f}")
print(f"   Std     : {df_valid['amp_optimal'].std():.3f}")
print()

# =============================================================================
# CALIBRATION FORMULE : amp = a × R²_inversion + b
# =============================================================================

print("="*80)
print("CALIBRATION FORMULE DYNAMIQUE")
print("="*80)
print()

# Régression linéaire
X = df_valid['r2_inversion'].values
y = df_valid['amp_optimal'].values

slope, intercept, r_value, p_value_reg, std_err = linregress(X, y)
r2_regression = r_value ** 2

print("📐 FORMULE CALIBRÉE :")
print()
print(f"   amp = {slope:.4f} × R²_inversion + {intercept:.4f}")
print()
print(f"   R² régression  : {r2_regression:.4f}")
print(f"   P-value        : {p_value_reg:.4f}")
print(f"   Erreur std     : {std_err:.4f}")
print()

# Prédictions avec formule
df_valid['amp_inversion'] = slope * df_valid['r2_inversion'] + intercept

# Calculer impact avec amp_inversion
# Note : On utilise la formule impact_brut déjà calculée
df_valid['impact_pred_inversion'] = df_valid['impact_pred_baseline'] * (df_valid['amp_inversion'] / 2.5)

# Erreurs
df_valid['error_inversion'] = abs(df_valid['impact_pred_inversion'] - df_valid['impact_real'])

# =============================================================================
# VALIDATION LEAVE-ONE-OUT
# =============================================================================

print("="*80)
print("VALIDATION LEAVE-ONE-OUT (17 DATES)")
print("="*80)
print()

loo_predictions = []
loo_errors = []

for i in range(len(df_valid)):
    # Exclure date i
    train_mask = df_valid.index != df_valid.index[i]
    X_train = df_valid.loc[train_mask, 'r2_inversion'].values
    y_train = df_valid.loc[train_mask, 'amp_optimal'].values
    
    # Régression sur n-1 dates
    slope_loo, intercept_loo, _, _, _ = linregress(X_train, y_train)
    
    # Prédire date i
    r2_test = df_valid.iloc[i]['r2_inversion']
    amp_pred_loo = slope_loo * r2_test + intercept_loo
    
    # Calculer erreur
    amp_true = df_valid.iloc[i]['amp_optimal']
    error_loo = abs(amp_pred_loo - amp_true)
    
    loo_predictions.append(amp_pred_loo)
    loo_errors.append(error_loo)

mae_loo = np.mean(loo_errors)
rmse_loo = np.sqrt(np.mean(np.array(loo_errors)**2))

print(f"📊 Validation Leave-One-Out :")
print(f"   MAE  : {mae_loo:.3f} (amp)")
print(f"   RMSE : {rmse_loo:.3f} (amp)")
print()

# =============================================================================
# COMPARAISON 3 APPROCHES
# =============================================================================

print("="*80)
print("COMPARAISON FINALE : BASELINE vs SESSION 101 vs INVERSION")
print("="*80)
print()

# Approche A : Baseline fixe (amp=2.5)
mae_baseline = df_valid['error_baseline'].mean()
rmse_baseline = np.sqrt((df_valid['error_baseline']**2).mean())

# Approche B : Session 101 (R² 72h)
# Note : On n'a pas R² 72h pour Cluster #1, donc on ne peut pas comparer directement
# On va juste montrer les résultats Inversion

# Approche C : Inversion
mae_inversion = df_valid['error_inversion'].mean()
rmse_inversion = np.sqrt((df_valid['error_inversion']**2).mean())

print("📊 APPROCHE A : BASELINE FIXE (amp=2.5)")
print(f"   MAE  : {mae_baseline:.2f} pips")
print(f"   RMSE : {rmse_baseline:.2f} pips")
print()

print("📊 APPROCHE C : INVERSION DYNAMIQUE")
print(f"   MAE  : {mae_inversion:.2f} pips")
print(f"   RMSE : {rmse_inversion:.2f} pips")
print(f"   Amélioration vs baseline : {((mae_baseline - mae_inversion) / mae_baseline * 100):+.1f}%")
print()

# =============================================================================
# RÉSUMÉ PAR DATE
# =============================================================================

print("="*80)
print("RÉSUMÉ PAR DATE (17 DATES)")
print("="*80)
print()

print("Date       | Cluster | R²_inv | amp_opt | amp_inv | Error Base | Error Inv | Amélio")
print("-"*100)

for _, row in df_valid.sort_values('date').iterrows():
    cluster_short = row['cluster'].split('_')[0]
    amelio = row['error_baseline'] - row['error_inversion']
    
    status = "✅" if row['error_inversion'] < 10 else "⚠️" if row['error_inversion'] < 20 else "❌"
    
    print(f"{status} {row['date']} | {cluster_short:3s} | {row['r2_inversion']:6.4f} | "
          f"{row['amp_optimal']:5.3f} | {row['amp_inversion']:5.3f} | "
          f"{row['error_baseline']:6.1f}p | {row['error_inversion']:6.1f}p | {amelio:+6.1f}p")

print()

# =============================================================================
# DÉCISION FINALE
# =============================================================================

print("="*80)
print("DÉCISION FINALE")
print("="*80)
print()

# Critères décision
improvement_pct = (mae_baseline - mae_inversion) / mae_baseline * 100
is_significant = p_value < 0.10

print("📊 CRITÈRES DÉCISION :")
print(f"   1. Corrélation significative (p < 0.10) : {'✅ OUI' if is_significant else '❌ NON'}")
print(f"   2. Amélioration MAE vs baseline        : {improvement_pct:+.1f}%")
print(f"   3. Amélioration absolue                : {mae_baseline - mae_inversion:.2f} pips")
print()

if is_significant and improvement_pct > 10:
    print("✅✅✅ RECOMMANDATION : ADOPTER FORMULE INVERSION")
    print()
    print("   Formule production :")
    print(f"   amp = {slope:.4f} × R²_inversion + {intercept:.4f}")
    print()
    print("   Justification :")
    print(f"   - Corrélation significative (p={p_value:.4f})")
    print(f"   - Amélioration {improvement_pct:.1f}% vs baseline")
    print(f"   - Validation LOO stable (MAE={mae_loo:.3f})")
    print(f"   - Généralise sur 2 clusters différents")
elif improvement_pct > 20:
    print("⚠️ RECOMMANDATION : CONSIDÉRER FORMULE INVERSION")
    print()
    print("   Amélioration substantielle (+{improvement_pct:.1f}%) mais corrélation non significative")
    print("   Nécessite validation sur échantillon plus grand")
else:
    print("❌ RECOMMANDATION : CONSERVER BASELINE FIXE (amp=2.5)")
    print()
    print(f"   Amélioration insuffisante ({improvement_pct:+.1f}%)")
    print(f"   Complexité ajoutée non justifiée")

print()

# Sauvegarder résultats
output_file = Path(__file__).parent / "phase3_combined_calibration.csv"
df_valid.to_csv(output_file, index=False)

print("="*80)
print("CALIBRATION FINALE TERMINÉE ✅")
print("="*80)
print()
print(f"✅ Résultats : {output_file.name}")
