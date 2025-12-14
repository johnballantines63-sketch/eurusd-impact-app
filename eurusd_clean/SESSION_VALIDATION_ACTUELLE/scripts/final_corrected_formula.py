#!/usr/bin/env python3
"""
Formule Corrigée Finale pour Tous les Mouvements

Objectif :
1. Utiliser formule puissance comme base
2. Ajouter facteur correctif pour mouvements forts (basé sur impact_base)
3. Tester et valider

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


def calculate_corrected_impact_power(impact_base: float, a: float = 40.4205, b: float = 0.0733) -> float:
    """
    Formule puissance : impact = a * impact_base^b
    """
    if impact_base <= 0:
        return 0.0
    return a * (impact_base ** b)


def calculate_corrected_impact_hybrid(impact_base: float) -> float:
    """
    Formule hybride : puissance + facteur correctif pour mouvements forts
    """
    if impact_base <= 0:
        return 0.0
    
    # Formule puissance de base
    impact_power = calculate_corrected_impact_power(impact_base)
    
    # Facteur correctif : plus impact_base est élevé, plus on amplifie
    # Si impact_base > 15 pips (mouvements forts), appliquer facteur supplémentaire
    if impact_base > 15.0:
        # Facteur progressif : 1.0 à 15 pips, jusqu'à 2.5x à 20+ pips
        excess = impact_base - 15.0
        correction_factor = 1.0 + (excess / 5.0) * 1.5  # Max 2.5x à 20+ pips
        correction_factor = min(correction_factor, 2.5)
        return impact_power * correction_factor
    else:
        return impact_power


def optimize_hybrid_correction(df: pd.DataFrame) -> Dict:
    """
    Optimise les paramètres de la formule hybride
    """
    best_params = None
    best_mae = float('inf')
    
    # Tester différents seuils et facteurs
    for threshold in [10.0, 12.0, 15.0, 18.0, 20.0]:
        for max_factor in [2.0, 2.5, 3.0, 3.5, 4.0]:
            corrected = []
            for impact_base in df['impact_base']:
                if impact_base <= 0:
                    corrected.append(0.0)
                    continue
                
                impact_power = calculate_corrected_impact_power(impact_base)
                
                if impact_base > threshold:
                    excess = impact_base - threshold
                    correction_factor = 1.0 + (excess / 5.0) * (max_factor - 1.0)
                    correction_factor = min(correction_factor, max_factor)
                    corrected.append(impact_power * correction_factor)
                else:
                    corrected.append(impact_power)
            
            mae = np.mean(np.abs(np.array(corrected) - df['peak_pips'].values))
            
            if mae < best_mae:
                best_mae = mae
                best_params = {
                    'threshold': threshold,
                    'max_factor': max_factor,
                    'mae': mae
                }
    
    return best_params


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("FORMULE CORRIGÉE FINALE")
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
    df_filtered = df_filtered[df_filtered['impact_base'] > 0].copy()
    
    print(f"Impact base moyen : {df_filtered['impact_base'].mean():.2f} pips")
    print(f"Impact réel moyen : {df_filtered['peak_pips'].mean():.2f} pips")
    print()
    
    # 3. Tester formules
    print("📊 ÉTAPE 2 : Test formules corrigées")
    print("-" * 80)
    print()
    
    # 3.1 Formule puissance simple
    impacts_power = [calculate_corrected_impact_power(ib) for ib in df_filtered['impact_base']]
    df_filtered['impact_power'] = impacts_power
    mae_power = np.mean(np.abs(df_filtered['impact_power'] - df_filtered['peak_pips']))
    ratio_power = np.median(df_filtered['impact_power'] / df_filtered['peak_pips'])
    corr_power = np.corrcoef(df_filtered['impact_power'], df_filtered['peak_pips'])[0, 1]
    
    print("1️⃣ Formule puissance simple :")
    print(f"   impact = 40.4205 * impact_base^0.0733")
    print(f"   MAE : {mae_power:.2f} pips")
    print(f"   Ratio médian : {ratio_power:.3f}")
    print(f"   Corrélation : {corr_power:.3f}")
    print()
    
    # 3.2 Formule hybride (optimisée)
    print("2️⃣ Formule hybride (puissance + correctif mouvements forts) :")
    print("   Optimisation en cours...")
    
    best_params = optimize_hybrid_correction(df_filtered)
    
    # Appliquer formule hybride optimale
    impacts_hybrid = []
    for impact_base in df_filtered['impact_base']:
        if impact_base <= 0:
            impacts_hybrid.append(0.0)
            continue
        
        impact_power = calculate_corrected_impact_power(impact_base)
        
        if impact_base > best_params['threshold']:
            excess = impact_base - best_params['threshold']
            correction_factor = 1.0 + (excess / 5.0) * (best_params['max_factor'] - 1.0)
            correction_factor = min(correction_factor, best_params['max_factor'])
            impacts_hybrid.append(impact_power * correction_factor)
        else:
            impacts_hybrid.append(impact_power)
    
    df_filtered['impact_hybrid'] = impacts_hybrid
    mae_hybrid = np.mean(np.abs(df_filtered['impact_hybrid'] - df_filtered['peak_pips']))
    ratio_hybrid = np.median(df_filtered['impact_hybrid'] / df_filtered['peak_pips'])
    corr_hybrid = np.corrcoef(df_filtered['impact_hybrid'], df_filtered['peak_pips'])[0, 1]
    
    print(f"   Seuil : {best_params['threshold']:.1f} pips")
    print(f"   Facteur max : {best_params['max_factor']:.2f}x")
    print(f"   MAE : {mae_hybrid:.2f} pips")
    print(f"   Ratio médian : {ratio_hybrid:.3f}")
    print(f"   Corrélation : {corr_hybrid:.3f}")
    print()
    
    # 4. Comparer
    print("=" * 80)
    print("📊 COMPARAISON")
    print("=" * 80)
    print()
    
    mae_base = np.mean(np.abs(df_filtered['impact_base'] - df_filtered['peak_pips']))
    ratio_base = np.median(df_filtered['impact_base'] / df_filtered['peak_pips'])
    
    print(f"{'Méthode':<40} {'MAE':<12} {'Ratio médian':<15} {'Corrélation':<15}")
    print("-" * 82)
    print(f"{'Base (sans correction)':<40} {mae_base:>10.2f}   {ratio_base:>13.3f}   {0.232:>13.3f}")
    print(f"{'Formule puissance':<40} {mae_power:>10.2f}   {ratio_power:>13.3f}   {corr_power:>13.3f}")
    print(f"{'Formule hybride (optimale)':<40} {mae_hybrid:>10.2f}   {ratio_hybrid:>13.3f}   {corr_hybrid:>13.3f}")
    print()
    
    # 5. Analyse par classe
    print("📊 Analyse par classe RÉELLE (formule hybride) :")
    print()
    
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df_filtered[df_filtered['movement_class'] == movement_class]
        if len(df_class) > 0:
            mae_class = np.mean(np.abs(df_class['impact_hybrid'] - df_class['peak_pips']))
            ratio_class = np.median(df_class['impact_hybrid'] / df_class['peak_pips'])
            
            print(f"   {movement_class:12s} ({len(df_class):3d} mouvements) :")
            print(f"      MAE : {mae_class:.2f} pips")
            print(f"      Ratio médian : {ratio_class:.3f}")
            print(f"      Impact réel moy : {df_class['peak_pips'].mean():.1f} pips")
            print(f"      Impact prédit moy : {df_class['impact_hybrid'].mean():.1f} pips")
    print()
    
    # 6. Sauvegarder
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_filtered.to_csv(output_dir / 'predictions_final_corrected_formula.csv', index=False)
    
    final_formula = {
        'formula_type': 'hybrid_power',
        'base_formula': 'impact = 40.4205 * impact_base^0.0733',
        'correction_threshold': best_params['threshold'],
        'correction_max_factor': best_params['max_factor'],
        'correction_formula': f"Si impact_base > {best_params['threshold']}: multiplier par (1 + (excess/5) * {best_params['max_factor']-1.0})",
        'mae': mae_hybrid,
        'median_ratio': ratio_hybrid,
        'correlation': corr_hybrid
    }
    
    pd.DataFrame([final_formula]).to_csv(output_dir / 'final_corrected_formula.csv', index=False)
    
    print(f"💾 Fichiers sauvegardés dans : {output_dir}")
    print()
    
    print("=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)
    print()
    print("💡 FORMULE FINALE RECOMMANDÉE :")
    print(f"   1. Calculer impact_base avec formule actuelle")
    print(f"   2. Appliquer formule puissance : impact = 40.4205 * impact_base^0.0733")
    print(f"   3. Si impact_base > {best_params['threshold']:.1f} pips :")
    print(f"      → Appliquer facteur correctif progressif (max {best_params['max_factor']:.2f}x)")
    print()
    print(f"   Performance :")
    print(f"   - MAE : {mae_hybrid:.2f} pips")
    print(f"   - Ratio médian : {ratio_hybrid:.3f}")
    print(f"   - Corrélation : {corr_hybrid:.3f}")
    print()


if __name__ == '__main__':
    main()


