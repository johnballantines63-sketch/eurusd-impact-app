"""
DIAGNOSTIC : Pourquoi event_title = None ?
==========================================

Inspecte la table events pour 11.09.2025
"""

import sys
from pathlib import Path

# Setup paths
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root / "app"))

from config import Config
import duckdb

config = Config()
db_path = config.get_db_path()

print("="*80)
print("DIAGNOSTIC TABLE EVENTS - 11.09.2025")
print("="*80)

conn = duckdb.connect(str(db_path))

# 1. Schéma table events
print("\n1. COLONNES TABLE EVENTS :")
print("-" * 80)
schema = conn.execute("DESCRIBE events").df()
print(schema)

# 2. Sample événements 11.09.2025
print("\n2. ÉVÉNEMENTS 11.09.2025 (toutes colonnes) :")
print("-" * 80)
query = """
SELECT *
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND country = 'US'
ORDER BY ts_utc
LIMIT 5
"""
df = conn.execute(query).df()
print(df)

# 3. Colonnes contenant texte
print("\n3. COLONNES TEXTE (event_key, event_title, etc.) :")
print("-" * 80)
query = """
SELECT 
    ts_utc,
    event_key,
    event_title,
    country,
    actual,
    estimate
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND country = 'US'
ORDER BY ts_utc
"""
df = conn.execute(query).df()
print(df.to_string())

# 4. Compter NULL
print("\n4. NOMBRE DE NULL DANS event_title :")
print("-" * 80)
query = """
SELECT 
    COUNT(*) as total,
    COUNT(event_title) as avec_titre,
    COUNT(*) - COUNT(event_title) as sans_titre
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND country = 'US'
"""
df = conn.execute(query).df()
print(df)

# 5. Vérifier event_families
print("\n5. NOMS DEPUIS event_families :")
print("-" * 80)
query = """
SELECT DISTINCT
    e.event_key,
    e.event_title,
    ef.family,
    COUNT(*) as n_occurrences
FROM events e
INNER JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
GROUP BY e.event_key, e.event_title, ef.family
ORDER BY e.event_key
"""
df = conn.execute(query).df()
print(df.to_string())

conn.close()

print("\n" + "="*80)
print("DIAGNOSTIC TERMINÉ")
print("="*80)
