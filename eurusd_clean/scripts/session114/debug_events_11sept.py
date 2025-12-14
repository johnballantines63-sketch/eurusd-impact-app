"""
DEBUG: Vérifier événements 11 septembre dans la DB
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
print("DEBUG: ÉVÉNEMENTS 11 SEPTEMBRE 2025")
print("="*70)
print()

# Requête TOUS les événements US du 11 septembre
query = """
SELECT 
    e.event_key,
    e.event_title,
    e.ts_utc,
    e.actual,
    e.estimate,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
ORDER BY e.ts_utc, e.event_key
"""

df = conn.execute(query).df()

print(f"Total événements US trouvés: {len(df)}")
print()

# Grouper par heure
df['hour'] = df['ts_utc'].astype(str).str[11:16]

for hour in df['hour'].unique():
    events_at_hour = df[df['hour'] == hour]
    print(f"Heure {hour}: {len(events_at_hour)} événement(s)")
    
    for idx, row in events_at_hour.iterrows():
        score = row['empirical_score'] if not pd.isna(row['empirical_score']) else 'N/A'
        estimate = 'OUI' if not pd.isna(row['estimate']) else 'NON'
        print(f"  - {row['event_key']:30} | Score: {score:>6} | Estimate: {estimate}")
    print()

# Compter ceux avec score
with_score = df[df['empirical_score'].notna()]
print(f"Avec empirical_score: {len(with_score)}")

with_estimate = df[df['estimate'].notna()]
print(f"Avec estimate: {len(with_estimate)}")

both = df[(df['empirical_score'].notna()) & (df['estimate'].notna())]
print(f"Avec SCORE ET ESTIMATE: {len(both)}")
print()

print("="*70)
print("ÉVÉNEMENTS ATTENDUS SELON SESSION 113 (9 à 14:30):")
print("="*70)
print("1. cpi s.a")
print("2. inflation rate_mom")
print("3. cpi")
print("4. core inflation rate_yoy")
print("5. core inflation rate_mom")
print("6. jobless claims 4-week average")
print("7. inflation rate_yoy")
print("8. initial jobless claims")
print("9. continuing jobless claims")
print()
