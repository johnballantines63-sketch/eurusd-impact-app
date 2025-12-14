#!/usr/bin/env python3
"""
SESSION 125 - ÉTAPE 7 FINALE : WINDOW FIXE 240 (APPROCHE VALIDÉE)
===================================================================
Retour à l'approche qui donnait corrélation positive : 0.3731

Paramètres validés :
- Window fixe : 240 min (4h)
- Lookback : 30 jours
- Dernière inversion (amplitude ≥30 pips)
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
print("SESSION 125 - ÉTAPE 7 FINALE : WINDOW 240 FIXE")
print("="*80)
print()

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
MATCHES_PATH = Path(__file__).parent / "matching_clusters" / "matching_clusters.json"
OUTPUT_DIR = Path(__file__).parent / "trend_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# PARAMÈTRES VALIDÉS
WINDOW = 240  # Fixe
LOOKBACK_DAYS = 30
MIN_AMPLITUDE_PIPS = 30

print(f"📁 Base : {DB_PATH}")
print(f"📊 Window : {WINDOW} min (FIXE)")
print(f"📊 Lookback : {LOOKBACK_DAYS} jours")
print(f"📊 Amplitude min : {MIN_AMPLITUDE_PIPS} pips")
print()

# ============================================================================
# FONCTIONS DÉTECTION
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
            'price': extremum['price'],
            'amplitude_pips': amplitude,
            'duration_hours': duration,
            'r2': r_squared
        })
    
    return reversals

# ============================================================================
# CHARGER CLUSTERS
# ============================================================================

print("="*80)
print("ÉTAPE 1 : CHARGEMENT")
print("="*80)
print()

with open(MATCHES_PATH, 'r') as f:
    matches_data = json.load(f)

clusters_with_prices = [c for c in matches_data['matching_clusters'] if c.get('prices_available')]

print(f"✅ {len(clusters_with_prices)} clusters")
print()

# ============================================================================
# DÉTECTION WINDOW FIXE 240
# ============================================================================

print("="*80)
print("ÉTAPE 2 : DÉTECTION (WINDOW 240 FIXE)")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

results = []
success_count = 0
error_count = 0

for i, cluster in enumerate(clusters_with_prices, 1):
    cluster_time = pd.to_datetime(cluster['cluster_time'])
    cluster_time_bern = cluster_time.tz_convert('Europe/Zurich')
    
    print(f"🔍 [{i}/{len(clusters_with_prices)}] {cluster_time.date()} ... ", end='')
    
    lookback_start = cluster_time_bern - timedelta(days=LOOKBACK_DAYS)
    
    try:
        df_prices = conn.execute("""
            SELECT datetime, close, high, low
            FROM prices_bern
            WHERE datetime >= ? AND datetime < ?
            ORDER BY datetime
        """, [str(lookback_start), str(cluster_time_bern)]).df()
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'], utc=True).dt.tz_convert('Europe/Zurich')
        
        if len(df_prices) < WINDOW * 2:
            print("❌ Données insuffisantes")
            error_count += 1
            continue
        
        prices = df_prices['close'].values
        timestamps = df_prices['datetime'].tolist()
        
        # Détecter inversions avec window fixe 240
        reversals = detect_trend_reversals(
            prices, 
            timestamps,
            window=WINDOW,
            min_amplitude_pips=MIN_AMPLITUDE_PIPS
        )
        
        if len(reversals) == 0:
            print("⚠️  Aucune inversion")
            error_count += 1
            continue
        
        # Dernière inversion
        last_reversal = reversals[-1]
        
        results.append({
            'cluster_time': str(cluster_time),
            'impact_measured': cluster.get('impact_measured'),
            'inversion_found': True,
            'inversion_time': str(last_reversal['time']),
            'inversion_type': last_reversal['type'],
            'inversion_price': float(last_reversal['price']),
            'trend_duration_hours': float(last_reversal['duration_hours']),
            'trend_r2': float(last_reversal['r2']),
            'trend_amplitude_pips': float(last_reversal['amplitude_pips']),
            'num_reversals_found': len(reversals)
        })
        
        print(f"✅ R²={last_reversal['r2']:.4f} (dur={last_reversal['duration_hours']:.1f}h, {len(reversals)} inversions)")
        success_count += 1
            
    except Exception as e:
        print(f"❌ Erreur : {str(e)[:50]}")
        error_count += 1

conn.close()

print()
print(f"✅ {success_count} tendances calculées")
print(f"⚠️  {error_count} échecs")
print()

# ============================================================================
# ANALYSE CORRÉLATION
# ============================================================================

print("="*80)
print("ÉTAPE 3 : ANALYSE CORRÉLATION R² ↔ IMPACT")
print("="*80)
print()

if len(results) < 5:
    print("⚠️  Pas assez de résultats")
else:
    df_results = pd.DataFrame(results)
    df_valid = df_results[
        df_results['impact_measured'].notna() & 
        df_results['trend_r2'].notna()
    ].copy()
    
    print(f"📊 {len(df_valid)} cas valides")
    print()
    
    if len(df_valid) >= 5:
        correlation = df_valid['trend_r2'].corr(df_valid['impact_measured'])
        
        print(f"📈 CORRÉLATION R² ↔ IMPACT : {correlation:.4f}")
        print()
        
        print("📊 Statistiques R² :")
        print(f"   Min  : {df_valid['trend_r2'].min():.4f}")
        print(f"   Max  : {df_valid['trend_r2'].max():.4f}")
        print(f"   Moy  : {df_valid['trend_r2'].mean():.4f}")
        print(f"   Med  : {df_valid['trend_r2'].median():.4f}")
        print()
        
        print("📊 Statistiques Impact :")
        print(f"   Min  : {df_valid['impact_measured'].min():.1f} pips")
        print(f"   Max  : {df_valid['impact_measured'].max():.1f} pips")
        print(f"   Moy  : {df_valid['impact_measured'].mean():.1f} pips")
        print(f"   Med  : {df_valid['impact_measured'].median():.1f} pips")
        print()
        
        print("📊 Impact moyen par groupe R² :")
        df_valid['r2_group'] = pd.cut(
            df_valid['trend_r2'], 
            bins=[0, 0.3, 0.6, 1.0],
            labels=['Faible (<0.3)', 'Moyen (0.3-0.6)', 'Fort (>0.6)']
        )
        
        for group_name in ['Faible (<0.3)', 'Moyen (0.3-0.6)', 'Fort (>0.6)']:
            group_data = df_valid[df_valid['r2_group'] == group_name]
            if len(group_data) > 0:
                avg_impact = group_data['impact_measured'].mean()
                print(f"   {group_name:20s} : {avg_impact:.1f} pips (n={len(group_data)})")
        print()

# ============================================================================
# SAUVEGARDER
# ============================================================================

print("="*80)
print("ÉTAPE 4 : SAUVEGARDE")
print("="*80)
print()

output_json = OUTPUT_DIR / "trend_analysis_final.json"
with open(output_json, 'w') as f:
    json.dump({
        'method': 'Window fixe 240 min (approche validée)',
        'parameters': {
            'window': WINDOW,
            'lookback_days': LOOKBACK_DAYS,
            'min_amplitude_pips': MIN_AMPLITUDE_PIPS
        },
        'results': results,
        'summary': {
            'total_analyzed': len(clusters_with_prices),
            'success_count': success_count,
            'error_count': error_count
        }
    }, f, indent=2)

print(f"💾 JSON : {output_json.name}")

if results:
    df_export = pd.DataFrame(results)
    output_csv = OUTPUT_DIR / "trend_analysis_final.csv"
    df_export.to_csv(output_csv, index=False)
    print(f"💾 CSV : {output_csv.name}")

print()

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("="*80)
print("RÉSUMÉ - APPROCHE VALIDÉE (WINDOW 240 FIXE)")
print("="*80)
print()

print(f"📊 Clusters analysés : {len(clusters_with_prices)}")
print(f"✅ Tendances calculées : {success_count}")
print(f"⚠️  Échecs : {error_count}")
print()

if len(results) >= 5 and 'correlation' in locals():
    print(f"📈 Corrélation R² ↔ Impact : {correlation:.4f}")
    
    if correlation > 0.3:
        print()
        print("✅✅ CORRÉLATION POSITIVE CONFIRMÉE !")
        print()
        print("🎯 PROCHAINE ÉTAPE :")
        print("   8. Calibrer fonction amplification(R²)")
        print("   9. Intégrer dans Planificateur")
    elif correlation > 0.2:
        print()
        print("✅ Corrélation modérée mais positive")
    else:
        print()
        print("⚠️  Corrélation faible")

print()
print("="*80)
print("ÉTAPE 7 TERMINÉE ✅")
print("="*80)
