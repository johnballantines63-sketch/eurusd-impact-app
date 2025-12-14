"""
MODULE CALCUL DURÉE TENDANCE

Date : 29 octobre 2025 - Session 92.12
Objectif : Identifier depuis combien de temps la tendance actuelle est en place

MÉTHODE :
=========
Fenêtres glissantes de tailles croissantes (3h, 6h, 12h, 18h, 24h)
→ Trouver la plus longue fenêtre avec R² ≥ 0.10 et même direction

INTUITION ANDRÉ :
==================
"pondérer la tendance haussière ou baissière avec sa durée 
plus elle est longue plus l'impact de la tendance sera forte sur une inversion"

Score tendance = direction × (duree/24) × r_squared
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import pandas as pd
import numpy as np


def calculate_regression_on_window(prices: np.ndarray) -> Tuple[str, float, float]:
    """
    Calcule régression linéaire sur une fenêtre de prix
    
    Args:
        prices: Array numpy des prix (ordre chronologique)
    
    Returns:
        Tuple (tendance: str, pente: float, r_squared: float)
    """
    if len(prices) < 60:  # Minimum 1h de données
        return "NEUTRE", 0.0, 0.0
    
    # Temps (1, 2, 3, ..., n)
    t = np.arange(1, len(prices) + 1)
    
    # Moyennes
    t_mean = np.mean(t)
    y_mean = np.mean(prices)
    
    # Calcul pente
    numerator = np.sum((t - t_mean) * (prices - y_mean))
    denominator = np.sum((t - t_mean) ** 2)
    
    if denominator == 0:
        return "NEUTRE", 0.0, 0.0
    
    slope = numerator / denominator
    
    # Prédictions
    y_pred = slope * t + (y_mean - slope * t_mean)
    
    # R²
    ss_tot = np.sum((prices - y_mean) ** 2)
    ss_res = np.sum((prices - y_pred) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    # Détermination tendance
    r2_threshold = 0.10
    
    if r_squared < r2_threshold:
        trend = "NEUTRE"
    elif slope < -0.000001:
        trend = "BAISSIER"
    elif slope > 0.000001:
        trend = "HAUSSIER"
    else:
        trend = "NEUTRE"
    
    return trend, slope, r_squared


def find_trend_duration(prices_df: pd.DataFrame, target_trend: str) -> Dict:
    """
    Trouve depuis combien de temps la tendance actuelle est en place
    
    STRATÉGIE :
    - Tester fenêtres glissantes : 3h, 6h, 12h, 18h, 24h
    - Trouver la plus longue fenêtre avec R² ≥ 0.10 et même direction
    - Si aucune fenêtre significative → durée = temps depuis dernier pic
    
    Args:
        prices_df: DataFrame prix 24h
        target_trend: Tendance à chercher ('HAUSSIER', 'BAISSIER', 'NEUTRE')
    
    Returns:
        Dict avec:
            - duration_hours: Durée tendance en heures
            - duration_minutes: Durée en minutes
            - method: Méthode utilisée ('regression_window' ou 'last_peak')
            - confidence: Niveau confiance (R² si regression, 0 si peak)
    """
    prices = prices_df['close'].values
    total_minutes = len(prices)
    
    print(f"\n🔍 RECHERCHE DURÉE TENDANCE {target_trend} :")
    print(f"   Total données : {total_minutes} minutes ({total_minutes/60:.1f}h)")
    
    # Si tendance NEUTRE → durée = 0
    if target_trend == "NEUTRE":
        print(f"   → Tendance NEUTRE → Durée = 0h")
        return {
            'duration_hours': 0.0,
            'duration_minutes': 0,
            'method': 'neutral',
            'confidence': 0.0
        }
    
    # Fenêtres à tester (en minutes)
    windows_minutes = [
        24 * 60,  # 24h
        18 * 60,  # 18h
        12 * 60,  # 12h
        6 * 60,   # 6h
        3 * 60    # 3h
    ]
    
    # Chercher la plus longue fenêtre avec même tendance
    longest_duration = 0
    best_r_squared = 0.0
    
    for window_min in windows_minutes:
        if window_min > total_minutes:
            continue
        
        # Extraire fenêtre (derniers N minutes)
        window_prices = prices[-window_min:]
        
        # Calculer régression
        trend, slope, r_squared = calculate_regression_on_window(window_prices)
        
        window_hours = window_min / 60
        
        print(f"   Fenêtre {window_hours:.0f}h : {trend} (R²={r_squared:.3f}, pente={slope*10000:.2f} pips/min)")
        
        # Vérifier si tendance correspond ET R² significatif
        if trend == target_trend and r_squared >= 0.10:
            longest_duration = window_min
            best_r_squared = r_squared
            print(f"      ✅ Tendance {target_trend} confirmée sur {window_hours:.0f}h")
            break  # On garde la plus longue
        elif trend == target_trend and r_squared < 0.10:
            print(f"      ⚠️  Tendance {target_trend} mais R² < 0.10 (faible)")
        else:
            print(f"      ❌ Tendance différente ou R² trop faible")
    
    # Si aucune fenêtre significative trouvée → méthode fallback
    if longest_duration == 0:
        print(f"\n   ⚠️  Aucune fenêtre significative trouvée")
        print(f"   → Fallback : Calculer depuis dernier pic")
        
        # Trouver dernier pic (HIGH ou LOW)
        if target_trend == "BAISSIER":
            # Chercher dernier HIGH
            last_peak_idx = np.argmax(prices)
            duration_minutes = total_minutes - last_peak_idx
        else:  # HAUSSIER
            # Chercher dernier LOW
            last_peak_idx = np.argmin(prices)
            duration_minutes = total_minutes - last_peak_idx
        
        print(f"   → Dernier pic à t-{duration_minutes} min → Durée = {duration_minutes/60:.1f}h")
        
        return {
            'duration_hours': duration_minutes / 60,
            'duration_minutes': duration_minutes,
            'method': 'last_peak',
            'confidence': 0.0
        }
    
    # Fenêtre significative trouvée
    duration_hours = longest_duration / 60
    print(f"\n   ✅ DURÉE TENDANCE : {duration_hours:.1f}h (R²={best_r_squared:.3f})")
    
    return {
        'duration_hours': duration_hours,
        'duration_minutes': longest_duration,
        'method': 'regression_window',
        'confidence': best_r_squared
    }


def calculate_weighted_trend_score(
    trend: str,
    r_squared: float,
    duration_hours: float
) -> Dict:
    """
    Calcule score tendance pondéré : Direction × Durée × R²
    
    FORMULE ANDRÉ :
    score_tendance = direction × (duree/24) × r_squared
    
    Où :
    - direction : +1.0 (HAUSSIER), -1.0 (BAISSIER), 0.0 (NEUTRE)
    - duree : Heures depuis début tendance (max 24)
    - r_squared : Force statistique tendance
    
    EXEMPLES :
    - Date 11.09 : BAISSIER 22.9h, R²=0.55 → score = -0.52
    - Date 01.15 : HAUSSIER 5.3h, R²=0.70 → score = +0.15
    
    Args:
        trend: 'HAUSSIER', 'BAISSIER', 'NEUTRE'
        r_squared: Coefficient détermination
        duration_hours: Durée tendance en heures
    
    Returns:
        Dict avec:
            - trend: Tendance
            - direction: +1/-1/0
            - duration_hours: Durée
            - r_squared: R²
            - duration_normalized: Durée normalisée (0-1)
            - score: Score pondéré (-1.0 à +1.0)
    """
    # Direction numérique
    if trend == 'HAUSSIER':
        direction = +1.0
    elif trend == 'BAISSIER':
        direction = -1.0
    else:
        direction = 0.0
    
    # Normaliser durée sur 24h (plafonner à 24)
    duration_normalized = min(duration_hours, 24.0) / 24.0
    
    # Score pondéré
    score = direction * duration_normalized * r_squared
    
    print(f"\n📊 SCORE TENDANCE PONDÉRÉ :")
    print(f"   Tendance : {trend}")
    print(f"   Direction : {direction:+.1f}")
    print(f"   Durée : {duration_hours:.1f}h → Normalisé : {duration_normalized:.3f}")
    print(f"   R² : {r_squared:.3f}")
    print(f"   SCORE = {direction:+.1f} × {duration_normalized:.3f} × {r_squared:.3f} = {score:+.3f}")
    
    return {
        'trend': trend,
        'direction': direction,
        'duration_hours': duration_hours,
        'r_squared': r_squared,
        'duration_normalized': duration_normalized,
        'score': score
    }


def test_duration_calculation():
    """
    Test unitaire - Cas 11.09.2025
    
    Attendu :
    - Tendance : BAISSIER
    - Durée : ~22.9h
    - R² : ~0.55
    - Score : -0.52
    """
    print("=" * 60)
    print("TEST CALCUL DURÉE - CAS 11.09.2025")
    print("=" * 60)
    
    # Simuler prix baissiers 24h (1440 minutes)
    np.random.seed(42)
    t = np.arange(1440)
    
    # Tendance baissière avec bruit
    prices = 1.17289 - 0.00003 * t + np.random.normal(0, 0.00005, len(t))
    
    df = pd.DataFrame({'close': prices})
    
    # Calculer tendance globale
    trend_global, slope, r2 = calculate_regression_on_window(prices)
    print(f"\nTendance globale 24h : {trend_global} (R²={r2:.3f})")
    
    # Trouver durée
    duration_info = find_trend_duration(df, trend_global)
    
    # Score pondéré
    score_info = calculate_weighted_trend_score(
        trend_global,
        r2,
        duration_info['duration_hours']
    )
    
    print(f"\n✅ TEST TERMINÉ")
    print(f"   Score attendu : -0.52")
    print(f"   Score obtenu : {score_info['score']:+.3f}")
    
    return score_info


if __name__ == "__main__":
    # Exécuter test
    result = test_duration_calculation()
