"""
CALCUL CORRÉLATION R² vs AMP (30 DATES)
========================================
"""

import pandas as pd
import numpy as np

df = pd.read_csv('recalibration_30_dates_results.csv')

x = df['r_squared_72h'].values
y = df['amp_optimal'].values

# Corrélation Pearson
corr = np.corrcoef(x, y)[0, 1]

print(f"Corrélation R² vs Amp Optimale (30 dates) : {corr:.3f}")
print(f"\nComparaison :")
print(f"  S98 (10 dates)  : 0.472")
print(f"  S99 (20 dates)  : ~0.37")
print(f"  S99-EXT (30 dates) : {corr:.3f}")

# Régression
x_mean = np.mean(x)
y_mean = np.mean(y)
a = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
b = y_mean - a * x_mean

print(f"\nFormule : amp = {a:.4f} × R² + {b:.4f}")

# Distribution
print(f"\nDistribution Amp Optimale :")
print(f"  Min     : {y.min():.3f}")
print(f"  Q1      : {np.percentile(y, 25):.3f}")
print(f"  Médiane : {np.median(y):.3f}")
print(f"  Q3      : {np.percentile(y, 75):.3f}")
print(f"  Max     : {y.max():.3f}")
print(f"  Moyenne : {y.mean():.3f}")

# Dates à la borne
borne_inf = (y <= 0.51).sum()
borne_sup = (y >= 4.99).sum()

print(f"\nDates borne inférieure (0.5) : {borne_inf}/30 ({borne_inf/30*100:.1f}%)")
print(f"Dates borne supérieure (5.0) : {borne_sup}/30 ({borne_sup/30*100:.1f}%)")

# Outlier contre-intuitif
df_outlier = df[(df['r_squared_72h'] > 0.7) & (df['amp_optimal'] <= 0.51)]
if len(df_outlier) > 0:
    print(f"\n⚠️  ANOMALIES (R² élevé + Amp basse) :")
    for _, row in df_outlier.iterrows():
        print(f"  {row['date']} : R²={row['r_squared_72h']:.3f}, Amp={row['amp_optimal']:.3f}, Impact={row['impact_real']:.1f} pips")
