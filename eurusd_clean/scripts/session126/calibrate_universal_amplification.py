#!/usr/bin/env python3
"""
SESSION 126 - PIPELINE MASTER CALIBRATION UNIVERSELLE
======================================================
Script master automatisé pour calibrer fonction amplification
sur N'IMPORTE QUEL type d'événement

Usage:
    python calibrate_universal_amplification.py --event_type="fed interest rate decision"
    python calibrate_universal_amplification.py --event_type="cpi" --min_occurrences=5

Architecture: 6 ÉTAPES (modules Session 125 + Session 126)
"""
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
import duckdb
import pandas as pd
import numpy as np
from typing import Dict, List

# Import modules Session 126
from utils_mapping import get_empirical_score, map_country_to_currency
from validate_predictions import validate_predictions_with_baseline
from decide_integration import decide_integration

print("=" * 80)
print("PIPELINE MASTER - CALIBRATION UNIVERSELLE AMPLIFICATION")
print("Session 126 - André Valentin avec Claude")
print("=" * 80)
print()

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"

# Paramètres validés Session 125
WINDOW = 240  # 4h (optimal)
LOOKBACK_DAYS = 30
MIN_AMPLITUDE_PIPS = 30
MAX_DATE = '2025-11-05'  # Période avec prix validés

# ============================================================================
# ÉTAPE 1 : TROUVER ÉVÉNEMENTS TYPE
# ============================================================================

def find_events_by_type(
    event_type: str,
    conn,
    start_date: str = '2023-01-01',
    end_date: str = MAX_DATE,
    importance_n: int = 3
) -> pd.DataFrame:
    """
    ÉTAPE 1 : Trouve tous événements d'un type spécifique
    
    Correction Session 126 : Utiliser table 'events' (pas 'economic_events')
    """
    print(f"[ÉTAPE 1] Recherche événements '{event_type}'...")
    print()
    
    query = """
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        estimate,
        previous
    FROM events
    WHERE country = 'US'
      AND event_key = ?
      AND importance_n = ?
      AND ts_utc >= ?
      AND ts_utc <= ?
    ORDER BY ts_utc
    """
    
    df_events = conn.execute(query, [event_type, importance_n, start_date, end_date]).df()
    
    print(f"✅ {len(df_events)} événements '{event_type}' trouvés")
    print(f"   Période : {start_date} → {end_date}")
    print(f"   Importance : {importance_n} (HIGH)")
    print()
    
    return df_events


# ============================================================================
# ÉTAPE 2 : MESURER IMPACT RÉEL
# ============================================================================

def measure_real_impact(cluster_time, conn, lookforward_minutes: int = 60):
    """
    ÉTAPE 2 : Mesure impact réel EUR/USD après événement
    
    Méthode :
    - Baseline = prix 5 min avant cluster
    - Impact = max movement 60 min après cluster
    """
    time_before = cluster_time - timedelta(minutes=5)
    time_after = cluster_time + timedelta(minutes=lookforward_minutes)
    
    try:
        df_prices = conn.execute("""
            SELECT datetime, close, high, low
            FROM prices_bern
            WHERE datetime >= ? AND datetime <= ?
            ORDER BY datetime
        """, [str(time_before), str(time_after)]).df()
        
        if len(df_prices) < 10:
            return None
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        
        # Baseline = dernier prix avant événement
        before_mask = df_prices['datetime'] < cluster_time
        if before_mask.sum() == 0:
            return None
        
        baseline = df_prices[before_mask].iloc[-1]['close']
        
        # Impact = max mouvement après
        after_mask = df_prices['datetime'] > cluster_time
        if after_mask.sum() == 0:
            return None
        
        after_data = df_prices[after_mask]
        max_high = after_data['high'].max()
        min_low = after_data['low'].min()
        
        impact_up = (max_high - baseline) * 10000
        impact_down = (baseline - min_low) * 10000
        
        return max(impact_up, impact_down)
        
    except Exception as e:
        return None


# ============================================================================
# ÉTAPE 3 : CALCULER R² TENDANCES
# ============================================================================

def detect_swing_highs(prices, window=240, threshold=0.0001):
    """Détection swing highs (Session 125)"""
    swing_highs = []
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        if center > max(left.max(), right.max()) + threshold:
            swing_highs.append(i)
    return swing_highs


def detect_swing_lows(prices, window=240, threshold=0.0001):
    """Détection swing lows (Session 125)"""
    swing_lows = []
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        if center < min(left.min(), right.min()) - threshold:
            swing_lows.append(i)
    return swing_lows


