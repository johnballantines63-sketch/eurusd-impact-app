#!/usr/bin/env python3
"""
DIAGNOSTIC - Événements 11.09
==============================
Investiguer pourquoi aucun événement trouvé
"""

import sys
from pathlib import Path
import duckdb
import importlib.util

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

spec_config = importlib.util.spec_from_file_location(
    "config",
    project_root / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
Config = config_module.Config

config = Config()
db_path = config.get_db_path()

print("="*80)
print("DIAGNOSTIC ÉVÉNEMENTS 11.09.2025")
print("="*80)
print()

conn = duckdb.connect(str(db_path), read_only=True)

# Test 1 : Tous événements du 11.09
print("TEST 1 : Tous événements US du 11.09")
print("-"*80)
query1 = """
SELECT COUNT(*) as total
FROM events e
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
"""
result = conn.execute(query1).fetchone()
print(f"Total événements US : {result[0]}")
print()

# Test 2 : Avec scores
print("TEST 2 : Événements US avec empirical_score")
print("-"*80)
query2 = """
SELECT COUNT(*) as total
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
"""
result = conn.execute(query2).fetchone()
print(f"Avec empirical_score : {result[0]}")
print()

# Test 3 : Avec scores > 40
print("TEST 3 : Événements score > 40")
print("-"*80)
query3 = """
SELECT COUNT(*) as total
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND ef.empirical_score > 40
"""
result = conn.execute(query3).fetchone()
print(f"Score > 40 : {result[0]}")
print()

# Test 4 : Voir les timestamps
print("TEST 4 : Timestamps événements 11.09 (score > 40)")
print("-"*80)
query4 = """
SELECT e.ts_utc, ef.family, ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
LIMIT 20
"""
results = conn.execute(query4).fetchdf()
print(results.to_string())
print()

# Test 5 : Vérifier filtre temporel
print("TEST 5 : Test filtre temporel 12:00-13:00+02:00")
print("-"*80)
query5 = """
SELECT COUNT(*) as total
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND ef.empirical_score > 40
    AND e.ts_utc >= '2025-09-11 12:00:00+02:00'::TIMESTAMP
    AND e.ts_utc < '2025-09-11 13:00:00+02:00'::TIMESTAMP
"""
result = conn.execute(query5).fetchone()
print(f"Avec filtre temporel : {result[0]}")
print()

# Test 6 : Sans filtre temporel
print("TEST 6 : Même requête SANS filtre temporel")
print("-"*80)
query6 = """
SELECT e.ts_utc, ef.family, ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
"""
results = conn.execute(query6).fetchdf()
print(f"Total trouvé : {len(results)}")
if len(results) > 0:
    print()
    print("Premiers événements :")
    print(results.head(15).to_string())
print()

conn.close()

print("="*80)
print("✅ DIAGNOSTIC TERMINÉ")
print("="*80)
