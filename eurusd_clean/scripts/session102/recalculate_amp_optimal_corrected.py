#!/usr/bin/env python3
"""
RECALCUL amp_optimal AVEC IMPACT CORRIGÉ
=========================================

Recalcule l'amplification optimale avec l'impact réel corrigé (56.2 pips).

Auteur : André Valentin
Date   : 31 octobre 2025 - Session 103
"""

import sys
import json
from pathlib import Path
from scipy.optimize import minimize_scalar

print("=" * 80)
print("RECALCUL amp_optimal - IMPACT CORRIGÉ")
print("=" * 80)
print()

# Import formules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "fx_impact_app" / "src"))
from formulas_validated import calculate_impact_d

# Charger impact corrigé
impact_file = Path(__file__).parent / "impact_real_corrected.json"
if not impact_file.exists():
    print("❌ ERREUR : Lancer d'abord measure_impact_real_corrected.py")
    sys.exit(1)

with open(impact_file) as f:
    data = json.load(f)

# Données
score_adjusted = 84.2  # Du test précédent
num_events = 11
impact_real_corrected = data['impact_real_corrected']['impact_pips']
impact_old = data['impact_old_method']['impact_pips']

print("📊 DONNÉES :")
print(f"   Score ajusté       : {score_adjusted}")
print(f"   Num events         : {num_events}")
print(f"   Impact réel (corrigé) : {impact_real_corrected:.1f} pips")
print(f"   Impact ancien      : {impact_old:.1f} pips")
print()

# Calcul baseline amp=2.5
impact_baseline = calculate_impact_d(
    empirical_score=score_adjusted,
    num_events=num_events,
    amplification=2.5,
    correction_factor=0.758
)

print("📊 IMPACT BASELINE (amp=2.5) :")
print(f"   Impact calculé : {impact_baseline:.1f} pips")
print(f"   Impact réel    : {impact_real_corrected:.1f} pips")
print(f"   Écart          : {abs(impact_baseline - impact_real_corrected):.1f} pips")
print()

# Optimisation
print("🔄 Optimisation amp_optimal...")

def error_function(amp):
    impact_pred = calculate_impact_d(
        empirical_score=score_adjusted,
        num_events=num_events,
        amplification=amp,
        correction_factor=0.758
    )
    return abs(impact_pred - impact_real_corrected)

result = minimize_scalar(error_function, bounds=(0.5, 5.0), method='bounded')
amp_optimal = result.x
error_optimal = result.fun

print()
print("🎯 AMPLIFICATION OPTIMALE :")
print(f"   amp_optimal    : {amp_optimal:.3f}")
print(f"   Erreur finale  : {error_optimal:.3f} pips")
print()

# Vérification
impact_with_optimal = calculate_impact_d(
    empirical_score=score_adjusted,
    num_events=num_events,
    amplification=amp_optimal,
    correction_factor=0.758
)

print("✅ VÉRIFICATION :")
print(f"   Impact avec amp_optimal : {impact_with_optimal:.1f} pips")
print(f"   Impact réel corrigé     : {impact_real_corrected:.1f} pips")
print(f"   Écart                   : {abs(impact_with_optimal - impact_real_corrected):.2f} pips")
print()

# Comparaison baseline
correction_factor_amp = amp_optimal / 2.5

print("=" * 80)
print("COMPARAISON BASELINE")
print("=" * 80)
print()
print(f"   Baseline      : amp = 2.5")
print(f"   Optimal       : amp = {amp_optimal:.3f}")
print(f"   Correction    : {correction_factor_amp:.3f}x")
print()

if abs(amp_optimal - 2.5) < 0.1:
    print("✅ amp_optimal ≈ 2.5 : BASELINE DÉJÀ OPTIMALE !")
    print()
    print("🎯 CONCLUSION :")
    print("   Le facteur d'amplification 2.5 est VALIDÉ pour le cas 11.09")
    print("   Utiliser amp=2.5 comme RÉFÉRENCE pour calibration 44 dates")
elif amp_optimal < 2.5:
    print("⚠️ amp_optimal < 2.5 : Baseline SUR-ESTIME")
    print(f"   Correction : {correction_factor_amp:.3f}x")
else:
    print("⚠️ amp_optimal > 2.5 : Baseline SOUS-ESTIME")
    print(f"   Correction : {correction_factor_amp:.3f}x")

print()
print("=" * 80)
print("MÉTHODE OPTION A VALIDÉE")
print("=" * 80)
print()
print(f"Pour calibration 44 dates :")
print(f"  1. Baseline référence : amp = {amp_optimal:.3f} (cas 11.09)")
print(f"  2. Pour chaque date :")
print(f"     - Calculer impact avec amp = {amp_optimal:.3f}")
print(f"     - Trouver amp_optimal_date")
print(f"     - delta_amp = (amp_optimal_date - {amp_optimal:.3f}) / {amp_optimal:.3f}")
print(f"  3. Régression : delta_amp = f(R², amplitude, durée)")
print()
print("=" * 80)

# Sauvegarder
output_data = {
    **data,
    'calibration': {
        'score_adjusted': score_adjusted,
        'num_events': num_events,
        'impact_baseline_2_5': float(impact_baseline),
        'amp_optimal': float(amp_optimal),
        'correction_factor': float(correction_factor_amp),
        'error_pips': float(error_optimal),
        'recommendation': 'use_amp_optimal_as_reference' if abs(amp_optimal - 2.5) > 0.1 else 'baseline_2_5_validated'
    }
}

output_file = Path(__file__).parent / "calibration_reference_11_09.json"
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)

print(f"💾 Résultats sauvegardés : {output_file.name}")
print()
print("🚀 Prêt pour calibration 44 dates avec méthode Option A")
