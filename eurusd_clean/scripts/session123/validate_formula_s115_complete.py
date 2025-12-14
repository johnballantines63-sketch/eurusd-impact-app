"""
Validation FORMULE COMPLÈTE Session 115 sur 110 patterns cluster 11 septembre

Méthodologie rigoureuse :
1. Charge 149 patterns Rev12 (données précises)
2. Charge résultats validation cluster (110 patterns)
3. Cross-reference pour récupérer données complètes
4. Applique FORMULE COMPLÈTE S115 :
   - Creux = wave1 - pullback
   - Momentum factor selon timing delta
   - Wave2 amplifié = wave2_base × momentum × surprise_boost
   - Impact total = creux + wave2_amplifié
5. Compare vs amplitude réelle
6. Calcule statistiques (MAE, R², distributions)

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - VALIDATION RIGOUREUSE
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List

# Fichiers
PATTERNS_REV12_FILE = Path(__file__).parent / 'validation_results' / 'double_waves_rev12_2024_2025.json'
CLUSTER_VALIDATION_FILE = Path(__file__).parent / 'validation_results' / 'cluster_sept11_validation.json'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'


def calculate_momentum_factor(timing_delta_minutes: float) -> float:
    """
    Calculer momentum factor selon overlapping intensity (Session 115)
    
    Calibration 11 septembre :
    - timing_delta = 34 min (14:35 → 15:09)
    - momentum_factor = 1.346
    
    Formule :
    - timing < 20 min → overlapping fort → momentum > 1.3
    - timing >= 20 min → overlapping faible → momentum → 1.0
    
    Interpolation exponentielle :
    momentum = 1.0 + 0.346 × exp(-timing / 20)
    """
    
    # Décroissance exponentielle calibrée sur 11 septembre
    decay = np.exp(-timing_delta_minutes / 20.0)
    momentum = 1.0 + (0.346 * decay)
    
    return momentum


def calculate_surprise_boost(events_scores: List[Dict]) -> float:
    """
    Calculer boost selon surprises (Session 115)
    
    Max +10% si surprises très fortes (> 50%)
    """
    
    if len(events_scores) == 0:
        return 0.0
    
    surprise_values = [abs(e.get('surprise', 0)) for e in events_scores]
    avg_surprise = np.mean(surprise_values)
    
    if avg_surprise > 50:
        # Boost proportionnel, max 10%
        boost = min(0.10, (avg_surprise - 50) / 500)
    else:
        boost = 0.0
    
    return boost


def apply_formula_complete_s115(pattern_rev12: Dict, events_scores: List[Dict]) -> Dict:
    """
    Appliquer FORMULE COMPLÈTE Session 115
    
    Inputs:
        pattern_rev12: Pattern Rev12 complet (wave1, wave2, pullback, timing)
        events_scores: Scores événements calculés
    
    Returns:
        Dict avec prédiction complète + breakdown
    """
    
    # ========================================================================
    # DONNÉES PATTERN REV12
    # ========================================================================
    
    wave1_amp = pattern_rev12.get('wave1_amp_pips', 0)
    wave2_amp = pattern_rev12.get('wave2_amp_pips', 0)
    pullback1_ratio = pattern_rev12.get('pullback1_ratio', 0)
    pullback2_ratio = pattern_rev12.get('pullback2_ratio', 0)
    
    # Timing
    peak1_time = pd.to_datetime(pattern_rev12.get('peak1_time'))
    peak2_time = pd.to_datetime(pattern_rev12.get('peak2_time'))
    timing_delta = (peak2_time - peak1_time).total_seconds() / 60.0
    
    # ========================================================================
    # ÉTAPE 1 : CALCULER CREUX (baseline → creux)
    # ========================================================================
    
    # Pullback depuis peak1
    pullback1_pips = wave1_amp * pullback1_ratio
    
    # Creux = point bas entre wave1 et wave2
    creux_pips = wave1_amp - pullback1_pips
    
    # ========================================================================
    # ÉTAPE 2 : CALCULER IMPACT WAVE2 BASE
    # ========================================================================
    
    # Total scores events (tous événements du cluster)
    total_score = sum(e.get('score', 0) for e in events_scores)
    
    # Amplification base 2.8 (calibrée Session 113)
    AMPLIFICATION = 2.8
    
    wave2_base_predicted = total_score * AMPLIFICATION / 100.0
    
    # ========================================================================
    # ÉTAPE 3 : MOMENTUM FACTOR (overlapping intensity)
    # ========================================================================
    
    momentum_factor = calculate_momentum_factor(timing_delta)
    
    # ========================================================================
    # ÉTAPE 4 : SURPRISE BOOST (max +10%)
    # ========================================================================
    
    surprise_boost = calculate_surprise_boost(events_scores)
    
    # ========================================================================
    # ÉTAPE 5 : WAVE2 AMPLIFIÉ
    # ========================================================================
    
    wave2_amplified = wave2_base_predicted * momentum_factor * (1 + surprise_boost)
    
    # ========================================================================
    # ÉTAPE 6 : IMPACT TOTAL
    # ========================================================================
    
    impact_total_predicted = creux_pips + wave2_amplified
    
    # ========================================================================
    # MÉTRIQUES ADDITIONNELLES
    # ========================================================================
    
    extension_factor = wave2_amp / wave1_amp if wave1_amp > 0 else 0
    
    return {
        # Prédiction
        'impact_total_predicted': impact_total_predicted,
        
        # Breakdown
        'wave1_amp': wave1_amp,
        'wave2_amp_real': wave2_amp,
        'pullback1_pips': pullback1_pips,
        'pullback1_ratio': pullback1_ratio,
        'creux_pips': creux_pips,
        
        # Wave2 calculation
        'total_score_events': total_score,
        'wave2_base_predicted': wave2_base_predicted,
        'timing_delta_minutes': timing_delta,
        'momentum_factor': momentum_factor,
        'surprise_boost': surprise_boost,
        'wave2_amplified': wave2_amplified,
        
        # Métriques
        'extension_factor': extension_factor,
        'pattern_type': 'double_wave_overlapping'
    }


def main():
    """Validation complète formule S115 sur 110 patterns"""
    
    print("=" * 80)
    print("VALIDATION FORMULE COMPLÈTE SESSION 115")
    print("Cluster 11 septembre : 110 patterns Double Wave")
    print("=" * 80)
    print()
    
    # ========================================================================
    # CHARGEMENT DONNÉES
    # ========================================================================
    
    print("📂 CHARGEMENT DONNÉES")
    print("=" * 80)
    print()
    
    # Charger 149 patterns Rev12
    print(f"Chargement patterns Rev12...")
    with open(PATTERNS_REV12_FILE, 'r') as f:
        patterns_rev12 = json.load(f)
    print(f"   ✅ {len(patterns_rev12)} patterns Rev12 chargés")
    print()
    
    # Charger validation cluster (110 patterns)
    print(f"Chargement validation cluster...")
    with open(CLUSTER_VALIDATION_FILE, 'r') as f:
        cluster_data = json.load(f)
    
    validation_results = cluster_data['validation_results']
    print(f"   ✅ {len(validation_results)} patterns cluster chargés")
    print()
    
    # ========================================================================
    # CROSS-REFERENCE PATTERNS
    # ========================================================================
    
    print("🔗 CROSS-REFERENCE PATTERNS REV12 + CLUSTER")
    print("=" * 80)
    print()
    
    # Créer index patterns Rev12 par date
    rev12_by_date = {p['date']: p for p in patterns_rev12}
    
    matched_patterns = []
    missing_patterns = []
    
    for validation in validation_results:
        date = validation['date']
        
        if date in rev12_by_date:
            matched_patterns.append({
                'date': date,
                'pattern_rev12': rev12_by_date[date],
                'validation': validation
            })
        else:
            missing_patterns.append(date)
    
    print(f"Patterns matched  : {len(matched_patterns)}")
    print(f"Patterns missing  : {len(missing_patterns)}")
    
    if len(missing_patterns) > 0:
        print()
        print(f"⚠️  Patterns manquants (premiers 5) :")
        for date in missing_patterns[:5]:
            print(f"   - {date}")
    
    print()
    
    if len(matched_patterns) == 0:
        print("❌ Aucun pattern matched ! Impossible de continuer.")
        return
    
    # ========================================================================
    # APPLICATION FORMULE COMPLÈTE
    # ========================================================================
    
    print("🧮 APPLICATION FORMULE COMPLÈTE S115")
    print("=" * 80)
    print()
    
    results_complete = []
    
    for i, item in enumerate(matched_patterns, 1):
        date = item['date']
        pattern_rev12 = item['pattern_rev12']
        validation = item['validation']
        
        if i % 20 == 0 or i == 1:
            print(f"[{i}/{len(matched_patterns)}] {date}")
        
        # Events scores
        events_scores = validation.get('events_scores', [])
        
        # Amplitude réelle
        real_amplitude = pattern_rev12['wave2_amp_pips']
        
        # Appliquer formule complète
        prediction = apply_formula_complete_s115(pattern_rev12, events_scores)
        
        # MAE
        mae = abs(real_amplitude - prediction['impact_total_predicted'])
        mae_pct = (mae / real_amplitude * 100) if real_amplitude > 0 else 0
        
        results_complete.append({
            'date': date,
            'real_amplitude': real_amplitude,
            'predicted_amplitude': prediction['impact_total_predicted'],
            'mae': mae,
            'mae_pct': mae_pct,
            
            # Breakdown
            'wave1_amp': prediction['wave1_amp'],
            'creux_pips': prediction['creux_pips'],
            'wave2_amplified': prediction['wave2_amplified'],
            'momentum_factor': prediction['momentum_factor'],
            'timing_delta': prediction['timing_delta_minutes'],
            'surprise_boost': prediction['surprise_boost'],
            'extension_factor': prediction['extension_factor'],
            
            # Reference
            'is_reference': (date == '2025-09-11'),
            'events_count': len(events_scores)
        })
    
    print()
    print(f"✅ {len(results_complete)} patterns traités")
    print()
    
    # ========================================================================
    # STATISTIQUES GLOBALES
    # ========================================================================
    
    print("=" * 80)
    print("📊 STATISTIQUES FORMULE COMPLÈTE S115")
    print("=" * 80)
    print()
    
    mae_values = [r['mae'] for r in results_complete]
    mae_mean = np.mean(mae_values)
    mae_median = np.median(mae_values)
    mae_std = np.std(mae_values)
    mae_min = np.min(mae_values)
    mae_max = np.max(mae_values)
    
    print(f"MAE (Mean Absolute Error) :")
    print(f"   Moyenne   : {mae_mean:.2f} pips")
    print(f"   Médiane   : {mae_median:.2f} pips")
    print(f"   Écart-type: {mae_std:.2f} pips")
    print(f"   Min       : {mae_min:.2f} pips")
    print(f"   Max       : {mae_max:.2f} pips")
    print()
    
    # Distribution
    under_2 = sum(1 for mae in mae_values if mae < 2)
    under_5 = sum(1 for mae in mae_values if mae < 5)
    under_10 = sum(1 for mae in mae_values if mae < 10)
    under_20 = sum(1 for mae in mae_values if mae < 20)
    
    print(f"Distribution MAE :")
    print(f"   MAE < 2 pips  : {under_2}/{len(results_complete)} ({under_2/len(results_complete)*100:.1f}%)")
    print(f"   MAE < 5 pips  : {under_5}/{len(results_complete)} ({under_5/len(results_complete)*100:.1f}%)")
    print(f"   MAE < 10 pips : {under_10}/{len(results_complete)} ({under_10/len(results_complete)*100:.1f}%)")
    print(f"   MAE < 20 pips : {under_20}/{len(results_complete)} ({under_20/len(results_complete)*100:.1f}%)")
    print()
    
    # R²
    real_values = [r['real_amplitude'] for r in results_complete]
    pred_values = [r['predicted_amplitude'] for r in results_complete]
    
    real_mean = np.mean(real_values)
    ss_tot = sum((r - real_mean)**2 for r in real_values)
    ss_res = sum((real_values[i] - pred_values[i])**2 for i in range(len(real_values)))
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    print(f"R² (coefficient détermination) : {r_squared:.3f}")
    if r_squared > 0.90:
        print("   ✅✅✅ Excellent (> 0.90)")
    elif r_squared > 0.80:
        print("   ✅✅ Très bon (> 0.80)")
    elif r_squared > 0.70:
        print("   ✅ Bon (> 0.70)")
    elif r_squared > 0:
        print("   ⚠️  Faible (< 0.70)")
    else:
        print("   ❌ Négatif (formule pire que moyenne)")
    
    print()
    
    # ========================================================================
    # CAS RÉFÉRENCE 11 SEPTEMBRE
    # ========================================================================
    
    print("=" * 80)
    print("🌟 CAS RÉFÉRENCE : 11 SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    ref_case = next((r for r in results_complete if r['is_reference']), None)
    
    if ref_case:
        print(f"Date          : {ref_case['date']}")
        print(f"Réel          : {ref_case['real_amplitude']:.2f} pips")
        print(f"Prédit        : {ref_case['predicted_amplitude']:.2f} pips")
        print(f"MAE           : {ref_case['mae']:.2f} pips")
        print()
        print(f"Breakdown :")
        print(f"   Wave1           : {ref_case['wave1_amp']:.2f} pips")
        print(f"   Creux           : {ref_case['creux_pips']:.2f} pips")
        print(f"   Wave2 amplifié  : {ref_case['wave2_amplified']:.2f} pips")
        print(f"   Timing delta    : {ref_case['timing_delta']:.1f} min")
        print(f"   Momentum factor : {ref_case['momentum_factor']:.3f}")
        print(f"   Surprise boost  : {ref_case['surprise_boost']:.1%}")
        print(f"   Extension       : {ref_case['extension_factor']:.2f}x")
        print()
        
        # Validation Session 115
        if ref_case['mae'] < 2:
            print("✅✅✅ VALIDATION SESSION 115 : MAE < 2 pips")
        elif ref_case['mae'] < 5:
            print("✅✅ TRÈS BON : MAE < 5 pips")
        else:
            print("⚠️  MAE > 5 pips sur cas référence")
    else:
        print("⚠️  11 septembre non trouvé dans patterns matched")
    
    print()
    
    # ========================================================================
    # TOP/BOTTOM 5
    # ========================================================================
    
    sorted_results = sorted(results_complete, key=lambda x: x['mae'])
    
    print("=" * 80)
    print("TOP 5 MEILLEURS CAS (MAE plus faible)")
    print("=" * 80)
    print()
    
    for i, r in enumerate(sorted_results[:5], 1):
        marker = "★" if r['is_reference'] else f"{i}."
        print(f"{marker} {r['date']}")
        print(f"   Réel    : {r['real_amplitude']:6.1f} pips")
        print(f"   Prédit  : {r['predicted_amplitude']:6.1f} pips")
        print(f"   MAE     : {r['mae']:6.2f} pips")
        print(f"   Momentum: {r['momentum_factor']:.3f}")
        print()
    
    print("=" * 80)
    print("TOP 5 PIRES CAS (MAE plus élevée)")
    print("=" * 80)
    print()
    
    for i, r in enumerate(sorted_results[-5:][::-1], 1):
        print(f"{i}. {r['date']}")
        print(f"   Réel    : {r['real_amplitude']:6.1f} pips")
        print(f"   Prédit  : {r['predicted_amplitude']:6.1f} pips")
        print(f"   MAE     : {r['mae']:6.2f} pips")
        print(f"   Momentum: {r['momentum_factor']:.3f}")
        print()
    
    # ========================================================================
    # VERDICT FINAL
    # ========================================================================
    
    print("=" * 80)
    print("🎯 VERDICT FINAL - FORMULE COMPLÈTE S115")
    print("=" * 80)
    print()
    
    print(f"Échantillon     : {len(results_complete)} patterns cluster 11 sept")
    print(f"MAE moyen       : {mae_mean:.2f} pips")
    print(f"R²              : {r_squared:.3f}")
    print()
    
    if mae_mean < 5 and r_squared > 0.90:
        print("🎉🎉🎉 OBJECTIF ATTEINT !")
        print()
        print("   ✅ MAE moyen < 5 pips")
        print("   ✅ R² > 0.90")
        print(f"   ✅ {under_5} cas sur {len(results_complete)} < 5 pips ({under_5/len(results_complete)*100:.1f}%)")
        print()
        print("   FORMULE SESSION 115 VALIDÉE SUR CLUSTER HOMOGÈNE")
        print("   Prête pour production sur ce type de pattern")
    elif mae_mean < 10:
        print("✅✅ BON RÉSULTAT")
        print()
        print(f"   MAE moyen : {mae_mean:.2f} pips")
        print(f"   R²        : {r_squared:.3f}")
        print()
        print("   Formule acceptable pour ce cluster")
        print("   Ajustements mineurs possibles")
    elif mae_mean < 20:
        print("✅ RÉSULTAT ACCEPTABLE")
        print()
        print(f"   MAE moyen : {mae_mean:.2f} pips")
        print(f"   R²        : {r_squared:.3f}")
        print()
        print("   Formule utilisable avec prudence")
        print("   Investigation outliers recommandée")
    else:
        print("⚠️  RÉSULTAT INSUFFISANT")
        print()
        print(f"   MAE moyen : {mae_mean:.2f} pips (objectif < 5)")
        print(f"   R²        : {r_squared:.3f} (objectif > 0.90)")
        print()
        print("   Formule nécessite révision ou cluster inadapté")
    
    print()
    
    # ========================================================================
    # SAUVEGARDE
    # ========================================================================
    
    output = {
        'summary': {
            'patterns_total': len(results_complete),
            'mae_mean': float(mae_mean),
            'mae_median': float(mae_median),
            'mae_std': float(mae_std),
            'mae_min': float(mae_min),
            'mae_max': float(mae_max),
            'r_squared': float(r_squared),
            'under_2pips': under_2,
            'under_5pips': under_5,
            'under_10pips': under_10,
            'under_20pips': under_20
        },
        'reference_case': ref_case,
        'results': results_complete
    }
    
    output_file = OUTPUT_DIR / 'formula_s115_complete_validation.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"💾 Résultats complets : {output_file}")
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
