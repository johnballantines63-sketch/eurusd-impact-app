#!/usr/bin/env python3
"""
Optimisation du seuil θ pour meilleur compromis accuracy/couverture
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from sklearn.metrics import accuracy_score, matthews_corrcoef, f1_score

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

BASE_DIR = Path(__file__).parent.parent / 'outputs'
RESULTS_FILE = BASE_DIR / 'validation_direction_large_testset.csv'
DIRECTION_THRESHOLDS_FILE = BASE_DIR / 'direction_thresholds.json'
OUTPUT_FILE = BASE_DIR / 'theta_optimization_results.csv'

def main():
    print("="*80)
    print("OPTIMISATION SEUIL θ - ACCURACY vs COUVERTURE")
    print("="*80)
    print()
    
    # Charger résultats
    if not RESULTS_FILE.exists():
        print(f"❌ Fichier introuvable : {RESULTS_FILE}")
        print("   Exécutez d'abord validate_direction_large_testset.py")
        return
    
    df = pd.read_csv(RESULTS_FILE)
    
    if len(df) == 0:
        print("❌ Aucune donnée disponible")
        return
    
    print(f"📊 {len(df)} résultats chargés")
    print()
    
    # Split train/test (80/20)
    TRAIN_SPLIT = 0.8
    split_idx = int(len(df) * TRAIN_SPLIT)
    df_train = df.iloc[:split_idx].copy()
    df_test = df.iloc[split_idx:].copy()
    
    print(f"📅 Split : {len(df_train)} train, {len(df_test)} test")
    print()
    
    # Extraire scores S et directions réelles
    scores_S = df_test['score_S'].values
    directions_real = df_test['direction_real'].values
    
    # Tester différents seuils θ
    print("="*80)
    print("🔍 TEST DE DIFFÉRENTS SEUILS θ")
    print("="*80)
    print()
    
    thetas_to_test = np.arange(-0.5, 1.0, 0.05)
    
    results = []
    
    for theta in thetas_to_test:
        # Appliquer seuil
        predictions = []
        for S in scores_S:
            if S > theta:
                pred = 'UP'
            elif S < -theta:
                pred = 'DOWN'
            else:
                pred = 'UNKNOWN'
            predictions.append(pred)
        
        predictions = np.array(predictions)
        mask = predictions != 'UNKNOWN'
        
        if mask.sum() > 0:
            y_true = directions_real[mask]
            y_pred = predictions[mask]
            
            y_true_bin = (y_true == 'UP').astype(int)
            y_pred_bin = (y_pred == 'UP').astype(int)
            
            accuracy = accuracy_score(y_true_bin, y_pred_bin) * 100
            mcc = matthews_corrcoef(y_true_bin, y_pred_bin)
            f1 = f1_score(y_true_bin, y_pred_bin, zero_division=0)
            coverage = (mask.sum() / len(predictions)) * 100
            
            # Score composite : accuracy × coverage (normalisé)
            composite_score = accuracy * (coverage / 100)
            
            results.append({
                'theta': theta,
                'accuracy': accuracy,
                'mcc': mcc,
                'f1': f1,
                'coverage': coverage,
                'n_valid': mask.sum(),
                'n_total': len(predictions),
                'composite_score': composite_score
            })
        else:
            results.append({
                'theta': theta,
                'accuracy': 0.0,
                'mcc': 0.0,
                'f1': 0.0,
                'coverage': 0.0,
                'n_valid': 0,
                'n_total': len(predictions),
                'composite_score': 0.0
            })
    
    df_results = pd.DataFrame(results)
    
    # Trouver meilleurs seuils selon différents critères
    print("="*80)
    print("📈 MEILLEURS SEUILS SELON CRITÈRES")
    print("="*80)
    print()
    
    # 1. Meilleur accuracy (avec minimum 50% couverture)
    df_min_coverage = df_results[df_results['coverage'] >= 50.0]
    if len(df_min_coverage) > 0:
        best_acc = df_min_coverage.loc[df_min_coverage['accuracy'].idxmax()]
        print(f"🎯 Meilleur accuracy (≥50% couverture) :")
        print(f"   θ = {best_acc['theta']:.2f}")
        print(f"   Accuracy : {best_acc['accuracy']:.1f}%")
        print(f"   Couverture : {best_acc['coverage']:.1f}%")
        print(f"   MCC : {best_acc['mcc']:.3f}")
        print(f"   F1 : {best_acc['f1']:.3f}")
        print()
    
    # 2. Meilleur composite score (accuracy × coverage)
    best_composite = df_results.loc[df_results['composite_score'].idxmax()]
    print(f"⭐ Meilleur compromis (accuracy × coverage) :")
    print(f"   θ = {best_composite['theta']:.2f}")
    print(f"   Accuracy : {best_composite['accuracy']:.1f}%")
    print(f"   Couverture : {best_composite['coverage']:.1f}%")
    print(f"   Score composite : {best_composite['composite_score']:.1f}")
    print(f"   MCC : {best_composite['mcc']:.3f}")
    print(f"   F1 : {best_composite['f1']:.3f}")
    print()
    
    # 3. Meilleur MCC
    df_valid_mcc = df_results[df_results['n_valid'] >= 5]
    if len(df_valid_mcc) > 0:
        best_mcc = df_valid_mcc.loc[df_valid_mcc['mcc'].idxmax()]
        print(f"📊 Meilleur MCC (≥5 échantillons) :")
        print(f"   θ = {best_mcc['theta']:.2f}")
        print(f"   Accuracy : {best_mcc['accuracy']:.1f}%")
        print(f"   Couverture : {best_mcc['coverage']:.1f}%")
        print(f"   MCC : {best_mcc['mcc']:.3f}")
        print(f"   F1 : {best_mcc['f1']:.3f}")
        print()
    
    # 4. Seuil actuel calibré
    with open(DIRECTION_THRESHOLDS_FILE, 'r') as f:
        direction_thresholds = json.load(f)
    theta_current = direction_thresholds.get('1h', 0.0)
    
    current_row = df_results[df_results['theta'].abs() - abs(theta_current) < 0.01]
    if len(current_row) > 0:
        current = current_row.iloc[0]
        print(f"📌 Seuil actuel (θ={theta_current:.2f}) :")
        print(f"   Accuracy : {current['accuracy']:.1f}%")
        print(f"   Couverture : {current['coverage']:.1f}%")
        print(f"   MCC : {current['mcc']:.3f}")
        print(f"   F1 : {current['f1']:.3f}")
        print()
    
    # Afficher top 10 par composite score
    print("="*80)
    print("🏆 TOP 10 SEUILS (par score composite)")
    print("="*80)
    print()
    
    df_top10 = df_results.nlargest(10, 'composite_score')
    print(df_top10[['theta', 'accuracy', 'coverage', 'mcc', 'f1', 'composite_score']].to_string(index=False))
    print()
    
    # Sauvegarder résultats
    df_results.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Résultats sauvegardés : {OUTPUT_FILE}")
    print()
    
    # Recommandation
    print("="*80)
    print("💡 RECOMMANDATION")
    print("="*80)
    print()
    
    recommended_theta = best_composite['theta']
    print(f"Recommandation : θ = {recommended_theta:.2f}")
    print(f"   → Bon compromis entre accuracy ({best_composite['accuracy']:.1f}%) et couverture ({best_composite['coverage']:.1f}%)")
    print()
    
    if abs(recommended_theta - theta_current) > 0.05:
        print(f"⚠️  Différence avec seuil actuel ({theta_current:.2f}) : {abs(recommended_theta - theta_current):.2f}")
        print(f"   → Considérer mise à jour de direction_thresholds.json")
    else:
        print(f"✅ Seuil actuel proche de l'optimal")
    print()

if __name__ == '__main__':
    main()


