"""
Module pour créer une timeline séquentielle avec calcul VECTORIEL correct
Version 8.6.6 : FIX Pullback correct (4% par minute, plafond 50%)

Changements v8.6.6 :
- FIX CRITIQUE : Pullback 12%/min → 4%/min (selon données MT5 réelles)
- FIX CRITIQUE : Plafond 250% → 50% (Fibonacci)
- SUPPRESSION : PULLBACK_REDUCER 0.73 (inutile avec bon calcul)

Changements v8.6.1 :
- FIX CRITIQUE : prev_phase_peak_time maintenant correctement sauvegardé entre phases
- Déplacement de la sauvegarde du peak_time à la fin de la boucle

Changements v8.6 :
- Ajout fonction calculate_pullback() basée sur analyse empirique du 11 sept 2025
- Pullback appliqué uniquement si intervalle < 30 minutes entre phases
- Formule : ~4% par minute, plafonné à 50% (Fibonacci)
- Intégration dans la boucle des phases pour ajuster le prix de départ

Changements v8.5 (conservés) :
- Facteur d'atténuation adaptatif (0.66-1.02)
- Application selon cohérence surprise/direction
"""

# 🔥 DEBUG: Forcer rechargement module
print("🔄 [RELOAD] sequence_multi_event_timeline v8.6.6 - FIX Pullback Correct")

from datetime import timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def calculate_pullback(
    phase1_impact: float,
    minutes_since_peak: float,
    minutes_to_next_phase: float
) -> float:
    """
    Calcule le pullback entre deux phases rapprochées
    Basé sur observation empirique du 11 septembre 2025
    
    ✅ CORRECTION v8.6.6 : Retour aux valeurs empiriques correctes
    Observation 11 sept 2025 (données MT5 réelles) :
    - Phase 1 : +360 pips réels (14:30 → 14:35, 5 minutes)
    - Pullback : -200 pips (14:35 → 14:45, 10 minutes)
    - Pullback % : 200/360 = 55.6% en 10 min = 5.56% par minute
    
    Pour être conservateur, on utilise 4% par minute avec plafond 50% (Fibonacci)
    
    Args:
        phase1_impact: Impact de la phase précédente en pips
        minutes_since_peak: Minutes écoulées depuis le pic de Phase 1
        minutes_to_next_phase: Minutes entre début Phase 1 et début Phase 2
    
    Returns:
        float: Pullback en pips (valeur positive)
    
    Règle critique :
    - Si intervalle > 30 min : pas de pullback (phases indépendantes)
    - Si intervalle < 30 min : pullback proportionnel au temps
    """
    
    # Pas de pullback pour phases éloignées (> 30 min)
    if minutes_to_next_phase > 30:
        return 0.0
    
    # ✅ CORRECTION v8.6.6 : Valeurs empiriques correctes
    pullback_pct_per_minute = 0.04  # 4% par minute (empirique)
    
    # Calcul du pourcentage de pullback
    pullback_pct = min(
        pullback_pct_per_minute * minutes_since_peak,
        0.50  # Plafond 50% Fibonacci
    )
    
    # Appliquer au mouvement de Phase 1
    pullback_pips = abs(phase1_impact) * pullback_pct
    
    # 📊 Log pour debug
    print(f"🔄 Pullback calculé : {pullback_pips:.1f} pips "
          f"({pullback_pct*100:.1f}% sur {abs(phase1_impact):.1f} pips, {minutes_since_peak:.0f} min)")
    
    return pullback_pips
