"""
Module pour créer une timeline séquentielle avec calcul VECTORIEL correct
Version 8.5 ADAPTIVE : Facteur d'atténuation adaptatif basé sur analyse empirique

Changements v8.5 :
- Ajout fonction calculate_attenuation_factor() basée sur H1 (surprise extrême) et H3 (cohérence)
- Application du facteur quand phases consécutives vont dans la même direction
- Facteur de base : 0.70 (médiane empirique sur 22 cas)
- Ajustements : 0.66 (incohérent) à 1.02 (cohérent)
"""

# 🔥 DEBUG: Forcer rechargement module
print("🔄 [RELOAD] sequence_multi_event_timeline v8.5 - Facteur adaptatif ACTIF")

from datetime import timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def calculate_attenuation_factor(
    events: List[Dict],
    direction: str,
    prev_direction: Optional[str] = None
) -> float:
    """
    Calcule le facteur d'atténuation adaptatif pour événements multiples
    Basé sur analyse empirique de 22 transitions (Sept-Oct 2025)
    
    Hypothèses validées :
    - H1 (corr=0.359) : Surprise extrême (>10) → amplification
    - H3 (corr=0.412) : Cohérence surprise/direction → moins d'atténuation
    
    Args:
        events: Liste des événements de la phase
        direction: Direction de la phase ('UP' ou 'DOWN')
        prev_direction: Direction de la phase précédente (None si première phase)
    
    Returns:
        float: Facteur entre 0.66 et 1.02
            - 0.66 : Forte atténuation (incohérent)
            - 0.70 : Atténuation de base (médiane)
            - 0.80 : Atténuation modérée (surprise extrême)
            - 1.02 : Quasi-aucune atténuation (cohérent)
    """
    
    # Si première phase OU directions opposées : pas d'atténuation
    if prev_direction is None or prev_direction != direction:
        return 1.0
    
    # Facteur de base (médiane empirique)
    base_factor = 0.70
    
    # Extraire les surprises
    surprises = [evt.get('surprise', 0) for evt in events if 'surprise' in evt]
    
    if not surprises:
        return base_factor
    
    # H1 : Détecter surprise extrême
    max_surprise = max([abs(s) for s in surprises])
    
    # H3 : Calculer cohérence surprise/direction
    mean_surprise = np.mean(surprises)
    
    # Cohérent si : UP et surprises positives, OU DOWN et surprises négatives
    is_coherent = (
        (direction == 'UP' and mean_surprise > 0) or
        (direction == 'DOWN' and mean_surprise < 0)
    )
    
    # Application des règles
    if is_coherent:
        # H3 dominant : cohérence → quasi-aucune atténuation
        factor = 1.02
    elif max_surprise > 10:
        # H1 : surprise extrême → amplification modérée
        factor = 0.80
    else:
        # Cas standard : atténuation de base
        factor = base_factor
    
    # Si incohérent ET pas de surprise extrême : atténuation plus forte
    if not is_coherent and max_surprise <= 10:
        factor = 0.66
    
    return factor


def _generate_phase_note(
    num_events: int,
    attenuation_factor: float,
    prev_direction: Optional[str],
    combined_direction: str,
    impact_raw: float,
    impact_combined: float
) -> str:
    """Génère la note explicative de la phase"""
    
    base_note = (
        f"✅ {num_events} événements simultanés - Impact vectoriel combiné"
        if num_events > 1
        else "✅ Événement isolé"
    )
    
    # Ajouter info sur atténuation si appliquée
    # Note : Si facteur != 1.0, c'est que les directions étaient forcément les mêmes
    if attenuation_factor != 1.0:
        if attenuation_factor >= 1.0:
            reason = "cohérence surprise/direction"
        elif attenuation_factor >= 0.75:
            reason = "surprise extrême" if attenuation_factor == 0.80 else "standard"
        else:
            reason = "incohérence surprise/direction"
        
        base_note += (
            f"\n⚠️ Facteur d'atténuation : {attenuation_factor:.2f} ({reason})"
            f"\n   Impact brut : {impact_raw:+.1f} pips → Impact ajusté : {impact_combined:+.1f} pips"
        )
    
    return base_note


