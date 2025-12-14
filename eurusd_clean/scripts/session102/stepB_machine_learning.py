#!/usr/bin/env python3
"""
ÉTAPE B : MACHINE LEARNING POUR AMPLIFICATION
==============================================

Test modèles ML pour prédire amp_parfaite
avec validation rigoureuse (LOO cross-validation)

Modèles testés :
1. Régression Linéaire Multiple (interprétable)
2. Random Forest (non-linéaire)

Features : R², durée, amplitude, num_events, max_surprise
Target : amp_parfaite
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import warnings

warnings.filterwarnings('ignore')

print("=" * 80)
print("ÉTAPE B : MACHINE LEARNING")
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

print("⚠️  ATTENTION : 22 points = échantillon TRÈS PETIT pour ML")
print("   Risque élevé d'overfitting")
print("   → Utilisation Leave-One-Out obligatoire")
print()

# ============================================================================
# PRÉPARER FEATURES
# ============================================================================

print("=" * 80)
print("PRÉPARATION FEATURES")
print("=" * 80)
print()

# Features disponibles
feature_columns = ['r_squared', 'duration_hours', 'amplitude_pips', 'num_events', 'max_surprise']

print("Features utilisées :")
for i, feat in enumerate(feature_columns, 1):
    print(f"   {i}. {feat}")
print()

# Vérifier données manquantes
missing = df[feature_columns].isnull().sum()
if missing.sum() > 0:
    print("⚠️ Données manquantes :")
    print(missing[missing > 0])
    print()

# Préparer X et y
X = df[feature_columns].values
y = df['amp_parfaite'].values

print(f"X shape : {X.shape}")
print(f"y shape : {y.shape}")
print()

# Statistiques features
print("Statistiques features :")
print(df[feature_columns].describe())
print()

# ============================================================================
# BASELINE (amp=2.5)
# ============================================================================

print("=" * 80)
print("BASELINE (amp=2.5 fixe)")
print("=" * 80)
print()

# Recalculer erreur baseline pour comparaison
y_baseline = np.full_like(y, 1.0)  # amp_parfaite = 1.0 si prédiction parfaite avec amp=2.5
mae_baseline = mean_absolute_error(y, y_baseline)

print(f"MAE baseline (prédire amp=1.0 toujours) : {mae_baseline:.3f}")
print(f"→ Équivaut à erreur {mae_baseline * df['impact_predit'].mean():.1f} pips moyenne")
print()

# ============================================================================
# MODÈLE 1 : RÉGRESSION LINÉAIRE MULTIPLE
# ============================================================================

print("=" * 80)
print("MODÈLE 1 : RÉGRESSION LINÉAIRE MULTIPLE")
print("=" * 80)
print()

# Standardiser features (important pour régression)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Leave-One-Out Cross-Validation
loo = LeaveOneOut()
model_lr = LinearRegression()

predictions_lr = []
true_values = []

print("Cross-validation Leave-One-Out (LOO) :")
print("   (Entraîne sur 21, teste sur 1, répète 22 fois)")
print()

for train_idx, test_idx in loo.split(X_scaled):
    X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    model_lr.fit(X_train, y_train)
    pred = model_lr.predict(X_test)[0]
    
    predictions_lr.append(pred)
    true_values.append(y_test[0])

predictions_lr = np.array(predictions_lr)
true_values = np.array(true_values)

# Métriques
mae_lr = mean_absolute_error(true_values, predictions_lr)
r2_lr = r2_score(true_values, predictions_lr)

print(f"MAE (LOO) : {mae_lr:.3f}")
print(f"R² (LOO)  : {r2_lr:.3f}")
print()

# Amélioration vs baseline
improvement_lr = ((mae_baseline - mae_lr) / mae_baseline) * 100
print(f"Amélioration vs baseline : {improvement_lr:+.1f}%")
print()

# Entraîner sur TOUTES les données pour voir coefficients
model_lr_full = LinearRegression()
model_lr_full.fit(X_scaled, y)

print("Coefficients (features standardisées) :")
for feat, coef in zip(feature_columns, model_lr_full.coef_):
    print(f"   {feat:20s} : {coef:+.4f}")
print(f"   Intercept              : {model_lr_full.intercept_:+.4f}")
print()

# Feature importance (valeur absolue coefficients)
importance_lr = np.abs(model_lr_full.coef_)
importance_lr_norm = importance_lr / importance_lr.sum()

print("Importance relative features :")
for feat, imp in sorted(zip(feature_columns, importance_lr_norm), key=lambda x: x[1], reverse=True):
    print(f"   {feat:20s} : {imp:.1%}")
print()

# ============================================================================
# MODÈLE 2 : RANDOM FOREST
# ============================================================================

print("=" * 80)
print("MODÈLE 2 : RANDOM FOREST")
print("=" * 80)
print()

print("⚠️  Random Forest avec 22 points = RISQUE OVERFITTING ÉLEVÉ")
print("   Résultats à prendre avec précaution")
print()

# Random Forest avec paramètres conservateurs (éviter overfitting)
model_rf = RandomForestRegressor(
    n_estimators=50,      # Peu d'arbres
    max_depth=3,          # Arbres peu profonds
    min_samples_split=5,  # Minimum 5 échantillons pour split
    random_state=42
)

predictions_rf = []

for train_idx, test_idx in loo.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    model_rf.fit(X_train, y_train)
    pred = model_rf.predict(X_test)[0]
    
    predictions_rf.append(pred)

predictions_rf = np.array(predictions_rf)

# Métriques
mae_rf = mean_absolute_error(true_values, predictions_rf)
r2_rf = r2_score(true_values, predictions_rf)

print(f"MAE (LOO) : {mae_rf:.3f}")
print(f"R² (LOO)  : {r2_rf:.3f}")
print()

improvement_rf = ((mae_baseline - mae_rf) / mae_baseline) * 100
print(f"Amélioration vs baseline : {improvement_rf:+.1f}%")
print()

# Entraîner sur toutes les données pour feature importance
model_rf_full = RandomForestRegressor(
    n_estimators=50,
    max_depth=3,
    min_samples_split=5,
    random_state=42
)
model_rf_full.fit(X, y)

importance_rf = model_rf_full.feature_importances_

print("Importance features (Random Forest) :")
for feat, imp in sorted(zip(feature_columns, importance_rf), key=lambda x: x[1], reverse=True):
    print(f"   {feat:20s} : {imp:.1%}")
print()

# ============================================================================
# COMPARAISON MODÈLES
# ============================================================================

print("=" * 80)
print("COMPARAISON MODÈLES")
print("=" * 80)
print()

results = {
    'Baseline (amp=1.0)': {'mae': mae_baseline, 'improvement': 0},
    'Linear Regression': {'mae': mae_lr, 'improvement': improvement_lr},
    'Random Forest': {'mae': mae_rf, 'improvement': improvement_rf}
}

print("Classement (MAE) :")
for i, (name, metrics) in enumerate(sorted(results.items(), key=lambda x: x[1]['mae']), 1):
    print(f"   {i}. {name:25s} : MAE={metrics['mae']:.3f} ({metrics['improvement']:+.1f}%)")
print()

# Meilleur modèle
best_model_name = min(results.items(), key=lambda x: x[1]['mae'])[0]
best_mae = results[best_model_name]['mae']
best_improvement = results[best_model_name]['improvement']

if best_improvement > 20:
    print(f"✅✅ {best_model_name} : AMÉLIORATION SIGNIFICATIVE ({best_improvement:+.1f}%)")
elif best_improvement > 10:
    print(f"✅ {best_model_name} : Amélioration bonne ({best_improvement:+.1f}%)")
elif best_improvement > 5:
    print(f"⚠️ {best_model_name} : Amélioration faible ({best_improvement:+.1f}%)")
else:
    print(f"❌ Aucun modèle n'améliore significativement le baseline")

print()

# ============================================================================
# ANALYSE ERREURS PAR CAS
# ============================================================================

print("=" * 80)
print("ANALYSE ERREURS PAR CAS")
print("=" * 80)
print()

df_results = df[['event_date', 'r_squared', 'duration_hours', 'amp_parfaite']].copy()
df_results['pred_lr'] = predictions_lr
df_results['pred_rf'] = predictions_rf
df_results['pred_baseline'] = 1.0

df_results['error_lr'] = np.abs(df_results['amp_parfaite'] - df_results['pred_lr'])
df_results['error_rf'] = np.abs(df_results['amp_parfaite'] - df_results['pred_rf'])
df_results['error_baseline'] = np.abs(df_results['amp_parfaite'] - df_results['pred_baseline'])

# Cas où LR aide le plus
print("TOP 5 CAS : Linear Regression aide le plus :")
top_lr = df_results.copy()
top_lr['gain_lr'] = top_lr['error_baseline'] - top_lr['error_lr']
top_lr = top_lr.nlargest(5, 'gain_lr')

for idx, row in top_lr.iterrows():
    print(f"   {row['event_date'].strftime('%Y-%m-%d')} : Gain {row['gain_lr']:.3f}")
    print(f"      Erreur baseline: {row['error_baseline']:.3f} → LR: {row['error_lr']:.3f}")
print()

# Cas où LR dégrade
print("TOP 5 CAS : Linear Regression dégrade :")
bottom_lr = df_results.copy()
bottom_lr['loss_lr'] = bottom_lr['error_lr'] - bottom_lr['error_baseline']
bottom_lr = bottom_lr.nlargest(5, 'loss_lr')

for idx, row in bottom_lr.iterrows():
    print(f"   {row['event_date'].strftime('%Y-%m-%d')} : Perte {row['loss_lr']:.3f}")
    print(f"      Erreur baseline: {row['error_baseline']:.3f} → LR: {row['error_lr']:.3f}")
print()

# ============================================================================
# GRAPHIQUES
# ============================================================================

print("=" * 80)
print("GÉNÉRATION GRAPHIQUES")
print("=" * 80)
print()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Machine Learning : Prédiction Amplification', fontsize=16)

# Graph 1 : Prédictions vs Réel (Linear Regression)
axes[0, 0].scatter(true_values, predictions_lr, alpha=0.6, s=100)
axes[0, 0].plot([true_values.min(), true_values.max()], 
                [true_values.min(), true_values.max()], 
                'r--', alpha=0.5, label='Prédiction parfaite')
axes[0, 0].set_xlabel('Amp Parfaite (réel)')
axes[0, 0].set_ylabel('Amp Prédite (LR)')
axes[0, 0].set_title(f'Linear Regression - R²={r2_lr:.3f}')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Graph 2 : Prédictions vs Réel (Random Forest)
axes[0, 1].scatter(true_values, predictions_rf, alpha=0.6, s=100, color='orange')
axes[0, 1].plot([true_values.min(), true_values.max()], 
                [true_values.min(), true_values.max()], 
                'r--', alpha=0.5, label='Prédiction parfaite')
axes[0, 1].set_xlabel('Amp Parfaite (réel)')
axes[0, 1].set_ylabel('Amp Prédite (RF)')
axes[0, 1].set_title(f'Random Forest - R²={r2_rf:.3f}')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Graph 3 : Feature Importance (LR)
axes[1, 0].barh(feature_columns, importance_lr_norm)
axes[1, 0].set_xlabel('Importance Relative')
axes[1, 0].set_title('Feature Importance (Linear Regression)')
axes[1, 0].grid(True, alpha=0.3, axis='x')

# Graph 4 : Feature Importance (RF)
axes[1, 1].barh(feature_columns, importance_rf, color='orange')
axes[1, 1].set_xlabel('Importance')
axes[1, 1].set_title('Feature Importance (Random Forest)')
axes[1, 1].grid(True, alpha=0.3, axis='x')

plt.tight_layout()
graph_path = data_dir / "stepB_machine_learning.png"
plt.savefig(graph_path, dpi=150)
print(f"✅ Graphiques : {graph_path}")
print()

# Sauvegarder résultats
df_results.to_csv(data_dir / "stepB_results_ml.csv", index=False)
print(f"✅ Résultats : stepB_results_ml.csv")
print()

# ============================================================================
# CONCLUSIONS
# ============================================================================

print("=" * 80)
print("CONCLUSIONS ÉTAPE B")
print("=" * 80)
print()

print(f"1. MEILLEUR MODÈLE : {best_model_name}")
print(f"   MAE : {best_mae:.3f}")
print(f"   Amélioration : {best_improvement:+.1f}%")
print()

print(f"2. FEATURES IMPORTANTES (Linear Regression) :")
top_features = sorted(zip(feature_columns, importance_lr_norm), key=lambda x: x[1], reverse=True)[:3]
for feat, imp in top_features:
    print(f"   - {feat} ({imp:.1%})")
print()

if best_improvement > 10:
    print("✅ RECOMMANDATION : ML apporte amélioration")
    print("   → Intégrer modèle dans Planificateur")
    print()
elif best_improvement > 0:
    print("⚠️ RECOMMANDATION : Amélioration faible")
    print("   → Tester B' (Calibration par zones)")
    print()
else:
    print("❌ RECOMMANDATION : ML n'apporte rien")
    print("   → Passer à B' (Calibration par zones)")
    print()

print("3. LIMITES :")
print("   ⚠️ Seulement 22 observations")
print("   ⚠️ Risque overfitting (surtout Random Forest)")
print("   ⚠️ Généralisation incertaine")
print()

print("4. PROCHAINE ÉTAPE :")
if best_improvement < 10:
    print("   → Tester B' : Calibration par zones (SIMPLE)")
    print("   → Puis C : Analyser cas extrême 2024-11-13")
else:
    print("   → C : Analyser cas extrême 2024-11-13")
    print("   → Puis intégration Planificateur")

print()
print("=" * 80)
print("✅ ÉTAPE B TERMINÉE")
print("=" * 80)
