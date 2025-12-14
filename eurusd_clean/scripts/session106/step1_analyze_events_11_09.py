#!/usr/bin/env python3
"""
SESSION 106 - ÉTAPE 1 : ANALYSE ÉVÉNEMENTS 11.09.2025
======================================================

Objectif : Analyser les 11 événements CPI pour comprendre
comment construire la formule score_adjusted

Cible : Obtenir score_adjusted = 84.2

Auteur : André Valentin + Claude
Date   : 2 novembre 2025
Phase  : Développement formule (Option C)
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
import importlib.util

print("="*80)
print("SESSION 106 - ÉTAPE 1 : ANALYSE ÉVÉNEMENTS 11.09.2025")
print("="*80)
print()

# Setup
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Config
spec_config = importlib.util.spec_from_file_location(
    "config",
    project_root / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
Config = config_module.Config

config = Config()
db_path = config.get_db_path()

print(f"📂 Database : {db_path}")
print()

# Charger événements 11.09
DATE = '2025-09-11'

query = """
SELECT 
    e.event_key,
    e.actual,
    e.estimate,
    ef.empirical_score,
    ef.family
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
  AND DATE(e.ts_utc) = '2025-09-11'
  AND ef.empirical_score > 40
ORDER BY ef.empirical_score DESC
"""

print("📊 Chargement événements 11.09.2025...")

with duckdb.connect(str(db_path), read_only=True) as conn:
    events_df = conn.execute(query).fetchdf()

print(f"✅ {len(events_df)} événements chargés")
print()

# Calculer surprises
events_df['surprise'] = abs(
    (events_df['actual'] - events_df['estimate']) / events_df['estimate']
)

# Afficher tableau complet
print("="*80)
print("TABLEAU ÉVÉNEMENTS 11.09.2025")
print("="*80)
print()

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 30)

print(events_df.to_string(index=False))
print()

# Statistiques
print("="*80)
print("STATISTIQUES")
print("="*80)
print()

print(f"Nombre événements     : {len(events_df)}")
print(f"Score empirique moyen : {events_df['empirical_score'].mean():.2f}")
print(f"Score empirique max   : {events_df['empirical_score'].max():.2f}")
print(f"Score empirique min   : {events_df['empirical_score'].min():.2f}")
print(f"Score empirique σ     : {events_df['empirical_score'].std():.2f}")
print()

print(f"Surprise moyenne      : {events_df['surprise'].mean():.2%}")
print(f"Surprise max          : {events_df['surprise'].max():.2%}")
print(f"Surprise min          : {events_df['surprise'].min():.2%}")
print(f"Surprise σ            : {events_df['surprise'].std():.2%}")
print()

# Identifier événements dominants
print("="*80)
print("ÉVÉNEMENTS DOMINANTS")
print("="*80)
print()

# Top 3 scores
print("🏆 TOP 3 SCORES :")
top_scores = events_df.nlargest(3, 'empirical_score')
for idx, row in top_scores.iterrows():
    print(f"  {row['event_key']:30s} : score={row['empirical_score']:5.1f}, surprise={row['surprise']:6.2%}")
print()

# Top 3 surprises
print("🔥 TOP 3 SURPRISES :")
top_surprises = events_df.nlargest(3, 'surprise')
for idx, row in top_surprises.iterrows():
    print(f"  {row['event_key']:30s} : surprise={row['surprise']:6.2%}, score={row['empirical_score']:5.1f}")
print()

# Corrélation score vs surprise
corr = events_df['empirical_score'].corr(events_df['surprise'])
print(f"📊 Corrélation score ↔ surprise : {corr:+.3f}")
print()

# Distribution familles
print("="*80)
print("DISTRIBUTION FAMILLES")
print("="*80)
print()

family_counts = events_df['family'].value_counts()
for family, count in family_counts.items():
    avg_score = events_df[events_df['family'] == family]['empirical_score'].mean()
    print(f"{family:20s} : {count} événements, score moyen={avg_score:.1f}")
print()

# Objectif
print("="*80)
print("OBJECTIF CALIBRATION")
print("="*80)
print()

print(f"🎯 score_adjusted attendu : 84.2")
print(f"📊 Score moyen actuel     : {events_df['empirical_score'].mean():.2f}")
print(f"📈 Écart                  : {84.2 - events_df['empirical_score'].mean():.2f}")
print()

amplification_needed = 84.2 / events_df['empirical_score'].mean()
print(f"💡 Amplification nécessaire : {amplification_needed:.3f}×")
print()

# Sauvegarder
output_csv = Path(__file__).parent / 'events_11_09_analysis.csv'
events_df.to_csv(output_csv, index=False)

output_json = Path(__file__).parent / 'events_11_09_analysis.json'
events_df.to_json(output_json, orient='records', indent=2)

print("💾 Données sauvegardées :")
print(f"   - {output_csv.name}")
print(f"   - {output_json.name}")
print()

print("="*80)
print("✅ ÉTAPE 1 COMPLÉTÉE - ANALYSE TERMINÉE")
print("="*80)
print()
print("📋 PROCHAINE ÉTAPE : Tester formulations (Étape 2)")
