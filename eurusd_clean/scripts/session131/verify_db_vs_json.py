#!/usr/bin/env python3
"""
Vérification JSON vs DB - Session 131
Objectif: S'assurer que les événements du 11 septembre dans le JSON
correspondent exactement à ce qui est dans la base de données.
"""

import json
import duckdb
from datetime import datetime, timezone
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "data" / "eurusd_news_impact.db"
JSON_PATH = BASE_DIR / "scripts" / "session130" / "reference_cases_with_r2_clusters.json"

def load_json_events():
    """Charger les événements du 11 septembre depuis le JSON"""
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    
    doublewave_overlap = data['reference_cases']['DoubleWave_Overlap']
    events = doublewave_overlap['events']
    
    print(f"\n{'='*80}")
    print(f"ÉVÉNEMENTS 11 SEPTEMBRE 2025 DANS LE JSON")
    print(f"{'='*80}")
    print(f"Nombre total: {len(events)}")
    print(f"\nListe des événements:")
    
    json_events = []
    for i, evt in enumerate(events, 1):
        event_key = evt['event_key']
        ts = evt['ts_utc']
        country = evt['country']
        importance = evt['importance']
        
        print(f"{i:2d}. {ts} | {event_key:50s} | {country} | {importance}")
        json_events.append({
            'event_key': event_key,
            'ts_utc': ts,
            'country': country,
            'importance': importance
        })
    
    return json_events

def query_db_events():
    """Interroger la DB pour tous les événements du 11 septembre 2025"""
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Requête pour obtenir TOUS les événements du 11 septembre 2025
    # On cherche entre 00:00 et 23:59 ce jour-là
    query = """
    SELECT 
        event_key,
        ts_utc,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_calendar
    WHERE DATE(ts_utc) = '2025-09-11'
    ORDER BY ts_utc, event_key
    """
    
    result = conn.execute(query).fetchall()
    
    print(f"\n{'='*80}")
    print(f"ÉVÉNEMENTS 11 SEPTEMBRE 2025 DANS LA BASE DE DONNÉES")
    print(f"{'='*80}")
    print(f"Nombre total: {len(result)}")
    print(f"\nListe des événements:")
    
    db_events = []
    for i, row in enumerate(result, 1):
        event_key, ts_utc, country, importance, actual, forecast, previous = row
        print(f"{i:2d}. {ts_utc} | {event_key:50s} | {country} | {importance}")
        db_events.append({
            'event_key': event_key,
            'ts_utc': str(ts_utc),
            'country': country,
            'importance': importance
        })
    
    conn.close()
    return db_events

def compare_events(json_events, db_events):
    """Comparer les événements JSON vs DB"""
    print(f"\n{'='*80}")
    print(f"COMPARAISON JSON vs DB")
    print(f"{'='*80}")
    
    # Créer des sets pour comparaison
    json_set = set((e['event_key'], e['ts_utc'], e['country']) for e in json_events)
    db_set = set((e['event_key'], e['ts_utc'], e['country']) for e in db_events)
    
    # Événements dans JSON mais pas dans DB
    missing_in_db = json_set - db_set
    if missing_in_db:
        print(f"\n⚠️  ÉVÉNEMENTS DANS JSON MAIS PAS DANS DB:")
        for evt in missing_in_db:
            print(f"  - {evt[1]} | {evt[0]} | {evt[2]}")
    else:
        print(f"\n✅ Tous les événements du JSON sont dans la DB")
    
    # Événements dans DB mais pas dans JSON
    missing_in_json = db_set - json_set
    if missing_in_json:
        print(f"\n⚠️  ÉVÉNEMENTS DANS DB MAIS PAS DANS JSON:")
        for evt in missing_in_json:
            print(f"  - {evt[1]} | {evt[0]} | {evt[2]}")
    else:
        print(f"\n✅ Tous les événements de la DB sont dans le JSON")
    
    # Résumé
    print(f"\n{'='*80}")
    print(f"RÉSUMÉ")
    print(f"{'='*80}")
    print(f"Événements dans JSON: {len(json_events)}")
    print(f"Événements dans DB:   {len(db_events)}")
    print(f"Manquants dans DB:    {len(missing_in_db)}")
    print(f"Manquants dans JSON:  {len(missing_in_json)}")
    
    if len(json_events) == len(db_events) and len(missing_in_db) == 0 and len(missing_in_json) == 0:
        print(f"\n✅ PARFAITE CORRESPONDANCE JSON ↔ DB")
    else:
        print(f"\n⚠️  IL Y A DES DIFFÉRENCES ENTRE JSON ET DB")
    
    return missing_in_db, missing_in_json

if __name__ == "__main__":
    print(f"\n{'#'*80}")
    print(f"# VÉRIFICATION JSON vs DB - 11 SEPTEMBRE 2025")
    print(f"{'#'*80}")
    
    # 1. Charger événements du JSON
    json_events = load_json_events()
    
    # 2. Interroger la DB
    db_events = query_db_events()
    
    # 3. Comparer
    missing_in_db, missing_in_json = compare_events(json_events, db_events)
    
    print(f"\n{'#'*80}")
    print(f"# FIN DE LA VÉRIFICATION")
    print(f"{'#'*80}\n")
