"""
Vérifier scores Jobless Claims - 11.09.2025
"""

import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root / "app"))

from config import Config
import duckdb

config = Config()
db_path = config.get_db_path()
conn = duckdb.connect(str(db_path))

print("="*80)
print("SCORES JOBLESS CLAIMS - 11.09.2025")
print("="*80)

query = """
SELECT 
    e.ts_utc,
    e.event_key,
    COALESCE(e.event_title, e.event_key) as name,
    e.actual,
    e.estimate,
    ef.family,
    ef.empirical_score
FROM events e
INNER JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND (
        e.event_key LIKE '%jobless%' 
        OR e.event_key LIKE '%unemployment%'
        OR e.event_key LIKE '%claims%'
    )
ORDER BY e.ts_utc, ef.empirical_score DESC
"""

df = conn.execute(query).df()

if df.empty:
    print("\n❌ Aucun événement Jobless/Claims trouvé !")
else:
    print(f"\n✅ {len(df)} événements trouvés :\n")
    for idx, row in df.iterrows():
        score = row['empirical_score']
        status = "✅ HIGH" if score > 40 else "⚠️ MEDIUM" if score > 20 else "❌ LOW"
        print(f"{status} {row['ts_utc']} | {row['name']}")
        print(f"     Score: {score:.1f} | Actual: {row['actual']} | Estimate: {row['estimate']}")
        print()

# Tous événements avec score
print("\n" + "="*80)
print("TOUS ÉVÉNEMENTS US 11.09.2025 (par score)")
print("="*80)

query2 = """
SELECT 
    e.ts_utc,
    e.event_key,
    COALESCE(e.event_title, e.event_key) as name,
    AVG(ef.empirical_score) as avg_score,
    COUNT(*) as n
FROM events e
INNER JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
GROUP BY e.ts_utc, e.event_key, COALESCE(e.event_title, e.event_key)
ORDER BY avg_score DESC
"""

df2 = conn.execute(query2).df()

print(f"\n{len(df2)} événements uniques :\n")
for idx, row in df2.iterrows():
    score = row['avg_score']
    status = "✅ HIGH" if score > 40 else "⚠️ MED" if score > 20 else "❌ LOW"
    print(f"{status} {score:5.1f} | {row['ts_utc']} | {row['name']}")

conn.close()

print("\n" + "="*80)
