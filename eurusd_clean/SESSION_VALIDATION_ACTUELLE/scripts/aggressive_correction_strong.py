#!/usr/bin/env python3
"""
Correction Agressive pour Mouvements Forts

Objectif :
Utiliser impact_base comme proxy de la force du mouvement
Si impact_base élevé → mouvement fort probable → facteur correctif élevé

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


def calculate_corrected_impact_aggressive(impact_base: float) -> float:
    """
    Correction agressive basée sur impact_base
    Plus impact_base est élevé, plus le facteur correctif est élevé
    """
    if impact_base <= 0:
        return 0.0
    
    # Zones de correction
    if impact_base <= 5.0:
        # Très faible : multiplier modéré
        return impact_base * 2.0
    elif impact_base <= 10.0:
        # Faible : multiplier moyen
        return impact_base * 2.5
    elif impact_base <= 15.0:
        # Moyen : multiplier élevé
        return impact_base * 3.0
    elif impact_base <= 20.0:
        # Élevé : multiplier très élevé
        return impact_base * 4.0
    else:
        # Très élevé : multiplier maximum
        return impact_base * 5.0


def optimize_aggressive_correction(df: pd.DataFrame) -> Dict:
    """
    Optimise les seuils et facteurs de la correction agressive (version rapide)
    """
    best_params = None
    best_mae = float('inf')
    
    # Seuils fixes (basés sur distribution)
    thresholds = [5.0, 10.0, 15.0, 20.0]
    t1, t2, t3 = thresholds[0], thresholds[1], thresholds[2]
    
    # Optimiser facteurs un par un (plus rapide)
    print("   Optimisation facteurs...")
    
    # Facteur 1 (impact_base <= 5)
    best_f1 = 2.0
    best_mae_f1 = float('inf')
    for f1 in np.arange(1.5, 3.0, 0.1):
        corrected = []
        for impact_base in df['impact_base']:
            if impact_base <= t1:
                corrected.append(impact_base * f1)
            else:
                corrected.append(impact_base * 2.0)  # Facteur temporaire
        mae = np.mean(np.abs(np.array(corrected) - df['peak_pips'].values))
        if mae < best_mae_f1:
            best_mae_f1 = mae
            best_f1 = f1
    
    # Facteur 2 (5 < impact_base <= 10)
    best_f2 = 2.5
    best_mae_f2 = float('inf')
    for f2 in np.arange(2.0, 4.0, 0.1):
        corrected = []
        for impact_base in df['impact_base']:
            if impact_base <= t1:
                corrected.append(impact_base * best_f1)
            elif impact_base <= t2:
                corrected.append(impact_base * f2)
            else:
                corrected.append(impact_base * 3.0)  # Facteur temporaire
        mae = np.mean(np.abs(np.array(corrected) - df['peak_pips'].values))
        if mae < best_mae_f2:
            best_mae_f2 = mae
            best_f2 = f2
    
    # Facteur 3 (10 < impact_base <= 15)
    best_f3 = 3.0
    best_mae_f3 = float('inf')
    for f3 in np.arange(3.0, 5.0, 0.1):
        corrected = []
        for impact_base in df['impact_base']:
            if impact_base <= t1:
                corrected.append(impact_base * best_f1)
            elif impact_base <= t2:
                corrected.append(impact_base * best_f2)
            elif impact_base <= t3:
                corrected.append(impact_base * f3)
            else:
                corrected.append(impact_base * 4.0)  # Facteur temporaire
        mae = np.mean(np.abs(np.array(corrected) - df['peak_pips'].values))
        if mae < best_mae_f3:
            best_mae_f3 = mae
            best_f3 = f3
    
    # Facteur 4 (impact_base > 15)
    best_f4 = 4.0
    best_mae_f4 = float('inf')
    for f4 in np.arange(4.0, 7.0, 0.1):
        corrected = []
        for impact_base in df['impact_base']:
            if impact_base <= t1:
                corrected.append(impact_base * best_f1)
            elif impact_base <= t2:
                corrected.append(impact_base * best_f2)
            elif impact_base <= t3:
                corrected.append(impact_base * best_f3)
            else:
                corrected.append(impact_base * f4)
        mae = np.mean(np.abs(np.array(corrected) - df['peak_pips'].values))
        if mae < best_mae_f4:
            best_mae_f4 = mae
            best_f4 = f4
    
    # Calculer MAE final avec tous les facteurs
    corrected_final = []
    for impact_base in df['impact_base']:
        if impact_base <= t1:
            corrected_final.append(impact_base * best_f1)
        elif impact_base <= t2:
            corrected_final.append(impact_base * best_f2)
        elif impact_base <= t3:
            corrected_final.append(impact_base * best_f3)
        else:
            corrected_final.append(impact_base * best_f4)
    
    mae_final = np.mean(np.abs(np.array(corrected_final) - df['peak_pips'].values))
    
    return {
        'threshold1': t1,
        'threshold2': t2,
        'threshold3': t3,
        'factor1': best_f1,
        'factor2': best_f2,
        'factor3': best_f3,
        'factor4': best_f4,
        'mae': mae_final
    }


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("CORRECTION AGRESSIVE POUR MOUVEMENTS FORTS")
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
    
    # 3. Optimiser correction agressive
    print("📊 ÉTAPE 2 : Optimisation correction agressive")
    print("-" * 80)
    print("   (Cela peut prendre quelques minutes...)")
    print()
    
    best_params = optimize_aggressive_correction(df_filtered)
    
    print("✅ Paramètres optimaux trouvés :")
    print(f"   Seuil 1 : {best_params['threshold1']:.1f} pips → facteur {best_params['factor1']:.2f}x")
    print(f"   Seuil 2 : {best_params['threshold2']:.1f} pips → facteur {best_params['factor2']:.2f}x")
    print(f"   Seuil 3 : {best_params['threshold3']:.1f} pips → facteur {best_params['factor3']:.2f}x")
    print(f"   > Seuil 3 : facteur {best_params['factor4']:.2f}x")
    print()
    
    # 4. Appliquer correction optimale
    corrected_impacts = []
    for impact_base in df_filtered['impact_base']:
        if impact_base <= 0:
            corrected_impacts.append(0.0)
        elif impact_base <= best_params['threshold1']:
            corrected_impacts.append(impact_base * best_params['factor1'])
        elif impact_base <= best_params['threshold2']:
            corrected_impacts.append(impact_base * best_params['factor2'])
        elif impact_base <= best_params['threshold3']:
            corrected_impacts.append(impact_base * best_params['factor3'])
        else:
            corrected_impacts.append(impact_base * best_params['factor4'])
    
    df_filtered['impact_corrected'] = corrected_impacts
    
    # 5. Comparer résultats
    print("📊 ÉTAPE 3 : Comparaison résultats")
    print("-" * 80)
    print()
    
    mae_base = np.mean(np.abs(df_filtered['impact_base'] - df_filtered['peak_pips']))
    ratio_base = np.median(df_filtered['impact_base'] / df_filtered['peak_pips'])
    corr_base = np.corrcoef(df_filtered['impact_base'], df_filtered['peak_pips'])[0, 1]
    
    mae_corrected = np.mean(np.abs(df_filtered['impact_corrected'] - df_filtered['peak_pips']))
    ratio_corrected = np.median(df_filtered['impact_corrected'] / df_filtered['peak_pips'])
    corr_corrected = np.corrcoef(df_filtered['impact_corrected'], df_filtered['peak_pips'])[0, 1]
    
    print(f"{'Méthode':<40} {'MAE':<12} {'Ratio médian':<15} {'Corrélation':<15}")
    print("-" * 82)
    print(f"{'Base (sans correction)':<40} {mae_base:>10.2f}   {ratio_base:>13.3f}   {corr_base:>13.3f}")
    print(f"{'Correction agressive (optimale)':<40} {mae_corrected:>10.2f}   {ratio_corrected:>13.3f}   {corr_corrected:>13.3f}")
    print()
    
    # 6. Analyse par classe
    print("📊 Analyse par classe RÉELLE :")
    print()
    
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df_filtered[df_filtered['movement_class'] == movement_class]
        if len(df_class) > 0:
            mae_class = np.mean(np.abs(df_class['impact_corrected'] - df_class['peak_pips']))
            ratio_class = np.median(df_class['impact_corrected'] / df_class['peak_pips'])
            
            # Distribution impact_base pour cette classe
            avg_base_class = df_class['impact_base'].mean()
            
            print(f"   {movement_class:12s} ({len(df_class):3d} mouvements) :")
            print(f"      Impact base moy    : {avg_base_class:.2f} pips")
            print(f"      Impact réel moy    : {df_class['peak_pips'].mean():.1f} pips")
            print(f"      Impact corrigé moy : {df_class['impact_corrected'].mean():.1f} pips")
            print(f"      MAE                : {mae_class:.2f} pips")
            print(f"      Ratio médian       : {ratio_class:.3f}")
    print()
    
    # 7. Sauvegarder
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_filtered.to_csv(output_dir / 'predictions_aggressive_correction.csv', index=False)
    
    final_formula = {
        'formula_type': 'aggressive_threshold_based',
        'threshold1': best_params['threshold1'],
        'factor1': best_params['factor1'],
        'threshold2': best_params['threshold2'],
        'factor2': best_params['factor2'],
        'threshold3': best_params['threshold3'],
        'factor3': best_params['factor3'],
        'factor4': best_params['factor4'],
        'formula': f"Si impact_base <= {best_params['threshold1']}: *{best_params['factor1']:.2f}x | "
                   f"Si <= {best_params['threshold2']}: *{best_params['factor2']:.2f}x | "
                   f"Si <= {best_params['threshold3']}: *{best_params['factor3']:.2f}x | "
                   f"Sinon: *{best_params['factor4']:.2f}x",
        'mae': mae_corrected,
        'median_ratio': ratio_corrected,
        'correlation': corr_corrected
    }
    
    pd.DataFrame([final_formula]).to_csv(output_dir / 'aggressive_correction_formula.csv', index=False)
    
    print(f"💾 Fichiers sauvegardés dans : {output_dir}")
    print()
    
    print("=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)
    print()
    print("💡 FORMULE FINALE RECOMMANDÉE :")
    print(f"   Basée sur impact_base (proxy de force du mouvement) :")
    print(f"   - Si impact_base <= {best_params['threshold1']:.1f} pips : multiplier par {best_params['factor1']:.2f}x")
    print(f"   - Si impact_base <= {best_params['threshold2']:.1f} pips : multiplier par {best_params['factor2']:.2f}x")
    print(f"   - Si impact_base <= {best_params['threshold3']:.1f} pips : multiplier par {best_params['factor3']:.2f}x")
    print(f"   - Si impact_base > {best_params['threshold3']:.1f} pips : multiplier par {best_params['factor4']:.2f}x")
    print()
    print(f"   Performance :")
    print(f"   - MAE : {mae_corrected:.2f} pips")
    print(f"   - Ratio médian : {ratio_corrected:.3f}")
    print(f"   - Corrélation : {corr_corrected:.3f}")
    print()


if __name__ == '__main__':
    main()


