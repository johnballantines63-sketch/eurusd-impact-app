"""
Module pour créer une timeline séquentielle avec calcul VECTORIEL correct
Version 8.4 FIXED : Correction du calcul d'impact combiné
"""

from datetime import timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def calculate_real_ttr_for_phase(
    phase: Dict, 
    real_prices_df: pd.DataFrame,
    max_lookback_minutes: int = 60,
    use_adaptive_threshold: bool = True
) -> float:
    """
    Mesure le TTR RÉEL en observant les prix après l'événement
    VERSION AMÉLIORÉE avec seuil adaptatif
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
        ref_price = phase_prices.iloc[0]['price']
        
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
                retracement_threshold = 0.15
            elif movement_pips < 20:
                retracement_threshold = 0.20
            elif movement_pips < 30:
                retracement_threshold = 0.25
            else:
                retracement_threshold = 0.30
        else:
            retracement_threshold = 0.30
        
        phase['ttr_metadata'] = {
            'movement_pips': movement_pips,
            'threshold_used': retracement_threshold,
            'peak_minutes': int(peak_idx)
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
            impact_combined = impact_up - impact_down
            combined_direction = "UP"
        else:
            impact_combined = impact_down - impact_up
            combined_direction = "DOWN"
        
        min_latency = min(pred.get('latency_median', 5.0) for pred in events)
        max_ttr_theoretical = max(pred.get('ttr_median', 30.0) for pred in events)
        
        phase = {
            'phase_num': phase_idx + 1,
            'start_time': str(start_time),
            'start': start_time,
            'predicted_end': str(start_time + timedelta(minutes=max_ttr_theoretical)),
            'duration_minutes': max_ttr_theoretical,
            'impact_combined': impact_combined,
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
            'note': (
                f"✅ {len(events)} événements simultanés - Impact vectoriel combiné"
                if len(events) > 1 
                else "✅ Événement isolé"
            )
        }
        
        if real_prices_df is not None and len(real_prices_df) > 0:
            try:
                ttr_real = calculate_real_ttr_for_phase(phase, real_prices_df)
                
                phase['ttr_predicted'] = ttr_real
                phase['ttr_real'] = ttr_real
                phase['ttr_source'] = 'observed'
                phase['duration_minutes'] = ttr_real
                phase['predicted_end'] = str(start_time + timedelta(minutes=ttr_real))
                
                ttr_error = abs(ttr_real - max_ttr_theoretical)
                phase['ttr_error_minutes'] = ttr_error
                
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
