"""
SESSION 142 - PHASE 4 : VALIDATION GLOBALE
==========================================

Objectif : Valider gains sur MAE global (396 mouvements)

Méthodologie :
1. Charger tous les mouvements
2. Appliquer optimisations (médiane pour DOUBLE_WAVE_UP 300-400)
3. Re-calculer MAE global
4. Comparer vs baseline 14.94 pips (Session 141)
5. Vérifier stabilité groupes EXCELLENT

Date : 16 novembre 2025
Auteur : André Valentin avec Claude
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_FILE = Path(__file__).parent.parent / "session137" / "step3_movements_with_patterns_v2.csv"
OUTPUT_DIR = Path(__file__).parent
OUTPUT_RESULTS = OUTPUT_DIR / "phase4_validation_globale.json"

# Optimisations appliquées
OPTIMIZATIONS = {
    "DOUBLE_WAVE_UP_300_400": {
        "method": "median",
        "mae_before": 29.79,
        "mae_after": 23.76,
        "gain": -6.03
    },
    "DOUBLE_WAVE_DOWN_300_400": {
        "method": "mean",  # Pas d'amélioration possible
        "mae_before": 26.66,
        "mae_after": 26.66,
        "gain": 0.0
    }
}

# Baseline Session 141
BASELINE_MAE_GLOBAL = 14.94

# ============================================================================
# FONCTIONS
# ============================================================================

def load_movements() -> pd.DataFrame:
    """Charge les mouvements avec patterns."""
    print(f"📂 Chargement : {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'], utc=True)
    print(f"✅ {len(df)} mouvements chargés")
    return df

def assign_score_range(score: float) -> str:
    """Assigne un score à une range."""
    if score < 100:
        return "0-100"
    elif score < 200:
        return "100-200"
    elif score < 300:
        return "200-300"
    elif score < 400:
        return "300-400"
    elif score < 500:
        return "400-500"
    else:
        return "500+"

def create_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Crée les groupes (pattern_type, score_range)."""
    df = df.copy()
    df['score_range'] = df['total_score'].apply(assign_score_range)
    return df

def perform_loocv_group(group_df: pd.DataFrame, use_median: bool = False) -> Dict:
    """Effectue LOO-CV sur un groupe."""
    n = len(group_df)
    if n == 0:
        return {"mae": 0.0, "errors": [], "count": 0}
    
    # Si moins de 2 cas, impossible de faire LOO-CV
    if n < 2:
        return {"mae": 0.0, "errors": [], "count": n, "skipped": True}
    
    errors = []
    
    for i in range(n):
        # Retirer cas i
        train_df = group_df.drop(group_df.index[i])
        test_row = group_df.iloc[i]
        
        # Prédiction selon méthode
        if use_median:
            prediction = float(train_df['impact_pips'].median())
        else:
            prediction = float(train_df['impact_pips'].mean())
        
        actual = float(test_row['impact_pips'])
        error = abs(actual - prediction)
        errors.append(error)
    
    mae = float(np.mean(errors)) if errors else 0.0
    
    return {
        "mae": mae,
        "errors": errors,
        "count": n,
        "skipped": False
    }

def calculate_global_mae(df: pd.DataFrame) -> Dict:
    """Calcule MAE global avec optimisations."""
    print("\n" + "=" * 80)
    print("CALCUL MAE GLOBAL AVEC OPTIMISATIONS")
    print("=" * 80)
    
    groups = df.groupby(['pattern_type', 'score_range'])
    all_errors = []
    group_results = []
    
    for (pattern, score_range), group_df in groups:
        # Vérifier si optimisation appliquée
        use_median = False
        if pattern == "DOUBLE_WAVE_UP" and score_range == "300-400":
            use_median = True
            print(f"\n✅ {pattern} {score_range}: Utilisation MÉDIANE (optimisé)")
        elif pattern == "DOUBLE_WAVE_DOWN" and score_range == "300-400":
            print(f"\n⚠️  {pattern} {score_range}: Utilisation MOYENNE (pas d'amélioration possible)")
        
        # LOO-CV
        results = perform_loocv_group(group_df, use_median=use_median)
        
        # Ne compter que les groupes avec LOO-CV valide (n >= 2)
        if not results.get('skipped', False):
            all_errors.extend(results['errors'])
        
        group_results.append({
            "pattern": pattern,
            "score_range": score_range,
            "count": results['count'],
            "mae": results['mae'],
            "method": "median" if use_median else "mean",
            "skipped": results.get('skipped', False)
        })
    
    mae_global = float(np.mean(all_errors)) if all_errors else 0.0
    
    return {
        "mae_global": mae_global,
        "total_movements": len(df),
        "group_results": group_results
    }

