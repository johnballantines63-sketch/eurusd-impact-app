"""
RÉSULTATS ANALYSE GROUPING V2
==============================

Analyse effectuée sur step3_movements_with_patterns_v2.csv
Date : 14 novembre 2025
Session : 139
"""

import pandas as pd
import numpy as np

# Charger le CSV
df = pd.read_csv('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session137/step3_movements_with_patterns_v2.csv')

print("="*80)
print("📊 ANALYSE GROUPING V2 - RÉSULTATS COMPLETS")
print("="*80)
print(f"\nTotal mouvements : {len(df)}")

# 1. Distribution patterns
print("\n" + "="*80)
print("1. DISTRIBUTION PATTERNS")
print("="*80)
patterns = df['pattern_type'].value_counts().sort_values(ascending=False)
for pattern, count in patterns.items():
    pct = count/len(df)*100
    print(f"  • {pattern:35s}: {count:3d} ({pct:5.1f}%)")

# 2. Statistiques scores
print("\n" + "="*80)
print("2. STATISTIQUES SCORES")
print("="*80)
print(f"  • Min     : {df['total_score'].min():.2f}")
print(f"  • Max     : {df['total_score'].max():.2f}")
print(f"  • Moyenne : {df['total_score'].mean():.2f}")
print(f"  • Médiane : {df['total_score'].median():.2f}")
print(f"  • Q1      : {df['total_score'].quantile(0.25):.2f}")
print(f"  • Q3      : {df['total_score'].quantile(0.75):.2f}")

# 3. Créer score_ranges
def assign_score_range(score):
    if score < 100: return "0-100"
    elif score < 200: return "100-200"
    elif score < 300: return "200-300"
    elif score < 400: return "300-400"
    elif score < 500: return "400-500"
    else: return "500+"

df['score_range'] = df['total_score'].apply(assign_score_range)

print("\n" + "="*80)
print("3. DISTRIBUTION SCORE_RANGES")
print("="*80)
ranges = df['score_range'].value_counts().sort_index()
for range_name, count in ranges.items():
    pct = count/len(df)*100
    print(f"  • {range_name:10s}: {count:3d} ({pct:5.1f}%)")

# 4. Grouper
grouped = df.groupby(['pattern_type', 'score_range']).size().reset_index(name='count')

print("\n" + "="*80)
print("4. GROUPES CRÉÉS (AVANT FILTRAGE)")
print("="*80)
print(f"  • Total groupes créés : {len(grouped)}")
print(f"  • Groupes ≥3 cas     : {len(grouped[grouped['count'] >= 3])}")
print(f"  • Groupes <3 cas     : {len(grouped[grouped['count'] < 3])}")

# 5. Filtrer
filtered = grouped[grouped['count'] >= 3].copy()

print("\n" + "="*80)
print("5. GROUPES APRÈS FILTRAGE (≥3 CAS)")
print("="*80)
print(f"  • Groupes conservés       : {len(filtered)}")
print(f"  • Cas couverts           : {filtered['count'].sum()} / {len(df)} ({filtered['count'].sum()/len(df)*100:.1f}%)")
print(f"  • Cas par groupe (moyen) : {filtered['count'].mean():.1f}")
print(f"  • Cas par groupe (min)   : {filtered['count'].min()}")
print(f"  • Cas par groupe (max)   : {filtered['count'].max()}")

# 6. Distribution par pattern
print("\n" + "="*80)
print("6. DISTRIBUTION PAR PATTERN (groupes filtrés)")
print("="*80)
pattern_dist = filtered.groupby('pattern_type').agg({'count': ['sum', 'count']})
pattern_dist.columns = ['total_cases', 'nb_groups']
pattern_dist = pattern_dist.sort_values('total_cases', ascending=False)
for pattern in pattern_dist.index:
    total = pattern_dist.loc[pattern, 'total_cases']
    nb = int(pattern_dist.loc[pattern, 'nb_groups'])
    pct = total/filtered['count'].sum()*100
    print(f"  • {pattern:35s}: {total:3d} cas ({pct:5.1f}%) | {nb:2d} groupes")

# 7. Distribution par score_range
print("\n" + "="*80)
print("7. DISTRIBUTION PAR SCORE_RANGE (groupes filtrés)")
print("="*80)
range_dist = filtered.groupby('score_range').agg({'count': ['sum', 'count']})
range_dist.columns = ['total_cases', 'nb_groups']
range_dist = range_dist.sort_index()
for range_name in range_dist.index:
    total = range_dist.loc[range_name, 'total_cases']
    nb = int(range_dist.loc[range_name, 'nb_groups'])
    pct = total/filtered['count'].sum()*100
    print(f"  • {range_name:10s}: {total:3d} cas ({pct:5.1f}%) | {nb:2d} groupes")

# 8. Top 20 groupes
print("\n" + "="*80)
print("8. TOP 20 GROUPES")
print("="*80)
top20 = filtered.nlargest(20, 'count')
for i, (idx, row) in enumerate(top20.iterrows(), 1):
    print(f"  {i:2d}. {row['pattern_type']:35s} | {row['score_range']:10s} | {row['count']:3d} cas")

# 9. Bottom 10 groupes
print("\n" + "="*80)
print("9. BOTTOM 10 GROUPES (plus petits conservés)")
print("="*80)
bottom10 = filtered.nsmallest(10, 'count')
for i, (idx, row) in enumerate(bottom10.iterrows(), 1):
    print(f"  {i:2d}. {row['pattern_type']:35s} | {row['score_range']:10s} | {row['count']:3d} cas")

# 10. Matrice
print("\n" + "="*80)
print("10. MATRICE COMPLÈTE (pattern × score_range)")
print("="*80)
pivot = filtered.pivot(index='pattern_type', columns='score_range', values='count').fillna(0).astype(int)
pivot['TOTAL'] = pivot.sum(axis=1)
pivot.loc['TOTAL'] = pivot.sum(axis=0)
print(pivot.to_string())

print("\n" + "="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80)
print(f"\n📌 CONCLUSION : {len(filtered)} groupes valides créés (≥3 cas)")
print(f"📌 Couverture : {filtered['count'].sum()} / {len(df)} mouvements ({filtered['count'].sum()/len(df)*100:.1f}%)")
print(f"📌 Prochaine étape : LOO-CV sur ces {len(filtered)} groupes")
