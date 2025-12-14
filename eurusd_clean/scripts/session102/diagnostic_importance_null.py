#!/usr/bin/env python3
"""
DIAGNOSTIC IMPORTANCE_N = NULL
===============================

Comprendre pourquoi certains événements ont importance_n = NULL
avant de décider comment les traiter.

Questions :
1. Combien d'événements ont importance_n = NULL ?
2. Quels types d'événements ?
3. Ont-ils un empirical_score ?
4. Pattern spécifique ?
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 100)
print("DIAGNOSTIC IMPORTANCE_N = NULL")
print("=" * 100)
print()

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# STATISTIQUES GLOBALES
# ============================================================================

print("=" * 100)
print("STATISTIQUES GLOBALES")
print("=" * 100)
print()

query_stats = """
SELECT 
    COUNT(*) as total_events,
    COUNT(importance_n) as with_importance,
    COUNT(*) - COUNT(importance_n) as null_importance,
    ROUND(100.0 * (COUNT(*) - COUNT(importance_n)) / COUNT(*), 1) as pct_null
FROM events
WHERE country = 'US'
"""

stats = conn.execute(query_stats).fetchdf().iloc[0]

print(f"Total événements US      : {stats['total_events']:,}")
print(f"Avec importance_n        : {stats['with_importance']:,}")
print(f"Avec importance_n = NULL : {stats['null_importance']:,} ({stats['pct_null']:.1f}%)")
print()

# ============================================================================
# ÉVÉNEMENTS NULL POUR 11.09.2025
# ============================================================================

print("=" * 100)
print("ÉVÉNEMENTS NULL - 11.09.2025")
print("=" * 100)
print()

query_11sept = """
SELECT 
    e.event_key,
    e.event_title,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.importance_n,
    ef.empirical_score,
    ef.family
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND e.importance_n IS NULL
ORDER BY e.ts_utc, e.event_key
"""

df_null_11sept = conn.execute(query_11sept).fetchdf()

print(f"Événements avec importance_n = NULL : {len(df_null_11sept)}\n")

if len(df_null_11sept) > 0:
    for idx, event in df_null_11sept.iterrows():
        name = event['event_title'] if pd.notna(event['event_title']) else event['event_key']
        score = f"{event['empirical_score']:.1f}" if pd.notna(event['empirical_score']) else "NULL"
        family = event['family'] if pd.notna(event['family']) else "NULL"
        
        print(f"{idx+1:2d}. {name:45s}")
        print(f"    event_key : {event['event_key']}")
        print(f"    family    : {family}")
        print(f"    score     : {score}")
        print(f"    ts_utc    : {event['ts_utc']}")
        print()

# ============================================================================
# PATTERN : ÉVÉNEMENTS NULL PAR FAMILLE
# ============================================================================

print("=" * 100)
print("PATTERN : FAMILLES AVEC IMPORTANCE_N = NULL")
print("=" * 100)
print()

query_families = """
SELECT 
    ef.family,
    COUNT(DISTINCT e.event_key) as num_events,
    COUNT(CASE WHEN e.importance_n IS NULL THEN 1 END) as null_count,
    COUNT(CASE WHEN e.importance_n = 1 THEN 1 END) as high_count,
    COUNT(CASE WHEN e.importance_n = 2 THEN 1 END) as medium_count,
    COUNT(CASE WHEN e.importance_n = 3 THEN 1 END) as low_count,
    AVG(ef.empirical_score) as avg_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND ef.family IS NOT NULL
