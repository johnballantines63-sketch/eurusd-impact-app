"""
Requête SQL directe - Top candidats manuels
===========================================

Cherche dates spécifiques avec événements majeurs connus.
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
print("CANDIDATS MANUELS - DATES SPÉCIFIQUES")
print("="*70)

# Dates candidates basées sur calendrier économique
target_dates = [
    '2025-09-11',  # Référence validée
    '2025-06-05',  # ECB + US
    '2025-07-03',  # NFP
    '2025-06-06',  # NFP
    '2025-03-07',  # NFP
    '2024-12-18',  # FOMC
    '2024-11-01',  # NFP
    '2024-09-18',  # FOMC
    '2024-08-14',  # CPI
    '2024-07-11',  # CPI
]

for target_date in target_dates[:10]:
    query = f"""
    SELECT 
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
    WHERE DATE(ts_utc) = '{target_date}'
        AND importance_n >= 2
        AND country IN ('US', 'DE', 'EU')
        AND actual IS NOT NULL
    ORDER BY ts_utc
    """
    
    df = conn.execute(query).fetchdf()
    
    if len(df) >= 2:
        print(f"\n📅 {target_date} - {len(df)} événements")
        
        # Analyser timing
        df['ts_pd'] = pd.to_datetime(df['ts_utc'])
        times = df['ts_pd'].values
        
        # Détecter clusters
        clusters = [[0]]
        for i in range(1, len(times)):
            gap = (pd.Timestamp(times[i]) - pd.Timestamp(times[i-1])).total_seconds() / 60
            if gap <= 5:
                clusters[-1].append(i)
            else:
                clusters.append([i])
        
        print(f"   {len(clusters)} cluster(s) détecté(s)")
        
        # Si 2 clusters, analyser
        if len(clusters) == 2:
            c1 = df.iloc[clusters[0]]
            c2 = df.iloc[clusters[1]]
            
            t1 = pd.to_datetime(c1.iloc[0]['ts_utc'])
            t2 = pd.to_datetime(c2.iloc[0]['ts_utc'])
            gap = (t2 - t1).total_seconds() / 60
            
            s1_max = c1['surprise_pct'].max()
            s2_max = c2['surprise_pct'].max()
            
            print(f"   Cluster 1: {t1.strftime('%H:%M')} ({len(c1)} events) - Surprise max: {s1_max:.1f}%")
            print(f"   Cluster 2: {t2.strftime('%H:%M')} ({len(c2)} events) - Surprise max: {s2_max:.1f}%")
            print(f"   Gap: {gap:.0f} min")
            
            if 10 <= gap <= 25 and (s1_max > 10 or s2_max > 10):
                print(f"   ✅ BON CANDIDAT DOUBLE WAVE")
        else:
            # Afficher tous les events
            for idx, row in df.iterrows():
                t = pd.to_datetime(row['ts_utc']).strftime('%H:%M')
                s = row['surprise_pct']
                print(f"   {t} | {row['country']} | {row['event_key'][:40]:40s} | {s:.1f}%")

conn.close()

print("\n" + "="*70)
print("CANDIDATS VALIDÉS: Chercher lignes avec ✅")
print("="*70)
