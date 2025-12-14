"""
DÉTECTION TENDANCE AVEC EXTREMA - SESSION 102 CORRIGÉ
======================================================

Méthode corrigée basée sur détection Swing High/Low :
1. Détecter pics et creux majeurs (extrema)
2. Trouver dernier extremum dans 72h
3. Mesurer tendance depuis extremum jusqu'à événement
4. Calculer durée, amplitude et R² PROPRES

Basé sur observation graphique MT5 :
- 11.09.2025 : Pic 9 sept 08:00 → Event 11 sept 14:30
- Durée : ~54h (pas 14h)
- Amplitude : ~83 pips (pas 14 pips)
"""

import numpy as np
from scipy.stats import linregress

def detect_swing_highs(prices, window=20, threshold=0.0001):
    """
    Détecte swing highs (pics locaux)
    
    Args:
        prices: array de prix
        window: fenêtre de comparaison (ex: 20 = 20 bougies de chaque côté)
        threshold: seuil minimum pour être considéré comme pic (en prix)
        
    Returns:
        list: indices des swing highs
    """
    swing_highs = []
    
    for i in range(window, len(prices) - window):
        # Prix central
        center = prices[i]
        
        # Fenêtre gauche et droite
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        
        # C'est un swing high si center est plus haut que tous les voisins
        if center > max(left.max(), right.max()) + threshold:
            swing_highs.append(i)
    
    return swing_highs


def detect_swing_lows(prices, window=20, threshold=0.0001):
    """
    Détecte swing lows (creux locaux)
    
    Args:
        prices: array de prix
        window: fenêtre de comparaison
        threshold: seuil minimum pour être considéré comme creux
        
    Returns:
        list: indices des swing lows
    """
    swing_lows = []
    
    for i in range(window, len(prices) - window):
        # Prix central
        center = prices[i]
        
        # Fenêtre gauche et droite
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        
        # C'est un swing low si center est plus bas que tous les voisins
        if center < min(left.min(), right.min()) - threshold:
            swing_lows.append(i)
    
    return swing_lows


def find_last_major_extremum(prices, timestamps, window=20):
    """
    Trouve le dernier extremum majeur (pic ou creux) avant l'événement
    
    Args:
        prices: array de prix (72h avant événement)
        timestamps: array de timestamps
        window: fenêtre détection swing
        
    Returns:
        dict: {
            'type': 'HIGH' ou 'LOW',
            'index': int,
            'price': float,
            'timestamp': datetime
        }
    """
    
    # Détecter tous les extrema
    swing_highs = detect_swing_highs(prices, window)
    swing_lows = detect_swing_lows(prices, window)
    
    if len(swing_highs) == 0 and len(swing_lows) == 0:
        # Pas d'extremum détecté, utiliser le point le plus extrême
        max_idx = np.argmax(prices)
        min_idx = np.argmin(prices)
        
        # Choisir le plus récent
        if max_idx > min_idx:
            return {
                'type': 'HIGH',
                'index': max_idx,
                'price': prices[max_idx],
                'timestamp': timestamps[max_idx] if max_idx < len(timestamps) else None
            }
        else:
            return {
                'type': 'LOW',
                'index': min_idx,
                'price': prices[min_idx],
                'timestamp': timestamps[min_idx] if min_idx < len(timestamps) else None
            }
    
    # Combiner tous les extrema avec leurs indices
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
    
    # Trier par index (chronologique)
    extrema.sort(key=lambda x: x['index'])
    
    if len(extrema) == 0:
        # Fallback : dernier max ou min
        max_idx = np.argmax(prices)
        min_idx = np.argmin(prices)
        
        if max_idx > min_idx:
            return {
                'type': 'HIGH',
                'index': max_idx,
                'price': prices[max_idx],
                'timestamp': timestamps[max_idx] if max_idx < len(timestamps) else None
            }
        else:
            return {
                'type': 'LOW',
                'index': min_idx,
                'price': prices[min_idx],
                'timestamp': timestamps[min_idx] if min_idx < len(timestamps) else None
            }
    
    # Retourner le dernier extremum (le plus récent avant événement)
    return extrema[-1]


