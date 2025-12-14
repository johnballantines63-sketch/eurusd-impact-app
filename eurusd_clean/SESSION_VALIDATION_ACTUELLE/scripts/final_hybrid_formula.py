#!/usr/bin/env python3
"""
Formule Hybride Finale : Linéaire Multiple + Correctif Mouvements Forts

Objectif :
1. Utiliser formule linéaire multiple comme base
2. Ajouter facteur correctif pour mouvements forts (basé sur features)
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


def calculate_linear_prediction(row: pd.Series) -> float:
    """
    Calcule prédiction avec formule linéaire multiple (optimisée précédemment)
    """
    # Coefficients optimisés
    intercept = 30.5450
    coef_base_score = 0.4692
    coef_adjusted_score = 0.1882
    coef_surprise_avg = 0.0201
    coef_surprise_max = -0.0034
    coef_n_events = 0.7355
    coef_n_events_us = 0.0  # À optimiser si nécessaire
    coef_n_events_high = 0.0
    coef_n_core_events = 0.0
    coef_ratio_high = 0.0
    coef_ratio_us = 0.0
    
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


def optimize_strong_movement_correction(df: pd.DataFrame) -> Dict:
    """
    Optimise des facteurs correctifs pour différents niveaux de mouvements forts
    """
    # Calculer prédictions linéaires
    linear_preds = []
    for idx, row in df.iterrows():
        pred = calculate_linear_prediction(row)
        linear_preds.append(pred)
    
    df['impact_linear'] = linear_preds
    
    # Identifier différents niveaux de mouvements forts
    # Niveau 1 : FORT (score élevé OU beaucoup d'événements)
    df['is_strong'] = (
        (df['avg_adjusted_empirical_score'] >= 40.0) |
        (df['n_events_total'] >= 15)
    )
    
    # Niveau 2 : TRÈS_FORT (critères plus larges pour mieux capturer)
    df['is_very_strong'] = (
        ((df['avg_adjusted_empirical_score'] >= 45.0) & (df['n_events_total'] >= 15)) |
        ((df['avg_adjusted_empirical_score'] >= 40.0) & (df['n_events_total'] >= 17)) |
        ((df['avg_surprise_pct'] >= 40.0) & (df['n_events_total'] >= 15))
    )
    
    # Optimiser facteurs séparément
    best_factor_strong = 1.0
    best_factor_very_strong = 1.0
    best_mae = float('inf')
    
    # Optimiser facteur FORT
    for f_strong in np.arange(1.0, 2.0, 0.1):
        # Optimiser facteur TRÈS_FORT (plus agressif)
        for f_very_strong in np.arange(1.5, 4.0, 0.2):
            corrected = []
            for idx, row in df.iterrows():
                pred = row['impact_linear']
                if row['is_very_strong']:
                    corrected.append(pred * f_very_strong)
                elif row['is_strong']:
                    corrected.append(pred * f_strong)
                else:
                    corrected.append(pred)
            
            mae = np.mean(np.abs(np.array(corrected) - df['peak_pips'].values))
            if mae < best_mae:
                best_mae = mae
                best_factor_strong = f_strong
                best_factor_very_strong = f_very_strong
    
    return {
        'factor_strong': best_factor_strong,
        'factor_very_strong': best_factor_very_strong,
        'mae': best_mae,
        'criteria_strong': 'adjusted_score >= 40 OR n_events >= 15',
        'criteria_very_strong': '(adjusted_score >= 45 AND n_events >= 15) OR (adjusted_score >= 40 AND n_events >= 17) OR (surprise >= 40% AND n_events >= 15)'
    }


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("FORMULE HYBRIDE FINALE")
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
    
    # 3. Optimiser correctif mouvements forts
    print("📊 ÉTAPE 2 : Optimisation correctif mouvements forts")
    print("-" * 80)
    
    correction_params = optimize_strong_movement_correction(df_filtered)
    
    print(f"Facteur correctif FORT : {correction_params['factor_strong']:.2f}x")
    print(f"Facteur correctif TRÈS_FORT : {correction_params['factor_very_strong']:.2f}x")
    print(f"Critères FORT : {correction_params['criteria_strong']}")
    print(f"Critères TRÈS_FORT : {correction_params['criteria_very_strong']}")
    print()
    
    # 4. Appliquer formule hybride
    print("📊 ÉTAPE 3 : Application formule hybride")
    print("-" * 80)
    
    # Identifier niveaux
    df_filtered['is_strong'] = (
        (df_filtered['avg_adjusted_empirical_score'] >= 40.0) |
        (df_filtered['n_events_total'] >= 15)
    )
    
    df_filtered['is_very_strong'] = (
        ((df_filtered['avg_adjusted_empirical_score'] >= 45.0) & (df_filtered['n_events_total'] >= 15)) |
        ((df_filtered['avg_adjusted_empirical_score'] >= 40.0) & (df_filtered['n_events_total'] >= 17)) |
        ((df_filtered['avg_surprise_pct'] >= 40.0) & (df_filtered['n_events_total'] >= 15))
    )
    
    hybrid_preds = []
    for idx, row in df_filtered.iterrows():
        linear_pred = row['impact_linear']
        
        if row['is_very_strong']:
            hybrid_pred = linear_pred * correction_params['factor_very_strong']
        elif row['is_strong']:
            hybrid_pred = linear_pred * correction_params['factor_strong']
        else:
            hybrid_pred = linear_pred
        
        hybrid_preds.append(hybrid_pred)
    
    df_filtered['impact_hybrid'] = hybrid_preds
    
    mae_hybrid = np.mean(np.abs(df_filtered['impact_hybrid'] - df_filtered['peak_pips']))
    ratio_hybrid = np.median(df_filtered['impact_hybrid'] / df_filtered['peak_pips'])
    corr_hybrid = np.corrcoef(df_filtered['impact_hybrid'], df_filtered['peak_pips'])[0, 1]
    
    # 5. Comparer
    print("=" * 80)
    print("📊 COMPARAISON")
    print("=" * 80)
    print()
    
    print(f"{'Méthode':<40} {'MAE':<12} {'Ratio médian':<15} {'Corrélation':<15}")
    print("-" * 82)
    print(f"{'Linéaire seule':<40} {mae_linear:>10.2f}   {ratio_linear:>13.3f}   {corr_linear:>13.3f}")
    print(f"{'Hybride (avec correctif)':<40} {mae_hybrid:>10.2f}   {ratio_hybrid:>13.3f}   {corr_hybrid:>13.3f}")
    print()
    
    # 6. Analyse par classe
    print("📊 Analyse par classe RÉELLE (formule hybride) :")
    print()
    
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df_filtered[df_filtered['movement_class'] == movement_class]
        if len(df_class) > 0:
            mae_class = np.mean(np.abs(df_class['impact_hybrid'] - df_class['peak_pips']))
            ratio_class = np.median(df_class['impact_hybrid'] / df_class['peak_pips'])
            
            # Compter combien sont détectés comme forts
            n_detected_strong = df_class['is_strong'].sum()
            n_detected_very_strong = df_class['is_very_strong'].sum()
            
            print(f"   {movement_class:12s} ({len(df_class):3d} mouvements) :")
            print(f"      Détectés FORT : {n_detected_strong}/{len(df_class)} ({n_detected_strong/len(df_class)*100:.1f}%)")
            print(f"      Détectés TRÈS_FORT : {n_detected_very_strong}/{len(df_class)} ({n_detected_very_strong/len(df_class)*100:.1f}%)")
            print(f"      MAE : {mae_class:.2f} pips")
            print(f"      Ratio médian : {ratio_class:.3f}")
            print(f"      Impact réel moy : {df_class['peak_pips'].mean():.1f} pips")
            print(f"      Impact prédit moy : {df_class['impact_hybrid'].mean():.1f} pips")
    print()
    
    # 7. Sauvegarder
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_filtered.to_csv(output_dir / 'predictions_hybrid_final.csv', index=False)
    
    final_formula = {
        'formula_type': 'hybrid_linear_corrective',
        'base_formula': 'impact = 30.5450 + 0.4692*base_score + 0.1882*adjusted_score + 0.0201*surprise_avg - 0.0034*surprise_max + 0.7355*n_events',
        'correction_criteria_strong': correction_params['criteria_strong'],
        'correction_factor_strong': correction_params['factor_strong'],
        'correction_criteria_very_strong': correction_params['criteria_very_strong'],
        'correction_factor_very_strong': correction_params['factor_very_strong'],
        'mae': mae_hybrid,
        'median_ratio': ratio_hybrid,
        'correlation': corr_hybrid
    }
    
    pd.DataFrame([final_formula]).to_csv(output_dir / 'final_hybrid_formula.csv', index=False)
    
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
    print("2. Si mouvement FORT (adjusted_score >= 40 OU n_events >= 15) :")
    print(f"   → Multiplier par {correction_params['factor_strong']:.2f}x")
    print()
    print("3. Si mouvement TRÈS_FORT (critères élargis) :")
    print(f"   → Multiplier par {correction_params['factor_very_strong']:.2f}x")
    print()
    print(f"   Performance :")
    print(f"   - MAE : {mae_hybrid:.2f} pips")
    print(f"   - Ratio médian : {ratio_hybrid:.3f}")
    print(f"   - Corrélation : {corr_hybrid:.3f}")
    print()


if __name__ == '__main__':
    main()


