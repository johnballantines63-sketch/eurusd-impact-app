"""
CALIBRATION EMPIRIQUE AVEC AMPLITUDE - SESSION 92.13

AMÉLIORATION ANDRÉ :
====================
"je pense qu'on peut encore améliorer si on tient compte de l'écart en pips 
entre début et fin de tendance le delta de la tendance"

FORMULE ACTUELLE S92.12 :
=========================
Impact = 52.0 × direction_factor × (1 + score_tendance × 0.100)
score_tendance = direction × (durée/24) × R²

FORMULE PROPOSÉE S92.13 :
=========================
score_tendance = direction × (durée/24) × R² × amplitude_factor

EXEMPLE PROBLÈME :
==================
Tendance A : BAISSIER 18h, R²=0.75, amplitude -50 pips → Score actuel : -0.559
Tendance B : BAISSIER 18h, R²=0.75, amplitude -10 pips → Score actuel : -0.559
→ Les deux ont le MÊME score alors que A est beaucoup plus fort !

SOLUTION : Intégrer amplitude_factor

Date : 29 octobre 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import duckdb
from pathlib import Path
from typing import Dict, Tuple, List
import matplotlib.pyplot as plt


# ============================================================================
# PARTIE 1 : FONCTIONS RÉUTILISÉES (S92.12)
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


def find_trend_duration(prices_df: pd.DataFrame, target_trend: str) -> float:
    """Trouve durée tendance actuelle (version simplifiée)"""
    prices = prices_df['close'].values
    total_minutes = len(prices)
    
    if target_trend == "NEUTRE":
        return 0.0
    
    windows_minutes = [24*60, 18*60, 12*60, 6*60, 3*60]
    
    for window_min in windows_minutes:
        if window_min > total_minutes:
            continue
        
        window_prices = prices[-window_min:]
        trend, slope, r_squared = calculate_regression_on_window(window_prices)
        
        if trend == target_trend and r_squared >= 0.10:
            return window_min / 60.0  # Retourne heures
    
    # Si pas de fenêtre valide, chercher dernier extremum
    if target_trend == "BAISSIER":
        last_peak_idx = np.argmax(prices)
        duration_minutes = total_minutes - last_peak_idx
    else:
        last_peak_idx = np.argmin(prices)
        duration_minutes = total_minutes - last_peak_idx
    
    return duration_minutes / 60.0


def load_prices_24h_before(date_str: str, event_time_bern: str, conn) -> pd.DataFrame:
    """Charge prix EURUSD 24h avant événement"""
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


# ============================================================================
# PARTIE 2 : NOUVELLES FONCTIONS AMPLITUDE (S92.13)
# ============================================================================

def calculate_amplitude(prices_df: pd.DataFrame, trend: str, duration_hours: float) -> Dict:
    """
    Calcule amplitude de la tendance
    
    MÉTHODES TESTÉES :
    1. HIGH - LOW sur 24h
    2. Début tendance - Fin tendance
    3. Variation depuis extremum
    
    Args:
        prices_df: DataFrame prix 24h
        trend: 'HAUSSIER', 'BAISSIER', 'NEUTRE'
        duration_hours: Durée tendance
    
    Returns:
        Dict avec différentes mesures amplitude
    """
    prices = prices_df['close'].values
    
    # Méthode 1 : HIGH - LOW sur 24h
    price_high = prices.max()
    price_low = prices.min()
    amplitude_range = (price_high - price_low) * 10000  # en pips
    
    # Méthode 2 : Début tendance - Fin tendance
    if trend == "NEUTRE" or duration_hours == 0:
        amplitude_trend = 0.0
        start_price = prices[-1]
        end_price = prices[-1]
    else:
        # Calculer nb minutes correspondant à la durée
        duration_minutes = int(duration_hours * 60)
        duration_minutes = min(duration_minutes, len(prices))
        
        start_price = prices[-duration_minutes]
        end_price = prices[-1]
        amplitude_trend = (end_price - start_price) * 10000  # en pips (peut être négatif)
    
    # Méthode 3 : Variation depuis extremum
    if trend == "BAISSIER":
        # Amplitude = HIGH - prix_actuel
        amplitude_from_extreme = (price_high - prices[-1]) * 10000
    elif trend == "HAUSSIER":
        # Amplitude = prix_actuel - LOW
        amplitude_from_extreme = (prices[-1] - price_low) * 10000
    else:
        amplitude_from_extreme = 0.0
    
    return {
        'amplitude_range': amplitude_range,
        'amplitude_trend': amplitude_trend,
        'amplitude_from_extreme': amplitude_from_extreme,
        'start_price': start_price,
        'end_price': end_price,
        'price_high': price_high,
        'price_low': price_low
    }


def calculate_amplitude_factor(amplitude: Dict, method: int) -> float:
    """
    Calcule facteur amplitude selon méthode choisie
    
    MÉTHODES :
    1. Linéaire : amplitude_pips / 50
    2. Plafonné : min(amplitude_pips / 100, 1.0)
    3. Logarithmique : log(1 + amplitude_pips / 20)
    4. Racine carrée : sqrt(amplitude_pips / 10)
    
    Args:
        amplitude: Dict depuis calculate_amplitude()
        method: Numéro méthode (1-4)
    
    Returns:
        float: Facteur amplitude (> 0)
    """
    # Utiliser amplitude_from_extreme (plus cohérent avec tendance)
    amp = abs(amplitude['amplitude_from_extreme'])
    
    if method == 1:
        # Linéaire : amplitude / 50
        factor = amp / 50.0
    elif method == 2:
        # Plafonné : min(amplitude / 100, 1.0)
        factor = min(amp / 100.0, 1.0)
    elif method == 3:
        # Logarithmique : log(1 + amplitude / 20)
        factor = np.log(1 + amp / 20.0)
    elif method == 4:
        # Racine carrée : sqrt(amplitude / 10)
        factor = np.sqrt(amp / 10.0)
    else:
        factor = 1.0
    
    # Assurer factor > 0 (min 0.1 pour éviter division par zéro)
    factor = max(factor, 0.1)
    
    return factor


def calculate_score_tendance_v2(
    trend: str,
    duration_hours: float,
    r_squared: float,
    amplitude_factor: float
) -> float:
    """
    Calcule score tendance V2 avec amplitude
    
    FORMULE S92.13 :
    score = direction × (durée/24) × R² × amplitude_factor
    
    Args:
        trend: 'HAUSSIER', 'BAISSIER', 'NEUTRE'
        duration_hours: Durée tendance
        r_squared: Coefficient détermination
        amplitude_factor: Facteur amplitude
    
    Returns:
        float: Score entre -inf et +inf (pratique -2 à +2)
    """
    if trend == "HAUSSIER":
        direction = +1.0
    elif trend == "BAISSIER":
        direction = -1.0
    else:
        direction = 0.0
    
    duration_normalized = min(duration_hours, 24.0) / 24.0
    
    score = direction * duration_normalized * r_squared * amplitude_factor
    
    return score


# ============================================================================
# PARTIE 3 : CALIBRATION GRID SEARCH 3D
# ============================================================================

def calculate_impact_s92_13(
    surprise_net: float,
    score_tendance: float,
    base_impact: float,
    coef_score: float
) -> float:
    """
    Calcule impact avec formule S92.13
    
    Args:
        surprise_net: Surprise nette en %
        score_tendance: Score tendance V2
        base_impact: Base impact calibré
        coef_score: Coefficient score
    
    Returns:
        float: Impact prédit en pips
    """
    # Direction factor (surprise nette)
    if surprise_net > 30:
        direction_factor = 1.05
    elif surprise_net > 0:
        direction_factor = min(1.0 + (surprise_net / 200), 1.05)
    elif surprise_net >= -30:
        direction_factor = max(1.0 + (surprise_net / 100), 0.7)
    else:
        direction_factor = 0.7
    
    # Combined factor
    combined_factor = direction_factor * (1 + score_tendance * coef_score)
    
    # Impact final
    impact = base_impact * combined_factor
    
    return impact


def grid_search_3d(
    date_str: str,
    event_time_bern: str,
    surprise_net: float,
    impact_real: float,
    conn
) -> pd.DataFrame:
    """
    Grid search 3D pour trouver paramètres optimaux
    
    PARAMÈTRES TESTÉS :
    - base_impact : [48, 50, 52, 54, 56] (5 valeurs)
    - coef_score : [0.06, 0.08, 0.10, 0.12, 0.14] (5 valeurs)
    - amplitude_method : [1, 2, 3, 4] (4 méthodes)
    TOTAL : 5 × 5 × 4 = 100 combinaisons
    
    Args:
        date_str: Date format 'YYYY-MM-DD'
        event_time_bern: Heure Bern
        surprise_net: Surprise nette %
        impact_real: Impact réel en pips
        conn: Connexion DB
    
    Returns:
        DataFrame avec tous résultats triés par erreur
    """
    print(f"\n{'='*60}")
    print(f"GRID SEARCH 3D - {date_str}")
    print(f"Impact réel : {impact_real:.1f} pips")
    print(f"{'='*60}")
    
    # Charger prix 24h
    prices_df = load_prices_24h_before(date_str, event_time_bern, conn)
    
    # Régression linéaire
    trend, slope, r_squared = calculate_regression_on_window(prices_df['close'].values)
    
    # Durée tendance
    duration_hours = find_trend_duration(prices_df, trend)
    
    # Amplitude
    amplitude = calculate_amplitude(prices_df, trend, duration_hours)
    
    print(f"\n📊 DONNÉES TENDANCE :")
    print(f"   Tendance : {trend}")
    print(f"   Durée : {duration_hours:.1f}h")
    print(f"   R² : {r_squared:.3f}")
    print(f"   Amplitude range : {amplitude['amplitude_range']:.1f} pips")
    print(f"   Amplitude trend : {amplitude['amplitude_trend']:.1f} pips")
    print(f"   Amplitude from extreme : {amplitude['amplitude_from_extreme']:.1f} pips")
    
    # Paramètres grid
    base_impacts = [48.0, 50.0, 52.0, 54.0, 56.0]
    coef_scores = [0.06, 0.08, 0.10, 0.12, 0.14]
    amplitude_methods = [1, 2, 3, 4]
    
    results = []
    
    print(f"\n🔍 TEST {len(base_impacts)} × {len(coef_scores)} × {len(amplitude_methods)} = {len(base_impacts)*len(coef_scores)*len(amplitude_methods)} combinaisons...")
    
    for base_impact in base_impacts:
        for coef_score in coef_scores:
            for amp_method in amplitude_methods:
                # Calculer amplitude_factor
                amp_factor = calculate_amplitude_factor(amplitude, amp_method)
                
                # Score tendance V2
                score_v2 = calculate_score_tendance_v2(
                    trend,
                    duration_hours,
                    r_squared,
                    amp_factor
                )
                
                # Impact prédit
                impact_pred = calculate_impact_s92_13(
                    surprise_net,
                    score_v2,
                    base_impact,
                    coef_score
                )
                
                # Erreur
                error = abs(impact_pred - impact_real)
                
                results.append({
                    'base_impact': base_impact,
                    'coef_score': coef_score,
                    'amplitude_method': amp_method,
                    'amplitude_factor': amp_factor,
                    'score_tendance_v2': score_v2,
                    'impact_pred': impact_pred,
                    'impact_real': impact_real,
                    'error': error,
                    'error_pct': (error / impact_real) * 100
                })
    
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values('error')
    
    print(f"\n✅ Grid search terminé : {len(df_results)} combinaisons testées")
    
    return df_results


def test_validation_dates(
    validation_dates: List[Dict],
    best_params: Dict,
    conn
) -> pd.DataFrame:
    """
    Teste paramètres optimaux sur dates validation
    
    Args:
        validation_dates: Liste dicts avec date, time, surprise, impact_real
        best_params: Dict avec base_impact, coef_score, amplitude_method
        conn: Connexion DB
    
    Returns:
        DataFrame résultats validation
    """
    print(f"\n{'='*60}")
    print(f"VALIDATION SUR {len(validation_dates)} DATES")
    print(f"Paramètres optimaux :")
    print(f"  base_impact = {best_params['base_impact']:.1f}")
    print(f"  coef_score = {best_params['coef_score']:.3f}")
    print(f"  amplitude_method = {best_params['amplitude_method']}")
    print(f"{'='*60}")
    
    results = []
    
    for date_info in validation_dates:
        date_str = date_info['date']
        event_time = date_info['time']
        surprise = date_info['surprise']
        impact_real = date_info['impact_real']
        
        print(f"\n📅 Test {date_str} {event_time}")
        
        # Charger prix
        prices_df = load_prices_24h_before(date_str, event_time, conn)
        
        # Régression
        trend, slope, r_squared = calculate_regression_on_window(prices_df['close'].values)
        
        # Durée
        duration_hours = find_trend_duration(prices_df, trend)
        
        # Amplitude
        amplitude = calculate_amplitude(prices_df, trend, duration_hours)
        amp_factor = calculate_amplitude_factor(amplitude, best_params['amplitude_method'])
        
        # Score V2
        score_v2 = calculate_score_tendance_v2(
            trend,
            duration_hours,
            r_squared,
            amp_factor
        )
        
        # Impact prédit
        impact_pred = calculate_impact_s92_13(
            surprise,
            score_v2,
            best_params['base_impact'],
            best_params['coef_score']
        )
        
        error = abs(impact_pred - impact_real)
        
        print(f"   Tendance : {trend} {duration_hours:.1f}h R²={r_squared:.3f}")
        print(f"   Amplitude factor : {amp_factor:.3f}")
        print(f"   Score V2 : {score_v2:+.3f}")
        print(f"   Impact prédit : {impact_pred:.1f} pips")
        print(f"   Impact réel : {impact_real:.1f} pips")
        print(f"   Erreur : {error:.1f} pips ({error/impact_real*100:.1f}%)")
        
        results.append({
            'date': date_str,
            'trend': trend,
            'duration_hours': duration_hours,
            'r_squared': r_squared,
            'amplitude_factor': amp_factor,
            'amplitude_from_extreme': amplitude['amplitude_from_extreme'],
            'score_v2': score_v2,
            'surprise_net': surprise,
            'impact_pred': impact_pred,
            'impact_real': impact_real,
            'error': error,
            'error_pct': (error / impact_real) * 100
        })
    
    df_results = pd.DataFrame(results)
    
    # Statistiques globales
    mae = df_results['error'].mean()
    rmse = np.sqrt((df_results['error'] ** 2).mean())
    
    print(f"\n{'='*60}")
    print(f"STATISTIQUES VALIDATION :")
    print(f"  MAE : {mae:.2f} pips")
    print(f"  RMSE : {rmse:.2f} pips")
    print(f"  Erreur max : {df_results['error'].max():.2f} pips")
    print(f"  Erreur min : {df_results['error'].min():.2f} pips")
    print(f"{'='*60}")
    
    return df_results


# ============================================================================
# PARTIE 4 : MAIN CALIBRATION
# ============================================================================

def main():
    """Exécution complète calibration avec amplitude"""
    
    print("\n" + "="*80)
    print("CALIBRATION EMPIRIQUE AVEC AMPLITUDE - SESSION 92.13")
    print("="*80)
    
    # Connexion DB
    db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb'
    conn = duckdb.connect(db_path, read_only=True)
    
    try:
        # CAS CALIBRATION : 11.09.2025
        print("\n🎯 PHASE 1 : CALIBRATION SUR CAS 11.09.2025")
        
        df_grid = grid_search_3d(
            date_str='2025-09-11',
            event_time_bern='14:30:00',
            surprise_net=33.6,
            impact_real=51.7,
            conn=conn
        )
        
        # Afficher top 10 résultats
        print(f"\n🏆 TOP 10 COMBINAISONS :")
        print(df_grid.head(10).to_string(index=False))
        
        # Meilleurs paramètres
        best = df_grid.iloc[0]
        
        print(f"\n✅ MEILLEURS PARAMÈTRES TROUVÉS :")
        print(f"   base_impact = {best['base_impact']:.1f}")
        print(f"   coef_score = {best['coef_score']:.3f}")
        print(f"   amplitude_method = {best['amplitude_method']}")
        print(f"   amplitude_factor = {best['amplitude_factor']:.3f}")
        print(f"   Score V2 = {best['score_tendance_v2']:+.3f}")
        print(f"   Impact prédit = {best['impact_pred']:.1f} pips")
        print(f"   Erreur calibration = {best['error']:.1f} pips ({best['error_pct']:.1f}%)")
        
        # Sauvegarder résultats grid
        output_path = Path(__file__).parent / 'calibration_amplitude_grid_search.csv'
        df_grid.to_csv(output_path, index=False)
        print(f"\n💾 Grid search sauvegardé : {output_path}")
        
        # PHASE 2 : VALIDATION
        print(f"\n{'='*80}")
        print(f"🎯 PHASE 2 : VALIDATION SUR 3 AUTRES DATES")
        print(f"{'='*80}")
        
        validation_dates = [
            {
                'date': '2025-01-15',
                'time': '14:30:00',
                'surprise': 27.5,
                'impact_real': 49.9
            },
            {
                'date': '2025-05-13',
                'time': '14:30:00',
                'surprise': -108.5,
                'impact_real': 34.0
            },
            {
                'date': '2025-07-15',
                'time': '14:30:00',
                'surprise': -70.0,
                'impact_real': 24.6
            }
        ]
        
        best_params = {
            'base_impact': best['base_impact'],
            'coef_score': best['coef_score'],
            'amplitude_method': int(best['amplitude_method'])
        }
        
        df_validation = test_validation_dates(validation_dates, best_params, conn)
        
        # Sauvegarder validation
        output_val = Path(__file__).parent / 'validation_amplitude.csv'
        df_validation.to_csv(output_val, index=False)
        print(f"\n💾 Validation sauvegardée : {output_val}")
        
        # COMPARAISON S92.12 vs S92.13
        print(f"\n{'='*80}")
        print(f"📊 COMPARAISON S92.12 vs S92.13")
        print(f"{'='*80}")
        
        # MAE S92.12 (référence)
        mae_s92_12 = 5.3  # Depuis SESSION92.12_RAPPORT_COMPLET.md
        
        # MAE S92.13 (4 dates : calibration + validation)
        all_errors = [best['error']] + df_validation['error'].tolist()
        mae_s92_13 = np.mean(all_errors)
        
        print(f"\n🔢 MÉTRIQUES GLOBALES (4 dates) :")
        print(f"   MAE S92.12 : {mae_s92_12:.2f} pips")
        print(f"   MAE S92.13 : {mae_s92_13:.2f} pips")
        
        if mae_s92_13 < mae_s92_12:
            improvement = ((mae_s92_12 - mae_s92_13) / mae_s92_12) * 100
            print(f"   ✅ AMÉLIORATION : -{improvement:.1f}%")
            print(f"\n🎉 SUCCÈS ! Amplitude améliore la formule !")
        else:
            degradation = ((mae_s92_13 - mae_s92_12) / mae_s92_12) * 100
            print(f"   ❌ DÉGRADATION : +{degradation:.1f}%")
            print(f"\n⚠️ Amplitude n'améliore pas la formule")
        
        print(f"\n{'='*80}")
        print(f"✅ CALIBRATION AMPLITUDE TERMINÉE")
        print(f"{'='*80}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
