#!/usr/bin/env python3
"""
SESSION 107 - PHASE 2 CLUSTER #3 : ANALYSE CORRÉLATIONS
=========================================================
Objectif : Comprendre variance amp_optimal (1.538 → 5.000)

Analyses :
1. Graphiques scatter : amp_optimal vs variables
2. Régression linéaire multiple
3. Décision : Baseline 2.5 fixe vs Dynamique
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error

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
    '✅ Excellent' if x < 5 else 
    '✅ Bon' if x < 10 else 
    '⚠️ Moyen' if x < 20 else 
    '❌ Faible'
)

print("📊 Qualité prédiction baseline :")
for quality, count in df['quality'].value_counts().items():
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
        
        # Pearson
        pearson_r, pearson_p = stats.pearsonr(df['amp_optimal'], df[var])
        
        print(f"📊 {label} :")
        print(f"   Corrélation  : {corr:+.3f}")
        print(f"   Pearson r    : {pearson_r:+.3f} (p={pearson_p:.4f})")
        print(f"   Significatif : {'✅ Oui' if pearson_p < 0.05 else '❌ Non (p>0.05)'}")
        print()

# =============================================================================
# GRAPHIQUES SCATTER
# =============================================================================

print("="*80)
print("3. GÉNÉRATION GRAPHIQUES")
print("="*80)
print()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Cluster #3 : amp_optimal vs Variables', fontsize=16, fontweight='bold')

plot_idx = 0
for var, label in variables.items():
    if var not in df.columns:
        continue
    
    ax = axes[plot_idx // 2, plot_idx % 2]
    
    # Scatter
    ax.scatter(df[var], df['amp_optimal'], s=100, alpha=0.6, c='blue')
    
    # Régression linéaire
    X = df[var].values.reshape(-1, 1)
    y = df['amp_optimal'].values
    
    reg = LinearRegression()
    reg.fit(X, y)
    y_pred = reg.predict(X)
    
    ax.plot(df[var], y_pred, 'r--', linewidth=2, label=f'y = {reg.coef_[0]:.3f}x + {reg.intercept_:.3f}')
    
    # Ligne baseline 2.5
    ax.axhline(y=2.5, color='green', linestyle=':', linewidth=2, label='Baseline 2.5')
    
    # Labels
    ax.set_xlabel(label, fontsize=12)
    ax.set_ylabel('amp_optimal', fontsize=12)
    ax.set_title(f'Corrélation : {correlations[var]:+.3f}', fontsize=11)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Annoter points
    for idx, row in df.iterrows():
        ax.annotate(row['date'][5:], (row[var], row['amp_optimal']), 
                   fontsize=8, alpha=0.7, xytext=(5, 5), textcoords='offset points')
    
    plot_idx += 1

plt.tight_layout()
output_plot = Path(__file__).parent / "cluster3_correlations.png"
plt.savefig(output_plot, dpi=150, bbox_inches='tight')
print(f"✅ Graphique sauvegardé : {output_plot.name}")
print()

# =============================================================================
# RÉGRESSION MULTIPLE
# =============================================================================

print("="*80)
print("4. RÉGRESSION LINÉAIRE MULTIPLE")
print("="*80)
print()

# Préparer features
feature_cols = ['max_surprise', 'impact_real', 'adjusted_score']
X_multi = df[feature_cols].values
y_multi = df['amp_optimal'].values

# Régression
reg_multi = LinearRegression()
reg_multi.fit(X_multi, y_multi)
y_pred_multi = reg_multi.predict(X_multi)

# Métriques
r2_multi = r2_score(y_multi, y_pred_multi)
mae_multi = mean_absolute_error(y_multi, y_pred_multi)

print("📊 Modèle : amp_optimal = β0 + β1×surprise + β2×impact + β3×score")
print()
print(f"Coefficients :")
print(f"   Intercept (β0)      : {reg_multi.intercept_:.4f}")
for i, col in enumerate(feature_cols):
    print(f"   {col:20s} (β{i+1}) : {reg_multi.coef_[i]:+.4f}")
print()
print(f"Métriques :")
print(f"   R²              : {r2_multi:.3f}")
print(f"   MAE             : {mae_multi:.3f}")
print()

# Prédictions
df['amp_predicted'] = y_pred_multi
df['amp_error'] = abs(df['amp_predicted'] - df['amp_optimal'])

print("📊 Prédictions par date :")
print("-"*80)
for _, row in df.iterrows():
    print(f"   {row['date']} : amp_optimal={row['amp_optimal']:.3f} | "
          f"predicted={row['amp_predicted']:.3f} | error={row['amp_error']:.3f}")
print()

# =============================================================================
# ANALYSE OUTLIERS
# =============================================================================

print("="*80)
print("5. ANALYSE OUTLIERS")
print("="*80)
print()

# Identifier outliers (amp > 3.0 ou amp < 1.8)
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

# Comparer MAE baseline vs MAE régression
baseline_mae = df['error_baseline'].mean()
regression_mae = mae_multi  # MAE de la régression sur amp_optimal

print("📊 Comparaison performance :")
print(f"   MAE Baseline (amp=2.5 fixe)  : {baseline_mae:.2f} pips")
print(f"   MAE Régression (amp dynamique) : Non calculable directement")
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
    print("   Formule proposée :")
    print(f"   amp = {reg_multi.intercept_:.4f} ", end="")
    for i, col in enumerate(feature_cols):
        print(f"{reg_multi.coef_[i]:+.4f}×{col} ", end="")
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
output_file = Path(__file__).parent / "cluster3_analysis_results.csv"
df.to_csv(output_file, index=False)
print()
print(f"✅ Résultats enrichis sauvegardés : {output_file.name}")
