#!/usr/bin/env python3
"""
EXÉCUTION RAPIDE PIPELINE SESSION 75
À exécuter depuis terminal :
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts
python3 exec_pipeline_session75.py
"""

import subprocess
import sys

print("\n" + "="*80)
print("EXÉCUTION PIPELINE SESSION 75")
print("="*80 + "\n")

try:
    # Exécuter pipeline complet
    result = subprocess.run(
        [sys.executable, 'pipeline_complete_session75.py'],
        check=True,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if result.stderr:
        print("\n⚠️  Warnings/Errors:")
        print(result.stderr)
    
    print("\n✅ Pipeline complété avec succès!")
    
except subprocess.CalledProcessError as e:
    print(f"\n❌ Erreur d'exécution (code {e.returncode}):")
    print(e.stdout)
    print(e.stderr)
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    sys.exit(1)
