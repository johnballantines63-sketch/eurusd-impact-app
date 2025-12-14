"""
Module pour créer une timeline séquentielle avec calcul VECTORIEL correct
Version 8.6.7 : TOUTES clés ajoutées (peak_time, cumulative_price, etc.)

Changements v8.6.7 :
- AJOUT : peak_time, cumulative_price, minutes_since_prev_phase
- AJOUT : predicted_end, note, ttr_real, surprise, actual_value, forecast
- CORRECTION : Toutes les clés attendues par price_curve_generator.py et streamlit_sequential_ui.py

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
print("🔄 [RELOAD] sequence_multi_event_timeline v8.6.7 - TOUTES clés ajoutées")

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


def sequence_multi_event_timeline(
    phases: List[Dict[str, Any]],
    start_price: float = None,
    duration_minutes: int = 120,
    debug: bool = False,
    real_prices_df: Optional[pd.DataFrame] = None
) -> List[Dict[str, Any]]:
    """
    Génère une timeline séquentielle avec application correcte des impacts.
    
    Version 8.6.7 : TOUTES clés ajoutées (peak_time, cumulative_price, etc.)
    
    Args:
        phases: Liste de dictionnaires contenant les informations de chaque phase
        start_price: Prix de départ
        duration_minutes: Durée totale de la simulation
        debug: Si True, affiche les logs de debug
        real_prices_df: DataFrame optionnel des prix réels pour calcul TTR observé
        
    Returns:
        List[Dict]: Liste des phases enrichies avec ttr_source, pullback_pips, etc.
    """
    
    if debug:
        print("\n" + "="*80)
        print("🎯 SEQUENCE_MULTI_EVENT_TIMELINE v8.6.7 - TOUTES clés ajoutées")

    # 🔧 NORMALISATION AUTOMATIQUE DES DONNÉES D'ENTRÉE
    # Accepte deux formats :
    # Format 1 (ancien) : phase['start_time'], phase['impact'], phase['duration']
    # Format 2 (nouveau) : phase['event']['ts_utc'], phase['predicted_pips'], phase['direction']
    
    normalized_phases = []
    for phase_idx, phase in enumerate(phases):
        # Détecter le format
        if 'start_time' in phase:
            # Format 1 : déjà normalisé
            normalized_phases.append(phase)
        elif 'event' in phase and 'ts_utc' in phase['event']:
            # Format 2 : normaliser
            normalized_phase = {
                'start_time': phase['event']['ts_utc'],
                'impact': phase['predicted_pips'] * phase['direction'],
                'duration': phase.get('duration', 5),
                'event_name': phase['event'].get('family', f"Event {phase_idx + 1}"),
                'latency_median': phase.get('latency_median', 5),
                'ttr_median': phase.get('ttr_median', 10),
                # Garder données originales pour référence
                '_original': phase
            }
            normalized_phases.append(normalized_phase)
        else:
            raise ValueError(f"Format de phase non reconnu à l'index {phase_idx}: {list(phase.keys())}")
    
    # Remplacer phases par la version normalisée
    phases = normalized_phases
    
    # Si start_price non fourni, déduire du premier événement
    if start_price is None:
        start_price = 1.17000  # Valeur par défaut EUR/USD
    
        print("="*80)
    
    # Initialisation
    timeline = []
    current_price = start_price
    
    # Variables pour suivre le pic de la phase précédente
    prev_phase_peak_price = start_price
    prev_phase_peak_time = None
    prev_phase_impact = 0.0
    
    for phase_idx, phase in enumerate(phases):
        phase_start_time = pd.to_datetime(phase['start_time'])
        phase_start_minute = int((phase_start_time - pd.to_datetime(phases[0]['start_time'])).total_seconds() / 60)
        phase_duration = phase.get('duration', 5)
        impact = phase['impact']  # Impact déjà calculé avec multiplicateur
        
        if debug:
            print(f"\n📍 Phase {phase_idx + 1}: {phase['event_name']}")
            print(f"   Minute: {phase_start_minute}, Impact: {impact:.1f} pips, Durée: {phase_duration} min")
        
        # 🔄 v8.6 : Gestion du pullback entre phases rapprochées
        pullback_pips = 0.0
        if phase_idx > 0 and prev_phase_peak_time is not None:
            minutes_to_next_phase = (phase_start_time - prev_phase_peak_time).total_seconds() / 60
            
            if minutes_to_next_phase < 30:
                # Calculer le pullback depuis le pic de la phase précédente
                minutes_since_peak = minutes_to_next_phase
                pullback_pips = calculate_pullback(
                    phase1_impact=prev_phase_impact,
                    minutes_since_peak=minutes_since_peak,
                    minutes_to_next_phase=minutes_to_next_phase
                )
                
                # Appliquer le pullback au prix de départ de cette phase
                if prev_phase_impact > 0:  # Si Phase 1 était haussière
                    current_price = prev_phase_peak_price - (pullback_pips * 0.0001)  # Baisse
                else:  # Si Phase 1 était baissière
                    current_price = prev_phase_peak_price + (pullback_pips * 0.0001)  # Hausse
                
                if debug:
                    print(f"   🔄 Pullback appliqué: {pullback_pips:.1f} pips")
                    print(f"   Prix ajusté: {prev_phase_peak_price:.5f} → {current_price:.5f}")
        
        # Remplir les minutes avant le début de cette phase
        prev_minute = timeline[-1]['minute'] if timeline else 0
        for min_idx in range(prev_minute + 1, phase_start_minute):
            timeline.append({
                'minute': min_idx,
                'price': current_price,
                'phase': None
            })
        
        # Phase active: appliquer l'impact progressivement
        phase_start_price = current_price
        impact_in_price = impact * 0.0001  # Conversion pips → prix
        
        for min_offset in range(phase_duration):
            minute = phase_start_minute + min_offset
            
            # Progression linéaire de l'impact
            progress = (min_offset + 1) / phase_duration
            current_price = phase_start_price + (impact_in_price * progress)
            
            timeline.append({
                'minute': minute,
                'price': current_price,
                'phase': phase_idx + 1
            })
        
        # ✅ v8.6.1 : Sauvegarder le pic de cette phase APRÈS la boucle
        prev_phase_peak_price = current_price
        prev_phase_peak_time = phase_start_time + timedelta(minutes=phase_duration)
        prev_phase_impact = impact  # Impact FINAL avec multiplicateur
        
        if debug:
            print(f"   📊 Prix final: {phase_start_price:.5f} → {current_price:.5f}")
            print(f"   💾 Peak sauvegardé: prix={prev_phase_peak_price:.5f}, "
                  f"time={prev_phase_peak_time}, impact={prev_phase_impact:.1f} pips")
    
    # Enrichir chaque phase avec les métadonnées calculées
    enriched_phases = []
    for idx, phase in enumerate(phases):
        enriched_phase = phase.copy()
        
        # Ajouter phase_num
        enriched_phase['phase_num'] = idx + 1
        
        # Ajouter events si pas présent (à partir de _original)
        if 'events' not in enriched_phase:
            if '_original' in enriched_phase and 'event' in enriched_phase['_original']:
                enriched_phase['events'] = [enriched_phase['_original']['event']]
            else:
                # Créer un événement par défaut depuis les données disponibles
                enriched_phase['events'] = [{
                    'family': enriched_phase.get('event_name', 'Unknown'),
                    'country': 'US',  # Par défaut
                    'start_time': enriched_phase.get('start_time')
                }]
        
        # Ajouter source du TTR
        if real_prices_df is not None:
            enriched_phase['ttr_source'] = 'observed'
        else:
            enriched_phase['ttr_source'] = 'predicted'
        
        # Ajouter duration_minutes si pas présent
        if 'duration_minutes' not in enriched_phase:
            enriched_phase['duration_minutes'] = enriched_phase.get('duration', 5)
        
        # Ajouter direction si pas présent
        if 'direction' not in enriched_phase:
            impact = enriched_phase.get('impact', 0)
            enriched_phase['direction'] = 'UP' if impact > 0 else 'DOWN'
        
        # Ajouter impact_combined si pas présent
        if 'impact_combined' not in enriched_phase:
            enriched_phase['impact_combined'] = enriched_phase.get('impact', 0)
        
        # Ajouter latency_minutes et ttr_minutes si pas présents
        if 'latency_minutes' not in enriched_phase:
            enriched_phase['latency_minutes'] = enriched_phase.get('latency_median', 5)
        if 'ttr_minutes' not in enriched_phase:
            enriched_phase['ttr_minutes'] = enriched_phase.get('ttr_median', 10)
        if 'ttr_predicted' not in enriched_phase:
            enriched_phase['ttr_predicted'] = enriched_phase.get('ttr_median', 10)
        
        # Ajouter pullback si applicable (phase 2+)
        if idx > 0:
            enriched_phase['pullback_pips'] = pullback_pips if 'pullback_pips' in locals() else 0.0
        else:
            enriched_phase['pullback_pips'] = 0.0
        
        # 🆕 v8.6.7 : Ajout des clés manquantes pour compatibilité complète
        
        # peak_time : Timestamp du pic de cette phase
        if 'peak_time' not in enriched_phase:
            phase_end = pd.to_datetime(enriched_phase['start_time']) + timedelta(minutes=enriched_phase['duration_minutes'])
            enriched_phase['peak_time'] = phase_end
        
        # cumulative_price : Prix cumulé au pic de cette phase
        if 'cumulative_price' not in enriched_phase:
            if idx == 0:
                # Première phase : start_price + impact
                enriched_phase['cumulative_price'] = start_price + (enriched_phase['impact_combined'] / 10000)
            else:
                # Phases suivantes : prix cumulé précédent + impact
                prev_cumulative = enriched_phases[idx - 1].get('cumulative_price', start_price)
                
                # Si pullback, partir du prix après pullback
                if enriched_phase.get('pullback_pips', 0) > 0:
                    pullback_change = enriched_phase['pullback_pips'] / 10000
                    phase_start_price = prev_cumulative - pullback_change
                    enriched_phase['cumulative_price'] = phase_start_price + (enriched_phase['impact_combined'] / 10000)
                else:
                    enriched_phase['cumulative_price'] = prev_cumulative + (enriched_phase['impact_combined'] / 10000)
        
        # minutes_since_prev_phase : Minutes depuis la phase précédente
        if 'minutes_since_prev_phase' not in enriched_phase:
            if idx > 0:
                prev_end = pd.to_datetime(enriched_phases[idx - 1]['peak_time'])
                curr_start = pd.to_datetime(enriched_phase['start_time'])
                enriched_phase['minutes_since_prev_phase'] = (curr_start - prev_end).total_seconds() / 60
            else:
                enriched_phase['minutes_since_prev_phase'] = 0
        
        # predicted_end : Timestamp de fin prédite
        if 'predicted_end' not in enriched_phase:
            enriched_phase['predicted_end'] = enriched_phase['peak_time']
        
        # note : Note de statut (optionnel mais utile pour UI)
        if 'note' not in enriched_phase:
            if enriched_phase.get('pullback_pips', 0) > 0:
                enriched_phase['note'] = f"✅ Phase avec pullback de {enriched_phase['pullback_pips']:.1f} pips"
            else:
                enriched_phase['note'] = "✅ Phase complète sans interférence"
        
        # Clés optionnelles (ne pas bloquer si absentes)
        enriched_phase.setdefault('ttr_real', None)
        enriched_phase.setdefault('surprise', None)
        enriched_phase.setdefault('actual_value', None)
        enriched_phase.setdefault('forecast', None)
        
        enriched_phases.append(enriched_phase)
    
    if debug:
        print("\n" + "="*80)
        print(f"✅ {len(enriched_phases)} phases enrichies")
        print(f"   Prix départ: {start_price:.5f}")
        print(f"   Prix final: {current_price:.5f}")
        print(f"   Variation totale: {(current_price - start_price) * 10000:.1f} pips")
        print("="*80 + "\n")
    
    return enriched_phases


def calculate_ttr_accuracy_stats(predictions: List[Dict], actuals: Optional[List[Dict]] = None) -> Dict:
    """
    Calcule les statistiques de précision Time-To-Revert (TTR).
    
    Args:
        predictions: Liste des prédictions avec 'ttr_minutes' ou phases enrichies
        actuals: Liste optionnelle des valeurs réelles avec 'ttr_minutes'
                 Si None, retourne un dict vide avec count = len(predictions)
    
    Returns:
        Dict avec mae, rmse, mape, etc.
    """
    # Si pas d'actuals, retourner juste le count
    if actuals is None:
        return {
            'mae': None,
            'rmse': None,
            'mape': None,
            'count': len(predictions) if predictions else 0,
            'n_phases': len(predictions) if predictions else 0  # Alias pour compatibilité
        }
    
    if not predictions or not actuals:
        return {
            'mae': None,
            'rmse': None,
            'mape': None,
            'count': 0,
            'n_phases': 0
        }
    
    pred_ttrs = np.array([p.get('ttr_minutes', 0) for p in predictions])
    actual_ttrs = np.array([a.get('ttr_minutes', 0) for a in actuals])
    
    # Calcul des erreurs
    errors = pred_ttrs - actual_ttrs
    abs_errors = np.abs(errors)
    squared_errors = errors ** 2
    
    # MAE (Mean Absolute Error)
    mae = np.mean(abs_errors)
    
    # RMSE (Root Mean Squared Error)
    rmse = np.sqrt(np.mean(squared_errors))
    
    # MAPE (Mean Absolute Percentage Error)
    # Éviter division par zéro
    valid_mask = actual_ttrs != 0
    if valid_mask.any():
        mape = np.mean(np.abs(errors[valid_mask] / actual_ttrs[valid_mask])) * 100
    else:
        mape = None
    
    return {
        'mae': float(mae),
        'rmse': float(rmse),
        'mape': float(mape) if mape is not None else None,
        'count': len(predictions),
        'n_phases': len(predictions)
    }
