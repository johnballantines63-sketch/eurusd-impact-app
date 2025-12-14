#!/usr/bin/env python3
"""
Investigation Événements Unknown avec Estimate NaN
==================================================

Objectif : Comprendre pourquoi certains événements ont "Unknown" comme nom et estimate NaN
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
print('INVESTIGATION ÉVÉNEMENTS UNKNOWN AVEC ESTIMATE NaN')
print('='*100)
print()

# 1. Vérifier directement dans la DB
print('='*100)
print('1. VÉRIFICATION DIRECTE DANS LA DB')
print('='*100)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Charger événements pour 2025-08-01
query = """
SELECT 
    e.ts_utc,
    e.event_key,
    e.event_title,
    e.country,
    e.actual,
    e.estimate,
    e.forecast,
    e.previous,
    e.importance_n,
    ef.family,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-08-01'
ORDER BY e.ts_utc
"""

df_db = conn.execute(query).df()
conn.close()

print(f'Nombre d\'événements dans DB : {len(df_db)}')
print()

if not df_db.empty:
    print('Échantillon événements DB:')
    print('-'*100)
    for idx, row in df_db.head(10).iterrows():
        print(f'Event Key: {row.get("event_key", "N/A")}')
        print(f'Event Title: {row.get("event_title", "N/A")}')
        print(f'Country: {row.get("country", "N/A")}')
        print(f'Actual: {row.get("actual", "N/A")}')
        print(f'Estimate: {row.get("estimate", "N/A")}')
        print(f'Forecast: {row.get("forecast", "N/A")}')
        print(f'Previous: {row.get("previous", "N/A")}')
        print()
    
    # Statistiques
    print('='*100)
    print('STATISTIQUES')
    print('='*100)
    print()
    
    events_with_estimate = df_db[df_db['estimate'].notna()]
    events_with_forecast = df_db[df_db['forecast'].notna()]
    events_with_previous = df_db[df_db['previous'].notna()]
    events_with_title = df_db[df_db['event_title'].notna()]
    
    print(f'Événements avec estimate : {len(events_with_estimate)}/{len(df_db)} ({len(events_with_estimate)/len(df_db)*100:.1f}%)')
    print(f'Événements avec forecast : {len(events_with_forecast)}/{len(df_db)} ({len(events_with_forecast)/len(df_db)*100:.1f}%)')
    print(f'Événements avec previous : {len(events_with_previous)}/{len(df_db)} ({len(events_with_previous)/len(df_db)*100:.1f}%)')
    print(f'Événements avec event_title : {len(events_with_title)}/{len(df_db)} ({len(events_with_title)/len(df_db)*100:.1f}%)')
    print()
    
    # Événements sans estimate
    events_no_estimate = df_db[df_db['estimate'].isna()]
    if not events_no_estimate.empty:
        print('='*100)
        print('ÉVÉNEMENTS SANS ESTIMATE')
        print('='*100)
        print()
        for idx, row in events_no_estimate.head(10).iterrows():
            print(f'Event Key: {row.get("event_key", "N/A")}')
            print(f'Event Title: {row.get("event_title", "N/A")}')
            print(f'Country: {row.get("country", "N/A")}')
            print(f'Actual: {row.get("actual", "N/A")}')
            print(f'Forecast: {row.get("forecast", "N/A")}')
            print(f'Previous: {row.get("previous", "N/A")}')
            print()

# 2. Vérifier comment le pipeline charge les événements
print('='*100)
print('2. VÉRIFICATION PIPELINE')
print('='*100)
print()

from scripts.run_pipeline_complete import PipelineExecutor

executor = PipelineExecutor(DB_PATH, verbose=False)
events_pipeline = executor.etape1_charger_evenements('2025-08-01')

print(f'Nombre d\'événements chargés par pipeline : {len(events_pipeline)}')
print()

if not events_pipeline.empty:
    print('Colonnes disponibles:')
    print('-'*100)
    print(events_pipeline.columns.tolist())
    print()
    
    print('Échantillon événements pipeline:')
    print('-'*100)
    for idx, row in events_pipeline.head(10).iterrows():
        # Vérifier toutes les colonnes possibles pour le nom
        name = row.get('name') or row.get('event_title') or row.get('event_key') or row.get('label') or 'Unknown'
        estimate = row.get('estimate') or row.get('forecast') or row.get('previous')
        
        print(f'Name: {name}')
        print(f'Estimate: {estimate}')
        print(f'Actual: {row.get("actual", "N/A")}')
        print(f'Forecast: {row.get("forecast", "N/A")}')
        print(f'Previous: {row.get("previous", "N/A")}')
        print()
    
    # Vérifier colonnes manquantes
    print('='*100)
    print('VÉRIFICATION COLONNES')
    print('='*100)
    print()
    
    has_name = 'name' in events_pipeline.columns
    has_event_title = 'event_title' in events_pipeline.columns
    has_event_key = 'event_key' in events_pipeline.columns
    
    print(f'Colonne "name" présente : {has_name}')
    print(f'Colonne "event_title" présente : {has_event_title}')
    print(f'Colonne "event_key" présente : {has_event_key}')
    print()
    
    if not has_name:
        print('⚠️ Colonne "name" absente - Utiliser event_title ou event_key')
    if not has_event_title and not has_event_key:
        print('⚠️ Ni event_title ni event_key présents - Impossible d\'identifier les événements')

print('='*100)
print('✅ INVESTIGATION TERMINÉE')
print('='*100)