def calculate_real_ttr_for_phase(
    phase: Dict, 
    real_prices_df: pd.DataFrame,
    max_lookback_minutes: int = 60,
    use_adaptive_threshold: bool = True,
    cumulative_price: float = None  # ✅ NOUVEAU : Prix cumulé des phases précédentes
) -> float:
    """
    Mesure le TTR RÉEL en observant les prix après l'événement
    VERSION AMÉLIORÉE avec calcul incrémental pour phases multiples
    
    Args:
        phase: Dictionnaire de la phase
        real_prices_df: DataFrame des prix réels
        max_lookback_minutes: Durée maximale d'observation
        use_adaptive_threshold: Utiliser seuil adaptatif
        cumulative_price: Prix de FIN de la phase précédente (pour calcul incrémental)
    """
    
    if real_prices_df is None or len(real_prices_df) == 0:
        return phase['ttr_predicted']
    
    try:
        start_time = pd.Timestamp(phase['start_time'])
        
        if hasattr(start_time, 'tz') and start_time.tz is not None:
            start_time = start_time.tz_localize(None)
        
        real_prices_clean = real_prices_df.copy()
        if len(real_prices_clean) > 0:
            sample_time = real_prices_clean['time'].iloc[0]
            if hasattr(sample_time, 'tz') and sample_time.tz is not None:
                real_prices_clean['time'] = real_prices_clean['time'].dt.tz_localize(None)
        
        direction = phase['direction']
        
        mask = (real_prices_clean['time'] >= start_time)
        phase_prices = real_prices_clean[mask].head(max_lookback_minutes)
        
        if len(phase_prices) < 2:
            return phase['ttr_predicted']
        
        phase_prices = phase_prices.reset_index(drop=True)
        
        # ✅ MODIFICATION CRITIQUE : Prix de référence
        if cumulative_price is not None:
            # Utiliser le prix cumulé (fin phase précédente)
            ref_price = cumulative_price
            phase['_used_cumulative_price'] = True
        else:
            # Première phase : utiliser le prix initial
            ref_price = phase_prices.iloc[0]['price']
            phase['_used_cumulative_price'] = False
        
        if direction == 'DOWN':
            peak_idx = phase_prices['price'].idxmin()
        else:
            peak_idx = phase_prices['price'].idxmax()
        
        peak_price = phase_prices.loc[peak_idx, 'price']
        movement_pips = abs((peak_price - ref_price) * 10000)
        
        if movement_pips < 3:
            return phase['ttr_predicted']
        
        # ✨ SEUIL ADAPTATIF selon l'amplitude du mouvement
        if use_adaptive_threshold:
            if movement_pips < 5:
                retracement_threshold = 0.10
            elif movement_pips < 10:
                retracement_threshold = 0.12
            elif movement_pips < 20:
                retracement_threshold = 0.15
            elif movement_pips < 30:
                retracement_threshold = 0.18
            else:
                retracement_threshold = 0.20
        else:
            retracement_threshold = 0.20
        
        phase['ttr_metadata'] = {
            'movement_pips': movement_pips,
            'threshold_used': retracement_threshold,
            'peak_minutes': int(peak_idx),
            'ref_price_used': ref_price,
            'peak_price': peak_price,
            'cumulative_mode': cumulative_price is not None
        }
        
        if peak_idx >= len(phase_prices) - 1:
            phase['ttr_metadata']['reason'] = 'peak_at_end'
            return float(len(phase_prices))
        
        after_peak = phase_prices.loc[peak_idx + 1:]
        
        for idx in after_peak.index:
            current_price = phase_prices.loc[idx, 'price']
            
            if direction == 'DOWN':
                retracement_pips = (current_price - peak_price) * 10000
            else:
                retracement_pips = (peak_price - current_price) * 10000
            
            if retracement_pips > movement_pips * retracement_threshold:
                phase['ttr_metadata']['reason'] = 'retracement_detected'
                phase['ttr_metadata']['retracement_pct'] = (retracement_pips / movement_pips * 100)
                return float(idx)
        
        phase['ttr_metadata']['reason'] = 'no_retracement'
        return float(len(phase_prices))
        
    except Exception as e:
        print(f"❌ Erreur calculate_real_ttr_for_phase: {e}")
        return phase.get('ttr_predicted', 30)


