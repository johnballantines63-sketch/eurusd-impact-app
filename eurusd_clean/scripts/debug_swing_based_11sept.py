"""
Debug : Pourquoi le pic à 08:00 n'est pas sélectionné ?
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
    detect_swing_highs_lows,
    prepare_price_series,
    linear_regression_segment
)
import duckdb


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
    
    # Trouver indices
    event_idx = prices.index.get_indexer([event_datetime], method='nearest')[0]
    target_dt = tz.localize(datetime(2025, 9, 9, 8, 0))
    target_idx = prices.index.get_indexer([target_dt], method='nearest')[0]
    
    t_min_idx = max(0, event_idx - 10080)
    t_max_idx = max(t_min_idx, event_idx - 120)
    
    print("=" * 80)
    print("DEBUG SWING-BASED : PIC À 08:00")
    print("=" * 80)
    print(f"Target (08:00) : index {target_idx}, datetime {prices.index[target_idx]}")
    print(f"Event (14:30) : index {event_idx}, datetime {prices.index[event_idx]}")
    print()
    
    # Détecter swing points
    all_swing_highs = set()
    for window in [30, 60, 120, 240]:
        for threshold in [0.00005, 0.0001, 0.0002]:
            swing_highs, _ = detect_swing_highs_lows(prices, window=window, threshold=threshold)
            all_swing_highs.update(swing_highs)
    
    swing_highs_in_window = [idx for idx in all_swing_highs if t_min_idx <= idx <= t_max_idx]
    
    # Chercher maximums locaux
    local_maxima = []
    for i in range(t_min_idx + 60, t_max_idx, 15):
        window_local = prices.iloc[max(0, i-60):min(len(prices), i+60)]
        if len(window_local) > 0:
            local_max_idx = window_local.idxmax()
            if isinstance(local_max_idx, pd.Timestamp):
                local_max_pos = prices.index.get_loc(local_max_idx)
                if t_min_idx <= local_max_pos <= t_max_idx:
                    local_maxima.append(local_max_pos)
    
    all_highs = sorted(set(swing_highs_in_window + local_maxima), reverse=True)
    
    print(f"Swing highs dans fenêtre : {len(swing_highs_in_window)}")
    print(f"Maximums locaux : {len(local_maxima)}")
    print(f"Total candidats : {len(all_highs)}")
    print()
    
    # Vérifier si 08:00 est dans les candidats
    if target_idx in all_highs:
        print(f"✅ 08:00 est dans les candidats (index {target_idx})")
    else:
        print(f"❌ 08:00 n'est PAS dans les candidats")
        # Chercher le plus proche
        closest = min(all_highs, key=lambda x: abs(x - target_idx))
        print(f"   Plus proche : index {closest}, datetime {prices.index[closest]}, distance {abs(closest - target_idx)} min")
    print()
    
    # Tester le segment depuis 08:00
    y = prepare_price_series(prices, use_log=True, denoise=False)
    segment_y = y.iloc[target_idx:event_idx + 1].values
    x = np.arange(len(segment_y))
    reg = linear_regression_segment(segment_y, x)
    
    amplitude = (prices.iloc[event_idx] - prices.iloc[target_idx]) * 10000
    
    print(f"📊 Segment depuis 08:00 :")
    print(f"   Longueur : {len(segment_y)} minutes ({len(segment_y)/60:.1f} heures)")
    print(f"   R² : {reg['r2']:.4f}")
    print(f"   Slope : {reg['slope']:.6f} (bearish si < 0)")
    print(f"   T-stat : {reg['tstat']:.2f}")
    print(f"   Amplitude : {amplitude:.1f} pips")
    print()
    
    # Comparer avec 11:38
    dt_1138 = tz.localize(datetime(2025, 9, 11, 11, 38))
    idx_1138 = prices.index.get_indexer([dt_1138], method='nearest')[0]
    segment_y_1138 = y.iloc[idx_1138:event_idx + 1].values
    x_1138 = np.arange(len(segment_y_1138))
    reg_1138 = linear_regression_segment(segment_y_1138, x_1138)
    amplitude_1138 = (prices.iloc[event_idx] - prices.iloc[idx_1138]) * 10000
    
    print(f"📊 Segment depuis 11:38 (actuellement sélectionné) :")
    print(f"   Longueur : {len(segment_y_1138)} minutes ({len(segment_y_1138)/60:.1f} heures)")
    print(f"   R² : {reg_1138['r2']:.4f}")
    print(f"   Slope : {reg_1138['slope']:.6f}")
    print(f"   T-stat : {reg_1138['tstat']:.2f}")
    print(f"   Amplitude : {amplitude_1138:.1f} pips")


if __name__ == '__main__':
    main()


