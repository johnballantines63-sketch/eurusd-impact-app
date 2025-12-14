"""
Analyse Relation core_score ↔ Impact Réel

Objectif : Déterminer si la relation est :
1. Linéaire et constante → Facteur de calibration
2. Non-linéaire ou contextuelle → Feature Random Forest

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

def analyze_relation_core_score_impact():
    """Analyser la relation entre core_score et impact réel"""
    
    print("="*100)
    print("ANALYSE RELATION core_score ↔ Impact Réel")
    print("="*100)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Vérifier si table existe
    try:
        count = conn.execute("SELECT COUNT(*) FROM core_scores_by_date").fetchone()[0]
        if count == 0:
            print("❌ Table core_scores_by_date vide")
            print("   Exécutez d'abord : python creer_table_core_scores_by_date.py --populate")
            conn.close()
            return
    except:
        print("❌ Table core_scores_by_date n'existe pas")
        print("   Exécutez d'abord : python creer_table_core_scores_by_date.py --create --populate")
        conn.close()
        return
    
    # Charger données
    query = """
    SELECT 
        core_type,
        country,
        empirical_score as core_score,
        impact_real,
        ratio,
        n_core_events
    FROM core_scores_by_date
    WHERE impact_real IS NOT NULL
      AND empirical_score IS NOT NULL
      AND empirical_score > 0
    ORDER BY core_type, country
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    if df.empty:
        print("❌ Aucune donnée disponible")
        return
    
    print(f"📊 {len(df)} enregistrements analysés")
    print()
    
    # Analyse globale
    print("="*100)
    print("ANALYSE GLOBALE")
    print("="*100)
    print()
    
    # Corrélation
    correlation = df['core_score'].corr(df['impact_real'])
    print(f"Corrélation core_score ↔ impact_real : {correlation:.3f}")
    
    # Régression linéaire simple
    X = df[['core_score']].values
    y = df['impact_real'].values
    
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    print(f"R² (linéaire) : {r2:.3f}")
    print(f"MAE (linéaire) : {mae:.2f} pips")
    print(f"Coefficient : {model.coef_[0]:.3f}")
    print(f"Intercept : {model.intercept_:.2f}")
    print()
    
    # Test de linéarité (test de Pearson)
    pearson_r, pearson_p = stats.pearsonr(df['core_score'], df['impact_real'])
    print(f"Test Pearson : r={pearson_r:.3f}, p-value={pearson_p:.4f}")
    if pearson_p < 0.05:
        print("✅ Relation linéaire significative (p < 0.05)")
    else:
        print("❌ Relation linéaire non significative (p >= 0.05)")
    print()
    
    # Analyse par core_type
    print("="*100)
    print("ANALYSE PAR CORE TYPE")
    print("="*100)
    print()
    
    results_by_type = []
    
    for core_type in df['core_type'].unique():
        df_type = df[df['core_type'] == core_type].copy()
        
        if len(df_type) < 3:
            continue
        
        # Corrélation
        corr = df_type['core_score'].corr(df_type['impact_real'])
        
        # Régression linéaire
        X_type = df_type[['core_score']].values
        y_type = df_type['impact_real'].values
        
        model_type = LinearRegression()
        model_type.fit(X_type, y_type)
        y_pred_type = model_type.predict(X_type)
        
        r2_type = r2_score(y_type, y_pred_type)
        mae_type = mean_absolute_error(y_type, y_pred_type)
        
        # Ratio moyen
        ratio_mean = df_type['ratio'].mean()
        ratio_std = df_type['ratio'].std()
        
        results_by_type.append({
            'core_type': core_type,
            'n': len(df_type),
            'correlation': corr,
            'r2': r2_type,
            'mae': mae_type,
            'coefficient': model_type.coef_[0],
            'intercept': model_type.intercept_,
            'ratio_mean': ratio_mean,
            'ratio_std': ratio_std
        })
        
        print(f"{core_type}:")
        print(f"  N : {len(df_type)}")
        print(f"  Corrélation : {corr:.3f}")
        print(f"  R² : {r2_type:.3f}")
        print(f"  MAE : {mae_type:.2f} pips")
        print(f"  Coefficient : {model_type.coef_[0]:.3f}")
        print(f"  Ratio moyen : {ratio_mean:.3f} ± {ratio_std:.3f}")
        print()
    
    # Analyse de variance du ratio
    print("="*100)
    print("ANALYSE VARIANCE DU RATIO")
    print("="*100)
    print()
    
    df_results = pd.DataFrame(results_by_type)
    
    # Coefficient de variation (CV) = std / mean
    df_results['cv'] = df_results['ratio_std'] / df_results['ratio_mean']
    
    print(f"{'Core Type':<20} {'N':<6} {'Ratio Moyen':<12} {'Ratio Std':<12} {'CV':<10} {'R²':<8}")
    print("-"*80)
    
    for _, row in df_results.iterrows():
        print(f"{row['core_type']:<20} {row['n']:<6} {row['ratio_mean']:>11.3f} {row['ratio_std']:>11.3f} {row['cv']:>9.3f} {row['r2']:>7.3f}")
    
    print()
    
    # Interprétation
    print("="*100)
    print("INTERPRÉTATION")
    print("="*100)
    print()
    
    # Si CV < 0.3 → Ratio stable → Facteur de calibration
    # Si CV > 0.3 → Ratio variable → Feature RF
    stable_ratios = df_results[df_results['cv'] < 0.3]
    variable_ratios = df_results[df_results['cv'] >= 0.3]
    
    print("Ratios stables (CV < 0.3) → Facteur de calibration approprié :")
    if not stable_ratios.empty:
        for _, row in stable_ratios.iterrows():
            print(f"  ✅ {row['core_type']} : CV={row['cv']:.3f}, Ratio={row['ratio_mean']:.3f}")
    else:
        print("  Aucun")
    print()
    
    print("Ratios variables (CV >= 0.3) → Feature RF approprié :")
    if not variable_ratios.empty:
        for _, row in variable_ratios.iterrows():
            print(f"  ⚠️  {row['core_type']} : CV={row['cv']:.3f}, Ratio={row['ratio_mean']:.3f}")
    else:
        print("  Aucun")
    print()
    
    # Analyse R²
    high_r2 = df_results[df_results['r2'] > 0.5]
    low_r2 = df_results[df_results['r2'] <= 0.5]
    
    print("R² élevé (> 0.5) → Relation linéaire forte → Facteur de calibration :")
    if not high_r2.empty:
        for _, row in high_r2.iterrows():
            print(f"  ✅ {row['core_type']} : R²={row['r2']:.3f}")
    else:
        print("  Aucun")
    print()
    
    print("R² faible (<= 0.5) → Relation non-linéaire → Feature RF :")
    if not low_r2.empty:
        for _, row in low_r2.iterrows():
            print(f"  ⚠️  {row['core_type']} : R²={row['r2']:.3f}")
    else:
        print("  Aucun")
    print()
    
    # Recommandation finale
    print("="*100)
    print("RECOMMANDATION")
    print("="*100)
    print()
    
    # Critères pour facteur de calibration :
    # 1. CV < 0.3 (ratio stable)
    # 2. R² > 0.5 (relation linéaire forte)
    # 3. Corrélation > 0.5
    
    calibration_candidates = df_results[
        (df_results['cv'] < 0.3) & 
        (df_results['r2'] > 0.5) & 
        (df_results['correlation'] > 0.5)
    ]
    
    rf_candidates = df_results[
        (df_results['cv'] >= 0.3) | 
        (df_results['r2'] <= 0.5) | 
        (df_results['correlation'] <= 0.5)
    ]
    
    if len(calibration_candidates) > len(rf_candidates):
        print("✅ RECOMMANDATION : Facteur de calibration")
        print()
        print("Raisons :")
        print("  - Ratios stables (CV < 0.3)")
        print("  - Relation linéaire forte (R² > 0.5)")
        print("  - Corrélation élevée (> 0.5)")
        print()
        print("Implémentation :")
        print("  impact_predicted = (impact_base * amplification) * ratio_mean")
    else:
        print("✅ RECOMMANDATION : Feature Random Forest")
        print()
        print("Raisons :")
        print("  - Ratios variables (CV >= 0.3)")
        print("  - Relation non-linéaire (R² <= 0.5)")
        print("  - Corrélation faible (<= 0.5)")
        print()
        print("Implémentation :")
        print("  features = [impact_base, amplification, core_score, ...]")
        print("  RF apprend la relation non-linéaire")
    
    print()
    
    # Sauvegarder résultats
    output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'analyse_relation_core_score_impact.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_file, index=False)
    
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()
    
    print("="*100)
    print("ANALYSE TERMINÉE")
    print("="*100)

if __name__ == '__main__':
    analyze_relation_core_score_impact()




