#!/usr/bin/env python3
"""
VALIDATION FORMULES SUR CAS 11.09.2025
======================================

Test crucial : Est-ce que les formules calibrées prédisent
correctement le cas de référence 11.09.2025 ?
"""

import pandas as pd
from pathlib import Path
import numpy as np

print("=" * 80)
print("VALIDATION CAS RÉFÉRENCE 11.09.2025")
print("=" * 80)

# Charger données
project_root = Path(__file__).resolve().parents[3]
csv_path = project_root / "eurusd_clean" / "scripts" / "session102" / "analysis_real_data_optimized.csv"
df = pd.read_csv(csv_path)

# Cas 11.09.2025
ref_date = '2025-09-11'
ref_row = df[df['date'] == ref_date].iloc[0]

# Métriques
r2 = ref_row['trend_r2_optimized']
amplitude_pips = ref_row['trend_amplitude_optimized']
amp_parfaite = ref_row['amp_parfaite']

print(f"\n📍 CAS RÉFÉRENCE : {ref_date}")
print(f"\n   Métriques tendance optimisées :")
print(f"   - R²              : {r2:.3f}")
print(f"   - Amplitude       : {amplitude_pips:.1f} pips")
print(f"   - Durée           : {ref_row['trend_duration_optimized']:.1f}h")
print(f"\n   Amplification parfaite attendue : {amp_parfaite:.3f}")

# ============================================================================
# TEST FORMULES CALIBRÉES
# ============================================================================

print(f"\n{'='*80}")
print("TEST FORMULES CALIBRÉES")
print(f"{'='*80}")

# Normaliser amplitude
amp_norm = amplitude_pips / 100.0

# F1: Linéaire simple (R² seul)
amp_f1 = 0.872 * r2 + 0.751
error_f1 = abs(amp_f1 - amp_parfaite)
print(f"\n✅ F1: Linéaire simple (R² seul)")
print(f"   amp = 0.872×{r2:.3f} + 0.751")
print(f"   amp = {amp_f1:.3f}")
print(f"   vs parfaite {amp_parfaite:.3f}")
print(f"   Erreur : {error_f1:.3f} ({error_f1/amp_parfaite*100:.1f}%)")

# F2: Linéaire dual (R² + amplitude)
amp_f2 = 0.833 * r2 + 0.050 * amp_norm + 0.700
error_f2 = abs(amp_f2 - amp_parfaite)
print(f"\n✅ F2: Linéaire dual (R² + amplitude)")
print(f"   amp = 0.833×{r2:.3f} + 0.050×{amp_norm:.3f} + 0.700")
print(f"   amp = {amp_f2:.3f}")
print(f"   vs parfaite {amp_parfaite:.3f}")
print(f"   Erreur : {error_f2:.3f} ({error_f2/amp_parfaite*100:.1f}%)")

# F3: Inverse (R² faible → amp forte)
amp_f3 = 0.041 / (r2 + 0.1) + 1.129
error_f3 = abs(amp_f3 - amp_parfaite)
print(f"\n✅ F3: Inverse (R² faible → amp forte)")
print(f"   amp = 0.041/({r2:.3f}+0.1) + 1.129")
print(f"   amp = {amp_f3:.3f}")
print(f"   vs parfaite {amp_parfaite:.3f}")
print(f"   Erreur : {error_f3:.3f} ({error_f3/amp_parfaite*100:.1f}%)")

# F4: Ratio proportionnel ancré
ref_amp_parfaite = amp_parfaite  # Ancré sur ce cas
ref_r2 = r2
amp_f4 = ref_amp_parfaite * ((r2 / ref_r2) ** 3.0)
error_f4 = abs(amp_f4 - amp_parfaite)
print(f"\n✅ F4: Ratio proportionnel ancré")
print(f"   amp = {ref_amp_parfaite:.3f}×(({r2:.3f}/{ref_r2:.3f})^3.0)")
print(f"   amp = {amp_f4:.3f}")
print(f"   vs parfaite {amp_parfaite:.3f}")
print(f"   Erreur : {error_f4:.3f} ({error_f4/amp_parfaite*100:.1f}%)")

# F5: Combinée (R² + amplitude + inverse)
amp_f5 = 0.775 * r2 + 0.050 * amp_norm + 0.120 / (r2 + 0.1) + 0.534
error_f5 = abs(amp_f5 - amp_parfaite)
print(f"\n✅ F5: Combinée (R² + amplitude + inverse) [MEILLEURE]")
print(f"   amp = 0.775×{r2:.3f} + 0.050×{amp_norm:.3f} + 0.120/({r2:.3f}+0.1) + 0.534")
print(f"   amp = {amp_f5:.3f}")
print(f"   vs parfaite {amp_parfaite:.3f}")
print(f"   Erreur : {error_f5:.3f} ({error_f5/amp_parfaite*100:.1f}%)")

# ============================================================================
# BASELINE
# ============================================================================

