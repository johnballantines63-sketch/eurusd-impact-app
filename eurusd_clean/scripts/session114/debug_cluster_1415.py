"""
DEBUG: Voir ce qu'est le cluster 14:15
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
print("CLUSTER 14:15 - QU'EST-CE QUE C'EST ?")
print("="*70)
print()

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
    AND e.ts_utc >= '2025-09-11 14:10:00'
    AND e.ts_utc <= '2025-09-11 14:20:00'
    AND e.country IN ('US', 'DE', 'EU')
    AND ef.empirical_score IS NOT NULL
ORDER BY e.ts_utc, e.country, e.event_key
"""

df = conn.execute(query).df()

print(f"Événements entre 14:10 et 14:20 : {len(df)}")
print()

for idx, row in df.iterrows():
    score = row['empirical_score'] if not pd.isna(row['empirical_score']) else 'N/A'
    estimate = 'OUI' if not pd.isna(row['estimate']) else 'NON'
    print(f"{row['ts_utc']} | {row['country']:3} | {row['event_key']:30} | Score: {score:>6} | Estimate: {estimate}")

print()
print("="*70)
print("CONCLUSION:")
print("="*70)
print()

if len(df) > 0 and df['country'].iloc[0] in ['DE', 'EU']:
    print("❌ Ces événements sont européens (DE/EU)")
    print("   Ils n'ont PAS d'impact direct sur EUR/USD comme les US")
    print("   Il faut les FILTRER du test")
    print()
    print("SOLUTION: Ne charger que les événements US dans le test")
    print("   Car on teste l'impact sur EUR/USD causé par US news")
elif len(df) > 0:
    print("⚠️ Ces événements sont US")
    print("   Mais ils arrivent 15 min AVANT le cluster principal")
    print("   Pattern overlapping = event PENDANT pullback, pas AVANT")
else:
    print("✅ Aucun événement trouvé (normal)")

print()
print("="*70)