def analyze_groups_status(group_results: List[Dict]) -> Dict:
    """Analyse le statut des groupes (EXCELLENT vs ACCEPTABLE)."""
    excellent = [g for g in group_results if g['mae'] < 20.0]
    acceptable = [g for g in group_results if g['mae'] >= 20.0]
    
    return {
        "excellent_count": len(excellent),
        "acceptable_count": len(acceptable),
        "total_groups": len(group_results),
        "excellent_percent": 100.0 * len(excellent) / len(group_results) if group_results else 0.0
    }

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("SESSION 142 - PHASE 4 : VALIDATION GLOBALE")
    print("=" * 80)
    
    # 1. Charger données
    df = load_movements()
    
    # 2. Créer groupes
    df = create_groups(df)
    
    # 3. Calculer MAE global avec optimisations
    results = calculate_global_mae(df)
    
    mae_global = results['mae_global']
    group_results = results['group_results']
    
    print(f"\n📊 MAE GLOBAL : {mae_global:.2f} pips")
    print(f"   Baseline (Session 141) : {BASELINE_MAE_GLOBAL:.2f} pips")
    print(f"   Amélioration : {mae_global - BASELINE_MAE_GLOBAL:+.2f} pips")
    
    # 4. Analyser statut groupes
    status = analyze_groups_status(group_results)
    
    print(f"\n📈 STATUT GROUPES :")
    print(f"   EXCELLENT (MAE < 20) : {status['excellent_count']}/{status['total_groups']} "
          f"({status['excellent_percent']:.1f}%)")
    print(f"   ACCEPTABLE (MAE ≥ 20) : {status['acceptable_count']}/{status['total_groups']}")
    
    # 5. Détails groupes ACCEPTABLE
    acceptable_groups = [g for g in group_results if g['mae'] >= 20.0]
    if acceptable_groups:
        print(f"\n⚠️  GROUPES ACCEPTABLE :")
        for g in acceptable_groups:
            print(f"   {g['pattern']:30s} {g['score_range']:10s}: "
                  f"MAE {g['mae']:.2f} pips (n={g['count']}, method={g['method']})")
    
    # 6. Sauvegarder résultats
    validation_results = {
        "mae_global": mae_global,
        "baseline_mae_global": BASELINE_MAE_GLOBAL,
        "improvement": mae_global - BASELINE_MAE_GLOBAL,
        "improvement_percent": ((mae_global - BASELINE_MAE_GLOBAL) / BASELINE_MAE_GLOBAL * 100) if BASELINE_MAE_GLOBAL > 0 else 0.0,
        "status": status,
        "group_results": group_results,
        "optimizations_applied": OPTIMIZATIONS
    }
    
    with open(OUTPUT_RESULTS, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    print(f"\n✅ Résultats sauvegardés : {OUTPUT_RESULTS}")
    
    # 7. Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION PHASE 4")
    print("=" * 80)
    
    improvement = mae_global - BASELINE_MAE_GLOBAL
    
    if improvement < 0:
        print(f"\n✅ SUCCÈS : MAE global amélioré de {abs(improvement):.2f} pips")
        print(f"   MAE optimisé : {mae_global:.2f} pips")
        print(f"   Baseline : {BASELINE_MAE_GLOBAL:.2f} pips")
    elif improvement == 0:
        print(f"\n⚠️  MAE global inchangé : {mae_global:.2f} pips")
    else:
        print(f"\n❌ MAE global dégradé de {improvement:.2f} pips")
        print(f"   ⚠️  Vérifier optimisations appliquées")
    
    if status['excellent_count'] >= 21:
        print(f"\n✅ Groupes EXCELLENT : {status['excellent_count']}/{status['total_groups']} "
              f"({status['excellent_percent']:.1f}%)")
        print(f"   Objectif : ≥ 21 groupes EXCELLENT ✅")
    else:
        print(f"\n⚠️  Groupes EXCELLENT : {status['excellent_count']}/{status['total_groups']} "
              f"({status['excellent_percent']:.1f}%)")
        print(f"   Objectif : ≥ 21 groupes EXCELLENT ⚠️")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

