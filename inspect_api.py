#!/usr/bin/env python3
"""Inspecte les méthodes disponibles dans ScoringEngine"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path("fx_impact_app/src")))

from config import get_db_path
from scoring_engine import ScoringEngine

print("🔍 Méthodes disponibles dans ScoringEngine:")
print()

engine = ScoringEngine(get_db_path())

methods = [m for m in dir(engine) if not m.startswith('_')]
for method in methods:
    print(f"  - {method}")

print()
print("💡 Utilisez la bonne méthode pour calculer les scores")
engine.close()
