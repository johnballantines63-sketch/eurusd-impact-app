"""
Double Wave Momentum Module
===========================

Ce module implémente la détection et prédiction du phénomène "Double Wave Momentum"
découvert et validé en Session 64.

Contexte
--------
Quand un cluster d'événements majeurs (surprise > 20%, ≥5 événements) est publié,
le marché réagit en 2 vagues distinctes au lieu d'un mouvement linéaire :

1. Phase 1 (T+0 to T+5) : Réaction immédiate des algorithmes haute fréquence
2. Pullback (T+5 to T+11) : Prise de profits technique (~84% retrace)
3. Phase 2 (T+11 to T+15) : Ordres institutionnels, plus forte que Phase 1
4. Stabilisation (T+40) : Retour à l'équilibre

Performance Validée (11 septembre 2025)
---------------------------------------
- Impact : 93% précision (56.6 vs 53 pips)
- Timing : 100% précision (T+5, T+11, T+15, T+40 exacts)

Auteur: Session 64-65
Date: 24 octobre 2025
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional


def detect_double_wave_conditions(
    events: List[Dict],
    surprise_threshold: float = 20.0,
    min_cluster_size: int = 5
) -> bool:
    """
    Détecte si les conditions de Double Wave Momentum sont remplies.
    
    Le Double Wave se produit uniquement quand TOUS les critères sont satisfaits :
    1. Au moins un événement avec surprise > 20%
    2. Cluster d'au moins 5 événements simultanés (même minute)
    3. Au moins un événement d'importance HIGH (importance_n == 3)
    
    Parameters
    ----------
    events : List[Dict]
        Liste des événements du cluster. Chaque événement doit contenir :
        - 'actual' : Valeur réelle publiée
        - 'estimate' ou 'forecast' ou 'previous' : Valeur de référence
        - 'importance_n' : Niveau d'importance (1=LOW, 2=MEDIUM, 3=HIGH)
        
    surprise_threshold : float, optional
        Seuil de surprise en % (défaut : 20.0)
        
    min_cluster_size : int, optional
        Nombre minimum d'événements simultanés (défaut : 5)
    
    Returns
    -------
    bool
        True si conditions Double Wave remplies, False sinon
    
    Examples
    --------
    >>> events = [
    ...     {'actual': 0.4, 'estimate': 0.3, 'importance_n': 3},  # CPI
    ...     {'actual': 263, 'estimate': 235, 'importance_n': 3},  # Jobless
    ...     # ... 7 autres événements
    ... ]
    >>> detect_double_wave_conditions(events)
    True
    
    >>> simple_event = [{'actual': 0.2, 'estimate': 0.19, 'importance_n': 2}]
    >>> detect_double_wave_conditions(simple_event)
    False  # Surprise < 20% et cluster < 5
    
    Notes
    -----
    - Les événements NULL ou sans valeur de référence sont ignorés
    - La surprise est calculée comme : |actual - reference| / |reference| * 100
    - Si plusieurs références disponibles, priorité : estimate > forecast > previous
    """
    
    # Critère 1 : Taille du cluster
    if len(events) < min_cluster_size:
        return False
    
    # Critère 2 : Au moins un événement HIGH importance
    # FIX SESSION 69: Gérer pandas.NA avec pd.notna()
    import pandas as pd
    has_high_importance = any(
        pd.notna(event.get('importance_n')) and event.get('importance_n') == 3
        for event in events
    )
    if not has_high_importance:
        return False
    
    # Critère 3 : Au moins un événement avec surprise > threshold
    max_surprise = 0.0
    
    for event in events:
        actual = event.get('actual')
        if actual is None:
            continue
            
        # Chercher valeur de référence (priorité : estimate > forecast > previous)
        reference = (
            event.get('estimate') or 
            event.get('forecast') or 
            event.get('previous')
        )
        
        if reference is None or reference == 0:
            continue
        
        # Calculer surprise en %
        surprise_pct = abs(actual - reference) / abs(reference) * 100
        max_surprise = max(max_surprise, surprise_pct)
    
    return max_surprise >= surprise_threshold


DOUBLE_WAVE_PROFILES = {
    # Paramètres dérivés de scripts/session137/doublewave_real_metrics_summary.csv (session 137)
    # Les ratios d'amplitude issus des données ont été plafonnés pour éviter que
    # la Phase 1 ne dépasse systématiquement l'impact final.
    "UP": {
        "phase1_ratio": 0.78,
        "dip_ratio": 0.48,
        "phase1_minutes": 65,
        "phase2_minutes": 93,
        "pullback_fraction": 0.45,
        "stabilization_tail": 25,
        "stabilization_ratio": 0.85,
    },
    "DOWN": {
        "phase1_ratio": 0.78,
        "dip_ratio": 0.43,
        "phase1_minutes": 69,
        "phase2_minutes": 90,
        "pullback_fraction": 0.45,
        "stabilization_tail": 25,
        "stabilization_ratio": 0.85,
    },
}


def predict_double_wave_timeline(
    base_impact: float,
    surprise_pct: float,
    cluster_size: int,
    start_time: datetime,
    direction: str = "UP",
) -> Dict:
    """
    Génère une timeline Double Wave recalibrée (Session 137+).

    Les paramètres (ratios d'amplitudes, timings) proviennent des 160 cas
    DOUBLE_WAVE extraits via `scripts/session137/step3_movements_with_patterns_v2.csv`
    et mesurés par inversion sur les prix (cf. `doublewave_real_metrics_summary.csv`).

    Parameters
    ----------
    base_impact : float
        Impact total prédit (pips absolus)
    surprise_pct : float
        Surprise moyenne du cluster (usage informatif)
    cluster_size : int
        Taille du cluster multi-events
    start_time : datetime
        Heure de début (premier événement)
    direction : str, optional
        'UP' ou 'DOWN' (défaut 'UP')
    """

    profile = DOUBLE_WAVE_PROFILES.get(direction.upper(), DOUBLE_WAVE_PROFILES["UP"])

    phase1_ratio = profile["phase1_ratio"]
    dip_ratio = profile["dip_ratio"]
    phase1_minutes = profile["phase1_minutes"]
    phase2_minutes = profile["phase2_minutes"]
    pullback_minutes = phase1_minutes + (phase2_minutes - phase1_minutes) * profile["pullback_fraction"]
    stabilization_minutes = phase2_minutes + profile["stabilization_tail"]

    phase1_impact = base_impact * phase1_ratio
    pullback_retrace = phase1_impact * dip_ratio
    phase2_impact = base_impact  # le pic absolu reste l'impact prédit
    total_net = base_impact

    phase1_peak_time = start_time + timedelta(minutes=phase1_minutes)
    pullback_low_time = start_time + timedelta(minutes=pullback_minutes)
    phase2_peak_time = start_time + timedelta(minutes=phase2_minutes)
    stabilization_time = start_time + timedelta(minutes=stabilization_minutes)

    return {
        "type": "double_wave",
        "direction": direction.upper(),
        "phase1": {
            "impact_pips": round(phase1_impact, 2),
            "peak_time": phase1_peak_time,
            "duration_min": phase1_minutes,
        },
        "pullback": {
            "retrace_pips": round(pullback_retrace, 2),
            "low_time": pullback_low_time,
            "duration_min": round(pullback_minutes - phase1_minutes, 2),
        },
        "phase2": {
            "impact_pips": round(phase2_impact, 2),
            "peak_time": phase2_peak_time,
            "duration_min": round(phase2_minutes - pullback_minutes, 2),
        },
        "stabilization_time": stabilization_time,
        "total_net_pips": round(total_net, 2),
        "conditions": {
            "surprise_pct": round(surprise_pct, 2),
            "cluster_size": cluster_size,
        },
        "profile": {
            "phase1_ratio": phase1_ratio,
            "dip_ratio": dip_ratio,
            "phase2_ratio": 1.0,
            "stabilization_ratio": profile["stabilization_ratio"],
        },
    }


# Validation interne du module
if __name__ == "__main__":
    print("=== Test Double Wave Module ===\n")
    
    # Test 1 : Cas 11 septembre 2025 (référence)
    print("Test 1 : 11 septembre 2025 (Double Wave attendu)")
    events_11sept = [
        {'actual': 0.4, 'estimate': 0.3, 'importance_n': 3},  # CPI MoM
        {'actual': 2.9, 'estimate': 2.9, 'importance_n': 3},  # CPI YoY
        {'actual': 263, 'estimate': 235, 'importance_n': 3},  # Jobless
        {'actual': 1939, 'estimate': 1950, 'importance_n': 2},
        {'actual': 0.3, 'estimate': 0.3, 'importance_n': 2},
        {'actual': 3.1, 'estimate': 3.1, 'importance_n': 2},
        {'actual': 0.2, 'estimate': 0.2, 'importance_n': 2},
        {'actual': 2.2, 'estimate': 2.2, 'importance_n': 2},
        {'actual': 0.1, 'estimate': 0.1, 'importance_n': 2},
    ]
    
    is_double_wave = detect_double_wave_conditions(events_11sept)
    print(f"  Conditions remplies : {is_double_wave}")
    print(f"  Cluster size : {len(events_11sept)}")
    print(f"  Surprise max : 33.3%")
    
    if is_double_wave:
        start = datetime(2025, 9, 11, 12, 30, 0)  # 14:30 Berne
        timeline = predict_double_wave_timeline(57.0, 33.3, 9, start)
        print(f"\n  Timeline générée :")
        print(f"    Phase 1 : {timeline['phase1']['impact_pips']} pips @ {timeline['phase1']['peak_time'].strftime('%H:%M')}")
        print(f"    Pullback : {timeline['pullback']['retrace_pips']} pips @ {timeline['pullback']['low_time'].strftime('%H:%M')}")
        print(f"    Phase 2 : {timeline['phase2']['impact_pips']} pips @ {timeline['phase2']['peak_time'].strftime('%H:%M')}")
        print(f"    Stabilisation : {timeline['stabilization_time'].strftime('%H:%M')}")
        print(f"    Total net : {timeline['total_net_pips']} pips")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2 : Événement simple (Single Wave attendu)
    print("Test 2 : Événement simple (Single Wave attendu)")
    simple_event = [
        {'actual': 0.21, 'estimate': 0.19, 'importance_n': 2},
    ]
    
    is_double_wave = detect_double_wave_conditions(simple_event)
    print(f"  Conditions remplies : {is_double_wave}")
    print(f"  Raison : Cluster < 5 et surprise ~10%")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3 : Cas limite (frontière)
    print("Test 3 : Cas limite frontière (Single Wave attendu)")
    edge_case = [
        {'actual': 0.23, 'estimate': 0.19, 'importance_n': 3},  # 21% surprise
        {'actual': 100, 'estimate': 95, 'importance_n': 2},
        {'actual': 50, 'estimate': 48, 'importance_n': 2},
        {'actual': 1.5, 'estimate': 1.4, 'importance_n': 2},
    ]
    
    is_double_wave = detect_double_wave_conditions(edge_case)
    print(f"  Conditions remplies : {is_double_wave}")
    print(f"  Raison : Surprise > 20% mais cluster = 4 < 5")
    
    print("\n=== Tests terminés ===")
