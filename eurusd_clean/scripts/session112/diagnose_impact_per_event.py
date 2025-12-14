#!/usr/bin/env python3
"""
DIAGNOSTIC IMPACT PAR ÉVÉNEMENT - 11 SEPTEMBRE 2025
====================================================

Calcule l'impact individuel de chaque événement du cluster
pour comprendre la contribution de chacun à l'impact total.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import math

# Chemins
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent.parent.parent
src_path = project_root / 'fx_impact_app' / 'src'
db_path = project_root / 'eurusd_clean' / 'app' / 'data' / 'warehouse.duckdb'

sys.path.insert(0, str(src_path))

from formulas_validated import calculate_impact_d, calculate_adjusted_empirical_score

print("="*80)
print("📊 DIAGNOSTIC IMPACT PAR ÉVÉNEMENT - 11 SEPTEMBRE 2025")
print("="*80)

con = duckdb.connect(str(db_path), read_only=True)

# Extraire événements normalisés
query = """
SELECT DISTINCT ON (REPLACE(LOWER(TRIM(e.event_key)), '-', ' '))
    e.event_key,
    COALESCE(e.event_title, e.event_key) as name,
    e.country,
    e.actual,
    e.estimate,
    e.previous,
    e.importance_n,
    ef.empirical_score,
    ef.avg_movement_pips
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key
WHERE e.ts_utc = '2025-09-11 14:30:00+02:00'
  AND e.estimate IS NOT NULL
  AND e.actual IS NOT NULL
  AND ef.empirical_score IS NOT NULL
ORDER BY REPLACE(LOWER(TRIM(e.event_key)), '-', ' '), 
         ef.empirical_score DESC NULLS LAST
