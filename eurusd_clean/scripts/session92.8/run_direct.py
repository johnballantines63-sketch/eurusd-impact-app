#!/usr/bin/env python3
"""Exécution directe tests Session 92.12"""

import os
import sys

# Changer vers le bon répertoire
script_dir = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session92.8'
os.chdir(script_dir)
sys.path.insert(0, script_dir)

# Importer et exécuter
print("Démarrage tests Session 92.12...")
print("="*80)

try:
    from execute_test_WEIGHTED import main
    
    # Exécuter
    df_results = main()
    
    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
