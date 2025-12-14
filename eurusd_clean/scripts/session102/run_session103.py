#!/usr/bin/env python3
"""
Script exécution Session 103 - Test SOLUTION #1
"""

import subprocess
import sys
from pathlib import Path

print("=" * 80)
print("SESSION 103 - TEST SOLUTION #1 : Calcul amplitude max-min")
print("=" * 80)
print()
print("Modification effectuée :")
print("  ❌ AVANT : abs(price_end - price_start)")
print("  ✅ APRÈS : max(segment) - min(segment)")
print()
print("Lancement calibration...")
print("=" * 80)
print()

# Exécuter calibration
script_dir = Path(__file__).parent
result = subprocess.run(
    ["python3", "calibrate_amp_formula.py"],
    cwd=script_dir,
    capture_output=False,  # Afficher sortie en direct
    text=True
)

sys.exit(result.returncode)
