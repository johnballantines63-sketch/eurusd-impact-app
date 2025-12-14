"""
ANALYSE ROBUSTESSE CALCULS DIRECTS
===================================
"""

import pandas as pd
import numpy as np

# Charger données
df_recalib = pd.read_csv('recalibration_20_dates_results.csv')

# Corrélation R² vs Amp Optimale
x = df_recalib['r_squared_72h'].values
y = df_recalib['amp_optimal'].values

corr = np.corrcoef(x, y)[0, 1]

print(f"Corrélation R² vs Amp Optimale : {corr:.3f}")

# Distribution amplifications
print(f"\nAmplifications optimales :")
print(f"  Min  : {y.min():.3f}")
print(f"  Max  : {y.max():.3f}")
print(f"  Mean : {y.mean():.3f}")
print(f"  Med  : {np.median(y):.3f}")

# Dates à la borne
borne_inf = (y <= 0.51).sum()
borne_sup = (y >= 4.99).sum()

print(f"\nDates borne inférieure (0.5) : {borne_inf}/20")
print(f"Dates borne supérieure (5.0) : {borne_sup}/20")
