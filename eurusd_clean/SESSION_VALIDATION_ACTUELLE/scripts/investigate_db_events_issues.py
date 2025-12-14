#!/usr/bin/env python3
"""
Investigation Problèmes Événements dans DB
===========================================

Objectif : Comprendre pourquoi certains événements ont event_title=NaN et estimate=NaN
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

print('='*100)
print('INVESTIGATION PROBLÈMES ÉVÉNEMENTS DANS DB')
print('='*100)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Événements avec event_title = NaN
print('='*100)
print('1. ÉVÉNEMENTS AVEC event_title = NaN')
print('='*100)
print()

query_no_title = """
SELECT 
    e.ts_utc,
    e.event_key,
    e.event_title,
    e.label,
    e.country,
    e.actual,
    e.estimate,
    e.forecast,
    e.previous
FROM events e
WHERE DATE(e.ts_utc) = '2025-08-01'
    AND (e.event_title IS NULL OR e.event_title = '')
ORDER BY e.ts_utc
LIMIT 20
"""

df_no_title = conn.execute(query_no_title).df()

if not df_no_title.empty:
    print(f'Nombre d\'événements sans event_title : {len(df_no_title)}')
    print()
    print('Échantillon:')
    print('-'*100)
    for idx, row in df_no_title.head(10).iterrows():
        print(f'Event Key: {row.get("event_key", "N/A")}')
        print(f'Event Title: {row.get("event_title", "N/A")}')
        print(f'Label: {row.get("label", "N/A")}')
        print(f'Country: {row.get("country", "N/A")}')
        print()
else:
    print('✅ Aucun événement sans event_title trouvé')
    print()

# 2. Événements avec estimate = NaN
print('='*100)
print('2. ÉVÉNEMENTS AVEC estimate = NaN')
print('='*100)
print()

query_no_estimate = """
SELECT 
    e.ts_utc,
    e.event_key,
    e.event_title,
    e.country,
    e.actual,
    e.estimate,
    e.forecast,
    e.previous
FROM events e
WHERE DATE(e.ts_utc) = '2025-08-01'
    AND e.estimate IS NULL
ORDER BY e.ts_utc
LIMIT 20
"""

df_no_estimate = conn.execute(query_no_estimate).df()

if not df_no_estimate.empty:
    print(f'Nombre d\'événements sans estimate : {len(df_no_estimate)}')
    print()
    print('Échantillon:')
    print('-'*100)
    for idx, row in df_no_estimate.head(10).iterrows():
        print(f'Event Key: {row.get("event_key", "N/A")}')
        print(f'Event Title: {row.get("event_title", "N/A")}')
        print(f'Country: {row.get("country", "N/A")}')
        print(f'Actual: {row.get("actual", "N/A")}')
        print(f'Estimate: {row.get("estimate", "N/A")}')
        print(f'Forecast: {row.get("forecast", "N/A")}')
        print(f'Previous: {row.get("previous", "N/A")}')
        print()
else:
    print('✅ Aucun événement sans estimate trouvé')
    print()

# 3. Statistiques globales pour 2025-08-01
print('='*100)
print('3. STATISTIQUES GLOBALES 2025-08-01')
print('='*100)
print()

query_stats = """
SELECT 
    COUNT(*) as total_events,
    COUNT(CASE WHEN e.event_title IS NOT NULL AND e.event_title != '' THEN 1 END) as with_title,
    COUNT(CASE WHEN e.estimate IS NOT NULL THEN 1 END) as with_estimate,
    COUNT(CASE WHEN e.forecast IS NOT NULL THEN 1 END) as with_forecast,
    COUNT(CASE WHEN e.previous IS NOT NULL THEN 1 END) as with_previous,
    COUNT(CASE WHEN e.actual IS NOT NULL THEN 1 END) as with_actual
FROM events e
WHERE DATE(e.ts_utc) = '2025-08-01'
"""

df_stats = conn.execute(query_stats).df()

if not df_stats.empty:
    stats = df_stats.iloc[0]
    print(f'Total événements : {stats["total_events"]}')
    print(f'Avec event_title : {stats["with_title"]} ({stats["with_title"]/stats["total_events"]*100:.1f}%)')
    print(f'Avec estimate : {stats["with_estimate"]} ({stats["with_estimate"]/stats["total_events"]*100:.1f}%)')
    print(f'Avec forecast : {stats["with_forecast"]} ({stats["with_forecast"]/stats["total_events"]*100:.1f}%)')
    print(f'Avec previous : {stats["with_previous"]} ({stats["with_previous"]/stats["total_events"]*100:.1f}%)')
    print(f'Avec actual : {stats["with_actual"]} ({stats["with_actual"]/stats["total_events"]*100:.1f}%)')
    print()

# 4. Vérifier structure table events
print('='*100)
print('4. STRUCTURE TABLE events')
print('='*100)
print()

query_structure = """
DESCRIBE events
"""

df_structure = conn.execute(query_structure).df()

if not df_structure.empty:
    print('Colonnes table events:')
    print('-'*100)
    for idx, row in df_structure.iterrows():
        print(f'{row["column_name"]} : {row["column_type"]}')
    print()

# 5. Vérifier si label existe et contient des valeurs
print('='*100)
print('5. VÉRIFICATION COLONNE label')
print('='*100)
print()

query_label = """
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN e.label IS NOT NULL AND e.label != '' THEN 1 END) as with_label
FROM events e
WHERE DATE(e.ts_utc) = '2025-08-01'
"""

try:
    df_label = conn.execute(query_label).df()
    if not df_label.empty:
        stats_label = df_label.iloc[0]
        print(f'Total événements : {stats_label["total"]}')
        print(f'Avec label : {stats_label["with_label"]} ({stats_label["with_label"]/stats_label["total"]*100:.1f}%)')
        print()
except Exception as e:
    print(f'⚠️ Colonne label n\'existe pas ou erreur : {e}')
    print()

conn.close()

print('='*100)
print('✅ INVESTIGATION TERMINÉE')
print('='*100)




