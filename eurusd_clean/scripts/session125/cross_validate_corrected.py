#!/usr/bin/env python3
"""
SESSION 125 - VALIDATION CROISÉE CPI → AUTRE FAMILLE (CORRIGÉ)
===============================================================
Version corrigée utilisant table 'events' (pas 'economic_events')
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
print("SESSION 125 - VALIDATION CROISÉE (TABLE EVENTS)")
print("="*80)
print()

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
CALIBRATION_PATH = Path(__file__).parent / "calibration_results" / "amplification_function_calibrated.json"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
OUTPUT_DIR = Path(__file__).parent / "cross_validation"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# CHARGER FONCTION CPI
# ============================================================================

with open(CALIBRATION_PATH, 'r') as f:
    calib_data = json.load(f)

params = calib_data['best_model']['parameters']

def calculate_amplification_from_r2(r2_trend):
    a, b, c = params
    r2 = max(0.0, min(1.0, r2_trend))
    amp = a + b * r2 + c * r2**2
    return max(0.01, min(0.20, amp))

print(f"✅ Fonction CPI : {calib_data['best_model']['formula']}")
print()

# ============================================================================
# FONCTIONS
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

def calculate_adjusted_empirical_score(base_score, surprise_pct):
    if surprise_pct <= 10:
        return base_score
    elif surprise_pct <= 20:
        return base_score * 1.15
    else:
        return base_score * 1.30

def calculate_impact_d(empirical_score, num_events, amplification):
    return empirical_score * amplification * np.sqrt(num_events)

# ============================================================================
# EXPLORER TABLE EVENTS
# ============================================================================

print("="*80)
print("EXPLORATION TABLE EVENTS")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Compter événements HIGH par famille
query = """
SELECT 
    event_title,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND ts_utc >= '2023-01-01'
GROUP BY event_title
ORDER BY count DESC
LIMIT 20
"""

df_families = conn.execute(query).df()

print("📊 TOP 20 familles HIGH US (table events, depuis 2023) :")
print()

for idx, row in df_families.iterrows():
    print(f"   {row['count']:3d}× {row['event_title']}")

print()

# Choisir une famille NON-CPI pour test
print("🎯 SÉLECTION FAMILLE POUR TEST DE GÉNÉRALISATION :")
print()

# Exclure CPI
non_cpi_families = df_families[~df_families['event_title'].str.contains('CPI', case=False, na=False)]

if len(non_cpi_families) > 0:
    test_family = non_cpi_families.iloc[0]['event_title']
    test_count = non_cpi_families.iloc[0]['count']
    
    print(f"   ✅ Famille sélectionnée : {test_family}")
    print(f"      Occurrences : {test_count}")
    print()
else:
    print("   ⚠️  Aucune famille non-CPI trouvée")
    conn.close()
    sys.exit(1)

# ============================================================================
# CHARGER CLUSTERS FAMILLE TEST
# ============================================================================

print("="*80)
print(f"CHARGEMENT CLUSTERS : {test_family}")
print("="*80)
print()

query_test = """
SELECT 
    ts_utc,
    event_title,
    event_key,
    country,
    actual,
    estimate,
    forecast,
    importance_n
FROM events
WHERE country = 'US'
  AND event_title = ?
  AND importance_n = 3
  AND ts_utc >= '2023-01-01'
