"""
DÉTECTION TENDANCE PROPRE - SESSION 102
========================================

Fonction pour identifier et mesurer PROPREMENT une tendance :
- Début de la tendance (breakpoint)
- Fin de la tendance (événement)
- Durée PROPRE (heures)
- Amplitude PROPRE (pips)
- Direction (UP/DOWN)
- R² de la tendance identifiée

Méthode : Piecewise regression + rolling R²
"""

import numpy as np
from scipy.stats import linregress

def detect_trend_proper(prices, timestamps):
    """
    Détecte tendance dominante et mesure durée + amplitude propres
    
    Args:
        prices: array de prix (close)
        timestamps: array de timestamps correspondants
        
    Returns:
        dict: {
            'start_idx': int,          # Index début tendance
            'end_idx': int,            # Index fin tendance (dernier)
            'duration_hours': float,   # Durée PROPRE
            'amplitude_pips': float,   # Amplitude PROPRE
            'direction': str,          # 'UP', 'DOWN', 'FLAT'
            'r_squared': float,        # R² de la tendance
            'slope_pips_hour': float   # Pente en pips/heure
        }
    """
    
    if len(prices) < 10:
        return {
            'start_idx': 0,
            'end_idx': len(prices) - 1,
            'duration_hours': 0.0,
            'amplitude_pips': 0.0,
            'direction': 'FLAT',
            'r_squared': 0.0,
            'slope_pips_hour': 0.0
        }
    
    # ========================================================================
    # MÉTHODE 1 : Rolling R² pour identifier fenêtre optimale
    # ========================================================================
    
    best_r2 = 0.0
    best_start = 0
    best_end = len(prices) - 1
    best_slope = 0.0
    
    # Tester fenêtres de différentes tailles (minimum 12h = 720 minutes)
    min_window = max(720, len(prices) // 6)  # Au moins 12h ou 1/6 de dataset
    
    # Scanner fenêtres
    for window_size in range(min_window, len(prices) + 1, 60):  # Par incrément 1h
        
        # Fenêtre se terminant à la fin (avant événement)
        end_idx = len(prices) - 1
        start_idx = max(0, end_idx - window_size)
        
        if end_idx - start_idx < min_window:
            continue
        
        # Extraire segment
        segment_prices = prices[start_idx:end_idx + 1]
        
        if len(segment_prices) < 10:
            continue
        
        # Régression linéaire
        t = np.arange(len(segment_prices))
        slope, intercept, r_value, p_value, std_err = linregress(t, segment_prices)
        r_squared = r_value ** 2
        
        # Garder si meilleur R²
        if r_squared > best_r2:
            best_r2 = r_squared
            best_start = start_idx
            best_end = end_idx
            best_slope = slope
    
    # ========================================================================
    # MÉTHODE 2 : Si R² faible partout, détecter breakpoint
    # ========================================================================
    
    if best_r2 < 0.3:
        # Pas de tendance claire sur aucune fenêtre
        # Essayer de détecter breakpoint (changement régime)
        
        breakpoint_idx = detect_breakpoint(prices)
        
        if breakpoint_idx is not None and breakpoint_idx > 0:
            # Recalculer depuis breakpoint
            start_idx = breakpoint_idx
            end_idx = len(prices) - 1
            
            segment_prices = prices[start_idx:end_idx + 1]
            
            if len(segment_prices) >= 10:
                t = np.arange(len(segment_prices))
                slope, intercept, r_value, p_value, std_err = linregress(t, segment_prices)
                r_squared = r_value ** 2
                
                # Utiliser si R² amélioré
                if r_squared > best_r2:
                    best_r2 = r_squared
                    best_start = start_idx
                    best_end = end_idx
                    best_slope = slope
    
    # ========================================================================
    # CALCUL MÉTRIQUES FINALES
    # ========================================================================
    
    # Durée en heures
    if len(timestamps) > best_end and best_start < len(timestamps):
        duration_seconds = (timestamps[best_end] - timestamps[best_start]).total_seconds()
        duration_hours = duration_seconds / 3600.0
    else:
        duration_hours = (best_end - best_start) / 60.0  # Approximation si timestamps manquants
    
    # Amplitude PROPRE (prix fin - prix début de la tendance)
    price_start = prices[best_start]
    price_end = prices[best_end]
    amplitude_pips = abs(price_end - price_start) * 10000
    
    # Direction
    if best_slope > 0:
        direction = 'UP'
    elif best_slope < 0:
        direction = 'DOWN'
    else:
        direction = 'FLAT'
    
    # Slope en pips/heure
    slope_pips_hour = best_slope * 10000 * 60  # slope par minute → pips/heure
    
    return {
        'start_idx': best_start,
        'end_idx': best_end,
        'duration_hours': duration_hours,
        'amplitude_pips': amplitude_pips,
        'direction': direction,
        'r_squared': best_r2,
        'slope_pips_hour': slope_pips_hour
    }


def detect_breakpoint(prices, min_segment=120):
    """
    Détecte breakpoint (changement de régime) dans série de prix
    
    Méthode : Variance minimale sur segments
    
    Args:
        prices: array de prix
        min_segment: taille minimale segment (minutes)
        
    Returns:
        int: index du breakpoint, ou None si pas trouvé
    """
    
    if len(prices) < 2 * min_segment:
        return None
    
    best_breakpoint = None
    best_score = float('inf')
    
    # Tester différents points de coupure
    for i in range(min_segment, len(prices) - min_segment, 30):  # Par pas de 30min
        
        # Segment 1 : avant breakpoint
        seg1 = prices[:i]
        
        # Segment 2 : après breakpoint
        seg2 = prices[i:]
        
        # Régression sur chaque segment
        t1 = np.arange(len(seg1))
        t2 = np.arange(len(seg2))
        
        try:
            slope1, intercept1, r1, p1, err1 = linregress(t1, seg1)
            slope2, intercept2, r2, p2, err2 = linregress(t2, seg2)
            
            # Résidus
            pred1 = slope1 * t1 + intercept1
            pred2 = slope2 * t2 + intercept2
            
            residuals1 = seg1 - pred1
            residuals2 = seg2 - pred2
            
            # Score = variance totale résidus
            score = np.var(residuals1) + np.var(residuals2)
            
            # Bonus si pentes très différentes (vraiment 2 régimes différents)
            if abs(slope1 - slope2) > 0.0001:  # Différence significative
                score *= 0.8  # Favoriser
            
            if score < best_score:
                best_score = score
                best_breakpoint = i
                
        except:
            continue
    
    # Vérifier que breakpoint trouvé améliore vraiment
    if best_breakpoint is not None:
        # Comparer variance avec vs sans breakpoint
        
        # Sans breakpoint (une seule régression)
        t_full = np.arange(len(prices))
        slope_full, intercept_full, _, _, _ = linregress(t_full, prices)
        pred_full = slope_full * t_full + intercept_full
        var_without = np.var(prices - pred_full)
        
        # Avec breakpoint
        var_with = best_score
        
        # Amélioration significative ?
        if var_with < var_without * 0.8:  # Au moins 20% mieux
            return best_breakpoint
    
    return None


def calculate_trend_strength_score(trend_info):
    """
    Calcule score force tendance (0-100)
    
    Args:
        trend_info: dict retourné par detect_trend_proper
        
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
    # Amplitude forte > 100 pips
    if amplitude >= 100:
        amplitude_score = 30
    elif amplitude >= 50:
        amplitude_score = (amplitude / 100) * 30
    else:
        amplitude_score = (amplitude / 50) * 15
    
    total_score = r2_score + duration_score + amplitude_score
    
    return min(total_score, 100.0)


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTS DÉTECTION TENDANCE PROPRE")
    print("=" * 80)
    
    from datetime import datetime, timedelta
    
    # Test 1 : Tendance forte 48h
    print("\n📊 TEST 1 : Tendance haussière forte 48h")
    print("-" * 80)
    
    n_points = 72 * 60  # 72h en minutes
    t = np.arange(n_points)
    
    # Prix : flat 24h puis tendance haussière 48h
    prices = np.ones(n_points) * 1.1000
    prices[24*60:] = 1.1000 + (t[24*60:] - 24*60) * 0.0001  # Montée progressive
    
    timestamps = [datetime.now() - timedelta(minutes=n_points-i) for i in range(n_points)]
    
    result = detect_trend_proper(prices, timestamps)
    
    print(f"Début tendance    : {result['start_idx']/60:.1f}h (attendu ~24h)")
    print(f"Durée tendance    : {result['duration_hours']:.1f}h (attendu ~48h)")
    print(f"Amplitude         : {result['amplitude_pips']:.1f} pips")
    print(f"Direction         : {result['direction']} (attendu UP)")
    print(f"R²                : {result['r_squared']:.3f}")
    print(f"Score force       : {calculate_trend_strength_score(result):.1f}/100")
    
    # Test 2 : Pas de tendance (bruit)
    print("\n📊 TEST 2 : Pas de tendance (bruit)")
    print("-" * 80)
    
    np.random.seed(42)
    prices_noise = 1.1000 + np.random.randn(n_points) * 0.0001
    
    result2 = detect_trend_proper(prices_noise, timestamps)
    
    print(f"Durée tendance    : {result2['duration_hours']:.1f}h")
    print(f"Amplitude         : {result2['amplitude_pips']:.1f} pips")
    print(f"Direction         : {result2['direction']}")
    print(f"R²                : {result2['r_squared']:.3f} (attendu < 0.3)")
    print(f"Score force       : {calculate_trend_strength_score(result2):.1f}/100")
    
    # Test 3 : Tendance courte forte (12h)
    print("\n📊 TEST 3 : Tendance courte mais forte (12h)")
    print("-" * 80)
    
    prices3 = np.ones(n_points) * 1.1000
    prices3[-12*60:] = 1.1000 + (t[-12*60:] - t[-12*60]) * 0.0005  # Montée rapide 12h
    
    result3 = detect_trend_proper(prices3, timestamps)
    
    print(f"Début tendance    : {result3['start_idx']/60:.1f}h avant fin")
    print(f"Durée tendance    : {result3['duration_hours']:.1f}h (attendu ~12h)")
    print(f"Amplitude         : {result3['amplitude_pips']:.1f} pips")
    print(f"R²                : {result3['r_squared']:.3f}")
    print(f"Score force       : {calculate_trend_strength_score(result3):.1f}/100")
    
    print("\n" + "=" * 80)
    print("TESTS TERMINÉS")
    print("=" * 80)
