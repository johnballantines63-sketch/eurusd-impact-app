#!/usr/bin/env python3
"""
Prédiction Classe de Mouvement + Correction Formule

Objectif :
1. PRÉDIRE la classe de mouvement (FORT/TRÈS_FORT/MOYEN/FAIBLE) AVANT le mouvement
   basé uniquement sur les événements/cluster (features prédictives)
2. Appliquer la formule d'amplification appropriée selon la classe PRÉDITE
3. Comparer avec la réalité (classes connues) pour valider

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler

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


def extract_predictive_features(row: pd.Series) -> Dict:
    """
    Extrait features prédictives (calculables AVANT le mouvement)
    """
    return {
        'base_empirical_score': row['avg_base_empirical_score'],
        'adjusted_empirical_score': row['avg_adjusted_empirical_score'],
        'avg_surprise_pct': row['avg_surprise_pct'],
        'max_surprise_pct': row['max_surprise_pct'],
        'surprise_net': row['surprise_net'],
        'n_events_total': row['n_events_total'],
        'n_events_us': row['n_events_us'],
        'n_events_eu': row['n_events_eu'],
        'n_events_high': row['n_events_high'],
        'n_events_medium': row['n_events_medium'],
        'n_events_low': row['n_events_low'],
        'n_core_events': row['n_core_events'],
        'ratio_high_events': row['n_events_high'] / row['n_events_total'] if row['n_events_total'] > 0 else 0.0,
        'ratio_us_events': row['n_events_us'] / row['n_events_total'] if row['n_events_total'] > 0 else 0.0,
        'ratio_core_events': row['n_core_events'] / row['n_events_total'] if row['n_events_total'] > 0 else 0.0,
    }


def calculate_base_prediction(row: pd.Series) -> float:
    """
    Calcule la prédiction de base (sans correction classe)
    """
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
    
    impact_predicted = calculate_impact_d(
        empirical_score=empirical_score,
        num_events=num_events,
        amplification=amplification,
        correction_factor=0.758
    )
    
    return impact_predicted


def train_movement_classifier(df_features: pd.DataFrame, df_labels: pd.Series) -> Tuple:
    """
    Entraîne un classifieur pour prédire la classe de mouvement
    """
    # Préparer données
    X = df_features.fillna(0)
    y = df_labels
    
    # Standardiser
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Tester plusieurs classifieurs
    classifiers = {
        'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10),
        'GradientBoosting': GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
    }
    
    best_classifier = None
    best_score = 0.0
    best_name = None
    
    for name, clf in classifiers.items():
        clf.fit(X_train, y_train)
        score = clf.score(X_test, y_test)
        
        if score > best_score:
            best_score = score
            best_classifier = clf
            best_name = name
    
    # Réentraîner sur toutes les données
    best_classifier.fit(X_scaled, y)
    
    # Évaluer
    y_pred = best_classifier.predict(X_scaled)
    accuracy = accuracy_score(y, y_pred)
    
    return best_classifier, scaler, best_name, accuracy


def find_optimal_multipliers_by_class(df: pd.DataFrame) -> Dict:
    """
    Trouve les multiplicateurs optimaux pour chaque classe de mouvement
    """
    multipliers = {}
    
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df[df['movement_class'] == movement_class].copy()
        
        if len(df_class) == 0:
            continue
        
        # Optimiser multiplier pour cette classe
        best_mult = 1.0
        best_mae = float('inf')
        
        for mult in np.arange(0.5, 10.0, 0.1):
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
    """
    Fonction principale
    """
    
    print("=" * 80)
    print("PRÉDICTION CLASSE MOUVEMENT + CORRECTION FORMULE")
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
    
    # 3. Extraire features prédictives
    print("📊 ÉTAPE 2 : Extraction features prédictives")
    print("-" * 80)
    
    features_list = []
    for idx, row in df_filtered.iterrows():
        features = extract_predictive_features(row)
        features_list.append(features)
    
    df_features = pd.DataFrame(features_list)
    df_labels = df_filtered['movement_class']
    
    print(f"✅ {len(df_features.columns)} features extraites")
    print()
    
    # 4. Entraîner classifieur
    print("📊 ÉTAPE 3 : Entraînement classifieur de classe")
    print("-" * 80)
    
    classifier, scaler, classifier_name, accuracy = train_movement_classifier(df_features, df_labels)
    
    print(f"✅ Classifieur : {classifier_name}")
    print(f"   Précision globale : {accuracy:.1%}")
    print()
    
    # Prédire classes
    X_scaled = scaler.transform(df_features.fillna(0))
    predicted_classes = classifier.predict(X_scaled)
    df_filtered['movement_class_predicted'] = predicted_classes
    
    # Statistiques prédiction
    print("📊 Précision par classe :")
    from sklearn.metrics import classification_report
    print(classification_report(df_labels, predicted_classes))
    print()
    
    # 5. Trouver multiplicateurs optimaux par classe RÉELLE
    print("📊 ÉTAPE 4 : Optimisation multiplicateurs par classe RÉELLE")
    print("-" * 80)
    
    multipliers_real = find_optimal_multipliers_by_class(df_filtered)
    
    print("Multiplicateurs optimaux (basés sur classes RÉELLES) :")
    for movement_class, stats in multipliers_real.items():
        print(f"   {movement_class:12s} : {stats['multiplier']:>5.2f}x (MAE: {stats['mae']:.2f} pips, {stats['n_samples']:3d} échantillons)")
    print()
    
    # 6. Appliquer corrections selon classe PRÉDITE
    print("📊 ÉTAPE 5 : Application corrections selon classe PRÉDITE")
    print("-" * 80)
    
    # Créer mapping multiplicateurs
    mult_map = {cls: stats['multiplier'] for cls, stats in multipliers_real.items()}
    
    # Appliquer selon classe prédite
    impacts_corrected_predicted = []
    for idx, row in df_filtered.iterrows():
        pred_class = row['movement_class_predicted']
        multiplier = mult_map.get(pred_class, 1.0)
        impact_corrected = row['impact_base'] * multiplier
        impacts_corrected_predicted.append(impact_corrected)
    
    df_filtered['impact_corrected_predicted'] = impacts_corrected_predicted
    
    # Comparer avec correction selon classe RÉELLE (pour référence)
    impacts_corrected_real = []
    for idx, row in df_filtered.iterrows():
        real_class = row['movement_class']
        multiplier = mult_map.get(real_class, 1.0)
        impact_corrected = row['impact_base'] * multiplier
        impacts_corrected_real.append(impact_corrected)
    
    df_filtered['impact_corrected_real'] = impacts_corrected_real
    
    # 7. Comparer résultats
    print("📊 ÉTAPE 6 : Comparaison résultats")
    print("-" * 80)
    print()
    
    # Base (sans correction)
    mae_base = np.mean(np.abs(df_filtered['impact_base'] - df_filtered['peak_pips']))
    ratio_base = np.median(df_filtered['impact_base'] / df_filtered['peak_pips'])
    corr_base = np.corrcoef(df_filtered['impact_base'], df_filtered['peak_pips'])[0, 1]
    
    # Correction selon classe PRÉDITE
    mae_predicted = np.mean(np.abs(df_filtered['impact_corrected_predicted'] - df_filtered['peak_pips']))
    ratio_predicted = np.median(df_filtered['impact_corrected_predicted'] / df_filtered['peak_pips'])
    corr_predicted = np.corrcoef(df_filtered['impact_corrected_predicted'], df_filtered['peak_pips'])[0, 1]
    
    # Correction selon classe RÉELLE (référence idéale)
    mae_real = np.mean(np.abs(df_filtered['impact_corrected_real'] - df_filtered['peak_pips']))
    ratio_real = np.median(df_filtered['impact_corrected_real'] / df_filtered['peak_pips'])
    corr_real = np.corrcoef(df_filtered['impact_corrected_real'], df_filtered['peak_pips'])[0, 1]
    
    print(f"{'Méthode':<40} {'MAE':<12} {'Ratio médian':<15} {'Corrélation':<15}")
    print("-" * 82)
    print(f"{'Base (sans correction)':<40} {mae_base:>10.2f}   {ratio_base:>13.3f}   {corr_base:>13.3f}")
    print(f"{'Correction classe PRÉDITE':<40} {mae_predicted:>10.2f}   {ratio_predicted:>13.3f}   {corr_predicted:>13.3f}")
    print(f"{'Correction classe RÉELLE (réf)':<40} {mae_real:>10.2f}   {ratio_real:>13.3f}   {corr_real:>13.3f}")
    print()
    
    # Analyse par classe
    print("📊 Analyse par classe (correction selon classe PRÉDITE) :")
    print()
    for movement_class in ['FAIBLE', 'MOYEN', 'FORT', 'TRÈS_FORT']:
        df_class = df_filtered[df_filtered['movement_class'] == movement_class]
        if len(df_class) > 0:
            # Prédictions correctes
            correct_predictions = (df_class['movement_class_predicted'] == movement_class).sum()
            accuracy_class = correct_predictions / len(df_class) * 100
            
            # MAE pour cette classe
            mae_class = np.mean(np.abs(df_class['impact_corrected_predicted'] - df_class['peak_pips']))
            ratio_class = np.median(df_class['impact_corrected_predicted'] / df_class['peak_pips'])
            
            print(f"   {movement_class:12s} ({len(df_class):3d} mouvements) :")
            print(f"      Précision classification : {accuracy_class:.1f}% ({correct_predictions}/{len(df_class)})")
            print(f"      MAE après correction     : {mae_class:.2f} pips")
            print(f"      Ratio médian              : {ratio_class:.3f}")
    print()
    
    # 8. Sauvegarder résultats
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder données complètes
    df_filtered.to_csv(output_dir / 'predictions_with_class_correction.csv', index=False)
    
    # Sauvegarder multiplicateurs
    df_mult = pd.DataFrame([
        {'movement_class': cls, **stats} 
        for cls, stats in multipliers_real.items()
    ])
    df_mult.to_csv(output_dir / 'optimal_multipliers_by_class.csv', index=False)
    
    # Sauvegarder résultats comparaison
    comparison = {
        'method': ['Base', 'Classe prédite', 'Classe réelle'],
        'mae': [mae_base, mae_predicted, mae_real],
        'median_ratio': [ratio_base, ratio_predicted, ratio_real],
        'correlation': [corr_base, corr_predicted, corr_real]
    }
    pd.DataFrame(comparison).to_csv(output_dir / 'comparison_class_correction.csv', index=False)
    
    print(f"💾 Fichiers sauvegardés dans : {output_dir}")
    print()
    
    print("=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)
    print()
    print("💡 CONCLUSION :")
    print(f"   - Précision classification : {accuracy:.1%}")
    print(f"   - MAE avec correction prédite : {mae_predicted:.2f} pips")
    print(f"   - MAE avec correction réelle (réf) : {mae_real:.2f} pips")
    print(f"   - Amélioration vs base : {(mae_base - mae_predicted) / mae_base * 100:.1f}%")
    print()


if __name__ == '__main__':
    main()


