#!/usr/bin/env python3
"""
SESSION 125 - ÉTAPE 10 : VALIDATION CROISÉE CPI → NFP
======================================================
Teste si la fonction amp(R²) calibrée sur CPI généralise aux événements NFP

Workflow :
1. Trouver tous clusters NFP historiques (Non-Farm Payrolls)
2. Matcher clusters NFP identiques (±5 min, même composition)
3. Calculer R² tendance pour chaque cluster NFP
4. Prédire impact NFP avec fonction CPI : amp = f(R²)
5. Comparer avec impact mesuré NFP
6. Métriques : Généralisation réussie ?

DÉCISION :
- Si généralise bien → amp(R²) UNIVERSELLE → Pipeline master
- Si ne généralise pas → Fonctions spécifiques par famille
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

# Configuration
DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
CALIBRATION_PATH = Path(__file__).parent / "calibration_results" / "amplification_function_calibrated.json"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
OUTPUT_DIR = Path(__file__).parent / "cross_validation"
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"📁 DB : {DB_PATH}")
print(f"📁 Calibration (CPI) : {CALIBRATION_PATH}")
print(f"📁 Scores : {SCORES_PATH}")
print()

# ============================================================================
# CHARGER FONCTION CPI
# ============================================================================

print("="*80)
print("CHARGEMENT FONCTION CPI")
print("="*80)
print()

with open(CALIBRATION_PATH, 'r') as f:
    calib_data = json.load(f)

params = calib_data['best_model']['parameters']

def calculate_amplification_from_r2(r2_trend):
    """Fonction calibrée sur CPI (quadratique)"""
    a, b, c = params
    r2 = max(0.0, min(1.0, r2_trend))
    amp = a + b * r2 + c * r2**2
    return max(0.01, min(0.20, amp))

print(f"✅ Fonction CPI : {calib_data['best_model']['formula']}")
print(f"   Calibrée sur {calib_data['statistics']['n_samples']} clusters CPI")
print()

# ============================================================================
# FONCTIONS DÉTECTION R²
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
# FORMULES VALIDÉES
# ============================================================================

def calculate_adjusted_empirical_score(base_score, surprise_pct):
    """Session 55"""
    if surprise_pct <= 10:
        return base_score
    elif surprise_pct <= 20:
        return base_score * 1.15
    else:
        return base_score * 1.30

def calculate_impact_d(empirical_score, num_events, amplification):
    """Session 51"""
    return empirical_score * amplification * np.sqrt(num_events)

# ============================================================================
# ÉTAPE 1 : TROUVER CLUSTERS NFP
# ============================================================================

print("="*80)
print("ÉTAPE 1 : RECHERCHE CLUSTERS NFP")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Requête NFP : "Non-Farm Employment Change" ou "Nonfarm Payrolls"
query_nfp = """
SELECT 
    datetime_utc,
    event_name,
    country,
    actual,
    forecast,
    importance
FROM economic_events
WHERE country = 'US'
  AND importance = 'HIGH'
  AND (
    event_name LIKE '%Non-Farm%'
    OR event_name LIKE '%Nonfarm%'
    OR event_name LIKE '%NFP%'
    OR event_name LIKE '%Payroll%'
  )
  AND datetime_utc >= '2023-01-01'
