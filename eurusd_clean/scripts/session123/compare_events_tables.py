"""
Comparer tables events vs economic_events

Vérifier timezone et structure

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Comparaison tables
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def compare_events_tables():
    """Comparer events (ancienne) vs economic_events (nouvelle)"""
    
    print("=" * 80)
    print("COMPARAISON TABLES EVENTS")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Structure events (ancienne)
    print("TABLE events (ancienne, 58k) :")
    print("-" * 80)
    
    try:
        query_events_struct = "DESCRIBE events"
        events_struct = conn.execute(query_events_struct).df()
        print(events_struct.to_string())
        print()
        
        # Échantillon 11 septembre
        query_events_sept = """
        SELECT ts_utc, country, event_title, importance_n
        FROM events
        WHERE DATE(ts_utc) = '2025-09-11'
          AND country IN ('US', 'EU')
        ORDER BY ts_utc
        LIMIT 10
        """
        
        events_sept = conn.execute(query_events_sept).df()
        print(f"Échantillon 11 septembre (events) : {len(events_sept)} lignes")
        if len(events_sept) > 0:
            print(events_sept.to_string())
        else:
            print("   (aucun événement)")
        print()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print()
    
    # Structure economic_events (nouvelle)
    print("TABLE economic_events (nouvelle, 125k) :")
    print("-" * 80)
    
    query_ecoevents_struct = "DESCRIBE economic_events"
    ecoevents_struct = conn.execute(query_ecoevents_struct).df()
    print(ecoevents_struct.to_string())
    print()
    
    # Échantillon 11 septembre
    query_ecoevents_sept = """
    SELECT datetime_utc, country, event_name, importance
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND country IN ('usd', 'eur')
      AND importance = 'HIGH'
    ORDER BY datetime_utc
    LIMIT 10
    """
    
    ecoevents_sept = conn.execute(query_ecoevents_sept).df()
    print(f"Échantillon 11 septembre HIGH (economic_events) : {len(ecoevents_sept)} lignes")
    print(ecoevents_sept.to_string())
    print()
    
    # Comparaison timestamps
    print("COMPARAISON TIMESTAMPS :")
    print("-" * 80)
    
    if len(events_sept) > 0:
        print("events.ts_utc (ancienne) :")
        for idx, row in events_sept.head(3).iterrows():
            print(f"   {row['ts_utc']} - {row['country']} - {row['event_title']}")
        print()
    
    print("economic_events.datetime_utc (nouvelle) :")
    for idx, row in ecoevents_sept.head(3).iterrows():
        print(f"   {row['datetime_utc']} - {row['country']} - {row['event_name']}")
    print()
    
    print("INTERPRÉTATION :")
    print("-" * 80)
    print()
    print("Si CPI US publié à 14:30 Bern (12:30 UTC) :")
    print("   → events montre quelle heure ?")
    print("   → economic_events montre 12:30 → donc UTC ✅")
    print()
    
    conn.close()
    
    print("=" * 80)


if __name__ == '__main__':
    compare_events_tables()
