#!/usr/bin/env python3
"""
VÉRIFICATION : amp_optimal 11.09 → impact réel
===============================================

Vérifie que amp=1.982 (optimal trouvé) donne bien impact=44.6 pips (mesuré)

Auteur : André Valentin
Date   : 31 octobre 2025 - Session 103
"""

import sys
from pathlib import Path

# Import formules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "fx_impact_app" / "src"))
from formulas_validated import calculate_impact_d

print("=" * 80)
print("VÉRIFICATION : amp_optimal 11.09 → impact réel")
print("=" * 80)
print()

# Données cas 11.09 (résultats validation)
score_adjusted = 84.2
num_events = 11
amp_optimal = 1.982
impact_real_measured = 44.6

print("📊 DONNÉES CAS 11.09 :")
print(f"   Score ajusté  : {score_adjusted}")
print(f"   Num events    : {num_events}")
print(f"   Amp optimal   : {amp_optimal}")
print(f"   Impact réel   : {impact_real_measured} pips")
print()

# Calcul impact avec amp_optimal
impact_calculated = calculate_impact_d(
    empirical_score=score_adjusted,
    num_events=num_events,
    amplification=amp_optimal,
    correction_factor=0.758
)

print("🧮 CALCUL AVEC amp_optimal :")
print(f"   calculate_impact_d(")
print(f"      score={score_adjusted},")
print(f"      events={num_events},")
print(f"      amp={amp_optimal}")
print(f"   )")
print(f"   = {impact_calculated:.2f} pips")
print()

# Comparaison
ecart = abs(impact_calculated - impact_real_measured)
ecart_pct = (ecart / impact_real_measured) * 100

print("📊 COMPARAISON :")
print(f"   Calculé : {impact_calculated:.2f} pips")
print(f"   Mesuré  : {impact_real_measured:.2f} pips")
print(f"   Écart   : {ecart:.2f} pips ({ecart_pct:.2f}%)")
print()

if ecart < 0.1:
    print("✅ PARFAIT : amp_optimal donne exactement l'impact réel !")
    print()
    print("=" * 80)
    print("💡 RECOMMANDATION :")
    print("=" * 80)
    print()
    print(f"Utiliser amp={amp_optimal:.3f} comme BASELINE au lieu de 2.5")
    print()
    print("AVANTAGES :")
    print(f"  ✅ Baseline validée empiriquement (cas 11.09)")
    print(f"  ✅ Point de référence calibré sur données réelles")
    print(f"  ✅ Écarts relatifs plus significatifs")
    print()
    print("MÉTHODE PROPOSÉE (Option A) :")
    print()
    print("Pour chaque date :")
    print(f"  1. Calculer impact avec amp={amp_optimal:.3f} (baseline)")
    print("  2. Trouver amp_optimal réel")
    print(f"  3. delta_amp = (amp_optimal - {amp_optimal:.3f}) / {amp_optimal:.3f}")
    print("  4. Chercher corrélation : delta_amp = f(R², amplitude, durée)")
    print()
    print("=" * 80)
    print(f"🎯 VALIDATION : amp={amp_optimal:.3f} → {impact_calculated:.2f} pips ✅")
    print("=" * 80)
else:
    print(f"⚠️ ÉCART DÉTECTÉ : {ecart:.2f} pips")
    print()
    print("Possible cause : Arrondi amp_optimal ?")
    print()
    print("Valeur exacte amp_optimal depuis optimisation :")
    print("(Vérifier dans step5_output.json)")
