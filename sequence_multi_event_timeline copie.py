"""
Module pour créer une timeline séquentielle avec calcul VECTORIEL correct
Version 8.4 : Ajout du calcul du TTR réel depuis les prix observés
"""

from datetime import timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def calculate_real_ttr_for_phase(
    phase: Dict, 
    real_prices_df: pd.DataFrame,
    retracement_threshold: float = 0.30,
    max_lookback_minutes: int = 60
) -> float:
    """
    Mesure le TTR RÉEL en observant les prix après l'événement
    
    MÉTHODOLOGIE :
    1. Identifier le prix de référence (à T0)
    2. Trouver le peak (max/min selon direction prédite)
    3. Détecter le retracement significatif (> threshold du mouvement)
    4. TTR = temps entre T0 et retracement
    
    Args:
        phase: Dict de la phase (contient start_time, direction, etc)
        real_prices_df: DataFrame avec colonnes ['time', 'price']
        retracement_threshold: % du mouvement pour détecter retracement (défaut: 30%)
        max_lookback_minutes: Fenêtre max d'observation (défaut: 60 min)
    
    Returns:
        TTR observé en minutes (float)
        Si pas de retracement détecté, retourne le TTR théorique (fallback)
    """
    
    # Validation données
    if real_prices_df is None or len(real_prices_df) == 0:
        return phase['ttr_predicted']  # Fallback sur théorique
    
    # Parser start_time
    start_time = pd.to_datetime(phase['start_time'])
    direction = phase['direction']
    
    # Filtrer les prix dans la fenêtre d'observation
    mask = (real_prices_df['time'] >= start_time)
    phase_prices = real_prices_df[mask].head(max_lookback_minutes)
    
    if len(phase_prices) < 2:
        return phase['ttr_predicted']  # Pas assez de données
    
    # Reset index pour avoir des indices séquentiels
    phase_prices = phase_prices.reset_index(drop=True)
    
    # Prix de référence (à T0)
    ref_price = phase_prices.iloc[0]['price']
    
    # === ÉTAPE 1 : Trouver le peak (prix extrême) ===
    if direction == 'DOWN':
        peak_idx = phase_prices['price'].idxmin()
    else:  # UP
        peak_idx = phase_prices['price'].idxmax()
    
    peak_price = phase_prices.loc[peak_idx, 'price']
    movement_pips = abs((peak_price - ref_price) * 10000)
    
    # Si mouvement trop faible (< 5 pips), considérer comme non significatif
    if movement_pips < 5:
        return phase['ttr_predicted']  # Pas de mouvement clair
    
    # === ÉTAPE 2 : Chercher le retracement après le peak ===
    # On cherche uniquement APRÈS le peak
    if peak_idx >= len(phase_prices) - 1:
        # Peak est le dernier point → pas de retracement observable
        return len(phase_prices)
    
    after_peak = phase_prices.loc[peak_idx + 1:]
    
    for idx in after_peak.index:
        current_price = phase_prices.loc[idx, 'price']
        
        # Calculer le retracement par rapport au peak
        if direction == 'DOWN':
            # Pour mouvement DOWN : retracement = remontée
            retracement_pips = (current_price - peak_price) * 10000
        else:
            # Pour mouvement UP : retracement = descente
            retracement_pips = (peak_price - current_price) * 10000
        
        # Si retracement > threshold du mouvement initial
        if retracement_pips > movement_pips * retracement_threshold:
            # Retracement significatif détecté !
            ttr_minutes = idx  # idx = nombre de minutes depuis T0
            return float(ttr_minutes)
    
    # === ÉTAPE 3 : Pas de retracement détecté ===
    # Retourner le temps jusqu'à la fin de la fenêtre observée
    return float(len(phase_prices))


