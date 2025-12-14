#!/usr/bin/env python3
"""
Script principal Session 131 - Vérifications et Analyses
Exécute:
1. Vérification JSON vs DB
2. Analyse cluster US isolé
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

print(f"\n{'#'*80}")
print(f"# SESSION 131 - VÉRIFICATIONS ET ANALYSES")
print(f"{'#'*80}\n")

# 1. Vérification JSON vs DB
print(f"\n{'='*80}")
print(f"ÉTAPE 1/2 - VÉRIFICATION JSON vs DB")
print(f"{'='*80}\n")

script1 = BASE_DIR / "verify_db_vs_json.py"
result1 = subprocess.run([sys.executable, str(script1)], capture_output=True, text=True)
print(result1.stdout)
if result1.stderr:
    print(f"ERREURS:\n{result1.stderr}")

# 2. Analyse cluster US isolé
print(f"\n{'='*80}")
print(f"ÉTAPE 2/2 - ANALYSE CLUSTER US ISOLÉ")
print(f"{'='*80}\n")

script2 = BASE_DIR / "analyze_us_cluster_isolated.py"
result2 = subprocess.run([sys.executable, str(script2)], capture_output=True, text=True)
print(result2.stdout)
if result2.stderr:
    print(f"ERREURS:\n{result2.stderr}")

print(f"\n{'#'*80}")
print(f"# FIN DES ANALYSES SESSION 131")
print(f"{'#'*80}\n")
