"""
SCRIPT 2 - RÉGRESSION ML MULTI-VARIABLES (SESSION 76)
======================================================

OBJECTIF : Créer modèle ML robuste avec validation croisée

VARIABLES PRÉDICTEURS :
- score_ajuste : Score empirique ajusté par surprise
- nb_events : Nombre événements dans cluster
- surprise_max : Surprise maximum (%)
- coherence_famille : Ratio famille dominante

TARGET :
- impact_reel_pips : Impact observé (valeur absolue)

MÉTRIQUES SUCCÈS :
- R² > 0.7 (bon) ou > 0.8 (excellent)
- MAE cross-val < 20 pips
- Stabilité std < 5 pips

Date : 25 octobre 2025
Session : 76
"""

import sys
import os
from pathlib import Path

fx_app_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(fx_app_path))

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')


# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent
INPUT_PATH = SCRIPT_DIR / "dataset_session76_extended.csv"
OUTPUT_RESULTS = SCRIPT_DIR / "regression_results_session76.txt"
OUTPUT_MODEL_PARAMS = SCRIPT_DIR / "model_parameters_session76.txt"


# ════════════════════════════════════════════════════════════════
# FONCTIONS PRÉPARATION DONNÉES
# ════════════════════════════════════════════════════════════════

def calculate_adjusted_score(row):
    """
    Calcule score ajusté selon surprise
    
    Formule Session 55 validée :
    - surprise < 5% : facteur = 1.0
    - 5% ≤ surprise < 15% : facteur = 1.0 → 1.5 (linéaire)
    - 15% ≤ surprise < 30% : facteur = 1.5 → 1.9 (linéaire)
    - surprise ≥ 30% : facteur = 1.9 (plafond)
    """
    score_base = row['score_moyen']
    surprise = row['surprise_max']
    
    if surprise < 5:
        facteur = 1.0
    elif surprise < 15:
        facteur = 1.0 + (surprise - 5) / 10 * 0.5
    elif surprise < 30:
        facteur = 1.5 + (surprise - 15) / 15 * 0.4
    else:
        facteur = 1.9
    
    return score_base * facteur


def prepare_dataset(df):
    """
    Prépare dataset pour régression ML
    
    Returns:
        X : Features (4 colonnes)
        y : Target (impact_reel_pips)
    """
    print(f"\n{'='*70}")
    print("PRÉPARATION DATASET")
    print(f"{'='*70}")
    
    # Calculer score ajusté
    df['score_ajuste'] = df.apply(calculate_adjusted_score, axis=1)
    
    # Variables prédicteurs
    feature_cols = ['score_ajuste', 'nb_events', 'surprise_max', 'coherence_famille']
    
    # Target
    target_col = 'impact_pips'
    
    # Extraction
    X = df[feature_cols].copy()
    y = df[target_col].copy().abs()  # Valeur absolue
    
    print(f"✅ Dataset préparé :")
    print(f"   Observations : {len(df)}")
    print(f"   Features : {len(feature_cols)}")
    print(f"   Target : {target_col} (valeur absolue)")
    
    print(f"\n📊 Statistiques features :")
    print(X.describe())
    
    print(f"\n📊 Statistiques target :")
    print(y.describe())
    
    # Vérifier NaN
    nan_counts = X.isna().sum()
    if nan_counts.sum() > 0:
        print(f"\n⚠️  NaN détectés :")
        print(nan_counts[nan_counts > 0])
        print(f"   Remplacement par médiane...")
        X = X.fillna(X.median())
    
    return X, y


# ════════════════════════════════════════════════════════════════
# FONCTIONS RÉGRESSION ML
# ════════════════════════════════════════════════════════════════

def train_linear_regression(X, y):
    """
    Entraîne régression linéaire multi-variables
    
    Returns:
        model : Modèle entraîné
        metrics : Dictionnaire métriques
    """
    print(f"\n{'='*70}")
    print("RÉGRESSION LINÉAIRE MULTI-VARIABLES")
    print(f"{'='*70}")
    
    # Créer modèle
    model = LinearRegression()
    
    # Entraîner
    print("Entraînement modèle...")
    model.fit(X, y)
    
    # Prédictions
    y_pred = model.predict(X)
    
    # Métriques training set
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    
    print(f"\n📊 MÉTRIQUES TRAINING SET :")
    print(f"   R² : {r2:.3f}")
    print(f"   MAE : {mae:.1f} pips")
    print(f"   RMSE : {rmse:.1f} pips")
    
    # Coefficients
    print(f"\n📊 COEFFICIENTS RÉGRESSION :")
    print(f"   Intercept : {model.intercept_:.2f}")
    
    for i, col in enumerate(X.columns):
        print(f"   {col:20s} : {model.coef_[i]:8.4f}")
    
    metrics = {
        'r2_train': r2,
        'mae_train': mae,
        'rmse_train': rmse
    }
    
    return model, metrics


