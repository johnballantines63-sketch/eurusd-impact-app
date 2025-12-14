#!/usr/bin/env python3
"""
Exécution complète Pipeline Session 75
Phase 1 : Scanner stratifié
Phase 2 : Dataset avec événements
Phase 3 : Analyse ML
"""

import sys
import os
from pathlib import Path

# Chemins
fx_impact_app_path = Path(__file__).parent.parent
scripts_path = fx_impact_app_path / "scripts"

print("\n" + "="*70)
print("PIPELINE COMPLET SESSION 75")
print("="*70 + "\n")

# Phase 1 : Scanner stratifié
print("🔍 PHASE 1 : Scanner mouvements stratifié")
print("-" * 70)

os.chdir(str(scripts_path))
exit_code = os.system("python3 scanner_movements_session75.py")

if exit_code != 0:
    print(f"\n❌ Erreur Phase 1 (code {exit_code})")
    sys.exit(1)

print("\n✅ Phase 1 complétée")

# Vérifier output Phase 1
output_csv = fx_impact_app_path / "data" / "movements_strong_session75_stratified.csv"
if output_csv.exists():
    import pandas as pd
    df = pd.read_csv(output_csv)
    print(f"   Fichier créé : {output_csv.name}")
    print(f"   Mouvements : {len(df)}")
    print(f"   Dates uniques : {df['date'].nunique()}")
else:
    print(f"❌ Fichier output non créé : {output_csv}")
    sys.exit(1)

# Phase 2 : Dataset avec événements
print(f"\n🔍 PHASE 2 : Créer dataset avec événements")
print("-" * 70)

# Modifier temporairement create_dataset pour utiliser nouveau CSV
# Note : On va créer une copie adaptée

print("   📝 Note : Utiliser create_dataset_session73_FIXED.py")
print("   📝 Modifier input CSV vers movements_strong_session75_stratified.csv")
print("   ⏭️  Phase 2 à exécuter manuellement (modification CSV input nécessaire)")

print(f"\n{'='*70}")
print("PHASE 1 COMPLÉTÉE AVEC SUCCÈS")
print("="*70)
print("\n📊 Prochaines étapes :")
print("   1. Vérifier dataset : movements_strong_session75_stratified.csv")
print("   2. Modifier create_dataset_session73_FIXED.py (ligne input CSV)")
print("   3. Exécuter create_dataset_session73_FIXED.py")
print("   4. Exécuter analyze_correlations_session73_FIXED.py")