def calculate_r2_for_event(event_time, conn, window=WINDOW, lookback_days=LOOKBACK_DAYS):
    """
    ÉTAPE 3 : Calcule R² tendance pré-événement
    
    Méthode Session 125 :
    - Détecte dernière inversion (swing high/low)
    - Calcule R² régression linéaire (inversion → événement)
    """
    lookback_start = event_time - timedelta(days=lookback_days)
    
    try:
        df_prices = conn.execute("""
            SELECT datetime, close
            FROM prices_bern
            WHERE datetime >= ? AND datetime < ?
            ORDER BY datetime
        """, [str(lookback_start), str(event_time)]).df()
        
        if len(df_prices) < window * 2:
            return None
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        prices = df_prices['close'].values
        timestamps = df_prices['datetime'].tolist()
        
        # Détection inversions
        swing_highs = detect_swing_highs(prices, window)
        swing_lows = detect_swing_lows(prices, window)
        
        extrema = []
        for idx in swing_highs:
            extrema.append({'type': 'HIGH', 'index': idx, 'price': prices[idx], 'timestamp': timestamps[idx]})
        for idx in swing_lows:
            extrema.append({'type': 'LOW', 'index': idx, 'price': prices[idx], 'timestamp': timestamps[idx]})
        
        extrema.sort(key=lambda x: x['index'])
        
        if not extrema:
            return None
        
        # Dernière inversion
        reversals = []
        for extremum in extrema:
            start_idx = extremum['index']
            end_idx = len(prices) - 1
            
            if end_idx - start_idx < 60:
                continue
            
            segment_prices = prices[start_idx:end_idx + 1]
            amplitude = (segment_prices.max() - segment_prices.min()) * 10000
            
            if amplitude < MIN_AMPLITUDE_PIPS:
                continue
            
            price_start = prices[start_idx]
            price_end = prices[end_idx]
            
            if extremum['type'] == 'HIGH' and price_end < price_start:
                reversal_type = 'HIGH_TO_LOW'
            elif extremum['type'] == 'LOW' and price_end > price_start:
                reversal_type = 'LOW_TO_HIGH'
            else:
                continue
            
            # R² régression linéaire
            from scipy.stats import linregress
            t = np.arange(len(segment_prices))
            slope, intercept, r_value, _, _ = linregress(t, segment_prices)
            r_squared = r_value ** 2
            
            duration = (timestamps[end_idx] - timestamps[start_idx]).total_seconds() / 3600.0
            
            reversals.append({
                'type': reversal_type,
                'time': extremum['timestamp'],
                'r2': r_squared,
                'duration_hours': duration,
                'amplitude_pips': amplitude
            })
        
        if reversals:
            return reversals[-1]  # Dernière inversion
        else:
            return None
            
    except Exception as e:
        return None


# ============================================================================
# ÉTAPE 4 : CALIBRER FONCTION AMPLIFICATION
# ============================================================================

