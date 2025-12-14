#!/usr/bin/env python3
"""
Recherche Facteurs Prédictifs pour Mouvements FORT/TRÈS_FORT

Objectif :
1. Identifier des facteurs calculables AVANT le mouvement
2. Ces facteurs doivent être corrélés avec l'amplitude réelle
3. Créer une formule de correction basée sur ces facteurs prédictifs

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'core'))

# Imports des formules validées
try:
    from src.core.formulas_validated import (
        calculate_adjusted_empirical_score,
        calculate_amplification_extended
    )
except ImportError:
    def calculate_adjusted_empirical_score(base_score: float, surprise_pct: float) -> float:
        if surprise_pct < 5.0:
            factor = 1.0
        elif surprise_pct < 15.0:
            factor = 1.0 + (surprise_pct - 5.0) / 10.0 * 0.5
        elif surprise_pct < 30.0:
            factor = 1.5 + (surprise_pct - 15.0) / 15.0 * 0.4
        else:
            factor = 1.9
        return base_score * factor
    
    def calculate_amplification_extended(surprise_pct: float) -> float:
        abs_surprise = abs(surprise_pct)
        if abs_surprise < 5.0:
            return 1.0
        elif abs_surprise < 15.0:
            return 1.0 + (abs_surprise - 5.0) / 10.0 * 0.5
        elif abs_surprise < 30.0:
            return 1.5 + (abs_surprise - 15.0) / 15.0 * 0.4
        elif abs_surprise < 100.0:
            return 1.9 + (abs_surprise - 30.0) / 70.0 * 1.1
        elif abs_surprise < 200.0:
            return 3.0 + (abs_surprise - 100.0) / 100.0 * 1.0
        else:
            return min(5.5 + 0.371 * np.log10(abs_surprise - 199), 10.0)


def extract_predictive_features(row: pd.Series) -> Dict:
    """
    Extrait tous les facteurs prédictifs (calculables AVANT le mouvement)
    """
    features = {
        # Scores
        'base_empirical_score': row['avg_base_empirical_score'],
        'adjusted_empirical_score': row['avg_adjusted_empirical_score'],
        
        # Surprises
        'avg_surprise_pct': row['avg_surprise_pct'],
        'max_surprise_pct': row['max_surprise_pct'],
        'surprise_net': row['surprise_net'],
        
        # Événements
        'n_events_total': row['n_events_total'],
        'n_events_us': row['n_events_us'],
        'n_events_eu': row['n_events_eu'],
        'n_events_high': row['n_events_high'],
        'n_events_medium': row['n_events_medium'],
        'n_events_low': row['n_events_low'],
        'n_core_events': row['n_core_events'],
        
        # Ratios
        'ratio_high_events': row['n_events_high'] / row['n_events_total'] if row['n_events_total'] > 0 else 0.0,
        'ratio_us_events': row['n_events_us'] / row['n_events_total'] if row['n_events_total'] > 0 else 0.0,
        'ratio_core_events': row['n_core_events'] / row['n_events_total'] if row['n_events_total'] > 0 else 0.0,
        
        # Impact réel (pour corrélation)
        'impact_real': row['peak_pips']
    }
    
    return features


def analyze_correlations(df_features: pd.DataFrame) -> pd.DataFrame:
    """
    Analyse les corrélations entre facteurs prédictifs et impact réel
    """
    correlations = []
    
    # Exclure impact_real de la liste des features
    feature_cols = [col for col in df_features.columns if col != 'impact_real']
    
    for col in feature_cols:
        if df_features[col].dtype in [np.float64, np.int64]:
            # Filtrer valeurs valides
            valid = df_features[[col, 'impact_real']].dropna()
            if len(valid) > 10:
                corr, p_value = pearsonr(valid[col], valid['impact_real'])
                correlations.append({
                    'feature': col,
                    'correlation': corr,
                    'p_value': p_value,
                    'abs_correlation': abs(corr),
                    'n_samples': len(valid)
                })
    
    df_corr = pd.DataFrame(correlations)
    df_corr = df_corr.sort_values('abs_correlation', ascending=False)
    
    return df_corr


def find_best_multiplier_formula(df_features: pd.DataFrame, df_corr: pd.DataFrame) -> Dict:
    """
    Trouve la meilleure formule de correction basée sur les facteurs prédictifs
    """
    # Prendre les top features corrélées
    top_features = df_corr.head(10)['feature'].tolist()
    
    # Préparer données
    X = df_features[top_features].fillna(0)
    y = df_features['impact_real']
    
    # Standardiser
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Régression linéaire
    model = LinearRegression()
    model.fit(X_scaled, y)
    
    # Prédire
    y_pred = model.predict(X_scaled)
    
    # Calculer ratio prédit/réel moyen pour chaque mouvement
    ratios = y_pred / y
    median_ratio = np.median(ratios)
    
    # Calculer MAE
    mae = np.mean(np.abs(y_pred - y))
    
    # Corrélation
    correlation = np.corrcoef(y_pred, y)[0, 1]
    
    return {
        'features': top_features,
        'coefficients': model.coef_.tolist(),
        'intercept': model.intercept_,
        'mae': mae,
        'median_ratio': median_ratio,
        'correlation': correlation,
        'scaler_mean': scaler.mean_.tolist(),
        'scaler_scale': scaler.scale_.tolist()
    }


def test_simple_multiplier_formulas(df_features: pd.DataFrame) -> List[Dict]:
    """
    Teste des formules simples de correction basées sur un seul facteur
    """
    results = []
    
    # Facteurs à tester
    factors_to_test = [
        'n_events_total',
        'n_events_us',
        'n_events_high',
        'n_core_events',
        'avg_base_empirical_score',
        'avg_adjusted_empirical_score',
        'avg_surprise_pct',
        'max_surprise_pct',
        'ratio_high_events',
        'ratio_us_events'
    ]
    
    for factor in factors_to_test:
        if factor not in df_features.columns:
            continue
        
        # Tester différentes formules
        for formula_type in ['linear', 'log', 'sqrt', 'square']:
            if formula_type == 'linear':
                # impact_corrected = impact_base * (1 + factor * multiplier)
                # Optimiser multiplier
                best_mult = 0.0
                best_mae = float('inf')
                
                for mult in np.arange(0.0, 2.0, 0.1):
                    corrected = df_features['impact_base'] * (1.0 + df_features[factor] * mult)
                    mae = np.mean(np.abs(corrected - df_features['impact_real']))
                    if mae < best_mae:
                        best_mae = mae
                        best_mult = mult
                
                if best_mult > 0:
                    corrected = df_features['impact_base'] * (1.0 + df_features[factor] * best_mult)
                    ratio = np.median(corrected / df_features['impact_real'])
                    corr = np.corrcoef(corrected, df_features['impact_real'])[0, 1]
                    
                    results.append({
                        'factor': factor,
                        'formula_type': formula_type,
                        'formula': f"impact_base * (1 + {factor} * {best_mult:.3f})",
                        'multiplier': best_mult,
                        'mae': best_mae,
                        'median_ratio': ratio,
                        'correlation': corr
                    })
            
            elif formula_type == 'log':
                # impact_corrected = impact_base * (1 + log(factor + 1) * multiplier)
                factor_log = np.log1p(df_features[factor].fillna(0))
                
                best_mult = 0.0
                best_mae = float('inf')
                
                for mult in np.arange(0.0, 5.0, 0.2):
                    corrected = df_features['impact_base'] * (1.0 + factor_log * mult)
                    mae = np.mean(np.abs(corrected - df_features['impact_real']))
                    if mae < best_mae:
                        best_mae = mae
                        best_mult = mult
                
                if best_mult > 0:
                    corrected = df_features['impact_base'] * (1.0 + factor_log * best_mult)
                    ratio = np.median(corrected / df_features['impact_real'])
                    corr = np.corrcoef(corrected, df_features['impact_real'])[0, 1]
                    
                    results.append({
                        'factor': factor,
                        'formula_type': formula_type,
                        'formula': f"impact_base * (1 + log({factor} + 1) * {best_mult:.3f})",
                        'multiplier': best_mult,
                        'mae': best_mae,
                        'median_ratio': ratio,
                        'correlation': corr
                    })
    
    return results


def main():
    """
    Fonction principale
    """
    
    print("=" * 80)
    print("RECHERCHE FACTEURS PRÉDICTIFS POUR MOUVEMENTS FORT/TRÈS_FORT")
    print("=" * 80)
    print()
    
    # 1. Charger données
    db_file = Path(__file__).parent.parent / 'outputs' / 'predictable_movements_database.csv'
    df = pd.read_csv(db_file)
    
    # Filtrer mouvements FORT/TRÈS_FORT avec US
    df_strong = df[
        (df['movement_class'].isin(['FORT', 'TRÈS_FORT'])) &
        (df['n_events_us'] > 0) & 
        (df['avg_base_empirical_score'] > 0)
    ].copy()
    
    print(f"📊 {len(df_strong)} mouvements FORT/TRÈS_FORT analysés")
    print()
    
    # 2. Calculer prédictions de base
    print("📊 ÉTAPE 1 : Calcul prédictions de base")
    print("-" * 80)
    
    def calculate_base_prediction(row: pd.Series) -> Dict:
        """Calcule la prédiction de base"""
        base_score = row['avg_base_empirical_score']
        adjusted_score = row['avg_adjusted_empirical_score']
        surprise_pct = row['avg_surprise_pct']
        num_events = row['n_events_total']
        
        if pd.notna(adjusted_score) and adjusted_score > 0:
            empirical_score = adjusted_score
        elif pd.notna(base_score) and base_score > 0:
            empirical_score = calculate_adjusted_empirical_score(base_score, surprise_pct)
        else:
            return {'impact_base': 0.0}
        
        amplification = 1.0
        if pd.notna(surprise_pct) and surprise_pct > 15.0:
            amplification = calculate_amplification_extended(surprise_pct)
            amplification = min(amplification, 3.0)
        
        if num_events >= 2:
            intercept = -10.47
            coefficient = 0.477
        else:
            intercept = -7.08
            coefficient = 0.419
        
        impact_brut = intercept + (coefficient * empirical_score)
        impact_amplifie = abs(impact_brut) * amplification
        impact_base = impact_amplifie * 0.758
        
        return {'impact_base': impact_base}
    
    impacts_base = []
    for idx, row in df_strong.iterrows():
        pred = calculate_base_prediction(row)
        impacts_base.append(pred['impact_base'])
    
    df_strong['impact_base'] = impacts_base
    
    print(f"Impact base moyen : {np.mean(impacts_base):.2f} pips")
    print(f"Impact réel moyen : {df_strong['peak_pips'].mean():.2f} pips")
    print()
    
    # 3. Extraire features prédictives
    print("📊 ÉTAPE 2 : Extraction features prédictives")
    print("-" * 80)
    
    features_list = []
    for idx, row in df_strong.iterrows():
        features = extract_predictive_features(row)
        features['impact_base'] = row['impact_base']
        features_list.append(features)
    
    df_features = pd.DataFrame(features_list)
    
    print(f"✅ {len(df_features.columns)} features extraites")
    print()
    
    # 4. Analyser corrélations
    print("📊 ÉTAPE 3 : Analyse corrélations avec impact réel")
    print("-" * 80)
    print()
    
    df_corr = analyze_correlations(df_features)
    
    print("🔍 Top 10 facteurs les plus corrélés avec impact réel :")
    print()
    print(f"{'Facteur':<30} {'Corrélation':<15} {'P-value':<15} {'|Corr|':<15}")
    print("-" * 75)
    for _, row in df_corr.head(10).iterrows():
        sig = "***" if row['p_value'] < 0.001 else "**" if row['p_value'] < 0.01 else "*" if row['p_value'] < 0.05 else ""
        print(f"{row['feature']:<30} {row['correlation']:>13.3f}{sig:<2}   {row['p_value']:>13.4f}   {row['abs_correlation']:>13.3f}")
    print()
    
    # 5. Tester formules simples
    print("📊 ÉTAPE 4 : Test formules de correction simples")
    print("-" * 80)
    print()
    
    simple_results = test_simple_multiplier_formulas(df_features)
    
    if simple_results:
        df_simple = pd.DataFrame(simple_results)
        df_simple = df_simple.sort_values('mae')
        
        print("🔍 Top 5 formules simples (par MAE) :")
        print()
        print(f"{'Formule':<50} {'MAE':<12} {'Ratio':<12} {'Corrélation':<15}")
        print("-" * 89)
        for _, row in df_simple.head(5).iterrows():
            print(f"{row['formula']:<50} {row['mae']:>10.2f}   {row['median_ratio']:>10.3f}   {row['correlation']:>13.3f}")
        print()
        
        best_simple = df_simple.iloc[0]
        print(f"🏆 Meilleure formule simple :")
        print(f"   {best_simple['formula']}")
        print(f"   MAE : {best_simple['mae']:.2f} pips")
        print(f"   Ratio médian : {best_simple['median_ratio']:.3f}")
        print(f"   Corrélation : {best_simple['correlation']:.3f}")
        print()
    
    # 6. Régression multiple
    print("📊 ÉTAPE 5 : Régression multiple (tous facteurs)")
    print("-" * 80)
    print()
    
    try:
        regression_result = find_best_multiplier_formula(df_features, df_corr)
        
        print("🔍 Régression multiple :")
        print(f"   Features utilisées : {', '.join(regression_result['features'][:5])}...")
        print(f"   MAE : {regression_result['mae']:.2f} pips")
        print(f"   Ratio médian : {regression_result['median_ratio']:.3f}")
        print(f"   Corrélation : {regression_result['correlation']:.3f}")
        print()
        
        # Afficher coefficients
        print("   Coefficients (top 5) :")
        for i, (feat, coef) in enumerate(zip(regression_result['features'][:5], 
                                             regression_result['coefficients'][:5])):
            print(f"      {feat:<30} : {coef:>10.4f}")
        print()
        
    except Exception as e:
        print(f"⚠️  Erreur régression : {e}")
        regression_result = None
    
    # 7. Recommandation
    print("=" * 80)
    print("💡 RECOMMANDATION")
    print("=" * 80)
    print()
    
    if simple_results and regression_result:
        if best_simple['mae'] < regression_result['mae']:
            print("✅ Utiliser formule simple (plus facile à implémenter) :")
            print(f"   {best_simple['formula']}")
        else:
            print("✅ Utiliser régression multiple (meilleure précision) :")
            print(f"   {len(regression_result['features'])} features combinées")
    elif simple_results:
        print("✅ Utiliser formule simple :")
        print(f"   {best_simple['formula']}")
    
    print()
    
    # 8. Sauvegarder
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_corr.to_csv(output_dir / 'predictive_factors_correlations.csv', index=False)
    
    if simple_results:
        df_simple.to_csv(output_dir / 'simple_correction_formulas.csv', index=False)
    
    if regression_result:
        pd.DataFrame([regression_result]).to_csv(output_dir / 'regression_correction_formula.csv', index=False)
    
    print(f"💾 Fichiers sauvegardés dans : {output_dir}")
    print()
    
    print("=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)


if __name__ == '__main__':
    main()


