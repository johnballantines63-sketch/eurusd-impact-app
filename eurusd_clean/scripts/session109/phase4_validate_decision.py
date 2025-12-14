"""
SESSION 109 - PHASE 4 : VALIDATION & DÉCISION FINALE
=====================================================

Objectif : Valider les formules trouvées en Phase 3 et décider quelle approche adopter

Étapes :
1. VALIDATION 11.09.2025 (garde-fou méthodologique)
2. Calculer baseline propre par cluster
3. Appliquer formules dynamiques
4. Calculer MAE baseline vs dynamique
5. Tests robustesse (leave-one-out)
6. RECOMMANDATION FINALE

Date : 3 novembre 2025
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR  # Fichiers directement dans session109/
GRAPHS_DIR = BASE_DIR / "graphs"
GRAPHS_DIR.mkdir(exist_ok=True)

def load_phase_results():
    """Charge tous les résultats des phases précédentes"""
    print("📂 Chargement des résultats phases 1-3...")
    
    # Phase 1 : Métriques
    phase1 = pd.read_csv(RESULTS_DIR / "phase1_all_metrics_17dates.csv")
    print(f"✅ Phase 1 : {len(phase1)} dates avec métriques")
    
    # Phase 2 : Corrélations
    phase2 = pd.read_csv(RESULTS_DIR / "phase2_correlation_results_3approaches.csv")
    print(f"✅ Phase 2 : {len(phase2)} combinaisons testées")
    
    # Phase 3 : Top 3
    phase3 = pd.read_csv(RESULTS_DIR / "phase3_top3_combinations.csv")
    print(f"✅ Phase 3 : {len(phase3)} méthodes significatives")
    
    return phase1, phase2, phase3

def validate_reference_case(df):
    """VALIDATION 11.09.2025 - Garde-fou méthodologique"""
    print("\n" + "="*80)
    print("🎯 VALIDATION CAS RÉFÉRENCE 11.09.2025")
    print("="*80)
    
    # Séparer par cluster (ATTENTION : valeurs numériques 1 et 3, pas "C#1" et "C#3")
    df_C1 = df[df['cluster'] == 1].copy()
    df_C3 = df[df['cluster'] == 3].copy()
    
    print(f"\n📁 Debug: {len(df_C1)} dates C#1, {len(df_C3)} dates C#3")
    
    # Check 1 : Baseline C#3
    baseline_C3 = df_C3['amp_optimal'].mean()
    print(f"\n📊 Baseline C#3 calculée : {baseline_C3:.3f}")
    print(f"   Attendu : ~2.5")
    
    deviation_C3 = abs(baseline_C3 - 2.5)
    if deviation_C3 > 0.15:
        print(f"   ❌ ERREUR : Écart {deviation_C3:.3f} > 0.15")
        raise ValueError("Baseline C#3 dévie de la valeur attendue !")
    else:
        print(f"   ✅ OK : Écart {deviation_C3:.3f} < 0.15")
    
    # Check 2 : amp_optimal 11.09
    date_11sept = df[df['date'] == '2025-09-11']
    if len(date_11sept) == 0:
        print("   ⚠️  WARNING : Date 11.09.2025 non trouvée dans dataset")
    else:
        amp_11sept = date_11sept['amp_optimal'].values[0]
        print(f"\n📊 amp_optimal 11.09 : {amp_11sept:.3f}")
        print(f"   Attendu : 2.537")
        
        deviation_11sept = abs(amp_11sept - 2.537)
        if deviation_11sept > 0.1:
            print(f"   ❌ ERREUR : Écart {deviation_11sept:.3f} > 0.1")
            raise ValueError("amp_optimal 11.09 dévie de la valeur attendue !")
        else:
            print(f"   ✅ OK : Écart {deviation_11sept:.3f} < 0.1")
    
    print("\n✅✅✅ VALIDATION 11.09.2025 : TOUTES VÉRIFICATIONS PASSÉES")
    
    return baseline_C3, df_C1, df_C3

def calculate_baselines_by_cluster(df_C1, df_C3):
    """Calcule baseline propre pour chaque cluster"""
    print("\n" + "="*80)
    print("📊 CALCUL BASELINES PAR CLUSTER")
    print("="*80)
    
    baseline_C1 = df_C1['amp_optimal'].mean()
    baseline_C3 = df_C3['amp_optimal'].mean()
    
    print(f"\n🔵 Cluster #1 (Manufacturing, {len(df_C1)} dates) :")
    print(f"   Baseline : {baseline_C1:.3f}")
    print(f"   Min : {df_C1['amp_optimal'].min():.3f}")
    print(f"   Max : {df_C1['amp_optimal'].max():.3f}")
    print(f"   Std : {df_C1['amp_optimal'].std():.3f}")
    
    print(f"\n🔴 Cluster #3 (CPI, {len(df_C3)} dates) :")
    print(f"   Baseline : {baseline_C3:.3f}")
    print(f"   Min : {df_C3['amp_optimal'].min():.3f}")
    print(f"   Max : {df_C3['amp_optimal'].max():.3f}")
    print(f"   Std : {df_C3['amp_optimal'].std():.3f}")
    
    return baseline_C1, baseline_C3

def apply_dynamic_formula_C1(df_C1, baseline_C1):
    """Applique formule dynamique volatility_pips sur C#1"""
    print("\n" + "="*80)
    print("🔬 APPLICATION FORMULE DYNAMIQUE C#1")
    print("="*80)
    
    # Formule Phase 3 : amp = 0.0339 × volatility_pips + 0.5352
    a = 0.0339
    b = 0.5352
    
    print(f"\nFormule : amp = {a:.4f} × volatility_pips + {b:.4f}")
    
    # Appliquer formule
    df_C1 = df_C1.copy()
    df_C1['amp_predicted_dynamic'] = a * df_C1['volatility_pips'] + b
    df_C1['amp_predicted_baseline'] = baseline_C1
    
    # Calculer erreurs
    df_C1['error_dynamic'] = abs(df_C1['amp_optimal'] - df_C1['amp_predicted_dynamic'])
    df_C1['error_baseline'] = abs(df_C1['amp_optimal'] - df_C1['amp_predicted_baseline'])
    
    # Métriques
    mae_dynamic = df_C1['error_dynamic'].mean()
    mae_baseline = df_C1['error_baseline'].mean()
    improvement = ((mae_baseline - mae_dynamic) / mae_baseline) * 100
    
    print(f"\n📊 RÉSULTATS C#1 ({len(df_C1)} dates) :")
    print(f"   MAE Baseline fixe ({baseline_C1:.3f}) : {mae_baseline:.3f}")
    print(f"   MAE Formule dynamique       : {mae_dynamic:.3f}")
    print(f"   Amélioration                : {improvement:+.1f}%")
    
    if improvement > 0:
        print(f"   ✅ Formule dynamique MEILLEURE !")
    else:
        print(f"   ❌ Baseline fixe MEILLEURE")
    
    return df_C1, mae_dynamic, mae_baseline, improvement