def calibrate_amplification_function(events_with_data: List[Dict], df_scores: pd.DataFrame) -> Dict:
    """
    ÉTAPE 4 : Calibre fonction amp = f(R²)
    
    Méthode Session 125 :
    - Pour chaque événement : calcule amplification idéale
    - Teste modèles : linéaire, quadratique, logarithmique
    - Choisit meilleur (R² fit maximal)
    """
    print(f"[ÉTAPE 4] Calibration fonction amplification...")
    print()
    
    calibration_data = []
    
    for event_data in events_with_data:
        if event_data.get('r2_trend') is None or event_data.get('impact_measured') is None:
            continue
        
        event_key = event_data['event_key']
        country = event_data['country']
        r2_trend = event_data['r2_trend']
        impact_measured = event_data['impact_measured']
        
        # Score empirique
        score = get_empirical_score(event_key, country, df_scores)
        if score is None:
            continue
        
        # Amplification idéale = impact / (score × √1)
        amp_ideal = impact_measured / (score * 1.0)  # n_events = 1 pour événements simples
        
        calibration_data.append({
            'r2_trend': r2_trend,
            'amp_ideal': amp_ideal,
            'impact_measured': impact_measured,
            'score': score
        })
    
    if len(calibration_data) < 3:
        print(f"⚠️  Pas assez de données pour calibration (n={len(calibration_data)} < 3)")
        return None
    
    df_calib = pd.DataFrame(calibration_data)
    X = df_calib['r2_trend'].values
    y = df_calib['amp_ideal'].values
    
    print(f"✅ {len(calibration_data)} points de calibration")
    print()
    
    # Test 3 modèles
    from scipy.optimize import curve_fit
    from sklearn.metrics import r2_score, mean_absolute_error
    
    models = {}
    
    # Linéaire
    def linear(r2, a, b):
        return a + b * r2
    
    try:
        popt_lin, _ = curve_fit(linear, X, y, bounds=([-1, -1], [1, 1]))
        y_pred_lin = linear(X, *popt_lin)
        models['linear'] = {
            'params': popt_lin.tolist(),
            'r2_fit': r2_score(y, y_pred_lin),
            'mae': mean_absolute_error(y, y_pred_lin),
            'formula': f"amp = {popt_lin[0]:.6f} + {popt_lin[1]:.6f}×R²"
        }
    except:
        models['linear'] = None
    
    # Quadratique
    def quadratic(r2, a, b, c):
        return a + b * r2 + c * r2**2
    
    try:
        popt_quad, _ = curve_fit(quadratic, X, y, bounds=([-1, -1, -1], [1, 1, 1]))
        y_pred_quad = quadratic(X, *popt_quad)
        models['quadratic'] = {
            'params': popt_quad.tolist(),
            'r2_fit': r2_score(y, y_pred_quad),
            'mae': mean_absolute_error(y, y_pred_quad),
            'formula': f"amp = {popt_quad[0]:.6f} + {popt_quad[1]:.6f}×R² + {popt_quad[2]:.6f}×R²²"
        }
    except:
        models['quadratic'] = None
    
    # Logarithmique
    def logarithmic(r2, a, b):
        return a + b * np.log(r2 + 0.01)
    
    try:
        popt_log, _ = curve_fit(logarithmic, X, y, bounds=([-1, -1], [1, 1]))
        y_pred_log = logarithmic(X, *popt_log)
        models['logarithmic'] = {
            'params': popt_log.tolist(),
            'r2_fit': r2_score(y, y_pred_log),
            'mae': mean_absolute_error(y, y_pred_log),
            'formula': f"amp = {popt_log[0]:.6f} + {popt_log[1]:.6f}×log(R²+0.01)"
        }
    except:
        models['logarithmic'] = None
    
    # Choisir meilleur
    valid_models = {k: v for k, v in models.items() if v is not None}
    if not valid_models:
        print("❌ Aucun modèle n'a pu être calibré")
        return None
    
    best_model_name = max(valid_models, key=lambda k: valid_models[k]['r2_fit'])
    best_model = valid_models[best_model_name]
    
    print(f"✅ Meilleur modèle : {best_model_name.upper()}")
    print(f"   Formule : {best_model['formula']}")
    print(f"   R² fit  : {best_model['r2_fit']:.4f}")
    print(f"   MAE fit : {best_model['mae']:.4f}")
    print()
    
    # Créer fonction Python
    if best_model_name == 'linear':
        a, b = best_model['params']
        def amp_function(r2):
            r2 = max(0.0, min(1.0, r2))
            return max(0.01, min(0.20, a + b * r2))
    elif best_model_name == 'quadratic':
        a, b, c = best_model['params']
        def amp_function(r2):
            r2 = max(0.0, min(1.0, r2))
            return max(0.01, min(0.20, a + b * r2 + c * r2**2))
    else:  # logarithmic
        a, b = best_model['params']
        def amp_function(r2):
            r2 = max(0.0, min(1.0, r2))
            return max(0.01, min(0.20, a + b * np.log(r2 + 0.01)))
    
    return {
        'function': amp_function,
        'best_model': best_model_name,
        'parameters': best_model['params'],
        'formula': best_model['formula'],
        'metrics': {
            'r2_fit': best_model['r2_fit'],
            'mae_fit': best_model['mae'],
            'n_samples': len(calibration_data)
        },
        'all_models': models
    }


# ============================================================================
# PIPELINE COMPLET
# ============================================================================

