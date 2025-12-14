#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG SCRIPT - Tester calcul impact
"""

import sys
sys.path.append('..')

from formulas_validated_v2 import ImpactPredictor

# Test CPI US
print("=" * 80)
print("DEBUG - CPI US")
print("=" * 80)

events_data_cpi = {
    'nb_events': 1,
    'scores': [30],
    'surprises': [15.5],
    'directions': ['UP'],
    'families': ['CPI']
}

predictor = ImpactPredictor()

# Calculer features
features = predictor.calculate_features(events_data_cpi)

print("\n📊 FEATURES CALCULÉES:")
print(f"  nb_events        = {features.nb_events}")
print(f"  score_cumule     = {features.score_cumule}")
print(f"  score_moyen      = {features.score_moyen}")
print(f"  surprise_max     = {features.surprise_max}")
print(f"  surprise_moyenne = {features.surprise_moyenne}")
print(f"  surprise_cumule  = {features.surprise_cumule}")
print(f"  ratio_concordance= {features.ratio_concordance}")
print(f"  coherence_famille= {features.coherence_famille}")

# Prédiction ML
impact = predictor.predict_ml(features)

print(f"\n🎯 CALCUL MANUEL:")
print(f"  intercept = {predictor.coefficients['intercept']}")

calculation = predictor.coefficients['intercept']
print(f"\n  Démarrage: {calculation:.2f}")

calculation += predictor.coefficients['nb_events'] * features.nb_events
print(f"  + nb_events ({predictor.coefficients['nb_events']:.2f} × {features.nb_events}) = {calculation:.2f}")

calculation += predictor.coefficients['score_cumule'] * features.score_cumule
print(f"  + score_cumule ({predictor.coefficients['score_cumule']:.3f} × {features.score_cumule}) = {calculation:.2f}")

calculation += predictor.coefficients['score_moyen'] * features.score_moyen
print(f"  + score_moyen ({predictor.coefficients['score_moyen']:.3f} × {features.score_moyen}) = {calculation:.2f}")

calculation += predictor.coefficients['surprise_max'] * features.surprise_max
print(f"  + surprise_max ({predictor.coefficients['surprise_max']:.3f} × {features.surprise_max}) = {calculation:.2f}")

calculation += predictor.coefficients['surprise_moyenne'] * features.surprise_moyenne
print(f"  + surprise_moyenne ({predictor.coefficients['surprise_moyenne']:.3f} × {features.surprise_moyenne}) = {calculation:.2f}")

calculation += predictor.coefficients['surprise_cumule'] * features.surprise_cumule
print(f"  + surprise_cumule ({predictor.coefficients['surprise_cumule']:.3f} × {features.surprise_cumule}) = {calculation:.2f}")

calculation += predictor.coefficients['ratio_concordance'] * features.ratio_concordance
print(f"  + ratio_concordance ({predictor.coefficients['ratio_concordance']:.3f} × {features.ratio_concordance}) = {calculation:.2f}")

calculation += predictor.coefficients['coherence_famille'] * features.coherence_famille
print(f"  + coherence_famille ({predictor.coefficients['coherence_famille']:.3f} × {features.coherence_famille}) = {calculation:.2f}")

print(f"\n💡 RÉSULTAT FINAL:")
print(f"  Avant cap : {calculation:.2f} pips")
print(f"  Impact retourné par predict_ml() : {impact:.2f} pips")

print("\n" + "=" * 80)
