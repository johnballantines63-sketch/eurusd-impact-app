"""
MÉTHODOLOGIE ANDRÉ - BASELINE CAS DE RÉFÉRENCE
================================================

1. Baseline = amp_optimal du 11.09.2025 = 2.537
2. Écart = amp_optimal_autre_date - 2.537
3. Corrélation écart vs métriques tendance
4. Formule : écart = f(métrique)
5. Prédiction : amp = 2.537 + écart_prédit

Date : 3 novembre 2025
"""

import pandas as pd
import numpy as np
from scipy.stats import linregress
from pathlib import Path

scripts_dir = Path(__file__).parent.parent

# Charger C#3
c3_file = scripts_dir / "session107" / "cluster3_inversion_analysis.csv"
df_c3 = pd.read_csv(c3_file)

# Charger C#1
c1_file = scripts_dir / "session108" / "cluster1_inversion_analysis.csv"
df_c1 = pd.read_csv(c1_file)

# Combiner
df_c3['cluster'] = 3
df_c1['cluster'] = 1
df = pd.concat([df_c3, df_c1], ignore_index=True)

print("="*80)
print("MÉTHODOLOGIE ANDRÉ - BASELINE CAS DE RÉFÉRENCE")
print("="*80)

# ÉTAPE 1 : Baseline = amp_optimal du 11.09.2025
baseline_11sept = df[df['date'] == '2025-09-11']['amp_optimal'].values[0]

print(f"\n📊 ÉTAPE 1 : BASELINE CAS DE RÉFÉRENCE")
print(f"   Date : 11.09.2025")
print(f"   amp_optimal : {baseline_11sept:.4f}")
print(f"   → BASELINE = {baseline_11sept:.4f}")

# ÉTAPE 2 : Calculer écarts
df['ecart_vs_reference'] = df['amp_optimal'] - baseline_11sept

print(f"\n📊 ÉTAPE 2 : ÉCARTS PAR RAPPORT À RÉFÉRENCE")
print(f"\n{'Date':10s} {'Cluster':8s} {'amp_optimal':12s} {'Écart':8s}")
print("-"*50)
for _, row in df.head(10).iterrows():
    print(f"{row['date']:10s} C#{int(row['cluster'])}      {row['amp_optimal']:12.4f} {row['ecart_vs_reference']:+8.4f}")

# ÉTAPE 3 : Tester corrélations écart vs métriques
print(f"\n" + "="*80)
print("ÉTAPE 3 : CORRÉLATIONS ÉCART VS MÉTRIQUES TENDANCE")
print("="*80)

metriques = ['r2_inversion', 'duration_hours', 'amplitude_inversion', 'quality_score']

resultats = []
for metrique in metriques:
    X = df[metrique].values
    y = df['ecart_vs_reference'].values
    
    # Supprimer NaN
    mask = ~(np.isnan(X) | np.isnan(y))
    X_clean = X[mask]
    y_clean = y[mask]
    
    if len(X_clean) < 3:
        continue
    
    slope, intercept, r_value, p_value, std_err = linregress(X_clean, y_clean)
    
    resultats.append({
        'metrique': metrique,
        'r': r_value,
        'r2': r_value**2,
        'p': p_value,
        'slope': slope,
        'intercept': intercept,
        'n': len(X_clean)
    })
    
df_corr = pd.DataFrame(resultats).sort_values('r2', ascending=False)

print(f"\n{'Métrique':20s} {'n':3s} {'r':7s} {'R²':7s} {'p-value':9s} {'Signif':6s}")
print("-"*70)
for _, row in df_corr.iterrows():
    signif = "✅" if row['p'] < 0.05 else "⚠️" if row['p'] < 0.10 else "❌"
    print(f"{row['metrique']:20s} {int(row['n']):3d} {row['r']:+7.3f} {row['r2']:7.3f} {row['p']:9.4f} {signif}")

# Meilleure métrique
best = df_corr.iloc[0]

print(f"\n🎯 MEILLEURE MÉTRIQUE : {best['metrique']}")
print(f"   Corrélation : r={best['r']:+.3f}, R²={best['r2']:.3f}")
print(f"   P-value : {best['p']:.4f}")
print(f"   Formule : écart = {best['slope']:.4f} × {best['metrique']} + {best['intercept']:.4f}")

# ÉTAPE 4 : Calculer prédictions avec meilleure métrique
print(f"\n" + "="*80)
print(f"ÉTAPE 4 : PRÉDICTIONS AVEC {best['metrique']}")
print("="*80)

X_best = df[best['metrique']].values
df['ecart_predit'] = best['slope'] * X_best + best['intercept']
df['amp_predit'] = baseline_11sept + df['ecart_predit']

# Erreurs
df['error_baseline'] = np.abs(df['amp_optimal'] - baseline_11sept)
df['error_dynamic'] = np.abs(df['amp_optimal'] - df['amp_predit'])

# Statistiques
mae_baseline = df['error_baseline'].mean()
mae_dynamic = df['error_dynamic'].mean()
improvement = ((mae_baseline - mae_dynamic) / mae_baseline) * 100

print(f"\n📊 RÉSULTATS (n={len(df)}) :")
print(f"   MAE Baseline : {mae_baseline:.4f}")
print(f"   MAE Dynamique : {mae_dynamic:.4f}")
print(f"   Amélioration : {improvement:+.1f}%")

# Par cluster
print(f"\n📊 PAR CLUSTER :")
for cluster_num in [3, 1]:
    df_c = df[df['cluster'] == cluster_num]
    mae_base_c = df_c['error_baseline'].mean()
    mae_dyn_c = df_c['error_dynamic'].mean()
    imp_c = ((mae_base_c - mae_dyn_c) / mae_base_c) * 100
    
    print(f"   Cluster #{cluster_num} (n={len(df_c):2d}) : {imp_c:+.1f}%")

# TEST 11.09.2025
print(f"\n" + "="*80)
print("VALIDATION CAS DE RÉFÉRENCE 11.09.2025")
print("="*80)

row_11sept = df[df['date'] == '2025-09-11'].iloc[0]
print(f"\nDate : {row_11sept['date']}")
print(f"amp_optimal : {row_11sept['amp_optimal']:.4f}")
print(f"Écart réel  : {row_11sept['ecart_vs_reference']:+.4f}")
print(f"Écart prédit: {row_11sept['ecart_predit']:+.4f}")
print(f"amp_prédit  : {row_11sept['amp_predit']:.4f}")
print(f"Erreur      : {row_11sept['error_dynamic']:.4f}")

# Exemples
print(f"\n" + "="*80)
print("EXEMPLES (5 premières dates)")
print("="*80)

print(f"\n{'Date':10s} {'C#':2s} {'amp_opt':8s} {'Écart':8s} {'Prédit':8s} {'Erreur':8s}")
print("-"*60)
for _, row in df.head(5).iterrows():
    print(f"{row['date']:10s} {int(row['cluster']):2d} {row['amp_optimal']:8.4f} {row['ecart_vs_reference']:+8.4f} {row['amp_predit']:8.4f} {row['error_dynamic']:8.4f}")

print(f"\n" + "="*80)
print("🎯 FORMULE FINALE")
print("="*80)

print(f"\nBASELINE = {baseline_11sept:.4f} (cas référence 11.09.2025)")
print(f"\nÉCART = {best['slope']:.4f} × {best['metrique']} + {best['intercept']:.4f}")
print(f"\nAMP_FINAL = BASELINE + ÉCART")
print(f"          = {baseline_11sept:.4f} + ({best['slope']:.4f} × {best['metrique']} + {best['intercept']:.4f})")

print(f"\n" + "="*80)
