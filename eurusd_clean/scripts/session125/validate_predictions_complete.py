#!/usr/bin/env python3
"""
SESSION 125 - ÉTAPE 9C : VALIDATION PRÉDICTIONS AMPLIFICATION DYNAMIQUE
========================================================================
Teste la séquence complète AVANT intégration Planificateur

Workflow :
1. Pour chaque des 29 clusters CPI
2. Détecter R² tendance (window 240, lookback 30j)
3. Calculer amplification = f(R²) avec fonction calibrée
4. Prédire impact avec amplification dynamique
5. Comparer avec impact mesuré
6. Calculer métriques vs baseline (amp=2.5 fixe)
7. DÉCISION : Intégrer ou non ?
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
print("SESSION 125 - VALIDATION PRÉDICTIONS AMPLIFICATION DYNAMIQUE")
print("="*80)
print()

# Configuration
DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
TRENDS_PATH = Path(__file__).parent / "trend_analysis" / "trend_analysis_final.csv"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
CALIBRATION_PATH = Path(__file__).parent / "calibration_results" / "amplification_function_calibrated.json"
OUTPUT_DIR = Path(__file__).parent / "validation_predictions"
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"📁 Tendances : {TRENDS_PATH}")
print(f"📁 Scores : {SCORES_PATH}")
print(f"📁 Calibration : {CALIBRATION_PATH}")
print()

# ============================================================================
# CHARGER FONCTION CALIBRÉE
# ============================================================================

with open(CALIBRATION_PATH, 'r') as f:
    calib_data = json.load(f)

params = calib_data['best_model']['parameters']

def calculate_amplification_from_r2(r2_trend):
    """Fonction calibrée quadratique"""
    a, b, c = params
    r2 = max(0.0, min(1.0, r2_trend))
    amp = a + b * r2 + c * r2**2
    return max(0.01, min(0.20, amp))

print(f"✅ Fonction calibrée chargée : {calib_data['best_model']['formula']}")
print()

# ============================================================================
# FONCTIONS DÉTECTION R² (copie Session 125 Étape 7)
# ============================================================================

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

# ============================================================================
# FORMULES VALIDÉES (Session 55)
# ============================================================================

def calculate_adjusted_empirical_score(base_score, surprise_pct):
    """Session 55 - Ajustement score (99.9% précision)"""
    if surprise_pct <= 10:
        return base_score
    elif surprise_pct <= 20:
        return base_score * 1.15
    else:
        return base_score * 1.30

def calculate_impact_d(empirical_score, num_events, amplification):
    """Session 51 - Impact D (98.6% précision)"""
    return empirical_score * amplification * np.sqrt(num_events)

# ============================================================================
# CHARGER DONNÉES
# ============================================================================

print("="*80)
print("ÉTAPE 1 : CHARGEMENT")
print("="*80)
print()

df_trends = pd.read_csv(TRENDS_PATH)
df_scores = pd.read_csv(SCORES_PATH)

print(f"✅ {len(df_trends)} clusters")
print(f"✅ {len(df_scores)} familles scores")
print()

# ============================================================================
# TEST PRÉDICTIONS COMPLÈTES
# ============================================================================

print("="*80)
print("ÉTAPE 2 : PRÉDICTIONS AVEC AMPLIFICATION DYNAMIQUE")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

results = []

for idx, row in df_trends.iterrows():
    cluster_time = pd.to_datetime(row['cluster_time'])
    impact_measured = row['impact_measured']
    
    if pd.isna(impact_measured):
        continue
    
    print(f"🔍 [{idx+1}/{len(df_trends)}] {cluster_time.date()} ... ", end='')
    
    cluster_time_utc = cluster_time.tz_localize(None) if cluster_time.tzinfo else cluster_time
    
    try:
        # 1. CHARGER ÉVÉNEMENTS ±5 min
        time_start = cluster_time_utc - pd.Timedelta(minutes=5)
        time_end = cluster_time_utc + pd.Timedelta(minutes=5)
        
        df_events = conn.execute("""
            SELECT event_name, country, actual, forecast
            FROM economic_events
            WHERE datetime_utc >= ? AND datetime_utc <= ?
              AND importance = 'HIGH'
        """, [str(time_start), str(time_end)]).df()
        
        if len(df_events) == 0:
            print("⚠️  Pas d'événements")
            continue
        
        # Mapper scores
        df_events = df_events.merge(
            df_scores[['event_name', 'country', 'empirical_score']],
            on=['event_name', 'country'],
            how='left'
        )
        
        df_measurable = df_events[df_events['empirical_score'].notna()]
        
        if len(df_measurable) == 0:
            print("⚠️  Pas de scores")
            continue
        
        # 2. CALCULER SCORE ET SURPRISE
        base_score = df_measurable['empirical_score'].mean()
        
        surprises = []
        for _, evt in df_measurable.iterrows():
            if pd.notna(evt['actual']) and pd.notna(evt['forecast']) and evt['forecast'] != 0:
                surprise_pct = abs((evt['actual'] - evt['forecast']) / evt['forecast']) * 100
                surprises.append(surprise_pct)
        
        max_surprise = max(surprises) if surprises else 0
        
        adjusted_score = calculate_adjusted_empirical_score(base_score, max_surprise)
        
        # 3. DÉTECTER R² TENDANCE
        lookback_start = cluster_time_utc - pd.Timedelta(days=30)
        
        df_prices = conn.execute("""
            SELECT datetime, close
            FROM prices_1m
            WHERE datetime >= ? AND datetime < ?
            ORDER BY datetime
        """, [str(lookback_start), str(cluster_time_utc)]).df()
        
        r2_detected = False
        r2_value = None
        amp_dynamic = 2.5  # Défaut
        
        if len(df_prices) >= 480:
            prices_array = df_prices['close'].values
            timestamps_array = pd.to_datetime(df_prices['datetime']).tolist()
            
            reversals = detect_trend_reversals(prices_array, timestamps_array, window=240, min_amplitude_pips=30)
            
            if reversals:
                last_reversal = reversals[-1]
                r2_value = last_reversal['r2']
                amp_dynamic = calculate_amplification_from_r2(r2_value)
                r2_detected = True
        
        # 4. PRÉDIRE IMPACT (Dynamique)
        impact_pred_dynamic = calculate_impact_d(
            adjusted_score,
            len(df_measurable),
            amp_dynamic
        )
        
        # 5. PRÉDIRE IMPACT (Baseline fixe 2.5)
        impact_pred_baseline = calculate_impact_d(
            adjusted_score,
            len(df_measurable),
            2.5
        )
        
        results.append({
            'cluster_time': str(cluster_time),
            'impact_measured': float(impact_measured),
            'r2_detected': r2_detected,
            'r2_value': float(r2_value) if r2_value else None,
            'amp_dynamic': float(amp_dynamic),
            'impact_pred_dynamic': float(impact_pred_dynamic),
            'impact_pred_baseline': float(impact_pred_baseline),
            'error_dynamic': float(abs(impact_pred_dynamic - impact_measured)),
            'error_baseline': float(abs(impact_pred_baseline - impact_measured)),
            'n_events': len(df_measurable),
            'base_score': float(base_score),
            'adjusted_score': float(adjusted_score),
            'max_surprise': float(max_surprise)
        })
        
        print(f"✅ R²={r2_value:.3f if r2_value else 0:.3f}, amp={amp_dynamic:.4f}, pred={impact_pred_dynamic:.1f} (real={impact_measured:.1f})")
        
    except Exception as e:
        print(f"❌ {str(e)[:50]}")

conn.close()

print()
print(f"✅ {len(results)} prédictions complètes")
print()

# ============================================================================
# ANALYSE COMPARATIVE
# ============================================================================

print("="*80)
print("ÉTAPE 3 : ANALYSE COMPARATIVE")
print("="*80)
print()

if len(results) >= 5:
    df_results = pd.DataFrame(results)
    
    # Métriques globales
    mae_dynamic = df_results['error_dynamic'].mean()
    mae_baseline = df_results['error_baseline'].mean()
    
    rmse_dynamic = np.sqrt((df_results['error_dynamic'] ** 2).mean())
    rmse_baseline = np.sqrt((df_results['error_baseline'] ** 2).mean())
    
    r2_dynamic = 1 - (df_results['error_dynamic'] ** 2).sum() / ((df_results['impact_measured'] - df_results['impact_measured'].mean()) ** 2).sum()
    r2_baseline = 1 - (df_results['error_baseline'] ** 2).sum() / ((df_results['impact_measured'] - df_results['impact_measured'].mean()) ** 2).sum()
    
    print(f"📊 MÉTRIQUES GLOBALES (n={len(results)})")
    print()
    
    print(f"{'Méthode':<20} {'MAE (pips)':<15} {'RMSE (pips)':<15} {'R²':<10}")
    print("-" * 60)
    print(f"{'Dynamique R²':<20} {mae_dynamic:<15.2f} {rmse_dynamic:<15.2f} {r2_dynamic:<10.4f}")
    print(f"{'Baseline (2.5)':<20} {mae_baseline:<15.2f} {rmse_baseline:<15.2f} {r2_baseline:<10.4f}")
    print()
    
    # Amélioration
    improvement_mae = ((mae_baseline - mae_dynamic) / mae_baseline) * 100
    improvement_rmse = ((rmse_baseline - rmse_dynamic) / rmse_baseline) * 100
    
    print(f"📈 AMÉLIORATION :")
    print(f"   MAE  : {improvement_mae:+.1f}%")
    print(f"   RMSE : {improvement_rmse:+.1f}%")
    print()
    
    # R² détectés
    n_r2_detected = df_results['r2_detected'].sum()
    print(f"🔍 R² détecté : {n_r2_detected}/{len(results)} cas ({n_r2_detected/len(results)*100:.1f}%)")
    print()
    
    # Statistiques par détection R²
    df_detected = df_results[df_results['r2_detected']]
    df_not_detected = df_results[~df_results['r2_detected']]
    
    if len(df_detected) > 0:
        print(f"📊 AVEC R² détecté (n={len(df_detected)}) :")
        print(f"   MAE dynamique  : {df_detected['error_dynamic'].mean():.2f} pips")
        print(f"   MAE baseline   : {df_detected['error_baseline'].mean():.2f} pips")
        print()
    
    if len(df_not_detected) > 0:
        print(f"📊 SANS R² détecté (n={len(df_not_detected)}) :")
        print(f"   MAE (amp=2.5)  : {df_not_detected['error_baseline'].mean():.2f} pips")
        print()

# ============================================================================
# DÉCISION
# ============================================================================

print("="*80)
print("DÉCISION D'INTÉGRATION")
print("="*80)
print()

if len(results) >= 5:
    if improvement_mae > 5 and improvement_rmse > 5:
        print("✅✅ AMÉLIORATION SIGNIFICATIVE (>5%) !")
        print()
        print("🎯 RECOMMANDATION : INTÉGRER dans Planificateur")
        decision = "INTEGRATE"
    elif improvement_mae > 0 and improvement_rmse > 0:
        print("✅ Amélioration modeste")
        print()
        print("⚠️  RECOMMANDATION : À discuter (amélioration faible)")
        decision = "DISCUSS"
    else:
        print("❌ PAS D'AMÉLIORATION")
        print()
        print("🚫 RECOMMANDATION : NE PAS INTÉGRER")
        decision = "REJECT"
else:
    print("⚠️  Pas assez de données pour décision")
    decision = "INSUFFICIENT_DATA"

# ============================================================================
# SAUVEGARDE
# ============================================================================

print()
print("="*80)
print("SAUVEGARDE RÉSULTATS")
print("="*80)
print()

# JSON complet
output_json = OUTPUT_DIR / "validation_amplification_dynamic.json"
with open(output_json, 'w') as f:
    json.dump({
        'method': 'Amplification dynamique basée sur R² tendance',
        'calibration_formula': calib_data['best_model']['formula'],
        'results': results,
        'metrics': {
            'mae_dynamic': float(mae_dynamic),
            'mae_baseline': float(mae_baseline),
            'rmse_dynamic': float(rmse_dynamic),
            'rmse_baseline': float(rmse_baseline),
            'r2_dynamic': float(r2_dynamic),
            'r2_baseline': float(r2_baseline),
            'improvement_mae_pct': float(improvement_mae),
            'improvement_rmse_pct': float(improvement_rmse)
        },
        'decision': decision
    }, f, indent=2)

print(f"💾 JSON : {output_json.name}")

# CSV
if results:
    pd.DataFrame(results).to_csv(OUTPUT_DIR / "validation_predictions.csv", index=False)
    print(f"💾 CSV : validation_predictions.csv")

print()
print("="*80)
print("ÉTAPE 9C TERMINÉE ✅")
print("="*80)
print()

print(f"🎯 DÉCISION : {decision}")
