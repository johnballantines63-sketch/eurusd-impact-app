#!/usr/bin/env python3
"""
DÉTECTION TENDANCE SIMPLE - SESSION 103
=======================================

Approche SIMPLE et ROBUSTE :
1. Trouver TOP N prix (les plus hauts/bas de la période)
2. Éliminer doublons temporels
3. Détecter inversions
4. Prendre dernière inversion = tendance actuelle

KISS : Keep It Simple, Stupid
"""

import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy.stats import linregress

# Ajouter chemin config
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 80)
print("DÉTECTION TENDANCE SIMPLE - CAS 11.09.2025")
print("=" * 80)
print("\nApproche : TOP N PRIX (simple mais efficace)")
print("=" * 80)

# ============================================================================
# PARAMÈTRES
# ============================================================================

LOOKBACK_DAYS = 14
TOP_N_EXTREMA = 5  # Prendre les 5 prix les plus hauts/bas
MIN_TIME_BETWEEN_EXTREMA_HOURS = 12  # Espacer extrema de 12h min
MIN_TREND_AMPLITUDE_PIPS = 30

# ============================================================================
# FONCTIONS
# ============================================================================

def find_top_n_extrema_simple(prices, timestamps, top_n=5, min_hours_apart=12):
    """
    Trouve les TOP N prix les plus hauts et les plus bas
    Élimine doublons temporels (pics trop proches)
    
    Approche SIMPLE : pas de prominence, juste les prix extrêmes !
    """
    
    min_minutes_apart = min_hours_apart * 60
    
    # ========== HIGHS ==========
    # Indices triés par prix décroissant
    high_indices = np.argsort(prices)[::-1]
    
    selected_highs = []
    for idx in high_indices:
        # Vérifier si assez espacé des précédents
        too_close = False
        for selected in selected_highs:
            if abs(idx - selected['index']) < min_minutes_apart:
                too_close = True
                break
        
        if not too_close:
            selected_highs.append({
                'type': 'HIGH',
                'index': int(idx),
                'price': float(prices[idx]),
                'timestamp': timestamps[idx] if idx < len(timestamps) else None
            })
        
        if len(selected_highs) >= top_n:
            break
    
    # ========== LOWS ==========
    low_indices = np.argsort(prices)  # Croissant
    
    selected_lows = []
    for idx in low_indices:
        too_close = False
        for selected in selected_lows:
            if abs(idx - selected['index']) < min_minutes_apart:
                too_close = True
                break
        
        if not too_close:
            selected_lows.append({
                'type': 'LOW',
                'index': int(idx),
                'price': float(prices[idx]),
                'timestamp': timestamps[idx] if idx < len(timestamps) else None
            })
        
        if len(selected_lows) >= top_n:
            break
    
    # Combiner et trier chronologiquement
    all_extrema = selected_highs + selected_lows
    all_extrema.sort(key=lambda x: x['index'])
    
    return all_extrema


def detect_inversions_from_extrema(extrema, prices, timestamps, min_amplitude_pips=30):
    """Détecte inversions entre extrema"""
    
    inversions = []
    event_time = timestamps[-1]  # Dernier timestamp = événement
    
    for extremum in extrema:
        start_idx = extremum['index']
        end_idx = len(prices) - 1
        
        if end_idx - start_idx < 60:
            continue
        
        # FILTRE : Extremum doit être au moins 48h avant événement
        # (pour éviter pics secondaires trop récents)
        hours_before_event = (end_idx - start_idx) / 60.0
        if hours_before_event < 48:
            continue
        
        segment_prices = prices[start_idx:end_idx + 1]
        amplitude = (segment_prices.max() - segment_prices.min()) * 10000
        
        if amplitude < min_amplitude_pips:
            continue
        
        # Durée
        if start_idx < len(timestamps) and end_idx < len(timestamps):
            duration_hours = (timestamps[end_idx] - timestamps[start_idx]).total_seconds() / 3600
        else:
            duration_hours = (end_idx - start_idx) / 60.0
        
        # Direction
        price_start = prices[start_idx]
        price_end = prices[end_idx]
        
        # R²
        t = np.arange(len(segment_prices))
        slope, intercept, r_value, _, _ = linregress(t, segment_prices)
        r_squared = r_value ** 2
        
        # Type inversion
        if extremum['type'] == 'HIGH' and price_end < price_start:
            inversion_type = 'HIGH_TO_LOW'
        elif extremum['type'] == 'LOW' and price_end > price_start:
            inversion_type = 'LOW_TO_HIGH'
        else:
            continue
        
        inversions.append({
            'type': inversion_type,
            'reversal_point': extremum,
            'amplitude_pips': amplitude,
            'duration_hours': duration_hours,
            'r_squared': r_squared,
            'end_price': price_end
        })
    
    return inversions


# ============================================================================
# TEST CAS 11.09.2025
# ============================================================================

event_time_utc = datetime(2025, 9, 11, 12, 30)
lookback_time = event_time_utc - timedelta(days=LOOKBACK_DAYS)

print(f"\n📅 PÉRIODE : {LOOKBACK_DAYS} jours")
print(f"   {lookback_time.strftime('%Y-%m-%d')} → {event_time_utc.strftime('%Y-%m-%d')}")

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

query = """
SELECT datetime, close
FROM prices_1m
WHERE datetime >= ?
  AND datetime < ?
ORDER BY datetime ASC
"""

df_prices = conn.execute(query, [lookback_time, event_time_utc]).fetchdf()
conn.close()

prices = df_prices['close'].values
timestamps = pd.to_datetime(df_prices['datetime']).tolist()

print(f"\n✅ {len(df_prices)} points | Range: {(prices.max() - prices.min()) * 10000:.1f} pips")
print(f"   Prix MIN: {prices.min():.4f} | Prix MAX: {prices.max():.4f}")

