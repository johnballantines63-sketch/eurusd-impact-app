#!/usr/bin/env python3
"""
Wrapper pour exécuter test Session 92.9
"""
import sys
from pathlib import Path

# Ajouter le répertoire au path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Importer et exécuter
from execute_test_complet import main

if __name__ == "__main__":
    main()
