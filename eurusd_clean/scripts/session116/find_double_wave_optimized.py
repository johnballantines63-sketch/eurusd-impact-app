"""
Recherche optimisée Double Wave patterns
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
print("RECHERCHE DOUBLE WAVE - OPTIMISÉE")
print("="*70)

# Chercher dates avec événements espacés 10-25 min
query = """
WITH events_major AS (
    SELECT 
        DATE(ts_utc) as event_date,
        ts_utc,
        event_key,
        country,
        actual,
        estimate,
        importance_n,
        CASE 
            WHEN actual IS NOT NULL AND estimate IS NOT NULL AND ABS(estimate) > 0.001 THEN
                ABS(((actual - estimate) / estimate) * 100)
            WHEN actual IS NOT NULL AND previous IS NOT NULL AND ABS(previous) > 0.001 THEN
                ABS(((actual - previous) / previous) * 100)
            ELSE NULL
        END as surprise_pct
    FROM events
    WHERE ts_utc >= '2024-01-01'
        AND ts_utc < '2025-11-06'
        AND importance_n >= 2
        AND country IN ('US', 'DE', 'EU')
        AND actual IS NOT NULL
)
SELECT *
FROM events_major
WHERE surprise_pct > 5
ORDER BY event_date DESC, ts_utc
LIMIT 300
"""

df = conn.execute(query).fetchdf()
conn.close()

print(f"✅ {len(df)} événements avec surprise > 5%\n")

# Grouper par date et analyser clusters
dates_dict = {}
for date in df['event_date'].unique():
    date_events = df[df['event_date'] == date].sort_values('ts_utc')
    if len(date_events) >= 2:
        dates_dict[date] = date_events

print(f"📅 {len(dates_dict)} dates avec 2+ événements\n")

# Analyser clusters
candidates = []
for date, events in list(dates_dict.items())[:20]:
    events['ts_pd'] = pd.to_datetime(events['ts_utc'])
    times = events['ts_pd'].values
    
    # Détecter clusters (< 5 min = même cluster)
    clusters = [[0]]
    for i in range(1, len(times)):
        gap = (pd.Timestamp(times[i]) - pd.Timestamp(times[i-1])).total_seconds() / 60
        if gap <= 5:
            clusters[-1].append(i)
        else:
            clusters.append([i])
    
    # Vérifier 2 clusters avec gap 10-25 min
    if len(clusters) == 2:
        c1 = events.iloc[clusters[0]]
        c2 = events.iloc[clusters[1]]
        
        t1 = pd.to_datetime(c1.iloc[0]['ts_utc'])
        t2 = pd.to_datetime(c2.iloc[0]['ts_utc'])
        gap = (t2 - t1).total_seconds() / 60
        
        if 10 <= gap <= 25:
            s1 = c1['surprise_pct'].max()
            s2 = c2['surprise_pct'].max()
            
            if s1 > 10 or s2 > 10:
                candidates.append({
                    'date': date,
                    'c1_time': t1.strftime('%H:%M'),
                    'c1_n': len(c1),
                    'c1_surprise': s1,
                    'c2_time': t2.strftime('%H:%M'),
                    'c2_n': len(c2),
                    'c2_surprise': s2,
                    'gap': gap
                })

print("CANDIDATS DOUBLE WAVE:\n" + "="*70)
for c in candidates[:10]:
    print(f"📅 {c['date']}")
    print(f"   C1: {c['c1_time']} ({c['c1_n']} events) - Surprise: {c['c1_surprise']:.1f}%")
    print(f"   C2: {c['c2_time']} ({c['c2_n']} events) - Surprise: {c['c2_surprise']:.1f}%")
    print(f"   Gap: {c['gap']:.0f} min\n")
