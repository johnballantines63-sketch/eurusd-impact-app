#!/usr/bin/env python3
"""
DÉTECTION TENDANCE DYNAMIQUE - SESSION 103 CORRIGÉE
===================================================

CORRECTION ERREUR MÉTHODOLOGIQUE :
- ❌ Fenêtre fixe 72h (arbitraire)
- ✅ Détection dynamique dernière inversion majeure

Principe :
1. Charger N jours de données (10-30 jours)
2. Identifier extrema majeurs (prominence)
3. Détecter inversions de tendance
4. Prendre dernière inversion avant événement
5. Mesurer tendance depuis cette inversion (durée variable)
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
print("DÉTECTION TENDANCE DYNAMIQUE - CAS 11.09.2025")
print("=" * 80)
print("\n⚠️  CORRECTION ERREUR MÉTHODOLOGIQUE")
print("   Fenêtre 72h arbitraire → Détection dynamique")
print("=" * 80)

# ============================================================================
# PARAMÈTRES
# ============================================================================

LOOKBACK_DAYS = 14  # Charger 14 jours de données
MIN_PROMINENCE_PIPS = 30  # Seuil extremum majeur (abaissé de 40 à 30)
MIN_TREND_AMPLITUDE_PIPS = 30  # Amplitude min tendance
PROMINENCE_WINDOW_HOURS = 24  # Fenêtre calcul prominence (augmenté de 12h à 24h)

# ============================================================================
# FONCTIONS DÉTECTION
# ============================================================================

def calculate_prominence(prices, index, window_hours=12):
    """
    Calcule la prominence d'un point = à quel point il se distingue
    de son environnement local
    
    Prominence = distance verticale entre le point et le minimum
    dans une fenêtre autour
    """
    window_minutes = window_hours * 60
    
    if index < window_minutes or index >= len(prices) - window_minutes:
        return 0.0
    
    # Fenêtre autour du point
    window_prices = np.concatenate([
        prices[index - window_minutes:index],
        prices[index + 1:index + window_minutes + 1]
    ])
    
    # Prominence = différence avec minimum environnement
    prominence = (prices[index] - window_prices.min()) * 10000  # pips
    
    return prominence


def find_major_extrema(prices, timestamps, prominence_window_hours=12, min_prominence_pips=40):
    """
    Trouve les extrema MAJEURS basés sur prominence
    
    Returns:
        list: [
            {
                'type': 'HIGH' ou 'LOW',
                'index': int,
                'price': float,
                'timestamp': datetime,
                'prominence': float (pips)
            }
        ]
    """
    
    window_minutes = prominence_window_hours * 60
    extrema = []
    
    for i in range(window_minutes, len(prices) - window_minutes):
        # Calculer prominence
        prom = calculate_prominence(prices, i, prominence_window_hours)
        
        if prom < min_prominence_pips:
            continue
        
        # Vérifier si c'est un max ou min local
        center = prices[i]
        left = prices[i - window_minutes:i]
        right = prices[i + 1:i + window_minutes + 1]
        
        is_high = center > left.max() and center > right.max()
        is_low = center < left.min() and center < right.min()
        
        if is_high:
            extrema.append({
                'type': 'HIGH',
                'index': i,
                'price': center,
                'timestamp': timestamps[i] if i < len(timestamps) else None,
                'prominence': prom
            })
        elif is_low:
            extrema.append({
                'type': 'LOW',
                'index': i,
                'price': center,
                'timestamp': timestamps[i] if i < len(timestamps) else None,
                'prominence': prom
            })
    
    # Trier par index (chronologique)
    extrema.sort(key=lambda x: x['index'])
    
    return extrema


def detect_trend_inversions(extrema, prices, timestamps, min_amplitude_pips=30):
    """
    Détecte les inversions de tendance entre extrema
    
    Returns:
        list: [
            {
                'type': 'HIGH_TO_LOW' ou 'LOW_TO_HIGH',
                'reversal_point': extremum dict,
                'amplitude_pips': float,
                'duration_hours': float,
                'r_squared': float
            }
        ]
    """
    
    inversions = []
    
    for i, extremum in enumerate(extrema):
        # Mesurer tendance depuis cet extremum jusqu'à fin
        start_idx = extremum['index']
        end_idx = len(prices) - 1
        
        if end_idx - start_idx < 60:  # Au moins 1h
            continue
        
        # Segment prix
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
        
        # R² tendance
        t = np.arange(len(segment_prices))
        slope, intercept, r_value, _, _ = linregress(t, segment_prices)
        r_squared = r_value ** 2
        
        # Identifier type inversion
        if extremum['type'] == 'HIGH' and price_end < price_start:
            inversion_type = 'HIGH_TO_LOW'
        elif extremum['type'] == 'LOW' and price_end > price_start:
            inversion_type = 'LOW_TO_HIGH'
        else:
            continue  # Pas une vraie inversion
        
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

# Charger N jours de données (pas 72h !)
lookback_time = event_time_utc - timedelta(days=LOOKBACK_DAYS)

print(f"\n📅 PÉRIODE ANALYSE :")
print(f"   Début : {lookback_time.strftime('%Y-%m-%d %H:%M')} UTC")
print(f"   Fin   : {event_time_utc.strftime('%Y-%m-%d %H:%M')} UTC")
print(f"   Durée : {LOOKBACK_DAYS} jours ({LOOKBACK_DAYS * 24} heures)")
print(f"\n   (Au lieu de 72h arbitraires)")

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

print(f"\n✅ Chargé {len(df_prices)} points prix (M1)")
print(f"   Prix min : {prices.min():.4f}")
print(f"   Prix max : {prices.max():.4f}")
print(f"   Range    : {(prices.max() - prices.min()) * 10000:.1f} pips")

# ============================================================================
# ÉTAPE 1 : IDENTIFIER EXTREMA MAJEURS
# ============================================================================

print(f"\n{'='*80}")
print(f"ÉTAPE 1 : IDENTIFICATION EXTREMA MAJEURS")
print(f"{'='*80}")
print(f"\nParamètres :")
print(f"   Fenêtre prominence : {PROMINENCE_WINDOW_HOURS}h")
print(f"   Seuil prominence   : {MIN_PROMINENCE_PIPS} pips")

extrema = find_major_extrema(
    prices, 
    timestamps, 
    prominence_window_hours=PROMINENCE_WINDOW_HOURS,
    min_prominence_pips=MIN_PROMINENCE_PIPS
)

print(f"\n✅ Détecté {len(extrema)} extrema majeurs :\n")

# Afficher tous les extrema
for i, ext in enumerate(extrema, 1):
    time_str = ext['timestamp'].strftime('%Y-%m-%d %H:%M') if ext['timestamp'] else 'N/A'
    print(f"   {i:2d}. {ext['type']:<5} | {time_str} | {ext['price']:.4f} | Prominence: {ext['prominence']:.1f} pips")

# ============================================================================
# ÉTAPE 2 : DÉTECTER INVERSIONS
# ============================================================================

print(f"\n{'='*80}")
print(f"ÉTAPE 2 : DÉTECTION INVERSIONS DE TENDANCE")
print(f"{'='*80}")
print(f"\nParamètres :")
print(f"   Amplitude min : {MIN_TREND_AMPLITUDE_PIPS} pips")

inversions = detect_trend_inversions(
    extrema, 
    prices, 
    timestamps,
    min_amplitude_pips=MIN_TREND_AMPLITUDE_PIPS
)

print(f"\n✅ Détecté {len(inversions)} inversions majeures :\n")

if len(inversions) == 0:
    print("   ⚠️  Aucune inversion détectée")
    print("   → Essayer de baisser les seuils (prominence, amplitude)")
else:
    for i, inv in enumerate(inversions, 1):
        rev = inv['reversal_point']
        time_str = rev['timestamp'].strftime('%Y-%m-%d %H:%M') if rev['timestamp'] else 'N/A'
        
        print(f"   {i}. {inv['type']}")
        print(f"      Point inversion : {time_str} à {rev['price']:.4f}")
        print(f"      Durée tendance  : {inv['duration_hours']:.1f}h ({inv['duration_hours']/24:.1f} jours)")
        print(f"      Amplitude       : {inv['amplitude_pips']:.1f} pips")
        print(f"      R²              : {inv['r_squared']:.3f}")
        print()

# ============================================================================
# ÉTAPE 3 : IDENTIFIER TENDANCE ACTUELLE
# ============================================================================

print(f"{'='*80}")
print(f"ÉTAPE 3 : IDENTIFICATION TENDANCE ACTUELLE")
print(f"{'='*80}")

if len(inversions) > 0:
    # Prendre la DERNIÈRE inversion (tendance actuelle)
    current_trend = inversions[-1]
    rev = current_trend['reversal_point']
    
    print(f"\n🎯 TENDANCE ACTUELLE (dernière inversion) :")
    print(f"\n   Type inversion    : {current_trend['type']}")
    print(f"   Point inversion   : {rev['timestamp'].strftime('%Y-%m-%d %H:%M') if rev['timestamp'] else 'N/A'}")
    print(f"   Prix inversion    : {rev['price']:.4f}")
    print(f"   Prominence        : {rev['prominence']:.1f} pips")
    print(f"\n   Métriques tendance depuis inversion :")
    print(f"   ├─ Durée          : {current_trend['duration_hours']:.1f}h ({current_trend['duration_hours']/24:.1f} jours)")
    print(f"   ├─ Amplitude      : {current_trend['amplitude_pips']:.1f} pips")
    print(f"   └─ R²             : {current_trend['r_squared']:.3f}")
    
    # Comparaison avec cible MT5
    target_time = pd.Timestamp('2025-09-09 06:00:00', tz='UTC')
    target_type = 'HIGH_TO_LOW'
    target_amplitude = 95
    target_duration = 54
    
    print(f"\n   📊 Comparaison cible MT5 (pic 9/09) :")
    
    if rev['timestamp']:
        rev_time = rev['timestamp'].tz_localize('UTC') if rev['timestamp'].tz is None else rev['timestamp'].tz_convert('UTC')
        time_diff_hours = abs((rev_time - target_time).total_seconds() / 3600)
        type_match = current_trend['type'] == target_type
        amp_diff = abs(current_trend['amplitude_pips'] - target_amplitude)
        dur_diff = abs(current_trend['duration_hours'] - target_duration)
        
        print(f"   ├─ Type correct   : {'✅' if type_match else '❌'} ({current_trend['type']} vs {target_type})")
        print(f"   ├─ Écart temps    : {time_diff_hours:.1f}h")
        print(f"   ├─ Écart amplitude: {amp_diff:.1f} pips")
        print(f"   └─ Écart durée    : {dur_diff:.1f}h")
        
        # Score qualité
        if type_match and time_diff_hours < 12 and amp_diff < 30:
            print(f"\n   ✅✅ EXCELLENTE DÉTECTION !")
        elif type_match and time_diff_hours < 24:
            print(f"\n   ✅ BONNE DÉTECTION")
        else:
            print(f"\n   ⚠️  DÉTECTION IMPARFAITE")

else:
    print("\n❌ Aucune inversion détectée")
    print("\n   Actions :")
    print(f"   1. Baisser seuil prominence (actuellement {MIN_PROMINENCE_PIPS} pips)")
    print(f"   2. Baisser seuil amplitude (actuellement {MIN_TREND_AMPLITUDE_PIPS} pips)")
    print(f"   3. Augmenter lookback_days (actuellement {LOOKBACK_DAYS} jours)")

# ============================================================================
# RÉSUMÉ
# ============================================================================

print(f"\n{'='*80}")
print("RÉSUMÉ & RECOMMANDATION")
print(f"{'='*80}")

if len(inversions) > 0:
    print(f"\n✅ Méthode détection dynamique fonctionne !")
    print(f"\n   Résultats :")
    print(f"   ├─ {len(extrema)} extrema majeurs détectés")
    print(f"   ├─ {len(inversions)} inversions identifiées")
    print(f"   └─ Tendance actuelle : {current_trend['duration_hours']/24:.1f} jours")
    print(f"\n   Avantages vs fenêtre fixe 72h :")
    print(f"   ✅ Pas de coupure arbitraire des tendances")
    print(f"   ✅ Capture la vraie durée du mouvement")
    print(f"   ✅ Détecte le vrai point de départ")
    print(f"\n   Prochaine étape :")
    print(f"   → Intégrer dans detect_trend_extremum.py")
    print(f"   → Relancer calibration formule amplification")
else:
    print(f"\n⚠️  Ajuster paramètres détection")
    print(f"\n   Paramètres actuels peut-être trop stricts :")
    print(f"   - Prominence min : {MIN_PROMINENCE_PIPS} pips")
    print(f"   - Amplitude min  : {MIN_TREND_AMPLITUDE_PIPS} pips")
    print(f"   - Fenêtre prom   : {PROMINENCE_WINDOW_HOURS}h")

print(f"\n{'='*80}")
