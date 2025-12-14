"""
Comparer les scores des segments commençant à 05:55 vs 11:38
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
from core.trend_detection_pre_event import prepare_price_series, linear_regression_segment
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

# Préparer série
y = prepare_price_series(prices_series, use_log=True, denoise=False)

# Pic attendu à 05:55 le 09.09
expected_pic = tz.localize(datetime(2025, 9, 9, 5, 55))
expected_pic_idx = prices_series.index.get_indexer([expected_pic], method='nearest')[0]

# Segment détecté à 11:38 le 11.09
detected_start = tz.localize(datetime(2025, 9, 11, 11, 38))
detected_start_idx = prices_series.index.get_indexer([detected_start], method='nearest')[0]

print('='*80)
print('COMPARAISON DES SEGMENTS')
print('='*80)
print(f'Événement : {event_time.strftime("%Y-%m-%d %H:%M")} (index {event_idx})')
print()

# Segment 1 : 05:55 → 14:30
segment1_y = y.iloc[expected_pic_idx:event_idx + 1].values
x1 = np.arange(len(segment1_y))
reg1 = linear_regression_segment(segment1_y, x1)
length1 = len(segment1_y)
distance1 = event_idx - expected_pic_idx

length_bonus1 = min(0.5, (length1 / 2880.0) * 0.5) if length1 >= 1440 else 0.0
if distance1 >= 2880:
    early_bonus1 = 0.8
elif distance1 >= 1440:
    early_bonus1 = 0.5
elif distance1 >= 720:
    early_bonus1 = 0.2
else:
    early_bonus1 = 0.0
peak_bonus1 = 0.3  # Supposons que c'est un pic détecté
score1 = reg1['r2'] * (1 + length_bonus1 + early_bonus1 + peak_bonus1)

print(f'SEGMENT 1 : 05:55 → 14:30')
print(f'   Début : {prices_series.index[expected_pic_idx].strftime("%Y-%m-%d %H:%M")} (index {expected_pic_idx})')
print(f'   Durée : {length1} minutes ({length1/60:.1f} heures)')
print(f'   Distance depuis événement : {distance1} minutes ({distance1/60:.1f} heures)')
print(f'   R² : {reg1["r2"]:.4f}')
print(f'   Slope : {reg1["slope"]:.6f}')
print(f'   Length bonus : {length_bonus1:.3f}')
print(f'   Early bonus : {early_bonus1:.3f}')
print(f'   Peak bonus : {peak_bonus1:.3f}')
print(f'   SCORE FINAL : {score1:.4f}')
print()

# Segment 2 : 11:38 → 14:30
segment2_y = y.iloc[detected_start_idx:event_idx + 1].values
x2 = np.arange(len(segment2_y))
reg2 = linear_regression_segment(segment2_y, x2)
length2 = len(segment2_y)
distance2 = event_idx - detected_start_idx

length_bonus2 = min(0.5, (length2 / 2880.0) * 0.5) if length2 >= 1440 else 0.0
if distance2 >= 2880:
    early_bonus2 = 0.8
elif distance2 >= 1440:
    early_bonus2 = 0.5
elif distance2 >= 720:
    early_bonus2 = 0.2
else:
    early_bonus2 = 0.0
peak_bonus2 = 0.0  # Pas un pic détecté
score2 = reg2['r2'] * (1 + length_bonus2 + early_bonus2 + peak_bonus2)

print(f'SEGMENT 2 : 11:38 → 14:30')
print(f'   Début : {prices_series.index[detected_start_idx].strftime("%Y-%m-%d %H:%M")} (index {detected_start_idx})')
print(f'   Durée : {length2} minutes ({length2/60:.1f} heures)')
print(f'   Distance depuis événement : {distance2} minutes ({distance2/60:.1f} heures)')
print(f'   R² : {reg2["r2"]:.4f}')
print(f'   Slope : {reg2["slope"]:.6f}')
print(f'   Length bonus : {length_bonus2:.3f}')
print(f'   Early bonus : {early_bonus2:.3f}')
print(f'   Peak bonus : {peak_bonus2:.3f}')
print(f'   SCORE FINAL : {score2:.4f}')
print()

if score1 > score2:
    print(f'✅ Segment 1 (05:55) devrait être sélectionné (score {score1:.4f} > {score2:.4f})')
else:
    print(f'⚠️  Segment 2 (11:38) est sélectionné car score {score2:.4f} > {score1:.4f}')
    print(f'   Différence : {score2 - score1:.4f}')
    print()
    print(f'   Pour que Segment 1 soit sélectionné, il faudrait :')
    print(f'   - Augmenter R² de {reg1["r2"]:.4f} à {score2 / (1 + length_bonus1 + early_bonus1 + peak_bonus1):.4f}')
    print(f'   - OU augmenter les bonus pour compenser la différence de R²')


