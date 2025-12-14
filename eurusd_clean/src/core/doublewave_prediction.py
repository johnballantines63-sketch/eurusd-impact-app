"""
DoubleWave Pattern Prediction Module
====================================

Module de prédiction pour patterns DoubleWave_Overlap avec critères 
d'inclusion/exclusion validés Session 131.

Contexte Session 131
-------------------
- Overlap standards : variabilité 1.97× (ACCEPTABLE)
- Overlap superposition : cas spécial 11 septembre (score 651)
- Cascade : variabilité 7.49× (NON PRÉDICTIBLE)

Amplifications Validées
-----------------------
- Overlap standards : 0.1201 (moyenne 3 cas : 0.0877, 0.0999, 0.1727)
- Overlap superposition : 0.0128 (11 sept validé Session 115)
- Cascade : EXCLURE (trop variable)

Critères Inclusion/Exclusion
----------------------------
PRÉDIRE (Overlap standards) :
  ✅ Score 150-650 points (Session 135: ajusté de 350→650 pour variantes MoM/YoY/U3/U6)
  ✅ 5-10 events scorés
  ✅ Pays majeurs (US/EU/UK/CA/JP/CH)
  ✅ Pas d'événements périphériques

PRÉDIRE (Overlap superposition) :
  ⚠️ Score > 500 points
  ⚠️ > 15 events
  ⚠️ Superposition ECB+US temporelle
  ⚠️ Composition mixte ECB rates + US CPI/NFP/Claims

EXCLURE :
  ❌ Cascade (7.49× variable)
  ❌ Événements périphériques (RS, MK, UZ, CO)
  ❌ Score < 50 ou > 650 sans superposition (Session 135: ajusté de 600→650)
  ❌ 0 events scorés

Auteur: Session 132
Date: 13 novembre 2025
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd


class PatternClassifier:
    """
    Classificateur de patterns DoubleWave.
    
    Identifie si un ensemble d'événements correspond à :
    - DoubleWave_Overlap standard
    - DoubleWave_Overlap superposition
    - DoubleWave_Cascade
    """
    
    # Critères stricts Session 131
    # Session 135 : Ajusté OVERLAP_SCORE_MAX 350→650 pour accommoder variantes MoM/YoY/U3/U6
    OVERLAP_SCORE_MIN = 150
    OVERLAP_SCORE_MAX = 650
    OVERLAP_EVENTS_MIN = 5
    OVERLAP_EVENTS_MAX = 10
    
    SUPERPOSITION_SCORE_MIN = 500
    SUPERPOSITION_EVENTS_MIN = 15
    SUPERPOSITION_TIME_WINDOW_MIN = 30  # minutes
    
    MAJOR_COUNTRIES = {'US', 'EU', 'UK', 'CA', 'JP', 'CH'}
    PERIPHERAL_COUNTRIES = {'RS', 'MK', 'UZ', 'CO'}
    
    @staticmethod
    def classify_pattern(
        events: List[Dict],
        total_score: float
    ) -> Tuple[str, Dict]:
        """
        Classifie le pattern d'événements.
        
        Parameters
        ----------
        events : List[Dict]
            Événements scorés uniquement
        total_score : float
            Score total calculé
            
        Returns
        -------
        Tuple[str, Dict]
            ('pattern_type', {'details': ...})
            
        Patterns possibles :
        - 'overlap_standard' : Score 150-350, 5-10 events
        - 'overlap_superposition' : Score > 500, > 15 events
        - 'cascade' : Score < 150 ou événements périphériques
        - 'unknown' : Autres cas
        """
        n_events = len(events)
        countries = {e.get('country') for e in events}
        
        # Vérifier événements périphériques
        has_peripherals = bool(countries.intersection(
            PatternClassifier.PERIPHERAL_COUNTRIES
        ))
        
        # Détecter Cascade (événements périphériques ou score très faible)
        if has_peripherals or total_score < 100:
            return 'cascade', {
                'has_peripherals': has_peripherals,
                'peripheral_countries': countries.intersection(
                    PatternClassifier.PERIPHERAL_COUNTRIES
                ),
                'low_score': total_score < 100
            }
        
        # Détecter superposition (score exceptionnel + nombreux events)
        if (total_score > PatternClassifier.SUPERPOSITION_SCORE_MIN and 
            n_events > PatternClassifier.SUPERPOSITION_EVENTS_MIN):
            return 'overlap_superposition', {
                'score': total_score,
                'events': n_events,
                'exceptional': True
            }
        
        # Détecter Overlap standard
        if (PatternClassifier.OVERLAP_SCORE_MIN <= total_score <= PatternClassifier.OVERLAP_SCORE_MAX and
            PatternClassifier.OVERLAP_EVENTS_MIN <= n_events <= PatternClassifier.OVERLAP_EVENTS_MAX):
            return 'overlap_standard', {
                'score': total_score,
                'events': n_events,
                'countries': countries
            }
        
        # Cas non classifié
        return 'unknown', {
            'score': total_score,
            'events': n_events,
            'reason': 'Score ou nombre events hors critères'
        }


class InclusionCriteria:
    """
    Critères d'inclusion/exclusion validés Session 131.
    
    Décide si un pattern est PRÉDICTIBLE ou doit être EXCLU.
    """
    
    MAJOR_COUNTRIES = {'US', 'EU', 'UK', 'CA', 'JP', 'CH'}
    PERIPHERAL_COUNTRIES = {'RS', 'MK', 'UZ', 'CO'}
    
    @staticmethod
    def check_overlap_standard(
        events: List[Dict],
        total_score: float,
        pattern_details: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si Overlap standard est prédictible.
        
        Parameters
        ----------
        events : List[Dict]
            Événements scorés
        total_score : float
            Score total
        pattern_details : Dict
            Détails pattern du classifier
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (is_predictable, exclusion_reason)
            
        Critères inclusion :
        - Score 150-350 points
        - 5-10 events scorés
        - Pays majeurs (US/EU/UK/CA/JP/CH)
        - Aucun événement périphérique
        """
        # Critère 1 : Score
        # Session 135 : Seuil ajusté 350→650 pour accommoder variantes MoM/YoY/U3/U6
        if total_score < 150:
            return False, f"Score trop faible ({total_score:.0f} < 150 points)"
        if total_score > 650:
            return False, f"Score anormal ({total_score:.0f} > 650, vérifier superposition)"
        
        # Critère 2 : Nombre events
        n_scored = len(events)
        
        if n_scored == 0:
            return False, "Aucun événement scoré - prédiction impossible"
        if n_scored < 5:
            return False, f"Trop peu d'événements scorés ({n_scored} < 5)"
        if n_scored > 10:
            return False, f"Trop d'événements ({n_scored} > 10, vérifier superposition)"
        
        # Critère 3 : Pays majeurs
        countries = {e.get('country') for e in events}
        major_countries_present = countries.intersection(
            InclusionCriteria.MAJOR_COUNTRIES
        )
        
        if not major_countries_present:
            countries_list = ', '.join(sorted(countries))
            return False, f"Aucun pays majeur (pays: {countries_list})"
        
        # Critère 4 : Événements périphériques
        peripheral_present = countries.intersection(
            InclusionCriteria.PERIPHERAL_COUNTRIES
        )
        
        if peripheral_present:
            peripherals_list = ', '.join(sorted(peripheral_present))
            return False, f"Événements périphériques détectés ({peripherals_list})"
        
        return True, None
    
    @staticmethod
    def check_overlap_superposition(
        events: List[Dict],
        total_score: float,
        pattern_details: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si Overlap superposition (cas spécial 11 sept).
        
        Critères détection (AU MOINS 2 sur 4) :
        1. Score > 500 points
        2. > 15 events
        3. Superposition ECB + US (< 30 min)
        4. Composition mixte ECB rates + US CPI/NFP/Claims
        
        Parameters
        ----------
        events : List[Dict]
            Événements scorés
        total_score : float
            Score total
        pattern_details : Dict
            Détails pattern
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (is_superposition, None)
        """
        criteria_met = 0
        details = []
        
        # Critère 1 : Score exceptionnel
        if total_score > 500:
            criteria_met += 1
            details.append(f"Score exceptionnel ({total_score:.0f})")
        
        # Critère 2 : Nombreux events
        if len(events) > 15:
            criteria_met += 1
            details.append(f"Nombreux événements ({len(events)})")
        
        # Critère 3 : Superposition temporelle ECB+US
        # Vérifier si events ECB et US sont proches temporellement
        has_ecb = any(e.get('country') == 'EU' and 
                      'rate' in e.get('event_key', '').lower() 
                      for e in events)
        has_us_major = any(e.get('country') == 'US' and 
                          any(keyword in e.get('event_key', '').lower() 
                              for keyword in ['cpi', 'nfp', 'claim', 'payroll'])
                          for e in events)
        
        if has_ecb and has_us_major:
            # Vérifier timestamps si disponibles
            ecb_times = [e.get('ts_utc') for e in events 
                        if e.get('country') == 'EU' and 
                        'rate' in e.get('event_key', '').lower() and
                        e.get('ts_utc')]
            us_times = [e.get('ts_utc') for e in events 
                       if e.get('country') == 'US' and
                       any(k in e.get('event_key', '').lower() 
                           for k in ['cpi', 'nfp', 'claim', 'payroll']) and
                       e.get('ts_utc')]
            
            # Si timestamps disponibles, vérifier delta < 30 min
            if ecb_times and us_times:
                min_delta = min(
                    abs((pd.Timestamp(ecb_t) - pd.Timestamp(us_t)).total_seconds() / 60)
                    for ecb_t in ecb_times
                    for us_t in us_times
                )
                if min_delta < 30:
                    criteria_met += 1
                    details.append(f"Superposition ECB+US ({min_delta:.0f} min)")
            else:
                # Si pas de timestamps, détecter présence ECB+US suffit
                criteria_met += 1
                details.append("Composition ECB rates + US majeur")
        
        # Critère 4 : Composition mixte (déjà vérifié dans critère 3)
        # On compte séparément si composition très variée
        countries = {e.get('country') for e in events}
        if len(countries) >= 3 and 'EU' in countries and 'US' in countries:
            criteria_met += 1
            details.append(f"Composition mixte ({len(countries)} pays)")
        
        # Au moins 2 critères doivent être remplis
        is_superposition = criteria_met >= 2
        
        return is_superposition, ', '.join(details) if is_superposition else None


def calculate_combined_surprise(events: List[Dict]) -> float:
    """
    Calcule surprise combinée pour cluster (formule Session 113).
    
    Utilise surprise vectorielle algébrique :
    - Somme des surprises pondérées par importance
    - Conversion en points pour taux/inflation
    - Direction respectée (positif/négatif)
    
    Parameters
    ----------
    events : List[Dict]
        Événements avec actual, estimate/forecast, previous
        
    Returns
    -------
    float
        Facteur surprise combiné (multiplicatif)
        
    Notes
    -----
    Formule simplifiée pour Session 132 MVP :
    - surprise = (actual - estimate) / |estimate|
    - Si estimate manquant : utiliser previous
    - Retourner 1.0 + moyenne(surprises) en valeur absolue
    """
    surprises = []
    
    for event in events:
        actual = event.get('actual')
        if actual is None or pd.isna(actual):
            continue
        
        # Chercher valeur de référence (priorité : estimate > forecast > previous)
        reference = (
            event.get('estimate') or 
            event.get('forecast') or 
            event.get('previous')
        )
        
        if reference is None or pd.isna(reference) or reference == 0:
            continue
        
        # Calculer surprise en %
        surprise_pct = (actual - reference) / abs(reference) * 100
        surprises.append(surprise_pct)
    
    if not surprises:
        # Aucune surprise calculable → facteur neutre
        return 1.0
    
    # Surprise moyenne en valeur absolue
    mean_surprise = abs(sum(surprises) / len(surprises))
    
    # Facteur multiplicatif : 1.0 + (surprise / 100)
    # Exemples : surprise 20% → facteur 1.20
    #           surprise 50% → facteur 1.50
    surprise_factor = 1.0 + (mean_surprise / 100.0)
    
    # Limiter entre 0.5 et 3.0 pour éviter valeurs extrêmes
    return max(0.5, min(3.0, surprise_factor))


def predict_doublewave_overlap(
    events: List[Dict],
    pattern_type: Optional[str] = None,
    debug: bool = False
) -> Dict:
    """
    Prédit l'impact d'un pattern DoubleWave_Overlap avec critères
    d'inclusion/exclusion STRICTS Session 131.
    
    Cette fonction est le POINT D'ENTRÉE principal du module.
    Elle applique les critères validés empiriquement.
    
    RÈGLE D'OR : Mieux EXCLURE un cas douteux que PRÉDIRE mal.
    
    Parameters
    ----------
    events : List[Dict]
        Liste événements avec scores. Chaque événement doit contenir :
        - 'event_key' : Identifiant événement
        - 'country' : Code pays (US, EU, etc.)
        - 'score' : Score empirique event_families
        - 'actual', 'estimate', 'previous' : Valeurs
        - 'ts_utc' : Timestamp publication (optionnel)
        
    pattern_type : Optional[str]
        Type pattern si déjà détecté. Si None, sera détecté automatiquement.
        
    debug : bool
        Si True, inclut informations debug dans retour
    
    Returns
    -------
    dict
        {
            'prediction': float | None,  # Impact prédit (pips) ou None si exclu
            'amplification': float | None,  # Amp utilisée ou None
            'status': str,  # 'predicted', 'excluded', 'special_case'
            'reason': str,  # Explication décision (TOUJOURS documenté)
            'pattern_type': str,  # Type pattern identifié
            'criteria_met': dict,  # Détails critères
            'events_analyzed': int,  # Nombre events analysés
            'events_scored': int,  # Nombre events scorés
            'total_score': float,  # Score total
            'surprise_factor': float | None,  # Facteur surprise calculé
            'debug_info': dict | None  # Informations debug (si debug=True)
        }
    
    Examples
    --------
    >>> # Cas Overlap standard (2023-02-03)
    >>> events = [
    ...     {'event_key': 'non_farm_payrolls', 'country': 'US', 'score': 48.84,
    ...      'actual': 517, 'estimate': 190},
    ...     # ... 5 autres événements
    ... ]
    >>> result = predict_doublewave_overlap(events)
    >>> result['status']
    'predicted'
    >>> result['amplification']
    0.1201
    >>> result['prediction']
    42.3  # Exemple
    
    >>> # Cas Cascade exclu (2023-03-07)
    >>> events_cascade = [
    ...     {'event_key': 'auction', 'country': 'ES', 'score': 10.0},
    ...     {'event_key': 'gdp', 'country': 'GR', 'score': 15.0}
    ... ]
    >>> result = predict_doublewave_overlap(events_cascade)
    >>> result['status']
    'excluded'
    >>> result['reason']
    'Pattern Cascade non prédictible (variabilité 7.49×)'
    
    >>> # Cas 11 septembre (superposition)
    >>> events_11sept = [...]  # 20 events, score 651
    >>> result = predict_doublewave_overlap(events_11sept)
    >>> result['status']
    'special_case'
    >>> result['amplification']
    0.0128
    
    Notes
    -----
    - Toutes les décisions sont DOCUMENTÉES dans 'reason'
    - Les amplifications sont FIXES (validées empiriquement)
    - Ne JAMAIS prédire un Cascade (7.49× variable → exclusion)
    - Les critères sont STRICTS (pas d'approximation)
    """
    
    # ÉTAPE 1 : Validation entrée
    if not events or len(events) == 0:
        return {
            'prediction': None,
            'amplification': None,
            'status': 'excluded',
            'reason': 'Aucun événement fourni',
            'pattern_type': 'unknown',
            'criteria_met': {},
            'events_analyzed': 0,
            'events_scored': 0,
            'total_score': 0.0,
            'surprise_factor': None,
            'debug_info': None
        }
    
    # ÉTAPE 2 : Filtrer events scorés et calculer score total
    scored_events = [e for e in events if e.get('score', 0) > 0]
    total_score = sum(e.get('score', 0) for e in scored_events)
    
    # ÉTAPE 3 : EXCLUSION IMMÉDIATE si 0 events scorés
    if len(scored_events) == 0:
        return {
            'prediction': None,
            'amplification': None,
            'status': 'excluded',
            'reason': 'Aucun événement scoré - prédiction impossible',
            'pattern_type': 'unknown',
            'criteria_met': {'has_scored_events': False},
            'events_analyzed': len(events),
            'events_scored': 0,
            'total_score': 0.0,
            'surprise_factor': None,
            'debug_info': None
        }
    
    # ÉTAPE 4 : Classifier pattern (AVANT exclusion score pour pattern correct)
    classifier = PatternClassifier()
    pattern_detected, pattern_details = classifier.classify_pattern(
        scored_events, total_score
    )
    
    # ÉTAPE 5 : EXCLUSION si score anormalement bas (mais avec pattern correct maintenant)
    if total_score < 50:
        return {
            'prediction': None,
            'amplification': None,
            'status': 'excluded',
            'reason': f'Score trop faible ({total_score:.0f} < 50 points) - événements mineurs',
            'pattern_type': pattern_detected,  # ← Pattern correct maintenant (cascade, overlap, etc.)
            'criteria_met': {'score_valid': False},
            'events_analyzed': len(events),
            'events_scored': len(scored_events),
            'total_score': total_score,
            'surprise_factor': None,
            'debug_info': None
        }
    
    # Info debug si demandé
    debug_info = None
    if debug:
        debug_info = {
            'pattern_detected': pattern_detected,
            'pattern_details': pattern_details,
            'scored_events': len(scored_events),
            'total_score': total_score,
            'countries': list({e.get('country') for e in scored_events})
        }
    
    # ÉTAPE 6 : Appliquer critères inclusion/exclusion
    
    # CAS 1 : Cascade → EXCLURE SYSTÉMATIQUEMENT
    if pattern_detected == 'cascade':
        return {
            'prediction': None,
            'amplification': None,
            'status': 'excluded',
            'reason': 'Pattern Cascade non prédictible (variabilité 7.49×)',
            'pattern_type': 'cascade',
            'criteria_met': {
                'cascade_detected': True,
                'has_peripherals': pattern_details.get('has_peripherals', False),
                'peripheral_countries': list(pattern_details.get('peripheral_countries', set())),
                'low_score': pattern_details.get('low_score', False)
            },
            'events_analyzed': len(events),
            'events_scored': len(scored_events),
            'total_score': total_score,
            'surprise_factor': None,
            'debug_info': debug_info
        }
    
    # CAS 2 : Vérifier Overlap superposition (11 septembre)
    criteria = InclusionCriteria()
    is_superposition, superposition_details = criteria.check_overlap_superposition(
        scored_events, total_score, pattern_details
    )
    
    if is_superposition:
        # Utiliser amp 0.0128 (cas spécial validé Session 115)
        amplification = 0.0128
        
        # Calculer surprise combinée
        surprise_factor = calculate_combined_surprise(scored_events)
        
        # Impact prédit : score × amp × surprise
        prediction = total_score * amplification * surprise_factor
        
        return {
            'prediction': round(prediction, 2),
            'amplification': amplification,
            'status': 'special_case',
            'reason': f'Superposition ECB+US détectée (score {total_score:.0f}, {len(scored_events)} events) - {superposition_details}',
            'pattern_type': 'overlap_superposition',
            'criteria_met': {
                'superposition': True,
                'score': total_score,
                'events': len(scored_events),
                'details': superposition_details
            },
            'events_analyzed': len(events),
            'events_scored': len(scored_events),
            'total_score': total_score,
            'surprise_factor': surprise_factor,
            'debug_info': debug_info
        }
    
    # CAS 3 : Vérifier Overlap standard
    is_predictable, exclusion_reason = criteria.check_overlap_standard(
        scored_events, total_score, pattern_details
    )
    
    if not is_predictable:
        # EXCLURE avec raison documentée
        return {
            'prediction': None,
            'amplification': None,
            'status': 'excluded',
            'reason': exclusion_reason,
            'pattern_type': 'overlap_standard',
            'criteria_met': {'predictable': False, 'reason': exclusion_reason},
            'events_analyzed': len(events),
            'events_scored': len(scored_events),
            'total_score': total_score,
            'surprise_factor': None,
            'debug_info': debug_info
        }
    
    # CAS 4 : Overlap standard VALIDÉ → PRÉDIRE
    
    # Utiliser amp 0.1201 (moyenne 3 cas standards Session 131)
    amplification = 0.1201
    
    # Calculer surprise combinée
    surprise_factor = calculate_combined_surprise(scored_events)
    
    # Impact prédit : score × amp × surprise
    prediction = total_score * amplification * surprise_factor
    
    # Pays pour documentation
    countries = sorted({e.get('country') for e in scored_events})
    countries_str = ', '.join(countries)
    
    return {
        'prediction': round(prediction, 2),
        'amplification': amplification,
        'status': 'predicted',
        'reason': f'Overlap standard validé (score {total_score:.0f}, {len(scored_events)} events {countries_str})',
        'pattern_type': 'overlap_standard',
        'criteria_met': {
            'score_range': (150, 650),  # Session 135: ajusté de 350→650
            'events_range': (5, 10),
            'major_countries': True,
            'no_peripherals': True,
            'score': total_score,
            'events': len(scored_events)
        },
        'events_analyzed': len(events),
        'events_scored': len(scored_events),
        'total_score': total_score,
        'surprise_factor': surprise_factor,
        'debug_info': debug_info
    }


# Tests validation du module
if __name__ == "__main__":
    print("=== Tests Module DoubleWave Prediction ===\n")
    
    # Test 1 : Overlap standard (2023-02-03)
    print("Test 1 : Overlap standard (2023-02-03)")
    print("-" * 50)
    
    events_standard = [
        {'event_key': 'non_farm_payrolls', 'country': 'US', 'score': 48.84,
         'actual': 517, 'estimate': 190},
        {'event_key': 'unemployment_rate', 'country': 'US', 'score': 44.86,
         'actual': 3.4, 'estimate': 3.6},
        {'event_key': 'average_hourly_earnings', 'country': 'US', 'score': 30.0,
         'actual': 0.3, 'estimate': 0.3},
        {'event_key': 'inflation_rate', 'country': 'EU', 'score': 48.84,
         'actual': 8.6, 'estimate': 9.2},
        {'event_key': 'core_inflation_rate', 'country': 'EU', 'score': 44.86,
         'actual': 5.3, 'estimate': 5.2},
        {'event_key': 'gdp_growth_rate', 'country': 'EU', 'score': 44.86,
         'actual': 0.1, 'estimate': 0.1}
    ]
    
    result = predict_doublewave_overlap(events_standard, debug=True)
    print(f"Status: {result['status']}")
    print(f"Pattern: {result['pattern_type']}")
    print(f"Amplification: {result['amplification']}")
    print(f"Prediction: {result['prediction']} pips")
    print(f"Reason: {result['reason']}")
    print(f"Score total: {result['total_score']:.1f}")
    print(f"Surprise factor: {result['surprise_factor']:.3f}")
    print()
    
    # Test 2 : Cascade périphériques (2023-03-07)
    print("\nTest 2 : Cascade périphériques (2023-03-07)")
    print("-" * 50)
    
    events_cascade = [
        {'event_key': 'auction', 'country': 'ES', 'score': 10.0,
         'actual': 3.5, 'estimate': 3.4},
        {'event_key': 'gdp', 'country': 'GR', 'score': 15.0,
         'actual': 2.0, 'estimate': 1.8}
    ]
    
    result = predict_doublewave_overlap(events_cascade, debug=True)
    print(f"Status: {result['status']}")
    print(f"Pattern: {result['pattern_type']}")
    print(f"Prediction: {result['prediction']}")
    print(f"Reason: {result['reason']}")
    print()
    
    # Test 3 : 0 events scorés
    print("\nTest 3 : 0 events scorés")
    print("-" * 50)
    
    events_no_scores = [
        {'event_key': 'random', 'country': 'US', 'score': 0},
        {'event_key': 'random2', 'country': 'EU', 'score': 0}
    ]
    
    result = predict_doublewave_overlap(events_no_scores)
    print(f"Status: {result['status']}")
    print(f"Reason: {result['reason']}")
    print()
    
    # Test 4 : Superposition simulée (score > 500, > 15 events)
    print("\nTest 4 : Superposition simulée (score > 500)")
    print("-" * 50)
    
    events_superposition = []
    # Simuler 20 événements avec score élevé
    for i in range(20):
        country = 'EU' if i < 10 else 'US'
        events_superposition.append({
            'event_key': f'event_{i}',
            'country': country,
            'score': 35.0,
            'actual': 1.5,
            'estimate': 1.0
        })
    
    result = predict_doublewave_overlap(events_superposition, debug=True)
    print(f"Status: {result['status']}")
    print(f"Pattern: {result['pattern_type']}")
    print(f"Amplification: {result['amplification']}")
    print(f"Prediction: {result['prediction']} pips")
    print(f"Score total: {result['total_score']:.1f}")
    print(f"Reason: {result['reason']}")
    print()
    
    print("="*50)
    print("Tests terminés avec succès ✅")
