#!/usr/bin/env python3
"""
Rend les scripts shell exécutables
"""
import os
from pathlib import Path

def make_executable():
    script_dir = Path(__file__).parent
    shell_scripts = list(script_dir.glob("*.sh"))
    
    for script in shell_scripts:
        os.chmod(script, 0o755)
        print(f"✅ {script.name} est maintenant exécutable")
    
    if shell_scripts:
        print(f"\n✅ {len(shell_scripts)} script(s) rendu(s) exécutable(s)")
    else:
        print("⚠️  Aucun script shell trouvé")

if __name__ == "__main__":
    make_executable()
