"""
CALIBRATION EMPIRIQUE SCORE PONDÉRÉ - SESSION 92.12

Méthodologie correcte (comme Sessions 51-55) :
1. RÉTRO-INGÉNIERIE sur cas 11.09.2025 (impact réel connu)
2. CORRÉLATION entre facteur correction et score tendance (durée × R²)
3. FORMULE EMPIRIQUE calibrée
4. VALIDATION sur autres dates

Date : 29 octobre 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import duckdb
from pathlib import Path
from typing import Dict, Tuple
import matplotlib.pyplot as plt


# ============================================================================
# PARTIE 1 : FONCTIONS CALCUL SCORE TENDANCE (réutilisation)
# ============================================================================

def calculate_regression_on_window(prices: np.ndarray) -> Tuple[str, float, float]:
    """Régression linéaire sur fenêtre prix"""
    if len(prices) < 60:
        return "NEUTRE", 0.0, 0.0
    
    t = np.arange(1, len(prices) + 1)
    t_mean = np.mean(t)
    y_mean = np.mean(prices)
    
    numerator = np.sum((t - t_mean) * (prices - y_mean))
    denominator = np.sum((t - t_mean) ** 2)
    
    if denominator == 0:
        return "NEUTRE", 0.0, 0.0
    
    slope = numerator / denominator
    y_pred = slope * t + (y_mean - slope * t_mean)
    
    ss_tot = np.sum((prices - y_mean) ** 2)
    ss_res = np.sum((prices - y_pred) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
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
    """Trouve durée tendance actuelle"""
    prices = prices_df['close'].values
    total_minutes = len(prices)
    
    if target_trend == "NEUTRE":
        return {
            'duration_hours': 0.0,
            'duration_minutes': 0,
            'method': 'neutral',
            'confidence': 0.0
        }
    
    windows_minutes = [24*60, 18*60, 12*60, 6*60, 3*60]
    
    longest_duration = 0
    best_r_squared = 0.0
    
    for window_min in windows_minutes:
        if window_min > total_minutes:
            continue
        
        window_prices = prices[-window_min:]
        trend, slope, r_squared = calculate_regression_on_window(window_prices)
        
        if trend == target_trend and r_squared >= 0.10:
            longest_duration = window_min
            best_r_squared = r_squared
            break
    
    if longest_duration == 0:
        if target_trend == "BAISSIER":
            last_peak_idx = np.argmax(prices)
            duration_minutes = total_minutes - last_peak_idx
        else:
            last_peak_idx = np.argmin(prices)
            duration_minutes = total_minutes - last_peak_idx
        
        return {
            'duration_hours': duration_minutes / 60,
            'duration_minutes': duration_minutes,
            'method': 'last_peak',
            'confidence': 0.0
        }
    
    return {
        'duration_hours': longest_duration / 60,
        'duration_minutes': longest_duration,
        'method': 'regression_window',
        'confidence': best_r_squared
    }


def load_prices_24h(date_str: str, event_time_bern: str, conn) -> pd.DataFrame:
    """Charge prix 24h avant événement"""
    hour, minute, _ = event_time_bern.split(':')
    hour_db = int(hour) - 2
    minute_int = int(minute)
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_24h_before = date_obj - timedelta(days=1)
    date_24h_str = date_24h_before.strftime('%Y-%m-%d')
    
    timestamp_start = f"{date_24h_str} {hour_db:02d}:{minute_int:02d}:00+02:00"
    timestamp_end = f"{date_str} {hour_db:02d}:{minute_int:02d}:00+02:00"
    
    query = f"""
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime >= '{timestamp_start}'::TIMESTAMP
      AND datetime <= '{timestamp_end}'::TIMESTAMP
    ORDER BY datetime ASC
    """
    
    df = conn.execute(query).df()
    return df


def calculate_trend_score(prices_df: pd.DataFrame) -> Dict:
    """Calcule score tendance complet"""
    prices = prices_df['close'].values
    
    # Régression globale
    trend, slope, r_squared = calculate_regression_on_window(prices)
    
    # Durée
    duration_info = find_trend_duration(prices_df, trend)
    
    # Direction numérique
    if trend == 'HAUSSIER':
        direction = +1.0
    elif trend == 'BAISSIER':
        direction = -1.0
    else:
        direction = 0.0
    
    # Score pondéré
    duration_normalized = min(duration_info['duration_hours'], 24.0) / 24.0
    score = direction * duration_normalized * r_squared
    
    return {
        'trend': trend,
        'direction': direction,
        'duration_hours': duration_info['duration_hours'],
        'r_squared': r_squared,
        'duration_normalized': duration_normalized,
        'score': score
    }


# ============================================================================
# PARTIE 2 : CALIBRATION RÉTRO-INGÉNIERIE
# ============================================================================

def calibrate_on_reference_case(
    date_str: str,
    event_time_bern: str,
    surprise_net: float,
    impact_reel: float,
    db_path: str
):
    """
    ÉTAPE 1 : RÉTRO-INGÉNIERIE sur cas 11.09.2025
    
    Question : Quel facteur_correction nécessaire pour atteindre impact_reel ?
    
    Formule générale :
    Impact = base_impact × direction_factor × (1 + direction_sentiment × coef)
    
    On cherche le coefficient optimal pour direction_sentiment
    """
    print(f"\n{'='*80}")
    print(f"ÉTAPE 1 : CALIBRATION SUR CAS RÉFÉRENCE {date_str}")
    print(f"{'='*80}")
    
    conn = duckdb.connect(db_path, read_only=True)
    
    try:
        # Charger prix
        prices_df = load_prices_24h(date_str, event_time_bern, conn)
        
        # Calculer score tendance
        trend_info = calculate_trend_score(prices_df)
        
        print(f"\n📊 TENDANCE :")
        print(f"   Type : {trend_info['trend']}")
        print(f"   Durée : {trend_info['duration_hours']:.1f}h")
        print(f"   R² : {trend_info['r_squared']:.3f}")
        print(f"   Score pondéré : {trend_info['score']:+.3f}")
        
        # Direction factor (surprise nette)
        if surprise_net > 30:
            direction_factor = 1.05
        elif surprise_net > 0:
            direction_factor = min(1.0 + (surprise_net / 200), 1.05)
        elif surprise_net >= -30:
            direction_factor = max(1.0 + (surprise_net / 100), 0.7)
        else:
            direction_factor = 0.7
        
        print(f"\n🔢 PARAMÈTRES :")
        print(f"   Surprise nette : {surprise_net:+.1f}%")
        print(f"   Direction factor : {direction_factor:.3f}")
        print(f"   Impact réel : {impact_reel:.1f} pips")
        
        # RÉTRO-INGÉNIERIE : Tester différents base_impact
        print(f"\n🔬 RÉTRO-INGÉNIERIE - Recherche base_impact optimal :")
        print(f"   Formule : Impact = base_impact × direction_factor × (1 + score × coef)")
        
        # Tester range base_impact
        best_base = None
        best_coef = None
        best_error = float('inf')
        
        results = []
        
        for base_impact in np.arange(30, 60, 2):
            for coef in np.arange(0.0, 0.5, 0.05):
                # Calculer impact prédit
                combined_factor = direction_factor * (1 + trend_info['score'] * coef)
                impact_pred = base_impact * combined_factor
                
                error = abs(impact_pred - impact_reel)
                
                results.append({
                    'base_impact': base_impact,
                    'coef': coef,
                    'impact_pred': impact_pred,
                    'error': error
                })
                
                if error < best_error:
                    best_error = error
                    best_base = base_impact
                    best_coef = coef
        
        print(f"\n✅ CALIBRATION OPTIMALE :")
        print(f"   Base impact : {best_base:.1f} pips")
        print(f"   Coefficient score : {best_coef:.3f}")
        print(f"   Combined factor : {direction_factor * (1 + trend_info['score'] * best_coef):.3f}")
        print(f"   Impact prédit : {best_base * direction_factor * (1 + trend_info['score'] * best_coef):.1f} pips")
        print(f"   Impact réel : {impact_reel:.1f} pips")
        print(f"   Erreur : {best_error:.1f} pips ({best_error/impact_reel*100:.1f}%)")
        
        return {
            'base_impact': best_base,
            'coef_score': best_coef,
            'trend_info': trend_info,
            'direction_factor': direction_factor,
            'error': best_error,
            'all_results': pd.DataFrame(results)
        }
    
    finally:
        conn.close()


# ============================================================================
# PARTIE 3 : VALIDATION SUR AUTRES DATES
# ============================================================================

def validate_on_other_dates(
    base_impact: float,
    coef_score: float,
    dates: list,
    db_path: str
):
    """
    ÉTAPE 3 : VALIDATION formule calibrée sur autres dates
    """
    print(f"\n{'='*80}")
    print(f"ÉTAPE 3 : VALIDATION SUR AUTRES DATES")
    print(f"{'='*80}")
    print(f"\nFormule calibrée :")
    print(f"   Impact = {base_impact:.1f} × direction_factor × (1 + score × {coef_score:.3f})")
    
    conn = duckdb.connect(db_path, read_only=True)
    
    results = []
    
    try:
        for date_str, event_time, surprise, impact_reel in dates:
            print(f"\n{'='*60}")
            print(f"TEST : {date_str}")
            print(f"{'='*60}")
            
            # Charger prix
            prices_df = load_prices_24h(date_str, event_time, conn)
            
            # Score tendance
            trend_info = calculate_trend_score(prices_df)
            
            # Direction factor
            if surprise > 30:
                direction_factor = 1.05
            elif surprise > 0:
                direction_factor = min(1.0 + (surprise / 200), 1.05)
            elif surprise >= -30:
                direction_factor = max(1.0 + (surprise / 100), 0.7)
            else:
                direction_factor = 0.7
            
            # Impact prédit
            combined_factor = direction_factor * (1 + trend_info['score'] * coef_score)
            impact_pred = base_impact * combined_factor
            
            error = abs(impact_pred - impact_reel)
            
            print(f"   Tendance : {trend_info['trend']} {trend_info['duration_hours']:.1f}h R²={trend_info['r_squared']:.3f}")
            print(f"   Score : {trend_info['score']:+.3f}")
            print(f"   Direction factor : {direction_factor:.3f}")
            print(f"   Combined factor : {combined_factor:.3f}")
            print(f"   Impact prédit : {impact_pred:.1f} pips")
            print(f"   Impact réel : {impact_reel:.1f} pips")
            print(f"   Erreur : {error:.1f} pips ({error/impact_reel*100:.1f}%)")
            
            results.append({
                'date': date_str,
                'surprise': surprise,
                'trend': trend_info['trend'],
                'duration_hours': trend_info['duration_hours'],
                'r_squared': trend_info['r_squared'],
                'score': trend_info['score'],
                'direction_factor': direction_factor,
                'combined_factor': combined_factor,
                'impact_pred': impact_pred,
                'impact_reel': impact_reel,
                'error': error,
                'error_pct': error/impact_reel*100
            })
    
    finally:
        conn.close()
    
    df = pd.DataFrame(results)
    
    # Statistiques
    print(f"\n{'='*80}")
    print(f"STATISTIQUES VALIDATION")
    print(f"{'='*80}")
    print(f"\nMAE (Mean Absolute Error) : {df['error'].mean():.1f} pips")
    print(f"RMSE : {np.sqrt((df['error']**2).mean()):.1f} pips")
    print(f"Erreur max : {df['error'].max():.1f} pips (date {df.loc[df['error'].idxmax(), 'date']})")
    print(f"Erreur min : {df['error'].min():.1f} pips (date {df.loc[df['error'].idxmin(), 'date']})")
    print(f"Précision moyenne : {100 - df['error_pct'].mean():.1f}%")
    
    return df


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Calibration complète"""
    print("="*80)
    print("CALIBRATION EMPIRIQUE SCORE PONDÉRÉ - SESSION 92.12")
    print("Méthodologie : Rétro-ingénierie → Corrélation → Validation")
    print("="*80)
    
    db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb'
    
    # ÉTAPE 1 : Calibration sur 11.09.2025
    calibration = calibrate_on_reference_case(
        date_str='2025-09-11',
        event_time_bern='14:30:00',
        surprise_net=33.6,
        impact_reel=51.7,  # Impact réel validé MT5
        db_path=db_path
    )
    
    # ÉTAPE 2 : Sauvegarder tous résultats calibration
    output_calibration = Path(__file__).parent / 'calibration_grid_search.csv'
    calibration['all_results'].to_csv(output_calibration, index=False)
    print(f"\n💾 Grid search sauvegardé : {output_calibration}")
    
    # ÉTAPE 3 : Validation sur autres dates
    other_dates = [
        ('2025-01-15', '14:30:00', +27.5, 49.9),
        ('2025-05-13', '14:30:00', -108.5, 34.0),
        ('2025-07-15', '14:30:00', -70.0, 24.6)
    ]
    
    validation_df = validate_on_other_dates(
        base_impact=calibration['base_impact'],
        coef_score=calibration['coef_score'],
        dates=other_dates,
        db_path=db_path
    )
    
    # Sauvegarder résultats validation
    output_validation = Path(__file__).parent / 'validation_calibration.csv'
    validation_df.to_csv(output_validation, index=False)
    print(f"\n💾 Validation sauvegardée : {output_validation}")
    
    # DÉCISION
    print(f"\n{'='*80}")
    print(f"DÉCISION SESSION 92.12")
    print(f"{'='*80}")
    
    mae = validation_df['error'].mean()
    
    if mae < 8.0:
        print(f"\n✅ MAE = {mae:.1f} pips < 8.0 pips")
        print(f"\n🎉 FORMULE VALIDÉE - SESSION 92.12 SUCCÈS")
        print(f"\nFormule finale :")
        print(f"   Impact = {calibration['base_impact']:.1f} × direction_factor × (1 + score × {calibration['coef_score']:.3f})")
    else:
        print(f"\n❌ MAE = {mae:.1f} pips > 8.0 pips")
        print(f"\n⚠️  Score pondéré n'améliore pas suffisamment")
        print(f"\nOptions :")
        print(f"   1. Accepter V2 (surprise nette) MAE 8.5 pips")
        print(f"   2. Affiner calibration (autres coefficients)")
        print(f"   3. Approche différente (Session 92.13)")
    
    return calibration, validation_df


if __name__ == "__main__":
    calibration, validation = main()
