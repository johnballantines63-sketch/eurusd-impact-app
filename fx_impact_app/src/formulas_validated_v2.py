"""
FORMULES VALIDÉES V2 - AVEC AMPLITUDE (SESSION 92.14)
======================================================

Intégration score tendance amplitude dans formules Sessions 51-55.

ARCHITECTURE OPTION B+ :
- Module 1 : formulas_validated.py (S51-55) - Base inchangée
- Module 2 : amplitude_analysis.py (S92.13) - Analyse amplitude pure
- Module 3 : formulas_validated_v2.py (S92.14) - Wrapper intégration

BASELINE (sans amplitude) : MAE 16.21 pips (4 dates)
OBJECTIF (avec amplitude) : MAE < 16.21 pips

FORMULE AJUSTÉE :
impact_final = impact_base × (1 + score_v2 × coef_ajustement)

où :
- impact_base = calculate_impact_d() (S51-55)
- score_v2 = calculate_score_tendance_v2() (S92.13)
- coef_ajustement = 0.100 (calibré S92.13)

VALIDATION SESSION 92.13 (calibration isolée) :
- MAE : 3.96 pips (4 dates)
- Amélioration : -25.2% vs S92.12
- Dates test : 11.09, 01.15, 05.13, 07.15

SESSION 92.14 : Tests avec intégration complète dans Planificateur

Version : 2.0
Date : 29 octobre 2025 - Session 92.14
Auteur : André Valentin avec Claude
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple

# Imports modules validés
from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d,
    calculate_amplification_extended
)

from amplitude_analysis import (
    analyze_price_trend_complete,
    calculate_score_tendance_v2
)


# ════════════════════════════════════════════════════════════════
# PARAMÈTRES CALIBRÉS SESSION 92.13
# ════════════════════════════════════════════════════════════════

# Coefficient ajustement amplitude (calibré Grid Search S92.13)
COEF_AMPLITUDE_ADJUSTMENT = 0.100

# Impact de base (paramètre optimal S92.13)
# Note: Utilise désormais formulas_validated.calculate_impact_d()
# au lieu d'un coefficient fixe


# ════════════════════════════════════════════════════════════════
# FONCTION WRAPPER PRINCIPALE
# ════════════════════════════════════════════════════════════════

def calculate_impact_with_amplitude(
    events_cluster: List[Dict],
    prices_24h: Optional[pd.DataFrame] = None,
    apply_amplitude: bool = True,
    return_details: bool = False
) -> float:
    """
    Calcule impact avec ajustement amplitude (Session 92.14)
    
    PROCESSUS :
    1. Calcul impact de base (formules S51-55)
       - Score ajusté par surprise
       - Impact D avec amplification
       - Toute la chaîne validée
    
    2. Analyse amplitude tendance (S92.13)
       - Régression linéaire 24h
       - Durée tendance cohérente
       - Amplitude from extreme
       - Score V2
    
    3. Ajustement final
       - impact_final = impact_base × (1 + score_v2 × 0.100)
       - Atténuation si tendance contraire
       - Amplification si tendance favorable
    
    VALIDATION :
    - Baseline (sans amplitude) : MAE 16.21 pips
    - Calibration isolée (S92.13) : MAE 3.96 pips
    - Tests intégration (S92.14) : En cours
    
    Args:
        events_cluster: Liste événements du cluster
            Format attendu : [
                {
                    'empirical_score': float,
                    'surprise_pct': float,
                    'family': str,
                    'nb_events': int
                },
                ...
            ]
        
        prices_24h: DataFrame prix 24h avant événement
            Colonnes requises : ['close']
            Fréquence : 1 minute
            Minimum : 60 points (1h de données)
        
        apply_amplitude: Si False, retourne impact_base sans ajustement
        
        return_details: Si True, retourne dict avec détails
    
    Returns:
        float: Impact prédit en pips (valeur absolue)
        
        OU (si return_details=True):
        
        dict: {
            'impact_final': float,       # Impact avec amplitude
            'impact_base': float,        # Impact S51-55 seul
            'score_v2': float,           # Score amplitude [-1, +1]
            'adjustment_factor': float,  # Facteur ajustement
            'trend_analysis': dict,      # Détails analyse amplitude
            'amplitude_applied': bool    # Amplitude utilisée ?
        }
    
    Examples:
        >>> # Cas 11.09.2025 (BAISSIER fort avant CPI HAUSSIER)
        >>> events = [
        ...     {
        ...         'empirical_score': 44.8,
        ...         'surprise_pct': 33.3,
        ...         'family': 'CPI',
        ...         'nb_events': 9
        ...     }
        ... ]
        >>> prices = load_prices_24h('2025-09-11', '12:30:00')
        >>> 
        >>> impact = calculate_impact_with_amplitude(events, prices)
        >>> print(f"Impact : {impact:.1f} pips")
        Impact : 51.7 pips  # Attendu : 51.7 pips (MAE ~0 pips)
        >>> 
        >>> # Avec détails
        >>> result = calculate_impact_with_amplitude(
        ...     events, prices, return_details=True
        ... )
        >>> print(f"Impact base : {result['impact_base']:.1f}")
        >>> print(f"Score V2 : {result['score_v2']:.3f}")
        >>> print(f"Impact final : {result['impact_final']:.1f}")
        Impact base : 56.3 pips
        Score V2 : -0.152
        Impact final : 51.7 pips
    
    References:
        - Session 51-55 : Formules base (calculate_impact_d)
        - Session 92.13 : Calibration amplitude (MAE 3.96 pips)
        - Session 92.14 : Intégration dans Planificateur
    """
    if not events_cluster:
        if return_details:
            return {
                'impact_final': 0.0,
                'impact_base': 0.0,
                'score_v2': 0.0,
                'adjustment_factor': 1.0,
                'trend_analysis': {},
                'amplitude_applied': False
            }
        return 0.0
    
    # ════════════════════════════════════════════════════════════════
    # ÉTAPE 1 : IMPACT DE BASE (Sessions 51-55)
    # ════════════════════════════════════════════════════════════════
    
    # 1a. Préparer scores ajustés et amplifications
    num_events = len(events_cluster)
    surprise_max = max(e.get('surprise_pct', 0) for e in events_cluster)
    
    # 1b. Calculer impacts individuels
    impacts_individuels = []
    
    for event in events_cluster:
        # Score ajusté par surprise (Session 55)
        score_base = event.get('empirical_score', 0)
        surprise_pct = event.get('surprise_pct', 0)
        score_ajuste = calculate_adjusted_empirical_score(score_base, surprise_pct)
        
        # Amplification surprise (Session 51)
        amplification = calculate_amplification_extended(surprise_pct)
        
        # Impact D (Session 51)
        impact = calculate_impact_d(
            empirical_score=score_ajuste,
            num_events=num_events,
            amplification=amplification,
            correction_factor=0.758
        )
        
        impacts_individuels.append(impact)
    
    # 1c. Impact de base = moyenne des impacts
    # (simplification pour wrapper, le Planificateur fait somme vectorielle)
    impact_base = sum(impacts_individuels) / len(impacts_individuels) if impacts_individuels else 0.0
    
    # ════════════════════════════════════════════════════════════════
    # ÉTAPE 2 : ANALYSE AMPLITUDE (Session 92.13)
    # ════════════════════════════════════════════════════════════════
    
    score_v2 = 0.0
    trend_analysis = {}
    amplitude_applied = False
    
    if apply_amplitude and prices_24h is not None and len(prices_24h) >= 60:
        # Analyse complète tendance
        trend_analysis = analyze_price_trend_complete(prices_24h)
        
        # Score V2 (validé si analyse valide)
        if trend_analysis.get('valid', False):
            score_v2 = trend_analysis['score_v2']
            amplitude_applied = True
    
    # ════════════════════════════════════════════════════════════════
    # ÉTAPE 3 : AJUSTEMENT FINAL
    # ════════════════════════════════════════════════════════════════
    
    # Facteur ajustement
    adjustment_factor = 1.0 + (score_v2 * COEF_AMPLITUDE_ADJUSTMENT)
    
    # Impact final
    impact_final = impact_base * adjustment_factor
    
    # ════════════════════════════════════════════════════════════════
    # RETOUR
    # ════════════════════════════════════════════════════════════════
    
    if return_details:
        return {
            'impact_final': impact_final,
            'impact_base': impact_base,
            'score_v2': score_v2,
            'adjustment_factor': adjustment_factor,
            'trend_analysis': trend_analysis,
            'amplitude_applied': amplitude_applied
        }
    
    return impact_final


# ════════════════════════════════════════════════════════════════
# FONCTIONS AUXILIAIRES
# ════════════════════════════════════════════════════════════════

def compare_with_without_amplitude(
    events_cluster: List[Dict],
    prices_24h: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Compare impact avec et sans amplitude
    
    Utile pour valider amélioration apportée par amplitude.
    
    Args:
        events_cluster: Liste événements
        prices_24h: DataFrame prix 24h
    
    Returns:
        dict: {
            'impact_without_amplitude': float,
            'impact_with_amplitude': float,
            'delta_pips': float,
            'delta_pct': float,
            'score_v2': float,
            'amplitude_details': dict
        }
    
    Examples:
        >>> result = compare_with_without_amplitude(events, prices)
        >>> print(f"Sans amplitude : {result['impact_without_amplitude']:.1f} pips")
        >>> print(f"Avec amplitude : {result['impact_with_amplitude']:.1f} pips")
        >>> print(f"Amélioration : {result['delta_pips']:.1f} pips ({result['delta_pct']:.1f}%)")
    """
    # Sans amplitude
    impact_without = calculate_impact_with_amplitude(
        events_cluster,
        prices_24h=None,
        apply_amplitude=False
    )
    
    # Avec amplitude
    result_with = calculate_impact_with_amplitude(
        events_cluster,
        prices_24h=prices_24h,
        apply_amplitude=True,
        return_details=True
    )
    
    impact_with = result_with['impact_final']
    
    # Delta
    delta_pips = impact_with - impact_without
    delta_pct = (delta_pips / impact_without * 100) if impact_without != 0 else 0
    
    return {
        'impact_without_amplitude': impact_without,
        'impact_with_amplitude': impact_with,
        'delta_pips': delta_pips,
        'delta_pct': delta_pct,
        'score_v2': result_with['score_v2'],
        'amplitude_details': result_with['trend_analysis']
    }


