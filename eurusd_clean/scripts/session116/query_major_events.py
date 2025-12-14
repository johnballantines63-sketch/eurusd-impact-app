"""
Requête ciblée - Événements majeurs EUR/USD seulement
======================================================

Focus sur événements à fort impact connus.
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import DB_PATH

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*70)
print("CANDIDATS DOUBLE WAVE - ÉVÉNEMENTS MAJEURS UNIQUEMENT")
print("="*70)

# Liste événements à fort impact EUR/USD
major_events = [
    'cpi',
    'core cpi',
    'inflation rate',
    'core inflation rate',
    'nonfarm payrolls',
    'non farm payrolls',
    'unemployment rate',
    'fomc',
    'fed interest rate decision',
    'ecb interest rate decision',
    'gdp growth rate',
    'retail sales',
    'pmi'
]

events_filter = "(" + " OR ".join([f"LOWER(event_key) LIKE '%{e}%'" for e in major_events]) + ")"

query = f"""
WITH major_events AS (
    SELECT 
        DATE(ts_utc) as event_date,
        ts_utc,
        event_key,
        country,
        actual,
        estimate,
        previous,
        importance_n
    FROM events
    WHERE ts_utc >= '2024-01-01'
        AND ts_utc < '2025-11-06'
        AND importance_n = 3
        AND country IN ('US', 'DE', 'EU')
        AND {events_filter}
        AND (actual IS NOT NULL OR estimate IS NOT NULL)
),

dates_grouped AS (
    SELECT 
        event_date,
        COUNT(*) as total_events,
        COUNT(DISTINCT HOUR(ts_utc)) as distinct_hours,
        MIN(ts_utc) as first_event,
        MAX(ts_utc) as last_event
    FROM major_events
    GROUP BY event_date
    HAVING total_events >= 2
        AND distinct_hours >= 1  -- Au moins dans différentes heures
)

SELECT 
    m.event_date,
    m.ts_utc,
    m.event_key,
    m.country,
    m.actual,
    m.estimate,
    m.previous,
    d.total_events,
    EXTRACT(EPOCH FROM (d.last_event - d.first_event))/60 as time_span_minutes
FROM major_events m
INNER JOIN dates_grouped d ON m.event_date = d.event_date
WHERE EXTRACT(EPOCH FROM (d.last_event - d.first_event))/60 BETWEEN 10 AND 90
ORDER BY m.event_date DESC, m.ts_utc
LIMIT 150
"""

df = conn.execute(query).fetchdf()
conn.close()

print(f"\n✅ {len(df)} événements sur {df['event_date'].nunique()} dates\n")

if df.empty:
    print("❌ Aucun résultat")
    sys.exit(1)

# Grouper par date
print("CANDIDATS:\n" + "="*70)

for date in df['event_date'].unique()[:15]:
    date_events = df[df['event_date'] == date].sort_values('ts_utc')
    
    if len(date_events) < 2:
        continue
    
    first_time = pd.to_datetime(date_events.iloc[0]['ts_utc'])
    last_time = pd.to_datetime(date_events.iloc[-1]['ts_utc'])
    gap = (last_time - first_time).total_seconds() / 60
    
    print(f"\n📅 {date} - Gap: {gap:.0f} min - Events: {len(date_events)}")
    
    for idx, row in date_events.iterrows():
        time_str = pd.to_datetime(row['ts_utc']).strftime('%H:%M')
        actual = f"{row['actual']:.2f}" if pd.notna(row['actual']) else "N/A"
        estimate = f"{row['estimate']:.2f}" if pd.notna(row['estimate']) else "N/A"
        
        print(f"   {time_str} | {row['country']:2s} | {row['event_key'][:40]:40s} | A:{actual:8s} E:{estimate:8s}")

print("\n" + "="*70)
