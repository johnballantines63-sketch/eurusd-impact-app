#!/usr/bin/env python3
"""
SESSION 128 - VALIDATION SPLIT TRAIN/TEST CPI
==============================================

ÉTAPE 5B Pipeline : Valider que calibration n'est pas en overfitting.

Process :
1. Charger 29 clusters CPI
2. Split 80/20 (train/test)
3. Recalibrer fonction sur train uniquement
4. Tester sur test set (données CPI non vues)
5. Comparer performances train vs test

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 128 Phase 5B
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.optimize import curve_fit

print("="*80)
print("VALIDATION SPLIT TRAIN/TEST CPI")
print("="*80)
print()

# ============================================================================
# ÉTAPE 1 : CHARGER DONNÉES CALIBRATION COMPLÈTE
# ============================================================================

print("ÉTAPE 1 : CHARGEMENT DONNÉES")
print("-"*80)
print()

CALIBRATION_DIR = Path(__file__).parent / "calibration_results_adapted"
data_file = CALIBRATION_DIR / "calibration_data.csv"

if not data_file.exists():
    print(f"❌ Fichier non trouvé : {data_file}")
    sys.exit(1)

df_calib = pd.read_csv(data_file)

print(f"✅ {len(df_calib)} clusters CPI chargés")
print()

# ============================================================================
# ÉTAPE 2 : SPLIT TRAIN/TEST 80/20
# ============================================================================

print("="*80)
print("ÉTAPE 2 : SPLIT TRAIN/TEST")
print("="*80)
print()

# Split random 80/20
train_df, test_df = train_test_split(
    df_calib, 
    test_size=0.2, 
    random_state=42
)

print(f"📊 Split effectué :")
print(f"   Train : {len(train_df)} clusters (80%)")
print(f"   Test  : {len(test_df)} clusters (20%)")
print()

print("Dates test set :")
for idx, row in test_df.iterrows():
    date = pd.to_datetime(row['cluster_time']).date()
    print(f"   {date} | R²={row['trend_r2']:.4f} | Impact={row['impact_measured']:.1f} pips")
print()

# ============================================================================
# ÉTAPE 3 : RECALIBRATION SUR TRAIN UNIQUEMENT
# ============================================================================

print("="*80)
print("ÉTAPE 3 : CALIBRATION SUR TRAIN")
print("="*80)
print()

X_train = train_df['trend_r2'].values
y_train = train_df['amplification_ideal'].values

X_test = test_df['trend_r2'].values
y_test = test_df['amplification_ideal'].values

print(f"📊 Données train :")
print(f"   N = {len(X_train)}")
print(f"   R² min = {X_train.min():.4f}, max = {X_train.max():.4f}")
print(f"   Amp min = {y_train.min():.4f}, max = {y_train.max():.4f}")
print()

# Modèle quadratique
def quadratic_model(r2, a, b, c):
    return a + b * r2 + c * r2**2

try:
    popt_quad, _ = curve_fit(quadratic_model, X_train, y_train)
    
    a, b, c = popt_quad
    
    print(f"✅ Modèle quadratique calibré (train) :")
    print(f"   amp = {a:.6f} + {b:.6f}×R² + {c:.6f}×R²²")
    print()
    
    # Prédictions train
    y_pred_train = quadratic_model(X_train, *popt_quad)
    mae_train = mean_absolute_error(y_train, y_pred_train)
    r2_train = r2_score(y_train, y_pred_train)
    
    print(f"   Performance train :")
    print(f"   MAE  = {mae_train:.6f}")
    print(f"   R² fit = {r2_train:.4f}")
    print()
    
except Exception as e:
    print(f"❌ Calibration échouée : {e}")
    sys.exit(1)

# ============================================================================
# ÉTAPE 4 : VALIDATION SUR TEST
# ============================================================================

print("="*80)
print("ÉTAPE 4 : VALIDATION SUR TEST")
print("="*80)
print()

# Prédictions test
y_pred_test = quadratic_model(X_test, *popt_quad)
mae_test = mean_absolute_error(y_test, y_pred_test)
r2_test = r2_score(y_test, y_pred_test)

print(f"📊 Performance test :")
print(f"   MAE  = {mae_test:.6f}")
print(f"   R² fit = {r2_test:.4f}")
print()

# Comparaison
ratio_mae = mae_test / mae_train if mae_train > 0 else float('inf')

print("="*80)
print("COMPARAISON TRAIN VS TEST")
print("="*80)
print()

print(f"   MAE Train : {mae_train:.6f}")
print(f"   MAE Test  : {mae_test:.6f}")
print(f"   Ratio     : {ratio_mae:.2f}×")
print()

print(f"   R² Train  : {r2_train:.4f}")
print(f"   R² Test   : {r2_test:.4f}")
print()

# ============================================================================
# ÉTAPE 5 : PRÉDICTIONS IMPACT (TRAIN VS TEST)
# ============================================================================

print("="*80)
print("ÉTAPE 5 : PRÉDICTIONS IMPACT")
print("="*80)
print()

# Recalculer impacts avec amplifications prédites
def calculate_impact_predictions(df, popt):
    predictions = []
    
    for idx, row in df.iterrows():
        r2 = row['trend_r2']
        amp_pred = quadratic_model(r2, *popt)
        
        total_score = row['total_score']
        n_events = row['n_events']
        
        impact_pred = total_score * amp_pred * np.sqrt(n_events)
        impact_real = row['impact_measured']
        
        predictions.append({
            'date': row['cluster_time'],
            'r2': r2,
            'impact_real': impact_real,
            'impact_pred': impact_pred,
            'error': abs(impact_pred - impact_real)
        })
    
    return pd.DataFrame(predictions)

df_pred_train = calculate_impact_predictions(train_df, popt_quad)
df_pred_test = calculate_impact_predictions(test_df, popt_quad)

mae_impact_train = df_pred_train['error'].mean()
mae_impact_test = df_pred_test['error'].mean()

print(f"📊 MAE Impact (pips) :")
print(f"   Train : {mae_impact_train:.2f} pips")
print(f"   Test  : {mae_impact_test:.2f} pips")
print(f"   Ratio : {mae_impact_test/mae_impact_train:.2f}×")
print()

# ============================================================================
# ÉTAPE 6 : DÉCISION
# ============================================================================

print("="*80)
print("DÉCISION OVERFITTING")
print("="*80)
print()

# Critères :
# - Ratio MAE < 2.0 → Pas d'overfitting
# - Ratio MAE 2.0-3.0 → Overfitting léger
# - Ratio MAE > 3.0 → Overfitting sévère

if ratio_mae < 2.0:
    decision = "✅ PAS D'OVERFITTING"
    comment = "Modèle se généralise bien aux données non vues"
    next_steps = [
        "Fonction validée sur données CPI out-of-sample",
        "Combiné avec validation croisée NFP (+98.6%)",
        "Prêt pour intégration production"
    ]
elif ratio_mae < 3.0:
    decision = "⚠️ OVERFITTING LÉGER"
    comment = "Performance test légèrement dégradée"
    next_steps = [
        "Acceptable pour usage production",
        "Monitorer performance en production",
        "Envisager régularisation si dégradation"
    ]
else:
    decision = "❌ OVERFITTING SÉVÈRE"
    comment = "Modèle ne se généralise pas"
    next_steps = [
        "Réduire complexité modèle (linéaire au lieu quadratique)",
        "Augmenter taille échantillon (>50 clusters)",
        "Utiliser régularisation (ridge, lasso)"
    ]

print(f"🎯 DÉCISION : {decision}")
print()
print(f"   {comment}")
print()
print("   Prochaines étapes :")
for step in next_steps:
    print(f"   • {step}")
print()

# Détails test set
print("="*80)
print("DÉTAILS TEST SET")
print("="*80)
print()

print(df_pred_test[['date', 'impact_real', 'impact_pred', 'error']].to_string(index=False))
print()

# Sauvegarder
OUTPUT_DIR = Path(__file__).parent / "validation_split_train_test"
OUTPUT_DIR.mkdir(exist_ok=True)

results = {
    'n_train': len(train_df),
    'n_test': len(test_df),
    'split_ratio': 0.8,
    'model': {
        'type': 'quadratic',
        'formula': f"amp = {a:.6f} + {b:.6f}×R² + {c:.6f}×R²²",
        'parameters': [float(a), float(b), float(c)]
    },
    'metrics': {
        'mae_amplification_train': float(mae_train),
        'mae_amplification_test': float(mae_test),
        'r2_train': float(r2_train),
        'r2_test': float(r2_test),
        'ratio_mae': float(ratio_mae),
        'mae_impact_train_pips': float(mae_impact_train),
        'mae_impact_test_pips': float(mae_impact_test)
    },
    'decision': decision,
    'comment': comment,
    'next_steps': next_steps,
    'test_predictions': df_pred_test.to_dict('records')
}

with open(OUTPUT_DIR / "split_validation_results.json", 'w') as f:
    json.dump(results, f, indent=2, default=str)

df_pred_train.to_csv(OUTPUT_DIR / "predictions_train.csv", index=False)
df_pred_test.to_csv(OUTPUT_DIR / "predictions_test.csv", index=False)

print(f"💾 Résultats sauvegardés : {OUTPUT_DIR.name}/")
print()

print("="*80)
print("✅ VALIDATION SPLIT TERMINÉE")
print("="*80)
print()

sys.exit(0 if ratio_mae < 3.0 else 1)
