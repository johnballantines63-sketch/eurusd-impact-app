#!/usr/bin/env python3
"""Trouver TOUS les événements US du 11 septembre 2025"""

import duckdb

con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("=" * 80)
print("TOUS LES ÉVÉNEMENTS US DU 11 SEPTEMBRE 2025")
print("=" * 80)

events = con.execute("""
    SELECT 
        ts_utc,
        event_key,
        event_title,
        country,
        actual,
        forecast,
        previous,
        CASE 
            WHEN forecast IS NOT NULL AND forecast != 0 
            THEN ROUND(ABS((actual - forecast) / forecast) * 100, 2)
            ELSE NULL
        END as surprise_pct
    FROM events
    WHERE ts_utc::DATE = '2025-09-11'
    AND country = 'US'
    ORDER BY ts_utc, surprise_pct DESC
""").fetchdf()

print(f"\nTotal événements US le 11 sept: {len(events)}\n")
print(events.to_string(index=False))

print("\n" + "=" * 80)
print("ÉVÉNEMENTS AVEC SURPRISE > 30%")
print("=" * 80)

high_surprise = events[events['surprise_pct'] > 30].copy()
if len(high_surprise) > 0:
    print(high_surprise.to_string(index=False))
else:
    print("Aucun événement avec surprise > 30%")

con.close()
