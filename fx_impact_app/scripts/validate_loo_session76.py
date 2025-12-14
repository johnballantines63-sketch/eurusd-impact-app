#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATION CROISÉE SIMPLE V3 - SESSION 76
==========================================
Analyse rapide avec régression linéaire pour évaluer la généralisation
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

print("=" * 80)
print("VALIDATION CROISÉE V3 - SESSION 76 (VERSION SIMPLIFIÉE)")
print("=" * 80)

# Charger dataset
df = pd.read_csv('../data/dataset_complete_session75_v3.csv')
print(f"\n✅ Dataset chargé : {len(df)} lignes")

# Filtrer ≥80 pips
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
print(f"✅ Ratio points/features (12) : {len(df_grouped)/12:.2f}")

# Préparer features
numeric_cols = ['score_cumule', 'score_moyen', 'surprise_max', 
                'surprise_moyenne', 'surprise_cumule']
for col in numeric_cols:
    df_grouped[col] = df_grouped[col].fillna(0)

# Encoder catégorielles
df_grouped['time_of_day_enc'] = df_grouped['time_of_day'].map({
    'Asia': 0, 'EU': 1, 'US': 2
}).fillna(1)

df_grouped['event_type_enc'] = df_grouped['event_type'].map({
    'CPI': 0, 'PMI': 1, 'Other': 2, None: 2
}).fillna(2)

df_grouped['country_enc'] = df_grouped['country'].map({
    'US': 0, 'EU': 1, 'CH': 2, 'JP': 3, None: 1
}).fillna(1)

# Sélectionner features
feature_cols = [
    'nb_events', 'score_cumule', 'score_moyen', 'surprise_max',
    'surprise_moyenne', 'surprise_cumule', 'ratio_concordance',
    'coherence_famille', 'time_of_day_enc', 'day_of_week',
    'event_type_enc', 'country_enc'
]

X = df_grouped[feature_cols].values
y = df_grouped['impact_observed'].values

print(f"\n✅ Features (X) : {X.shape}")
print(f"✅ Target (y) : {y.shape}")

print("\n" + "=" * 80)
print("VALIDATION CROISÉE LEAVE-ONE-OUT (LOO)")
print("=" * 80)

# Modèle de régression linéaire
model = LinearRegression()

# Leave-One-Out Cross-Validation
loo = LeaveOneOut()
y_pred_loo = np.zeros(len(y))

for train_idx, test_idx in loo.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    model.fit(X_train, y_train)
    y_pred_loo[test_idx] = model.predict(X_test)

# Métriques LOO
r2_loo = r2_score(y, y_pred_loo)
mae_loo = mean_absolute_error(y, y_pred_loo)
rmse_loo = np.sqrt(mean_squared_error(y, y_pred_loo))

print(f"\n🎯 RÉSULTATS LOO ({len(y)} folds) :")
print(f"   R²   = {r2_loo:.3f}")
print(f"   MAE  = {mae_loo:.1f} pips")
print(f"   RMSE = {rmse_loo:.1f} pips")

# Comparaison avec V3 Session 75
print("\n" + "=" * 80)
print("COMPARAISON V3 TRAINING vs LOO")
print("=" * 80)

print(f"\n📊 V3 Session 75 (training sur 16 points) :")
print(f"   R²   = 0.994")
print(f"   MAE  = 1.1 pips")

print(f"\n📊 V3 Session 76 (LOO sur {len(y)} points) :")
print(f"   R²   = {r2_loo:.3f}")
print(f"   MAE  = {mae_loo:.1f} pips")

delta_r2 = 0.994 - r2_loo
delta_mae = mae_loo - 1.1

print(f"\n📈 ÉCART :")
print(f"   ΔR²  = {delta_r2:+.3f} ({abs(delta_r2/0.994)*100:.1f}% dégradation)")
print(f"   ΔMAE = {delta_mae:+.1f} pips ({abs(delta_mae/1.1)*100:.1f}% dégradation)")

# Analyse overfitting
print("\n" + "=" * 80)
print("ANALYSE OVERFITTING")
print("=" * 80)

