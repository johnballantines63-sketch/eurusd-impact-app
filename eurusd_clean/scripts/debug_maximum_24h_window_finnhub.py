"""
Debug : Vérifier si le pic à 07:00 est détecté dans la fenêtre 24h
"""
import sys
from pathlib import Path
from datetime import datetime
import pytz
import pandas as pd

sys.path.insert(0, 'src')
from config import DB_PATH
import duckdb

tz = pytz.timezone('Europe/Zurich')
event_date = tz.localize(datetime(2025, 9, 11, 14, 30))

# Charger prix H1
conn = duckdb.connect(str(DB_PATH))
query = f'''
SELECT datetime, open, high, low, close
FROM prices_h1
WHERE datetime >= '{event_date - pd.Timedelta(days=3)}'
  AND datetime <= '{event_date + pd.Timedelta(hours=1)}'
ORDER BY datetime
'''
df = conn.execute(query).df()
conn.close()

df['datetime'] = pd.to_datetime(df['datetime'])
if df['datetime'].dt.tz is None:
    df['datetime'] = df['datetime'].dt.tz_localize('Europe/Zurich')
else:
    df['datetime'] = df['datetime'].dt.tz_convert('Europe/Zurich')

df = df.set_index('datetime')
prices_series = df['close']

# Trouver index événement
event_idx = prices_series.index.get_indexer([event_date], method='nearest')[0]

# Simuler la recherche du maximum dans fenêtre 24h centrée sur 08:00 le 09.09
target_hour = 8
day_offset = 2  # 2 jours avant = 09.09
candidate_dt = event_date - pd.Timedelta(days=day_offset)
candidate_dt = candidate_dt.replace(hour=target_hour, minute=0, second=0)
candidate_idx = prices_series.index.get_indexer([candidate_dt], method='nearest')[0]
candidate_time = prices_series.index[candidate_idx]

print(f'Cherchant autour de {candidate_time.strftime("%Y-%m-%d %H:%M")} (08:00 le 09.09)')
print(f'Index candidat : {candidate_idx}')
print()

# Fenêtre de 24h centrée (12h avant, 12h après) = 12 bougies H1
window_24h_bars = 12
window_start = max(0, candidate_idx - window_24h_bars)
window_end = min(len(prices_series) - 1, candidate_idx + window_24h_bars)
window_24h = prices_series.iloc[window_start:window_end + 1]

print(f'Fenêtre de recherche : {prices_series.index[window_start].strftime("%Y-%m-%d %H:%M")} → {prices_series.index[window_end].strftime("%Y-%m-%d %H:%M")}')
print(f'   ({window_end - window_start + 1} bougies H1)')
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
    
    # Vérifier si c'est le pic attendu (07:00 ou 08:00)
    expected_07 = tz.localize(datetime(2025, 9, 9, 7, 0))
    expected_08 = tz.localize(datetime(2025, 9, 9, 8, 0))
    expected_07_idx = prices_series.index.get_indexer([expected_07], method='nearest')[0]
    expected_08_idx = prices_series.index.get_indexer([expected_08], method='nearest')[0]
    
    if abs(max_24h_pos - expected_07_idx) < 2:
        print(f'✅ Le maximum trouvé correspond au pic à 07:00 !')
    elif abs(max_24h_pos - expected_08_idx) < 2:
        print(f'✅ Le maximum trouvé correspond au pic à 08:00 !')
    else:
        print(f'⚠️  Le maximum trouvé ({max_24h_time.strftime("%H:%M")}) ne correspond PAS aux pics attendus (07:00 ou 08:00)')
        print(f'   Pic à 07:00 : index {expected_07_idx}, prix {prices_series.iloc[expected_07_idx]:.5f}')
        print(f'   Pic à 08:00 : index {expected_08_idx}, prix {prices_series.iloc[expected_08_idx]:.5f}')


