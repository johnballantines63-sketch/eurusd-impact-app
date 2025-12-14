"""
STEP 5 : LOO-CV VALIDATION (Leave-One-Out Cross-Validation)
============================================================

Session 139 - 14 novembre 2025
Objectif : Valider la précision des prédictions par groupe avec LOO-CV

MÉTHODE LOO-CV :
1. Pour chaque groupe (pattern_type, score_range)
2. Pour chaque mouvement dans le groupe :
   - Retirer ce mouvement (test)
   - Calculer moyenne sur N-1 mouvements restants (train)
   - Prédire le mouvement retiré = moyenne train
   - Calculer erreur absolue
3. Calculer MAE (Mean Absolute Error) par groupe
4. Identifier groupes nécessitant optimisation

CRITÈRE SUCCÈS :
- MAE < 20 pips par groupe = Excellent
- MAE < 30 pips par groupe = Acceptable
- MAE > 30 pips = Nécessite optimisation

ENTRÉE :
- step3_movements_with_patterns_v2.csv (396 mouvements avec patterns)
- step4_pattern_groups_v2.csv (23 groupes validés)

SORTIE :
- step5_loocv_results.csv (résultats par groupe)
- Rapport détaillé performance
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error

# ============================================================================
# CONFIGURATION
# ============================================================================

MOVEMENTS_FILE = Path(__file__).parent.parent / "session137" / "step3_movements_with_patterns_v2.csv"
GROUPS_FILE = Path(__file__).parent / "step4_pattern_groups_v2.csv"
OUTPUT_FILE = Path(__file__).parent / "step5_loocv_results.csv"

MAE_EXCELLENT = 20.0  # pips
MAE_ACCEPTABLE = 30.0  # pips

# ============================================================================
# FONCTIONS
# ============================================================================

def load_data():
    """Charge les données."""
    print(f"📂 Chargement données...")
    
    movements = pd.read_csv(MOVEMENTS_FILE)
    groups = pd.read_csv(GROUPS_FILE)
    
    print(f"✅ {len(movements)} mouvements chargés")
    print(f"✅ {len(groups)} groupes chargés")
    
    return movements, groups

def perform_loocv_group(group_movements):
    """
    Effectue LOO-CV sur un groupe de mouvements.
    
    Retourne : (predictions, actuals, errors)
    """
    n = len(group_movements)
    predictions = []
    actuals = []
    errors = []
    
    for i in range(n):
        # Retirer le mouvement i (test)
        test_movement = group_movements.iloc[i]
        train_movements = group_movements.drop(group_movements.index[i])
        
        # Prédiction = moyenne des mouvements train
        prediction = train_movements['impact_pips'].mean()
        actual = test_movement['impact_pips']
        error = abs(prediction - actual)
        
        predictions.append(prediction)
        actuals.append(actual)
        errors.append(error)
    
    return predictions, actuals, errors

def analyze_loocv_results(movements, groups):
    """Analyse LOO-CV pour tous les groupes."""
    print("\n" + "="*80)
    print("🔧 ANALYSE LOO-CV PAR GROUPE")
    print("="*80)
    
    results = []
    
    for idx, group in groups.iterrows():
        pattern = group['pattern_type']
        score_range = group['score_range']
        
        # Filtrer mouvements du groupe
        mask = (movements['pattern_type'] == pattern) & \
               (movements['score_range'] == score_range)
        group_movements = movements[mask].copy()
        
        if len(group_movements) < 3:
            continue
        
        # Effectuer LOO-CV
        predictions, actuals, errors = perform_loocv_group(group_movements)
        
        # Calculer métriques
        mae = np.mean(errors)
        std_error = np.std(errors)
        max_error = np.max(errors)
        min_error = np.min(errors)
        
        # Déterminer statut
        if mae < MAE_EXCELLENT:
            status = "EXCELLENT"
        elif mae < MAE_ACCEPTABLE:
            status = "ACCEPTABLE"
        else:
            status = "À_OPTIMISER"
        
        # Stocker résultats
        result = {
            'pattern_type': pattern,
            'score_range': score_range,
            'n_cases': len(group_movements),
            'mean_actual': np.mean(actuals),
            'std_actual': np.std(actuals),
            'mean_predicted': np.mean(predictions),
            'mae': mae,
            'std_error': std_error,
            'min_error': min_error,
            'max_error': max_error,
            'status': status
        }
        results.append(result)
        
        # Afficher progression
        print(f"  ✓ {pattern:35s} | {score_range:10s} | MAE={mae:5.1f} pips | {status}")
    
    return pd.DataFrame(results)

def display_summary(results):
    """Affiche résumé des résultats."""
    print("\n" + "="*80)
    print("📊 RÉSUMÉ GLOBAL LOO-CV")
    print("="*80)
    
    # Statistiques globales
    total_cases = results['n_cases'].sum()
    mean_mae = results['mae'].mean()
    median_mae = results['mae'].median()
    
    print(f"\n📈 Statistiques globales :")
    print(f"  • Total groupes analysés : {len(results)}")
    print(f"  • Total cas couverts     : {total_cases}")
    print(f"  • MAE moyenne (tous groupes) : {mean_mae:.2f} pips")
    print(f"  • MAE médiane (tous groupes) : {median_mae:.2f} pips")
    
    # Distribution par statut
    print(f"\n📊 Distribution par statut :")
    status_counts = results['status'].value_counts()
    for status in ['EXCELLENT', 'ACCEPTABLE', 'À_OPTIMISER']:
        count = status_counts.get(status, 0)
        pct = (count / len(results)) * 100 if len(results) > 0 else 0
        cases = results[results['status'] == status]['n_cases'].sum()
        print(f"  • {status:15s} : {count:2d} groupes ({pct:5.1f}%) | {cases:3d} cas")
    
    # Top 10 meilleurs groupes
    print(f"\n🏆 TOP 10 MEILLEURS GROUPES (MAE le plus faible) :")
    top10 = results.nsmallest(10, 'mae')
    for i, (idx, row) in enumerate(top10.iterrows(), 1):
        print(f"  {i:2d}. {row['pattern_type']:35s} | {row['score_range']:10s} | "
              f"MAE={row['mae']:5.1f} pips | n={row['n_cases']:2d}")
    
    # Top 10 pires groupes
    print(f"\n⚠️  TOP 10 PIRES GROUPES (MAE le plus élevé) :")
    bottom10 = results.nlargest(10, 'mae')
    for i, (idx, row) in enumerate(bottom10.iterrows(), 1):
        print(f"  {i:2d}. {row['pattern_type']:35s} | {row['score_range']:10s} | "
              f"MAE={row['mae']:5.1f} pips | n={row['n_cases']:2d} | {row['status']}")

def save_results(results):
    """Sauvegarde les résultats."""
    print(f"\n💾 Sauvegarde résultats...")
    
    # Trier par MAE
    results_sorted = results.sort_values('mae')
    
    # Exporter
    results_sorted.to_csv(OUTPUT_FILE, index=False)
    
    print(f"✅ Résultats sauvegardés : {OUTPUT_FILE}")

def create_movements_with_loocv(movements, results):
    """Crée un fichier avec prédictions LOO-CV pour chaque mouvement."""
    print(f"\n🔧 Création fichier mouvements avec prédictions LOO-CV...")
    
    # Ajouter colonne pour prédiction LOO-CV
    movements['loocv_prediction'] = np.nan
    movements['loocv_error'] = np.nan
    
    for idx, group_result in results.iterrows():
        pattern = group_result['pattern_type']
        score_range = group_result['score_range']
        
        # Filtrer mouvements du groupe
        mask = (movements['pattern_type'] == pattern) & \
               (movements['score_range'] == score_range)
        group_movements = movements[mask].copy()
        
        if len(group_movements) < 3:
            continue
        
        # Effectuer LOO-CV
        predictions, actuals, errors = perform_loocv_group(group_movements)
        
        # Assigner prédictions
        movements.loc[mask, 'loocv_prediction'] = predictions
        movements.loc[mask, 'loocv_error'] = errors
    
    # Sauvegarder
    output_movements = Path(__file__).parent / "step5_movements_with_loocv.csv"
    movements.to_csv(output_movements, index=False)
    
    print(f"✅ Fichier créé : {output_movements}")
    
    return movements

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Fonction principale."""
    print("="*80)
    print("STEP 5 : LOO-CV VALIDATION")
    print("="*80)
    
    # 1. Charger données
    movements, groups = load_data()
    
    # Ajouter score_range aux mouvements
    def assign_score_range(score):
        if score < 100: return "0-100"
        elif score < 200: return "100-200"
        elif score < 300: return "200-300"
        elif score < 400: return "300-400"
        elif score < 500: return "400-500"
        else: return "500+"
    
    movements['score_range'] = movements['total_score'].apply(assign_score_range)
    
    # 2. Analyser LOO-CV
    results = analyze_loocv_results(movements, groups)
    
    # 3. Afficher résumé
    display_summary(results)
    
    # 4. Sauvegarder résultats
    save_results(results)
    
    # 5. Créer fichier avec prédictions
    movements_with_loocv = create_movements_with_loocv(movements, results)
    
    print("\n" + "="*80)
    print("✅ STEP 5 LOO-CV TERMINÉ")
    print("="*80)
    print(f"\n📁 Fichiers créés :")
    print(f"  • {OUTPUT_FILE}")
    print(f"  • step5_movements_with_loocv.csv")
    print(f"\n📊 Prochaine étape : Analyse des groupes À_OPTIMISER")

if __name__ == "__main__":
    main()
