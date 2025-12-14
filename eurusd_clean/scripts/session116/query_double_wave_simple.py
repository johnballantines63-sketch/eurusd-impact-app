"""
REQUÊTE SIMPLE - Candidats Double Wave
=======================================

Script SQL direct pour identifier rapidement les dates potentielles.

Date: 06 novembre 2025 - Session 116
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import DB_PATH

# Connexion DB
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*70)
print("RECHERCHE DATES AVEC 2 CLUSTERS DISTINCTS")
print("="*70)

# Requête: Dates avec événements HIGH, groupés par heure
query = """
WITH high_impact_events AS (
    SELECT 
        DATE(ts_utc) as event_date,
        HOUR(ts_utc) as event_hour,
        MINUTE(ts_utc) as event_minute,
        ts_utc,
        event_key,
        country,
        actual,
        estimate,
        previous,
        importance_n,
        CASE 
            WHEN actual IS NOT NULL AND estimate IS NOT NULL AND estimate != 0 THEN
                ABS(((actual - estimate) / estimate) * 100)
            WHEN actual IS NOT NULL AND previous IS NOT NULL AND previous != 0 THEN
                ABS(((actual - previous) / previous) * 100)
            ELSE 0
        END as surprise_pct
    FROM events
    WHERE ts_utc >= '2024-01-01'
        AND ts_utc < '2025-11-06'
        AND importance_n = 3  -- HIGH seulement
        AND country IN ('US', 'DE', 'EU')
        AND (actual IS NOT NULL OR estimate IS NOT NULL)
),

dates_with_clusters AS (
    SELECT 
        event_date,
        COUNT(DISTINCT CONCAT(event_hour, '-', FLOOR(event_minute/10))) as time_slots,
        COUNT(*) as total_events,
        MAX(surprise_pct) as max_surprise,
        AVG(surprise_pct) as avg_surprise
    FROM high_impact_events
    GROUP BY event_date
    HAVING time_slots = 2  -- Exactement 2 slots temporels différents
        AND total_events >= 2
        AND MAX(surprise_pct) > 15
)

SELECT 
    h.event_date,
    h.ts_utc,
    h.event_key,
    h.country,
    h.actual,
    h.estimate,
    h.surprise_pct,
    d.total_events,
    d.max_surprise
FROM high_impact_events h
INNER JOIN dates_with_clusters d ON h.event_date = d.event_date
ORDER BY h.event_date DESC, h.ts_utc
LIMIT 200
"""

df = conn.execute(query).fetchdf()

print(f"\n✅ {len(df)} événements sur {df['event_date'].nunique()} dates trouvés\n")

if df.empty:
    print("❌ Aucun résultat. Élargir les critères.")
    conn.close()
    sys.exit(1)

# Afficher par date
print("TOP CANDIDATS:\n" + "="*70)

for date in df['event_date'].unique()[:10]:
    date_events = df[df['event_date'] == date].sort_values('ts_utc')
    
    print(f"\n📅 {date}")
    print(f"   Total events: {len(date_events)}")
    
    for idx, row in date_events.iterrows():
        time_str = pd.to_datetime(row['ts_utc']).strftime('%H:%M')
        print(f"   {time_str} | {row['country']} | {row['event_key'][:50]} | Surprise: {row['surprise_pct']:.1f}%")

print("\n" + "="*70)
print("Examiner ces dates graphiquement pour confirmer pullback profond.")
print("="*70)

conn.close()
