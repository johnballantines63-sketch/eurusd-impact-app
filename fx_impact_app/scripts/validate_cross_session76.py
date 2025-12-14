#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATION CROISÉE V3 - SESSION 76
==================================
Objectif : Détecter overfitting sur modèle V3 (R²=0.994)
Méthode : Split 70/30 train/test
Critères décision :
- R² test >0.75 → V3 validé (formulas_v2.2.py)
- R² test <0.60 → Overfitting (formulas_v2.1.py basé V1)
- R² test 0.60-0.75 → Analyse approfondie
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# CHARGEMENT DONNÉES V3
# ==============================================================================

print("=" * 80)
print("VALIDATION CROISÉE V3 - SESSION 76")
print("=" * 80)

# Charger dataset V3
df = pd.read_csv('../data/dataset_complete_session75_v3.csv')
print(f"\n✅ Dataset V3 chargé : {len(df)} lignes")

# Filtrer mouvements significatifs (seuil 80 pips comme V1)
df_filtered = df[df['impact_observed'] >= 80].copy()
print(f"✅ Mouvements ≥80 pips : {len(df_filtered)} lignes")

# Agréger par date
df_grouped = df_filtered.groupby('date').agg({
    'impact_observed': 'max',
    'nb_events': 'first',
    'score_cumule': 'first',
    'score_moyen': 'first',
    'surprise_max': 'first',
    'surprise_moyenne': 'first',
    'surprise_cumule': 'first',
    'ratio_concordance': 'first',
    'coherence_famille': 'first',
    'time_of_day': 'first',
    'day_of_week': 'first',
    'event_type': 'first',
    'country': 'first'
}).reset_index()

print(f"✅ Dates uniques : {len(df_grouped)}")

# ==============================================================================
# PRÉPARATION FEATURES
# ==============================================================================

# Remplacer NaN par 0 pour features numériques
numeric_cols = ['score_cumule', 'score_moyen', 'surprise_max', 
                'surprise_moyenne', 'surprise_cumule']
for col in numeric_cols:
    df_grouped[col] = df_grouped[col].fillna(0)

# Encoder features catégorielles
df_grouped['time_of_day_encoded'] = df_grouped['time_of_day'].map({
    'Asia': 0, 'EU': 1, 'US': 2
}).fillna(1)

df_grouped['event_type_encoded'] = df_grouped['event_type'].map({
    'CPI': 0, 'PMI': 1, 'Other': 2, None: 2
}).fillna(2)

df_grouped['country_encoded'] = df_grouped['country'].map({
    'US': 0, 'EU': 1, 'CH': 2, 'JP': 3, None: 1
}).fillna(1)

# Sélectionner features (12 features comme V3)
feature_cols = [
    'nb_events',
    'score_cumule',
    'score_moyen',
    'surprise_max',
    'surprise_moyenne',
    'surprise_cumule',
    'ratio_concordance',
    'coherence_famille',
    'time_of_day_encoded',
    'day_of_week',
    'event_type_encoded',
    'country_encoded'
]

X = df_grouped[feature_cols].values
y = df_grouped['impact_observed'].values

print(f"\n✅ Features (X) : {X.shape}")
print(f"✅ Target (y) : {y.shape}")
print(f"✅ Ratio points/features : {X.shape[0] / X.shape[1]:.2f}")

# ==============================================================================
# VALIDATION CROISÉE SIMPLE (70/30)
# ==============================================================================

print("\n" + "=" * 80)
print("VALIDATION SIMPLE : SPLIT 70/30")
print("=" * 80)

# Split train/test (70/30)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)

print(f"\n📊 Split :")
print(f"   Train : {len(X_train)} points ({len(X_train)/len(X)*100:.0f}%)")
print(f"   Test  : {len(X_test)} points ({len(X_test)/len(X)*100:.0f}%)")

# Entraîner modèle (mêmes paramètres que V3)
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=5,
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=42
)

model.fit(X_train, y_train)
print("\n✅ Modèle entraîné")

# Prédictions
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

# Métriques TRAIN
r2_train = r2_score(y_train, y_pred_train)
mae_train = mean_absolute_error(y_train, y_pred_train)
rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train))

# Métriques TEST
r2_test = r2_score(y_test, y_pred_test)
mae_test = mean_absolute_error(y_test, y_pred_test)
rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))

# ==============================================================================
# RÉSULTATS
# ==============================================================================

print("\n" + "=" * 80)
print("📊 RÉSULTATS VALIDATION")
print("=" * 80)

print("\n🎯 TRAIN (11 points) :")
print(f"   R²   : {r2_train:.3f}")
print(f"   MAE  : {mae_train:.1f} pips")
print(f"   RMSE : {rmse_train:.1f} pips")

print("\n🎯 TEST (5 points) :")
print(f"   R²   : {r2_test:.3f}")
print(f"   MAE  : {mae_test:.1f} pips")
print(f"   RMSE : {rmse_test:.1f} pips")

print("\n📈 ÉCART Train vs Test :")
delta_r2 = r2_train - r2_test
delta_mae = mae_test - mae_train
print(f"   ΔR²  : {delta_r2:+.3f} ({abs(delta_r2/r2_train)*100:.1f}% variation)")
print(f"   ΔMAE : {delta_mae:+.1f} pips ({abs(delta_mae/mae_train)*100:.1f}% variation)")

# ==============================================================================
# VALIDATION CROISÉE K-FOLD (3 splits)
# ==============================================================================

print("\n" + "=" * 80)
print("VALIDATION K-FOLD (3 SPLITS)")
print("=" * 80)

