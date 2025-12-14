#!/usr/bin/env python3
"""
Wrapper exécution tests Session 92.12
Capture output et erreurs
"""

import subprocess
import sys
from pathlib import Path

script_dir = Path(__file__).parent
test_script = script_dir / 'execute_test_WEIGHTED.py'

print("="*80)
print("EXÉCUTION TESTS SESSION 92.12 - SCORE PONDÉRÉ")
print("="*80)
print(f"\nScript : {test_script}")
print(f"Working dir : {script_dir}")
print("\nDémarrage tests...")
print("="*80)

try:
    result = subprocess.run(
        [sys.executable, str(test_script)],
        cwd=str(script_dir),
        capture_output=True,
        text=True,
        timeout=120
    )
    
    print(result.stdout)
    
    if result.stderr:
        print("\n" + "="*80)
        print("STDERR:")
        print("="*80)
        print(result.stderr)
    
    if result.returncode == 0:
        print("\n" + "="*80)
        print("✅ TESTS TERMINÉS AVEC SUCCÈS")
        print("="*80)
    else:
        print("\n" + "="*80)
        print(f"❌ ERREUR - Code retour: {result.returncode}")
        print("="*80)
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("\n" + "="*80)
    print("⏱️  TIMEOUT - Tests trop longs (>120s)")
    print("="*80)
    sys.exit(1)
    
except Exception as e:
    print("\n" + "="*80)
    print(f"💥 EXCEPTION: {e}")
    print("="*80)
    sys.exit(1)
