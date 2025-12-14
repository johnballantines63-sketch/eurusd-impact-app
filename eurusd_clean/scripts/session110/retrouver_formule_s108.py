"""
RETROUVER LA FORMULE SESSION 108
"""
import pandas as pd
import numpy as np
from scipy.stats import linregress
from pathlib import Path

# Charger CSV Session 108
scripts_dir = Path(__file__).parent.parent
calib_file = scripts_dir / "session108" / "calibration_inversion_17dates.csv"
df = pd.read_csv(calib_file)

print("="*80)
print("FORMULE SESSION 108 - RÉGRESSION R² INVERSION")
print("="*80)

# Régression : amp_inversion = slope × r2_inversion + intercept
X = df['r2_inversion'].values
y = df['amp_inversion'].values

slope, intercept, r_value, p_value, std_err = linregress(X, y)

print(f"\n📊 FORMULE CALIBRÉE SESSION 108 :")
print(f"\n   amp = {slope:.4f} × R²_inversion + {intercept:.4f}")
print(f"\n📊 STATISTIQUES :")
print(f"   R² = {r_value**2:.4f}")
print(f"   r  = {r_value:+.4f}")
print(f"   p  = {p_value:.4f}")

# Vérifions sur amp_optimal
X2 = df['r2_inversion'].values  
y2 = df['amp_optimal'].values

slope2, intercept2, r_value2, p_value2, std_err2 = linregress(X2, y2)

print(f"\n📊 VÉRIFICATION SUR AMP_OPTIMAL :")
print(f"\n   amp = {slope2:.4f} × R²_inversion + {intercept2:.4f}")
print(f"\n📊 STATISTIQUES :")
print(f"   R² = {r_value2**2:.4f}")
print(f"   r  = {r_value2:+.4f}")
print(f"   p  = {p_value2:.4f}")

print("\n" + "="*80)
print("TEST SUR 11.09.2025")
print("="*80)

row_11sept = df[df['date'] == '2025-09-11'].iloc[0]
r2_11sept = row_11sept['r2_inversion']
amp_optimal_11sept = row_11sept['amp_optimal']

amp_predit = slope2 * r2_11sept + intercept2

print(f"\nDate : 2025-09-11")
print(f"R² inversion : {r2_11sept:.4f}")
print(f"amp_optimal  : {amp_optimal_11sept:.4f}")
print(f"amp_prédit   : {amp_predit:.4f}")
print(f"Erreur       : {abs(amp_optimal_11sept - amp_predit):.4f}")

print("\n" + "="*80)
