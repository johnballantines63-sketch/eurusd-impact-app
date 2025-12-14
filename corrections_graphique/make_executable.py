#!/usr/bin/env python3
"""
Script simple pour rendre run_full_fix.sh exécutable
"""
import os
import stat
from pathlib import Path

script_path = Path(__file__).parent / "run_full_fix.sh"

# Rendre exécutable
current_permissions = os.stat(script_path)
os.chmod(script_path, current_permissions.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

print(f"✅ {script_path.name} est maintenant exécutable")
print(f"\nLancez-le avec :")
print(f"  cd {script_path.parent}")
print(f"  ./run_full_fix.sh")
