"""
RECHERCHE PONDÉRATION OPTIMALE MULTI-PÉRIODES
==============================================

Session 98 - Trouver meilleurs poids w1, w2, w3 pour combinaison 24h+48h+72h

Formule testée :
    score_tendance = w1 × R²_24h + w2 × R²_48h + w3 × R²_72h
    amplification = a × score_tendance + b

Contraintes :
    - w1 + w2 + w3 = 1.0
    - Exploration systématique par pas de 0.1

Objectif : Minimiser MAE vs facteur_parfait

Date : 29 octobre 2025
"""

import sys
from pathlib import Path

# Ajouter chemins
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

import pandas as pd
import numpy as np
from itertools import product

print("="*80)
print("🎯 RECHERCHE PONDÉRATION OPTIMALE MULTI-PÉRIODES")
print("="*80)

# ============================================================================
# CHARGER DONNÉES MULTI-PÉRIODES
# ============================================================================

csv_path = Path(__file__).parent / "calibration_multiperiod.csv"

if not csv_path.exists():
    print(f"\n❌ ERREUR : Fichier introuvable : {csv_path}")
    print(f"   Exécutez d'abord : python3 test_multiperiod_trend.py")
    sys.exit(1)

df = pd.read_csv(csv_path)

print(f"\n✅ Données chargées : {len(df)} dates")

# Vérifier colonnes requises
required_cols = ['facteur_parfait', '24h_r_squared', '48h_r_squared', '72h_r_squared']
missing_cols = [col for col in required_cols if col not in df.columns]

if missing_cols:
    print(f"\n❌ ERREUR : Colonnes manquantes : {missing_cols}")
    sys.exit(1)

# Extraire données
facteur = df['facteur_parfait'].values
r2_24h = df['24h_r_squared'].values
r2_48h = df['48h_r_squared'].values
r2_72h = df['72h_r_squared'].values

print(f"\n📊 Données extraites :")
print(f"   Facteur parfait : min={facteur.min():.2f}, max={facteur.max():.2f}, moy={facteur.mean():.2f}")
print(f"   R² 24h : min={r2_24h.min():.3f}, max={r2_24h.max():.3f}, moy={r2_24h.mean():.3f}")
print(f"   R² 48h : min={r2_48h.min():.3f}, max={r2_48h.max():.3f}, moy={r2_48h.mean():.3f}")
print(f"   R² 72h : min={r2_72h.min():.3f}, max={r2_72h.max():.3f}, moy={r2_72h.mean():.3f}")

# ============================================================================
# GRID SEARCH PONDÉRATION
# ============================================================================

print(f"\n🔍 GRID SEARCH PONDÉRATION (pas 0.1)...")

# Générer combinaisons w1, w2, w3 avec w1 + w2 + w3 = 1.0
weights_range = np.arange(0.0, 1.1, 0.1)
combinations = []

for w1 in weights_range:
    for w2 in weights_range:
        w3 = 1.0 - w1 - w2
        if w3 >= -0.01 and w3 <= 1.01:  # Tolérance arrondi
            w3 = round(w3, 1)
            if w3 >= 0.0 and w3 <= 1.0:
                combinations.append((round(w1, 1), round(w2, 1), w3))

print(f"   Combinaisons à tester : {len(combinations)}")

best_mae = float('inf')
best_weights = None
best_coeffs = None
best_y_pred = None

results = []

for w1, w2, w3 in combinations:
    # Score tendance pondéré
    score_tendance = w1 * r2_24h + w2 * r2_48h + w3 * r2_72h
    
    # Régression linéaire : amplification = a × score_tendance + b
    x_mean = np.mean(score_tendance)
    y_mean = np.mean(facteur)
    
    numerator = np.sum((score_tendance - x_mean) * (facteur - y_mean))
    denominator = np.sum((score_tendance - x_mean) ** 2)
    
    if denominator > 0:
        a = numerator / denominator
        b = y_mean - a * x_mean
        
        # Prédictions
        y_pred = a * score_tendance + b
        
        # MAE
        mae = np.mean(np.abs(y_pred - facteur))
        
        # Corrélation
        corr = np.corrcoef(score_tendance, facteur)[0, 1]
        
        results.append({
            'w1': w1,
            'w2': w2,
            'w3': w3,
            'a': a,
            'b': b,
            'mae': mae,
            'correlation': corr
        })
        
        # Meilleure combinaison
        if mae < best_mae:
            best_mae = mae
            best_weights = (w1, w2, w3)
            best_coeffs = (a, b)
            best_y_pred = y_pred

print(f"   ✅ Grid search terminé : {len(results)} combinaisons testées")

# ============================================================================
# RÉSULTATS TOP 10
# ============================================================================

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('mae')

print(f"\n📊 TOP 10 COMBINAISONS :\n")
print(f"   {'Rang':>4} {'w1(24h)':>8} {'w2(48h)':>8} {'w3(72h)':>8} {'MAE':>8} {'Corrélation':>12}")
print(f"   {'-'*60}")

for i, row in results_df.head(10).iterrows():
    print(f"   {results_df.index.get_loc(i)+1:>4} {row['w1']:>8.1f} {row['w2']:>8.1f} {row['w3']:>8.1f} {row['mae']:>8.3f} {row['correlation']:>12.3f}")

# ============================================================================
# ANALYSE MEILLEURE COMBINAISON
# ============================================================================

