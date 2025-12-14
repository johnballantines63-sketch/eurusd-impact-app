"""
Investigation : Événements sans empirical_score
================================================

Objectif : Comprendre pourquoi certains événements n'ont pas de score
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import DB_PATH

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("=" * 80)
print("INVESTIGATION : ÉVÉNEMENTS SANS EMPIRICAL_SCORE")
print("=" * 80)

# 1. Statistiques globales
print("\n📊 STATISTIQUES GLOBALES")
print("-" * 80)

result = conn.execute("""
    SELECT COUNT(DISTINCT event_key || '_' || country) as total_families
    FROM event_families
""").fetchone()
print(f"Familles dans event_families: {result[0]}")

result = conn.execute("""
    SELECT COUNT(DISTINCT event_key || '_' || country) as total_events
    FROM events
    WHERE ts_utc >= '2025-01-01'
""").fetchone()
print(f"Événements uniques 2025: {result[0]}")

# 2. Événements du 11 sept SANS score
print("\n❌ ÉVÉNEMENTS 11 SEPT SANS EMPIRICAL_SCORE")
print("-" * 80)

result = conn.execute("""
    SELECT 
        e.event_key,
        e.event_title,
        e.country,
        e.actual,
        e.estimate,
        COUNT(*) as nb_occurrences
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc >= '2025-09-11 14:25:00+02:00'
        AND e.ts_utc < '2025-09-11 15:00:00+02:00'
        AND ef.event_key IS NULL
    GROUP BY e.event_key, e.event_title, e.country, e.actual, e.estimate
    ORDER BY e.country, e.event_key
""").fetchdf()

if not result.empty:
    print(f"\n{len(result)} événements sans score:")
    print(result.to_string(index=False))
else:
    print("\n✅ Tous les événements ont un score !")

# 3. Événements du 11 sept AVEC score
print("\n✅ ÉVÉNEMENTS 11 SEPT AVEC EMPIRICAL_SCORE")
print("-" * 80)

result = conn.execute("""
    SELECT 
        e.event_key,
        e.event_title,
        e.country,
        ef.empirical_score,
        COUNT(*) as nb_occurrences
    FROM events e
    INNER JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc >= '2025-09-11 14:25:00+02:00'
        AND e.ts_utc < '2025-09-11 15:00:00+02:00'
    GROUP BY e.event_key, e.event_title, e.country, ef.empirical_score
    ORDER BY e.country, e.event_key
""").fetchdf()

if not result.empty:
    print(f"\n{len(result)} événements avec score:")
    print(result.to_string(index=False))

# 4. Vérifier les event_key qui matcheraient si on ignorait le pays
print("\n🔍 ANALYSE : EVENT_KEY SANS MATCH DE PAYS")
print("-" * 80)

result = conn.execute("""
    SELECT 
        e.event_key,
        e.country as event_country,
        ef.country as family_country,
        ef.empirical_score
    FROM events e
    INNER JOIN event_families ef ON e.event_key = ef.event_key
    WHERE e.ts_utc >= '2025-09-11 14:25:00+02:00'
        AND e.ts_utc < '2025-09-11 15:00:00+02:00'
        AND e.country != ef.country
    LIMIT 10
""").fetchdf()

if not result.empty:
    print(f"\n⚠️  {len(result)} cas où event_key matche mais pas le pays:")
    print(result.to_string(index=False))
else:
    print("\n✅ Pas de problème de mismatch pays")

# 5. Sample event_families pour US et DE
print("\n📋 SAMPLE EVENT_FAMILIES (US)")
print("-" * 80)

result = conn.execute("""
    SELECT event_key, country, empirical_score, sample_size
    FROM event_families
    WHERE country = 'US'
    ORDER BY empirical_score DESC
    LIMIT 10
""").fetchdf()
print(result.to_string(index=False))

print("\n📋 SAMPLE EVENT_FAMILIES (DE)")
print("-" * 80)

result = conn.execute("""
    SELECT event_key, country, empirical_score, sample_size
    FROM event_families
    WHERE country = 'DE'
    LIMIT 10
""").fetchdf()

if not result.empty:
    print(result.to_string(index=False))
else:
    print("❌ Aucune famille pour DE !")

# 6. Vérifier les event_title NULL
print("\n🔍 ÉVÉNEMENTS AVEC event_title NULL")
print("-" * 80)

result = conn.execute("""
    SELECT 
        event_key,
        event_title,
        country,
        COUNT(*) as nb_occurrences
    FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+02:00'
        AND ts_utc < '2025-09-11 15:00:00+02:00'
        AND event_title IS NULL
    GROUP BY event_key, event_title, country
""").fetchdf()

if not result.empty:
    print(f"\n⚠️  {len(result)} événements avec event_title NULL:")
    print(result.to_string(index=False))
else:
    print("\n✅ Tous les événements ont un event_title")

# 7. Comparaison event_key vs event_title
print("\n🔍 COMPARAISON EVENT_KEY VS EVENT_TITLE")
print("-" * 80)

result = conn.execute("""
    SELECT 
        event_key,
        event_title,
        country,
        COUNT(*) as nb_lignes
    FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+02:00'
        AND ts_utc < '2025-09-11 15:00:00+02:00'
    GROUP BY event_key, event_title, country
    ORDER BY country, event_key
""").fetchdf()
print(result.to_string(index=False))

conn.close()

print("\n" + "=" * 80)
print("FIN INVESTIGATION")
print("=" * 80)