"""

df = con.execute(query).df()
con.close()

print(f"\n📋 Cluster 1 (14:30): {len(df)} événements")
print("="*80)

# Calculer impact individuel pour chaque événement
impacts_individual = []

for i, row in df.iterrows():
    # Calculer surprise
    if pd.notna(row['actual']) and pd.notna(row['estimate']) and abs(row['estimate']) > 0.01:
        surprise = abs((row['actual'] - row['estimate']) / row['estimate']) * 100
        surprise = min(surprise, 500.0)
    else:
        surprise = 0.0
    
    # Score ajusté selon surprise
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=row['empirical_score'],
        surprise_pct=surprise
    )
    
    # Impact si événement seul (num_events=1, amplification=2.5)
    impact_solo = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=1,
        amplification=2.5
    )
    
    # Impact proportionnel dans le cluster
    # (contribution théorique basée sur le score)
    
    impacts_individual.append({
        'name': row['name'],
        'event_key': row['event_key'],
        'score_base': row['empirical_score'],
        'surprise': surprise,
        'score_adjusted': adjusted_score,
        'impact_solo': impact_solo,
        'avg_movement': row['avg_movement_pips'] if pd.notna(row['avg_movement_pips']) else 0,
        'actual': row['actual'],
        'estimate': row['estimate']
    })

# DataFrame résultats
df_impacts = pd.DataFrame(impacts_individual)

# Afficher résultats
print("\n📊 IMPACT INDIVIDUEL PAR ÉVÉNEMENT")
print("="*80)
print(f"{'#':<3} {'Événement':<35} {'Score':<7} {'Surp%':<7} {'Adj':<7} {'Impact':<8} {'AvgMvt':<8}")
print("-"*80)

for i, row in df_impacts.iterrows():
    print(f"{i+1:<3} {row['name'][:34]:<35} "
          f"{row['score_base']:<7.1f} "
          f"{row['surprise']:<7.1f} "
          f"{row['score_adjusted']:<7.1f} "
          f"{row['impact_solo']:<8.1f} "
          f"{row['avg_movement']:<8.1f}")

# Statistiques
print("\n" + "="*80)
print("📊 STATISTIQUES")
print("="*80)

print(f"\nScores base:")
print(f"   Moyenne:  {df_impacts['score_base'].mean():.2f}")
print(f"   Médiane:  {df_impacts['score_base'].median():.2f}")
print(f"   Min:      {df_impacts['score_base'].min():.2f}")
print(f"   Max:      {df_impacts['score_base'].max():.2f}")

print(f"\nScores ajustés (avec surprise):")
print(f"   Moyenne:  {df_impacts['score_adjusted'].mean():.2f}")
print(f"   Médiane:  {df_impacts['score_adjusted'].median():.2f}")
print(f"   Min:      {df_impacts['score_adjusted'].min():.2f}")
print(f"   Max:      {df_impacts['score_adjusted'].max():.2f}")

print(f"\nSurprises:")
print(f"   Moyenne:  {df_impacts['surprise'].mean():.2f}%")
print(f"   Médiane:  {df_impacts['surprise'].median():.2f}%")
print(f"   Max:      {df_impacts['surprise'].max():.2f}%")

print(f"\nImpact solo (si événement seul):")
print(f"   Moyenne:  {df_impacts['impact_solo'].mean():.2f} pips")
print(f"   Médiane:  {df_impacts['impact_solo'].median():.2f} pips")
print(f"   Max:      {df_impacts['impact_solo'].max():.2f} pips")

# Calcul impact cluster (formule D avec 12 événements)
score_cluster_base = df_impacts['score_base'].mean()
score_cluster_adjusted = df_impacts['score_adjusted'].mean()
surprise_max = df_impacts['surprise'].max()

# Ajuster score cluster avec surprise max
score_final = calculate_adjusted_empirical_score(
    base_empirical_score=score_cluster_base,
    surprise_pct=surprise_max
)

impact_cluster = calculate_impact_d(
    empirical_score=score_final,
    num_events=12,
    amplification=2.5
)

print(f"\n" + "="*80)
print("📊 CALCUL IMPACT CLUSTER (12 événements)")
print("="*80)
print(f"\nScore base moyen:        {score_cluster_base:.2f}")
print(f"Surprise max:            {surprise_max:.2f}%")
print(f"Score final ajusté:      {score_final:.2f}")
print(f"Nombre événements:       12")
print(f"Amplification:           2.5")
print(f"\n➡️  Impact cluster:        {impact_cluster:.1f} pips")
print(f"    Attendu MT5:          37.4 pips")
print(f"    Écart:                {abs(impact_cluster - 37.4):.1f} pips ({abs(impact_cluster - 37.4) / 37.4 * 100:.1f}%)")

# Calculer amplification nécessaire
if impact_cluster > 0:
    amp_needed = (37.4 / impact_cluster) * 2.5
    print(f"\n💡 Amplification nécessaire: {amp_needed:.2f} (au lieu de 2.5)")

# Analyse des événements qui contribuent le plus
print(f"\n" + "="*80)
print("📊 TOP 5 ÉVÉNEMENTS PAR IMPACT SOLO")
print("="*80)

df_top = df_impacts.nlargest(5, 'impact_solo')
for i, row in df_top.iterrows():
    print(f"\n{row['name']}")
    print(f"   Score base:      {row['score_base']:.1f}")
    print(f"   Surprise:        {row['surprise']:.1f}%")
    print(f"   Score ajusté:    {row['score_adjusted']:.1f}")
    print(f"   Impact solo:     {row['impact_solo']:.1f} pips")
    print(f"   Avg movement:    {row['avg_movement']:.1f} pips")

# Comparaison avg_movement vs impact calculé
print(f"\n" + "="*80)
print("📊 COMPARAISON AVG_MOVEMENT vs IMPACT SOLO")
print("="*80)

df_with_avg = df_impacts[df_impacts['avg_movement'] > 0]
if len(df_with_avg) > 0:
    print(f"\n{'Événement':<35} {'AvgMvt':<8} {'ImpSolo':<8} {'Ratio':<6}")
    print("-"*60)
    for _, row in df_with_avg.iterrows():
        ratio = row['impact_solo'] / row['avg_movement'] if row['avg_movement'] > 0 else 0
        print(f"{row['name'][:34]:<35} {row['avg_movement']:<8.1f} {row['impact_solo']:<8.1f} {ratio:<6.2f}")
    
    avg_ratio = (df_with_avg['impact_solo'] / df_with_avg['avg_movement']).mean()
    print(f"\nRatio moyen impact_solo / avg_movement: {avg_ratio:.2f}")

print("\n" + "="*80)
print("FIN DU DIAGNOSTIC")
print("="*80)
