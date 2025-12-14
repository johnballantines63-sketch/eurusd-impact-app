"""
Debug pour comprendre pourquoi le pic à 05:55 n'est pas détecté
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
from core.trend_detection_pre_event import detect_swing_highs_lows
import duckdb

# Date et heure de l'événement (11.09.2025 14:30)
tz = pytz.timezone('Europe/Zurich')
event_date = tz.localize(datetime(2025, 9, 11, 14, 30))

# Charger prix
conn = duckdb.connect(str(DB_PATH))
query = f"""
SELECT datetime, close
FROM prices_bern
WHERE datetime >= '{event_date - pd.Timedelta(days=3)}'
  AND datetime <= '{event_date + pd.Timedelta(hours=1)}'
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
prices_series = df_prices['close']

# Trouver l'index de l'événement
event_idx = prices_series.index.get_indexer([event_date], method='nearest')[0]
event_time = prices_series.index[event_idx]

print('='*80)
print('DEBUG SWING-BASED DETECTION')
print('='*80)
print(f'Date événement : {event_date.strftime("%Y-%m-%d %H:%M")}')
print(f'Index événement : {event_idx}')
print()

# Pic attendu à 05:55 le 09.09
expected_pic = tz.localize(datetime(2025, 9, 9, 5, 55))
expected_pic_idx = prices_series.index.get_indexer([expected_pic], method='nearest')[0]
expected_pic_time = prices_series.index[expected_pic_idx]
expected_pic_price = prices_series.iloc[expected_pic_idx]

print(f'Pic attendu : {expected_pic_time.strftime("%Y-%m-%d %H:%M")} (index {expected_pic_idx}, prix {expected_pic_price:.5f})')
print()

# Simuler la logique de détection des maximums locaux autour de 08:00 le 09.09
target_hour = 8
day_offset = 2  # 2 jours avant l'événement = 09.09
candidate_dt = event_date - pd.Timedelta(days=day_offset)
candidate_dt = candidate_dt.replace(hour=target_hour, minute=0, second=0)
candidate_idx = prices_series.index.get_indexer([candidate_dt], method='nearest')[0]
candidate_time = prices_series.index[candidate_idx]

print(f'Cherchant autour de {candidate_time.strftime("%Y-%m-%d %H:%M")} (08:00 le 09.09)')
print(f'Index candidat : {candidate_idx}')
print()

# Fenêtre de 24h centrée (12h avant, 12h après)
window_start = max(0, candidate_idx - 720)  # 12h avant
window_end = min(len(prices_series) - 1, candidate_idx + 720)  # 12h après
window_24h = prices_series.iloc[window_start:window_end + 1]

print(f'Fenêtre de recherche : {prices_series.index[window_start].strftime("%Y-%m-%d %H:%M")} → {prices_series.index[window_end].strftime("%Y-%m-%d %H:%M")}')
print(f'   ({window_end - window_start + 1} points)')
print()

if len(window_24h) > 0:
    max_24h_idx = window_24h.idxmax()
    max_24h_pos = prices_series.index.get_loc(max_24h_idx)
    max_24h_price = prices_series.iloc[max_24h_pos]
    max_24h_time = prices_series.index[max_24h_pos]
    
    print(f'✅ Maximum trouvé dans cette fenêtre :')
    print(f'   Date/Heure : {max_24h_time.strftime("%Y-%m-%d %H:%M")}')
    print(f'   Index : {max_24h_pos}')
    print(f'   Prix : {max_24h_price:.5f}')
    print()
    
    # Vérifier si c'est le pic attendu
    if abs(max_24h_pos - expected_pic_idx) < 10:  # Tolérance de 10 minutes
        print(f'✅ Le maximum trouvé correspond au pic attendu !')
    else:
        print(f'⚠️  Le maximum trouvé ({max_24h_time.strftime("%H:%M")}) ne correspond PAS au pic attendu (05:55)')
        print(f'   Différence : {abs(max_24h_pos - expected_pic_idx)} minutes')
        print()
        print(f'   Prix à 05:55 : {expected_pic_price:.5f}')
        print(f'   Prix max trouvé : {max_24h_price:.5f}')
        print(f'   Différence prix : {abs(max_24h_price - expected_pic_price):.5f}')


