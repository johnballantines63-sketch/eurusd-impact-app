#!/usr/bin/env python3
"""
Régression Directe de l'Impact (sans classification de classe)

Objectif :
1. Utiliser régression directe pour prédire l'impact
2. Comparer avec la formule actuelle
3. Tester différentes approches

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict
from scipy.stats import pearsonr

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'core'))

# Imports des formules validées
try:
    from src.core.formulas_validated import (
        calculate_adjusted_empirical_score,
        calculate_impact_d,
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
    
    def calculate_impact_d(empirical_score: float, num_events: int = 1, 
                          amplification: float = 1.0, correction_factor: float = 0.758) -> float:
        if num_events >= 2:
            intercept = -10.47
            coefficient = 0.477
        else:
            intercept = -7.08
            coefficient = 0.419
        impact_brut = intercept + (coefficient * empirical_score)
        impact_amplifie = abs(impact_brut) * amplification
        return impact_amplifie * correction_factor


def calculate_base_prediction(row: pd.Series) -> float:
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
        return 0.0
    
    amplification = 1.0
    if pd.notna(surprise_pct) and surprise_pct > 15.0:
        amplification = calculate_amplification_extended(surprise_pct)
        amplification = min(amplification, 3.0)
    
    return calculate_impact_d(
        empirical_score=empirical_score,
        num_events=num_events,
        amplification=amplification,
        correction_factor=0.758
    )


def find_optimal_global_multiplier(df: pd.DataFrame) -> float:
    """
    Trouve un multiplicateur global optimal pour tous les mouvements
    """
    best_mult = 1.0
    best_mae = float('inf')
    
    for mult in np.arange(1.0, 8.0, 0.1):
        corrected = df['impact_base'] * mult
        mae = np.mean(np.abs(corrected - df['peak_pips']))
        if mae < best_mae:
            best_mae = mae
            best_mult = mult
    
    return best_mult, best_mae


def find_optimal_multiplier_by_impact_base(df: pd.DataFrame) -> Dict:
    """
    Trouve des multiplicateurs adaptatifs selon l'impact_base
    Plus l'impact_base est élevé, plus le multiplicateur est élevé
    """
    # Diviser en bins selon impact_base
    df['impact_base_bin'] = pd.cut(df['impact_base'], bins=5, labels=['Très faible', 'Faible', 'Moyen', 'Élevé', 'Très élevé'])
    
    multipliers = {}
    
    for bin_name in df['impact_base_bin'].cat.categories:
        df_bin = df[df['impact_base_bin'] == bin_name]
        
        if len(df_bin) == 0:
            continue
        
        best_mult = 1.0
        best_mae = float('inf')
        
        for mult in np.arange(1.0, 10.0, 0.1):
            corrected = df_bin['impact_base'] * mult
            mae = np.mean(np.abs(corrected - df_bin['peak_pips']))
            if mae < best_mae:
                best_mae = mae
                best_mult = mult
        
        multipliers[bin_name] = {
            'multiplier': best_mult,
            'mae': best_mae,
            'n_samples': len(df_bin),
            'avg_base': df_bin['impact_base'].mean(),
            'avg_real': df_bin['peak_pips'].mean()
        }
    
    return multipliers


def find_optimal_formula_linear(df: pd.DataFrame) -> Dict:
    """
    Trouve une formule linéaire optimale : impact = a * impact_base + b
    """
    # Régression linéaire simple
    X = df['impact_base'].values.reshape(-1, 1)
    y = df['peak_pips'].values
    
    # Utiliser numpy pour régression
    # y = a*x + b
    # a = (n*sum(xy) - sum(x)*sum(y)) / (n*sum(x²) - sum(x)²)
    # b = (sum(y) - a*sum(x)) / n
    
    n = len(X)
    sum_x = X.sum()
    sum_y = y.sum()
    sum_xy = (X.flatten() * y).sum()
    sum_x2 = (X.flatten() ** 2).sum()
    
    a = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    b = (sum_y - a * sum_x) / n
    
    # Prédire
    y_pred = a * X.flatten() + b
    mae = np.mean(np.abs(y_pred - y))
    ratio = np.median(y_pred / y)
    corr = np.corrcoef(y_pred, y)[0, 1]
    
    return {
        'formula': f"impact = {a:.4f} * impact_base + {b:.4f}",
        'coefficient': a,
        'intercept': b,
        'mae': mae,
        'median_ratio': ratio,
        'correlation': corr
    }


def find_optimal_formula_power(df: pd.DataFrame) -> Dict:
    """
    Trouve une formule puissance : impact = a * impact_base^b
    """
    # Log transformation pour régression linéaire
    # log(y) = log(a) + b*log(x)
    # y = a * x^b
    
    X_log = np.log1p(df['impact_base'].values)
    y_log = np.log1p(df['peak_pips'].values)
    
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
    y_pred = a * (df['impact_base'].values ** b)
    mae = np.mean(np.abs(y_pred - df['peak_pips'].values))
    ratio = np.median(y_pred / df['peak_pips'].values)
    corr = np.corrcoef(y_pred, df['peak_pips'].values)[0, 1]
    
    return {
        'formula': f"impact = {a:.4f} * impact_base^{b:.4f}",
        'coefficient': a,
        'power': b,
        'mae': mae,
        'median_ratio': ratio,
        'correlation': corr
    }


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("RÉGRESSION DIRECTE DE L'IMPACT")
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
    
    # 2. Calculer prédictions de base
    print("📊 ÉTAPE 1 : Calcul prédictions de base")
    print("-" * 80)
    
    impacts_base = []
    for idx, row in df_filtered.iterrows():
        impact_base = calculate_base_prediction(row)
        impacts_base.append(impact_base)
    
    df_filtered['impact_base'] = impacts_base
    df_filtered = df_filtered[df_filtered['impact_base'] > 0].copy()  # Filtrer prédictions valides
    
    print(f"Impact base moyen : {df_filtered['impact_base'].mean():.2f} pips")
    print(f"Impact réel moyen : {df_filtered['peak_pips'].mean():.2f} pips")
    print(f"Ratio base/réel : {df_filtered['impact_base'].mean() / df_filtered['peak_pips'].mean():.3f}")
    print()
    
    # 3. Test différentes approches
    print("📊 ÉTAPE 2 : Test différentes formules de correction")
    print("-" * 80)
    print()
    
    results = []
    
    # 3.1 Multiplicateur global
    print("1️⃣ Multiplicateur global optimal")
    mult_global, mae_global = find_optimal_global_multiplier(df_filtered)
    corrected_global = df_filtered['impact_base'] * mult_global
    ratio_global = np.median(corrected_global / df_filtered['peak_pips'])
    corr_global = np.corrcoef(corrected_global, df_filtered['peak_pips'])[0, 1]
    
    results.append({
        'method': 'Multiplicateur global',
        'formula': f"impact_base * {mult_global:.3f}",
        'mae': mae_global,
        'median_ratio': ratio_global,
        'correlation': corr_global
    })
    
    print(f"   Multiplicateur : {mult_global:.3f}x")
    print(f"   MAE : {mae_global:.2f} pips")
    print(f"   Ratio médian : {ratio_global:.3f}")
    print(f"   Corrélation : {corr_global:.3f}")
    print()
    
    # 3.2 Formule linéaire
    print("2️⃣ Formule linéaire (impact = a * impact_base + b)")
    result_linear = find_optimal_formula_linear(df_filtered)
    results.append({
        'method': 'Formule linéaire',
        **result_linear
    })
    
    print(f"   Formule : {result_linear['formula']}")
    print(f"   MAE : {result_linear['mae']:.2f} pips")
    print(f"   Ratio médian : {result_linear['median_ratio']:.3f}")
    print(f"   Corrélation : {result_linear['correlation']:.3f}")
    print()
    
    # 3.3 Formule puissance
    print("3️⃣ Formule puissance (impact = a * impact_base^b)")
    result_power = find_optimal_formula_power(df_filtered)
    results.append({
        'method': 'Formule puissance',
        **result_power
    })
    
    print(f"   Formule : {result_power['formula']}")
    print(f"   MAE : {result_power['mae']:.2f} pips")
    print(f"   Ratio médian : {result_power['median_ratio']:.3f}")
    print(f"   Corrélation : {result_power['correlation']:.3f}")
    print()
    
    # 3.4 Multiplicateur adaptatif par impact_base
    print("4️⃣ Multiplicateur adaptatif selon impact_base")
    mult_adaptive = find_optimal_multiplier_by_impact_base(df_filtered)
    
    # Appliquer
    corrected_adaptive = []
    for idx, row in df_filtered.iterrows():
        bin_name = row['impact_base_bin']
        if bin_name in mult_adaptive:
            mult = mult_adaptive[bin_name]['multiplier']
            corrected_adaptive.append(row['impact_base'] * mult)
        else:
            corrected_adaptive.append(row['impact_base'])
    
    df_filtered['impact_corrected_adaptive'] = corrected_adaptive
    mae_adaptive = np.mean(np.abs(df_filtered['impact_corrected_adaptive'] - df_filtered['peak_pips']))
    ratio_adaptive = np.median(df_filtered['impact_corrected_adaptive'] / df_filtered['peak_pips'])
    corr_adaptive = np.corrcoef(df_filtered['impact_corrected_adaptive'], df_filtered['peak_pips'])[0, 1]
    
    results.append({
        'method': 'Multiplicateur adaptatif',
        'formula': 'Selon bin impact_base',
        'mae': mae_adaptive,
        'median_ratio': ratio_adaptive,
        'correlation': corr_adaptive
    })
    
    print("   Multiplicateurs par bin :")
    for bin_name, stats in mult_adaptive.items():
        print(f"      {bin_name:15s} : {stats['multiplier']:>5.2f}x (MAE: {stats['mae']:.2f}, {stats['n_samples']:3d} échantillons)")
    print(f"   MAE global : {mae_adaptive:.2f} pips")
    print(f"   Ratio médian : {ratio_adaptive:.3f}")
    print(f"   Corrélation : {corr_adaptive:.3f}")
    print()
    
    # 4. Comparer toutes les méthodes
    print("=" * 80)
    print("📊 COMPARAISON TOUTES LES MÉTHODES")
    print("=" * 80)
    print()
    
    # Base
    mae_base = np.mean(np.abs(df_filtered['impact_base'] - df_filtered['peak_pips']))
    ratio_base = np.median(df_filtered['impact_base'] / df_filtered['peak_pips'])
    corr_base = np.corrcoef(df_filtered['impact_base'], df_filtered['peak_pips'])[0, 1]
    
    print(f"{'Méthode':<40} {'MAE':<12} {'Ratio médian':<15} {'Corrélation':<15}")
    print("-" * 82)
    print(f"{'Base (sans correction)':<40} {mae_base:>10.2f}   {ratio_base:>13.3f}   {corr_base:>13.3f}")
    
    for result in results:
        print(f"{result['method']:<40} {result['mae']:>10.2f}   {result['median_ratio']:>13.3f}   {result['correlation']:>13.3f}")
    print()
    
    # 5. Meilleure méthode
    best = min(results, key=lambda x: x['mae'])
    
    print("=" * 80)
    print("🏆 MEILLEURE MÉTHODE")
    print("=" * 80)
    print()
    print(f"Méthode : {best['method']}")
    print(f"Formule : {best.get('formula', 'N/A')}")
    print(f"MAE : {best['mae']:.2f} pips")
    print(f"Ratio médian : {best['median_ratio']:.3f}")
    print(f"Corrélation : {best['correlation']:.3f}")
    print()
    
    # 6. Analyse par classe de mouvement (pour référence)
    print("📊 Analyse par classe RÉELLE (avec meilleure méthode) :")
    print()
    
    # Appliquer meilleure méthode
    if best['method'] == 'Multiplicateur global':
        df_filtered['impact_corrected'] = df_filtered['impact_base'] * mult_global
    elif best['method'] == 'Formule linéaire':
        df_filtered['impact_corrected'] = result_linear['coefficient'] * df_filtered['impact_base'] + result_linear['intercept']
    elif best['method'] == 'Formule puissance':
        df_filtered['impact_corrected'] = result_power['coefficient'] * (df_filtered['impact_base'] ** result_power['power'])
    elif best['method'] == 'Multiplicateur adaptatif':
        df_filtered['impact_corrected'] = df_filtered['impact_corrected_adaptive']
    
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df_filtered[df_filtered['movement_class'] == movement_class]
        if len(df_class) > 0:
            mae_class = np.mean(np.abs(df_class['impact_corrected'] - df_class['peak_pips']))
            ratio_class = np.median(df_class['impact_corrected'] / df_class['peak_pips'])
            
            print(f"   {movement_class:12s} ({len(df_class):3d} mouvements) :")
            print(f"      MAE : {mae_class:.2f} pips")
            print(f"      Ratio médian : {ratio_class:.3f}")
    print()
    
    # 7. Sauvegarder
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_filtered.to_csv(output_dir / 'predictions_direct_regression.csv', index=False)
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_dir / 'direct_regression_comparison.csv', index=False)
    
    # Sauvegarder meilleure formule
    best_formula = {
        'method': best['method'],
        'formula': best.get('formula', ''),
        'mae': best['mae'],
        'median_ratio': best['median_ratio'],
        'correlation': best['correlation'],
        **{k: v for k, v in best.items() if k not in ['method', 'formula', 'mae', 'median_ratio', 'correlation']}
    }
    
    pd.DataFrame([best_formula]).to_csv(output_dir / 'best_direct_regression_formula.csv', index=False)
    
    print(f"💾 Fichiers sauvegardés dans : {output_dir}")
    print()
    
    print("=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)


if __name__ == '__main__':
    main()


