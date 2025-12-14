#!/usr/bin/env python3
"""
SESSION 108 - CALIBRATION FINALE : FORMULE INVERSION (17 DATES)
================================================================
Calibration de la formule amp = a × R²_inversion + b
sur 17 dates combinées (6 Cluster #3 + 11 Cluster #1)
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import linregress
from sklearn.metrics import mean_absolute_error, mean_squared_error

print("="*80)
print("SESSION 108 - CALIBRATION FORMULE INVERSION")
print("="*80)
print()
print("🎯 OBJECTIF : Calibrer amp = a × R²_inversion + b sur 17 dates")
print()

# =============================================================================
# CHARGEMENT DONNÉES
# =============================================================================

print("="*80)
print("CHARGEMENT DONNÉES")
print("="*80)
print()

# Cluster #3 (Session 107)
cluster3_file = Path(__file__).parent.parent / "session107" / "cluster3_inversion_analysis.csv"
df_c3 = pd.read_csv(cluster3_file)

# Sélectionner colonnes pertinentes
df_c3 = df_c3[['date', 'amp_optimal', 'r2_inversion', 'impact_real']].copy()
df_c3.rename(columns={'impact_real': 'impact_real_pips'}, inplace=True)
df_c3['cluster'] = 'Cluster #3 (CPI)'

print(f"✅ Cluster #3 : {len(df_c3)} dates (CPI)")

# Cluster #1 (Session 108)
cluster1_file = Path(__file__).parent / "cluster1_inversion_analysis.csv"
df_c1 = pd.read_csv(cluster1_file)

# Sélectionner colonnes pertinentes
df_c1 = df_c1[['date', 'amp_optimal', 'r2_inversion', 'impact_real_pips']].copy()
df_c1['cluster'] = 'Cluster #1 (Manufacturing)'

print(f"✅ Cluster #1 : {len(df_c1)} dates (Manufacturing)")
print()

# Combiner
df_all = pd.concat([df_c3, df_c1], ignore_index=True)

# Filtrer données valides
df_valid = df_all[df_all['r2_inversion'].notna()].copy()

print(f"✅ TOTAL : {len(df_valid)} dates valides pour calibration")
print()

if len(df_valid) < 10:
    print("❌ ERREUR : Pas assez de données (<10)")
    sys.exit(1)

# =============================================================================
# RÉGRESSION LINÉAIRE
# =============================================================================

print("="*80)
print("RÉGRESSION LINÉAIRE : amp = a × R²_inversion + b")
print("="*80)
print()

X = df_valid['r2_inversion'].values
y = df_valid['amp_optimal'].values

# Régression
slope, intercept, r_value, p_value, std_err = linregress(X, y)
r2_regression = r_value ** 2

print("📊 FORMULE CALIBRÉE :")
print()
print(f"   amp = {slope:.4f} × R²_inversion + {intercept:.4f}")
print()
print("📊 STATISTIQUES RÉGRESSION :")
print(f"   R²       : {r2_regression:.4f}")
print(f"   r        : {r_value:+.4f}")
print(f"   p-value  : {p_value:.4f}")
print(f"   std_err  : {std_err:.4f}")
print()

# Prédictions
df_valid['amp_predicted'] = slope * df_valid['r2_inversion'] + intercept

# Métriques
mae = mean_absolute_error(df_valid['amp_optimal'], df_valid['amp_predicted'])
rmse = np.sqrt(mean_squared_error(df_valid['amp_optimal'], df_valid['amp_predicted']))

print(f"📊 ERREUR RÉGRESSION :")
print(f"   MAE  : {mae:.4f}")
print(f"   RMSE : {rmse:.4f}")
print()

# =============================================================================
# VALIDATION LEAVE-ONE-OUT
# =============================================================================

print("="*80)
print("VALIDATION LEAVE-ONE-OUT (17 ITÉRATIONS)")
print("="*80)
print()

loo_errors = []
loo_predictions = []

for i in range(len(df_valid)):
    # Train : Toutes les dates sauf i
    train_mask = df_valid.index != df_valid.index[i]
    X_train = df_valid.loc[train_mask, 'r2_inversion'].values
    y_train = df_valid.loc[train_mask, 'amp_optimal'].values
    
    # Test : Date i
    X_test = df_valid.loc[df_valid.index[i], 'r2_inversion']
    y_test = df_valid.loc[df_valid.index[i], 'amp_optimal']
    
    # Régression sur train
    slope_loo, intercept_loo, _, _, _ = linregress(X_train, y_train)
    
    # Prédiction sur test
    y_pred = slope_loo * X_test + intercept_loo
    error = abs(y_test - y_pred)
    
    loo_errors.append(error)
    loo_predictions.append(y_pred)

df_valid['amp_predicted_loo'] = loo_predictions

mae_loo = np.mean(loo_errors)
rmse_loo = np.sqrt(np.mean([e**2 for e in loo_errors]))

print(f"📊 MÉTRIQUES LEAVE-ONE-OUT :")
print(f"   MAE  : {mae_loo:.4f}")
print(f"   RMSE : {rmse_loo:.4f}")
print()

print(f"📊 COMPARAISON :")
print(f"   Régression complète : MAE {mae:.4f}")
print(f"   Leave-One-Out       : MAE {mae_loo:.4f}")
print(f"   Différence          : {abs(mae_loo - mae):.4f}")
print()

if abs(mae_loo - mae) < 0.1:
    print("✅ VALIDATION : Modèle robuste (faible overfitting)")
else:
    print("⚠️ ATTENTION : Différence MAE significative (possible overfitting)")

print()

# =============================================================================
# COMPARAISON BASELINE vs INVERSION
# =============================================================================

print("="*80)
print("COMPARAISON : BASELINE (amp=2.5) vs INVERSION")
print("="*80)
print()

# Pour chaque date, calculer impact prédit avec baseline et inversion
# Formule Session 51 : impact = |impact_brut| × amp × 0.758

results_comparison = []

for idx, row in df_valid.iterrows():
    date = row['date']
    cluster = row['cluster']
    impact_real = row['impact_real_pips']
    amp_optimal = row['amp_optimal']
    r2_inv = row['r2_inversion']
    
    # Score selon cluster
    if 'CPI' in cluster:
        # Cluster #3 : Score varie, on utilise score moyen ~85
        score = 85.0
        num_events = 11
    else:
        # Cluster #1
        score = 87.1
        num_events = 8
    
    # Impact brut (formule Session 51)
    if num_events >= 2:
        impact_brut = -10.47 + 0.477 * score
    else:
        impact_brut = -7.08 + 0.419 * score
    
    # BASELINE (amp=2.5)
    impact_baseline = abs(impact_brut) * 2.5 * 0.758
    error_baseline = abs(impact_baseline - impact_real)
    
    # INVERSION (formule calibrée)
    amp_inversion = slope * r2_inv + intercept
    impact_inversion = abs(impact_brut) * amp_inversion * 0.758
    error_inversion = abs(impact_inversion - impact_real)
    
    results_comparison.append({
        'date': date,
        'cluster': cluster,
        'impact_real': impact_real,
        'impact_baseline': impact_baseline,
        'impact_inversion': impact_inversion,
        'error_baseline': error_baseline,
        'error_inversion': error_inversion,
        'amp_optimal': amp_optimal,
        'amp_inversion': amp_inversion,
        'r2_inversion': r2_inv
    })

df_comparison = pd.DataFrame(results_comparison)

# Statistiques globales
mae_baseline = df_comparison['error_baseline'].mean()
mae_inversion = df_comparison['error_inversion'].mean()
improvement = (mae_baseline - mae_inversion) / mae_baseline * 100

print(f"📊 MAE GLOBALE (17 dates) :")
print()
print(f"   Baseline (amp=2.5)    : {mae_baseline:.1f} pips")
print(f"   Inversion (calibrée)  : {mae_inversion:.1f} pips")
print(f"   Amélioration          : {improvement:+.1f}%")
print()

if improvement > 0:
    print(f"✅ INVERSION GAGNE : {improvement:.1f}% meilleur que baseline")
elif improvement > -10:
    print(f"≈ ÉQUIVALENT : Différence {abs(improvement):.1f}% (négligeable)")
else:
    print(f"❌ BASELINE GAGNE : {abs(improvement):.1f}% meilleur que Inversion")

print()

# Statistiques par cluster
print("📊 PAR CLUSTER :")
print()

for cluster_name in ['Cluster #3 (CPI)', 'Cluster #1 (Manufacturing)']:
    df_cluster = df_comparison[df_comparison['cluster'] == cluster_name]
    
    if len(df_cluster) == 0:
        continue
    
    mae_base_c = df_cluster['error_baseline'].mean()
    mae_inv_c = df_cluster['error_inversion'].mean()
    imp_c = (mae_base_c - mae_inv_c) / mae_base_c * 100
    
    print(f"   {cluster_name:30s} : ", end="")
    print(f"Baseline {mae_base_c:5.1f}p | Inversion {mae_inv_c:5.1f}p | {imp_c:+5.1f}%")

print()

# =============================================================================
# DÉTAIL PAR DATE
# =============================================================================

print("="*80)
print("DÉTAIL PAR DATE (TOP 5 MEILLEURES / TOP 5 PIRES)")
print("="*80)
print()

df_comparison['gain'] = df_comparison['error_baseline'] - df_comparison['error_inversion']
df_sorted = df_comparison.sort_values('gain', ascending=False)

print("✅ TOP 5 MEILLEURES (Inversion > Baseline) :")
print("-"*80)
print(f"{'Date':10s} | {'Cluster':15s} | {'Baseline':8s} | {'Inversion':9s} | {'Gain':6s}")
print("-"*80)

for i, (_, row) in enumerate(df_sorted.head(5).iterrows(), 1):
    cluster_short = 'CPI' if 'CPI' in row['cluster'] else 'Manuf'
    print(f"{row['date']:10s} | {cluster_short:15s} | "
          f"{row['error_baseline']:7.1f}p | {row['error_inversion']:8.1f}p | "
          f"{row['gain']:+5.1f}p")

print()
print("❌ TOP 5 PIRES (Baseline > Inversion) :")
print("-"*80)
print(f"{'Date':10s} | {'Cluster':15s} | {'Baseline':8s} | {'Inversion':9s} | {'Perte':6s}")
print("-"*80)

for i, (_, row) in enumerate(df_sorted.tail(5).iterrows(), 1):
    cluster_short = 'CPI' if 'CPI' in row['cluster'] else 'Manuf'
    print(f"{row['date']:10s} | {cluster_short:15s} | "
          f"{row['error_baseline']:7.1f}p | {row['error_inversion']:8.1f}p | "
          f"{row['gain']:+5.1f}p")

print()

# =============================================================================
# COMPARAISON SESSION 101 (R² 72h) - OPTIONNEL
# =============================================================================

print("="*80)
print("COMPARAISON AVEC SESSION 101 (R² 72h)")
print("="*80)
print()

# Charger résultats Session 101 pour Cluster #3
session101_file = Path(__file__).parent.parent / "session107" / "cluster3_complete_analysis.csv"

if session101_file.exists():
    df_s101 = pd.read_csv(session101_file)
    
    # MAE Session 101 sur Cluster #3
    mae_s101_c3 = df_s101['error_session101'].mean() if 'error_session101' in df_s101.columns else np.nan
    
    if not np.isnan(mae_s101_c3):
        # MAE Inversion sur Cluster #3 seulement
        mae_inv_c3 = df_comparison[df_comparison['cluster'] == 'Cluster #3 (CPI)']['error_inversion'].mean()
        
        print(f"📊 CLUSTER #3 (CPI) - 6 dates :")
        print()
        print(f"   Session 101 (R² 72h)  : {mae_s101_c3:.2f} pips")
        print(f"   Inversion (R² inv)    : {mae_inv_c3:.2f} pips")
        print(f"   Différence            : {mae_inv_c3 - mae_s101_c3:+.2f} pips")
        print()
        
        if mae_inv_c3 < mae_s101_c3:
            print(f"✅ INVERSION GAGNE sur Cluster #3 ({mae_s101_c3 - mae_inv_c3:.2f} pips)")
        elif abs(mae_inv_c3 - mae_s101_c3) < 1:
            print(f"≈ ÉQUIVALENT sur Cluster #3 (différence {abs(mae_inv_c3 - mae_s101_c3):.2f} pips)")
        else:
            print(f"❌ SESSION 101 GAGNE sur Cluster #3 ({mae_inv_c3 - mae_s101_c3:.2f} pips)")
        print()
    else:
        print("⚠️ Impossible de charger MAE Session 101")
        print()
else:
    print("⚠️ Fichier Session 101 non trouvé (comparaison sautée)")
    print()

# =============================================================================
# SAUVEGARDER RÉSULTATS
# =============================================================================

output_file = Path(__file__).parent / "calibration_inversion_17dates.csv"
df_comparison.to_csv(output_file, index=False)

print("="*80)
print("RÉSULTATS SAUVEGARDÉS")
print("="*80)
print()
print(f"✅ {output_file.name}")
print()

# =============================================================================
# DÉCISION FINALE
# =============================================================================

print("="*80)
print("DÉCISION FINALE")
print("="*80)
print()

print("📊 FORMULE CALIBRÉE (17 dates) :")
print()
print(f"   amp = {slope:.4f} × R²_inversion + {intercept:.4f}")
print()

print("📊 PERFORMANCE :")
print(f"   MAE Baseline      : {mae_baseline:.1f} pips")
print(f"   MAE Inversion     : {mae_inversion:.1f} pips")
print(f"   Amélioration      : {improvement:+.1f}%")
print(f"   Corrélation       : {r_value:+.3f}")
print(f"   P-value           : {p_value:.4f}")
print()

# Critères décision
criteria = []

if improvement > 5:
    criteria.append("✅ Amélioration MAE > 5%")
    decision_mae = True
else:
    criteria.append(f"⚠️ Amélioration MAE = {improvement:.1f}% (<5%)")
    decision_mae = False

if abs(r_value) > 0.3:
    criteria.append(f"✅ Corrélation forte (r={r_value:+.3f})")
    decision_corr = True
else:
    criteria.append(f"⚠️ Corrélation faible (r={r_value:+.3f})")
    decision_corr = False

if p_value < 0.05:
    criteria.append(f"✅ Significatif statistiquement (p={p_value:.4f})")
    decision_pval = True
else:
    criteria.append(f"⚠️ Non significatif (p={p_value:.4f})")
    decision_pval = False

print("📊 CRITÈRES DÉCISION :")
for criterion in criteria:
    print(f"   {criterion}")
print()

# Décision
if decision_mae and decision_corr:
    print("="*80)
    print("✅✅✅ RECOMMANDATION : ADOPTER FORMULE INVERSION")
    print("="*80)
    print()
    print("JUSTIFICATION :")
    print(f"  - Amélioration MAE significative ({improvement:+.1f}%)")
    print(f"  - Corrélation forte (r={r_value:+.3f})")
    print(f"  - Formule simple et interprétable")
    print(f"  - Validée sur 17 dates (2 clusters différents)")
elif mae_inversion < mae_baseline:
    print("="*80)
    print("≈ RECOMMANDATION : FORMULE INVERSION ACCEPTABLE")
    print("="*80)
    print()
    print("JUSTIFICATION :")
    print(f"  - Amélioration MAE modérée ({improvement:+.1f}%)")
    print(f"  - Corrélation correcte (r={r_value:+.3f})")
    print(f"  - Alternative valide à baseline fixe")
else:
    print("="*80)
    print("⚠️ RECOMMANDATION : CONSERVER BASELINE (amp=2.5)")
    print("="*80)
    print()
    print("JUSTIFICATION :")
    print(f"  - Baseline plus performante")
    print(f"  - Simplicité > Complexité")
    print(f"  - Formule Inversion pas assez meilleure")

print()
print("="*80)
print("CALIBRATION TERMINÉE ✅")
print("="*80)