def detect_trend_from_extremum(prices, timestamps, window_swing=20):
    """
    Détecte tendance depuis dernier extremum majeur jusqu'à événement
    
    Méthode corrigée :
    1. Trouve dernier pic/creux dans 72h
    2. Mesure tendance depuis cet extremum jusqu'à fin
    3. Calcule métriques PROPRES
    
    Args:
        prices: array de prix (72h avant événement)
        timestamps: array de timestamps correspondants
        window_swing: fenêtre détection swing (défaut 20 = 20min avec M1)
        
    Returns:
        dict: {
            'start_idx': int,
            'end_idx': int,
            'duration_hours': float,
            'amplitude_pips': float,
            'direction': str,
            'r_squared': float,
            'slope_pips_hour': float,
            'extremum_type': str
        }
    """
    
    if len(prices) < 100:
        return {
            'start_idx': 0,
            'end_idx': len(prices) - 1,
            'duration_hours': 0.0,
            'amplitude_pips': 0.0,
            'direction': 'FLAT',
            'r_squared': 0.0,
            'slope_pips_hour': 0.0,
            'extremum_type': 'NONE'
        }
    
    # 1. Trouver dernier extremum majeur
    extremum = find_last_major_extremum(prices, timestamps, window_swing)
    
    start_idx = extremum['index']
    end_idx = len(prices) - 1
    
    # Vérifier qu'il y a assez de données après extremum
    if end_idx - start_idx < 10:
        # Extremum trop proche de la fin, élargir vers l'arrière
        start_idx = max(0, end_idx - 100)
    
    # 2. Extraire segment depuis extremum
    segment_prices = prices[start_idx:end_idx + 1]
    
    if len(segment_prices) < 3:
        return {
            'start_idx': 0,
            'end_idx': len(prices) - 1,
            'duration_hours': 0.0,
            'amplitude_pips': 0.0,
            'direction': 'FLAT',
            'r_squared': 0.0,
            'slope_pips_hour': 0.0,
            'extremum_type': extremum['type']
        }
    
    # 3. Régression linéaire sur segment
    t = np.arange(len(segment_prices))
    slope, intercept, r_value, p_value, std_err = linregress(t, segment_prices)
    r_squared = r_value ** 2
    
    # 4. Durée en heures
    if len(timestamps) > end_idx and start_idx < len(timestamps):
        duration_seconds = (timestamps[end_idx] - timestamps[start_idx]).total_seconds()
        duration_hours = duration_seconds / 3600.0
    else:
        duration_hours = (end_idx - start_idx) / 60.0  # Approximation M1
    
    # 5. Amplitude PROPRE (max - min sur segment)
    price_start = prices[start_idx]
    price_end = prices[end_idx]
    segment_prices = prices[start_idx:end_idx + 1]
    amplitude_pips = (segment_prices.max() - segment_prices.min()) * 10000
    
    # 6. Direction
    if price_end > price_start:
        direction = 'UP'
    elif price_end < price_start:
        direction = 'DOWN'
    else:
        direction = 'FLAT'
    
    # 7. Slope en pips/heure
    slope_pips_hour = slope * 10000 * 60  # slope par minute → pips/heure
    
    return {
        'start_idx': start_idx,
        'end_idx': end_idx,
        'duration_hours': duration_hours,
        'amplitude_pips': amplitude_pips,
        'direction': direction,
        'r_squared': r_squared,
        'slope_pips_hour': slope_pips_hour,
        'extremum_type': extremum['type']
    }


