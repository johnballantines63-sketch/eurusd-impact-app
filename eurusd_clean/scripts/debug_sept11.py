#!/usr/bin/env python3
"""Debug: Vérifier événements 11 septembre 2025"""

import duckdb
import pandas as pd

db_path = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb"
conn = duckdb.connect(db_path, read_only=True)

print("=" * 70)
print("DEBUG - ÉVÉNEMENTS 11 SEPTEMBRE 2025")
print("=" * 70)

# 1. Tous événements du 11 septembre
print("\n1️⃣ TOUS les événements du 11 septembre 2025:")
result1 = conn.execute("""
    SELECT 
        ts_utc,
        country,
        event_title,
        importance_n
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
    ORDER BY ts_utc
""").fetchdf()

print(f"Total : {len(result1)} événements")
if len(result1) > 0:
    print(result1[['ts_utc', 'country', 'event_title', 'importance_n']])

# 2. Événements US haute importance
print("\n" + "=" * 70)
print("2️⃣ Événements US importance_n >= 3:")
result2 = conn.execute("""
    SELECT 
        ts_utc,
        country,
        event_title,
        importance_n
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
      AND country = 'US'
      AND importance_n >= 3
    ORDER BY ts_utc
""").fetchdf()

print(f"Total : {len(result2)} événements")
if len(result2) > 0:
    print(result2)
else:
    print("❌ Aucun trouvé !")
    
    # Vérifier les valeurs d'importance
    print("\n3️⃣ Distribution importance_n pour US le 11 sept:")
    result3 = conn.execute("""
        SELECT 
            importance_n,
            COUNT(*) as count
        FROM events
        WHERE DATE(ts_utc) = '2025-09-11'
          AND country = 'US'
        GROUP BY importance_n
        ORDER BY importance_n
    """).fetchdf()
    print(result3)

# 4. Avec jointure event_families
print("\n" + "=" * 70)
print("4️⃣ Avec jointure event_families:")
result4 = conn.execute("""
    SELECT 
        e.ts_utc,
        e.country,
        e.event_title,
        e.importance_n,
        ef.family,
        ef.avg_movement_pips
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '2025-09-11'
      AND e.country = 'US'
      AND e.importance_n >= 3
    LIMIT 5
""").fetchdf()

print(f"Total : {len(result4)} événements")
if len(result4) > 0:
    print(result4)

conn.close()
