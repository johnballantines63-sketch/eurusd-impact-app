#!/usr/bin/env python3
"""
Correction Basée sur Valeur de la Prédiction Linéaire

Objectif :
Si prédiction linéaire élevée → mouvement fort probable → facteur correctif
Plus simple et plus robuste que des critères complexes

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def calculate_linear_prediction(row: pd.Series) -> float:
    """Calcule prédiction linéaire"""
    intercept = 30.5450
    coef_base_score = 0.4692
    coef_adjusted_score = 0.1882
    coef_surprise_avg = 0.0201
    coef_surprise_max = -0.0034
    coef_n_events = 0.7355
    
    base_score = row['avg_base_empirical_score'] if pd.notna(row['avg_base_empirical_score']) else 0.0
    adjusted_score = row['avg_adjusted_empirical_score'] if pd.notna(row['avg_adjusted_empirical_score']) else 0.0
    surprise_avg = row['avg_surprise_pct'] if pd.notna(row['avg_surprise_pct']) else 0.0
    surprise_max = row['max_surprise_pct'] if pd.notna(row['max_surprise_pct']) else 0.0
    n_events = row['n_events_total'] if pd.notna(row['n_events_total']) else 0.0
    
    impact = (intercept +
              coef_base_score * base_score +
              coef_adjusted_score * adjusted_score +
              coef_surprise_avg * surprise_avg +
              coef_surprise_max * surprise_max +
              coef_n_events * n_events)
    
    return max(impact, 0.0)


def optimize_prediction_based_correction(df: pd.DataFrame) -> Dict:
    """
    Optimise correction basée sur valeur de prédiction linéaire
    Si prédiction > seuil → facteur correctif
    """
    # Calculer prédictions linéaires
    linear_preds = []
    for idx, row in df.iterrows():
        pred = calculate_linear_prediction(row)
        linear_preds.append(pred)
    
    df['impact_linear'] = linear_preds
    
    # Tester différents seuils et facteurs
    best_params = None
    best_mae = float('inf')
    
    for threshold in np.arange(40.0, 80.0, 5.0):
        for factor in np.arange(1.2, 2.5, 0.1):
            corrected = []
            for pred in df['impact_linear']:
                if pred > threshold:
                    corrected.append(pred * factor)
                else:
                    corrected.append(pred)
            
            mae = np.mean(np.abs(np.array(corrected) - df['peak_pips'].values))
            if mae < best_mae:
                best_mae = mae
                best_params = {
                    'threshold': threshold,
                    'factor': factor,
                    'mae': mae
                }
    
    return best_params


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("CORRECTION BASÉE SUR VALEUR PRÉDICTION")
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
    
    # 2. Calculer prédictions linéaires
    print("📊 ÉTAPE 1 : Calcul prédictions linéaires")
    print("-" * 80)
    
    linear_preds = []
    for idx, row in df_filtered.iterrows():
        pred = calculate_linear_prediction(row)
        linear_preds.append(pred)
    
    df_filtered['impact_linear'] = linear_preds
    
    mae_linear = np.mean(np.abs(df_filtered['impact_linear'] - df_filtered['peak_pips']))
    ratio_linear = np.median(df_filtered['impact_linear'] / df_filtered['peak_pips'])
    corr_linear = np.corrcoef(df_filtered['impact_linear'], df_filtered['peak_pips'])[0, 1]
    
    print(f"MAE linéaire : {mae_linear:.2f} pips")
    print(f"Ratio médian : {ratio_linear:.3f}")
    print(f"Corrélation : {corr_linear:.3f}")
    print()
    
    # 3. Optimiser correction
    print("📊 ÉTAPE 2 : Optimisation correction basée sur prédiction")
    print("-" * 80)
    print("   (Optimisation en cours...)")
    
    best_params = optimize_prediction_based_correction(df_filtered)
    
    print(f"✅ Seuil optimal : {best_params['threshold']:.1f} pips")
    print(f"   Facteur optimal : {best_params['factor']:.2f}x")
    print()
    
    # 4. Appliquer correction
    print("📊 ÉTAPE 3 : Application correction")
    print("-" * 80)
    
    corrected_preds = []
    for pred in df_filtered['impact_linear']:
        if pred > best_params['threshold']:
            corrected_preds.append(pred * best_params['factor'])
        else:
            corrected_preds.append(pred)
    
    df_filtered['impact_corrected'] = corrected_preds
    
    mae_corrected = np.mean(np.abs(df_filtered['impact_corrected'] - df_filtered['peak_pips']))
    ratio_corrected = np.median(df_filtered['impact_corrected'] / df_filtered['peak_pips'])
    corr_corrected = np.corrcoef(df_filtered['impact_corrected'], df_filtered['peak_pips'])[0, 1]
    
    # 5. Comparer
    print("=" * 80)
    print("📊 COMPARAISON")
    print("=" * 80)
    print()
    
    print(f"{'Méthode':<40} {'MAE':<12} {'Ratio médian':<15} {'Corrélation':<15}")
    print("-" * 82)
    print(f"{'Linéaire seule':<40} {mae_linear:>10.2f}   {ratio_linear:>13.3f}   {corr_linear:>13.3f}")
    print(f"{'Avec correction (seuil {best_params[\"threshold\"]:.0f})':<40} {mae_corrected:>10.2f}   {ratio_corrected:>13.3f}   {corr_corrected:>13.3f}")
    print()
    
    # 6. Analyse par classe
    print("📊 Analyse par classe RÉELLE :")
    print()
    
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df_filtered[df_filtered['movement_class'] == movement_class]
        if len(df_class) > 0:
            mae_class = np.mean(np.abs(df_class['impact_corrected'] - df_class['peak_pips']))
            ratio_class = np.median(df_class['impact_corrected'] / df_class['peak_pips'])
            
            # Compter combien dépassent le seuil
            n_above_threshold = (df_class['impact_linear'] > best_params['threshold']).sum()
            
            print(f"   {movement_class:12s} ({len(df_class):3d} mouvements) :")
            print(f"      Prédictions > seuil : {n_above_threshold}/{len(df_class)} ({n_above_threshold/len(df_class)*100:.1f}%)")
            print(f"      MAE : {mae_class:.2f} pips")
            print(f"      Ratio médian : {ratio_class:.3f}")
            print(f"      Impact réel moy : {df_class['peak_pips'].mean():.1f} pips")
            print(f"      Impact prédit moy : {df_class['impact_corrected'].mean():.1f} pips")
    print()
    
    # 7. Sauvegarder
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_filtered.to_csv(output_dir / 'predictions_prediction_based_correction.csv', index=False)
    
    final_formula = {
        'formula_type': 'linear_with_prediction_threshold',
        'base_formula': 'impact = 30.5450 + 0.4692*base_score + 0.1882*adjusted_score + 0.0201*surprise_avg - 0.0034*surprise_max + 0.7355*n_events',
        'correction_threshold': best_params['threshold'],
        'correction_factor': best_params['factor'],
        'correction_rule': f"Si impact_linear > {best_params['threshold']:.1f} pips : multiplier par {best_params['factor']:.2f}x",
        'mae': mae_corrected,
        'median_ratio': ratio_corrected,
        'correlation': corr_corrected
    }
    
    pd.DataFrame([final_formula]).to_csv(output_dir / 'final_prediction_based_formula.csv', index=False)
    
    print(f"💾 Fichiers sauvegardés dans : {output_dir}")
    print()
    
    print("=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)
    print()
    print("💡 FORMULE FINALE RECOMMANDÉE :")
    print()
    print("1. Calculer prédiction linéaire :")
    print("   impact = 30.5450 + 0.4692*base_score + 0.1882*adjusted_score")
    print("            + 0.0201*surprise_avg - 0.0034*surprise_max + 0.7355*n_events")
    print()
    print(f"2. Si impact > {best_params['threshold']:.1f} pips (mouvement fort probable) :")
    print(f"   → Multiplier par {best_params['factor']:.2f}x")
    print()
    print(f"   Performance :")
    print(f"   - MAE : {mae_corrected:.2f} pips")
    print(f"   - Ratio médian : {ratio_corrected:.3f}")
    print(f"   - Corrélation : {corr_corrected:.3f}")
    print()


if __name__ == '__main__':
    main()


