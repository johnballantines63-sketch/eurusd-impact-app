#!/usr/bin/env python3
"""
INVESTIGUER LOGIQUE VARIANTS _mom/_yoy
=======================================

Comprendre comment les variants sont créés
et pourquoi ils n'ont pas importance_n
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
print("INVESTIGATION VARIANTS _mom/_yoy")
print("=" * 100)
print()

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# CAS D'ÉTUDE : CORE INFLATION RATE
# ============================================================================

print("=" * 100)
print("CAS D'ÉTUDE : CORE INFLATION RATE ET SES VARIANTS")
print("=" * 100)
print()

query_cpi_variants = """
SELECT 
    e.event_key,
    e.event_title,
    e.importance_n,
    ef.empirical_score,
    ef.family,
    COUNT(*) as occurrences
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND (
        e.event_key LIKE '%core inflation%'
        OR e.event_key LIKE '%core cpi%'
    )
GROUP BY e.event_key, e.event_title, e.importance_n, ef.empirical_score, ef.family
ORDER BY e.event_key
"""

df_cpi = conn.execute(query_cpi_variants).fetchdf()

print(f"{'Event Key':<40} {'Title':<25} {'Imp':>5} {'Score':>7} {'Family':<15} {'Count':>7}")
print("-" * 120)

for idx, row in df_cpi.iterrows():
    event_key = row['event_key']
    title = row['event_title'] if pd.notna(row['event_title']) else "NULL"
    imp = str(row['importance_n']) if pd.notna(row['importance_n']) else "NULL"
    score = f"{row['empirical_score']:.1f}" if pd.notna(row['empirical_score']) else "NULL"
    family = row['family'] if pd.notna(row['family']) else "NULL"
    
    # Marquer les variants
    is_variant = "_mom" in event_key or "_yoy" in event_key
    marker = "🔸" if is_variant else "  "
    
    print(f"{marker} {event_key:<38} {title:<25} {imp:>5} {score:>7} {family:<15} {row['occurrences']:>7}")

# ============================================================================
# PATTERN : TOUS LES VARIANTS
# ============================================================================

print()
print("=" * 100)
print("PATTERN : TOUS LES VARIANTS _mom/_yoy")
print("=" * 100)
print()

query_all_variants = """
SELECT 
    CASE 
        WHEN event_key LIKE '%\\_mom' ESCAPE '\\' THEN 'MoM variant'
        WHEN event_key LIKE '%\\_yoy' ESCAPE '\\' THEN 'YoY variant'
        ELSE 'Other variant'
    END as variant_type,
    COUNT(*) as total,
    COUNT(CASE WHEN importance_n IS NULL THEN 1 END) as null_count,
    COUNT(CASE WHEN importance_n = 1 THEN 1 END) as high_count,
    ROUND(100.0 * COUNT(CASE WHEN importance_n IS NULL THEN 1 END) / COUNT(*), 1) as pct_null
FROM events
WHERE country = 'US'
    AND (event_key LIKE '%\\_mom' ESCAPE '\\' OR event_key LIKE '%\\_yoy' ESCAPE '\\')
GROUP BY variant_type
"""

df_variants = conn.execute(query_all_variants).fetchdf()

print(f"{'Type':<20} {'Total':>10} {'NULL':>10} {'HIGH':>10} {'% NULL':>10}")
print("-" * 70)

for idx, row in df_variants.iterrows():
    print(f"{row['variant_type']:<20} {row['total']:>10} {row['null_count']:>10} "
          f"{row['high_count']:>10} {row['pct_null']:>9.1f}%")

# ============================================================================
# IDENTIFIER PARENTS
# ============================================================================

print()
print("=" * 100)
print("IDENTIFIER PARENTS DES VARIANTS")
print("=" * 100)
print()

# Exemple : core inflation rate_mom → parent = core inflation rate
query_parent_child = """
WITH variants AS (
    SELECT 
        event_key as variant_key,
        REGEXP_REPLACE(event_key, '_mom$|_yoy$', '') as potential_parent,
        importance_n as variant_importance
    FROM events
    WHERE country = 'US'
        AND (event_key LIKE '%\\_mom' ESCAPE '\\' OR event_key LIKE '%\\_yoy' ESCAPE '\\')
        AND ts_utc >= '2025-09-01'
    LIMIT 10
)
SELECT 
    v.variant_key,
    v.variant_importance as variant_imp,
    p.event_key as parent_key,
    p.importance_n as parent_imp
FROM variants v
LEFT JOIN events p 
    ON p.event_key = v.potential_parent
    AND p.country = 'US'
    AND p.ts_utc >= '2025-09-01'
WHERE p.event_key IS NOT NULL
LIMIT 10
"""

df_parent = conn.execute(query_parent_child).fetchdf()

print("Exemples variant → parent :\n")
print(f"{'Variant':<40} {'V_Imp':>7} {'Parent':<40} {'P_Imp':>7}")
print("-" * 100)

for idx, row in df_parent.iterrows():
    v_imp = str(row['variant_imp']) if pd.notna(row['variant_imp']) else "NULL"
    p_imp = str(row['parent_imp']) if pd.notna(row['parent_imp']) else "NULL"
    
    match = "✅" if v_imp == p_imp else "❌"
    
    print(f"{match} {row['variant_key']:<38} {v_imp:>7} {row['parent_key']:<40} {p_imp:>7}")

conn.close()

# ============================================================================
# CONCLUSION
# ============================================================================

print()
print("=" * 100)
print("CONCLUSION")
print("=" * 100)
print()

print("DÉCOUVERTES :")
print()
print("1. Les variants _mom/_yoy sont MASSIFS en nombre")
print("2. Ils n'ont PAS hérité importance_n du parent")
print("3. Pattern clair : parent HIGH → variant NULL")
print()
print("SOLUTIONS POSSIBLES :")
print()
print("A. HÉRITER DU PARENT :")
print("   WHERE (importance_n = 1)")
print("   OR (event_key matches '_mom$|_yoy$' AND parent.importance_n = 1)")
print()
print("B. UTILISER FAMILY + SCORE :")
print("   WHERE (importance_n = 1)")
print("   OR (family IN ('CPI', 'Jobless Claims') AND score > 40)")
print()
print("C. FALLBACK SUR EMPIRICAL_SCORE UNIQUEMENT :")
print("   WHERE (importance_n = 1 OR score > 40)")
print("   → Simple mais inclut aussi variants avec score fort")
print()
print("RECOMMANDATION :")
print("→ Option C est la plus simple et cohérente avec notre méthodologie")
print("→ On garde les variants SEULEMENT s'ils ont score > 40")
print("→ Sinon on les exclut (probablement doublons de toute façon)")