kfold = KFold(n_splits=3, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
cv_mae_scores = cross_val_score(model, X, y, cv=kfold, 
                                 scoring='neg_mean_absolute_error')

print(f"\n🎯 R² Cross-Val :")
print(f"   Scores : {[f'{s:.3f}' for s in cv_scores]}")
print(f"   Moyenne : {cv_scores.mean():.3f}")
print(f"   Écart-type : {cv_scores.std():.3f}")

print(f"\n🎯 MAE Cross-Val :")
mae_cv_values = -cv_mae_scores
print(f"   Scores : {[f'{s:.1f}' for s in mae_cv_values]} pips")
print(f"   Moyenne : {mae_cv_values.mean():.1f} pips")
print(f"   Écart-type : {mae_cv_values.std():.1f} pips")

# ==============================================================================
# ANALYSE DÉTAILS TEST
# ==============================================================================

print("\n" + "=" * 80)
print("📋 DÉTAILS PRÉDICTIONS TEST")
print("=" * 80)

test_results = pd.DataFrame({
    'Réel': y_test,
    'Prédit': y_pred_test,
    'Erreur': np.abs(y_test - y_pred_test)
})
test_results = test_results.sort_values('Erreur', ascending=False)

print("\n" + test_results.to_string(index=False))

# ==============================================================================
# DÉCISION FINALE
# ==============================================================================

print("\n" + "=" * 80)
print("🎯 DÉCISION VALIDATION V3")
print("=" * 80)

print(f"\n📊 Critères décision :")
print(f"   R² test actuel : {r2_test:.3f}")
print(f"   R² train (V3)  : 0.994 (session 75)")
print(f"   R² train actuel: {r2_train:.3f}")

print("\n🔍 Analyse overfitting :")
if delta_r2 > 0.3:
    overfitting_status = "FORT"
    emoji = "🔴"
elif delta_r2 > 0.15:
    overfitting_status = "MODÉRÉ"
    emoji = "🟠"
else:
    overfitting_status = "FAIBLE"
    emoji = "🟢"

print(f"   {emoji} Overfitting : {overfitting_status}")
print(f"   Écart R² : {delta_r2:+.3f}")

print("\n💡 RECOMMANDATION :")
if r2_test > 0.75:
    decision = "✅ V3 VALIDÉ"
    version = "formulas_validated_v2.2.py"
    description = "Modèle V3 (12 features) généralise bien"
elif r2_test < 0.60:
    decision = "⚠️ OVERFITTING DÉTECTÉ"
    version = "formulas_validated_v2.1.py"
    description = "Utiliser V1 (8 features, R²=0.705)"
else:
    decision = "⚡ ZONE GRISE"
    version = "Analyse approfondie requise"
    description = f"R² test={r2_test:.3f}, MAE test={mae_test:.1f} pips"

print(f"\n   {decision}")
print(f"   Version à créer : {version}")
print(f"   Raison : {description}")

# ==============================================================================
# IMPORTANCE FEATURES (si V3 validé)
# ==============================================================================

if r2_test > 0.60:
    print("\n" + "=" * 80)
    print("📊 IMPORTANCE FEATURES")
    print("=" * 80)
    
    feature_importance = pd.DataFrame({
        'Feature': feature_cols,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=False)
    
    print("\n" + feature_importance.to_string(index=False))

# ==============================================================================
# SAUVEGARDE RÉSULTATS
# ==============================================================================

results_summary = f"""
VALIDATION CROISÉE V3 - SESSION 76
==================================
Date : 2024-10-24

CONFIGURATION
-------------
Dataset : dataset_complete_session75_v3.csv
Seuil : 80 pips
Points total : {len(df_grouped)}
Features : {len(feature_cols)} (V3)
Split : 70/30 (train/test)

RÉSULTATS SPLIT 70/30
---------------------
TRAIN ({len(X_train)} points) :
  R²   = {r2_train:.3f}
  MAE  = {mae_train:.1f} pips
  RMSE = {rmse_train:.1f} pips

TEST ({len(X_test)} points) :
  R²   = {r2_test:.3f}
  MAE  = {mae_test:.1f} pips
  RMSE = {rmse_test:.1f} pips

ÉCART Train/Test :
  ΔR²  = {delta_r2:+.3f}
  ΔMAE = {delta_mae:+.1f} pips

VALIDATION K-FOLD (3 splits)
----------------------------
R² Cross-Val  : {cv_scores.mean():.3f} ± {cv_scores.std():.3f}
MAE Cross-Val : {mae_cv_values.mean():.1f} ± {mae_cv_values.std():.1f} pips

ANALYSE OVERFITTING
-------------------
Statut : {overfitting_status}
Écart R² : {delta_r2:+.3f}
Ratio pts/features : {X.shape[0] / X.shape[1]:.2f}

DÉCISION
--------
{decision}
Version : {version}
Description : {description}

COMPARAISON V1 vs V3
--------------------
V1 (Session 75) :
  R² = 0.705
  MAE = 7.7 pips
  Features = 8
  
V3 (Session 75 training) :
  R² = 0.994
  MAE = 1.1 pips
  Features = 12

V3 (Session 76 test) :
  R² = {r2_test:.3f}
  MAE = {mae_test:.1f} pips
  Features = 12
"""

# Sauvegarder
with open('../data/validation_results_session76.txt', 'w', encoding='utf-8') as f:
    f.write(results_summary)

print("\n✅ Résultats sauvegardés : validation_results_session76.txt")

print("\n" + "=" * 80)
print("FIN VALIDATION CROISÉE")
print("=" * 80)
