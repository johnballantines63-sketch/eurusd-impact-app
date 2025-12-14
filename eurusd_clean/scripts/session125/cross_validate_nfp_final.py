#!/usr/bin/env python3
"""
SESSION 125 - VALIDATION CROISÉE CPI → NFP (FINAL)
===================================================
Teste fonction amp(R²) calibrée sur CPI sur événements NFP
Utilise event_key = 'non farm payrolls'
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
import json
from datetime import timedelta
from scipy.stats import linregress

print("="*80)
print("SESSION 125 - VALIDATION CROISÉE CPI → NFP")
print("="*80)
print()

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
CALIBRATION_PATH = Path(__file__).parent / "calibration_results" / "amplification_function_calibrated.json"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
OUTPUT_DIR = Path(__file__).parent / "cross_validation"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# FONCTIONS
# ============================================================================

with open(CALIBRATION_PATH, 'r') as f:
    calib_data = json.load(f)

params = calib_data['best_model']['parameters']

def calculate_amplification_from_r2(r2_trend):
    a, b, c = params
    r2 = max(0.0, min(1.0, r2_trend))
    amp = a + b * r2 + c * r2**2
    return max(0.01, min(0.20, amp))

def detect_swing_highs(prices, window=240, threshold=0.0001):
    swing_highs = []
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        if center > max(left.max(), right.max()) + threshold:
            swing_highs.append(i)
    return swing_highs

def detect_swing_lows(prices, window=240, threshold=0.0001):
    swing_lows = []
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        if center < min(left.min(), right.min()) - threshold:
            swing_lows.append(i)
    return swing_lows

def detect_trend_reversals(prices, timestamps, window=240, min_amplitude_pips=30):
    swing_highs = detect_swing_highs(prices, window)
    swing_lows = detect_swing_lows(prices, window)
    
    extrema = []
    for idx in swing_highs:
        extrema.append({'type': 'HIGH', 'index': idx, 'price': prices[idx], 'timestamp': timestamps[idx]})
    for idx in swing_lows:
        extrema.append({'type': 'LOW', 'index': idx, 'price': prices[idx], 'timestamp': timestamps[idx]})
    
    extrema.sort(key=lambda x: x['index'])
    
    reversals = []
    for extremum in extrema:
        start_idx = extremum['index']
        end_idx = len(prices) - 1
        
        if end_idx - start_idx < 60:
            continue
        
        segment_prices = prices[start_idx:end_idx + 1]
        amplitude = (segment_prices.max() - segment_prices.min()) * 10000
        
        if amplitude < min_amplitude_pips:
            continue
        
        price_start = prices[start_idx]
        price_end = prices[end_idx]
        
        if extremum['type'] == 'HIGH' and price_end < price_start:
            reversal_type = 'HIGH_TO_LOW'
        elif extremum['type'] == 'LOW' and price_end > price_start:
            reversal_type = 'LOW_TO_HIGH'
        else:
            continue
        
        duration = (timestamps[end_idx] - timestamps[start_idx]).total_seconds() / 3600.0
        
        t = np.arange(len(segment_prices))
        slope, intercept, r_value, _, _ = linregress(t, segment_prices)
        r_squared = r_value ** 2
        
        reversals.append({
            'type': reversal_type,
            'time': extremum['timestamp'],
            'r2': r_squared,
            'duration_hours': duration,
            'amplitude_pips': amplitude
        })
    
    return reversals

def calculate_adjusted_empirical_score(base_score, surprise_pct):
    if surprise_pct <= 10:
        return base_score
    elif surprise_pct <= 20:
        return base_score * 1.15
    else:
        return base_score * 1.30

def calculate_impact_d(empirical_score, num_events, amplification):
    return empirical_score * amplification * np.sqrt(num_events)

print(f"✅ Fonction CPI : {calib_data['best_model']['formula']}")
print(f"   Calibrée sur {calib_data['statistics']['n_samples']} clusters CPI")
print()

# ============================================================================
# CHARGER NFP
# ============================================================================

print("="*80)
print("CHARGEMENT ÉVÉNEMENTS NFP")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

query_nfp = """
SELECT 
    ts_utc,
    event_key,
    country,
    actual,
    estimate,
    importance_n
FROM events
WHERE country = 'US'
  AND event_key = 'non farm payrolls'
  AND importance_n = 3
  AND ts_utc >= '2023-01-01'