def cross_validate_model(model, X, y, n_folds=5):
    """
    Validation croisée K-Fold
    
    Returns:
        cv_metrics : Dictionnaire métriques validation croisée
    """
    print(f"\n{'='*70}")
    print(f"VALIDATION CROISÉE ({n_folds}-FOLD)")
    print(f"{'='*70}")
    
    # KFold
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    # Cross-validation scores
    print(f"Calcul scores validation croisée...")
    
    # R²
    scores_r2 = cross_val_score(model, X, y, cv=kf, scoring='r2')
    
    # MAE (négatif → positif)
    scores_mae = -cross_val_score(model, X, y, cv=kf, scoring='neg_mean_absolute_error')
    
    # RMSE (négatif → positif)
    scores_rmse = np.sqrt(-cross_val_score(model, X, y, cv=kf, scoring='neg_mean_squared_error'))
    
    print(f"\n📊 MÉTRIQUES VALIDATION CROISÉE ({n_folds}-FOLD) :")
    
    print(f"\n   R² :")
    print(f"      Moyenne : {scores_r2.mean():.3f}")
    print(f"      Std     : {scores_r2.std():.3f}")
    print(f"      Min     : {scores_r2.min():.3f}")
    print(f"      Max     : {scores_r2.max():.3f}")
    
    print(f"\n   MAE (pips) :")
    print(f"      Moyenne : {scores_mae.mean():.1f}")
    print(f"      Std     : {scores_mae.std():.1f}")
    print(f"      Min     : {scores_mae.min():.1f}")
    print(f"      Max     : {scores_mae.max():.1f}")
    
    print(f"\n   RMSE (pips) :")
    print(f"      Moyenne : {scores_rmse.mean():.1f}")
    print(f"      Std     : {scores_rmse.std():.1f}")
    print(f"      Min     : {scores_rmse.min():.1f}")
    print(f"      Max     : {scores_rmse.max():.1f}")
    
    # Vérifier critères succès
    print(f"\n{'='*70}")
    print("VÉRIFICATION CRITÈRES SUCCÈS")
    print(f"{'='*70}")
    
    r2_mean = scores_r2.mean()
    mae_mean = scores_mae.mean()
    mae_std = scores_mae.std()
    
    print(f"\n1. R² > 0.7 (bon) ou > 0.8 (excellent)")
    if r2_mean > 0.8:
        print(f"   ✅ EXCELLENT : R² = {r2_mean:.3f} (> 0.8)")
    elif r2_mean > 0.7:
        print(f"   ✅ BON : R² = {r2_mean:.3f} (> 0.7)")
    else:
        print(f"   ❌ INSUFFISANT : R² = {r2_mean:.3f} (< 0.7)")
    
    print(f"\n2. MAE cross-val < 20 pips")
    if mae_mean < 20:
        print(f"   ✅ EXCELLENT : MAE = {mae_mean:.1f} pips (< 20)")
    else:
        print(f"   ❌ INSUFFISANT : MAE = {mae_mean:.1f} pips (≥ 20)")
    
    print(f"\n3. Stabilité std < 5 pips")
    if mae_std < 5:
        print(f"   ✅ STABLE : std = {mae_std:.1f} pips (< 5)")
    else:
        print(f"   ⚠️  VARIABLE : std = {mae_std:.1f} pips (≥ 5)")
    
    cv_metrics = {
        'r2_cv_mean': r2_mean,
        'r2_cv_std': scores_r2.std(),
        'mae_cv_mean': mae_mean,
        'mae_cv_std': mae_std,
        'rmse_cv_mean': scores_rmse.mean(),
        'rmse_cv_std': scores_rmse.std()
    }
    
    return cv_metrics