ORDER BY datetime_utc
"""

df_nfp_raw = conn.execute(query_nfp).df()

print(f"✅ {len(df_nfp_raw)} événements NFP trouvés")
print()

if len(df_nfp_raw) > 0:
    print("📋 Échantillon événements NFP :")
    for idx, row in df_nfp_raw.head(5).iterrows():
        print(f"   {row['datetime_utc']} - {row['event_name']}")
    print()

# ============================================================================
# ÉTAPE 2 : MATCHER CLUSTERS NFP IDENTIQUES
# ============================================================================

print("="*80)
print("ÉTAPE 2 : MATCHING CLUSTERS NFP")
print("="*80)
print()

# Grouper par fenêtre ±5 min
df_nfp_raw['datetime'] = pd.to_datetime(df_nfp_raw['datetime_utc'])
df_nfp_raw = df_nfp_raw.sort_values('datetime')

clusters_nfp = []
window_minutes = 5

i = 0
while i < len(df_nfp_raw):
    current_time = df_nfp_raw.iloc[i]['datetime']
    
    # Tous événements dans ±5 min
    mask = (
        (df_nfp_raw['datetime'] >= current_time - pd.Timedelta(minutes=window_minutes)) &
        (df_nfp_raw['datetime'] <= current_time + pd.Timedelta(minutes=window_minutes))
    )
    
    cluster_events = df_nfp_raw[mask].copy()
    
    if len(cluster_events) > 0:
        cluster_time = cluster_events['datetime'].iloc[0]
        
        # Composition cluster
        composition = tuple(sorted(cluster_events['event_name'].tolist()))
        
        clusters_nfp.append({
            'cluster_time': cluster_time,
            'n_events': len(cluster_events),
            'composition': composition,
            'events': cluster_events
        })
        
        # Avancer après ce cluster
        i += len(cluster_events)
    else:
        i += 1

print(f"✅ {len(clusters_nfp)} clusters NFP identifiés")
print()

# Grouper par composition identique
from collections import defaultdict

composition_groups = defaultdict(list)
for cluster in clusters_nfp:
    composition_groups[cluster['composition']].append(cluster)

# Garder compositions avec ≥3 occurrences
matching_nfp = []
for composition, group in composition_groups.items():
    if len(group) >= 3:
        matching_nfp.append({
            'composition': composition,
            'occurrences': len(group),
            'clusters': group
        })

print(f"📊 Compositions NFP répétées (≥3 fois) : {len(matching_nfp)}")
print()

if matching_nfp:
    for match in matching_nfp:
        print(f"   {match['occurrences']}× : {', '.join(match['composition'][:2])}")
    print()

# ============================================================================
# ÉTAPE 3 : CALCULER IMPACT MESURÉ NFP
# ============================================================================

print("="*80)
print("ÉTAPE 3 : CALCUL IMPACT MESURÉ NFP")
print("="*80)
print()

nfp_with_impact = []

for match in matching_nfp:
    for cluster in match['clusters']:
        cluster_time = cluster['cluster_time']
        
        print(f"🔍 {cluster_time.date()} ... ", end='')
        
        try:
            # Charger prix ±2h
            time_start = cluster_time - pd.Timedelta(hours=2)
            time_end = cluster_time + pd.Timedelta(hours=2)
            
            df_prices = conn.execute("""
                SELECT datetime, high, low, close
                FROM prices_1m
                WHERE datetime >= ? AND datetime <= ?
                ORDER BY datetime
            """, [str(time_start), str(time_end)]).df()
            
            if len(df_prices) < 60:
                print("⚠️  Pas assez de prix")
                continue
            
            df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
            
            # Trouver prix avant/après
            before_mask = df_prices['datetime'] < cluster_time
            after_mask = df_prices['datetime'] > cluster_time
            
            if before_mask.sum() == 0 or after_mask.sum() == 0:
                print("⚠️  Pas de prix avant/après")
                continue
            
            price_before = df_prices[before_mask].iloc[-1]['close']
            
            # Impact = max high dans les 2h après - prix avant
            highs_after = df_prices[after_mask]['high']
            max_high = highs_after.max()
            
            impact_pips = (max_high - price_before) * 10000
            
            cluster['impact_measured'] = impact_pips
            nfp_with_impact.append(cluster)
            
            print(f"✅ Impact = {impact_pips:.1f} pips")
            
        except Exception as e:
            print(f"❌ {str(e)[:40]}")

print()
print(f"✅ {len(nfp_with_impact)} clusters NFP avec impact mesuré")
print()

# ============================================================================
# ÉTAPE 4 : PRÉDIRE IMPACT NFP AVEC FONCTION CPI
# ============================================================================

print("="*80)
print("ÉTAPE 4 : PRÉDICTIONS NFP AVEC FONCTION CPI")
print("="*80)
print()

df_scores = pd.read_csv(SCORES_PATH)

results_nfp = []

for cluster in nfp_with_impact:
    cluster_time = cluster['cluster_time']
    impact_measured = cluster['impact_measured']
    
    print(f"🔍 {cluster_time.date()} ... ", end='')
    
    try:
        # Charger événements
        df_events = cluster['events']
        
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
        
        # Score et surprise
        base_score = df_measurable['empirical_score'].mean()
        
        surprises = []
        for _, evt in df_measurable.iterrows():
            if pd.notna(evt['actual']) and pd.notna(evt['forecast']) and evt['forecast'] != 0:
                surprise_pct = abs((evt['actual'] - evt['forecast']) / evt['forecast']) * 100
                surprises.append(surprise_pct)
        
        max_surprise = max(surprises) if surprises else 0
        adjusted_score = calculate_adjusted_empirical_score(base_score, max_surprise)
        
        # Détecter R² tendance
        lookback_start = cluster_time - pd.Timedelta(days=30)
        
        df_prices = conn.execute("""
            SELECT datetime, close
            FROM prices_1m
            WHERE datetime >= ? AND datetime < ?
            ORDER BY datetime
        """, [str(lookback_start), str(cluster_time)]).df()
        
        r2_detected = False
        r2_value = None
        amp_from_r2 = 2.5  # Défaut
        
        if len(df_prices) >= 480:
            prices_array = df_prices['close'].values
            timestamps_array = pd.to_datetime(df_prices['datetime']).tolist()
            
            reversals = detect_trend_reversals(prices_array, timestamps_array, window=240, min_amplitude_pips=30)
            
            if reversals:
                last_reversal = reversals[-1]
                r2_value = last_reversal['r2']
                # UTILISER FONCTION CPI
                amp_from_r2 = calculate_amplification_from_r2(r2_value)
                r2_detected = True
        
        # Prédire avec fonction CPI
        impact_pred_cpi = calculate_impact_d(adjusted_score, len(df_measurable), amp_from_r2)
        
        # Prédire avec baseline
        impact_pred_baseline = calculate_impact_d(adjusted_score, len(df_measurable), 2.5)
        
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
            'n_events': len(df_measurable),
            'base_score': float(base_score),
            'max_surprise': float(max_surprise)
        })
        
        print(f"✅ R²={r2_value:.3f if r2_value else 0:.3f}, pred={impact_pred_cpi:.1f} (real={impact_measured:.1f})")
        
    except Exception as e:
        print(f"❌ {str(e)[:50]}")

conn.close()

print()
print(f"✅ {len(results_nfp)} prédictions NFP complètes")
print()

# ============================================================================
# ÉTAPE 5 : ANALYSE - FONCTION CPI GÉNÉRALISE À NFP ?
# ============================================================================

print("="*80)
print("ANALYSE : GÉNÉRALISATION CPI → NFP")
print("="*80)
print()

if len(results_nfp) >= 3:
    df_nfp_results = pd.DataFrame(results_nfp)
    
    # Métriques
    mae_cpi_function = df_nfp_results['error_cpi_function'].mean()
    mae_baseline = df_nfp_results['error_baseline'].mean()
    
    rmse_cpi = np.sqrt((df_nfp_results['error_cpi_function'] ** 2).mean())
    rmse_baseline = np.sqrt((df_nfp_results['error_baseline'] ** 2).mean())
    
    improvement_mae = ((mae_baseline - mae_cpi_function) / mae_baseline) * 100
    improvement_rmse = ((rmse_baseline - rmse_cpi) / rmse_baseline) * 100
    
    print(f"📊 VALIDATION CROISÉE NFP (n={len(results_nfp)})")
    print()
    
    print(f"{'Méthode':<25} {'MAE (pips)':<15} {'RMSE (pips)':<15}")
    print("-" * 55)
    print(f"{'Fonction CPI sur NFP':<25} {mae_cpi_function:<15.2f} {rmse_cpi:<15.2f}")
    print(f"{'Baseline (2.5)':<25} {mae_baseline:<15.2f} {rmse_baseline:<15.2f}")
    print()
    
    print(f"📈 AMÉLIORATION (fonction CPI appliquée à NFP) :")
    print(f"   MAE  : {improvement_mae:+.1f}%")
    print(f"   RMSE : {improvement_rmse:+.1f}%")
    print()
    
    # Décision généralisation
    if improvement_mae > 5 and improvement_rmse > 5:
        generalization = "EXCELLENT"
        print("✅✅ GÉNÉRALISATION EXCELLENTE !")
        print()
        print("🎯 La fonction amp(R²) calibrée sur CPI fonctionne bien sur NFP")
        print("   → Fonction UNIVERSELLE validée")
        print("   → Procéder à OPTION A : Pipeline master automatisé")
    elif improvement_mae > 0 and improvement_rmse > 0:
        generalization = "MODERATE"
        print("✅ Généralisation modérée")
        print()
        print("⚠️  Amélioration faible - À discuter")
    else:
        generalization = "FAILED"
        print("❌ PAS DE GÉNÉRALISATION")
        print()
        print("🚫 La fonction CPI ne généralise PAS aux NFP")
        print("   → Fonctions spécifiques par famille requises")
    
else:
    generalization = "INSUFFICIENT_DATA"
    print(f"⚠️  Pas assez de données NFP (n={len(results_nfp)} < 3)")
    generalization = "INSUFFICIENT_DATA"

# ============================================================================
# SAUVEGARDE
# ============================================================================

print()
print("="*80)
print("SAUVEGARDE")
print("="*80)
print()

output_json = OUTPUT_DIR / "cross_validation_cpi_to_nfp.json"
with open(output_json, 'w') as f:
    json.dump({
        'test': 'Cross-validation CPI function on NFP events',
        'cpi_calibration': calib_data['best_model']['formula'],
        'nfp_results': results_nfp,
        'metrics': {
            'n_nfp_clusters': len(results_nfp),
            'mae_cpi_function': float(mae_cpi_function) if len(results_nfp) >= 3 else None,
            'mae_baseline': float(mae_baseline) if len(results_nfp) >= 3 else None,
            'improvement_mae_pct': float(improvement_mae) if len(results_nfp) >= 3 else None,
            'improvement_rmse_pct': float(improvement_rmse) if len(results_nfp) >= 3 else None
        },
        'generalization': generalization
    }, f, indent=2)

print(f"💾 JSON : {output_json.name}")

if results_nfp:
    pd.DataFrame(results_nfp).to_csv(OUTPUT_DIR / "nfp_predictions.csv", index=False)
    print(f"💾 CSV : nfp_predictions.csv")

print()
print("="*80)
print("ÉTAPE 10 TERMINÉE ✅")
print("="*80)
print()

print(f"🎯 GÉNÉRALISATION : {generalization}")

if generalization == "EXCELLENT":
    print()
    print("➡️  PROCHAINE ÉTAPE : Créer Pipeline Master (Option A)")
elif generalization in ["MODERATE", "FAILED"]:
    print()
    print("➡️  PROCHAINE ÉTAPE : Fonctions spécifiques par famille")