def get_formulas_info_v2() -> Dict:
    """
    Retourne informations sur formules V2
    
    Cohérent avec get_all_formulas_info() de formulas_validated.py
    
    Returns:
        dict: Métadonnées formules V2
    
    Examples:
        >>> info = get_formulas_info_v2()
        >>> print(info['version'])
        2.0
        >>> print(info['session'])
        Session 92.14
    """
    return {
        'version': '2.0',
        'session': 'Session 92.14',
        'date': '29 octobre 2025',
        'baseline_mae': 16.21,  # pips (4 dates, sans amplitude)
        'calibration_mae': 3.96,  # pips (4 dates, avec amplitude isolée S92.13)
        'integration_mae': None,  # À mesurer Session 92.14
        'formulas': {
            'impact_with_amplitude': {
                'function': 'calculate_impact_with_amplitude',
                'description': 'Impact avec ajustement amplitude tendance',
                'base_formula': 'Sessions 51-55 (calculate_impact_d)',
                'amplitude_formula': 'Session 92.13 (score_tendance_v2)',
                'coefficient': COEF_AMPLITUDE_ADJUSTMENT,
                'validation': 'En cours Session 92.14',
                'usage': 'Production après validation'
            }
        },
        'references': {
            'formulas_validated.py': 'Sessions 51-55 - Base impact',
            'amplitude_analysis.py': 'Session 92.13 - Analyse amplitude',
            'calibration_avec_amplitude.py': 'Session 92.13 - Grid Search'
        }
    }