def save_results(model, X, metrics_train, metrics_cv):
    """
    Sauvegarde résultats régression
    """
    print(f"\n{'='*70}")
    print("EXPORT RÉSULTATS")
    print(f"{'='*70}")
    
    # Résultats texte
    with open(OUTPUT_RESULTS, 'w') as f:
        f.write("="*70 + "\n")
        f.write("RÉGRESSION ML MULTI-VARIABLES - SESSION 76\n")
        f.write("="*70 + "\n\n")
        
        f.write("MÉTRIQUES TRAINING SET :\n")
        f.write(f"   R² : {metrics_train['r2_train']:.3f}\n")
        f.write(f"   MAE : {metrics_train['mae_train']:.1f} pips\n")
        f.write(f"   RMSE : {metrics_train['rmse_train']:.1f} pips\n\n")
        
        f.write("MÉTRIQUES VALIDATION CROISÉE (5-FOLD) :\n")
        f.write(f"   R² : {metrics_cv['r2_cv_mean']:.3f} ± {metrics_cv['r2_cv_std']:.3f}\n")
        f.write(f"   MAE : {metrics_cv['mae_cv_mean']:.1f} ± {metrics_cv['mae_cv_std']:.1f} pips\n")
        f.write(f"   RMSE : {metrics_cv['rmse_cv_mean']:.1f} ± {metrics_cv['rmse_cv_std']:.1f} pips\n\n")
        
        f.write("COEFFICIENTS :\n")
        f.write(f"   Intercept : {model.intercept_:.2f}\n")
        for i, col in enumerate(X.columns):
            f.write(f"   {col:20s} : {model.coef_[i]:8.4f}\n")
    
    print(f"✅ Résultats sauvegardés : {OUTPUT_RESULTS}")
    
    # Paramètres modèle pour formulas_validated_v2.py
    with open(OUTPUT_MODEL_PARAMS, 'w') as f:
        f.write("# PARAMÈTRES MODÈLE ML V2.0 - SESSION 76\n")
        f.write("# Utilisés dans formulas_validated_v2.py\n\n")
        f.write(f"INTERCEPT = {model.intercept_:.4f}\n")
        f.write(f"COEF_SCORE_AJUSTE = {model.coef_[0]:.4f}\n")
        f.write(f"COEF_NB_EVENTS = {model.coef_[1]:.4f}\n")
        f.write(f"COEF_SURPRISE_MAX = {model.coef_[2]:.4f}\n")
        f.write(f"COEF_COHERENCE_FAMILLE = {model.coef_[3]:.4f}\n\n")
        f.write(f"# Métriques validation\n")
        f.write(f"R2_CV = {metrics_cv['r2_cv_mean']:.3f}\n")
        f.write(f"MAE_CV = {metrics_cv['mae_cv_mean']:.1f}\n")
    
    print(f"✅ Paramètres modèle sauvegardés : {OUTPUT_MODEL_PARAMS}")


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    """Point d'entrée principal"""
    print(f"\n{'='*70}")
    print("RÉGRESSION ML MULTI-VARIABLES - SESSION 76")
    print(f"{'='*70}")
    
    if not INPUT_PATH.exists():
        print(f"❌ Dataset non trouvé : {INPUT_PATH}")
        print(f"   Exécuter d'abord 1_scanner_movements_V3_EXTENDED.py")
        return 1
    
    print(f"✅ Dataset : {INPUT_PATH}")
    
    # Charger dataset
    print(f"\nChargement dataset...")
    df = pd.read_csv(INPUT_PATH)
    print(f"✅ {len(df)} mouvements chargés")
    
    # Vérifier taille minimum
    if len(df) < 20:
        print(f"\n⚠️  ATTENTION : Dataset petit ({len(df)} observations)")
        print(f"   Recommandé : ≥ 30 observations pour ML robuste")
        print(f"   Risque overfitting élevé")
    
    # Préparer données
    X, y = prepare_dataset(df)
    
    # Régression
    model, metrics_train = train_linear_regression(X, y)
    
    # Validation croisée
    metrics_cv = cross_validate_model(model, X, y, n_folds=5)
    
    # Sauvegarder résultats
    save_results(model, X, metrics_train, metrics_cv)
    
    print(f"\n{'='*70}")
    print("RÉGRESSION ML TERMINÉE AVEC SUCCÈS")
    print(f"{'='*70}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
