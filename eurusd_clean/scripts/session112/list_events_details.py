#!/usr/bin/env python3
"""
LISTE DÉTAILLÉE DES ÉVÉNEMENTS 11 SEPTEMBRE 2025
=================================================

Affiche tous les événements retenus avec leurs détails complets
pour analyse manuelle par André.
"""

import duckdb
import pandas as pd
from pathlib import Path

db_path = Path(__file__).parent.parent.parent / "app" / "data" / "warehouse.duckdb"

print("="*80)
print("📋 LISTE DÉTAILLÉE ÉVÉNEMENTS 11 SEPTEMBRE 2025 - 14:30")
print("="*80)

con = duckdb.connect(str(db_path), read_only=True)

# Requête DÉDUPLIQUÉE (DISTINCT ON event_key)
query = """
SELECT DISTINCT ON (e.event_key)
    e.event_key,
    e.event_title,
    COALESCE(e.event_title, e.event_key) as display_name,
    e.country,
    e.actual,
    e.estimate,
    e.previous,
    e.importance_n,
    ef.empirical_score,
    ef.latency_median,
    ef.avg_movement_pips,
    ef.sample_size
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key
WHERE e.ts_utc = '2025-09-11 14:30:00+02:00'
  AND e.estimate IS NOT NULL
  AND e.actual IS NOT NULL
  AND ef.empirical_score IS NOT NULL
ORDER BY e.event_key, ef.empirical_score DESC NULLS LAST
"""

df = con.execute(query).df()

print(f"\n📊 Total événements retenus: {len(df)}")
print(f"📊 Event_key uniques: {df['event_key'].nunique()}")

print("\n" + "="*80)
print("DÉTAILS PAR ÉVÉNEMENT")
print("="*80)

# Configurer pandas pour affichage complet
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

for i, row in df.iterrows():
    print(f"\n{i+1}. {row['display_name']}")
    print("-" * 80)
    print(f"   event_key:        {row['event_key']}")
    print(f"   event_title:      {row['event_title']}")
    print(f"   country:          {row['country']}")
    print(f"   importance:       {row['importance_n']}")
    print(f"   ")
    print(f"   actual:           {row['actual']}")
    print(f"   estimate:         {row['estimate']}")
    print(f"   previous:         {row['previous']}")
    print(f"   surprise:         {abs((row['actual'] - row['estimate']) / row['estimate'] * 100):.2f}%" if pd.notna(row['estimate']) and abs(row['estimate']) > 0.01 else "   surprise:         N/A")
    print(f"   ")
    print(f"   empirical_score:  {row['empirical_score']:.2f}")
    print(f"   latency_median:   {row['latency_median']}" if pd.notna(row['latency_median']) else f"   latency_median:   None")
    print(f"   avg_movement:     {row['avg_movement_pips']:.2f} pips" if pd.notna(row['avg_movement_pips']) else f"   avg_movement:     None")
    print(f"   sample_size:      {row['sample_size']}" if pd.notna(row['sample_size']) else f"   sample_size:      None")

# Statistiques globales
print("\n" + "="*80)
print("STATISTIQUES GLOBALES")
print("="*80)

print(f"\n📊 Scores empiriques:")
print(f"   Moyenne:  {df['empirical_score'].mean():.2f}")
print(f"   Médiane:  {df['empirical_score'].median():.2f}")
print(f"   Min:      {df['empirical_score'].min():.2f}")
print(f"   Max:      {df['empirical_score'].max():.2f}")

# Calculer surprises
surprises = []
for _, row in df.iterrows():
    if pd.notna(row['actual']) and pd.notna(row['estimate']) and abs(row['estimate']) > 0.01:
        surprise = abs((row['actual'] - row['estimate']) / row['estimate']) * 100
        surprises.append(surprise)

if surprises:
    import numpy as np
    print(f"\n📊 Surprises:")
    print(f"   Moyenne:  {np.mean(surprises):.2f}%")
    print(f"   Médiane:  {np.median(surprises):.2f}%")
    print(f"   Min:      {min(surprises):.2f}%")
    print(f"   Max:      {max(surprises):.2f}%")

# Distribution par importance
print(f"\n📊 Distribution par importance:")
importance_dist = df['importance_n'].value_counts().sort_index()
for imp, count in importance_dist.items():
    imp_label = "HIGH" if imp == 1 else "MEDIUM" if imp == 2 else "LOW" if imp == 3 else "N/A"
    print(f"   {imp_label:10s} ({imp}): {count} événements")

# Événements avec importance NULL
null_imp = df[df['importance_n'].isna()]
if len(null_imp) > 0:
    print(f"   NULL/NaN:          {len(null_imp)} événements")

# Vérifier doublons potentiels
print(f"\n⚠️  Doublons potentiels:")
# Chercher des event_key très similaires
print(f"   CPI variations:")
cpi_events = df[df['event_key'].str.contains('cpi', case=False, na=False)]
for _, row in cpi_events.iterrows():
    print(f"      - {row['event_key']}: score={row['empirical_score']:.2f}")

print(f"\n   Inflation variations:")
inf_events = df[df['event_key'].str.contains('inflation', case=False, na=False)]
for _, row in inf_events.iterrows():
    print(f"      - {row['event_key']}: score={row['empirical_score']:.2f}")

print(f"\n   Jobless variations:")
job_events = df[df['event_key'].str.contains('jobless', case=False, na=False)]
for _, row in job_events.iterrows():
    print(f"      - {row['event_key']}: score={row['empirical_score']:.2f}")

con.close()

print("\n" + "="*80)
print("FIN DE L'ANALYSE")
print("="*80)
