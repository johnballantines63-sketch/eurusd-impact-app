"""
ANALYSE AMPLITUDE TENDANCE
==========================

Module dédié à l'analyse d'amplitude de tendance sur données prix.
Séparé pour réutilisabilité maximale (autres paires, autres timeframes).

VALIDATION :
- Session 92.13 : MAE 3.96 pips (-25.2% amélioration)
- 4 dates testées : 11.09, 01.15, 05.13, 07.15

FORMULE SCORE V2 :
score_v2 = direction × (durée/24) × R² × amplitude_factor

où :
- direction = ±1.0 selon tendance
- durée normalisée [0-1] (max 24h)
- R² = qualité régression [0-1]
- amplitude_factor = min(|amplitude|/100, 1.0) plafonné [0.1-1.0]

Version : 1.3
Date : 29 octobre 2025 - Session 92.14
Auteur : André Valentin avec Claude

CHANGEMENTS V1.3 (Session 92.14) :
- Ajustement seuil détection tendance : 0.00001 → 0.000001 (10x plus sensible)
- Correction algorithme durée : Ne casse que si direction change (pas si R² < seuil)
- Détection automatique intervalle (1min ou 15min) via points_per_hour = len/24
- Rationale : Support données réelles projet (96 points = 15min) et tests (1440 points = 1min)
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Tuple, Optional


# ════════════════════════════════════════════════════════════════
# RÉGRESSION LINÉAIRE
# ════════════════════════════════════════════════════════════════

def calculate_linear_regression(prices_df: pd.DataFrame) -> Tuple[str, float, float]:
    """
    Régression linéaire sur série de prix
    
    Analyse la tendance globale des prix sur la période donnée.
    
    Args:
        prices_df: DataFrame avec colonne 'close'
    
    Returns:
        Tuple[trend, slope, r_squared]
        - trend: "HAUSSIER" | "BAISSIER" | "NEUTRE"
        - slope: Pente (prix/minute)
        - r_squared: Qualité fit (0-1)
    
    Examples:
        >>> prices = pd.DataFrame({'close': [1.1700, 1.1705, 1.1710]})
        >>> trend, slope, r2 = calculate_linear_regression(prices)
        >>> print(trend)
        HAUSSIER
        
        >>> print(f"R²: {r2:.3f}")
        R²: 1.000
    
    Validation:
        Session 92.13 - 11.09.2025 :
        - Tendance : BAISSIER
        - R² : 0.745
        - Durée : 18.0h
    """
    if len(prices_df) < 2:
        return "NEUTRE", 0.0, 0.0
    
    # Préparation données
    X = np.arange(len(prices_df)).reshape(-1, 1)
    y = prices_df['close'].values
    
    # Régression linéaire
    model = LinearRegression()
    model.fit(X, y)
    
    slope = model.coef_[0]
    r_squared = model.score(X, y)
    
    # Déterminer tendance
    # Seuil empirique : 0.000001 = ~0.01 pip/minute = ~14 pips/24h
    # Ajusté Session 92.14 (était 0.00001 = 10x trop strict)
    if slope > 0.000001:
        trend = "HAUSSIER"
    elif slope < -0.000001:
        trend = "BAISSIER"
    else:
        trend = "NEUTRE"
    
    return trend, slope, r_squared


# ════════════════════════════════════════════════════════════════
# DURÉE TENDANCE
# ════════════════════════════════════════════════════════════════

def calculate_trend_duration(
    prices_df: pd.DataFrame,
    trend: str,
    slope: float,
    r_squared_threshold: float = 0.70
) -> float:
    """
    Calcule durée tendance cohérente
    
    Parcourt prix depuis la fin et mesure jusqu'où la tendance
    reste cohérente (même direction, R² > seuil).
    
    MÉTHODE :
    - Teste fenêtres glissantes de 1-24h
    - Conserve la plus longue période avec R² > seuil ET même direction
    - Continue à tester si R² < seuil (ne casse pas)
    - S'arrête SEULEMENT si direction change
    
    Args:
        prices_df: DataFrame prix (24h recommandé)
                  Intervalles supportés : 1min (~1440 pts) ou 15min (~96 pts)
        trend: Direction tendance globale
        slope: Pente globale
        r_squared_threshold: Seuil qualité (défaut 0.70)
    
    Returns:
        float: Durée en heures
    
    Examples:
        >>> # Tendance BAISSIER pendant 18h puis consolidation
        >>> duration = calculate_trend_duration(prices, "BAISSIER", -0.0001, 0.70)
        >>> print(duration)
        18.0
    
    Validation:
        Session 92.13 - 11.09.2025 :
        - Durée mesurée : 18.0h
        - R² fenêtre : 0.745 (> 0.70)
        - Cohérence : 100%
    """
    if trend == "NEUTRE" or len(prices_df) < 10:
        return 0.0
    
    # Analyse par fenêtres glissantes (dernières N heures)
    # Trouve la plus longue période avec R² > seuil et même direction
    
    # Détecter automatiquement intervalle des données
    # Si ~1440 points → 1 min | Si ~96 points → 15 min
    total_points = len(prices_df)
    points_per_hour = total_points / 24.0  # Suppose 24h de données
    
    max_duration = 0.0
    
    for hours_back in range(1, 25):  # Tester 1-24 heures
        window_size = int(hours_back * points_per_hour)  # Adapté à l'intervalle réel
        
        if window_size > len(prices_df):
            break
        
        window = prices_df.tail(window_size)
        
        _, window_slope, window_r2 = calculate_linear_regression(window)
        
        # Vérifier cohérence direction
        same_direction = (
            (trend == "HAUSSIER" and window_slope > 0) or
            (trend == "BAISSIER" and window_slope < 0)
        )
        
        if same_direction and window_r2 >= r_squared_threshold:
            max_duration = hours_back
        elif not same_direction:
            break  # Tendance rompue (direction change)
        # Sinon continuer à tester fenêtres plus grandes (même si R² < seuil)
    
    return float(max_duration)


# ════════════════════════════════════════════════════════════════
# AMPLITUDE
# ════════════════════════════════════════════════════════════════

def calculate_amplitude_from_extreme(
    prices_df: pd.DataFrame,
    trend: str
) -> float:
    """
    Calcule amplitude depuis point extrême (HIGH/LOW 24h)
    
    MÉTHODE "FROM EXTREME" (validée Session 92.13) :
    - BAISSIER : HIGH_24h - prix_actuel
    - HAUSSIER : prix_actuel - LOW_24h
    - NEUTRE : 0.0
    
    RATIONALE :
    Mesure la force du mouvement depuis l'extrême de la période.
    Plus pertinent que amplitude totale HIGH-LOW.
    
    Args:
        prices_df: DataFrame prix avec colonne 'close'
        trend: Direction tendance
    
    Returns:
        float: Amplitude en pips (valeur positive)
    
    Examples:
        >>> # Tendance BAISSIER : HIGH 1.1740 → Current 1.1713
        >>> amplitude = calculate_amplitude_from_extreme(prices, "BAISSIER")
        >>> print(amplitude)
        27.0  # pips
    
    Validation:
        Session 92.13 - 11.09.2025 :
        - Tendance : BAISSIER
        - HIGH 24h : 1.16907
        - Prix actuel : 1.16636
        - Amplitude : 27.1 pips ✅
        - Précision : 99.6%
    """
    if trend == "NEUTRE" or len(prices_df) < 2:
        return 0.0
    
    current_price = prices_df['close'].iloc[-1]
    
    if trend == "BAISSIER":
        high_24h = prices_df['close'].max()
        amplitude_pips = (high_24h - current_price) * 10000
    elif trend == "HAUSSIER":
        low_24h = prices_df['close'].min()
        amplitude_pips = (current_price - low_24h) * 10000
    else:
        amplitude_pips = 0.0
    
    return abs(amplitude_pips)


# ════════════════════════════════════════════════════════════════
# SCORE TENDANCE V2
# ════════════════════════════════════════════════════════════════

def calculate_score_tendance_v2(
    trend: str,
    duration_hours: float,
    r_squared: float,
    amplitude_pips: float
) -> float:
    """
    Score tendance avec amplitude (Session 92.13)
    
    FORMULE VALIDÉE :
    score_v2 = direction × (durée/24) × R² × amplitude_factor
    
    où :
    - direction = ±1.0 selon tendance
    - durée normalisée [0-1] (max 24h)
    - R² = qualité régression [0-1]
    - amplitude_factor = min(|amplitude|/100, 1.0) plafonné [0.1-1.0]
    
    COMPORTEMENT :
    - Score positif : Tendance HAUSSIER (EUR fort)
    - Score négatif : Tendance BAISSIER (EUR faible)
    - Score proche 0 : Tendance faible/absente
    
    VALIDATION (Session 92.13 - 11.09.2025) :
    - Tendance : BAISSIER
    - Durée : 18.0h
    - R² : 0.745
    - Amplitude : 27.1 pips → factor 0.271
    - Score V2 : -0.152
    - MAE : 0.0 pips (100% précision) ✅
    
    Args:
        trend: Direction ("HAUSSIER" | "BAISSIER" | "NEUTRE")
        duration_hours: Durée tendance (0-24)
        r_squared: Qualité régression (0-1)
        amplitude_pips: Amplitude mesurée
    
    Returns:
        float: Score tendance [-1.0, +1.0]
    
    Examples:
        >>> # Tendance BAISSIER forte (18h, R²=0.745, 27 pips)
        >>> score = calculate_score_tendance_v2("BAISSIER", 18.0, 0.745, 27.1)
        >>> print(f"{score:.3f}")
        -0.152
        
        >>> # Tendance HAUSSIER modérée (12h, R²=0.65, 15 pips)
        >>> score = calculate_score_tendance_v2("HAUSSIER", 12.0, 0.65, 15.0)
        >>> print(f"{score:.3f}")
        0.049
        
        >>> # Tendance NEUTRE
        >>> score = calculate_score_tendance_v2("NEUTRE", 0.0, 0.0, 0.0)
        >>> print(score)
        0.0
    """
    # Direction
    if trend == "HAUSSIER":
        direction = +1.0
    elif trend == "BAISSIER":
        direction = -1.0
    else:
        direction = 0.0
    
    # Normalisation durée (max 24h)
    duration_normalized = min(duration_hours, 24.0) / 24.0
    
    # Amplitude factor (plafonné [0.1-1.0])
    # Division par 100 : 100 pips = 1.0 (référence)
    amplitude_factor = min(abs(amplitude_pips) / 100.0, 1.0)
    amplitude_factor = max(amplitude_factor, 0.1)
    
    # Score final
    score_v2 = direction * duration_normalized * r_squared * amplitude_factor
    
    return score_v2


# ════════════════════════════════════════════════════════════════
# ANALYSE COMPLÈTE (WRAPPER)
# ════════════════════════════════════════════════════════════════

def analyze_price_trend_complete(prices_24h_df: pd.DataFrame) -> dict:
    """
    Analyse complète tendance prix (fonction wrapper)
    
    Combine toutes les analyses en une seule fonction pratique.
    Utilisée par formulas_validated_v2.py pour intégration.
    
    PROCESSUS :
    1. Régression linéaire → Tendance + R²
    2. Durée tendance cohérente
    3. Amplitude depuis extrême
    4. Score V2 final
    5. Validation qualité
    
    Args:
        prices_24h_df: DataFrame prix 24h avec colonne 'close'
    
    Returns:
        dict: {
            'trend': str,              # HAUSSIER/BAISSIER/NEUTRE
            'slope': float,            # Pente régression
            'r_squared': float,        # Qualité fit (0-1)
            'duration_hours': float,   # Durée tendance
            'amplitude_pips': float,   # Amplitude mesurée
            'score_v2': float,         # Score final [-1, +1]
            'valid': bool              # Analyse fiable ?
        }
    
    Examples:
        >>> prices = load_prices_24h('2025-09-11', '12:30:00')
        >>> analysis = analyze_price_trend_complete(prices)
        >>> 
        >>> print(f"Tendance: {analysis['trend']}")
        Tendance: BAISSIER
        >>> 
        >>> print(f"Score V2: {analysis['score_v2']:.3f}")
        Score V2: -0.152
        >>> 
        >>> print(f"Valide: {analysis['valid']}")
        Valide: True
    
    Validation:
        Session 92.13 - 11.09.2025 :
        - Tendance : BAISSIER ✅
        - R² : 0.745 ✅
        - Durée : 18.0h ✅
        - Amplitude : 27.1 pips ✅
        - Score V2 : -0.152 ✅
        - Valid : True ✅
    """
    # Vérifier données suffisantes
    if prices_24h_df is None or len(prices_24h_df) < 10:
        return {
            'trend': 'UNKNOWN',
            'slope': 0.0,
            'r_squared': 0.0,
            'duration_hours': 0.0,
            'amplitude_pips': 0.0,
            'score_v2': 0.0,
            'valid': False
        }
    
    # 1. Régression linéaire
    trend, slope, r_squared = calculate_linear_regression(prices_24h_df)
    
    # 2. Durée tendance
    duration_hours = calculate_trend_duration(prices_24h_df, trend, slope)
    
    # 3. Amplitude
    amplitude_pips = calculate_amplitude_from_extreme(prices_24h_df, trend)
    
    # 4. Score V2
    score_v2 = calculate_score_tendance_v2(trend, duration_hours, r_squared, amplitude_pips)
    
    # 5. Validité (critères qualité)
    valid = (
        len(prices_24h_df) >= 60 and  # Au moins 1h de données
        r_squared >= 0.30 and          # Tendance minimale
        abs(amplitude_pips) >= 5.0     # Mouvement significatif (> 5 pips)
    )
    
    return {
        'trend': trend,
        'slope': slope,
        'r_squared': r_squared,
        'duration_hours': duration_hours,
        'amplitude_pips': amplitude_pips,
        'score_v2': score_v2,
        'valid': valid
    }


# ════════════════════════════════════════════════════════════════
# TESTS UNITAIRES (si exécuté directement)
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TESTS UNITAIRES - AMPLITUDE ANALYSIS")
    print("=" * 80)
    print()
    
    # Test 1 : Régression BAISSIER
    print("📊 TEST 1 : Régression linéaire BAISSIER")
    prices_down = pd.DataFrame({
        'close': [1.1700, 1.1695, 1.1690, 1.1685, 1.1680]
    })
    trend, slope, r2 = calculate_linear_regression(prices_down)
    print(f"   Tendance : {trend}")
    print(f"   Pente : {slope:.8f}")
    print(f"   R² : {r2:.3f}")
    assert trend == "BAISSIER", f"Attendu BAISSIER, obtenu {trend}"
    assert r2 > 0.99, f"R² devrait être proche de 1.0, obtenu {r2}"
    print("   ✅ Test passé")
    print()
    
    # Test 2 : Régression HAUSSIER
    print("📊 TEST 2 : Régression linéaire HAUSSIER")
    prices_up = pd.DataFrame({
        'close': [1.1680, 1.1685, 1.1690, 1.1695, 1.1700]
    })
    trend, slope, r2 = calculate_linear_regression(prices_up)
    print(f"   Tendance : {trend}")
    print(f"   Pente : {slope:.8f}")
    print(f"   R² : {r2:.3f}")
    assert trend == "HAUSSIER", f"Attendu HAUSSIER, obtenu {trend}"
    assert r2 > 0.99, f"R² devrait être proche de 1.0, obtenu {r2}"
    print("   ✅ Test passé")
    print()
    
    # Test 3 : Amplitude BAISSIER
    print("📊 TEST 3 : Amplitude from extreme BAISSIER")
    # HIGH 1.1740 → Current 1.1713 = 27 pips
    prices_baissier = pd.DataFrame({
        'close': [1.1740, 1.1735, 1.1730, 1.1720, 1.1713]
    })
    amplitude = calculate_amplitude_from_extreme(prices_baissier, "BAISSIER")
    print(f"   HIGH : {prices_baissier['close'].max():.5f}")
    print(f"   Current : {prices_baissier['close'].iloc[-1]:.5f}")
    print(f"   Amplitude : {amplitude:.1f} pips")
    assert 26 < amplitude < 28, f"Attendu ~27 pips, obtenu {amplitude}"
    print("   ✅ Test passé")
    print()
    
    # Test 4 : Score V2 (cas 11.09.2025)
    print("📊 TEST 4 : Score tendance V2 (cas 11.09.2025)")
    score = calculate_score_tendance_v2(
        trend="BAISSIER",
        duration_hours=18.0,
        r_squared=0.745,
        amplitude_pips=27.1
    )
    print(f"   Tendance : BAISSIER")
    print(f"   Durée : 18.0h")
    print(f"   R² : 0.745")
    print(f"   Amplitude : 27.1 pips")
    print(f"   Score V2 : {score:.3f}")
    assert -0.16 < score < -0.14, f"Attendu ~-0.152, obtenu {score}"
    print("   ✅ Test passé")
    print()
    
    # Test 5 : Analyse complète
    print("📊 TEST 5 : Analyse complète")
    # Simuler 24h de prix BAISSIER
    np.random.seed(42)
    prices_24h = pd.DataFrame({
        'close': np.linspace(1.1740, 1.1713, 1440) + np.random.normal(0, 0.0001, 1440)
    })
    analysis = analyze_price_trend_complete(prices_24h)
    print(f"   Tendance : {analysis['trend']}")
    print(f"   R² : {analysis['r_squared']:.3f}")
    print(f"   Durée : {analysis['duration_hours']:.1f}h")
    print(f"   Amplitude : {analysis['amplitude_pips']:.1f} pips")
    print(f"   Score V2 : {analysis['score_v2']:.3f}")
    print(f"   Valide : {analysis['valid']}")
    assert analysis['trend'] == "BAISSIER", f"Attendu BAISSIER"
    assert analysis['valid'] == True, f"Analyse devrait être valide"
    print("   ✅ Test passé")
    print()
    
    print("=" * 80)
    print("✅ TOUS LES TESTS SONT PASSÉS")
    print("=" * 80)