def calculate_trend_strength_score(trend_info):
    """
    Calcule score force tendance (0-100)
    
    Args:
        trend_info: dict retourné par detect_trend_from_extremum
        
    Returns:
        float: score 0-100
    """
    
    r2 = trend_info['r_squared']
    duration = trend_info['duration_hours']
    amplitude = trend_info['amplitude_pips']
    
    # R² (40% du score)
    r2_score = r2 * 40
    
    # Durée normalisée (30% du score)
    # Durée optimale = 48-60h
    if duration >= 48:
        duration_score = 30
    elif duration >= 24:
        duration_score = (duration / 48) * 30
    else:
        duration_score = (duration / 24) * 15
    
    # Amplitude normalisée (30% du score)
    # Amplitude forte > 80 pips
    if amplitude >= 80:
        amplitude_score = 30
    elif amplitude >= 40:
        amplitude_score = (amplitude / 80) * 30
    else:
        amplitude_score = (amplitude / 40) * 15
    
    total_score = r2_score + duration_score + amplitude_score
    
    return min(total_score, 100.0)


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTS DÉTECTION TENDANCE AVEC EXTREMA")
    print("=" * 80)
    
    from datetime import datetime, timedelta
    
    # Test 1 : Simulation cas 11.09.2025
    print("\n📊 TEST 1 : Simulation 11.09.2025 (pic → baisse)")
    print("-" * 80)
    
    # 72h en minutes
    n_points = 72 * 60
    t = np.arange(n_points)
    
    # Prix : montée progressive, pic à 54h avant fin, puis baisse
    prices = np.ones(n_points) * 1.1600
    
    # Montée jusqu'à pic (18h)
    prices[:18*60] = 1.1600 + (t[:18*60] / (18*60)) * 0.0170  # Monte jusqu'à 1.1770
    
    # Pic à 18h (index 18*60)
    peak_idx = 18 * 60
    
    # Baisse depuis pic (54h restantes)
    prices[peak_idx:] = 1.1770 - ((t[peak_idx:] - peak_idx) / (54*60)) * 0.0083  # Baisse vers 1.1687
    
    timestamps = [datetime.now() - timedelta(minutes=n_points-i) for i in range(n_points)]
    
    result = detect_trend_from_extremum(prices, timestamps, window_swing=20)
    
    print(f"Extremum détecté  : {result['extremum_type']} (attendu HIGH)")
    print(f"Début tendance    : index {result['start_idx']} / {peak_idx} attendu")
    print(f"Durée tendance    : {result['duration_hours']:.1f}h (attendu ~54h)")
    print(f"Amplitude         : {result['amplitude_pips']:.1f} pips (attendu ~83 pips)")
    print(f"Direction         : {result['direction']} (attendu DOWN)")
    print(f"R²                : {result['r_squared']:.3f}")
    print(f"Score force       : {calculate_trend_strength_score(result):.1f}/100")
    
    # Test 2 : Creux puis montée
    print("\n📊 TEST 2 : Creux puis montée")
    print("-" * 80)
    
    prices2 = np.ones(n_points) * 1.1700
    
    # Baisse jusqu'à creux (24h)
    prices2[:24*60] = 1.1700 - (t[:24*60] / (24*60)) * 0.0100  # Baisse jusqu'à 1.1600
    
    # Creux
    trough_idx = 24 * 60
    
    # Montée depuis creux (48h)
    prices2[trough_idx:] = 1.1600 + ((t[trough_idx:] - trough_idx) / (48*60)) * 0.0150  # Monte vers 1.1750
    
    result2 = detect_trend_from_extremum(prices2, timestamps, window_swing=20)
    
    print(f"Extremum détecté  : {result2['extremum_type']} (attendu LOW)")
    print(f"Début tendance    : index {result2['start_idx']} / {trough_idx} attendu")
    print(f"Durée tendance    : {result2['duration_hours']:.1f}h (attendu ~48h)")
    print(f"Amplitude         : {result2['amplitude_pips']:.1f} pips (attendu ~150 pips)")
    print(f"Direction         : {result2['direction']} (attendu UP)")
    print(f"R²                : {result2['r_squared']:.3f}")
    print(f"Score force       : {calculate_trend_strength_score(result2):.1f}/100")
    
    # Test 3 : Pas de tendance claire
    print("\n📊 TEST 3 : Range / Pas de tendance")
    print("-" * 80)
    
    np.random.seed(42)
    prices3 = 1.1650 + np.random.randn(n_points) * 0.0002  # Bruit
    
    result3 = detect_trend_from_extremum(prices3, timestamps, window_swing=20)
    
    print(f"Durée tendance    : {result3['duration_hours']:.1f}h")
    print(f"Amplitude         : {result3['amplitude_pips']:.1f} pips")
    print(f"Direction         : {result3['direction']}")
    print(f"R²                : {result3['r_squared']:.3f} (attendu < 0.3)")
    print(f"Score force       : {calculate_trend_strength_score(result3):.1f}/100")
    
    print("\n" + "=" * 80)
    print("TESTS TERMINÉS")
    print("=" * 80)
