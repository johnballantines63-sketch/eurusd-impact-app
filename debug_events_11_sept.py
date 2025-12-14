import sys
from pathlib import Path
import duckdb

src_path = Path(__file__).parent / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

query = """
SELECT 
    e.event_key,
    e.label,
    e.ts_utc,
    e.actual,
    e.estimate,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
ORDER BY e.ts_utc
"""

df = conn.execute(query).df()
print(f"\n📊 Événements 11 septembre 2025 : {len(df)} trouvés\n")
print(df.to_string())
conn.close()
