"""
Diagnostic : Pourquoi le calcul de R² échoue-t-il pour certaines dates ?
========================================================================
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH
import duckdb


def detect_swing_highs(prices, window=240, threshold=0.0001):
    """Détecte swing highs"""
    swing_highs = []
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        if center > max(left.max(), right.max()) + threshold:
            swing_highs.append(i)
    return swing_highs


def detect_swing_lows(prices, window=240, threshold=0.0001):
    """Détecte swing lows"""
    swing_lows = []
    for i in range(window, len(prices) - window):
        center = prices[i]
        left = prices[i-window:i]
        right = prices[i+1:i+window+1]
        if center < min(left.min(), right.min()) - threshold:
            swing_lows.append(i)
    return swing_lows


def detect_trend_reversals(swing_highs, swing_lows):
    """Détecte inversions de tendance"""
    all_points = sorted(set(swing_highs + swing_lows))
    reversals = []
    for i in range(1, len(all_points)):
        prev_idx = all_points[i-1]
        curr_idx = all_points[i]
        if (prev_idx in swing_highs and curr_idx in swing_lows) or \
           (prev_idx in swing_lows and curr_idx in swing_highs):
            reversals.append(curr_idx)
    return reversals


def diagnose_r2_calculation(
    date: datetime,
    target_time: str,
    db_path: Path,
    timezone_str: str = "Europe/Zurich",
    lookback_days: int = 3,
    window: int = 240
) -> Dict:
    """Diagnostique pourquoi le calcul de R² échoue"""
    
    conn = duckdb.connect(str(db_path))
    
    hour, minute = map(int, target_time.split(':'))
    cluster_time = pd.Timestamp(date).replace(hour=hour, minute=minute)
    cluster_time = cluster_time.tz_localize(timezone_str)
    
    lookback_start = cluster_time - pd.Timedelta(days=lookback_days)
    
    query = f"""
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime >= '{lookback_start.isoformat()}'
      AND datetime < '{cluster_time.isoformat()}'
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query).df()
    conn.close()
    
    result = {
        'date': date.strftime('%Y-%m-%d'),
        'cluster_time': cluster_time.isoformat(),
        'lookback_start': lookback_start.isoformat(),
        'has_data': False,
        'n_prices': 0,
        'enough_prices': False,
        'n_swing_highs': 0,
        'n_swing_lows': 0,
        'n_reversals': 0,
        'has_reversal': False,
        'last_reversal_idx': None,
        'segment_length': 0,
        'enough_segment': False,
        'r2_calculated': False,
        'r2_value': None,
        'error': None
    }
    
    if df_prices.empty:
        result['error'] = 'Aucune donnée de prix'
        return result
    
    result['has_data'] = True
    result['n_prices'] = len(df_prices)
    
    if len(df_prices) < window * 2:
        result['error'] = f'Pas assez de données de prix ({len(df_prices)} < {window * 2})'
        return result
    
    result['enough_prices'] = True
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    if df_prices['datetime'].dt.tz is None:
        df_prices['datetime'] = df_prices['datetime'].dt.tz_localize(timezone_str)
    else:
        df_prices['datetime'] = df_prices['datetime'].dt.tz_convert(timezone_str)
    
    prices = df_prices['close'].values
    
    # Détecter inversions
    swing_highs = detect_swing_highs(pd.Series(prices), window=window)
    swing_lows = detect_swing_lows(pd.Series(prices), window=window)
    reversals = detect_trend_reversals(swing_highs, swing_lows)
    
    result['n_swing_highs'] = len(swing_highs)
    result['n_swing_lows'] = len(swing_lows)
    result['n_reversals'] = len(reversals)
    
    if len(reversals) < 2:
        result['error'] = f'Pas assez de reversals ({len(reversals)} < 2)'
        return result
    
    result['has_reversal'] = True
    
    # Prendre le dernier segment avant cluster_time
    last_reversal_idx = reversals[-1]
    result['last_reversal_idx'] = last_reversal_idx
    
    if last_reversal_idx >= len(prices) - 1:
        result['error'] = f'Dernier reversal trop proche de la fin ({last_reversal_idx} >= {len(prices) - 1})'
        return result
    
    segment_prices = prices[last_reversal_idx:]
    result['segment_length'] = len(segment_prices)
    
    if len(segment_prices) < 10:
        result['error'] = f'Segment trop court ({len(segment_prices)} < 10)'
        return result
    
    result['enough_segment'] = True
    
    # Calculer R²
    x = np.arange(len(segment_prices))
    coeffs = np.polyfit(x, segment_prices, 1)
    y_pred = np.polyval(coeffs, x)
    ss_res = np.sum((segment_prices - y_pred) ** 2)
    ss_tot = np.sum((segment_prices - np.mean(segment_prices)) ** 2)
    
    if ss_tot == 0:
        result['error'] = 'Variance totale nulle (prix constants)'
        return result
    
    r2 = 1 - (ss_res / ss_tot)
    result['r2_calculated'] = True
    result['r2_value'] = max(0.0, min(1.0, r2))
    
    return result


def main():
    """Script principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnostic calcul R²')
    parser.add_argument('--date', type=str, required=True, help='Date référence (YYYY-MM-DD)')
    parser.add_argument('--time', type=str, default='14:30', help='Heure référence (HH:MM)')
    parser.add_argument('--dates', type=str, nargs='+', help='Dates à diagnostiquer (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    db_path = Path(DB_PATH)
    
    if args.dates:
        dates_to_test = [datetime.strptime(d, '%Y-%m-%d') for d in args.dates]
    else:
        # Dates qui échouent selon le test précédent
        dates_to_test = [
            datetime(2023, 7, 7),
            datetime(2023, 8, 4),
            datetime(2023, 9, 1),
            datetime(2023, 10, 6),
            datetime(2023, 12, 8),
        ]
    
    print("=" * 80)
    print("DIAGNOSTIC CALCUL R²")
    print("=" * 80)
    print()
    
    for date in dates_to_test:
        result = diagnose_r2_calculation(date, args.time, db_path)
        
        print(f"📅 Date : {result['date']}")
        print(f"   Cluster time : {result['cluster_time']}")
        print(f"   Lookback start : {result['lookback_start']}")
        print(f"   Données de prix : {result['n_prices']} points")
        print(f"   Swing highs : {result['n_swing_highs']}")
        print(f"   Swing lows : {result['n_swing_lows']}")
        print(f"   Reversals : {result['n_reversals']}")
        if result['last_reversal_idx'] is not None:
            print(f"   Dernier reversal idx : {result['last_reversal_idx']}")
            print(f"   Longueur segment : {result['segment_length']}")
        if result['r2_value'] is not None:
            print(f"   ✅ R² calculé : {result['r2_value']:.4f}")
        if result['error']:
            print(f"   ❌ Erreur : {result['error']}")
        print()


if __name__ == '__main__':
    main()

