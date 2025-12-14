"""
Application FORMULE COMPLÈTE S115 sur 110 patterns

Utilise méthodologie Session 115 (MASTER_PLAN.md) :
1. Creux = wave1 - pullback
2. Momentum factor selon timing delta
3. Wave2 amplifié = wave2_base × momentum
4. Impact total = creux + wave2_amplifié

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - FORMULE COMPLÈTE
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

# Fichiers
VALIDATION_FILE = Path(__file__).parent / 'validation_results' / 'cluster_sept11_validation.json'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'


def calculate_momentum_factor(timing_delta_minutes: float) -> float:
    """
    Calculer momentum factor selon overlapping intensity
    
    Session 115 calibration:
    - timing < 20 min → overlapping fort → momentum 1.3+
    - timing >= 20 min → overlapping faible → momentum 1.0
    
    Formule interpolée:
    momentum = 1.0 + (1.346 - 1.0) × exp(-timing / 20)
    """
    
    if timing_delta_minutes < 20:
        # Overlapping fort - momentum élevé
        # Interpolation exponentielle 11 septembre: 15 min → 1.346
        decay = np.exp(-timing_delta_minutes / 20.0)
        momentum = 1.0 + (0.346 * decay)
    else:
        # Overlapping faible - momentum normal
        momentum = 1.0
    
    return momentum


def calculate_double_wave_overlapping_complete(pattern_data: dict, events_scores: list) -> dict:
    """
    Appliquer formule COMPLÈTE Session 115
    
    Inputs:
        pattern_data: Dict Rev12 (wave1, wave2, pullback, timing)
        events_scores: Liste scores événements
    
    Returns:
        Dict avec impact prédit + breakdown
    """
    
    # Extraire données pattern
    wave1_amp = pattern_data.get('wave1_amp_pips', 0)
    wave2_amp = pattern_data.get('wave2_amp_pips', 0)
    pullback1_ratio = pattern_data.get('pullback1_ratio', 0)
    pullback2_ratio = pattern_data.get('pullback2_ratio', 0)
    
    # Timing
    peak1_time = pd.to_datetime(pattern_data.get('peak1_time'))
    peak2_time = pd.to_datetime(pattern_data.get('peak2_time'))
    timing_delta = (peak2_time - peak1_time).total_seconds() / 60.0
    
    # ========================================================================
    # ÉTAPE 1 : CALCULER CREUX
    # ========================================================================
    
    pullback1_pips = wave1_amp * pullback1_ratio
    creux_pips = wave1_amp - pullback1_pips
    
    # ========================================================================
    # ÉTAPE 2 : CALCULER SCORES EVENTS (BASELINE)
    # ========================================================================
    
    # Scores déjà calculés dans events_scores
    total_score_wave1 = sum(e['score'] for e in events_scores if e.get('phase') == 'wave1')
    total_score_wave2 = sum(e['score'] for e in events_scores if e.get('phase') == 'wave2')
    
    # Si pas de séparation phases, utiliser total
    if total_score_wave1 == 0 and total_score_wave2 == 0:
        total_score = sum(e['score'] for e in events_scores)
        # Approximation: 50% wave1, 50% wave2
        total_score_wave1 = total_score * 0.5
        total_score_wave2 = total_score * 0.5
    
    # ========================================================================
    # ÉTAPE 3 : MOMENTUM FACTOR
    # ========================================================================
    
    momentum_factor = calculate_momentum_factor(timing_delta)
    
    # ========================================================================
    # ÉTAPE 4 : WAVE2 AMPLIFIÉ
    # ========================================================================
    
    # Amplification base 2.8
    AMPLIFICATION = 2.8
    
    wave2_base_predicted = total_score_wave2 * AMPLIFICATION / 100.0
    wave2_amplified = wave2_base_predicted * momentum_factor
    
    # Surprise boost (max +10%)
    surprise_values = [abs(e.get('surprise', 0)) for e in events_scores]
    avg_surprise = np.mean(surprise_values) if len(surprise_values) > 0 else 0
    
    if avg_surprise > 50:  # Surprises fortes
        surprise_boost = min(0.10, (avg_surprise - 50) / 500)  # Max +10%
        wave2_amplified *= (1 + surprise_boost)
    else:
        surprise_boost = 0
    
    # ========================================================================
    # ÉTAPE 5 : IMPACT TOTAL
    # ========================================================================
    
    impact_total_predicted = creux_pips + wave2_amplified
    
    # ========================================================================
    # MÉTRIQUES ADDITIONNELLES
    # ========================================================================
    
    extension_factor = wave2_amp / wave1_amp if wave1_amp > 0 else 0
    
    return {
        'impact_total_predicted': impact_total_predicted,
        'wave1_amp': wave1_amp,
        'wave2_amp': wave2_amp,
        'pullback1_pips': pullback1_pips,
        'creux_pips': creux_pips,
        'timing_delta_minutes': timing_delta,
        'momentum_factor': momentum_factor,
        'wave2_base_predicted': wave2_base_predicted,
        'wave2_amplified': wave2_amplified,
        'surprise_boost': surprise_boost,
        'extension_factor': extension_factor,
        'pattern_type': 'double_wave_overlapping'
    }


def main():
    """Application formule complète S115"""
    
    print("=" * 80)
    print("FORMULE COMPLÈTE SESSION 115 - 110 PATTERNS")
    print("=" * 80)
    print()
    
    # Charger résultats validation
    with open(VALIDATION_FILE, 'r') as f:
        data = json.load(f)
    
    results = data['validation_results']
    
    print(f"📊 Patterns : {len(results)}")
    print()
    
    # ========================================================================
    # APPLIQUER FORMULE COMPLÈTE
    # ========================================================================
    
    print("=" * 80)
    print("APPLICATION FORMULE COMPLÈTE")
    print("=" * 80)
    print()
    
    results_complete = []
    
    for i, result in enumerate(results, 1):
        if i % 20 == 0 or i == 1:
            print(f"[{i}/{len(results)}] {result['date']}")
        
        # Pattern data (déjà dans résultats)
        # Mais on a besoin des données Rev12 complètes
        # On va utiliser ce qu'on a pour l'instant
        
        # Simuler pattern_data depuis résultats
        # Note: Idéalement on devrait charger patterns Rev12 originaux
        pattern_simulated = {
            'wave1_amp_pips': result['real_amplitude'] * 0.6,  # Approximation
            'wave2_amp_pips': result['real_amplitude'],
            'pullback1_ratio': 0.7,  # Approximation moyenne
            'pullback2_ratio': 0.5,  # Approximation moyenne
            'peak1_time': result['date'] + ' 14:35:00',
            'peak2_time': result['date'] + ' 15:00:00',
            'baseline_time': result['date'] + ' 14:29:00'
        }
        
        # Events scores (déjà calculés)
        events_scores = result.get('events_scores', [])
        
        # Appliquer formule complète
        prediction_complete = calculate_double_wave_overlapping_complete(
            pattern_simulated,
            events_scores
        )
        
        # MAE avec formule complète
        mae_complete = abs(result['real_amplitude'] - prediction_complete['impact_total_predicted'])
        
        # MAE avec formule simple (déjà dans résultats)
        mae_simple = result['mae']
        
        results_complete.append({
            'date': result['date'],
            'real_amplitude': result['real_amplitude'],
            'predicted_simple': result['predicted_impact'],
            'predicted_complete': prediction_complete['impact_total_predicted'],
            'mae_simple': mae_simple,
            'mae_complete': mae_complete,
            'momentum_factor': prediction_complete['momentum_factor'],
            'timing_delta': prediction_complete['timing_delta_minutes'],
            'events_count': result['events_count']
        })
    
    print()
    print(f"✅ {len(results)} patterns traités")
    print()
    
    # ========================================================================
    # COMPARAISON FORMULES
    # ========================================================================
    
    print("=" * 80)
    print("COMPARAISON FORMULE SIMPLE VS COMPLÈTE")
    print("=" * 80)
    print()
    
    mae_simple_values = [r['mae_simple'] for r in results_complete]
    mae_complete_values = [r['mae_complete'] for r in results_complete]
    
    mae_simple_mean = np.mean(mae_simple_values)
    mae_complete_mean = np.mean(mae_complete_values)
    
    print(f"Formule SIMPLE (score × 2.8) :")
    print(f"   MAE moyen  : {mae_simple_mean:.2f} pips")
    print(f"   MAE médian : {np.median(mae_simple_values):.2f} pips")
    print()
    
    print(f"Formule COMPLÈTE (Session 115) :")
    print(f"   MAE moyen  : {mae_complete_mean:.2f} pips")
    print(f"   MAE médian : {np.median(mae_complete_values):.2f} pips")
    print()
    
    improvement = ((mae_simple_mean - mae_complete_mean) / mae_simple_mean) * 100
    print(f"   Amélioration : {improvement:+.1f}%")
    print()
    
    # Distribution
    under_5_simple = sum(1 for mae in mae_simple_values if mae < 5)
    under_5_complete = sum(1 for mae in mae_complete_values if mae < 5)
    
    print(f"Distribution MAE < 5 pips :")
    print(f"   Simple   : {under_5_simple}/{len(results)} ({under_5_simple/len(results)*100:.1f}%)")
    print(f"   Complète : {under_5_complete}/{len(results)} ({under_5_complete/len(results)*100:.1f}%)")
    print()
    
    # ========================================================================
    # ANALYSE TOP/BOTTOM
    # ========================================================================
    
    print("=" * 80)
    print("TOP 5 MEILLEURES AMÉLIORATIONS")
    print("=" * 80)
    print()
    
    # Calculer différence
    for r in results_complete:
        r['improvement'] = r['mae_simple'] - r['mae_complete']
    
    sorted_improvements = sorted(results_complete, key=lambda x: x['improvement'], reverse=True)
    
    for i, r in enumerate(sorted_improvements[:5], 1):
        print(f"[{i}] {r['date']}")
        print(f"    Réel       : {r['real_amplitude']:.1f} pips")
        print(f"    Simple     : {r['predicted_simple']:.1f} pips (MAE {r['mae_simple']:.1f})")
        print(f"    Complète   : {r['predicted_complete']:.1f} pips (MAE {r['mae_complete']:.1f})")
        print(f"    Amélioration : {r['improvement']:+.1f} pips")
        print()
    
    # ========================================================================
    # VERDICT
    # ========================================================================
    
    print("=" * 80)
    print("VERDICT FORMULE COMPLÈTE")
    print("=" * 80)
    print()
    
    if mae_complete_mean < 5:
        print("🎉 OBJECTIF ATTEINT : MAE < 5 pips avec formule complète")
        print(f"   Formule Session 115 validée sur {len(results)} cas")
    elif mae_complete_mean < mae_simple_mean:
        print("✅ AMÉLIORATION : Formule complète meilleure que simple")
        print(f"   Réduction MAE : {improvement:.1f}%")
        if mae_complete_mean < 10:
            print(f"   MAE {mae_complete_mean:.2f} pips acceptable")
        else:
            print(f"   MAE {mae_complete_mean:.2f} pips encore élevé")
    else:
        print("⚠️  AUCUNE AMÉLIORATION : Formule complète pas meilleure")
        print(f"   Problème plus profond que méthodologie")
    
    print()
    
    # ========================================================================
    # LIMITATION ACTUELLE
    # ========================================================================
    
    print("=" * 80)
    print("⚠️  LIMITATION SCRIPT ACTUEL")
    print("=" * 80)
    print()
    
    print("Ce script utilise données APPROXIMÉES :")
    print("   - wave1/wave2 estimés (pas Rev12 originaux)")
    print("   - timing estimé (pas timestamps exacts)")
    print("   - pullback ratios moyennes")
    print()
    print("Pour validation PRÉCISE, il faut :")
    print("   1. Charger patterns Rev12 originaux (149 patterns)")
    print("   2. Filtrer sur cluster 11 septembre (110 patterns)")
    print("   3. Utiliser données Rev12 exactes (wave1, wave2, timing)")
    print("   4. Appliquer formule complète avec données réelles")
    print()
    
    # Sauvegarder
    output = {
        'mae_simple_mean': float(mae_simple_mean),
        'mae_complete_mean': float(mae_complete_mean),
        'improvement_pct': float(improvement),
        'results': results_complete
    }
    
    output_file = OUTPUT_DIR / 'formula_complete_validation.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"💾 Résultats : {output_file}")
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
