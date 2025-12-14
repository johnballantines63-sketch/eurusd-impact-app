#!/usr/bin/env python3
"""
SESSION 109 - PHASE 3 : SELECTION TOP 3
========================================
Analyser resultats Phase 2 et selectionner meilleures combinaisons

1. Identifier significatives (p < 0.05)
2. Analyser robustesse
3. Creer graphiques
4. Calculer formules regression
5. Tester amelioration vs baseline
6. Selectionner TOP 3

Auteur : Andre Valentin
Date : 3 novembre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import warnings
warnings.filterwarnings('ignore')

# Setup
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

print("="*80)
print("SESSION 109 - PHASE 3 : SELECTION TOP 3")
print("="*80)
print()


def create_scatter_plot(df_data, metric, target, title, output_path, cluster_label=None):
    """Cree graphique scatter avec regression"""
    
    X = df_data[metric].values
    y = df_data[target].values
    
    # Regression lineaire
    slope, intercept, r_value, p_value, std_err = linregress(X, y)
    
    # Creer figure
    plt.figure(figsize=(10, 6))
    
    if cluster_label:
        # Colorier par cluster
        colors = ['blue' if c == 3 else 'red' for c in df_data['cluster']]
        plt.scatter(X, y, c=colors, alpha=0.6, s=100)
        plt.legend(['C#3 (CPI)', 'C#1 (Manuf)'], loc='best')
    else:
        plt.scatter(X, y, alpha=0.6, s=100, color='blue')
    
    # Ligne regression
    x_line = np.linspace(X.min(), X.max(), 100)
    y_line = slope * x_line + intercept
    plt.plot(x_line, y_line, 'r--', linewidth=2, label=f'y = {slope:.4f}x + {intercept:.4f}')
    
    # Labels
    plt.xlabel(metric, fontsize=12)
    plt.ylabel(target, fontsize=12)
    plt.title(f'{title}\nR² = {r_value**2:.4f}, p = {p_value:.4f}', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Sauvegarder
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Graphique sauvegarde: {output_path.name}")
    
    return slope, intercept, r_value**2, p_value


def calculate_improvement(df_data, metric, target, baseline_dict=None):
    """
    Calcule amelioration vs baseline fixe.
    
    Si baseline_dict fourni : utilise baseline par cluster
    Sinon : utilise moyenne globale
    """
    X = df_data[metric].values
    y = df_data[target].values
    
    # Regression
    slope, intercept, r_value, p_value, std_err = linregress(X, y)
    
    # Predictions dynamiques
    y_pred_dynamic = slope * X + intercept
    mae_dynamic = np.mean(np.abs(y - y_pred_dynamic))
    
    # Baseline
    if baseline_dict and 'cluster' in df_data.columns:
        # Baseline par cluster
        y_baseline = df_data['cluster'].map(baseline_dict).values
    else:
        # Baseline = moyenne
        y_baseline = np.full_like(y, y.mean())
    
    mae_baseline = np.mean(np.abs(y - y_baseline))
    
    # Amelioration
    improvement_pct = ((mae_baseline - mae_dynamic) / mae_baseline * 100) if mae_baseline > 0 else 0
    
    return {
        'mae_baseline': mae_baseline,
        'mae_dynamic': mae_dynamic,
        'improvement_pct': improvement_pct,
        'formula': f'y = {slope:.4f} * {metric} + {intercept:.4f}'
    }


def main():
    """Script principal Phase 3"""
    
    # Charger resultats Phase 2
    print("="*80)
    print("CHARGEMENT RESULTATS PHASE 2")
    print("="*80)
    
    results_path = project_root / "eurusd_clean" / "scripts" / "session109" / "phase2_correlation_results_3approaches.csv"
    df_results = pd.read_csv(results_path)
    
    print(f"Resultats charges: {len(df_results)} lignes")
    
    # Charger donnees brutes
    data_path = project_root / "eurusd_clean" / "scripts" / "session109" / "phase1_all_metrics_17dates.csv"
    df_data = pd.read_csv(data_path)
    
    print(f"Donnees brutes: {len(df_data)} dates")
    
    # Baselines
    baseline_c3 = 2.5
    baseline_c1 = df_data[df_data['cluster'] == 1]['amp_optimal'].mean()
    baselines = {3: baseline_c3, 1: baseline_c1}
    
    print(f"\nBaselines:")
    print(f"  C#3: {baseline_c3:.4f}")
    print(f"  C#1: {baseline_c1:.4f}")
    
    # Calculer ecarts
    df_data['ecart_baseline'] = df_data.apply(
        lambda row: row['amp_optimal'] - baselines[row['cluster']],
        axis=1
    )
    
    # ========================================================================
    # ETAPE 1 : IDENTIFIER SIGNIFICATIVES (p < 0.05)
    # ========================================================================
    print("\n" + "="*80)
    print("ETAPE 1 : CORRELATIONS SIGNIFICATIVES (p < 0.05)")
    print("="*80)
    
    # Filtrer significatives
    significant = []
    
    for _, row in df_results.iterrows():
        # Spearman significatif
        if not pd.isna(row['spearman_p']) and row['spearman_p'] < 0.05:
            significant.append({
                'approach': row['approach'],
                'metric': row['metric'],
                'method': 'Spearman',
                'value': row['spearman_rho'],
                'p_value': row['spearman_p']
            })
        
        # Pearson significatif
        if not pd.isna(row['pearson_p']) and row['pearson_p'] < 0.05:
            significant.append({
                'approach': row['approach'],
                'metric': row['metric'],
                'method': 'Pearson',
                'value': row['pearson_r'],
                'p_value': row['pearson_p']
            })
        
        # Linear significatif
        if not pd.isna(row['linear_p']) and row['linear_p'] < 0.05:
            significant.append({
                'approach': row['approach'],
                'metric': row['metric'],
                'method': 'Linear',
                'value': row['linear_r2'],
                'p_value': row['linear_p']
            })
    
    df_significant = pd.DataFrame(significant)
    
    if len(df_significant) == 0:
        print("\nAUCUNE correlation significative trouvee (p < 0.05)")
        print("\nAnalyse des meilleures correlations (p < 0.10)...")
        
        # Fallback : p < 0.10
        for _, row in df_results.iterrows():
            if not pd.isna(row['spearman_p']) and row['spearman_p'] < 0.10:
                significant.append({
                    'approach': row['approach'],
                    'metric': row['metric'],
                    'method': 'Spearman',
                    'value': row['spearman_rho'],
                    'p_value': row['spearman_p']
                })
        
        df_significant = pd.DataFrame(significant)
    
    print(f"\n{len(df_significant)} correlations significatives trouvees")
    print(df_significant.to_string(index=False))
    
    # ========================================================================
    # ETAPE 2 : ANALYSE DETAILLEE TOP CANDIDATS
    # ========================================================================
    print("\n" + "="*80)
    print("ETAPE 2 : ANALYSE DETAILLEE")
    print("="*80)
    
    # Creer dossier graphiques
    graphs_dir = project_root / "eurusd_clean" / "scripts" / "session109" / "graphs"
    graphs_dir.mkdir(exist_ok=True)
    
    top_candidates = []
    
    # Analyser chaque correlation significative
    for idx, row in df_significant.iterrows():
        approach = row['approach']
        metric = row['metric']
        method = row['method']
        
        print(f"\n{'='*80}")
        print(f"CANDIDAT #{idx+1}: {metric} ({approach})")
        print(f"Methode: {method}, p-value: {row['p_value']:.4f}")
        print("="*80)
        
        # Preparer donnees selon approche
        if approach == 'Intra_C3':
            df_subset = df_data[df_data['cluster'] == 3].copy()
            target = 'amp_optimal'
            title = f"{metric} vs amp_optimal (Cluster #3)"
        elif approach == 'Intra_C1':
            df_subset = df_data[df_data['cluster'] == 1].copy()
            target = 'amp_optimal'
            title = f"{metric} vs amp_optimal (Cluster #1)"
        else:  # Ecarts_Combined
            df_subset = df_data.copy()
            target = 'ecart_baseline'
            title = f"{metric} vs ecart_baseline (17 dates)"
        
        # Creer graphique
        output_path = graphs_dir / f"scatter_{approach}_{metric}.png"
        
        slope, intercept, r2, p_val = create_scatter_plot(
            df_subset, metric, target, title, output_path,
            cluster_label=(approach == 'Ecarts_Combined')
        )
        
        print(f"\n  Formule: y = {slope:.4f} * {metric} + {intercept:.4f}")
        print(f"  R² = {r2:.4f}, p = {p_val:.4f}")
        
        # Calculer amelioration
        if approach == 'Intra_C1':
            baseline_dict = {1: baseline_c1}
        elif approach == 'Intra_C3':
            baseline_dict = {3: baseline_c3}
        else:
            baseline_dict = baselines
        
        improvement = calculate_improvement(df_subset, metric, target, baseline_dict)
        
        print(f"\n  MAE Baseline: {improvement['mae_baseline']:.4f}")
        print(f"  MAE Dynamic:  {improvement['mae_dynamic']:.4f}")
        print(f"  Amelioration: {improvement['improvement_pct']:+.1f}%")
        
        # Stocker
        top_candidates.append({
            'rank': idx + 1,
            'approach': approach,
            'metric': metric,
            'method': method,
            'r2': r2,
            'p_value': p_val,
            'formula': improvement['formula'],
            'mae_baseline': improvement['mae_baseline'],
            'mae_dynamic': improvement['mae_dynamic'],
            'improvement_pct': improvement['improvement_pct']
        })
    
    # ========================================================================
    # ETAPE 3 : SELECTION TOP 3
    # ========================================================================
    print("\n" + "="*80)
    print("ETAPE 3 : SELECTION TOP 3")
    print("="*80)
    
    df_candidates = pd.DataFrame(top_candidates)
    
    # Trier par p-value puis R²
    df_candidates = df_candidates.sort_values(['p_value', 'r2'], ascending=[True, False])
    
    top3 = df_candidates.head(3)
    
    print("\nTOP 3 COMBINAISONS :")
    print("="*80)
    
    for idx, row in top3.iterrows():
        print(f"\n#{row['rank']}. {row['metric']} ({row['approach']})")
        print(f"   Methode:      {row['method']}")
        print(f"   R²:           {row['r2']:.4f}")
        print(f"   P-value:      {row['p_value']:.4f}")
        print(f"   Formule:      {row['formula']}")
        print(f"   MAE Baseline: {row['mae_baseline']:.4f}")
        print(f"   MAE Dynamic:  {row['mae_dynamic']:.4f}")
        print(f"   Amelioration: {row['improvement_pct']:+.1f}%")
    
    # Sauvegarder
    output_path = project_root / "eurusd_clean" / "scripts" / "session109" / "phase3_top3_combinations.csv"
    top3.to_csv(output_path, index=False)
    
    print(f"\n\nTOP 3 sauvegarde: {output_path}")
    
    # ========================================================================
    # ETAPE 4 : SYNTHESE & RECOMMANDATION
    # ========================================================================
    print("\n" + "="*80)
    print("ETAPE 4 : SYNTHESE & RECOMMANDATION")
    print("="*80)
    
    if len(top3) == 0:
        print("\nAUCUNE correlation significative")
        print("\nRECOMMANDATION : Retour amp par cluster fixe")
        print("  C#3 : amp = 2.5")
        print("  C#1 : amp = 1.5")
    
    else:
        best = top3.iloc[0]
        
        print(f"\nMEILLEURE COMBINAISON : {best['metric']} ({best['approach']})")
        print(f"  R² = {best['r2']:.4f}")
        print(f"  p-value = {best['p_value']:.4f}")
        print(f"  Amelioration = {best['improvement_pct']:+.1f}%")
        
        if best['p_value'] < 0.05 and best['r2'] > 0.3:
            print("\n✅ RECOMMANDATION : Formule dynamique viable")
            print(f"   {best['formula']}")
            
            if best['approach'] == 'Intra_C1':
                print("\n   Applicable : Cluster #1 uniquement")
                print("   Cluster #3 : Garder amp = 2.5 (fixe)")
            elif best['approach'] == 'Intra_C3':
                print("\n   Applicable : Cluster #3 uniquement")
                print("   Cluster #1 : Garder amp = 1.5 (fixe)")
            else:
                print("\n   Applicable : Tous clusters (ajustement ecart)")
        
        elif best['p_value'] < 0.05:
            print("\n⚠️  RECOMMANDATION : Relation significative mais faible")
            print("   Comparer gain vs complexite")
            print("   Alternative : Amp par cluster fixe peut suffire")
        
        else:
            print("\n❌ RECOMMANDATION : Aucune relation significative")
            print("   Retour amp par cluster fixe")
    
    # ========================================================================
    # CONCLUSION
    # ========================================================================
    print("\n" + "="*80)
    print("PHASE 3 TERMINEE")
    print("="*80)
    print(f"Fichiers generes:")
    print(f"  - phase3_top3_combinations.csv")
    print(f"  - graphs/scatter_*.png ({len(df_significant)} graphiques)")
    print()
    print("Prochaine etape: Phase 4 - Validation & Decision finale")


if __name__ == "__main__":
    main()
