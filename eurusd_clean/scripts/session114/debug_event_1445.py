"""
DEBUG: Chercher événement 14:45 (Current Account)
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import config

conn = duckdb.connect(str(config.DB_PATH))

print("="*70)
print("RECHERCHE ÉVÉNEMENT 14:45 - CURRENT ACCOUNT")
print("="*70)
print()

# Chercher événements entre 14:35 et 15:00
query = """
SELECT 
    e.event_key,
    e.event_title,
    e.ts_utc,
    e.country,
    e.actual,
    e.estimate,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.ts_utc >= '2025-09-11 14:35:00'
    AND e.ts_utc <= '2025-09-11 15:00:00'
ORDER BY e.ts_utc, e.event_key
"""

df = conn.execute(query).df()

print(f"Événements entre 14:35 et 15:00 : {len(df)}")
print()

if len(df) == 0:
    print("❌ Aucun événement trouvé dans cette plage !")
    print()
    print("Recherche 'current account' dans toute la journée...")
    
    query2 = """
    SELECT 
        e.event_key,
        e.event_title,
        e.ts_utc,
        e.country,
        e.actual,
        e.estimate,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '2025-09-11'
        AND LOWER(e.event_key) LIKE '%current%account%'
    ORDER BY e.ts_utc
    """
    
    df2 = conn.execute(query2).df()
    
    if len(df2) == 0:
        print("❌ Aucun 'current account' trouvé le 11 septembre !")
        print()
        print("Recherche dans d'autres pays...")
        
        query3 = """
        SELECT 
            e.event_key,
            e.event_title,
            e.ts_utc,
            e.country
        FROM events e
        WHERE DATE(e.ts_utc) = '2025-09-11'
            AND e.ts_utc >= '2025-09-11 14:45:00'
            AND e.ts_utc < '2025-09-11 14:46:00'
        ORDER BY e.country, e.event_key
        """
        
        df3 = conn.execute(query3).df()
        print(f"Événements à 14:45 (tous pays) : {len(df3)}")
        
        if len(df3) > 0:
            for idx, row in df3.iterrows():
                print(f"  {row['country']:3} | {row['ts_utc']} | {row['event_key']}")
    else:
        print(f"✅ Trouvé {len(df2)} 'current account' :")
        for idx, row in df2.iterrows():
            print(f"  {row['ts_utc']} | {row['country']} | {row['event_key']}")
else:
    print("✅ Événements trouvés :")
    for idx, row in df.iterrows():
        score = row['empirical_score'] if not pd.isna(row['empirical_score']) else 'N/A'
        estimate = 'OUI' if not pd.isna(row['estimate']) else 'NON'
        print(f"  {row['ts_utc']} | {row['country']:3} | {row['event_key']:30} | Score: {score} | Estimate: {estimate}")

print()
print("="*70)
