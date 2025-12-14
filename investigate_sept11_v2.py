#!/usr/bin/env python3
"""
INVESTIGATION : 11 septembre 2025
Pourquoi seulement 6 événements au lieu de 33 ?
"""

import duckdb
import pandas as pd

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=True)

print("\n1️⃣ TOUS LES ÉVÉNEMENTS DU 11 SEPTEMBRE 2025:\n")

query = """
SELECT 
    e.ts_utc,
    strftime(e.ts_utc, '%H:%M:%S') as time,
    e.event_key,
    e.event_title,
    e.country,
    ef.empirical_score,
    ef.impact_level,
    CASE 
        WHEN ef.empirical_score IS NOT NULL AND ef.empirical_score > 0 THEN 'Inclus'
        ELSE 'EXCLU'
    END as status
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE CAST(e.ts_utc AS DATE) = '2025-09-11'
ORDER BY e.ts_utc
"""

df = conn.execute(query).fetchdf()
print(df.to_string(index=False))

print(f"\n📊 STATISTIQUES:")
print(f"   • Total événements : {len(df)}")
print(f"   • Inclus dans calcul : {(df['status'] == 'Inclus').sum()}")
print(f"   • Exclus : {(df['status'] == 'EXCLU').sum()}")

print("\n2️⃣ REGROUPEMENT PAR TIME_GROUP:\n")

included = df[df['status'] == 'Inclus'].copy()
if len(included) > 0:
    included['time_group'] = pd.to_datetime(included['ts_utc']).dt.floor('1min')
    grouped = included.groupby('time_group').agg({
        'event_key': 'count',
        'event_title': lambda x: ' | '.join(x.head(3)),
        'empirical_score': 'max'
    }).rename(columns={'event_key': 'count'})
    print(grouped)

print("\n3️⃣ POURQUOI CERTAINS SONT EXCLUS ?\n")

excluded = df[df['status'] == 'EXCLU']
if len(excluded) > 0:
    print(f"Raisons d'exclusion pour {len(excluded)} événements:")
    for idx, row in excluded.iterrows():
        reason = []
        if pd.isna(row['empirical_score']):
            reason.append("empirical_score NULL")
        elif row['empirical_score'] <= 0:
            reason.append(f"empirical_score={row['empirical_score']}")
        print(f"  • {row['time']} - {row['event_title']}: {', '.join(reason)}")

print("\n4️⃣ VÉRIFICATION : Événements à 14:30 précisément\n")

events_1430 = df[df['time'] == '14:30:00']
print(f"Événements à 14:30:00 exactement : {len(events_1430)}")
print(events_1430[['time', 'event_title', 'country', 'empirical_score', 'status']].to_string(index=False))

conn.close()
