#!/usr/bin/env python3
"""Vérifier pourquoi JOIN event_families ne fonctionne pas"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

print("ÉVÉNEMENTS 11 SEPT DANS economic_events :")
events = conn.execute("""
    SELECT event_name, country, COUNT(*) as count
    FROM economic_events
    WHERE datetime_utc >= '2025-09-11 12:30:00'
      AND datetime_utc < '2025-09-11 12:31:00'
      AND country = 'US'
    GROUP BY event_name, country
    LIMIT 5
""").df()
print(events)
print()

print("SCORES DANS event_families (US) :")
scores = conn.execute("""
    SELECT event_key, country, empirical_score
    FROM event_families
    WHERE UPPER(country) = 'US'
      AND event_key LIKE '%cpi%'
    LIMIT 10
""").df()
print(scores)
print()

print("TEST JOIN :")
test = conn.execute("""
    SELECT 
        e.event_name,
        e.country as e_country,
        ef.event_key,
        ef.country as ef_country,
        ef.empirical_score
    FROM economic_events e
    LEFT JOIN event_families ef 
        ON LOWER(e.event_name) = LOWER(ef.event_key)
        AND UPPER(e.country) = UPPER(ef.country)
    WHERE e.datetime_utc >= '2025-09-11 12:30:00'
      AND e.datetime_utc < '2025-09-11 12:31:00'
      AND e.country = 'US'
    LIMIT 5
""").df()
print(test)

conn.close()
