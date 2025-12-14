#!/usr/bin/env python3
"""
Runner pour list_available_dates.py - Session 91.2
Exécute le script et capture les résultats
"""

import subprocess
import sys
from pathlib import Path

script_dir = Path(__file__).parent
list_dates_script = script_dir / "list_available_dates.py"

print("🚀 Exécution de list_available_dates.py...\n")

# Exécuter le script
result = subprocess.run(
    [sys.executable, str(list_dates_script)],
    capture_output=True,
    text=True
)

# Afficher la sortie
print(result.stdout)

if result.stderr:
    print("⚠️ Erreurs:\n", result.stderr)

# Vérifier le succès
if result.returncode == 0:
    print("\n✅ Script exécuté avec succès !")
else:
    print(f"\n❌ Erreur d'exécution (code: {result.returncode})")
    sys.exit(1)