GROUP BY ef.family
HAVING COUNT(CASE WHEN e.importance_n IS NULL THEN 1 END) > 0
ORDER BY null_count DESC
LIMIT 20
"""

df_families = conn.execute(query_families).fetchdf()

print(f"Top 20 familles avec événements NULL :\n")
print(f"{'Famille':<30} {'Total':>7} {'NULL':>6} {'HIGH':>6} {'MED':>5} {'LOW':>5} {'Avg Score':>10}")
print("-" * 100)

for idx, row in df_families.iterrows():
    print(f"{row['family']:<30} {row['num_events']:>7} {row['null_count']:>6} "
          f"{row['high_count']:>6} {row['medium_count']:>5} {row['low_count']:>5} "
          f"{row['avg_score']:>10.1f}")

# ============================================================================
# CAS SPÉCIFIQUE : JOBLESS CLAIMS
# ============================================================================

print()
print("=" * 100)
print("CAS SPÉCIFIQUE : JOBLESS CLAIMS")
print("=" * 100)
print()

query_jobless = """
SELECT 
    e.event_key,
    COUNT(*) as occurrences,
    COUNT(CASE WHEN e.importance_n IS NULL THEN 1 END) as null_count,
    COUNT(CASE WHEN e.importance_n = 1 THEN 1 END) as high_count,
    COUNT(CASE WHEN e.importance_n = 2 THEN 1 END) as medium_count,
    COUNT(CASE WHEN e.importance_n = 3 THEN 1 END) as low_count
FROM events e
WHERE e.country = 'US'
    AND (
        e.event_key LIKE '%jobless%'
        OR e.event_key LIKE '%claims%'
    )
GROUP BY e.event_key
ORDER BY occurrences DESC
"""

df_jobless = conn.execute(query_jobless).fetchdf()

print("Événements jobless/claims et leur importance_n :\n")
print(f"{'Event Key':<45} {'Total':>7} {'NULL':>6} {'HIGH':>6} {'MED':>5} {'LOW':>5}")
print("-" * 100)

for idx, row in df_jobless.iterrows():
    print(f"{row['event_key']:<45} {row['occurrences']:>7} {row['null_count']:>6} "
          f"{row['high_count']:>6} {row['medium_count']:>5} {row['low_count']:>5}")

# ============================================================================
# VÉRIFIER SI PATTERN TEMPOREL
# ============================================================================

print()
print("=" * 100)
print("PATTERN TEMPOREL : NULL PAR ANNÉE")
print("=" * 100)
print()

query_temporal = """
SELECT 
    YEAR(e.ts_utc) as year,
    COUNT(*) as total_events,
    COUNT(CASE WHEN e.importance_n IS NULL THEN 1 END) as null_count,
    ROUND(100.0 * COUNT(CASE WHEN e.importance_n IS NULL THEN 1 END) / COUNT(*), 1) as pct_null
FROM events e
WHERE e.country = 'US'
GROUP BY YEAR(e.ts_utc)
ORDER BY year DESC
"""

df_temporal = conn.execute(query_temporal).fetchdf()

print(f"{'Année':<10} {'Total':>10} {'NULL':>10} {'% NULL':>10}")
print("-" * 50)

for idx, row in df_temporal.iterrows():
    print(f"{int(row['year']):<10} {row['total_events']:>10} {row['null_count']:>10} {row['pct_null']:>9.1f}%")

conn.close()

# ============================================================================
# CONCLUSION
# ============================================================================

print()
print("=" * 100)
print("CONCLUSION")
print("=" * 100)
print()

print("HYPOTHÈSES À VÉRIFIER :")
print()
print("1. Import incomplet :")
print("   → Certains événements n'ont pas importance_n dans source eodhd")
print("   → Données partielles")
print()
print("2. Événements MoM/YoY variants :")
print("   → Variants (_mom, _yoy) créés après import")
print("   → N'ont pas reçu importance_n")
print()
print("3. Pattern famille spécifique :")
print("   → Certaines familles systématiquement NULL")
print("   → Jobless Claims, Real Earnings, etc.")
print()
print("4. Pattern temporel :")
print("   → Données récentes moins complètes")
print("   → Ou changement dans import eodhd")
print()
print("RECOMMANDATION :")
print("→ Analyser les résultats ci-dessus pour décider stratégie")
