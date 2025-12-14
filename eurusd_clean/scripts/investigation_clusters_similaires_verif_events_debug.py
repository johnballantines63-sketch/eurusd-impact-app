#!/usr/bin/env python3
"""
DEBUG - Vérification événements autour de 12:30 et 12:45 UTC le 11 septembre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = "data/warehouse.duckdb"
REFERENCE_DATE = "2025-09-11"

def main():
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    print("=" * 80)
    print("DEBUG - ÉVÉNEMENTS 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    # Vérifier tous les événements US le 11 septembre entre 12:00 et 13:00 UTC
    query = """
    SELECT 
        ts_utc,
        strftime(ts_utc, '%H:%M:%S') as heure_utc,
        event_key,
        country,
        importance_n
    FROM events
    WHERE DATE(ts_utc) = ?
      AND country = 'US'
      AND importance_n >= 2
      AND strftime(ts_utc, '%H') = '12'
    ORDER BY ts_utc, event_key
    """
    
    df_us = conn.execute(query, [REFERENCE_DATE]).df()
    
    print(f"\n📊 Événements US le {REFERENCE_DATE} entre 12:00 et 12:59 UTC :")
    print(f"   Total : {len(df_us)} événements\n")
    
    if len(df_us) > 0:
        for idx, row in df_us.iterrows():
            print(f"   {row['heure_utc']} - {row['event_key']:<50} (importance: {row['importance_n']})")
    else:
        print("   ❌ Aucun événement trouvé")
    
    # Vérifier tous les "current account" le 11 septembre entre 12:00 et 13:00 UTC
    query_ca = """
    SELECT 
        ts_utc,
        strftime(ts_utc, '%H:%M:%S') as heure_utc,
        event_key,
        country,
        importance_n
    FROM events
    WHERE DATE(ts_utc) = ?
      AND LOWER(event_key) LIKE '%current account%'
      AND importance_n >= 2
      AND strftime(ts_utc, '%H') = '12'
    ORDER BY ts_utc, country, event_key
    """
    
    df_ca = conn.execute(query_ca, [REFERENCE_DATE]).df()
    
    print(f"\n📊 Événements 'current account' le {REFERENCE_DATE} entre 12:00 et 12:59 UTC :")
    print(f"   Total : {len(df_ca)} événements\n")
    
    if len(df_ca) > 0:
        for idx, row in df_ca.iterrows():
            print(f"   {row['heure_utc']} - {row['event_key']:<50} (country: {row['country']}, importance: {row['importance_n']})")
    else:
        print("   ❌ Aucun événement trouvé")
    
    # Vérifier tous les événements (tous pays) le 11 septembre entre 12:00 et 13:00 UTC
    query_all = """
    SELECT 
        ts_utc,
        strftime(ts_utc, '%H:%M:%S') as heure_utc,
        event_key,
        country,
        importance_n
    FROM events
    WHERE DATE(ts_utc) = ?
      AND importance_n >= 2
      AND strftime(ts_utc, '%H') = '12'
    ORDER BY ts_utc, country, event_key
    LIMIT 50
    """
    
    df_all = conn.execute(query_all, [REFERENCE_DATE]).df()
    
    print(f"\n📊 Tous événements (tous pays) le {REFERENCE_DATE} entre 12:00 et 12:59 UTC :")
    print(f"   Total (limité à 50) : {len(df_all)} événements\n")
    
    if len(df_all) > 0:
        for idx, row in df_all.iterrows():
            print(f"   {row['heure_utc']} - [{row['country']}] {row['event_key']:<45} (importance: {row['importance_n']})")
    else:
        print("   ❌ Aucun événement trouvé")
    
    conn.close()
    return 0

if __name__ == "__main__":
    exit(main())