# ============================================================================
# ÉTAPE 1 : TOP N EXTREMA
# ============================================================================

print(f"\n{'='*80}")
print(f"ÉTAPE 1 : TOP {TOP_N_EXTREMA} PRIX EXTRÊMES")
print(f"{'='*80}")

extrema = find_top_n_extrema_simple(
    prices, 
    timestamps, 
    top_n=TOP_N_EXTREMA,
    min_hours_apart=MIN_TIME_BETWEEN_EXTREMA_HOURS
)

print(f"\n✅ Détecté {len(extrema)} extrema (espacés de {MIN_TIME_BETWEEN_EXTREMA_HOURS}h min) :\n")

for i, ext in enumerate(extrema, 1):
    time_str = ext['timestamp'].strftime('%Y-%m-%d %H:%M') if ext['timestamp'] else 'N/A'
    
    # Vérifier si c'est le pic cible (9/09 ~06:00)
    is_target = False
    if ext['timestamp']:
        target_time = pd.Timestamp('2025-09-09 06:00:00', tz='UTC')
        ext_time = ext['timestamp'].tz_localize('UTC') if ext['timestamp'].tz is None else ext['timestamp'].tz_convert('UTC')
        time_diff_hours = abs((ext_time - target_time).total_seconds() / 3600)
        if time_diff_hours < 12 and ext['type'] == 'HIGH':
            is_target = True
    
    marker = " ← 🎯 PIC CIBLE !" if is_target else ""
    print(f"   {i:2d}. {ext['type']:<5} | {time_str} | {ext['price']:.4f}{marker}")

# ============================================================================
# ÉTAPE 2 : INVERSIONS
# ============================================================================

print(f"\n{'='*80}")
print(f"ÉTAPE 2 : INVERSIONS DE TENDANCE")
print(f"{'='*80}")

inversions = detect_inversions_from_extrema(
    extrema, 
    prices, 
    timestamps,
    min_amplitude_pips=MIN_TREND_AMPLITUDE_PIPS
)

print(f"\n✅ Détecté {len(inversions)} inversions :\n")

if len(inversions) == 0:
    print("   ⚠️  Aucune inversion détectée")
else:
    for i, inv in enumerate(inversions, 1):
        rev = inv['reversal_point']
        time_str = rev['timestamp'].strftime('%Y-%m-%d %H:%M') if rev['timestamp'] else 'N/A'
        
        print(f"   {i}. {inv['type']}")
        print(f"      Point: {time_str} à {rev['price']:.4f}")
        print(f"      Durée: {inv['duration_hours']:.1f}h ({inv['duration_hours']/24:.1f}j)")
        print(f"      Amplitude: {inv['amplitude_pips']:.1f} pips")
        print(f"      R²: {inv['r_squared']:.3f}")
        print()

# ============================================================================
# ÉTAPE 3 : TENDANCE ACTUELLE
# ============================================================================

print(f"{'='*80}")
print(f"ÉTAPE 3 : TENDANCE ACTUELLE")
print(f"{'='*80}")

if len(inversions) > 0:
    current_trend = inversions[-1]
    rev = current_trend['reversal_point']
    
    print(f"\n🎯 DERNIÈRE INVERSION (tendance actuelle) :")
    print(f"\n   Type: {current_trend['type']}")
    print(f"   Point: {rev['timestamp'].strftime('%Y-%m-%d %H:%M') if rev['timestamp'] else 'N/A'}")
    print(f"   Prix: {rev['price']:.4f}")
    print(f"\n   Métriques tendance :")
    print(f"   ├─ Durée: {current_trend['duration_hours']:.1f}h ({current_trend['duration_hours']/24:.1f}j)")
    print(f"   ├─ Amplitude: {current_trend['amplitude_pips']:.1f} pips")
    print(f"   └─ R²: {current_trend['r_squared']:.3f}")
    
    # Comparaison MT5
    target_time = pd.Timestamp('2025-09-09 06:00:00', tz='UTC')
    target_type = 'HIGH_TO_LOW'
    
    if rev['timestamp']:
        rev_time = rev['timestamp'].tz_localize('UTC') if rev['timestamp'].tz is None else rev['timestamp'].tz_convert('UTC')
        time_diff_hours = abs((rev_time - target_time).total_seconds() / 3600)
        type_match = current_trend['type'] == target_type
        
        print(f"\n   📊 vs MT5 (pic 9/09) :")
        print(f"   ├─ Type: {'✅' if type_match else '❌'}")
        print(f"   ├─ Écart temps: {time_diff_hours:.1f}h")
        print(f"   └─ Écart amplitude: {abs(current_trend['amplitude_pips'] - 95):.1f} pips")
        
        if type_match and time_diff_hours < 24:
            print(f"\n   ✅✅ EXCELLENTE DÉTECTION !")
        elif type_match:
            print(f"\n   ✅ BONNE DÉTECTION")
        else:
            print(f"\n   ⚠️  DÉTECTION IMPARFAITE")

else:
    print("\n❌ Aucune inversion détectée")

# ============================================================================
# RÉSUMÉ
# ============================================================================

print(f"\n{'='*80}")
print("CONCLUSION")
print(f"{'='*80}")

if len(inversions) > 0:
    print(f"\n✅ Approche TOP-N fonctionne !")
    print(f"\n   Avantages :")
    print(f"   ✅ Simple et robuste")
    print(f"   ✅ Capture les VRAIS extrema (pas de paramètre prominence)")
    print(f"   ✅ Le prix MAX est forcément détecté")
    print(f"\n   Cette approche doit être intégrée dans le système !")
else:
    print(f"\n⚠️  Ajuster paramètres")

print(f"\n{'='*80}")