ORDER BY ts_utc
"""

df_nfp = conn.execute(query_nfp).df()

print(f"✅ {len(df_nfp)} événements NFP depuis 2023")
print()

if len(df_nfp) < 3:
    print("⚠️  Pas assez d'événements NFP")
    conn.close()
    sys.exit(0)

df_nfp['ts_utc'] = pd.to_datetime(df_nfp['ts_utc'])

# ============================================================================
# CALCULER IMPACT MESURÉ NFP
# ============================================================================

print("="*80)
print("CALCUL IMPACT MESURÉ NFP")
print("="*80)
print()

nfp_with_impact = []

for idx, nfp_event in df_nfp.iterrows():
    cluster_time = nfp_event['ts_utc']
    
    print(f"🔍 [{idx+1}/{len(df_nfp)}] {cluster_time.date()} {cluster_time.time()} ... ", end='')
    
    try:
        time_start = cluster_time - pd.Timedelta(hours=2)
        time_end = cluster_time + pd.Timedelta(hours=2)
        
        df_prices = conn.execute("""
            SELECT datetime, high, low, close
            FROM prices_1m
            WHERE datetime >= ? AND datetime <= ?
            ORDER BY datetime
        """, [str(time_start), str(time_end)]).df()
        
        if len(df_prices) < 60:
            print("⚠️  Pas assez prix")
            continue
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        
        before_mask = df_prices['datetime'] < cluster_time
        after_mask = df_prices['datetime'] > cluster_time
        
        if before_mask.sum() == 0 or after_mask.sum() == 0:
            print("⚠️  Pas prix avant/après")
            continue
        
        price_before = df_prices[before_mask].iloc[-1]['close']
        max_high = df_prices[after_mask]['high'].max()
        
        impact_pips = (max_high - price_before) * 10000
        
        if impact_pips < 5:
            print(f"⚠️  Impact faible ({impact_pips:.1f}p)")
            continue
        
        nfp_with_impact.append({
            'cluster_time': cluster_time,
            'impact_measured': impact_pips,
            'event': nfp_event
        })
        
        print(f"✅ {impact_pips:.1f} pips")
        
    except Exception as e:
        print(f"❌ {str(e)[:40]}")

print()
print(f"✅ {len(nfp_with_impact)} NFP avec impact mesuré")
print()

if len(nfp_with_impact) < 3:
    print(f"⚠️  Pas assez de données (n={len(nfp_with_impact)} < 3)")
    conn.close()
    sys.exit(0)

# ============================================================================
# PRÉDIRE AVEC FONCTION CPI
# ============================================================================

print("="*80)
print("PRÉDICTIONS NFP AVEC FONCTION CPI")
print("="*80)
print()

df_scores = pd.read_csv(SCORES_PATH)

results_nfp = []

for nfp_data in nfp_with_impact:
    cluster_time = nfp_data['cluster_time']
    impact_measured = nfp_data['impact_measured']
    nfp_event = nfp_data['event']
    
    print(f"🔍 {cluster_time.date()} ... ", end='')
    
    try:
        # Mapper score (event_key = 'non farm payrolls' → event_name = 'non_farm_payrolls')
        # IMPORTANT : country = 'usd' (code devise) pas 'US' (code pays)
        score_row = df_scores[
            (df_scores['event_name'] == 'non_farm_payrolls') & 
            (df_scores['country'] == 'usd')
        ]
        
        if len(score_row) == 0:
            print("⚠️  Score NFP introuvable")
            continue
        
        base_score = score_row.iloc[0]['empirical_score']
        
        # Surprise
        if pd.notna(nfp_event['actual']) and pd.notna(nfp_event['estimate']) and nfp_event['estimate'] != 0:
            surprise_pct = abs((nfp_event['actual'] - nfp_event['estimate']) / nfp_event['estimate']) * 100
        else:
            surprise_pct = 0
        
        adjusted_score = calculate_adjusted_empirical_score(base_score, surprise_pct)
        
        # Détecter R²
        lookback_start = cluster_time - pd.Timedelta(days=30)
        
        df_prices = conn.execute("""
            SELECT datetime, close
            FROM prices_1m
            WHERE datetime >= ? AND datetime < ?
            ORDER BY datetime
        """, [str(lookback_start), str(cluster_time)]).df()
        
        r2_detected = False
        r2_value = None
        amp_from_r2 = 2.5
        
        if len(df_prices) >= 480:
            prices_array = df_prices['close'].values
            timestamps_array = pd.to_datetime(df_prices['datetime']).tolist()
            
            reversals = detect_trend_reversals(prices_array, timestamps_array, window=240, min_amplitude_pips=30)
            
            if reversals:
                last_reversal = reversals[-1]
                r2_value = last_reversal['r2']
                amp_from_r2 = calculate_amplification_from_r2(r2_value)
                r2_detected = True
        
        # Prédire
        impact_pred_cpi = calculate_impact_d(adjusted_score, 1, amp_from_r2)
        impact_pred_baseline = calculate_impact_d(adjusted_score, 1, 2.5)
        
        results_nfp.append({
            'cluster_time': str(cluster_time),
            'event_type': 'NFP',
            'impact_measured': float(impact_measured),
            'r2_detected': r2_detected,
            'r2_value': float(r2_value) if r2_value else None,
            'amp_from_cpi_function': float(amp_from_r2),
            'impact_pred_cpi_function': float(impact_pred_cpi),
            'impact_pred_baseline': float(impact_pred_baseline),
            'error_cpi_function': float(abs(impact_pred_cpi - impact_measured)),
            'error_baseline': float(abs(impact_pred_baseline - impact_measured)),
            'base_score': float(base_score),
            'surprise_pct': float(surprise_pct)
        })
        
        print(f"✅ R²={r2_value:.3f if r2_value else 0:.3f}, pred={impact_pred_cpi:.1f}, real={impact_measured:.1f}")
        
    except Exception as e:
        print(f"❌ {str(e)[:50]}")

conn.close()

print()
print(f"✅ {len(results_nfp)} prédictions NFP")
print()

# ============================================================================
# ANALYSE GÉNÉRALISATION
# ============================================================================

if len(results_nfp) >= 3:
    df_results = pd.DataFrame(results_nfp)
    
    mae_cpi = df_results['error_cpi_function'].mean()
    mae_baseline = df_results['error_baseline'].mean()
    
    rmse_cpi = np.sqrt((df_results['error_cpi_function'] ** 2).mean())
    rmse_baseline = np.sqrt((df_results['error_baseline'] ** 2).mean())
    
    improvement_mae = ((mae_baseline - mae_cpi) / mae_baseline) * 100
    improvement_rmse = ((rmse_baseline - rmse_cpi) / rmse_baseline) * 100
    
    print("="*80)
    print("ANALYSE : GÉNÉRALISATION CPI → NFP")
    print("="*80)
    print()
    
    print(f"📊 VALIDATION CROISÉE NFP (n={len(results_nfp)})")
    print()
    
    print(f"{'Méthode':<30} {'MAE (pips)':<15} {'RMSE (pips)':<15}")
    print("-" * 60)
    print(f"{'Fonction CPI sur NFP':<30} {mae_cpi:<15.2f} {rmse_cpi:<15.2f}")
    print(f"{'Baseline (amp=2.5)':<30} {mae_baseline:<15.2f} {rmse_baseline:<15.2f}")
    print()
    
    print(f"📈 AMÉLIORATION :")
    print(f"   MAE  : {improvement_mae:+.1f}%")
    print(f"   RMSE : {improvement_rmse:+.1f}%")
    print()
    
    # Décision
    if improvement_mae > 5 and improvement_rmse > 5:
        generalization = "EXCELLENT"
        print("✅✅ GÉNÉRALISATION EXCELLENTE !")
        print()
        print("🎯 La fonction amp(R²) calibrée sur CPI fonctionne bien sur NFP")
        print("   → Fonction UNIVERSELLE validée")
        print("   → Option A : Pipeline master automatisé")
    elif improvement_mae > 0 and improvement_rmse > 0:
        generalization = "MODERATE"
        print("✅ Généralisation modérée")
        print()
        print("⚠️  Amélioration faible mais positive")
    else:
        generalization = "FAILED"
        print("❌ PAS DE GÉNÉRALISATION")
        print()
        print("🚫 Fonction CPI ne généralise PAS aux NFP")
        print("   → Fonctions spécifiques par famille requises")
    
    # Sauvegarder
    output_json = OUTPUT_DIR / "cross_validation_cpi_to_nfp_final.json"
    with open(output_json, 'w') as f:
        json.dump({
            'test': 'Cross-validation CPI → NFP',
            'cpi_calibration': calib_data['best_model']['formula'],
            'nfp_results': results_nfp,
            'metrics': {
                'n_nfp': len(results_nfp),
                'mae_cpi_function': float(mae_cpi),
                'mae_baseline': float(mae_baseline),
                'rmse_cpi_function': float(rmse_cpi),
                'rmse_baseline': float(rmse_baseline),
                'improvement_mae_pct': float(improvement_mae),
                'improvement_rmse_pct': float(improvement_rmse)
            },
            'generalization': generalization
        }, f, indent=2)
    
    print()
    print(f"💾 Sauvegardé : {output_json.name}")
    print()
    print(f"🎯 GÉNÉRALISATION : {generalization}")
    
    if generalization == "EXCELLENT":
        print()
        print("➡️  PROCHAINE ÉTAPE : Pipeline Master (Option A)")

else:
    print(f"⚠️  Pas assez de données (n={len(results_nfp)} < 3)")

print()
print("="*80)
print("ÉTAPE 10 TERMINÉE ✅")
print("="*80)