def sequence_multi_event_timeline(
    predictions: List[Dict], 
    time_gap_minutes: int = 5,
    real_prices_df: Optional[pd.DataFrame] = None
) -> List[Dict]:
    """
    Crée une timeline séquentielle en GROUPANT les événements simultanés
    
    LOGIQUE VECTORIELLE :
    - Événements < time_gap_minutes d'écart → GROUPÉS → Impact vectoriel combiné
    - Événements > time_gap_minutes d'écart → SÉPARÉS → Phases distinctes
    
    NOUVEAU v8.4 :
    - Si real_prices_df fourni → Calcule TTR RÉEL au lieu du théorique
    - TTR observé basé sur détection de retracement dans les prix
    
    Args:
        predictions: Liste des prédictions individuelles
        time_gap_minutes: Écart max pour considérer événements comme simultanés (défaut: 5 min)
        real_prices_df: DataFrame optionnel avec colonnes ['time', 'price']
                       Si fourni, calcule TTR réel pour chaque phase
    
    Returns:
        Liste de phases, chaque phase = groupe d'événements avec impact combiné
    """
    
    if not predictions:
        return []
    
    # Trier par timestamp
    sorted_preds = sorted(predictions, key=lambda p: pd.to_datetime(p['event']['ts_utc']))
    
    # Grouper les événements par fenêtre temporelle
    phase_groups = []
    current_group = {
        'events': [sorted_preds[0]],
        'start_time': pd.to_datetime(sorted_preds[0]['event']['ts_utc'])
    }
    
    for pred in sorted_preds[1:]:
        event_time = pd.to_datetime(pred['event']['ts_utc'])
        gap = (event_time - current_group['start_time']).total_seconds() / 60
        
        if gap <= time_gap_minutes:
            # Événement dans la même fenêtre → GROUPER
            current_group['events'].append(pred)
        else:
            # Événement espacé → Nouvelle phase
            phase_groups.append(current_group)
            current_group = {
                'events': [pred],
                'start_time': event_time
            }
    
    # Ajouter le dernier groupe
    phase_groups.append(current_group)
    
    # Créer les phases avec calcul vectoriel
    phases = []
    
    for phase_idx, group in enumerate(phase_groups):
        events = group['events']
        start_time = group['start_time']
        
        # === CALCUL VECTORIEL ===
        # Combiner tous les impacts signés (direction incluse)
        total_impact_pips = sum(
            pred['predicted_pips'] * pred['direction'] 
            for pred in events
        )
        
        # Direction du mouvement combiné
        combined_direction = "UP" if total_impact_pips > 0 else "DOWN"
        
        # Latence : minimum des latences (réaction au plus rapide)
        min_latency = min(pred['latency_median'] for pred in events)
        
        # TTR : THÉORIQUE (sera remplacé si prix réels disponibles)
        max_ttr_theoretical = max(pred['ttr_median'] for pred in events)
        
        # === CONSTRUIRE LA PHASE (temporaire avec TTR théorique) ===
        phase = {
            'phase_num': phase_idx + 1,
            'start_time': str(start_time),
            'predicted_end': str(start_time + timedelta(minutes=max_ttr_theoretical)),
            'duration_minutes': max_ttr_theoretical,
            
            # Impact vectoriel combiné
            'impact_pips': total_impact_pips,
            'direction': combined_direction,
            
            # Timing
            'latency_minutes': min_latency,
            'ttr_predicted': max_ttr_theoretical,
            'ttr_theoretical': max_ttr_theoretical,  # Sauvegarder le théorique
            
            # Événements constitutifs
            'events': [
                {
                    'family': pred['event']['family'],
                    'country': pred['event']['country'],
                    'event_key': pred['event'].get('event_key', ''),
                    'time': str(pd.to_datetime(pred['event']['ts_utc'])),
                    'impact_individual': pred['predicted_pips'] * pred['direction'],
                    'surprise': pred.get('surprise', 0)
                }
                for pred in events
            ],
            
            # Métadonnées
            'num_events': len(events),
            'is_simultaneous': len(events) > 1,
            'note': (
                f"✅ {len(events)} événements simultanés - Impact vectoriel combiné"
                if len(events) > 1 
                else "✅ Événement isolé"
            )
        }
        
        # === NOUVEAU v8.4 : Calculer TTR RÉEL si prix disponibles ===
        if real_prices_df is not None and len(real_prices_df) > 0:
            try:
                ttr_real = calculate_real_ttr_for_phase(phase, real_prices_df)
                
                # Mettre à jour la phase avec TTR réel
                phase['ttr_predicted'] = ttr_real
                phase['ttr_real'] = ttr_real
                phase['ttr_source'] = 'observed'
                phase['duration_minutes'] = ttr_real
                phase['predicted_end'] = str(start_time + timedelta(minutes=ttr_real))
                
                # Calculer l'erreur
                ttr_error = abs(ttr_real - max_ttr_theoretical)
                phase['ttr_error_minutes'] = ttr_error
                
                # Mettre à jour la note
                if len(events) > 1:
                    phase['note'] = (
                        f"✅ {len(events)} événements simultanés - Impact vectoriel combiné\n"
                        f"📊 TTR observé: {ttr_real:.0f} min (théorique: {max_ttr_theoretical:.0f} min, "
                        f"erreur: {ttr_error:.0f} min)"
                    )
                else:
                    phase['note'] = (
                        f"✅ Événement isolé\n"
                        f"📊 TTR observé: {ttr_real:.0f} min (théorique: {max_ttr_theoretical:.0f} min, "
                        f"erreur: {ttr_error:.0f} min)"
                    )
                
            except Exception as e:
                # En cas d'erreur, garder le TTR théorique
                phase['ttr_source'] = 'theoretical'
                phase['ttr_error'] = str(e)
                print(f"⚠️ Erreur calcul TTR réel pour phase {phase_idx + 1}: {e}")
        else:
            # Pas de prix réels → garder TTR théorique
            phase['ttr_source'] = 'theoretical'
        
        phases.append(phase)
    
    return phases