def leave_one_out_validation_C1(df_C1):
    """Test robustesse leave-one-out sur C#1"""
    print("\n" + "="*80)
    print("🔄 TEST ROBUSTESSE LEAVE-ONE-OUT C#1")
    print("="*80)
    
    n = len(df_C1)
    errors_loo = []
    
    for i in range(n):
        # Train sur N-1
        train = df_C1.drop(df_C1.index[i])
        test = df_C1.iloc[i]
        
        # Recalculer régression sur train
        X_train = train['volatility_pips'].values
        y_train = train['amp_optimal'].values
        
        slope, intercept, r, p, se = stats.linregress(X_train, y_train)
        
        # Prédire sur test
        pred = slope * test['volatility_pips'] + intercept
        error = abs(test['amp_optimal'] - pred)
        errors_loo.append(error)
    
    mae_loo = np.mean(errors_loo)
    print(f"\n📊 MAE Leave-One-Out : {mae_loo:.3f}")
    print(f"   Stabilité : {'✅ Robuste' if mae_loo < 0.6 else '⚠️ Variable'}")
    
    return mae_loo

def create_final_visualizations(df_C1, baseline_C1):
    """Crée graphiques finaux Phase 4"""
    print("\n" + "="*80)
    print("📊 CRÉATION GRAPHIQUES FINAUX")
    print("="*80)
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Graphique 1 : Prédictions vs Réalité
    ax1 = axes[0]
    ax1.scatter(df_C1['amp_optimal'], df_C1['amp_predicted_dynamic'], 
                color='blue', s=100, alpha=0.7, label='Formule dynamique')
    ax1.scatter(df_C1['amp_optimal'], df_C1['amp_predicted_baseline'], 
                color='red', s=100, alpha=0.7, label='Baseline fixe')
    
    # Ligne parfaite
    min_val = df_C1['amp_optimal'].min() - 0.5
    max_val = df_C1['amp_optimal'].max() + 0.5
    ax1.plot([min_val, max_val], [min_val, max_val], 
             'k--', alpha=0.3, label='Prédiction parfaite')
    
    ax1.set_xlabel('amp_optimal (réel)', fontsize=12)
    ax1.set_ylabel('amp_predicted', fontsize=12)
    ax1.set_title('C#1 : Prédictions vs Réalité', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Graphique 2 : Erreurs par méthode
    ax2 = axes[1]
    x = np.arange(len(df_C1))
    width = 0.35
    
    ax2.bar(x - width/2, df_C1['error_baseline'], width, 
            label='Baseline fixe', color='red', alpha=0.7)
    ax2.bar(x + width/2, df_C1['error_dynamic'], width, 
            label='Formule dynamique', color='blue', alpha=0.7)
    
    ax2.set_xlabel('Date index', fontsize=12)
    ax2.set_ylabel('Erreur absolue', fontsize=12)
    ax2.set_title('C#1 : Comparaison Erreurs', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    output_file = GRAPHS_DIR / "phase4_final_validation_C1.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Graphique sauvegardé : {output_file}")
    plt.close()

def final_recommendation(improvement_C1, mae_dynamic_C1, mae_baseline_C1, baseline_C3):
    """Recommandation finale Phase 4"""
    print("\n" + "="*80)
    print("🎯 RECOMMANDATION FINALE SESSION 109")
    print("="*80)
    
    print("\n📊 RÉSUMÉ COMPLET :")
    print(f"\n🔵 Cluster #1 (Manufacturing) :")
    print(f"   MAE Baseline fixe (1.45)    : {mae_baseline_C1:.3f}")
    print(f"   MAE Formule dynamique       : {mae_dynamic_C1:.3f}")
    print(f"   Amélioration                : {improvement_C1:+.1f}%")
    
    print(f"\n🔴 Cluster #3 (CPI) :")
    print(f"   Baseline fixe               : {baseline_C3:.3f}")
    print(f"   Formule Session 101 (R² 72h): MAE 0.82 pips (validé S107)")
    
    print("\n" + "="*80)
    print("🏆 DÉCISION FINALE")
    print("="*80)
    
    if improvement_C1 > 20:
        print("\n✅✅✅ RECOMMANDATION : ADOPTER FORMULE DYNAMIQUE")
        print("\n📋 Formules à implémenter (Session 110) :")
        print("\n🔵 Cluster #1 (Manufacturing) :")
        print("   amp_C1 = 0.0339 × volatility_pips + 0.5352")
        print(f"   Amélioration : +{improvement_C1:.1f}%")
        
        print("\n🔴 Cluster #3 (CPI) :")
        print("   amp_C3 = 0.5490 × R²_72h + 1.6988")
        print("   Amélioration : +95% (Session 107)")
        
    elif improvement_C1 > 0:
        print("\n⚠️ RECOMMANDATION : MODÉRÉE")
        print(f"\nAmélioration C#1 : +{improvement_C1:.1f}% (modeste)")
        print("\n💡 Options :")
        print("   A. Adopter formule si simplicité OK")
        print("   B. Garder baseline fixe (robustesse)")
        
    else:
        print("\n❌ RECOMMANDATION : GARDER BASELINE FIXE")
        print(f"\nFormule dynamique MOINS bonne que baseline (-{abs(improvement_C1):.1f}%)")
        print("\n📋 Baselines à utiliser (Session 110) :")
        print(f"   C#1 : amp = 1.45 (fixe)")
        print(f"   C#3 : amp = 2.50 (fixe)")
    
    print("\n" + "="*80)
    print("📝 PROCHAINE ÉTAPE : SESSION 110")
    print("="*80)
    print("\n1. Implémenter formules choisies")
    print("2. Tests validation sur nouvelles dates")
    print("3. Intégration Planificateur")
    print("4. Documentation finale")

def main():
    """Fonction principale Phase 4"""
    print("="*80)
    print("SESSION 109 - PHASE 4 : VALIDATION & DÉCISION FINALE")
    print("="*80)
    
    # 1. Charger résultats
    phase1, phase2, phase3 = load_phase_results()
    
    # 2. VALIDATION 11.09.2025
    baseline_C3, df_C1, df_C3 = validate_reference_case(phase1)
    
    # 3. Calculer baselines
    baseline_C1, baseline_C3 = calculate_baselines_by_cluster(df_C1, df_C3)
    
    # 4. Appliquer formule dynamique C#1
    df_C1, mae_dynamic, mae_baseline, improvement = apply_dynamic_formula_C1(df_C1, baseline_C1)
    
    # 5. Test robustesse
    mae_loo = leave_one_out_validation_C1(df_C1)
    
    # 6. Graphiques finaux
    create_final_visualizations(df_C1, baseline_C1)
    
    # 7. Sauvegarder résultats
    output_file = BASE_DIR / "phase4_final_results.csv"
    df_C1.to_csv(output_file, index=False)
    print(f"\n✅ Résultats sauvegardés : {output_file}")
    
    # 8. Recommandation finale
    final_recommendation(improvement, mae_dynamic, mae_baseline, baseline_C3)
    
    print("\n" + "="*80)
    print("✅✅✅ PHASE 4 TERMINÉE")
    print("="*80)

if __name__ == "__main__":
    main()
