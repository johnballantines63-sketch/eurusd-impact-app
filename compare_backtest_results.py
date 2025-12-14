#!/usr/bin/env python3
"""
Compare les résultats avant/après la correction
"""

import json
import numpy as np

def load_results(filepath):
    """Charge un fichier JSON de résultats"""
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_results(data, label):
    """Analyse et affiche les métriques d'un fichier de résultats"""
    
    print(f"\n{'='*70}")
    print(f"📊 {label}")
    print(f"{'='*70}")
    
    results = data['results']
    
    # Impacts
    impacts = [r['impact_pips'] for r in results]
    n_zero = sum(1 for i in impacts if i == 0)
    n_nonzero = len(impacts) - n_zero
    
    print(f"\n💥 IMPACTS :")
    print(f"   Total phases : {len(results)}")
    print(f"   Impact = 0   : {n_zero} ({n_zero/len(results)*100:.1f}%)")
    print(f"   Impact > 0   : {n_nonzero} ({n_nonzero/len(results)*100:.1f}%)")
    
    if n_nonzero > 0:
        nonzero_impacts = [i for i in impacts if i > 0]
        print(f"   Impact moyen : {np.mean(nonzero_impacts):.1f} pips")
        print(f"   Impact min   : {np.min(nonzero_impacts):.1f} pips")
        print(f"   Impact max   : {np.max(nonzero_impacts):.1f} pips")
    
    # TTR
    errors = [r['error'] for r in results]
    ttr_obs = [r['ttr_observed'] for r in results]
    ttr_theo = [r['ttr_theoretical'] for r in results]
    
    print(f"\n📊 TTR :")
    print(f"   MAE          : {np.mean(errors):.1f} min")
    print(f"   RMSE         : {np.sqrt(np.mean(np.array(errors)**2)):.1f} min")
    print(f"   Médiane err  : {np.median(errors):.1f} min")
    print(f"   Erreur min   : {np.min(errors):.1f} min")
    print(f"   Erreur max   : {np.max(errors):.1f} min")
    
    # Distribution des erreurs
    bins = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 100)]
    print(f"\n   Distribution des erreurs :")
    for min_val, max_val in bins:
        count = sum(1 for e in errors if min_val <= e < max_val)
        pct = count / len(errors) * 100
        bar = "█" * int(pct / 2)
        label = f"{min_val}-{max_val} min" if max_val < 100 else f"> {min_val} min"
        print(f"      {label:<12} : {count:3} ({pct:5.1f}%) {bar}")
    
    # Fallbacks (TTR = 30 min)
    n_fallbacks = sum(1 for t in ttr_obs if t == 30)
    print(f"\n   ⚠️  TTR = 30 min (fallbacks) : {n_fallbacks} ({n_fallbacks/len(results)*100:.1f}%)")


def compare_files():
    """Compare les deux fichiers de résultats"""
    
    print("="*70)
    print("🔬 COMPARAISON RÉSULTATS BACKTEST")
    print("="*70)
    
    try:
        old_data = load_results('backtest_multi_events_results.json')
        analyze_results(old_data, "AVANT (version originale)")
    except FileNotFoundError:
        print("\n❌ Fichier backtest_multi_events_results.json introuvable")
        return
    
    try:
        new_data = load_results('backtest_multi_events_results_FIXED.json')
        analyze_results(new_data, "APRÈS (version corrigée)")
    except FileNotFoundError:
        print("\n❌ Fichier backtest_multi_events_results_FIXED.json introuvable")
        print("   → Lancez d'abord : python3 backtest_multi_events_phases_FIXED.py")
        return
    
    # Comparaison directe
    print(f"\n{'='*70}")
    print("📈 AMÉLIORATION")
    print(f"{'='*70}")
    
    old_results = old_data['results']
    new_results = new_data['results']
    
    old_impacts = [r['impact_pips'] for r in old_results]
    new_impacts = [r['impact_pips'] for r in new_results]
    
    old_errors = [r['error'] for r in old_results]
    new_errors = [r['error'] for r in new_results]
    
    old_mae = np.mean(old_errors)
    new_mae = np.mean(new_errors)
    
    old_n_zero = sum(1 for i in old_impacts if i == 0)
    new_n_zero = sum(1 for i in new_impacts if i == 0)
    
    print(f"\n💥 Impacts avec valeur = 0 :")
    print(f"   AVANT : {old_n_zero}/{len(old_results)} ({old_n_zero/len(old_results)*100:.1f}%)")
    print(f"   APRÈS : {new_n_zero}/{len(new_results)} ({new_n_zero/len(new_results)*100:.1f}%)")
    
    if old_n_zero > new_n_zero:
        improvement = (old_n_zero - new_n_zero) / old_n_zero * 100
        print(f"   ✅ Amélioration : -{improvement:.1f}%")
    else:
        print(f"   ⚠️  Pas d'amélioration")
    
    print(f"\n📊 MAE (Mean Absolute Error) :")
    print(f"   AVANT : {old_mae:.1f} min")
    print(f"   APRÈS : {new_mae:.1f} min")
    
    if new_mae < old_mae:
        improvement = (old_mae - new_mae) / old_mae * 100
        print(f"   ✅ Amélioration : -{improvement:.1f}%")
    else:
        print(f"   ⚠️  Pas d'amélioration")
    
    print(f"\n{'='*70}")
    
    # Objectif
    print(f"\n🎯 OBJECTIFS :")
    print(f"   Impact = 0     : < 20% ... {'✅ ATTEINT' if new_n_zero/len(new_results) < 0.20 else '❌ PAS ATTEINT'}")
    print(f"   MAE            : < 10 min ... {'✅ ATTEINT' if new_mae < 10 else '❌ PAS ATTEINT'}")
    
    if new_n_zero/len(new_results) < 0.20 and new_mae < 10:
        print(f"\n🎉 SUCCÈS ! Les objectifs sont atteints !")
    else:
        print(f"\n⚠️  Objectifs partiellement atteints - peut nécessiter seuil adaptatif")


if __name__ == "__main__":
    compare_files()