if delta_r2 > 0.3:
    status = "🔴 OVERFITTING FORT"
    severity = "CRITIQUE"
elif delta_r2 > 0.15:
    status = "🟠 OVERFITTING MODÉRÉ"
    severity = "SIGNIFICATIF"
else:
    status = "🟢 OVERFITTING FAIBLE"
    severity = "ACCEPTABLE"

print(f"\n{status}")
print(f"Sévérité : {severity}")
print(f"Écart R² : {delta_r2:+.3f}")

# Décision
print("\n" + "=" * 80)
print("💡 DÉCISION FINALE")
print("=" * 80)

if r2_loo > 0.75:
    decision = "✅ V3 VALIDÉ"
    version = "formulas_validated_v2.2.py"
    desc = "Modèle V3 (12 features) généralise bien"
elif r2_loo < 0.60:
    decision = "⚠️ OVERFITTING DÉTECTÉ"
    version = "formulas_validated_v2.1.py"
    desc = "Utiliser V1 (8 features, R²=0.705, MAE=7.7 pips)"
else:
    decision = "⚡ ZONE GRISE - ANALYSE APPROFONDIE"
    version = "Décision manuelle requise"
    desc = f"R²={r2_loo:.3f}, MAE={mae_loo:.1f} pips - entre seuils"

print(f"\n{decision}")
print(f"Version à créer : {version}")
print(f"Description : {desc}")

# Top/Bottom prédictions
print("\n" + "=" * 80)
print("📋 DÉTAILS PRÉDICTIONS")
print("=" * 80)

results_df = pd.DataFrame({
    'Date': df_grouped['date'].values,
    'Réel': y,
    'Prédit': y_pred_loo,
    'Erreur': np.abs(y - y_pred_loo)
}).sort_values('Erreur')

print("\n🎯 TOP 5 MEILLEURES PRÉDICTIONS :")
print(results_df.head(5).to_string(index=False))

print("\n⚠️ TOP 5 PIRES PRÉDICTIONS :")
print(results_df.tail(5).to_string(index=False))

# Distribution erreurs
print("\n📊 DISTRIBUTION DES ERREURS :")
errors = np.abs(y - y_pred_loo)
print(f"   Min    : {np.min(errors):.1f} pips")
print(f"   Q1     : {np.percentile(errors, 25):.1f} pips")
print(f"   Médiane: {np.median(errors):.1f} pips")
print(f"   Q3     : {np.percentile(errors, 75):.1f} pips")
print(f"   Max    : {np.max(errors):.1f} pips")

# Sauvegarder résultats
summary = f"""
VALIDATION CROISÉE V3 - SESSION 76 (LOO)
========================================

CONFIGURATION
-------------
Dataset : dataset_complete_session75_v3.csv
Méthode : Leave-One-Out Cross-Validation (LOO)
Modèle : Régression Linéaire
Points : {len(y)}
Features : 12

RÉSULTATS LOO
-------------
R²   = {r2_loo:.3f}
MAE  = {mae_loo:.1f} pips
RMSE = {rmse_loo:.1f} pips

COMPARAISON V3 TRAINING
-----------------------
V3 Training (S75) : R²=0.994, MAE=1.1 pips
V3 LOO (S76)      : R²={r2_loo:.3f}, MAE={mae_loo:.1f} pips
Écart             : ΔR²={delta_r2:+.3f}, ΔMAE={delta_mae:+.1f} pips

OVERFITTING
-----------
Statut : {status}
Sévérité : {severity}

DÉCISION
--------
{decision}
Version : {version}
{desc}

DISTRIBUTION ERREURS
--------------------
Min    : {np.min(errors):.1f} pips
Q1     : {np.percentile(errors, 25):.1f} pips
Médiane: {np.median(errors):.1f} pips
Q3     : {np.percentile(errors, 75):.1f} pips
Max    : {np.max(errors):.1f} pips
"""

with open('../data/validation_loo_session76.txt', 'w', encoding='utf-8') as f:
    f.write(summary)

print("\n" + "=" * 80)
print("✅ Résultats sauvegardés : validation_loo_session76.txt")
print("=" * 80)