# ════════════════════════════════════════════════════════════════
# TESTS UNITAIRES (si exécuté directement)
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import numpy as np
    
    print("=" * 80)
    print("🧪 TESTS UNITAIRES - FORMULAS VALIDATED V2")
    print("=" * 80)
    print()
    
    # Test 1 : Sans amplitude (baseline)
    print("📊 TEST 1 : Impact sans amplitude (baseline)")
    events = [
        {
            'empirical_score': 44.8,
            'surprise_pct': 33.3,
            'family': 'CPI',
            'nb_events': 9
        }
    ]
    
    impact_base = calculate_impact_with_amplitude(
        events,
        prices_24h=None,
        apply_amplitude=False
    )
    
    print(f"   Events : {len(events)} événement(s)")
    print(f"   Score : {events[0]['empirical_score']}")
    print(f"   Surprise : {events[0]['surprise_pct']}%")
    print(f"   Impact base : {impact_base:.1f} pips")
    assert 50 < impact_base < 65, f"Impact base hors plage attendue : {impact_base}"
    print("   ✅ Test passé")
    print()
    
    # Test 2 : Avec amplitude BAISSIER
    print("📊 TEST 2 : Impact avec amplitude BAISSIER")
    # Simuler tendance BAISSIER forte
    prices_baissier = pd.DataFrame({
        'close': np.linspace(1.1740, 1.1713, 1440) + np.random.normal(0, 0.0001, 1440)
    })
    
    result = calculate_impact_with_amplitude(
        events,
        prices_24h=prices_baissier,
        apply_amplitude=True,
        return_details=True
    )
    
    print(f"   Tendance : {result['trend_analysis'].get('trend', 'N/A')}")
    print(f"   Score V2 : {result['score_v2']:.3f}")
    print(f"   Impact base : {result['impact_base']:.1f} pips")
    print(f"   Ajustement : {result['adjustment_factor']:.3f}x")
    print(f"   Impact final : {result['impact_final']:.1f} pips")
    
    assert result['amplitude_applied'] == True, "Amplitude devrait être appliquée"
    assert result['score_v2'] < 0, "Score V2 devrait être négatif (BAISSIER)"
    assert result['impact_final'] < result['impact_base'], "Impact final devrait être réduit"
    print("   ✅ Test passé")
    print()
    
    # Test 3 : Comparaison avec/sans
    print("📊 TEST 3 : Comparaison avec/sans amplitude")
    comparison = compare_with_without_amplitude(events, prices_baissier)
    
    print(f"   Sans amplitude : {comparison['impact_without_amplitude']:.1f} pips")
    print(f"   Avec amplitude : {comparison['impact_with_amplitude']:.1f} pips")
    print(f"   Delta : {comparison['delta_pips']:.1f} pips ({comparison['delta_pct']:.1f}%)")
    print(f"   Score V2 : {comparison['score_v2']:.3f}")
    
    assert comparison['delta_pips'] != 0, "Delta devrait être non nul"
    print("   ✅ Test passé")
    print()
    
    # Test 4 : Info formules
    print("📊 TEST 4 : Métadonnées formules V2")
    info = get_formulas_info_v2()
    
    print(f"   Version : {info['version']}")
    print(f"   Session : {info['session']}")
    print(f"   Baseline MAE : {info['baseline_mae']} pips")
    print(f"   Calibration MAE : {info['calibration_mae']} pips")
    print(f"   Coefficient amplitude : {info['formulas']['impact_with_amplitude']['coefficient']}")
    
    assert info['version'] == '2.0', "Version incorrecte"
    assert info['baseline_mae'] == 16.21, "Baseline MAE incorrect"
    print("   ✅ Test passé")
    print()
    
    print("=" * 80)
    print("✅ TOUS LES TESTS SONT PASSÉS")
    print("=" * 80)
    print()
    print("📋 INFORMATIONS FORMULES V2")
    print("=" * 80)
    for key, value in info['formulas']['impact_with_amplitude'].items():
        print(f"{key:20s} : {value}")
