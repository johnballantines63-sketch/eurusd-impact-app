#!/usr/bin/env python3
"""
Validation détecteurs Single Wave V2 sur cas réels

OBJECTIF: Valider SingleWaveFortDetectorV2 et IntermediateDetectorV2 sur 5+ cas
- Charger cas identifiés (find_single_wave_cases_v2.py)
- Appliquer détecteurs V2
- Comparer impact détecté vs référence MT5
- Calculer MAE (objectif < 10 pips moyen)

CRITÈRES SUCCÈS:
- MAE moyen < 10 pips
- 3+ cas Single Fort validés
- 2+ cas Single Intermediate validés
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import json

# Imports fonctions utilitaires rev10
session119_dir = Path(__file__).parent.parent / 'session119'
sys.path.insert(0, str(session119_dir))

from double_wave_detector_rev10 import (
    load_ohlc_1m_duckdb,
    to_pips
)

# Imports détecteurs V2
session120_dir = Path(__file__).parent.parent / 'session120'
sys.path.insert(0, str(session120_dir))

from single_wave_detectors_v2 import (
    SingleWaveFortDetectorV2,
    SingleWaveIntermediateDetectorV2
)


def calculate_baseline(df_ohlc: pd.DataFrame, event_time: pd.Timestamp) -> float:
    """
    Calcule baseline = close(t-1) avant event
    
    BASELINE VALIDÉE (Session 118): close de la dernière barre AVANT event
    """
    before_event = df_ohlc[df_ohlc.index < event_time]
    
    if len(before_event) == 0:
        return None
    
    return before_event['close'].iloc[-1]


def get_mt5_impact_reference(
    df_ohlc: pd.DataFrame,
    event_time: pd.Timestamp,
    baseline: float,
    hours_after: int = 2
) -> dict:
    """
    Calcule impact MT5 référence (peak maximum après event)
    
    Args:
        df_ohlc: DataFrame OHLC
        event_time: Timestamp event
        baseline: Prix baseline
        hours_after: Heures après event à scanner
    
    Returns:
        {
            'impact_pips': float,
            'peak_time': Timestamp,
            'peak_price': float
        }
    """
    end_time = event_time + timedelta(hours=hours_after)
    df_after = df_ohlc[(df_ohlc.index > event_time) & (df_ohlc.index <= end_time)]
    
    if len(df_after) == 0:
        return None
    
    # Trouver peak maximum (absolu)
    max_high = df_after['high'].max()
    min_low = df_after['low'].min()
    
    # Direction (plus grande amplitude)
    up_move = max_high - baseline
    down_move = baseline - min_low
    
    if up_move >= down_move:
        # Mouvement haussier
        peak_price = max_high
        peak_idx = df_after['high'].idxmax()
    else:
        # Mouvement baissier
        peak_price = min_low
        peak_idx = df_after['low'].idxmin()
    
    impact_pips = to_pips(abs(peak_price - baseline))
    
    return {
        'impact_pips': impact_pips,
        'peak_time': peak_idx,
        'peak_price': peak_price,
        'direction': 'bullish' if up_move >= down_move else 'bearish'
    }


def validate_single_case(
    case: dict,
    db_path: str,
    detector_fort: SingleWaveFortDetectorV2,
    detector_intermediate: SingleWaveIntermediateDetectorV2
) -> dict:
    """
    Valide un cas Single Wave avec détecteurs V2
    
    Args:
        case: Dict cas candidat (depuis find_single_wave_cases_v2.py)
        db_path: Chemin warehouse.duckdb
        detector_fort: Instance SingleWaveFortDetectorV2
        detector_intermediate: Instance SingleWaveIntermediateDetectorV2
    
    Returns:
        {
            'case': Dict (cas original),
            'validation': Dict {
                'impact_detected': float,
                'impact_mt5': float,
                'mae': float,
                'success': bool,
                'detector_used': 'fort' / 'intermediate',
                'detection_details': Dict (sortie détecteur)
            }
        }
    """
    # Parse date/time
    tz_bern = pytz.timezone('Europe/Zurich')
    date_str = case['date']
    time_str = case['time']
    # Les dates dans le JSON sont en timezone Bern
    event_dt = pd.to_datetime(f"{date_str} {time_str}").tz_localize(tz_bern)
    
    # Fenêtre: event - 30min → event + 2h
    start_window = event_dt - timedelta(minutes=30)
    end_window = event_dt + timedelta(hours=2)
    
    # Charger OHLC 1-min
    try:
        df_ohlc = load_ohlc_1m_duckdb(
            db_path,
            'prices_bern',
            tz_bern,
            start_window,
            end_window
        )
    except Exception as e:
        return {
            'case': case,
            'validation': {
                'success': False,
                'error': f"Erreur chargement OHLC: {e}"
            }
        }
    
    if df_ohlc is None or len(df_ohlc) < 10:
        return {
            'case': case,
            'validation': {
                'success': False,
                'error': "Données OHLC insuffisantes"
            }
        }
    
    # Calculer baseline
    baseline = calculate_baseline(df_ohlc, event_dt)
    if baseline is None:
        return {
            'case': case,
            'validation': {
                'success': False,
                'error': "Baseline introuvable"
            }
        }
    
    # Référence MT5
    mt5_ref = get_mt5_impact_reference(df_ohlc, event_dt, baseline, hours_after=2)
    if mt5_ref is None:
        return {
            'case': case,
            'validation': {
                'success': False,
                'error': "Référence MT5 introuvable"
            }
        }
    
    # Appliquer détecteur V2 approprié
    pattern_type = case['pattern_type']
    
    if pattern_type == 'fort':
        detector = detector_fort
        detector_name = 'SingleWaveFortDetectorV2'
    else:
        detector = detector_intermediate
        detector_name = 'SingleWaveIntermediateDetectorV2'
    
    # Détecter pattern
    try:
        detection = detector.detect_pattern(df_ohlc, event_dt, baseline)
    except Exception as e:
        return {
            'case': case,
            'validation': {
                'success': False,
                'error': f"Erreur détection V2: {e}"
            }
        }
    
    if detection is None:
        # Détection échouée
        mae = abs(mt5_ref['impact_pips'] - 0)  # Considérer 0 pips détecté
        return {
            'case': case,
            'validation': {
                'success': False,
                'impact_detected': 0.0,
                'impact_mt5': round(mt5_ref['impact_pips'], 1),
                'mae': round(mae, 1),
                'detector_used': detector_name,
                'error': "Pattern non détecté par V2"
            }
        }
    
    # Détection réussie
    impact_detected = detection['impact_pips']
    impact_mt5 = mt5_ref['impact_pips']
    mae = abs(impact_detected - impact_mt5)
    
    return {
        'case': case,
        'validation': {
            'success': True,
            'impact_detected': round(impact_detected, 1),
            'impact_mt5': round(impact_mt5, 1),
            'mae': round(mae, 1),
            'detector_used': detector_name,
            'peak_time_detected': str(detection['peak_time']),
            'peak_time_mt5': str(mt5_ref['peak_time']),
            'pullback_ratio': round(detection.get('pullback_ratio_pct', 0), 1),
            'quality_score': round(detection.get('quality_score', 0), 3),
            'detection_details': detection
        }
    }


def validate_all_cases(
    candidates_file: str,
    db_path: str,
    output_file: str = None
) -> dict:
    """
    Valide tous les cas Single Wave
    
    Args:
        candidates_file: Fichier JSON cas candidats
        db_path: Chemin warehouse.duckdb
        output_file: Fichier JSON sortie validation (optionnel)
    
    Returns:
        {
            'summary': {...},
            'validations': [...]
        }
    """
    print(f"\n{'='*80}")
    print(f"VALIDATION SINGLE WAVE V2 - Session 121")
    print(f"{'='*80}\n")
    
    # Charger candidats
    with open(candidates_file, 'r') as f:
        data = json.load(f)
    
    candidates = data['candidates']
    print(f"Candidats chargés: {len(candidates)}")
    print(f"  - Single Fort:        {data['summary']['fort_count']}")
    print(f"  - Single Intermediate: {data['summary']['intermediate_count']}\n")
    
    # Créer détecteurs V2
    detector_fort = SingleWaveFortDetectorV2()
    detector_intermediate = SingleWaveIntermediateDetectorV2()
    
    # Valider chaque cas
    validations = []
    fort_validations = []
    intermediate_validations = []
    
    print("Validation cas...\n")
    
    for case in candidates:
        validation = validate_single_case(
            case,
            db_path,
            detector_fort,
            detector_intermediate
        )
        
        validations.append(validation)
        
        val_result = validation['validation']
        pattern_type = case['pattern_type']
        
        if pattern_type == 'fort':
            fort_validations.append(validation)
        else:
            intermediate_validations.append(validation)
        
        # Affichage
        if val_result['success']:
            emoji = "✅"
            status = f"MAE {val_result['mae']:5.1f} pips"
        else:
            emoji = "❌"
            status = val_result.get('error', 'Échec')[:40]
        
        print(f"{emoji} {case['date']} {case['time']} - {case['event_name'][:40]:40s} | "
              f"{pattern_type.upper():12s} | {status}")
    
    # Statistiques globales
    successful = [v for v in validations if v['validation']['success']]
    
    if len(successful) > 0:
        maes = [v['validation']['mae'] for v in successful]
        mae_mean = np.mean(maes)
        mae_std = np.std(maes)
        mae_min = np.min(maes)
        mae_max = np.max(maes)
        
        # Par type
        fort_successful = [v for v in fort_validations if v['validation']['success']]
        intermediate_successful = [v for v in intermediate_validations if v['validation']['success']]
        
        mae_fort = np.mean([v['validation']['mae'] for v in fort_successful]) if len(fort_successful) > 0 else None
        mae_intermediate = np.mean([v['validation']['mae'] for v in intermediate_successful]) if len(intermediate_successful) > 0 else None
    else:
        mae_mean = mae_std = mae_min = mae_max = None
        mae_fort = mae_intermediate = None
    
    summary = {
        'total_cases': len(candidates),
        'successful_detections': len(successful),
        'failed_detections': len(validations) - len(successful),
        'success_rate': round(len(successful) / len(validations) * 100, 1) if len(validations) > 0 else 0,
        'mae_mean': round(mae_mean, 2) if mae_mean is not None else None,
        'mae_std': round(mae_std, 2) if mae_std is not None else None,
        'mae_min': round(mae_min, 2) if mae_min is not None else None,
        'mae_max': round(mae_max, 2) if mae_max is not None else None,
        'fort': {
            'total': len(fort_validations),
            'successful': len(fort_successful) if len(fort_validations) > 0 else 0,
            'mae_mean': round(mae_fort, 2) if mae_fort is not None else None
        },
        'intermediate': {
            'total': len(intermediate_validations),
            'successful': len(intermediate_successful) if len(intermediate_validations) > 0 else 0,
            'mae_mean': round(mae_intermediate, 2) if mae_intermediate is not None else None
        }
    }
    
    print(f"\n{'='*80}")
    print(f"RÉSULTATS VALIDATION")
    print(f"{'='*80}")
    print(f"Cas testés:              {summary['total_cases']}")
    print(f"Détections réussies:     {summary['successful_detections']}")
    print(f"Détections échouées:     {summary['failed_detections']}")
    print(f"Taux succès:             {summary['success_rate']}%")
    
    if mae_mean is not None:
        print(f"\nMAE GLOBAL:")
        print(f"  Moyen:                 {summary['mae_mean']:.2f} pips")
        print(f"  Écart-type:            {summary['mae_std']:.2f} pips")
        print(f"  Minimum:               {summary['mae_min']:.2f} pips")
        print(f"  Maximum:               {summary['mae_max']:.2f} pips")
        
        print(f"\nMAE PAR TYPE:")
        print(f"  Single Fort:           {summary['fort']['mae_mean']:.2f} pips ({summary['fort']['successful']}/{summary['fort']['total']} cas)")
        print(f"  Single Intermediate:   {summary['intermediate']['mae_mean']:.2f} pips ({summary['intermediate']['successful']}/{summary['intermediate']['total']} cas)")
        
        print(f"\nOBJECTIF SESSION 121:")
        if mae_mean < 10:
            print(f"  MAE < 10 pips:         ✅ ATTEINT ({mae_mean:.2f} pips)")
        else:
            print(f"  MAE < 10 pips:         ❌ NON ATTEINT ({mae_mean:.2f} pips)")
        
        if summary['fort']['successful'] >= 3:
            print(f"  3+ Fort validés:       ✅ ATTEINT ({summary['fort']['successful']} cas)")
        else:
            print(f"  3+ Fort validés:       ❌ NON ATTEINT ({summary['fort']['successful']} cas)")
        
        if summary['intermediate']['successful'] >= 2:
            print(f"  2+ Intermediate:       ✅ ATTEINT ({summary['intermediate']['successful']} cas)")
        else:
            print(f"  2+ Intermediate:       ❌ NON ATTEINT ({summary['intermediate']['successful']} cas)")
    
    print(f"{'='*80}\n")
    
    # Sauvegarder résultats
    if output_file:
        output_data = {
            'validation_date': datetime.now(pytz.timezone('Europe/Zurich')).isoformat(),
            'summary': summary,
            'validations': validations
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Résultats sauvegardés: {output_file}\n")
    
    return {
        'summary': summary,
        'validations': validations
    }


if __name__ == '__main__':
    # Configuration
    db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
    candidates_file = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121/single_wave_candidates.json'
    output_file = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session121/single_wave_validation_results.json'
    
    # Valider tous les cas
    results = validate_all_cases(
        candidates_file=candidates_file,
        db_path=db_path,
        output_file=output_file
    )
    
    print("✅ Validation terminée avec succès!")