w1, w2, w3 = best_weights
a, b = best_coeffs

print(f"\n{'='*80}")
print(f"🏆 MEILLEURE COMBINAISON")
print(f"{'='*80}")

print(f"\n📐 POIDS OPTIMAUX :")
print(f"   w1 (24h) = {w1:.1f}")
print(f"   w2 (48h) = {w2:.1f}")
print(f"   w3 (72h) = {w3:.1f}")

print(f"\n📐 FORMULE COMPLÈTE :")
print(f"   score_tendance = {w1:.1f} × R²_24h + {w2:.1f} × R²_48h + {w3:.1f} × R²_72h")
print(f"   amplification = {a:.4f} × score_tendance + {b:.4f}")

# Corrélation
score_best = w1 * r2_24h + w2 * r2_48h + w3 * r2_72h
corr_best = np.corrcoef(score_best, facteur)[0, 1]

print(f"\n📊 PERFORMANCE :")
print(f"   MAE multi-périodes : {best_mae:.3f}")
print(f"   Corrélation        : {corr_best:.3f}")

# Comparaison avec périodes isolées
mae_24h_only = 0.702  # Du test précédent
mae_72h_only = 0.555  # Du test précédent
mae_fixe = 0.759

print(f"\n📊 COMPARAISON :")
print(f"   MAE multi-périodes (w1={w1:.1f}, w2={w2:.1f}, w3={w3:.1f}) : {best_mae:.3f}")
print(f"   MAE 72h seul                                : {mae_72h_only:.3f}")
print(f"   MAE 24h seul                                : {mae_24h_only:.3f}")
print(f"   MAE facteur fixe 2.5                        : {mae_fixe:.3f}")

if best_mae < mae_72h_only:
    improvement = ((mae_72h_only - best_mae) / mae_72h_only) * 100
    print(f"   Amélioration vs 72h seul : {improvement:.1f}% ✅")
elif best_mae < mae_fixe:
    improvement = ((mae_fixe - best_mae) / mae_fixe) * 100
    print(f"   Amélioration vs fixe 2.5 : {improvement:.1f}% ✅")
else:
    print(f"   ⚠️ Pas d'amélioration vs 72h seul")

# ============================================================================
# TEST DÉTAILLÉ PAR DATE
# ============================================================================

print(f"\n📋 TEST PAR DATE :")
print(f"   {'Date':12} {'Facteur Réel':>13} {'Prédit Multi':>13} {'Erreur':>8} {'Score':>8}")
print(f"   {'-'*60}")

for i, date in enumerate(df['date']):
    facteur_reel = facteur[i]
    facteur_predit = best_y_pred[i]
    erreur = abs(facteur_predit - facteur_reel)
    score = score_best[i]
    
    print(f"   {date:12} {facteur_reel:>13.3f} {facteur_predit:>13.3f} {erreur:>8.3f} {score:>8.3f}")

# Dates problématiques (MAE > 0.5)
problematic = [(df['date'].iloc[i], abs(best_y_pred[i] - facteur[i])) 
               for i in range(len(df)) 
               if abs(best_y_pred[i] - facteur[i]) > 0.5]

if problematic:
    print(f"\n⚠️ DATES AVEC ERREUR > 0.5 ({len(problematic)} dates) :")
    for date, err in problematic:
        print(f"   - {date} : erreur {err:.3f}")
    print(f"\n💡 Ces dates nécessitent analyse contexte macro/géopolitique")
else:
    print(f"\n✅ Toutes les dates ont MAE < 0.5 - Formule robuste !")

# ============================================================================
# SAUVEGARDER RÉSULTATS
# ============================================================================

output_csv = Path(__file__).parent / "ponderation_optimale_results.csv"
results_df.to_csv(output_csv, index=False)

print(f"\n💾 Résultats complets sauvegardés : {output_csv}")

# Sauvegarder meilleurs paramètres
best_params_txt = Path(__file__).parent / "best_amplification_formula.txt"
with open(best_params_txt, 'w') as f:
    f.write("="*80 + "\n")
    f.write("FORMULE AMPLIFICATION OPTIMALE - SESSION 98\n")
    f.write("="*80 + "\n\n")
    f.write("POIDS MULTI-PÉRIODES :\n")
    f.write(f"  w1 (24h) = {w1:.1f}\n")
    f.write(f"  w2 (48h) = {w2:.1f}\n")
    f.write(f"  w3 (72h) = {w3:.1f}\n\n")
    f.write("FORMULE COMPLÈTE :\n")
    f.write(f"  score_tendance = {w1:.1f} × R²_24h + {w2:.1f} × R²_48h + {w3:.1f} × R²_72h\n")
    f.write(f"  amplification = {a:.4f} × score_tendance + {b:.4f}\n\n")
    f.write("PERFORMANCE :\n")
    f.write(f"  MAE               : {best_mae:.3f}\n")
    f.write(f"  Corrélation       : {corr_best:.3f}\n")
    f.write(f"  Amélioration vs 2.5 : {((mae_fixe - best_mae) / mae_fixe * 100):.1f}%\n")

print(f"💾 Formule optimale sauvegardée : {best_params_txt}")

print("\n" + "="*80)
print("✅ RECHERCHE PONDÉRATION TERMINÉE")
print("="*80)

print(f"\n**Token usage:** ~132,000 / 190,000 (69%)")
