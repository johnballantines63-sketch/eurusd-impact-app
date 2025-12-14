"""
ANALYSE ROBUSTESSE - CORRÉLATION & DISTRIBUTION (SESSION 99)
============================================================

Session 99 - Phase 4 : Analyse robustesse formule S99

OBJECTIF :
    Analyser :
    1. Corrélation R²_72h vs Amplification Optimale
    2. Distribution amplifications optimales
    3. Distribution erreurs S99
    4. Identifier outliers

Date : 29 octobre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("="*80)
print("📊 ANALYSE ROBUSTESSE - SESSION 99")
print("="*80)

# Charger données
recalib_file = Path(__file__).parent / "recalibration_20_dates_results.csv"
test_file = Path(__file__).parent / "test_comparatif_20_dates_results.csv"

df_recalib = pd.read_csv(recalib_file)
df_test = pd.read_csv(test_file)

# ============================================================================
# PHASE 1 : CORRÉLATION R² vs AMP OPTIMALE
# ============================================================================

print(f"\n{'='*80}")
print(f"📈 PHASE 1 : Corrélation R²_72h vs Amplification Optimale")
print(f"{'='*80}\n")

x = df_recalib['r_squared_72h'].values
y = df_recalib['amp_optimal'].values

# Corrélation Pearson
corr_pearson = np.corrcoef(x, y)[0, 1]

# Coefficients régression (déjà calculés)
x_mean = np.mean(x)
y_mean = np.mean(y)
a = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
b = y_mean - a * x_mean

print(f"Corrélation Pearson : {corr_pearson:.3f}")
print(f"\nFormule S99 :")
print(f"  amp = {a:.4f} × R² + {b:.4f}")

# Comparaison avec S98
print(f"\nFormule S98 :")
print(f"  amp = 1.9938 × R² + 1.4448")

print(f"\nCorrélation S98 (10 dates) : 0.472")
print(f"Corrélation S99 (20 dates) : {corr_pearson:.3f}")

if abs(corr_pearson) > 0.40:
    print(f"✅ Corrélation SUFFISANTE (> 0.40)")
elif abs(corr_pearson) > 0.30:
    print(f"⚠️  Corrélation MOYENNE (0.30-0.40)")
else:
    print(f"❌ Corrélation FAIBLE (< 0.30)")

# ============================================================================
# PHASE 2 : DISTRIBUTION AMPLIFICATIONS OPTIMALES
# ============================================================================

print(f"\n{'='*80}")
print(f"📊 PHASE 2 : Distribution Amplifications Optimales")
print(f"{'='*80}\n")

amp_stats = df_recalib['amp_optimal'].describe()

print(f"Statistiques amplifications optimales :")
print(f"  Count   : {amp_stats['count']:.0f}")
print(f"  Moyenne : {amp_stats['mean']:.3f}")
print(f"  Médiane : {amp_stats['50%']:.3f}")
print(f"  Min     : {amp_stats['min']:.3f}")
print(f"  Max     : {amp_stats['max']:.3f}")
print(f"  Std Dev : {amp_stats['std']:.3f}")

# Identifier dates à la borne inférieure (0.5)
dates_borne_inf = df_recalib[df_recalib['amp_optimal'] <= 0.51]
print(f"\n⚠️  Dates à la borne inférieure (amp ≈ 0.5) : {len(dates_borne_inf)}/20 ({len(dates_borne_inf)/20*100:.0f}%)")
if len(dates_borne_inf) > 0:
    print(f"   Dates concernées :")
    for _, row in dates_borne_inf.iterrows():
        print(f"     - {row['date']} (impact: {row['impact_real']:.1f} pips, R²: {row['r_squared_72h']:.3f})")

# Identifier dates à la borne supérieure (5.0)
dates_borne_sup = df_recalib[df_recalib['amp_optimal'] >= 4.99]
print(f"\n⚠️  Dates à la borne supérieure (amp ≈ 5.0) : {len(dates_borne_sup)}/20 ({len(dates_borne_sup)/20*100:.0f}%)")
if len(dates_borne_sup) > 0:
    print(f"   Dates concernées :")
    for _, row in dates_borne_sup.iterrows():
        print(f"     - {row['date']} (impact: {row['impact_real']:.1f} pips, R²: {row['r_squared_72h']:.3f})")

# ============================================================================
# PHASE 3 : DISTRIBUTION ERREURS S99
# ============================================================================

print(f"\n{'='*80}")
print(f"📊 PHASE 3 : Distribution Erreurs S99")
print(f"{'='*80}\n")

errors_s99 = df_test['error_s99']
errors_stats = errors_s99.describe()

print(f"Statistiques erreurs S99 :")
print(f"  Count   : {errors_stats['count']:.0f}")
print(f"  Moyenne : {errors_stats['mean']:.2f} pips (MAE)")
print(f"  Médiane : {errors_stats['50%']:.2f} pips")
print(f"  Min     : {errors_stats['min']:.2f} pips")
print(f"  Max     : {errors_stats['max']:.2f} pips")
print(f"  Std Dev : {errors_stats['std']:.2f} pips")

# Quartiles
q1 = errors_stats['25%']
q3 = errors_stats['75%']

print(f"\n  Q1 (25%) : {q1:.2f} pips")
print(f"  Q2 (50%) : {errors_stats['50%']:.2f} pips")
print(f"  Q3 (75%) : {q3:.2f} pips")

# Outliers (> 20 pips)
outliers = df_test[df_test['error_s99'] > 20]
print(f"\n⚠️  Outliers (erreur > 20 pips) : {len(outliers)}/20 ({len(outliers)/20*100:.0f}%)")
if len(outliers) > 0:
    print(f"\n   Dates concernées :")
    for _, row in outliers.iterrows():
        print(f"     - {row['date']} : {row['error_s99']:.1f} pips (impact réel: {row['impact_real']:.1f} pips)")

# ============================================================================
# PHASE 4 : DATES EXCELLENTES (< 7 pips)
# ============================================================================

print(f"\n{'='*80}")
print(f"🌟 PHASE 4 : Dates Excellentes (Erreur < 7 pips)")
print(f"{'='*80}\n")

excellentes = df_test[df_test['error_s99'] < 7]
print(f"✅ Dates avec erreur < 7 pips : {len(excellentes)}/20 ({len(excellentes)/20*100:.0f}%)\n")

if len(excellentes) > 0:
    excellentes_sorted = excellentes.sort_values('error_s99')
    print(f"   {'Date':<12} {'Impact Réel':<12} {'Erreur S99':<12} {'R²_72h':<10}")
    print(f"   {'-'*50}")
    for _, row in excellentes_sorted.iterrows():
        print(f"   {row['date']:<12} {row['impact_real']:>10.1f}  {row['error_s99']:>10.2f}  {row['r_squared_72h']:>8.3f}")

# ============================================================================
# PHASE 5 : CORRÉLATION R² vs ERREUR S99
# ============================================================================

print(f"\n{'='*80}")
print(f"📈 PHASE 5 : Corrélation R²_72h vs Erreur S99")
print(f"{'='*80}\n")

# Fusionner données
df_merged = df_test.merge(df_recalib[['date', 'r_squared_72h']], on='date')

x_r2 = df_merged['r_squared_72h'].values
y_err = df_merged['error_s99'].values

corr_r2_error = np.corrcoef(x_r2, y_err)[0, 1]

print(f"Corrélation R²_72h vs Erreur S99 : {corr_r2_error:.3f}")

if corr_r2_error < -0.3:
    print(f"✅ Corrélation NÉGATIVE significative")
    print(f"   → R² élevé = Erreur faible (comme attendu)")
elif corr_r2_error > 0.3:
    print(f"❌ Corrélation POSITIVE (problème)")
    print(f"   → R² élevé = Erreur élevée (contre-intuitif)")
else:
    print(f"⚠️  Corrélation FAIBLE")
    print(f"   → R² n'explique pas bien les erreurs")

print("\n" + "="*80)
print("✅ ANALYSE ROBUSTESSE TERMINÉE")
print("="*80)
