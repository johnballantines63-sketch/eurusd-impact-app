#!/usr/bin/env python3
"""
VÉRIFICATION STRUCTURE - event_title vs event_key
==================================================

Objectif: Comprendre pourquoi beaucoup d'events ont event_title = None
mais ont quand même des event_key valides et des scores.
"""

import duckdb
from pathlib import Path

db_path = Path(__file__).parent.parent.parent / "app" / "data" / "warehouse.duckdb"

print("="*70)
print("VÉRIFICATION event_title vs event_key")
print("="*70)

con = duckdb.connect(str(db_path), read_only=True)

# Compter les événements avec/sans event_title
query = """
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN event_title IS NOT NULL THEN 1 END) as with_title,
    COUNT(CASE WHEN event_title IS NULL THEN 1 END) as without_title
FROM events
WHERE ts_utc = '2025-09-11 14:30:00+02:00'
  AND estimate IS NOT NULL
  AND actual IS NOT NULL
"""

result = con.execute(query).df()
print("\n📊 Distribution event_title (11 sept 14:30):")
print(f"   Total événements: {result['total'][0]}")
print(f"   Avec event_title: {result['with_title'][0]}")
print(f"   Sans event_title: {result['without_title'][0]}")

# Afficher quelques exemples
query2 = """
SELECT 
    event_key,
    event_title,
    actual,
    estimate,
    importance_n
FROM events
WHERE ts_utc = '2025-09-11 14:30:00+02:00'
  AND estimate IS NOT NULL
  AND actual IS NOT NULL
ORDER BY event_title IS NULL DESC, event_key
LIMIT 20
"""

df = con.execute(query2).df()
print("\n📋 Exemples (20 premiers):")
print(df.to_string(index=False))

# Vérifier si event_key contient toujours une valeur
query3 = """
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN event_key IS NOT NULL THEN 1 END) as with_key,
    COUNT(CASE WHEN event_key IS NULL THEN 1 END) as without_key
FROM events
WHERE ts_utc = '2025-09-11 14:30:00+02:00'
  AND estimate IS NOT NULL
  AND actual IS NOT NULL
"""

result3 = con.execute(query3).df()
print("\n📊 Distribution event_key:")
print(f"   Total événements: {result3['total'][0]}")
print(f"   Avec event_key: {result3['with_key'][0]}")
print(f"   Sans event_key: {result3['without_key'][0]}")

con.close()

print("\n" + "="*70)
print("💡 CONCLUSION:")
print("   Si event_key a toujours une valeur, utiliser:")
print("   COALESCE(e.event_title, e.event_key) AS name")
print("="*70)