def sequence_multi_event_timeline(
    predictions: List[Dict], 
    time_gap_minutes: int = 5,
    real_prices_df: Optional[pd.DataFrame] = None
) -> List[Dict]:
    """
    Crée une timeline séquentielle en GROUPANT les événements simultanés
    """
    
    if not predictions:
        return []
    
    sorted_preds = sorted(predictions, key=lambda p: pd.to_datetime(p['event']['ts_utc']))
    
    phase_groups = []
    current_group = {
        'events': [sorted_preds[0]],
        'start_time': pd.to_datetime(sorted_preds[0]['event']['ts_utc'])
    }
    
    for pred in sorted_preds[1:]:
        event_time = pd.to_datetime(pred['event']['ts_utc'])
        gap = (event_time - current_group['start_time']).total_seconds() / 60
        
        if gap <= time_gap_minutes:
            current_group['events'].append(pred)
        else:
            phase_groups.append(current_group)
            current_group = {
                'events': [pred],
                'start_time': event_time
            }
    
    phase_groups.append(current_group)
    
    phases = []
    
    # ✅ MODIFICATION v8.5 : Facteur d'atténuation adaptatif
    # Stocker la direction de la phase précédente pour détecter même direction
    prev_direction = None
    
    # ✅ MODIFICATION CRITIQUE : Calcul incrémental pour phases multiples
    # Chaque phase calcule son impact depuis le prix de FIN de la phase précédente
    cumulative_price = None  # Sera mis à jour après chaque phase
    
    for phase_idx, group in enumerate(phase_groups):
        events = group['events']
        start_time = group['start_time']
        
        # CALCUL VECTORIEL CORRIGÉ
        impact_up = 0.0
        impact_down = 0.0
        
        for pred in events:
            pips = pred.get('predicted_pips', 0)
            direction = pred.get('direction', 1)
            
            if direction > 0:
                impact_up += pips
            else:
                impact_down += pips
        
        if impact_up > impact_down:
            impact_combined_raw = impact_up - impact_down
            combined_direction = "UP"
        else:
            impact_combined_raw = impact_down - impact_up
            combined_direction = "DOWN"
        
        # ✨ NOUVEAU v8.5 : Application du facteur d'atténuation adaptatif
        attenuation_factor = calculate_attenuation_factor(
            events=events,
            direction=combined_direction,
            prev_direction=prev_direction
        )
        
        impact_combined = impact_combined_raw * attenuation_factor
        
        # 🔍 DEBUG: Tracer l'application du facteur
        print(f"  Phase {phase_idx + 1}: facteur={attenuation_factor:.2f}, brut={impact_combined_raw:.1f}, ajusté={impact_combined:.1f}")
        
        # ✅ IMPORTANT : Sauvegarder prev_direction AVANT de le mettre à jour
        # pour l'utiliser dans _generate_phase_note()
        prev_direction_for_note = prev_direction
        
        # Stocker la direction pour la prochaine phase
        prev_direction = combined_direction
        
        min_latency = min(pred.get('latency_median', 5.0) for pred in events)
        max_ttr_theoretical = max(pred.get('ttr_median', 30.0) for pred in events)
        
        phase = {
            'phase_num': phase_idx + 1,
            'start_time': str(start_time),
            'start': start_time,
            'predicted_end': str(start_time + timedelta(minutes=max_ttr_theoretical)),
            'duration_minutes': max_ttr_theoretical,
            'impact_combined': impact_combined,
            'impact_raw': impact_combined_raw,  # ✨ NOUVEAU v8.5 : Impact avant atténuation
            'attenuation_factor': attenuation_factor,  # ✨ NOUVEAU v8.5 : Facteur appliqué
            'direction': combined_direction,
            'latency_minutes': min_latency,
            'ttr_predicted': max_ttr_theoretical,
            'ttr_theoretical': max_ttr_theoretical,
            'events': [
                {
                    'family': pred['event'].get('family', 'Unknown'),
                    'country': pred['event'].get('country', ''),
                    'event_key': pred['event'].get('event_key', ''),
                    'time': str(pd.to_datetime(pred['event']['ts_utc'])),
                    'impact_individual': pred.get('predicted_pips', 0) * pred.get('direction', 1),
                    'surprise': pred.get('surprise', 0)
                }
                for pred in events
            ],
            'num_events': len(events),
            'is_simultaneous': len(events) > 1,
            'note': _generate_phase_note(
                num_events=len(events),
                attenuation_factor=attenuation_factor,
                prev_direction=prev_direction_for_note,  # ✅ Utiliser la direction AVANT MAJ
                combined_direction=combined_direction,
                impact_raw=impact_combined_raw,
                impact_combined=impact_combined
            )
        }
        
        if real_prices_df is not None and len(real_prices_df) > 0:
            try:
                ttr_real = calculate_real_ttr_for_phase(phase, real_prices_df, cumulative_price=cumulative_price)
                
                phase['ttr_predicted'] = ttr_real
                phase['ttr_real'] = ttr_real

                
                # ✅ Mettre à jour le prix cumulé pour la prochaine phase
                if 'ttr_metadata' in phase and 'peak_price' in phase['ttr_metadata']:
                    cumulative_price = phase['ttr_metadata']['peak_price']
                    print(f"  → Prix cumulé mis à jour : {cumulative_price:.5f}")
                phase['ttr_source'] = 'observed'
                phase['duration_minutes'] = ttr_real
                phase['predicted_end'] = str(start_time + timedelta(minutes=ttr_real))
                
                ttr_error = abs(ttr_real - max_ttr_theoretical)
                phase['ttr_error_minutes'] = ttr_error
                
                # ✨ FUSION : Conserver la note du facteur + ajouter TTR observé
                # Ne pas écraser la note générée par _generate_phase_note() !
                ttr_info = (
                    f"\n📊 TTR observé: {ttr_real:.0f} min (théorique: {max_ttr_theoretical:.0f} min, "
                    f"erreur: {ttr_error:.0f} min)"
                )
                
                # Ajouter le TTR à la note existante (qui contient déjà le facteur)
                phase['note'] = phase['note'] + ttr_info
                
            except Exception as e:
                phase['ttr_source'] = 'theoretical'
                phase['ttr_error'] = str(e)
                print(f"⚠️ Erreur calcul TTR réel pour phase {phase_idx + 1}: {e}")
        else:
            phase['ttr_source'] = 'theoretical'
        
        phases.append(phase)
    
    return phases


def format_phase_summary(phase: Dict) -> str:
    """Formate un résumé textuel d'une phase"""
    events_str = ', '.join([e['family'] for e in phase['events']])
    
    ttr_source = phase.get('ttr_source', 'theoretical')
    if ttr_source == 'observed':
        ttr_label = f"TTR observé : {phase['ttr_predicted']:.0f} min ✅"
        if 'ttr_theoretical' in phase:
            ttr_label += f" (théorique: {phase['ttr_theoretical']:.0f} min)"
    else:
        ttr_label = f"TTR prédit : {phase['ttr_predicted']:.0f} min"
    
    impact = phase.get('impact_combined', 0)
    
    summary = f"""
Phase {phase['phase_num']} : {phase['start_time']} ({events_str})
  Impact combiné : {impact:+.1f} pips {phase['direction']}
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
    """Calcule les statistiques d'erreur TTR"""
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
