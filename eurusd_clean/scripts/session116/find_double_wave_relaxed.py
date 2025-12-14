"""
Recherche ÉLARGIE - Critères assouplis
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
print("RECHERCHE DOUBLE WAVE - CRITÈRES ÉLARGIS")
print("="*70)

query = """
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
    AND (
        LOWER(event_key) LIKE '%cpi%' OR
        LOWER(event_key) LIKE '%inflation%' OR
        LOWER(event_key) LIKE '%nonfarm%' OR
        LOWER(event_key) LIKE '%unemployment%' OR
        LOWER(event_key) LIKE '%fomc%' OR
        LOWER(event_key) LIKE '%ecb%' OR
        LOWER(event_key) LIKE '%current account%' OR
        LOWER(event_key) LIKE '%jobless%'
    )
ORDER BY event_date DESC, ts_utc
LIMIT 500
"""

df = conn.execute(query).fetchdf()
conn.close()

print(f"✅ {len(df)} événements majeurs trouvés\n")

# Analyser par date
candidates = []
for date in df['event_date'].unique()[:30]:
    events = df[df['event_date'] == date].sort_values('ts_utc')
    
    if len(events) < 2:
        continue
    
    events['ts_pd'] = pd.to_datetime(events['ts_utc'])
    times = events['ts_pd'].values
    
    # Détecter clusters (< 5 min)
    clusters = [[0]]
    for i in range(1, len(times)):
        gap = (pd.Timestamp(times[i]) - pd.Timestamp(times[i-1])).total_seconds() / 60
        if gap <= 5:
            clusters[-1].append(i)
        else:
            clusters.append([i])
    
    # Accepter 2 OU 3 clusters (élargi)
    if 2 <= len(clusters) <= 3:
        c1 = events.iloc[clusters[0]]
        c2 = events.iloc[clusters[1]]
        
        t1 = pd.to_datetime(c1.iloc[0]['ts_utc'])
        t2 = pd.to_datetime(c2.iloc[0]['ts_utc'])
        gap = (t2 - t1).total_seconds() / 60
        
        # Élargir gap 10-30 min (au lieu de 10-25)
        # Élargir surprise > 5% (au lieu de > 10%)
        if 10 <= gap <= 30:
            s1_max = c1['surprise_pct'].max() if pd.notna(c1['surprise_pct'].max()) else 0
            s2_max = c2['surprise_pct'].max() if pd.notna(c2['surprise_pct'].max()) else 0
            
            if s1_max > 5 or s2_max > 5:
                candidates.append({
                    'date': date,
                    'c1_time': t1.strftime('%H:%M'),
                    'c1_n': len(c1),
                    'c1_surprise': s1_max,
                    'c1_keys': ', '.join(c1['event_key'].head(2).values),
                    'c2_time': t2.strftime('%H:%M'),
                    'c2_n': len(c2),
                    'c2_surprise': s2_max,
                    'c2_keys': ', '.join(c2['event_key'].head(2).values),
                    'gap': gap,
                    'num_clusters': len(clusters)
                })

print(f"🎯 {len(candidates)} CANDIDATS trouvés\n")
print("CANDIDATS DOUBLE WAVE:\n" + "="*70)

for c in candidates[:15]:
    print(f"\n📅 {c['date']} - {c['num_clusters']} cluster(s)")
    print(f"   C1: {c['c1_time']} ({c['c1_n']} events) - Surprise: {c['c1_surprise']:.1f}%")
    print(f"   → {c['c1_keys']}")
    print(f"   C2: {c['c2_time']} ({c['c2_n']} events) - Surprise: {c['c2_surprise']:.1f}%")
    print(f"   → {c['c2_keys']}")
    print(f"   Gap: {c['gap']:.0f} min")

print("\n" + "="*70)
