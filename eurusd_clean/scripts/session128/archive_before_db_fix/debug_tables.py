#!/usr/bin/env python3
"""
DEBUG : Vérifier TOUTES les tables pour 11 septembre 2025
"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

# Lister toutes les tables
print("=" * 80)
print("TOUTES LES TABLES DISPONIBLES")
print("=" * 80)
result = conn.execute("SHOW TABLES").df()
print(result)
print()

# Vérifier table events
print("=" * 80)
print("TABLE EVENTS")
print("=" * 80)
result = conn.execute("""
    SELECT COUNT(*) as total, MIN(ts_utc) as min_date, MAX(ts_utc) as max_date
    FROM events
    WHERE country = 'US' AND importance_n = 3
""").df()
print(result)
print()

# Vérifier table economic_events si elle existe
try:
    print("=" * 80)
    print("TABLE ECONOMIC_EVENTS")
    print("=" * 80)
    
    # Structure
    result = conn.execute("DESCRIBE economic_events").df()
    print("Colonnes :")
    print(result[['column_name', 'column_type']].head(10))
    print()
    
    # Comptage
    result = conn.execute("""
        SELECT COUNT(*) as total
        FROM economic_events
    """).df()
    print(f"Total événements : {result['total'].iloc[0]}")
    print()
    
    # Dates min/max
    # Trouver la colonne de date
    cols = conn.execute("DESCRIBE economic_events").df()
    date_col = None
    for col in ['ts_utc', 'datetime', 'date', 'event_time']:
        if col in cols['column_name'].values:
            date_col = col
            break
    
    if date_col:
        result = conn.execute(f"""
            SELECT MIN({date_col}) as min_date, MAX({date_col}) as max_date
            FROM economic_events
        """).df()
        print(f"Période : {result['min_date'].iloc[0]} → {result['max_date'].iloc[0]}")
        print()
        
        # Chercher 11 septembre
        result = conn.execute(f"""
            SELECT COUNT(*) as count
            FROM economic_events
            WHERE DATE({date_col}) = '2025-09-11'
        """).df()
        print(f"Événements 11 septembre 2025 : {result['count'].iloc[0]}")
        
except Exception as e:
    print(f"Table economic_events n'existe pas ou erreur : {e}")
    print()

conn.close()
