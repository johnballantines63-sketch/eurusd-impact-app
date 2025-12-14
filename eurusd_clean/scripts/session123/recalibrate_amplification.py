"""
Re-calibration formule sur cluster 11 septembre

Utilise les 110 cas similaires pour :
1. Optimiser amplification (pas 2.8 fixe)
2. Identifier et filtrer outliers
3. Split train/test (70/30)
4. Valider sur test set

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Re-calibration
"""

import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar

# Fichiers
VALIDATION_FILE = Path(__file__).parent / 'validation_results' / 'cluster_sept11_validation.json'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'


def calculate_mae_for_amplification(amplification: float, train_data: list) -> float:
    """Calculer MAE moyen pour une amplification donnée"""
    
    mae_values = []
    
    for result in train_data:
        # Recalculer predicted avec nouvelle amplification
        # predicted original = total_score * 2.8 / 100
        # On peut retrouver total_score
        predicted_old = result['predicted_impact']
        total_score = predicted_old * 100 / 2.8
        
        # Nouvelle prédiction
        predicted_new = total_score * amplification / 100.0
        
        # MAE
        mae = abs(result['real_amplitude'] - predicted_new)
        mae_values.append(mae)
    
    return np.mean(mae_values)


def main():
    """Re-calibration formule"""
    
    print("=" * 80)
    print("RE-CALIBRATION FORMULE SUR CLUSTER 11 SEPTEMBRE")
    print("=" * 80)
    print()
    
    # Charger résultats
    with open(VALIDATION_FILE, 'r') as f:
        data = json.load(f)
    
    results = data['validation_results']
    
    print(f"📊 Dataset : {len(results)} cas")
    print()
    
    # ========================================================================
    # ÉTAPE 1 : ANALYSER OUTLIERS
    # ========================================================================
    
    print("=" * 80)
    print("ÉTAPE 1 : ANALYSE OUTLIERS")
    print("=" * 80)
    print()
    
    mae_values = [r['mae'] for r in results]
    mae_mean = np.mean(mae_values)
    mae_median = np.median(mae_values)
    mae_std = np.std(mae_values)
    
    print(f"MAE moyen   : {mae_mean:.2f} pips")
    print(f"MAE médian  : {mae_median:.2f} pips")
    print(f"MAE std     : {mae_std:.2f} pips")
    print()
    
    # Identifier outliers (> mean + 2*std)
    threshold = mae_mean + 2 * mae_std
    
    outliers = [r for r in results if r['mae'] > threshold]
    clean = [r for r in results if r['mae'] <= threshold]
    
    print(f"Outliers (MAE > {threshold:.1f}) : {len(outliers)} ({len(outliers)/len(results)*100:.1f}%)")
    print()
    
    if len(outliers) > 0:
        print("TOP 5 OUTLIERS :")
        sorted_outliers = sorted(outliers, key=lambda x: x['mae'], reverse=True)
        for i, r in enumerate(sorted_outliers[:5], 1):
            print(f"   {i}. {r['date']}")
            print(f"      Réel: {r['real_amplitude']:.1f} | Prédit: {r['predicted_impact']:.1f} | MAE: {r['mae']:.1f}")
        print()
    
    print(f"✅ Dataset clean : {len(clean)} cas")
    print()
    
    # Stats sur dataset clean
    if len(clean) > 0:
        mae_clean = [r['mae'] for r in clean]
        print(f"Après filtrage outliers :")
        print(f"   MAE moyen  : {np.mean(mae_clean):.2f} pips")
        print(f"   MAE médian : {np.median(mae_clean):.2f} pips")
        print()
    
    # ========================================================================
    # ÉTAPE 2 : SPLIT TRAIN/TEST
    # ========================================================================
    
    print("=" * 80)
    print("ÉTAPE 2 : SPLIT TRAIN/TEST")
    print("=" * 80)
    print()
    
    # Utiliser dataset clean
    dataset = clean if len(clean) > 10 else results
    
    # Split 70/30
    n_train = int(len(dataset) * 0.7)
    
    # Shuffle pour éviter biais temporel
    np.random.seed(42)
    indices = np.random.permutation(len(dataset))
    
    train_indices = indices[:n_train]
    test_indices = indices[n_train:]
    
    train_data = [dataset[i] for i in train_indices]
    test_data = [dataset[i] for i in test_indices]
    
    print(f"Train set : {len(train_data)} cas (70%)")
    print(f"Test set  : {len(test_data)} cas (30%)")
    print()
    
    # ========================================================================
    # ÉTAPE 3 : OPTIMISER AMPLIFICATION
    # ========================================================================
    
    print("=" * 80)
    print("ÉTAPE 3 : OPTIMISATION AMPLIFICATION")
    print("=" * 80)
    print()
    
    print("🔍 Recherche amplification optimale...")
    print()
    
    # Optimiser sur train set
    result_opt = minimize_scalar(
        lambda amp: calculate_mae_for_amplification(amp, train_data),
        bounds=(0.1, 10.0),
        method='bounded'
    )
    
    optimal_amp = result_opt.x
    mae_train_optimal = result_opt.fun
    
    print(f"✅ Amplification optimale : {optimal_amp:.3f}")
    print(f"   MAE train (optimal)    : {mae_train_optimal:.2f} pips")
    print()
    
    print(f"Comparaison avec amplification 2.8 (Session 115) :")
    mae_train_28 = calculate_mae_for_amplification(2.8, train_data)
    print(f"   MAE train (amp=2.8)    : {mae_train_28:.2f} pips")
    print()
    
    improvement = ((mae_train_28 - mae_train_optimal) / mae_train_28) * 100
    print(f"   Amélioration : {improvement:+.1f}%")
    print()
    
    # ========================================================================
    # ÉTAPE 4 : VALIDATION TEST SET
    # ========================================================================
    
    print("=" * 80)
    print("ÉTAPE 4 : VALIDATION TEST SET")
    print("=" * 80)
    print()
    
    # Calculer MAE sur test set avec amplification optimale
    test_results_optimal = []
    test_results_28 = []
    
    for result in test_data:
        # Retrouver total_score
        predicted_old = result['predicted_impact']
        total_score = predicted_old * 100 / 2.8
        
        # Avec amp optimale
        predicted_optimal = total_score * optimal_amp / 100.0
        mae_optimal = abs(result['real_amplitude'] - predicted_optimal)
        
        # Avec amp 2.8
        mae_28 = result['mae']
        
        test_results_optimal.append(mae_optimal)
        test_results_28.append(mae_28)
    
    mae_test_optimal = np.mean(test_results_optimal)
    mae_test_28 = np.mean(test_results_28)
    
    print(f"TEST SET ({len(test_data)} cas) :")
    print()
    print(f"   Amplification optimale ({optimal_amp:.3f}) :")
    print(f"      MAE moyen  : {mae_test_optimal:.2f} pips")
    print(f"      MAE médian : {np.median(test_results_optimal):.2f} pips")
    print()
    
    print(f"   Amplification 2.8 (Session 115) :")
    print(f"      MAE moyen  : {mae_test_28:.2f} pips")
    print(f"      MAE médian : {np.median(test_results_28):.2f} pips")
    print()
    
    test_improvement = ((mae_test_28 - mae_test_optimal) / mae_test_28) * 100
    print(f"   Amélioration test : {test_improvement:+.1f}%")
    print()
    
    # Distribution
    under_5_optimal = sum(1 for mae in test_results_optimal if mae < 5)
    under_10_optimal = sum(1 for mae in test_results_optimal if mae < 10)
    under_20_optimal = sum(1 for mae in test_results_optimal if mae < 20)
    
    print(f"Distribution MAE (test set, amp optimale) :")
    print(f"   MAE < 5 pips  : {under_5_optimal}/{len(test_data)} ({under_5_optimal/len(test_data)*100:.1f}%)")
    print(f"   MAE < 10 pips : {under_10_optimal}/{len(test_data)} ({under_10_optimal/len(test_data)*100:.1f}%)")
    print(f"   MAE < 20 pips : {under_20_optimal}/{len(test_data)} ({under_20_optimal/len(test_data)*100:.1f}%)")
    print()
    
    # ========================================================================
    # VERDICT
    # ========================================================================
    
    print("=" * 80)
    print("VERDICT RE-CALIBRATION")
    print("=" * 80)
    print()
    
    if mae_test_optimal < 5:
        print("🎉 OBJECTIF ATTEINT : MAE test < 5 pips")
        print(f"   Formule validée avec amplification {optimal_amp:.3f}")
    elif mae_test_optimal < 10:
        print("✅ BON RÉSULTAT : MAE test < 10 pips")
        print(f"   Formule acceptable avec amplification {optimal_amp:.3f}")
    elif mae_test_optimal < 20:
        print("⚠️  RÉSULTAT MOYEN : MAE test < 20 pips")
        print(f"   Amélioration vs 2.8, mais encore éloigné objectif")
    else:
        print("❌ RÉSULTAT INSUFFISANT : MAE test > 20 pips")
        print(f"   Problème plus profond que juste l'amplification")
    
    print()
    
    # ========================================================================
    # ANALYSE LIMITES
    # ========================================================================
    
    print("=" * 80)
    print("ANALYSE LIMITES FORMULE")
    print("=" * 80)
    print()
    
    print("Même après optimisation, MAE reste élevé.")
    print()
    print("LIMITES IDENTIFIÉES :")
    print()
    print("1️⃣ SURPRISE LINÉAIRE INADAPTÉE")
    print("   Formule : impact ∝ |surprise|")
    print("   Problème : Surprise 500% traitée linéairement")
    print("   Solution : Capper surprise ou fonction non-linéaire")
    print()
    
    print("2️⃣ CONTEXTE MARCHÉ IGNORÉ")
    print("   Formule : Ne considère QUE les events")
    print("   Manque : Volatilité jour, sentiment, liquidité")
    print("   Solution : Ajouter facteurs contextuels")
    print()
    
    print("3️⃣ TIMING EVENTS IGNORÉ")
    print("   Formule : Tous events même poids")
    print("   Réalité : Event -1 min ≠ event -30 min")
    print("   Solution : Pondération temporelle")
    print()
    
    print("4️⃣ INTERACTIONS EVENTS IGNORÉES")
    print("   Formule : Somme simple des scores")
    print("   Réalité : Synergie/annulation entre events")
    print("   Solution : Matrice interaction ou ML")
    print()
    
    # Sauvegarder
    output = {
        'dataset_size': len(results),
        'outliers_filtered': len(outliers),
        'train_size': len(train_data),
        'test_size': len(test_data),
        'optimal_amplification': float(optimal_amp),
        'mae_train_optimal': float(mae_train_optimal),
        'mae_test_optimal': float(mae_test_optimal),
        'mae_test_baseline': float(mae_test_28),
        'improvement_pct': float(test_improvement)
    }
    
    output_file = OUTPUT_DIR / 'recalibration_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Résultats : {output_file}")
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
