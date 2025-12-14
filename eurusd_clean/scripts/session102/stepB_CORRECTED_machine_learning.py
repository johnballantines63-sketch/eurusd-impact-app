#!/usr/bin/env python3
"""
ÉTAPE B : MACHINE LEARNING (MÉTHODOLOGIE CORRECTE)
===================================================

CORRECTION : Suivre la VRAIE méthodologie de validation

Méthode :
1. Calculer impact avec amp=2.5 (baseline)
2. ML prédit amp_optimal
3. Recalculer impact avec amp_optimal
4. Comparer ERREUR EN PIPS vs baseline

Pas de prédiction directe de amp_parfaite !
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

print("=" * 80)
print("ÉTAPE B : MACHINE LEARNING (CORRIGÉ)")
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
# BASELINE (amp=2.5 fixe)
# ============================================================================

print("=" * 80)
print("BASELINE (amp=2.5 fixe)")
print("=" * 80)
print()

# Erreurs baseline EN PIPS
df['erreur_baseline_pips'] = np.abs(df['impact_real'] - df['impact_predit'])
mae_baseline_pips = df['erreur_baseline_pips'].mean()

print(f"MAE baseline : {mae_baseline_pips:.2f} pips")
print(f"   (impact calculé avec amp=2.5)")
print()

# ============================================================================
# PRÉPARER FEATURES
# ============================================================================

print("=" * 80)
print("PRÉPARATION FEATURES")
print("=" * 80)
print()

feature_columns = ['r_squared', 'duration_hours', 'amplitude_pips', 'num_events', 'max_surprise']

print("Features utilisées :")
for i, feat in enumerate(feature_columns, 1):
    print(f"   {i}. {feat}")
print()

X = df[feature_columns].values
y_target = df['amp_parfaite'].values  # Cible : amp_parfaite pour entraînement

print(f"X shape : {X.shape}")
print(f"Target : amp_parfaite (pour prédire amp optimal)")
print()

# ============================================================================
# MODÈLE 1 : RÉGRESSION LINÉAIRE (LOO)
# ============================================================================

print("=" * 80)
print("MODÈLE 1 : RÉGRESSION LINÉAIRE MULTIPLE")
print("=" * 80)
print()

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

loo = LeaveOneOut()
model_lr = LinearRegression()

predictions_amp_lr = []
errors_pips_lr = []

print("Cross-validation Leave-One-Out :")
print()

for train_idx, test_idx in loo.split(X_scaled):
    X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
    y_train, y_test = y_target[train_idx], y_target[test_idx]
    
    # Entraîner sur amp_parfaite
    model_lr.fit(X_train, y_train)
    amp_pred = model_lr.predict(X_test)[0]
    
    # MÉTHODOLOGIE CORRECTE : Recalculer impact avec amp prédit
    impact_base = df.iloc[test_idx[0]]['impact_predit']
    impact_pred = impact_base / 2.5 * amp_pred
    impact_real = df.iloc[test_idx[0]]['impact_real']
    
    # Erreur en PIPS
    error_pips = np.abs(impact_real - impact_pred)
    
    predictions_amp_lr.append(amp_pred)
    errors_pips_lr.append(error_pips)

errors_pips_lr = np.array(errors_pips_lr)
mae_lr_pips = errors_pips_lr.mean()

improvement_lr = ((mae_baseline_pips - mae_lr_pips) / mae_baseline_pips) * 100

print(f"MAE (LOO) : {mae_lr_pips:.2f} pips")
print(f"Amélioration vs baseline : {improvement_lr:+.1f}%")
print()

# Entraîner sur toutes données pour coefficients
model_lr_full = LinearRegression()
model_lr_full.fit(X_scaled, y_target)

print("Coefficients (features standardisées) :")
for feat, coef in zip(feature_columns, model_lr_full.coef_):
    print(f"   {feat:20s} : {coef:+.4f}")
print(f"   Intercept              : {model_lr_full.intercept_:+.4f}")
print()

importance_lr = np.abs(model_lr_full.coef_)
importance_lr_norm = importance_lr / importance_lr.sum()

print("Importance relative features :")
for feat, imp in sorted(zip(feature_columns, importance_lr_norm), key=lambda x: x[1], reverse=True):
    print(f"   {feat:20s} : {imp:.1%}")
print()

# ============================================================================
# MODÈLE 2 : RANDOM FOREST (LOO)
# ============================================================================

print("=" * 80)
print("MODÈLE 2 : RANDOM FOREST")
print("=" * 80)
print()

model_rf = RandomForestRegressor(
    n_estimators=50,
    max_depth=3,
    min_samples_split=5,
    random_state=42
)

predictions_amp_rf = []
errors_pips_rf = []

for train_idx, test_idx in loo.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y_target[train_idx], y_target[test_idx]
    
    model_rf.fit(X_train, y_train)
    amp_pred = model_rf.predict(X_test)[0]
    
    # Recalculer impact
    impact_base = df.iloc[test_idx[0]]['impact_predit']
    impact_pred = impact_base / 2.5 * amp_pred
    impact_real = df.iloc[test_idx[0]]['impact_real']
    
    error_pips = np.abs(impact_real - impact_pred)
    
    predictions_amp_rf.append(amp_pred)
    errors_pips_rf.append(error_pips)

errors_pips_rf = np.array(errors_pips_rf)
mae_rf_pips = errors_pips_rf.mean()

improvement_rf = ((mae_baseline_pips - mae_rf_pips) / mae_baseline_pips) * 100

print(f"MAE (LOO) : {mae_rf_pips:.2f} pips")
print(f"Amélioration vs baseline : {improvement_rf:+.1f}%")
print()

# Feature importance
model_rf_full = RandomForestRegressor(
    n_estimators=50,
    max_depth=3,
    min_samples_split=5,
    random_state=42
)
model_rf_full.fit(X, y_target)

importance_rf = model_rf_full.feature_importances_

print("Importance features :")
for feat, imp in sorted(zip(feature_columns, importance_rf), key=lambda x: x[1], reverse=True):
    print(f"   {feat:20s} : {imp:.1%}")
print()

# ============================================================================
# COMPARAISON MODÈLES (EN PIPS !)
# ============================================================================

print("=" * 80)
print("COMPARAISON MODÈLES (MAE EN PIPS)")
print("=" * 80)
print()

results = {
    'Baseline (amp=2.5)': {'mae': mae_baseline_pips, 'improvement': 0},
    'Linear Regression': {'mae': mae_lr_pips, 'improvement': improvement_lr},
    'Random Forest': {'mae': mae_rf_pips, 'improvement': improvement_rf}
}

print("Classement (MAE) :")
for i, (name, metrics) in enumerate(sorted(results.items(), key=lambda x: x[1]['mae']), 1):
    status = "✅" if metrics['improvement'] > 5 else "⚠️" if metrics['improvement'] > 0 else "❌"
    print(f"   {i}. {status} {name:25s} : MAE={metrics['mae']:.2f} pips ({metrics['improvement']:+.1f}%)")
print()

best_model_name = min(results.items(), key=lambda x: x[1]['mae'])[0]
best_mae = results[best_model_name]['mae']
best_improvement = results[best_model_name]['improvement']

if best_improvement > 20:
    print(f"✅✅ {best_model_name} : AMÉLIORATION SIGNIFICATIVE")
elif best_improvement > 10:
    print(f"✅ {best_model_name} : Amélioration bonne")
elif best_improvement > 5:
    print(f"⚠️ {best_model_name} : Amélioration faible")
else:
    print(f"❌ Aucun modèle n'améliore significativement")

print()

# ============================================================================
# SAUVEGARDER RÉSULTATS
# ============================================================================

df_results = df[['event_date', 'r_squared', 'duration_hours', 'impact_predit', 'impact_real']].copy()
df_results['amp_pred_lr'] = predictions_amp_lr
df_results['amp_pred_rf'] = predictions_amp_rf
df_results['error_baseline_pips'] = errors_pips_lr  # Baseline identique pour tous
df_results['error_lr_pips'] = errors_pips_lr
df_results['error_rf_pips'] = errors_pips_rf

df_results.to_csv(data_dir / "stepB_CORRECTED_results_ml.csv", index=False)

print(f"✅ Résultats : stepB_CORRECTED_results_ml.csv")
print()

# ============================================================================
# GRAPHIQUES
# ============================================================================

print("=" * 80)
print("GÉNÉRATION GRAPHIQUES")
print("=" * 80)
print()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('ML : Prédiction Amplification (Méthodologie Correcte)', fontsize=16)

# Graph 1 : Erreurs baseline vs LR
axes[0, 0].scatter(df['erreur_baseline_pips'], errors_pips_lr, alpha=0.6, s=100)
axes[0, 0].plot([0, df['erreur_baseline_pips'].max()], 
                [0, df['erreur_baseline_pips'].max()], 
                'r--', alpha=0.5, label='Pas de gain')
axes[0, 0].set_xlabel('Erreur Baseline (pips)')
axes[0, 0].set_ylabel('Erreur Linear Regression (pips)')
axes[0, 0].set_title(f'Amélioration : {improvement_lr:+.1f}%')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Graph 2 : Erreurs baseline vs RF
axes[0, 1].scatter(df['erreur_baseline_pips'], errors_pips_rf, alpha=0.6, s=100, color='orange')
axes[0, 1].plot([0, df['erreur_baseline_pips'].max()], 
                [0, df['erreur_baseline_pips'].max()], 
                'r--', alpha=0.5, label='Pas de gain')
axes[0, 1].set_xlabel('Erreur Baseline (pips)')
axes[0, 1].set_ylabel('Erreur Random Forest (pips)')
axes[0, 1].set_title(f'Amélioration : {improvement_rf:+.1f}%')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Graph 3 : Distribution erreurs
axes[1, 0].hist([df['erreur_baseline_pips'], errors_pips_lr, errors_pips_rf], 
                bins=15, alpha=0.7, label=['Baseline', 'LR', 'RF'])
axes[1, 0].set_xlabel('Erreur (pips)')
axes[1, 0].set_ylabel('Fréquence')
axes[1, 0].set_title('Distribution Erreurs')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Graph 4 : Comparaison MAE
model_names = ['Baseline', 'LR', 'RF']
model_maes = [mae_baseline_pips, mae_lr_pips, mae_rf_pips]
colors = ['red' if mae == mae_baseline_pips else 'green' if mae < mae_baseline_pips else 'orange' for mae in model_maes]

axes[1, 1].bar(model_names, model_maes, color=colors, alpha=0.7)
axes[1, 1].set_ylabel('MAE (pips)')
axes[1, 1].set_title('Comparaison MAE')
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
graph_path = data_dir / "stepB_CORRECTED_machine_learning.png"
plt.savefig(graph_path, dpi=150)
print(f"✅ Graphiques : {graph_path}")
print()

# ============================================================================
# CONCLUSIONS
# ============================================================================

print("=" * 80)
print("CONCLUSIONS ÉTAPE B (CORRIGÉ)")
print("=" * 80)
print()

print(f"1. MÉTHODE : Calcul impact puis comparaison PIPS (CORRECT)")
print()

print(f"2. RÉSULTATS :")
print(f"   Baseline   : {mae_baseline_pips:.2f} pips")
print(f"   LR         : {mae_lr_pips:.2f} pips ({improvement_lr:+.1f}%)")
print(f"   RF         : {mae_rf_pips:.2f} pips ({improvement_rf:+.1f}%)")
print()

print(f"3. FEATURES IMPORTANTES (LR) :")
top_features = sorted(zip(feature_columns, importance_lr_norm), key=lambda x: x[1], reverse=True)[:3]
for feat, imp in top_features:
    print(f"   {feat} ({imp:.1%})")
print()

if best_improvement > 10:
    print("✅ RECOMMANDATION : ML apporte amélioration")
else:
    print("⚠️ RECOMMANDATION : Tester B' (Zones simples)")

print()
print("=" * 80)
print("✅ ÉTAPE B TERMINÉE (CORRIGÉ)")
print("=" * 80)