amp_baseline = 2.5
error_baseline = abs(amp_baseline - amp_parfaite)
print(f"\n📊 BASELINE amp=2.5 fixe")
print(f"   amp = {amp_baseline:.3f}")
print(f"   vs parfaite {amp_parfaite:.3f}")
print(f"   Erreur : {error_baseline:.3f} ({error_baseline/amp_parfaite*100:.1f}%)")

# Amp constant optimisé = 1.2
amp_optimized = 1.2
error_optimized = abs(amp_optimized - amp_parfaite)
print(f"\n📊 AMP CONSTANT OPTIMISÉ = 1.2")
print(f"   amp = {amp_optimized:.3f}")
print(f"   vs parfaite {amp_parfaite:.3f}")
print(f"   Erreur : {error_optimized:.3f} ({error_optimized/amp_parfaite*100:.1f}%)")

# ============================================================================
# COMPARAISON
# ============================================================================

print(f"\n{'='*80}")
print("COMPARAISON ERREURS")
print(f"{'='*80}")

results = [
    ("F5 Combinée (MEILLEURE)", amp_f5, error_f5),
    ("F2 Linéaire dual", amp_f2, error_f2),
    ("F1 Linéaire simple", amp_f1, error_f1),
    ("F3 Inverse", amp_f3, error_f3),
    ("F4 Ratio ancré", amp_f4, error_f4),
    ("AMP CONSTANT 1.2", amp_optimized, error_optimized),
    ("BASELINE 2.5", amp_baseline, error_baseline),
]

# Trier par erreur
results_sorted = sorted(results, key=lambda x: x[2])

print(f"\n{'Méthode':<30} {'Amp prédite':>12} {'Erreur':>10} {'Erreur %':>10}")
print("-" * 80)

for method, amp_pred, error in results_sorted:
    error_pct = error / amp_parfaite * 100
    status = "✅✅" if error < 0.5 else "✅" if error < 1.0 else "⚠️" if error < 1.5 else "❌"
    print(f"{status} {method:<27} {amp_pred:>12.3f} {error:>10.3f} {error_pct:>9.1f}%")

# ============================================================================
# ANALYSE
# ============================================================================

print(f"\n{'='*80}")
print("ANALYSE CRITIQUE")
print(f"{'='*80}")

best_method, best_amp, best_error = results_sorted[0]

print(f"\n🏆 MEILLEURE sur cas 11.09 : {best_method}")
print(f"   Erreur : {best_error:.3f} ({best_error/amp_parfaite*100:.1f}%)")

if best_error > 1.0:
    print(f"\n❌ PROBLÈME DÉTECTÉ !")
    print(f"   TOUTES les formules ont erreur > 1.0")
    print(f"   Sur le cas de RÉFÉRENCE qui valide la méthode !")
    print(f"\n   Cela signifie :")
    print(f"   1. Les formules calibrées sous-estiment massivement ce cas")
    print(f"   2. Le cas 11.09 est un OUTLIER (amp parfaite 2.537 très haute)")
    print(f"   3. Confirme que relation dynamique inexistante")
    
if best_error < error_optimized:
    print(f"\n✅ Meilleure formule bat amp constant 1.2")
    print(f"   Amélioration : {(error_optimized - best_error):.3f}")
else:
    print(f"\n⚠️  Amp constant 1.2 MEILLEUR que formules calibrées !")
    print(f"   Pire erreur formule vs 1.2 : +{(best_error - error_optimized):.3f}")

# Distribution erreurs toutes formules
formule_errors = [error_f1, error_f2, error_f3, error_f5]
mean_error_formules = np.mean(formule_errors)

print(f"\n📊 Erreur moyenne formules : {mean_error_formules:.3f}")
print(f"   Erreur amp=1.2 constant  : {error_optimized:.3f}")
print(f"   Erreur baseline amp=2.5  : {error_baseline:.3f}")

if mean_error_formules > error_optimized:
    print(f"\n✅ CONFIRMATION : Amp constant 1.2 est OPTIMAL")
    print(f"   Même sur cas référence, formules complexes moins bonnes")
else:
    print(f"\n⚠️  Formules légèrement meilleures en moyenne")
    print(f"   Mais gain marginal vs complexité ajoutée")

print(f"\n{'='*80}")
print("CONCLUSION CAS 11.09.2025")
print(f"{'='*80}")

if best_error > 1.0 and error_optimized < best_error:
    print(f"\n❌ Le cas 11.09 (amp parfaite 2.537) est un OUTLIER")
    print(f"   Aucune formule ne le prédit bien")
    print(f"   Amp constant 1.2 est la solution la plus robuste")
    print(f"\n   RECOMMANDATION MAINTENUE : amp = 1.2")
elif best_error < 0.5:
    print(f"\n✅✅ Excellente prédiction sur cas référence !")
    print(f"   Envisager formule {best_method}")
else:
    print(f"\n⚠️  Prédiction correcte mais imparfaite")
    print(f"   Évaluer complexité vs gain marginal")

print(f"\n{'='*80}")
