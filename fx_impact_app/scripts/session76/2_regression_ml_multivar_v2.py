"""
SCRIPT 2B - RÉGRESSION ML OPTIMISÉE (SESSION 76 - TENTATIVE 2)
================================================================

CORRECTIONS vs Tentative 1 :
- Dataset V3.1 Ultra (27 obs) au lieu de V3 (20 obs)
- Test 3 configurations : 4, 3, 2 features
- Leave-One-Out CV (plus stable que 5-fold avec 27 obs)
- Analyse détaillée overfitting

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
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')


# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent
INPUT_PATH = SCRIPT_DIR / "dataset_session76_ultra.csv"  # ✅ CORRECTION
OUTPUT_RESULTS = SCRIPT_DIR / "regression_results_session76_v2.txt"
OUTPUT_MODEL_PARAMS = SCRIPT_DIR / "model_parameters_session76_v2.txt"
OUTPUT_COMPARISON = SCRIPT_DIR / "model_comparison_session76.txt"


# ════════════════════════════════════════════════════════════════
# FONCTIONS PRÉPARATION
# ════════════════════════════════════════════════════════════════

def calculate_adjusted_score(row):
    """Calcule score ajusté selon surprise (Formule Session 55)"""
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


def prepare_datasets(df):
    """
    Prépare 3 configurations de features
    
    Returns:
        dict: {
            '4_features': (X, y, feature_names),
            '3_features': (X, y, feature_names),
            '2_features': (X, y, feature_names)
        }
    """
    print(f"\n{'='*70}")
    print("PRÉPARATION DATASETS - 3 CONFIGURATIONS")
    print(f"{'='*70}")
    
    # Calculer score ajusté
    df['score_ajuste'] = df.apply(calculate_adjusted_score, axis=1)
    
    # Target
    y = df['impact_pips'].copy().abs()
    
    # Configuration 1 : 4 features (COMPLET)
    features_4 = ['score_ajuste', 'nb_events', 'surprise_max', 'coherence_famille']
    X_4 = df[features_4].copy()
    
    # Configuration 2 : 3 features (SANS coherence_famille)
    features_3 = ['score_ajuste', 'nb_events', 'surprise_max']
    X_3 = df[features_3].copy()
    
    # Configuration 3 : 2 features (MINIMAL)
    features_2 = ['score_ajuste', 'surprise_max']
    X_2 = df[features_2].copy()
    
    # Gestion NaN
    for X, name in [(X_4, '4 features'), (X_3, '3 features'), (X_2, '2 features')]:
        nan_counts = X.isna().sum()
        if nan_counts.sum() > 0:
            print(f"\n⚠️  NaN détectés dans {name} :")
            print(nan_counts[nan_counts > 0])
            X.fillna(X.median(), inplace=True)
    
    print(f"\n✅ 3 configurations préparées :")
    print(f"   Observations : {len(df)}")
    print(f"   Config 1 : 4 features (score_ajuste, nb_events, surprise_max, coherence_famille)")
    print(f"   Config 2 : 3 features (score_ajuste, nb_events, surprise_max)")
    print(f"   Config 3 : 2 features (score_ajuste, surprise_max)")
    
    return {
        '4_features': (X_4, y, features_4),
        '3_features': (X_3, y, features_3),
        '2_features': (X_2, y, features_2)
    }


# ════════════════════════════════════════════════════════════════
# FONCTIONS ML
# ════════════════════════════════════════════════════════════════

def train_and_validate_model(X, y, feature_names, config_name):
    """
    Entraîne et valide modèle avec Leave-One-Out CV
    
    Returns:
        dict: Métriques complètes
    """
    print(f"\n{'='*70}")
    print(f"CONFIGURATION : {config_name}")
    print(f"{'='*70}")
    
    print(f"\nFeatures : {', '.join(feature_names)}")
    print(f"Observations : {len(X)}")
    print(f"Ratio obs/features : {len(X)/len(feature_names):.1f}:1")
    
    # Créer modèle
    model = LinearRegression()
    
    # Training
    print(f"\nEntraînement modèle...")
    model.fit(X, y)
    
    y_pred_train = model.predict(X)
    
    # Métriques training
    r2_train = r2_score(y, y_pred_train)
    mae_train = mean_absolute_error(y, y_pred_train)
    rmse_train = np.sqrt(mean_squared_error(y, y_pred_train))
    
    print(f"\n📊 MÉTRIQUES TRAINING :")
    print(f"   R² : {r2_train:.3f}")
    print(f"   MAE : {mae_train:.1f} pips")
    print(f"   RMSE : {rmse_train:.1f} pips")
    
    # Coefficients
    print(f"\n📊 COEFFICIENTS :")
    print(f"   Intercept : {model.intercept_:.2f}")
    for i, name in enumerate(feature_names):
        print(f"   {name:20s} : {model.coef_[i]:8.4f}")
    
    # Leave-One-Out CV (plus stable que K-Fold avec 27 obs)
    print(f"\n📊 VALIDATION LEAVE-ONE-OUT :")
    
    loo = LeaveOneOut()
    
    scores_r2 = cross_val_score(model, X, y, cv=loo, scoring='r2')
    scores_mae = -cross_val_score(model, X, y, cv=loo, scoring='neg_mean_absolute_error')
    scores_rmse = np.sqrt(-cross_val_score(model, X, y, cv=loo, scoring='neg_mean_squared_error'))
    
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
    
    # Analyse overfitting
    print(f"\n📊 ANALYSE OVERFITTING :")
    r2_gap = r2_train - scores_r2.mean()
    mae_gap = scores_mae.mean() - mae_train
    
    print(f"   R² gap (train - CV) : {r2_gap:+.3f}")
    if r2_gap > 0.3:
        print(f"      ⚠️  OVERFITTING SÉVÈRE (gap > 0.3)")
    elif r2_gap > 0.15:
        print(f"      ⚠️  Overfitting modéré (gap > 0.15)")
    else:
        print(f"      ✅ Overfitting acceptable")
    
    print(f"\n   MAE gap (CV - train) : {mae_gap:+.1f} pips")
    if mae_gap > 10:
        print(f"      ⚠️  OVERFITTING SÉVÈRE (gap > 10 pips)")
    elif mae_gap > 5:
        print(f"      ⚠️  Overfitting modéré (gap > 5 pips)")
    else:
        print(f"      ✅ Overfitting acceptable")
    
    # Critères succès
    print(f"\n{'='*70}")
    print("VÉRIFICATION CRITÈRES SUCCÈS")
    print(f"{'='*70}")
    
    success_count = 0
    
    print(f"\n1. R² > 0.5 (acceptable) ou > 0.7 (bon)")
    if scores_r2.mean() > 0.7:
        print(f"   ✅ BON : R² = {scores_r2.mean():.3f}")
        success_count += 1
    elif scores_r2.mean() > 0.5:
        print(f"   ⚠️  ACCEPTABLE : R² = {scores_r2.mean():.3f}")
    else:
        print(f"   ❌ INSUFFISANT : R² = {scores_r2.mean():.3f}")
    
    print(f"\n2. MAE < 25 pips (acceptable) ou < 20 pips (bon)")
    if scores_mae.mean() < 20:
        print(f"   ✅ BON : MAE = {scores_mae.mean():.1f} pips")
        success_count += 1
    elif scores_mae.mean() < 25:
        print(f"   ⚠️  ACCEPTABLE : MAE = {scores_mae.mean():.1f} pips")
    else:
        print(f"   ❌ INSUFFISANT : MAE = {scores_mae.mean():.1f} pips")
    
    print(f"\n3. Stabilité std < 8 pips (acceptable) ou < 5 pips (bon)")
    if scores_mae.std() < 5:
        print(f"   ✅ BON : std = {scores_mae.std():.1f} pips")
        success_count += 1
    elif scores_mae.std() < 8:
        print(f"   ⚠️  ACCEPTABLE : std = {scores_mae.std():.1f} pips")
    else:
        print(f"   ❌ INSTABLE : std = {scores_mae.std():.1f} pips")
    
    print(f"\n4. Overfitting modéré (R² gap < 0.3, MAE gap < 10 pips)")
    if r2_gap < 0.3 and mae_gap < 10:
        print(f"   ✅ ACCEPTABLE")
        success_count += 1
    else:
        print(f"   ❌ OVERFITTING SÉVÈRE")
    
    print(f"\n📊 SCORE GLOBAL : {success_count}/4 critères")
    
    return {
        'config_name': config_name,
        'n_features': len(feature_names),
        'feature_names': feature_names,
        'model': model,
        'r2_train': r2_train,
        'mae_train': mae_train,
        'rmse_train': rmse_train,
        'r2_cv_mean': scores_r2.mean(),
        'r2_cv_std': scores_r2.std(),
        'mae_cv_mean': scores_mae.mean(),
        'mae_cv_std': scores_mae.std(),
        'rmse_cv_mean': scores_rmse.mean(),
        'rmse_cv_std': scores_rmse.std(),
        'r2_gap': r2_gap,
        'mae_gap': mae_gap,
        'success_count': success_count
    }


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    """Point d'entrée principal"""
    print(f"\n{'='*70}")
    print("RÉGRESSION ML OPTIMISÉE - SESSION 76 TENTATIVE 2")
    print(f"{'='*70}")
    print(f"\nCORRECTIONS vs Tentative 1 :")
    print(f"   ✅ Dataset V3.1 Ultra (27 obs) au lieu de V3 (20 obs)")
    print(f"   ✅ Test 3 configurations (4, 3, 2 features)")
    print(f"   ✅ Leave-One-Out CV (plus stable)")
    print(f"   ✅ Analyse overfitting détaillée")
    print()
    
    if not INPUT_PATH.exists():
        print(f"❌ Dataset non trouvé : {INPUT_PATH}")
        print(f"   Vérifier que scanner V3.1 Ultra a été exécuté")
        return 1
    
    print(f"✅ Dataset : {INPUT_PATH}")
    
    # Charger dataset
    print(f"\nChargement dataset V3.1 Ultra...")
    df = pd.read_csv(INPUT_PATH)
    print(f"✅ {len(df)} mouvements chargés")
    
    # Préparer 3 configurations
    datasets = prepare_datasets(df)
    
    # Tester chaque configuration
    results = {}
    
    for config_key in ['4_features', '3_features', '2_features']:
        X, y, feature_names = datasets[config_key]
        metrics = train_and_validate_model(X, y, feature_names, config_key)
        results[config_key] = metrics
    
    # Comparaison finale
    print(f"\n{'='*70}")
    print("COMPARAISON FINALE - 3 CONFIGURATIONS")
    print(f"{'='*70}")
    
    print(f"\n{'Config':<15} {'R² CV':<10} {'MAE CV':<12} {'Std':<10} {'Score':>8}")
    print(f"{'-'*60}")
    
    for config_key in ['4_features', '3_features', '2_features']:
        m = results[config_key]
        print(f"{m['config_name']:<15} {m['r2_cv_mean']:>6.3f}    {m['mae_cv_mean']:>6.1f} pips   {m['mae_cv_std']:>6.1f}    {m['success_count']}/4")
    
    # Sélectionner meilleur modèle
    best_config = max(results.values(), key=lambda x: x['success_count'])
    
    print(f"\n{'='*70}")
    print(f"MEILLEUR MODÈLE : {best_config['config_name']}")
    print(f"{'='*70}")
    print(f"\n   Score global : {best_config['success_count']}/4 critères")
    print(f"   R² CV : {best_config['r2_cv_mean']:.3f}")
    print(f"   MAE CV : {best_config['mae_cv_mean']:.1f} pips")
    
    # Sauvegarder résultats
    with open(OUTPUT_COMPARISON, 'w') as f:
        f.write("="*70 + "\n")
        f.write("COMPARAISON MODÈLES ML - SESSION 76\n")
        f.write("="*70 + "\n\n")
        
        for config_key in ['4_features', '3_features', '2_features']:
            m = results[config_key]
            f.write(f"\n{m['config_name'].upper()}\n")
            f.write("-"*70 + "\n")
            f.write(f"Features : {', '.join(m['feature_names'])}\n")
            f.write(f"R² train : {m['r2_train']:.3f}\n")
            f.write(f"R² CV : {m['r2_cv_mean']:.3f} ± {m['r2_cv_std']:.3f}\n")
            f.write(f"MAE train : {m['mae_train']:.1f} pips\n")
            f.write(f"MAE CV : {m['mae_cv_mean']:.1f} ± {m['mae_cv_std']:.1f} pips\n")
            f.write(f"Overfitting R² : {m['r2_gap']:+.3f}\n")
            f.write(f"Overfitting MAE : {m['mae_gap']:+.1f} pips\n")
            f.write(f"Score : {m['success_count']}/4\n")
        
        f.write(f"\n{'='*70}\n")
        f.write(f"MEILLEUR : {best_config['config_name']}\n")
        f.write(f"{'='*70}\n")
    
    print(f"\n✅ Comparaison sauvegardée : {OUTPUT_COMPARISON}")
    
    # Sauvegarder paramètres meilleur modèle
    best_model = best_config['model']
    best_features = best_config['feature_names']
    
    with open(OUTPUT_MODEL_PARAMS, 'w') as f:
        f.write("# PARAMÈTRES MEILLEUR MODÈLE ML - SESSION 76\n\n")
        f.write(f"CONFIG = '{best_config['config_name']}'\n")
        f.write(f"N_FEATURES = {best_config['n_features']}\n")
        f.write(f"FEATURES = {best_features}\n\n")
        f.write(f"INTERCEPT = {best_model.intercept_:.4f}\n")
        for i, name in enumerate(best_features):
            varname = name.upper().replace('_', '_COEF_')
            f.write(f"COEF_{varname.replace('COEF_COEF_', '')} = {best_model.coef_[i]:.4f}\n")
        f.write(f"\n# Métriques validation\n")
        f.write(f"R2_CV = {best_config['r2_cv_mean']:.3f}\n")
        f.write(f"MAE_CV = {best_config['mae_cv_mean']:.1f}\n")
        f.write(f"SUCCESS_SCORE = {best_config['success_count']}/4\n")
    
    print(f"✅ Paramètres meilleur modèle : {OUTPUT_MODEL_PARAMS}")
    
    print(f"\n{'='*70}")
    print("RÉGRESSION ML OPTIMISÉE TERMINÉE")
    print(f"{'='*70}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