def run_calibration_pipeline(event_type: str, min_occurrences: int = 3, output_dir: Path = None):
    """Pipeline complet 6 ÉTAPES"""
    
    if output_dir is None:
        output_dir = Path(__file__).parent / "calibration_results"
    output_dir.mkdir(exist_ok=True)
    
    # Connexion DB
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    df_scores = pd.read_csv(SCORES_PATH)
    
    # ÉTAPE 1 : Trouver événements
    df_events = find_events_by_type(event_type, conn)
    
    if len(df_events) < min_occurrences:
        print(f"❌ Pas assez d'événements (n={len(df_events)} < {min_occurrences})")
        conn.close()
        return None
    
    # ÉTAPE 2 + 3 : Mesurer impact + Calculer R²
    print(f"[ÉTAPE 2+3] Calcul impacts + R² tendances...")
    print()
    
    events_with_data = []
    
    for idx, row in df_events.iterrows():
        event_time = pd.to_datetime(row['ts_utc'])
        
        print(f"  [{idx+1}/{len(df_events)}] {event_time.strftime('%Y-%m-%d')}...", end=' ')
        
        # Mesurer impact
        impact = measure_real_impact(event_time, conn)
        if impact is None or impact < 5:
            print("⏭️  skip")
            continue
        
        # Calculer R²
        r2_info = calculate_r2_for_event(event_time, conn)
        if r2_info is None:
            print("⏭️  skip (no R²)")
            continue
        
        events_with_data.append({
            'event_time': event_time,
            'event_key': row['event_key'],
            'country': row['country'],
            'impact_measured': impact,
            'r2_trend': r2_info['r2'],
            'duration_hours': r2_info['duration_hours'],
            'amplitude_pips': r2_info['amplitude_pips']
        })
        
        print(f"✅ impact={impact:.1f}p | R²={r2_info['r2']:.3f}")
    
    print()
    print(f"✅ {len(events_with_data)} événements avec données complètes")
    print()
    
    if len(events_with_data) < min_occurrences:
        print(f"❌ Pas assez de données complètes (n={len(events_with_data)} < {min_occurrences})")
        conn.close()
        return None
    
    # ÉTAPE 4 : Calibration
    calibration_result = calibrate_amplification_function(events_with_data, df_scores)
    
    if calibration_result is None:
        conn.close()
        return None
    
    # ÉTAPE 5 : Validation
    print(f"[ÉTAPE 5] Validation prédictions vs baseline...")
    print()
    
    # Convertir format pour validate_predictions
    clusters_format = [{
        'cluster_time': e['event_time'],
        'events': [{'event_key': e['event_key'], 'country': e['country']}],
        'impact_measured': e['impact_measured'],
        'r2_trend': e['r2_trend'],
        'duration_hours': e['duration_hours'],
        'amplitude_pips': e['amplitude_pips']
    } for e in events_with_data]
    
    validation_result = validate_predictions_with_baseline(
        calibration_result['function'],
        clusters_format,
        df_scores,
        baseline_amp=2.5
    )
    
    metrics = validation_result['metrics']
    
    print(f"✅ Validation complétée")
    print(f"   MAE fonction : {metrics['mae_function']:.2f} pips")
    print(f"   MAE baseline : {metrics['mae_baseline']:.2f} pips")
    print(f"   Amélioration : +{metrics['improvement_mae_pct']:.1f}%")
    print()
    
    # ÉTAPE 6 : Décision
    print(f"[ÉTAPE 6] Décision intégration...")
    print()
    
    decision_result = decide_integration(metrics)
    
    print(f"{'='*80}")
    print(f"DÉCISION : {decision_result['decision']}")
    print(f"{'='*80}")
    print()
    print(f"Confiance    : {decision_result['confidence']}")
    print(f"Amélioration : +{decision_result['improvement_pct']:.1f}%")
    print()
    print(f"Recommandation :")
    print(f"  {decision_result['recommendation']}")
    print()
    print(f"Next steps :")
    for step in decision_result['next_steps']:
        print(f"  • {step}")
    print()
    
    # Export résultats
    event_type_safe = event_type.lower().replace(' ', '_')
    json_path = output_dir / f"{event_type_safe}_calibration.json"
    
    result_export = {
        'event_type': event_type,
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'window': WINDOW,
            'lookback_days': LOOKBACK_DAYS,
            'min_occurrences': min_occurrences,
            'max_date': MAX_DATE
        },
        'events_analyzed': len(events_with_data),
        'calibration': {
            'best_model': calibration_result['best_model'],
            'formula': calibration_result['formula'],
            'parameters': calibration_result['parameters'],
            'metrics': calibration_result['metrics']
        },
        'validation': metrics,
        'decision': decision_result
    }
    
    with open(json_path, 'w') as f:
        json.dump(result_export, f, indent=2)
    
    print(f"💾 Résultats exportés : {json_path.name}")
    print()
    
    conn.close()
    
    return result_export


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline Master - Calibration Universelle Amplification",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--event_type',
        type=str,
        required=True,
        help='Type événement (ex: "fed interest rate decision", "cpi")'
    )
    
    parser.add_argument(
        '--min_occurrences',
        type=int,
        default=3,
        help='Minimum événements requis (default: 3)'
    )
    
    parser.add_argument(
        '--output_dir',
        type=Path,
        default=None,
        help='Répertoire sortie (default: ./calibration_results)'
    )
    
    args = parser.parse_args()
    
    result = run_calibration_pipeline(
        event_type=args.event_type,
        min_occurrences=args.min_occurrences,
        output_dir=args.output_dir
    )
    
    if result is None:
        sys.exit(1)
    elif result['decision']['decision'] in ['EXCELLENT', 'GOOD']:
        sys.exit(0)
    else:
        sys.exit(2)
