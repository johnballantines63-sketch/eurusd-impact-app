#!/usr/bin/env python3
"""
DÉTECTION INVERSIONS DE TENDANCE - SESSION 103
==============================================

Objectif : Dans une fenêtre 72h, identifier la DERNIÈRE inversion majeure
qui marque le début de la tendance actuelle menant à l'événement.

Méthode :
1. Détecter tous les extrema (pics et creux)
2. Identifier les inversions (HIGH→LOW ou LOW→HIGH)
3. Filtrer inversions majeures (amplitude significative)
4. Prendre la dernière inversion avant événement
5. Mesurer tendance depuis ce point d'inversion
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
print("DÉTECTION INVERSIONS DE TENDANCE - CAS 11.09.2025")
print("=" * 80)

# ============================================================================
# FONCTIONS DÉTECTION EXTREMA
# ============================================================================

def detect_swing_highs(prices, window=240, threshold=0.0001):
    """Détecte swing highs (pics locaux)"""
    swing_highs = []
    
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        
        if center > max(left.max(), right.max()) + threshold:
            swing_highs.append(i)
    
    return swing_highs


def detect_swing_lows(prices, window=240, threshold=0.0001):
    """Détecte swing lows (creux locaux)"""
    swing_lows = []
    
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        
        if center < min(left.min(), right.min()) - threshold:
            swing_lows.append(i)
    
    return swing_lows


# ============================================================================
# FONCTION DÉTECTION INVERSIONS
# ============================================================================

def detect_trend_reversals(prices, timestamps, window=240, min_amplitude_pips=30):
    """
    Détecte les inversions de tendance majeures
    
    Une inversion = sequence HIGH→LOW ou LOW→HIGH avec amplitude significative
    
    Returns:
        list: [
            {
                'type': 'HIGH_TO_LOW' ou 'LOW_TO_HIGH',
                'reversal_point_idx': int,
                'reversal_point_type': 'HIGH' ou 'LOW',
                'reversal_time': datetime,
                'reversal_price': float,
                'amplitude_pips': float (depuis inversion jusqu'à fin),
                'duration_hours': float (depuis inversion jusqu'à fin)
            }
        ]
    """
    
    # Détecter tous les extrema
    swing_highs = detect_swing_highs(prices, window)
    swing_lows = detect_swing_lows(prices, window)
    
    # Combiner et trier par ordre chronologique
    extrema = []
    
    for idx in swing_highs:
        extrema.append({
            'type': 'HIGH',
            'index': idx,
            'price': prices[idx],
            'timestamp': timestamps[idx] if idx < len(timestamps) else None
        })
    
    for idx in swing_lows:
        extrema.append({
            'type': 'LOW',
            'index': idx,
            'price': prices[idx],
            'timestamp': timestamps[idx] if idx < len(timestamps) else None
        })
    
    # Trier chronologiquement
    extrema.sort(key=lambda x: x['index'])
    
    if len(extrema) < 2:
        return []
    
    # Identifier inversions
    reversals = []
    
    for i in range(len(extrema)):
        extremum = extrema[i]
        
        # Calculer tendance depuis cet extremum jusqu'à fin
        start_idx = extremum['index']
        end_idx = len(prices) - 1
        
        if end_idx - start_idx < 60:  # Au moins 1h de données après
            continue
        
        segment_prices = prices[start_idx:end_idx + 1]
        amplitude = (segment_prices.max() - segment_prices.min()) * 10000
        
        # Filtrer amplitude trop faible
        if amplitude < min_amplitude_pips:
            continue
        
        # Durée
        if start_idx < len(timestamps) and end_idx < len(timestamps):
            duration_seconds = (timestamps[end_idx] - timestamps[start_idx]).total_seconds()
            duration_hours = duration_seconds / 3600.0
        else:
            duration_hours = (end_idx - start_idx) / 60.0
        
        # Direction depuis cet extremum
        price_start = prices[start_idx]
        price_end = prices[end_idx]
        
        if extremum['type'] == 'HIGH' and price_end < price_start:
            reversal_type = 'HIGH_TO_LOW'  # Pic → Baisse
        elif extremum['type'] == 'LOW' and price_end > price_start:
            reversal_type = 'LOW_TO_HIGH'  # Creux → Montée
        else:
            continue  # Pas une vraie inversion
        
        # R² de la tendance
        t = np.arange(len(segment_prices))
        slope, intercept, r_value, _, _ = linregress(t, segment_prices)
        r_squared = r_value ** 2
        
        reversals.append({
            'type': reversal_type,
            'reversal_point_idx': start_idx,
            'reversal_point_type': extremum['type'],
            'reversal_time': extremum['timestamp'],
            'reversal_price': extremum['price'],
            'amplitude_pips': amplitude,
            'duration_hours': duration_hours,
            'r_squared': r_squared,
            'price_end': price_end
        })
    
    return reversals


# ============================================================================
# TEST CAS 11.09.2025
# ============================================================================

# Cas référence
event_time_utc = datetime(2025, 9, 11, 12, 30)
start_time = event_time_utc - timedelta(hours=72)

# Cible MT5
target_reversal_time = datetime(2025, 9, 9, 6, 0)  # Pic 9/09 08:00 Bern
target_reversal_type = 'HIGH_TO_LOW'
target_amplitude = 95  # pips
target_duration = 54   # heures

print(f"\n🎯 CIBLE MT5 :")
print(f"   Point inversion   : Pic 9/09/2025 08:00 Bern (06:00 UTC)")
print(f"   Type inversion    : HIGH_TO_LOW (pic → baisse)")
print(f"   Prix pic          : ~1.1778")
print(f"   Amplitude tendance: ~95-100 pips")
print(f"   Durée tendance    : ~54 heures")

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

df_prices = conn.execute(query, [start_time, event_time_utc]).fetchdf()
conn.close()

prices = df_prices['close'].values
timestamps = pd.to_datetime(df_prices['datetime']).tolist()

print(f"\n✅ Chargé {len(df_prices)} points prix")

# ============================================================================
# TEST DIFFÉRENTS WINDOWS
# ============================================================================

windows_to_test = [240, 480, 720, 960, 1440, 1800, 2160, 2880]

print("\n" + "=" * 80)
print("DÉTECTION INVERSIONS POUR DIFFÉRENTS WINDOWS")
print("=" * 80)

best_match = None
best_score = 999999

for window in windows_to_test:
    window_hours = window / 60
    
    print(f"\n{'='*80}")
    print(f"WINDOW = {window} minutes ({window_hours:.1f} heures)")
    print(f"{'='*80}")
    
    # Détecter inversions
    reversals = detect_trend_reversals(prices, timestamps, window=window, min_amplitude_pips=30)
    
    print(f"\n✅ Détecté {len(reversals)} inversions majeures :\n")
    
    if len(reversals) == 0:
        print("   ⚠️  Aucune inversion détectée")
        continue
    
    # Afficher toutes les inversions
    for i, rev in enumerate(reversals, 1):
        print(f"   {i}. {rev['type']} à {rev['reversal_time'].strftime('%Y-%m-%d %H:%M') if rev['reversal_time'] else 'N/A'}")
        print(f"      Prix: {rev['reversal_price']:.4f}")
        print(f"      Amplitude: {rev['amplitude_pips']:.1f} pips")
        print(f"      Durée: {rev['duration_hours']:.1f}h")
        print(f"      R²: {rev['r_squared']:.3f}")
        print()
    
    # Prendre la DERNIÈRE inversion (la plus proche de l'événement)
    last_reversal = reversals[-1]
    
    print(f"   🎯 DERNIÈRE INVERSION (tendance actuelle) :")
    print(f"      Type: {last_reversal['type']}")
    print(f"      Temps: {last_reversal['reversal_time'].strftime('%Y-%m-%d %H:%M') if last_reversal['reversal_time'] else 'N/A'}")
    print(f"      Prix: {last_reversal['reversal_price']:.4f}")
    print(f"      Amplitude: {last_reversal['amplitude_pips']:.1f} pips")
    print(f"      Durée: {last_reversal['duration_hours']:.1f}h")
    print(f"      R²: {last_reversal['r_squared']:.3f}")
    
    # Comparer avec cible MT5
    if last_reversal['reversal_time']:
        time_diff = abs((last_reversal['reversal_time'] - target_reversal_time).total_seconds() / 3600)
        amp_diff = abs(last_reversal['amplitude_pips'] - target_amplitude)
        dur_diff = abs(last_reversal['duration_hours'] - target_duration)
        type_match = last_reversal['type'] == target_reversal_type
        
        # Score match
        score = time_diff + (amp_diff / 10) + (dur_diff / 10)
        if not type_match:
            score += 1000
        
        print(f"\n   📊 Comparaison cible MT5 :")
        print(f"      Type match: {'✅' if type_match else '❌'}")
        print(f"      Écart temps: {time_diff:.1f}h")
        print(f"      Écart amplitude: {amp_diff:.1f} pips")
        print(f"      Écart durée: {dur_diff:.1f}h")
        print(f"      Score match: {score:.1f}")
        
        # Garder meilleur
        if score < best_score:
            best_score = score
            best_match = {
                'window': window,
                'reversal': last_reversal,
                'score': score,
                'time_diff': time_diff,
                'amp_diff': amp_diff,
                'type_match': type_match
            }

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("\n" + "=" * 80)
print("🏆 MEILLEUR RÉSULTAT")
print("=" * 80)

if best_match:
    print(f"\n   Window optimal: {best_match['window']} minutes ({best_match['window']/60:.1f}h)")
    print(f"\n   Point d'inversion détecté:")
    print(f"   ├─ Type: {best_match['reversal']['type']}")
    print(f"   ├─ Temps: {best_match['reversal']['reversal_time'].strftime('%Y-%m-%d %H:%M')}")
    print(f"   ├─ Prix: {best_match['reversal']['reversal_price']:.4f}")
    print(f"   ├─ Amplitude tendance: {best_match['reversal']['amplitude_pips']:.1f} pips")
    print(f"   ├─ Durée tendance: {best_match['reversal']['duration_hours']:.1f}h")
    print(f"   └─ R²: {best_match['reversal']['r_squared']:.3f}")
    
    print(f"\n   Qualité détection:")
    print(f"   ├─ Type correct: {'✅' if best_match['type_match'] else '❌'}")
    print(f"   ├─ Écart temps: {best_match['time_diff']:.1f}h")
    print(f"   ├─ Écart amplitude: {best_match['amp_diff']:.1f} pips")
    print(f"   └─ Score: {best_match['score']:.1f}")
    
    # Décision
    print(f"\n" + "=" * 80)
    print("DÉCISION")
    print("=" * 80)
    
    if best_match['type_match'] and best_match['time_diff'] < 6 and best_match['amp_diff'] < 20:
        print("\n✅✅ INVERSION CORRECTEMENT DÉTECTÉE !")
        print(f"\n   Recommandation:")
        print(f"   1. Utiliser méthode 'détection inversions' avec window={best_match['window']}")
        print(f"   2. Intégrer dans detect_trend_extremum.py")
        print(f"   3. Relancer calibration")
        
    elif best_match['type_match'] and best_match['amp_diff'] < 30:
        print("\n✅ DÉTECTION ACCEPTABLE")
        print(f"\n   Window={best_match['window']} donne résultats corrects")
        print(f"   Tester en calibration")
        
    else:
        print("\n⚠️  DÉTECTION IMPARFAITE")
        print(f"\n   Meilleurs résultats mais insuffisants")
        print(f"   Options:")
        print(f"   1. Affiner critères inversions (amplitude min, durée min)")
        print(f"   2. Gold standard manuel")
        print(f"   3. Accepter amp constant 1.2")

else:
    print("\n❌ Aucune inversion détectée sur aucun window")

print("\n" + "=" * 80)
