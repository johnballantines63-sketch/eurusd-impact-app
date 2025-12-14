"""
Compare les statistiques F autour de 08:00 et 12:20 pour comprendre
pourquoi la Méthode 2 choisit 12:20 au lieu de 08:00
"""

import sys
from pathlib import Path
from datetime import datetime
import pytz
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH
from core.trend_detection_pre_event import (
    prepare_price_series,
    linear_regression_segment
)
import duckdb


def calculate_f_stat_at_breakpoint(y, breakpoint_idx, t_min_idx, t0_idx):
    """Calcule la statistique F pour un point de rupture donné"""
    # Segment 1 : avant rupture
    segment1_y = y[t_min_idx:breakpoint_idx + 1]
    # Segment 2 : après rupture
    segment2_y = y[breakpoint_idx:t0_idx + 1]
    
    if len(segment1_y) < 240 or len(segment2_y) < 120:
        return None
    
    # Régression sur segment 1
    x1 = np.arange(len(segment1_y))
    reg1 = linear_regression_segment(segment1_y, x1)
    
    # Régression sur segment 2
    x2 = np.arange(len(segment2_y))
    reg2 = linear_regression_segment(segment2_y, x2)
    
    # Régression globale
    segment_global_y = y[t_min_idx:t0_idx + 1]
    x_global = np.arange(len(segment_global_y))
    reg_global = linear_regression_segment(segment_global_y, x_global)
    
    # SSE
    y1_pred = reg1['intercept'] + reg1['slope'] * x1
    y2_pred = reg2['intercept'] + reg2['slope'] * x2
    y_global_pred = reg_global['intercept'] + reg_global['slope'] * x_global
    
    sse1 = np.sum((segment1_y - y1_pred) ** 2)
    sse2 = np.sum((segment2_y - y2_pred) ** 2)
    sse_global = np.sum((segment_global_y - y_global_pred) ** 2)
    
    # F-stat
    k = 2
    n1 = len(segment1_y)
    n2 = len(segment2_y)
    
    numerator = (sse_global - (sse1 + sse2)) / k
    denominator = (sse1 + sse2) / (n1 + n2 - 2 * k)
    
    if denominator > 0:
        f_stat = numerator / denominator
        return {
            'f_stat': f_stat,
            'reg1': reg1,
            'reg2': reg2,
            'reg_global': reg_global
        }
    return None


def main():
    tz = pytz.timezone('Europe/Zurich')
    event_datetime = tz.localize(datetime(2025, 9, 11, 14, 30))
    lookback_start = event_datetime - pd.Timedelta(days=10)
    
    # Charger prix
    conn = duckdb.connect(str(DB_PATH))
    query = f"""
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime >= '{lookback_start.isoformat()}'
      AND datetime <= '{event_datetime.isoformat()}'
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query).df()
    conn.close()
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    if df_prices['datetime'].dt.tz is None:
        df_prices['datetime'] = df_prices['datetime'].dt.tz_localize('Europe/Zurich')
    else:
        df_prices['datetime'] = df_prices['datetime'].dt.tz_convert('Europe/Zurich')
    
    df_prices = df_prices.set_index('datetime')
    prices = df_prices['close']
    
    # Préparer série
    y = prepare_price_series(prices, use_log=True, denoise=False)
    
    # Trouver indices
    event_idx = prices.index.get_indexer([event_datetime], method='nearest')[0]
    t_min_idx = max(240, event_idx - 10080)  # 7 jours max
    
    # Points de rupture à tester
    breakpoints_to_test = [
        tz.localize(datetime(2025, 9, 9, 8, 0)),
        tz.localize(datetime(2025, 9, 9, 12, 20)),
        tz.localize(datetime(2025, 9, 9, 10, 0)),
        tz.localize(datetime(2025, 9, 9, 6, 0)),
    ]
    
    print("=" * 80)
    print("COMPARAISON STATISTIQUES F POUR DIFFÉRENTS POINTS DE RUPTURE")
    print("=" * 80)
    print()
    
    for bp_dt in breakpoints_to_test:
        bp_idx = prices.index.get_indexer([bp_dt], method='nearest')[0]
        if bp_idx < 0:
            continue
        
        result = calculate_f_stat_at_breakpoint(y.values, bp_idx, t_min_idx, event_idx)
        
        if result:
            print(f"📅 Point de rupture : {bp_dt.strftime('%Y-%m-%d %H:%M')}")
            print(f"   F-stat : {result['f_stat']:.2f}")
            print(f"   Segment 1 (avant) : R²={result['reg1']['r2']:.4f}, slope={result['reg1']['slope']:.6f}")
            print(f"   Segment 2 (après) : R²={result['reg2']['r2']:.4f}, slope={result['reg2']['slope']:.6f}")
            print(f"   Global : R²={result['reg_global']['r2']:.4f}")
            print()


if __name__ == '__main__':
    main()


