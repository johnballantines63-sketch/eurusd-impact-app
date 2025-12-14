#!/usr/bin/env python3
"""
Prédiction Classe de Mouvement - Version Simplifiée

Objectif :
1. PRÉDIRE la classe de mouvement basé sur des règles simples (sans ML)
2. Trouver multiplicateurs optimaux par classe
3. Tester la correction

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


def predict_movement_class_simple(row: pd.Series) -> str:
    """
    Prédit la classe de mouvement basé sur des règles simples
    Utilise uniquement des features calculables AVANT le mouvement
    """
    base_score = row['avg_base_empirical_score']
    adjusted_score = row['avg_adjusted_empirical_score']
    surprise_pct = row['avg_surprise_pct']
    num_events = row['n_events_total']
    n_events_high = row['n_events_high']
    n_events_us = row['n_events_us']
    
    # Calculer score prédictif
    score_used = adjusted_score if pd.notna(adjusted_score) and adjusted_score > 0 else base_score
    
    # Règles simples basées sur seuils
    # TRÈS_FORT : score élevé + beaucoup d'événements + surprise forte
    if (score_used >= 50.0 and num_events >= 15 and surprise_pct >= 30.0) or \
       (score_used >= 60.0 and num_events >= 12):
        return 'TRÈS_FORT'
    
    # FORT : score moyen-élevé + événements
    elif (score_used >= 40.0 and num_events >= 12) or \
         (score_used >= 35.0 and num_events >= 15) or \
         (n_events_high >= 8 and score_used >= 30.0):
        return 'FORT'
    
    # MOYEN : score moyen
    elif score_used >= 25.0 or num_events >= 10:
        return 'MOYEN'
    
    # FAIBLE : reste
    else:
        return 'FAIBLE'


def find_optimal_multipliers_by_class(df: pd.DataFrame) -> Dict:
    """Trouve les multiplicateurs optimaux pour chaque classe"""
    multipliers = {}
    
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df[df['movement_class'] == movement_class].copy()
        
        if len(df_class) == 0:
            continue
        
        # Optimiser multiplier
        best_mult = 1.0
        best_mae = float('inf')
        
        # Recherche plus fine
        for mult in np.arange(0.5, 8.0, 0.05):
            corrected = df_class['impact_base'] * mult
            mae = np.mean(np.abs(corrected - df_class['peak_pips']))
            
            if mae < best_mae:
                best_mae = mae
                best_mult = mult
        
        multipliers[movement_class] = {
            'multiplier': best_mult,
            'mae': best_mae,
            'n_samples': len(df_class),
            'avg_real': df_class['peak_pips'].mean(),
            'avg_base': df_class['impact_base'].mean()
        }
    
    return multipliers


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("PRÉDICTION CLASSE MOUVEMENT - VERSION SIMPLIFIÉE")
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
    
    print(f"Impact base moyen : {np.mean(impacts_base):.2f} pips")
    print(f"Impact réel moyen : {df_filtered['peak_pips'].mean():.2f} pips")
    print()
    
    # 3. Prédire classes
    print("📊 ÉTAPE 2 : Prédiction classes de mouvement")
    print("-" * 80)
    
    predicted_classes = []
    for idx, row in df_filtered.iterrows():
        pred_class = predict_movement_class_simple(row)
        predicted_classes.append(pred_class)
    
    df_filtered['movement_class_predicted'] = predicted_classes
    
    # Statistiques prédiction
    correct = (df_filtered['movement_class'] == df_filtered['movement_class_predicted']).sum()
    accuracy = correct / len(df_filtered) * 100
    
    print(f"Précision classification : {accuracy:.1f}% ({correct}/{len(df_filtered)})")
    print()
    
    # Détail par classe
    print("📊 Précision par classe :")
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df_filtered[df_filtered['movement_class'] == movement_class]
        if len(df_class) > 0:
            correct_class = (df_class['movement_class_predicted'] == movement_class).sum()
            accuracy_class = correct_class / len(df_class) * 100
            print(f"   {movement_class:12s} : {accuracy_class:>5.1f}% ({correct_class}/{len(df_class)})")
    print()
    
    # 4. Trouver multiplicateurs optimaux
    print("📊 ÉTAPE 3 : Optimisation multiplicateurs par classe RÉELLE")
    print("-" * 80)
    
    multipliers_real = find_optimal_multipliers_by_class(df_filtered)
    
    print("Multiplicateurs optimaux (basés sur classes RÉELLES) :")
    for movement_class, stats in multipliers_real.items():
        print(f"   {movement_class:12s} : {stats['multiplier']:>5.2f}x (MAE: {stats['mae']:.2f} pips, {stats['n_samples']:3d} échantillons)")
    print()
    
    # 5. Appliquer corrections
    print("📊 ÉTAPE 4 : Application corrections")
    print("-" * 80)
    
    mult_map = {cls: stats['multiplier'] for cls, stats in multipliers_real.items()}
    
    # Correction selon classe PRÉDITE
    impacts_corrected_pred = []
    for idx, row in df_filtered.iterrows():
        pred_class = row['movement_class_predicted']
        multiplier = mult_map.get(pred_class, 1.0)
        impacts_corrected_pred.append(row['impact_base'] * multiplier)
    
    df_filtered['impact_corrected_predicted'] = impacts_corrected_pred
    
    # Correction selon classe RÉELLE (référence)
    impacts_corrected_real = []
    for idx, row in df_filtered.iterrows():
        real_class = row['movement_class']
        multiplier = mult_map.get(real_class, 1.0)
        impacts_corrected_real.append(row['impact_base'] * multiplier)
    
    df_filtered['impact_corrected_real'] = impacts_corrected_real
    
    # 6. Comparer résultats
    print("📊 ÉTAPE 5 : Comparaison résultats")
    print("-" * 80)
    print()
    
    mae_base = np.mean(np.abs(df_filtered['impact_base'] - df_filtered['peak_pips']))
    ratio_base = np.median(df_filtered['impact_base'] / df_filtered['peak_pips'])
    corr_base = np.corrcoef(df_filtered['impact_base'], df_filtered['peak_pips'])[0, 1]
    
    mae_predicted = np.mean(np.abs(df_filtered['impact_corrected_predicted'] - df_filtered['peak_pips']))
    ratio_predicted = np.median(df_filtered['impact_corrected_predicted'] / df_filtered['peak_pips'])
    corr_predicted = np.corrcoef(df_filtered['impact_corrected_predicted'], df_filtered['peak_pips'])[0, 1]
    
    mae_real = np.mean(np.abs(df_filtered['impact_corrected_real'] - df_filtered['peak_pips']))
    ratio_real = np.median(df_filtered['impact_corrected_real'] / df_filtered['peak_pips'])
    corr_real = np.corrcoef(df_filtered['impact_corrected_real'], df_filtered['peak_pips'])[0, 1]
    
    print(f"{'Méthode':<40} {'MAE':<12} {'Ratio médian':<15} {'Corrélation':<15}")
    print("-" * 82)
    print(f"{'Base (sans correction)':<40} {mae_base:>10.2f}   {ratio_base:>13.3f}   {corr_base:>13.3f}")
    print(f"{'Correction classe PRÉDITE':<40} {mae_predicted:>10.2f}   {ratio_predicted:>13.3f}   {corr_predicted:>13.3f}")
    print(f"{'Correction classe RÉELLE (réf)':<40} {mae_real:>10.2f}   {ratio_real:>13.3f}   {corr_real:>13.3f}")
    print()
    
    # Analyse par classe réelle
    print("📊 Analyse par classe RÉELLE (avec correction selon classe PRÉDITE) :")
    print()
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df_filtered[df_filtered['movement_class'] == movement_class]
        if len(df_class) > 0:
            mae_class = np.mean(np.abs(df_class['impact_corrected_predicted'] - df_class['peak_pips']))
            ratio_class = np.median(df_class['impact_corrected_predicted'] / df_class['peak_pips'])
            correct_pred = (df_class['movement_class_predicted'] == movement_class).sum()
            
            print(f"   {movement_class:12s} ({len(df_class):3d} mouvements) :")
            print(f"      Classification correcte : {correct_pred}/{len(df_class)} ({correct_pred/len(df_class)*100:.1f}%)")
            print(f"      MAE après correction     : {mae_class:.2f} pips")
            print(f"      Ratio médian              : {ratio_class:.3f}")
    print()
    
    # 7. Sauvegarder
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_filtered.to_csv(output_dir / 'predictions_with_class_prediction.csv', index=False)
    
    df_mult = pd.DataFrame([
        {'movement_class': cls, **stats} 
        for cls, stats in multipliers_real.items()
    ])
    df_mult.to_csv(output_dir / 'optimal_multipliers_by_class_simple.csv', index=False)
    
    comparison = {
        'method': ['Base', 'Classe prédite', 'Classe réelle'],
        'mae': [mae_base, mae_predicted, mae_real],
        'median_ratio': [ratio_base, ratio_predicted, ratio_real],
        'correlation': [corr_base, corr_predicted, corr_real]
    }
    pd.DataFrame(comparison).to_csv(output_dir / 'comparison_class_prediction_simple.csv', index=False)
    
    print(f"💾 Fichiers sauvegardés dans : {output_dir}")
    print()
    
    print("=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)
    print()
    print("💡 CONCLUSION :")
    print(f"   - Précision classification : {accuracy:.1f}%")
    print(f"   - MAE avec correction prédite : {mae_predicted:.2f} pips")
    print(f"   - MAE avec correction réelle (réf) : {mae_real:.2f} pips")
    print(f"   - Amélioration vs base : {(mae_base - mae_predicted) / mae_base * 100:.1f}%")
    print()


if __name__ == '__main__':
    main()


