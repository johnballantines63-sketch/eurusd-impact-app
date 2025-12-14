#!/usr/bin/env python3
"""
Prédiction Directe de l'Impact depuis Features (sans formule actuelle)

Objectif :
Créer une formule de prédiction directement depuis les features prédictives
sans passer par calculate_impact_d qui semble défaillante

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'core'))


def extract_features(row: pd.Series) -> Dict:
    """Extrait features prédictives"""
    return {
        'base_score': row['avg_base_empirical_score'],
        'adjusted_score': row['avg_adjusted_empirical_score'],
        'surprise_avg': row['avg_surprise_pct'],
        'surprise_max': row['max_surprise_pct'],
        'n_events': row['n_events_total'],
        'n_events_us': row['n_events_us'],
        'n_events_high': row['n_events_high'],
        'n_core_events': row['n_core_events'],
        'ratio_high': row['n_events_high'] / row['n_events_total'] if row['n_events_total'] > 0 else 0.0,
        'ratio_us': row['n_events_us'] / row['n_events_total'] if row['n_events_total'] > 0 else 0.0,
    }


def find_linear_formula_from_features(df_features: pd.DataFrame, y: pd.Series) -> Dict:
    """
    Trouve une formule linéaire optimale : impact = a1*f1 + a2*f2 + ... + b
    """
    # Sélectionner features numériques
    feature_cols = [col for col in df_features.columns if col != 'impact_real']
    
    # Préparer données
    X = df_features[feature_cols].fillna(0).values
    y_arr = y.values
    
    # Régression linéaire multiple (méthode des moindres carrés)
    # y = X * coefficients + intercept
    # coefficients = (X'X)^-1 * X'y
    
    # Ajouter colonne de 1 pour intercept
    X_with_intercept = np.column_stack([np.ones(len(X)), X])
    
    # Calculer coefficients
    try:
        coefficients = np.linalg.lstsq(X_with_intercept, y_arr, rcond=None)[0]
        intercept = coefficients[0]
        coefs = coefficients[1:]
        
        # Prédire
        y_pred = X_with_intercept @ coefficients
        y_pred = np.maximum(y_pred, 0.0)  # Pas d'impact négatif
        
        # Évaluer
        mae = np.mean(np.abs(y_pred - y_arr))
        ratio = np.median(y_pred / y_arr)
        corr = np.corrcoef(y_pred, y_arr)[0, 1]
        
        return {
            'formula_type': 'linear_multiple',
            'features': feature_cols,
            'coefficients': coefs.tolist(),
            'intercept': float(intercept),
            'mae': mae,
            'median_ratio': ratio,
            'correlation': corr,
            'predictions': y_pred.tolist()
        }
    except Exception as e:
        print(f"⚠️  Erreur régression : {e}")
        return None


def find_power_formula_from_features(df_features: pd.DataFrame, y: pd.Series) -> Dict:
    """
    Trouve une formule puissance : impact = a * (score^b1) * (events^b2) * ...
    Simplifié : impact = a * (score * events)^b
    """
    # Utiliser score ajusté * nombre événements comme proxy
    score_events = df_features['adjusted_score'].fillna(0) * df_features['n_events'].fillna(0)
    
    # Log transformation
    X_log = np.log1p(score_events.values)
    y_log = np.log1p(y.values)
    
    # Régression linéaire sur logs
    n = len(X_log)
    sum_x = X_log.sum()
    sum_y = y_log.sum()
    sum_xy = (X_log * y_log).sum()
    sum_x2 = (X_log ** 2).sum()
    
    b = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    log_a = (sum_y - b * sum_x) / n
    a = np.exp(log_a)
    
    # Prédire
    y_pred = a * ((df_features['adjusted_score'].fillna(0) * df_features['n_events'].fillna(0)) ** b)
    y_pred = np.maximum(y_pred, 0.0)
    
    # Évaluer
    mae = np.mean(np.abs(y_pred - y.values))
    ratio = np.median(y_pred / y.values)
    corr = np.corrcoef(y_pred, y.values)[0, 1]
    
    return {
        'formula_type': 'power',
        'formula': f"impact = {a:.4f} * (adjusted_score * n_events)^{b:.4f}",
        'coefficient': a,
        'power': b,
        'mae': mae,
        'median_ratio': ratio,
        'correlation': corr,
        'predictions': y_pred.tolist()
    }


def find_simple_multiplier_formula(df_features: pd.DataFrame, y: pd.Series) -> Dict:
    """
    Formule simple : impact = base_score * multiplier_1 + n_events * multiplier_2 + ...
    """
    # Tester différentes combinaisons simples
    best_formula = None
    best_mae = float('inf')
    
    # Formule 1 : impact = a * score + b * events + c
    score = df_features['adjusted_score'].fillna(0).values
    events = df_features['n_events'].fillna(0).values
    
    # Optimiser a, b, c
    for a in np.arange(0.5, 3.0, 0.1):
        for b in np.arange(0.5, 5.0, 0.2):
            for c in np.arange(-10.0, 20.0, 2.0):
                y_pred = a * score + b * events + c
                y_pred = np.maximum(y_pred, 0.0)
                mae = np.mean(np.abs(y_pred - y.values))
                
                if mae < best_mae:
                    best_mae = mae
                    best_formula = {
                        'formula_type': 'simple_linear',
                        'formula': f"impact = {a:.2f} * adjusted_score + {b:.2f} * n_events + {c:.2f}",
                        'coef_score': a,
                        'coef_events': b,
                        'intercept': c,
                        'mae': mae,
                        'predictions': y_pred.tolist()
                    }
    
    if best_formula:
        y_pred = np.array(best_formula['predictions'])
        best_formula['median_ratio'] = float(np.median(y_pred / y.values))
        best_formula['correlation'] = float(np.corrcoef(y_pred, y.values)[0, 1])
    
    return best_formula


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("PRÉDICTION DIRECTE IMPACT DEPUIS FEATURES")
    print("=" * 80)
    print()
    
    # 1. Charger données
    db_file = Path(__file__).parent.parent / 'outputs' / 'predictable_movements_database.csv'
    df = pd.read_csv(db_file)
    
    # Filtrer avec événements US et scores valides
    df_filtered = df[
        (df['n_events_us'] > 0) & 
        (df['avg_base_empirical_score'] > 0)
    ].copy()
    
    print(f"📊 {len(df_filtered)} mouvements analysés")
    print()
    
    # 2. Extraire features
    print("📊 ÉTAPE 1 : Extraction features")
    print("-" * 80)
    
    features_list = []
    for idx, row in df_filtered.iterrows():
        features = extract_features(row)
        features['impact_real'] = row['peak_pips']
        features_list.append(features)
    
    df_features = pd.DataFrame(features_list)
    
    print(f"✅ {len(df_features.columns)} features extraites")
    print()
    
    # 3. Tester différentes formules
    print("📊 ÉTAPE 2 : Test formules directes")
    print("-" * 80)
    print()
    
    y = df_features['impact_real']
    
    # 3.1 Formule linéaire multiple
    print("1️⃣ Formule linéaire multiple (toutes features) :")
    result_linear = find_linear_formula_from_features(df_features.drop(columns=['impact_real']), y)
    
    if result_linear:
        print(f"   Formule : impact = intercept + sum(coef_i * feature_i)")
        print(f"   Intercept : {result_linear['intercept']:.4f}")
        print(f"   Top 5 coefficients :")
        for i, (feat, coef) in enumerate(zip(result_linear['features'][:5], result_linear['coefficients'][:5])):
            print(f"      {feat:<25} : {coef:>10.4f}")
        print(f"   MAE : {result_linear['mae']:.2f} pips")
        print(f"   Ratio médian : {result_linear['median_ratio']:.3f}")
        print(f"   Corrélation : {result_linear['correlation']:.3f}")
        print()
    
    # 3.2 Formule puissance
    print("2️⃣ Formule puissance (score * events) :")
    result_power = find_power_formula_from_features(df_features.drop(columns=['impact_real']), y)
    
    if result_power:
        print(f"   {result_power['formula']}")
        print(f"   MAE : {result_power['mae']:.2f} pips")
        print(f"   Ratio médian : {result_power['median_ratio']:.3f}")
        print(f"   Corrélation : {result_power['correlation']:.3f}")
        print()
    
    # 3.3 Formule simple
    print("3️⃣ Formule simple (score + events) :")
    result_simple = find_simple_multiplier_formula(df_features.drop(columns=['impact_real']), y)
    
    if result_simple:
        print(f"   {result_simple['formula']}")
        print(f"   MAE : {result_simple['mae']:.2f} pips")
        print(f"   Ratio médian : {result_simple['median_ratio']:.3f}")
        print(f"   Corrélation : {result_simple['correlation']:.3f}")
        print()
    
    # 4. Comparer
    print("=" * 80)
    print("📊 COMPARAISON")
    print("=" * 80)
    print()
    
    # Base (formule actuelle)
    from final_corrected_formula import calculate_base_prediction
    impacts_base = []
    for idx, row in df_filtered.iterrows():
        impact_base = calculate_base_prediction(row)
        impacts_base.append(impact_base)
    
    df_filtered['impact_base'] = impacts_base
    mae_base = np.mean(np.abs(df_filtered['impact_base'] - df_filtered['peak_pips']))
    ratio_base = np.median(df_filtered['impact_base'] / df_filtered['peak_pips'])
    
    print(f"{'Méthode':<40} {'MAE':<12} {'Ratio médian':<15} {'Corrélation':<15}")
    print("-" * 82)
    print(f"{'Base (formule actuelle)':<40} {mae_base:>10.2f}   {ratio_base:>13.3f}   {0.232:>13.3f}")
    
    if result_linear:
        print(f"{'Linéaire multiple':<40} {result_linear['mae']:>10.2f}   {result_linear['median_ratio']:>13.3f}   {result_linear['correlation']:>13.3f}")
    if result_power:
        print(f"{'Puissance':<40} {result_power['mae']:>10.2f}   {result_power['median_ratio']:>13.3f}   {result_power['correlation']:>13.3f}")
    if result_simple:
        print(f"{'Simple':<40} {result_simple['mae']:>10.2f}   {result_simple['median_ratio']:>13.3f}   {result_simple['correlation']:>13.3f}")
    print()
    
    # 5. Meilleure méthode
    results = []
    if result_linear:
        results.append(('Linéaire multiple', result_linear))
    if result_power:
        results.append(('Puissance', result_power))
    if result_simple:
        results.append(('Simple', result_simple))
    
    if results:
        best = min(results, key=lambda x: x[1]['mae'])
        
        print("=" * 80)
        print("🏆 MEILLEURE MÉTHODE")
        print("=" * 80)
        print()
        print(f"Méthode : {best[0]}")
        if 'formula' in best[1]:
            print(f"Formule : {best[1]['formula']}")
        print(f"MAE : {best[1]['mae']:.2f} pips")
        print(f"Ratio médian : {best[1]['median_ratio']:.3f}")
        print(f"Corrélation : {best[1]['correlation']:.3f}")
        print()
        
        # Analyse par classe
        if 'predictions' in best[1]:
            df_filtered['impact_direct'] = best[1]['predictions']
            
            print("📊 Analyse par classe RÉELLE :")
            print()
            for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
                df_class = df_filtered[df_filtered['movement_class'] == movement_class]
                if len(df_class) > 0:
                    mae_class = np.mean(np.abs(df_class['impact_direct'] - df_class['peak_pips']))
                    ratio_class = np.median(df_class['impact_direct'] / df_class['peak_pips'])
                    
                    print(f"   {movement_class:12s} ({len(df_class):3d} mouvements) :")
                    print(f"      MAE : {mae_class:.2f} pips")
                    print(f"      Ratio médian : {ratio_class:.3f}")
            print()
    
    # 6. Sauvegarder
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if 'impact_direct' in df_filtered.columns:
        df_filtered.to_csv(output_dir / 'predictions_direct_from_features.csv', index=False)
    
    if results:
        best_result = min(results, key=lambda x: x[1]['mae'])[1]
        pd.DataFrame([best_result]).to_csv(output_dir / 'best_direct_formula_from_features.csv', index=False)
    
    print(f"💾 Fichiers sauvegardés dans : {output_dir}")
    print()
    
    print("=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)


if __name__ == '__main__':
    main()


