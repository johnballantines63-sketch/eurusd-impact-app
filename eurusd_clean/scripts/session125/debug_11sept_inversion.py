#!/usr/bin/env python3
"""
DEBUG 11 SEPTEMBRE - Comparer avec Session 107
===============================================
Pourquoi R² = 0.1859 au lieu de 0.6376 ?
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import linregress
import pytz

print("="*80)
print("DEBUG 11 SEPTEMBRE - COMPARAISON SESSION 107")
print("="*80)
print()

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
TZ_BERN = pytz.timezone('Europe/Zurich')

# Référence Session 107 (validée MT5)
REF_INVERSION_TIME = datetime(2025, 9, 9, 8, 0, tzinfo=TZ_BERN)
REF_CLUSTER_TIME = datetime(2025, 9, 11, 14, 30, tzinfo=TZ_BERN)
REF_DURATION = 54.58
REF_R2 = 0.6376

print("🎯 RÉFÉRENCE SESSION 107 (validée MT5) :")
print(f"   Inversion : {REF_INVERSION_TIME.strftime('%Y-%m-%d %H:%M')} Bern")
print(f"   Cluster   : {REF_CLUSTER_TIME.strftime('%Y-%m-%d %H:%M')} Bern")
print(f"   Durée     : {REF_DURATION:.2f}h")
print(f"   R²        : {REF_R2:.4f}")
print(f"   Type      : PEAK → baisse")
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
        extrema.append({
            'type': 'HIGH',
            'index': idx,
            'price': prices[idx],
            'timestamp': timestamps[idx]
        })
    for idx in swing_lows:
        extrema.append({
            'type': 'LOW',
            'index': idx,
            'price': prices[idx],
            'timestamp': timestamps[idx]
        })
    
    extrema.sort(key=lambda x: x['index'])
    
    reversals = []
    for i in range(len(extrema)):
        extremum = extrema[i]
        start_idx = extremum['index']
        end_idx = len(prices) - 1
        
        if end_idx - start_idx < 60:
            continue
        
        segment_prices = prices[start_idx:end_idx + 1]
        amplitude = (segment_prices.max() - segment_prices.min()) * 10000
        
        if amplitude < min_amplitude_pips:
            continue
        
        duration_seconds = (timestamps[end_idx] - timestamps[start_idx]).total_seconds()
        duration_hours = duration_seconds / 3600.0
        
        price_start = prices[start_idx]
        price_end = prices[end_idx]
        
        if extremum['type'] == 'HIGH' and price_end < price_start:
            reversal_type = 'HIGH_TO_LOW'
        elif extremum['type'] == 'LOW' and price_end > price_start:
            reversal_type = 'LOW_TO_HIGH'
        else:
            continue
        
        t = np.arange(len(segment_prices))
        slope, intercept, r_value, _, _ = linregress(t, segment_prices)
        r_squared = r_value ** 2
        
        reversals.append({
            'type': reversal_type,
            'index': start_idx,
            'extremum_type': extremum['type'],
            'time': extremum['timestamp'],
            'price': extremum['price'],
            'amplitude_pips': amplitude,
            'duration_hours': duration_hours,
            'r2': r_squared
        })
    
    return reversals

# ============================================================================
# CHARGER DONNÉES 11 SEPTEMBRE
# ============================================================================

print("="*80)
print("ÉTAPE 1 : CHARGEMENT PRIX 11 SEPTEMBRE")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Charger 30 jours avant
lookback_start = REF_CLUSTER_TIME - timedelta(days=30)

df_prices = conn.execute("""
    SELECT datetime, close, high, low
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime < ?
    ORDER BY datetime
