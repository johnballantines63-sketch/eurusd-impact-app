#!/usr/bin/env python3
"""
Wrapper pour exécuter scanner Session 75
"""

import subprocess
import sys

print("Exécution scanner Session 75...")
print("="*70)

result = subprocess.run(
    [sys.executable, 'scanner_movements_session75.py'],
    capture_output=True,
    text=True
)

print(result.stdout)

if result.stderr:
    print("\n=== STDERR ===")
    print(result.stderr)

print(f"\nReturn code: {result.returncode}")

sys.exit(result.returncode)
