"""
VÉRIFICATION RAPIDE SESSION 109
"""
import pandas as pd
import numpy as np
from pathlib import Path

scripts_dir = Path(__file__).parent.parent
phase1_file = scripts_dir / "session109" / "phase1_all_metrics_17dates.csv"
df = pd.read_csv(phase1_file)

# Baselines
baseline_c1 = 1.451
baseline_c3 = 2.545
df['baseline'] = df['cluster'].map({1: baseline_c1, 3: baseline_c3})

# Écarts réels
df['ecart_reel'] = df['amp_optimal'] - df['baseline']

# Écarts prédits
SLOPE = 0.0166
INTERCEPT = -0.9878
df['ecart_predit'] = SLOPE * df['duration_hours'] + INTERCEPT

# Baseline = ZÉRO pour les écarts !
mae_baseline_ecarts = df['ecart_reel'].abs().mean()
mae_dynamic_ecarts = (df['ecart_reel'] - df['ecart_predit']).abs().mean()
improvement = ((mae_baseline_ecarts - mae_dynamic_ecarts) / mae_baseline_ecarts) * 100

print(f"MAE Baseline (mean |écarts|) : {mae_baseline_ecarts:.3f}")
print(f"MAE Dynamic                   : {mae_dynamic_ecarts:.3f}")
print(f"Amélioration                  : {improvement:+.1f}%")
print(f"\nAttendu Session 109 : +70.3%")
print(f"Différence : {abs(improvement - 70.3):.1f}%")