""", [str(lookback_start), str(REF_CLUSTER_TIME)]).df()

conn.close()

df_prices['datetime'] = pd.to_datetime(df_prices['datetime'], utc=True).dt.tz_convert(TZ_BERN)
df_prices.set_index('datetime', inplace=True)

print(f"✅ {len(df_prices):,} prix chargés")
print(f"   Période : {df_prices.index[0].strftime('%Y-%m-%d %H:%M')} → {df_prices.index[-1].strftime('%Y-%m-%d %H:%M')}")
print()

# ============================================================================
# DÉTECTER TOUTES INVERSIONS
# ============================================================================

print("="*80)
print("ÉTAPE 2 : DÉTECTION INVERSIONS (window=240)")
print("="*80)
print()

prices = df_prices['close'].values
timestamps = df_prices.index.tolist()

reversals = detect_trend_reversals(prices, timestamps, window=240, min_amplitude_pips=30)

print(f"✅ {len(reversals)} inversions détectées")
print()

# Afficher TOUTES les inversions
print("📋 TOUTES LES INVERSIONS DÉTECTÉES :")
print()

for i, rev in enumerate(reversals, 1):
    time_str = rev['time'].strftime('%Y-%m-%d %H:%M')
    
    # Calculer distance avec référence Session 107
    time_diff = abs((rev['time'] - REF_INVERSION_TIME).total_seconds() / 3600)
    r2_diff = abs(rev['r2'] - REF_R2)
    dur_diff = abs(rev['duration_hours'] - REF_DURATION)
    
    # Match avec référence ?
    is_match = (time_diff < 6 and dur_diff < 10)
    marker = " ← MATCH SESSION 107 ?" if is_match else ""
    
    print(f"   {i:2d}. {time_str} - {rev['extremum_type']:5s} ({rev['type']})")
    print(f"       R²={rev['r2']:.4f}, dur={rev['duration_hours']:.1f}h, amp={rev['amplitude_pips']:.1f}pips")
    print(f"       Écart réf: Δtime={time_diff:.1f}h, ΔR²={r2_diff:.4f}, Δdur={dur_diff:.1f}h{marker}")
    print()

# ============================================================================
# ANALYSER DERNIÈRE INVERSION (ce que mon script prend)
# ============================================================================

print("="*80)
print("ÉTAPE 3 : DERNIÈRE INVERSION (ce que mon script utilise)")
print("="*80)
print()

if reversals:
    last = reversals[-1]
    print(f"📊 DERNIÈRE inversion :")
    print(f"   Time     : {last['time'].strftime('%Y-%m-%d %H:%M')} Bern")
    print(f"   Type     : {last['type']}")
    print(f"   R²       : {last['r2']:.4f}")
    print(f"   Durée    : {last['duration_hours']:.1f}h")
    print(f"   Amplitude: {last['amplitude_pips']:.1f} pips")
    print()
    
    # Comparer avec référence
    time_diff = (last['time'] - REF_INVERSION_TIME).total_seconds() / 3600
    print(f"📊 Comparaison Session 107 :")
    print(f"   Écart temps : {time_diff:.1f}h")
    print(f"   Écart R²    : {last['r2'] - REF_R2:+.4f}")
    print(f"   Écart durée : {last['duration_hours'] - REF_DURATION:+.1f}h")
    print()

# ============================================================================
# VÉRIFIER INVERSION SPÉCIFIQUE SESSION 107
# ============================================================================

print("="*80)
print("ÉTAPE 4 : VÉRIFIER INVERSION SESSION 107 (09/09 08:00)")
print("="*80)
print()

# Chercher inversion proche 09/09 08:00
target_inversions = [
    r for r in reversals 
    if abs((r['time'] - REF_INVERSION_TIME).total_seconds() / 3600) < 6
]

if target_inversions:
    print(f"✅ {len(target_inversions)} inversion(s) proche(s) 09/09 08:00 :")
    print()
    
    for inv in target_inversions:
        print(f"   Time : {inv['time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Type : {inv['type']}")
        print(f"   R²   : {inv['r2']:.4f} (ref: {REF_R2:.4f})")
        print(f"   Dur  : {inv['duration_hours']:.1f}h (ref: {REF_DURATION:.1f}h)")
        print()
        
        # Si pas dernière, pourquoi ?
        is_last = (inv == reversals[-1])
        if not is_last:
            print(f"   ⚠️  Ce n'est PAS la dernière inversion !")
            print(f"      → Inversions plus récentes détectées après")
            print()
else:
    print("❌ Aucune inversion détectée proche 09/09 08:00")
    print()
    
    # Chercher pic manuel autour 09/09 08:00
    print("🔍 Recherche manuelle du pic 09/09 08:00 :")
    search_start = REF_INVERSION_TIME - timedelta(hours=2)
    search_end = REF_INVERSION_TIME + timedelta(hours=2)
    
    window_prices = df_prices[(df_prices.index >= search_start) & (df_prices.index <= search_end)]
    
    if len(window_prices) > 0:
        peak_idx = window_prices['high'].idxmax()
        peak_price = window_prices.loc[peak_idx, 'high']
        
        print(f"   Peak trouvé : {peak_idx.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Prix        : {peak_price:.5f}")
        print()
        
        # Vérifier si détecté comme swing high
        prices_array = df_prices['high'].values
        peak_pos = df_prices.index.get_loc(peak_idx)
        
        swing_highs = detect_swing_highs(prices_array, window=240)
        
        if peak_pos in swing_highs:
            print("   ✅ Peak détecté comme swing high")
        else:
            print("   ❌ Peak NON détecté comme swing high (window 240 trop petit ?)")
            print()
            
            # Tester avec window plus petit
            for test_window in [120, 180, 240, 360, 480]:
                swing_highs_test = detect_swing_highs(prices_array, window=test_window)
                if peak_pos in swing_highs_test:
                    print(f"      ✅ Détecté avec window={test_window} min")
                    break

# ============================================================================
# RÉSUMÉ
# ============================================================================

print()
print("="*80)
print("DIAGNOSTIC")
print("="*80)
print()

if target_inversions:
    inv = target_inversions[0]
    if inv == reversals[-1]:
        print("✅ Inversion Session 107 EST la dernière inversion détectée")
        print()
        if abs(inv['r2'] - REF_R2) < 0.1:
            print("✅ R² cohérent avec Session 107")
        else:
            print(f"⚠️  R² différent : {inv['r2']:.4f} vs {REF_R2:.4f}")
            print("   → Peut-être méthode calcul différente ?")
    else:
        print("⚠️  Inversion Session 107 existe MAIS n'est PAS la dernière")
        print()
        print("   RAISON : Inversions plus récentes détectées après 09/09")
        print()
        print("   OPTIONS :")
        print("   A) Filtrer inversions trop récentes (< 24h avant cluster)")
        print("   B) Utiliser inversion avec meilleur R² (pas forcément dernière)")
        print("   C) Critères additionnels (durée min, amplitude min)")
else:
    print("❌ Inversion Session 107 NON détectée")
    print()
    print("   RAISONS POSSIBLES :")
    print("   1. Window 240 min trop court pour ce pic")
    print("   2. Amplitude < 30 pips sur segment détecté")
    print("   3. Pic pas assez marqué localement")
    print()
    print("   SOLUTIONS :")
    print("   A) Tester différents windows (120, 360, 480 min)")
    print("   B) Réduire seuil amplitude")
    print("   C) Validation manuelle cas référence")

print()
print("="*80)
print("DEBUG TERMINÉ")
print("="*80)
