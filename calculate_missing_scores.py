#!/usr/bin/env python3
"""
Script wrapper pour calculer les métriques empiriques manquantes
"""

import sys
import os

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fx_impact_app', 'src'))

from calculate_missing_empirical_scores import calculate_missing_scores

if __name__ == "__main__":
    # Vérifier les arguments
    all_events = '--all' in sys.argv
    
    print()
    print("🚀 Lancement du calcul des métriques empiriques...")
    print()
    
    if all_events:
        print("Mode: TOUS les événements sans score")
    else:
        print("Mode: Événements HIGH prioritaires seulement")
        print("      (utilisez --all pour calculer tous les événements)")
    
    print()
    
    calculate_missing_scores(priority_only=not all_events)
