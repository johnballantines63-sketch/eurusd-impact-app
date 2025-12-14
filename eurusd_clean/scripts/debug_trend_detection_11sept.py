"""
Debug : Pourquoi le segment 09.09 08:00 n'est pas sélectionné ?
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
    detect_trend_pre_event,
    prepare_price_series,
    linear_regression_segment
)
import duckdb


def test_specific_segment(db_path, event_datetime, start_datetime):
    """Test un segment spécifique"""
    tz = pytz.timezone('Europe/Zurich')
    
    # Charger prix
    lookback_start = event_datetime - pd.Timedelta(days=10)
    
    conn = duckdb.connect(str(db_path))
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
    start_idx = prices.index.get_indexer([start_datetime], method='nearest')[0]
    
    if event_idx < 0 or start_idx < 0:
        print(f"❌ Indices non trouvés : event={event_idx}, start={start_idx}")
        return
    
    # Préparer série
    y = prepare_price_series(prices, use_log=True, denoise=False)
    
    # Segment
    segment_y = y.iloc[start_idx:event_idx + 1].values
    segment_prices = prices.iloc[start_idx:event_idx + 1].values
    
    length = len(segment_y)
    
    # Régression
    x = np.arange(length)
    reg = linear_regression_segment(segment_y, x)
    
    # Score avec la formule actuelle
    if length >= 2880:
        bonus_longueur = 0.5
    elif length >= 1440:
        bonus_longueur = 0.3
    elif length >= 720:
        bonus_longueur = 0.15
    else:
        bonus_longueur = 0.0
    
    penalty_courteur = 0.3 if length < 360 else (0.15 if length < 720 else 0.0)
    lambda_penalty = 0.1
    
    score = reg['r2'] * (1 + bonus_longueur) - penalty_courteur - (lambda_penalty / np.sqrt(length))
    
    # Amplitude
    amplitude = (prices.iloc[event_idx] - prices.iloc[start_idx]) * 10000
    
    print(f"📊 Segment {start_datetime.strftime('%Y-%m-%d %H:%M')} → {event_datetime.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Longueur : {length} minutes ({length/60:.1f} heures, {length/1440:.2f} jours)")
    print(f"   R² : {reg['r2']:.4f}")
    print(f"   T-stat : {reg['tstat']:.2f}")
    print(f"   Amplitude : {amplitude:.1f} pips")
    print(f"   Bonus longueur : {bonus_longueur:.2f}")
    print(f"   Pénalité courteur : {penalty_courteur:.2f}")
    print(f"   Score final : {score:.4f}")
    print()


def main():
    tz = pytz.timezone('Europe/Zurich')
    event_datetime = tz.localize(datetime(2025, 9, 11, 14, 30))
    
    # Test segments candidats
    candidates = [
        tz.localize(datetime(2025, 9, 8, 18, 15)),  # Ce que trouve l'algo actuel
        tz.localize(datetime(2025, 9, 9, 8, 0)),    # Ce qu'on cherche
        tz.localize(datetime(2025, 9, 8, 8, 0)),   # Alternative
    ]
    
    print("=" * 80)
    print("COMPARAISON SEGMENTS CANDIDATS")
    print("=" * 80)
    print()
    
    for start_dt in candidates:
        test_specific_segment(Path(DB_PATH), event_datetime, start_dt)
    
    # Résultat actuel
    print("=" * 80)
    print("RÉSULTAT ALGORITHME ACTUEL")
    print("=" * 80)
    result = detect_trend_pre_event(
        Path(DB_PATH),
        event_datetime,
        lookback_days=10,
        method="right-anchored"
    )
    print(f"Début détecté : {result.get('t_start_datetime')}")
    print(f"R² : {result.get('R2'):.4f}")
    print(f"Score : {result.get('score'):.4f}")


if __name__ == '__main__':
    main()


