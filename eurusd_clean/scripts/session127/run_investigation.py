"""
SESSION 127 - Exécution Investigation Scores Manquants
Wrapper pour exécuter investigate_missing_scores.py
"""

import sys
from pathlib import Path

# Ajouter répertoire scripts au path
sys.path.insert(0, str(Path(__file__).parent))

# Importer et exécuter
from investigate_missing_scores import main

if __name__ == "__main__":
    main()