def format_phase_summary(phase: Dict) -> str:
    """
    Formate un résumé textuel d'une phase
    """
    events_str = ', '.join([e['family'] for e in phase['events']])
    
    # Déterminer quel TTR afficher
    ttr_source = phase.get('ttr_source', 'theoretical')
    if ttr_source == 'observed':
        ttr_label = f"TTR observé : {phase['ttr_predicted']:.0f} min ✅"
        if 'ttr_theoretical' in phase:
            ttr_label += f" (théorique: {phase['ttr_theoretical']:.0f} min)"
    else:
        ttr_label = f"TTR prédit : {phase['ttr_predicted']:.0f} min"
    
    summary = f"""
Phase {phase['phase_num']} : {phase['start_time']} ({events_str})
  Impact combiné : {phase['impact_pips']:+.1f} pips {phase['direction']}
  Latence prédite : {phase['latency_minutes']:.0f} min
  {ttr_label}
  Durée totale : {phase['duration_minutes']:.0f} min
  {phase['note']}
"""
    
    if phase['num_events'] > 1:
        summary += "\n  Détails individuels :\n"
        for evt in phase['events']:
            summary += f"    - {evt['family']} : {evt['impact_individual']:+.1f} pips (surprise: {evt['surprise']:+.2f})\n"
    
    return summary


def calculate_ttr_accuracy_stats(phases: List[Dict]) -> Dict:
    """
    Calcule les statistiques d'erreur TTR si des phases ont du TTR observé
    
    Returns:
        Dict avec MAE, RMSE, et liste des erreurs individuelles
    """
    errors = []
    
    for phase in phases:
        if phase.get('ttr_source') == 'observed' and 'ttr_theoretical' in phase:
            error = abs(phase['ttr_real'] - phase['ttr_theoretical'])
            errors.append({
                'phase_num': phase['phase_num'],
                'ttr_theoretical': phase['ttr_theoretical'],
                'ttr_real': phase['ttr_real'],
                'error_minutes': error,
                'error_percentage': (error / phase['ttr_theoretical'] * 100) if phase['ttr_theoretical'] > 0 else 0
            })
    
    if not errors:
        return {
            'n_phases': 0,
            'mae': None,
            'rmse': None,
            'errors': []
        }
    
    error_values = [e['error_minutes'] for e in errors]
    
    return {
        'n_phases': len(errors),
        'mae': np.mean(error_values),
        'rmse': np.sqrt(np.mean([e**2 for e in error_values])),
        'max_error': max(error_values),
        'min_error': min(error_values),
        'errors': errors
    }
