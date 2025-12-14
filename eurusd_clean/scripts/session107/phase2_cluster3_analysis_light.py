#!/usr/bin/env python3
"""
SESSION 107 - PHASE 2 CLUSTER #3 : ANALYSE CORRÉLATIONS (VERSION LIGHT)
=========================================================================
Version sans matplotlib - Résultats texte uniquement
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

print("="*80)
print("SESSION 107 - PHASE 2 CLUSTER #3 : ANALYSE CORRÉLATIONS")
print("="*80)
print()

# Charger résultats Phase 1
results_file = Path(__file__).parent.parent / "session106" / "phase1_cluster3_results_FINAL_CORRECTED.csv"

if not results_file.exists():
    print(f"❌ Fichier résultats introuvable : {results_file}")
    sys.exit(1)

df = pd.read_csv(results_file)

print(f"✅ {len(df)} dates Cluster #3 chargées")
print()

# Afficher données
print("📊 DONNÉES CLUSTER #3")
print("="*80)
print(df[['date', 'impact_real', 'max_surprise', 'amp_optimal', 'error_baseline']].to_string(index=False))
print()

# =============================================================================
# STATISTIQUES DESCRIPTIVES
# =============================================================================

print("="*80)
print("1. STATISTIQUES DESCRIPTIVES")
print("="*80)
print()

print("📊 amp_optimal :")
print(f"   Moyenne  : {df['amp_optimal'].mean():.3f}")
print(f"   Médiane  : {df['amp_optimal'].median():.3f}")
print(f"   Écart-type : {df['amp_optimal'].std():.3f}")
print(f"   Min      : {df['amp_optimal'].min():.3f}")
print(f"   Max      : {df['amp_optimal'].max():.3f}")
print(f"   Range    : {df['amp_optimal'].max() - df['amp_optimal'].min():.3f}")
print()

print("📊 Baseline amp=2.5 :")
print(f"   MAE      : {df['error_baseline'].mean():.2f} pips")
print(f"   RMSE     : {np.sqrt((df['error_baseline']**2).mean()):.2f} pips")
print(f"   Médiane  : {df['error_baseline'].median():.2f} pips")
print()

# Classifier les cas
df['quality'] = df['error_baseline'].apply(lambda x: 
    '✅ Excellent (<5p)' if x < 5 else 
    '✅ Bon (<10p)' if x < 10 else 
    '⚠️ Moyen (<20p)' if x < 20 else 
    '❌ Faible (≥20p)'
)

print("📊 Qualité prédiction baseline :")
for quality, count in df['quality'].value_counts().sort_index().items():
    pct = count / len(df) * 100
    print(f"   {quality} : {count}/{len(df)} ({pct:.1f}%)")
print()

# =============================================================================
# ANALYSE CORRÉLATIONS
# =============================================================================

print("="*80)
print("2. CORRÉLATIONS amp_optimal vs VARIABLES")
print("="*80)
print()

# Variables à tester
variables = {
    'max_surprise': 'Surprise max (%)',
    'impact_real': 'Impact réel (pips)',
    'error_baseline': 'Erreur baseline (pips)',
    'adjusted_score': 'Score ajusté'
}

correlations = {}

for var, label in variables.items():
    if var in df.columns:
        corr = df['amp_optimal'].corr(df[var])
        correlations[var] = corr
        
        # Calcul manuel Pearson p-value (approximatif)
        n = len(df)
        t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2)
        # p-value approximatif (bilatéral)
        from scipy.stats import t as t_dist
        p_value = 2 * (1 - t_dist.cdf(abs(t_stat), n - 2))
        
        print(f"📊 {label} :")
        print(f"   Corrélation  : {corr:+.3f}")
        print(f"   P-value      : {p_value:.4f}")
        print(f"   Significatif : {'✅ Oui (p<0.05)' if p_value < 0.05 else '❌ Non (p≥0.05)'}")
        print()

# =============================================================================
# RÉGRESSION LINÉAIRE SIMPLE (meilleure variable)
# =============================================================================

print("="*80)
print("3. RÉGRESSION LINÉAIRE SIMPLE")
print("="*80)
print()

strongest_var = max(correlations.items(), key=lambda x: abs(x[1]))[0]
print(f"Variable la plus corrélée : {variables[strongest_var]} (r={correlations[strongest_var]:+.3f})")
print()

# Régression manuelle y = ax + b
X = df[strongest_var].values
y = df['amp_optimal'].values
n = len(X)

# Calcul coefficients
X_mean = X.mean()
y_mean = y.mean()

numerator = np.sum((X - X_mean) * (y - y_mean))
denominator = np.sum((X - X_mean)**2)

a = numerator / denominator  # pente
b = y_mean - a * X_mean      # intercept

# R²
y_pred = a * X + b
ss_res = np.sum((y - y_pred)**2)
ss_tot = np.sum((y - y_mean)**2)
r2 = 1 - (ss_res / ss_tot)

# MAE
mae = np.mean(np.abs(y - y_pred))

print(f"Formule : amp_optimal = {a:.4f} × {strongest_var} + {b:.4f}")
print(f"R²      : {r2:.3f}")
print(f"MAE     : {mae:.3f}")
print()

# =============================================================================
# RÉGRESSION MULTIPLE
# =============================================================================

print("="*80)
print("4. RÉGRESSION LINÉAIRE MULTIPLE")
print("="*80)
print()

# Préparer features (sans sklearn)
feature_cols = ['max_surprise', 'impact_real', 'adjusted_score']
X_multi = df[feature_cols].values
y_multi = df['amp_optimal'].values

# Ajouter colonne de 1 pour intercept
X_with_intercept = np.column_stack([np.ones(len(X_multi)), X_multi])

# Résolution (X'X)^-1 X'y
try:
    XtX = X_with_intercept.T @ X_with_intercept
    Xty = X_with_intercept.T @ y_multi
    coefficients = np.linalg.solve(XtX, Xty)
    
    intercept = coefficients[0]
    betas = coefficients[1:]
    
    # Prédictions
    y_pred_multi = X_with_intercept @ coefficients
    
    # R² et MAE
    ss_res_multi = np.sum((y_multi - y_pred_multi)**2)
    ss_tot_multi = np.sum((y_multi - y_multi.mean())**2)
    r2_multi = 1 - (ss_res_multi / ss_tot_multi)
    mae_multi = np.mean(np.abs(y_multi - y_pred_multi))
    
    print("📊 Modèle : amp_optimal = β0 + β1×surprise + β2×impact + β3×score")
    print()
    print(f"Coefficients :")
    print(f"   Intercept (β0)      : {intercept:.4f}")
    for i, col in enumerate(feature_cols):
        print(f"   {col:20s} (β{i+1}) : {betas[i]:+.4f}")
    print()
    print(f"Métriques :")
    print(f"   R²              : {r2_multi:.3f}")
    print(f"   MAE             : {mae_multi:.3f}")
    print()
    
    # Prédictions par date
    df['amp_predicted'] = y_pred_multi
    df['amp_error'] = np.abs(df['amp_predicted'] - df['amp_optimal'])
    
    print("📊 Prédictions par date :")
    print("-"*80)
    for _, row in df.iterrows():
        print(f"   {row['date']} : amp_optimal={row['amp_optimal']:.3f} | "
              f"predicted={row['amp_predicted']:.3f} | error={row['amp_error']:.3f}")
    print()
    
except np.linalg.LinAlgError:
    print("⚠️ Impossible de calculer régression multiple (matrice singulière)")
    r2_multi = 0
    mae_multi = 999
    print()

# =============================================================================
# ANALYSE OUTLIERS
# =============================================================================

print("="*80)
print("5. ANALYSE OUTLIERS")
print("="*80)
print()

# Identifier outliers (amp > 3.5 ou amp < 1.8)
df['is_outlier'] = (df['amp_optimal'] > 3.5) | (df['amp_optimal'] < 1.8)

outliers = df[df['is_outlier']]

if len(outliers) > 0:
    print(f"⚠️ {len(outliers)} outliers détectés (amp<1.8 ou amp>3.5) :")
    print()
    for _, row in outliers.iterrows():
        print(f"   📅 {row['date']} :")
        print(f"      amp_optimal    : {row['amp_optimal']:.3f}")
        print(f"      surprise       : {row['max_surprise']:.2f}%")
        print(f"      impact_real    : {row['impact_real']:.1f} pips")
        print(f"      error_baseline : {row['error_baseline']:.1f} pips")
        print()
else:
    print("✅ Aucun outlier extrême détecté")
    print()

# =============================================================================
# DÉCISION : FIXE vs DYNAMIQUE
# =============================================================================

print("="*80)
print("6. DÉCISION : BASELINE FIXE 2.5 vs DYNAMIQUE")
print("="*80)
print()

baseline_mae = df['error_baseline'].mean()

print("📊 Comparaison performance :")
print(f"   MAE Baseline (amp=2.5 fixe) : {baseline_mae:.2f} pips")
print()

print("💡 OBSERVATIONS :")
print()

# Observation 1 : Corrélations
strongest_corr = max(correlations.items(), key=lambda x: abs(x[1]))
print(f"1. Variable la plus corrélée : {variables[strongest_corr[0]]} (r={strongest_corr[1]:+.3f})")

if abs(strongest_corr[1]) < 0.5:
    print("   ⚠️ Corrélation FAIBLE (<0.5) → Modèle dynamique peu prédictif")
else:
    print("   ✅ Corrélation MODÉRÉE/FORTE (>0.5) → Modèle dynamique potentiellement utile")
print()

# Observation 2 : R² régression
print(f"2. R² régression multiple : {r2_multi:.3f}")

if r2_multi < 0.3:
    print("   ⚠️ R² FAIBLE (<0.3) → Modèle explique <30% variance")
elif r2_multi < 0.6:
    print("   ⚠️ R² MOYEN (0.3-0.6) → Modèle explique partiellement variance")
else:
    print("   ✅ R² BON (>0.6) → Modèle explique bien variance")
print()

# Observation 3 : Échantillon
print(f"3. Taille échantillon : {len(df)} dates")
if len(df) < 10:
    print("   ⚠️ PETIT échantillon (<10) → Risque overfitting élevé")
else:
    print("   ✅ Échantillon acceptable (≥10)")
print()

# Observation 4 : Baseline performance
good_cases = len(df[df['error_baseline'] < 20])
pct_good = good_cases / len(df) * 100

print(f"4. Performance baseline 2.5 : {good_cases}/{len(df)} cas <20 pips erreur ({pct_good:.0f}%)")
if pct_good >= 70:
    print("   ✅ BONNE performance (≥70% cas satisfaisants)")
elif pct_good >= 50:
    print("   ⚠️ MOYENNE performance (50-70% cas satisfaisants)")
else:
    print("   ❌ FAIBLE performance (<50% cas satisfaisants)")
print()

# =============================================================================
# RECOMMANDATION
# =============================================================================

print("="*80)
print("7. RECOMMANDATION FINALE")
print("="*80)
print()

# Critères de décision
use_dynamic = False
reasons = []

# Critère 1 : R² régression
if r2_multi >= 0.5:
    use_dynamic = True
    reasons.append(f"✅ R² régression élevé ({r2_multi:.3f})")
else:
    reasons.append(f"❌ R² régression faible ({r2_multi:.3f})")

# Critère 2 : Corrélations
if abs(strongest_corr[1]) >= 0.5:
    use_dynamic = True
    reasons.append(f"✅ Corrélation significative ({strongest_corr[1]:+.3f})")
else:
    reasons.append(f"❌ Corrélations faibles (max {strongest_corr[1]:+.3f})")

# Critère 3 : Baseline performance
if pct_good >= 70:
    reasons.append(f"✅ Baseline 2.5 déjà performante ({pct_good:.0f}% bons cas)")
else:
    reasons.append(f"⚠️ Baseline 2.5 améliorable ({pct_good:.0f}% bons cas)")

# Critère 4 : Échantillon
if len(df) >= 10:
    reasons.append(f"✅ Échantillon suffisant ({len(df)} dates)")
else:
    reasons.append(f"⚠️ Échantillon petit ({len(df)} dates)")

print("Critères de décision :")
for reason in reasons:
    print(f"   {reason}")
print()

if use_dynamic and r2_multi >= 0.6 and len(df) >= 10:
    print("🎯 RECOMMANDATION : AMPLIFICATION DYNAMIQUE")
    print()
    print("   Le modèle de régression explique suffisamment la variance")
    print("   et l'échantillon est assez grand pour justifier un modèle dynamique.")
    print()
    if 'betas' in locals():
        print("   Formule proposée :")
        print(f"   amp = {intercept:.4f} ", end="")
        for i, col in enumerate(feature_cols):
            print(f"{betas[i]:+.4f}×{col} ", end="")
        print()
    print()
    print("   ⚠️ MAIS : Tester sur dates supplémentaires avant production !")
    
elif baseline_mae < 20:
    print("🎯 RECOMMANDATION : BASELINE FIXE 2.5")
    print()
    print("   Raisons :")
    print(f"   - MAE baseline acceptable ({baseline_mae:.2f} pips)")
    print(f"   - Simplicité vs gain marginal modèle dynamique")
    if r2_multi < 0.5:
        print(f"   - R² régression insuffisant ({r2_multi:.3f})")
    if len(df) < 10:
        print(f"   - Échantillon trop petit ({len(df)} dates)")
    print()
    print("   ✅ AVANTAGE : Production-ready immédiatement")
    print("   ✅ AVANTAGE : Pas de risque overfitting")
    
else:
    print("🎯 RECOMMANDATION : COLLECTER PLUS DE DONNÉES")
    print()
    print("   - Baseline 2.5 a MAE élevée (>20 pips)")
    print("   - Mais régression insuffisante pour modèle fiable")
    print("   - Solution : Tester plus de dates Cluster #3")
    print(f"   - Objectif : Atteindre 15-20 dates pour régression robuste")

print()
print("="*80)
print("ANALYSE COMPLÈTE TERMINÉE ✅")
print("="*80)

# Sauvegarder résultats enrichis
if 'amp_predicted' in df.columns:
    output_file = Path(__file__).parent / "cluster3_analysis_results.csv"
    df.to_csv(output_file, index=False)
    print()
    print(f"✅ Résultats enrichis sauvegardés : {output_file.name}")