ORDER BY ts_utc
"""

df_test_events = conn.execute(query_test, [test_family]).df()

print(f"✅ {len(df_test_events)} événements {test_family}")
print()

# Grouper par cluster (±5 min)
df_test_events['ts_utc'] = pd.to_datetime(df_test_events['ts_utc'])

clusters_test = []
window_minutes = 5

i = 0
while i < len(df_test_events):
    current_time = df_test_events.iloc[i]['ts_utc']
    
    mask = (
        (df_test_events['ts_utc'] >= current_time - pd.Timedelta(minutes=window_minutes)) &
        (df_test_events['ts_utc'] <= current_time + pd.Timedelta(minutes=window_minutes))
    )
    
    cluster_events = df_test_events[mask].copy()
    
    if len(cluster_events) > 0:
        clusters_test.append({
            'cluster_time': cluster_events['ts_utc'].iloc[0],
            'n_events': len(cluster_events),
            'events': cluster_events
        })
        
        i += len(cluster_events)
    else:
        i += 1

print(f"✅ {len(clusters_test)} clusters identifiés")
print()

# ============================================================================
# CALCULER IMPACT MESURÉ
# ============================================================================

print("="*80)
print("CALCUL IMPACT MESURÉ")
print("="*80)
print()

clusters_with_impact = []

for cluster in clusters_test:
    cluster_time = cluster['cluster_time']
    
    print(f"🔍 {cluster_time.date()} {cluster_time.time()} ... ", end='')
    
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
        
        if impact_pips < 5:  # Filtrer impacts trop faibles
            print(f"⚠️  Impact faible ({impact_pips:.1f} pips)")
            continue
        
        cluster['impact_measured'] = impact_pips
        clusters_with_impact.append(cluster)
        
        print(f"✅ {impact_pips:.1f} pips")
        
    except Exception as e:
        print(f"❌ {str(e)[:40]}")

print()
print(f"✅ {len(clusters_with_impact)} clusters avec impact mesuré")
print()

# ============================================================================
# PRÉDIRE AVEC FONCTION CPI
# ============================================================================

if len(clusters_with_impact) < 3:
    print(f"⚠️  Pas assez de données (n={len(clusters_with_impact)} < 3)")
    conn.close()
    sys.exit(0)

print("="*80)
print(f"PRÉDICTIONS {test_family} AVEC FONCTION CPI")
print("="*80)
print()

df_scores = pd.read_csv(SCORES_PATH)

results = []

for cluster in clusters_with_impact[:10]:  # Limiter à 10 pour vitesse
    cluster_time = cluster['cluster_time']
    impact_measured = cluster['impact_measured']
    
    print(f"🔍 {cluster_time.date()} ... ", end='')
    
    try:
        df_events = cluster['events']
        
        # Mapper scores (utiliser event_title au lieu de event_name)
        df_events_merged = df_events.merge(
            df_scores[['event_name', 'country', 'empirical_score']],
            left_on=['event_title', 'country'],
            right_on=['event_name', 'country'],
            how='left'
        )
        
        df_measurable = df_events_merged[df_events_merged['empirical_score'].notna()]
        
        if len(df_measurable) == 0:
            print("⚠️  Pas de scores")
            continue
        
        base_score = df_measurable['empirical_score'].mean()
        
        surprises = []
        for _, evt in df_measurable.iterrows():
            if pd.notna(evt['actual']) and pd.notna(evt['estimate']) and evt['estimate'] != 0:
                surprise_pct = abs((evt['actual'] - evt['estimate']) / evt['estimate']) * 100
                surprises.append(surprise_pct)
        
        max_surprise = max(surprises) if surprises else 0
        adjusted_score = calculate_adjusted_empirical_score(base_score, max_surprise)
        
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
        
        impact_pred_cpi = calculate_impact_d(adjusted_score, len(df_measurable), amp_from_r2)
        impact_pred_baseline = calculate_impact_d(adjusted_score, len(df_measurable), 2.5)
        
        results.append({
            'cluster_time': str(cluster_time),
            'event_family': test_family,
            'impact_measured': float(impact_measured),
            'r2_detected': r2_detected,
            'r2_value': float(r2_value) if r2_value else None,
            'amp_from_cpi': float(amp_from_r2),
            'impact_pred_cpi': float(impact_pred_cpi),
            'impact_pred_baseline': float(impact_pred_baseline),
            'error_cpi': float(abs(impact_pred_cpi - impact_measured)),
            'error_baseline': float(abs(impact_pred_baseline - impact_measured))
        })
        
        print(f"✅ pred={impact_pred_cpi:.1f} real={impact_measured:.1f}")
        
    except Exception as e:
        print(f"❌ {str(e)[:40]}")

conn.close()

print()
print(f"✅ {len(results)} prédictions")
print()

# ============================================================================
# ANALYSE
# ============================================================================

if len(results) >= 3:
    df_results = pd.DataFrame(results)
    
    mae_cpi = df_results['error_cpi'].mean()
    mae_baseline = df_results['error_baseline'].mean()
    
    improvement = ((mae_baseline - mae_cpi) / mae_baseline) * 100
    
    print("="*80)
    print(f"GÉNÉRALISATION CPI → {test_family}")
    print("="*80)
    print()
    
    print(f"📊 n={len(results)} clusters")
    print()
    print(f"{'Méthode':<25} {'MAE (pips)':<15}")
    print("-" * 40)
    print(f"{'Fonction CPI':<25} {mae_cpi:<15.2f}")
    print(f"{'Baseline (2.5)':<25} {mae_baseline:<15.2f}")
    print()
    print(f"📈 Amélioration : {improvement:+.1f}%")
    print()
    
    if improvement > 5:
        print("✅✅ GÉNÉRALISATION EXCELLENTE !")
        decision = "EXCELLENT"
    elif improvement > 0:
        print("✅ Généralisation modérée")
        decision = "MODERATE"
    else:
        print("❌ PAS DE GÉNÉRALISATION")
        decision = "FAILED"
    
    # Sauvegarder
    output = OUTPUT_DIR / f"cross_validation_cpi_to_{test_family.replace(' ', '_').lower()}.json"
    with open(output, 'w') as f:
        json.dump({
            'test_family': test_family,
            'cpi_function': calib_data['best_model']['formula'],
            'results': results,
            'metrics': {
                'mae_cpi': float(mae_cpi),
                'mae_baseline': float(mae_baseline),
                'improvement_pct': float(improvement)
            },
            'decision': decision
        }, f, indent=2)
    
    print(f"💾 Sauvegardé : {output.name}")
    print()
    print(f"🎯 DÉCISION : {decision}")

print()
print("="*80)
