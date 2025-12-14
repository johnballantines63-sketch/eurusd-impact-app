"""
Vérification rapide des event_key pour inflation/CPI
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'app'))

from config import get_db_path
import duckdb

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 70)
print("🔍 Recherche événements inflation/CPI")
print("=" * 70)

# Chercher événements avec "inflation" ou "cpi" dans event_title ou event_key
query = """
SELECT DISTINCT 
    event_key,
    event_title,
    COUNT(*) as count
FROM events
WHERE country = 'US'
    AND (
        LOWER(event_title) LIKE '%inflation%'
        OR LOWER(event_title) LIKE '%cpi%'
        OR LOWER(event_key) LIKE '%inflation%'
        OR LOWER(event_key) LIKE '%cpi%'
    )
GROUP BY event_key, event_title
ORDER BY count DESC
LIMIT 20
"""

results = conn.execute(query).fetchdf()
print("\nÉvénements trouvés:")
print(results.to_string(index=False))

# Chercher dates récentes
query2 = """
SELECT DISTINCT 
    DATE(ts_utc) as date,
    event_title,
    actual,
    previous,
    estimate
FROM events
WHERE country = 'US'
    AND (LOWER(event_title) LIKE '%inflation%' OR LOWER(event_title) LIKE '%cpi%')
    AND actual IS NOT NULL
ORDER BY date DESC
LIMIT 10
"""

dates = conn.execute(query2).fetchdf()
print("\n📅 Dates récentes avec inflation/CPI:")
print(dates.to_string(index=False))

conn.close()
print("\n" + "=" * 70)
