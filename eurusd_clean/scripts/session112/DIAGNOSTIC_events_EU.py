#!/usr/bin/env python3
"""
Diagnostic : Pourquoi événements EU manquants ?
"""
import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
import config

conn = duckdb.connect(str(config.DB_PATH), read_only=True)

date_from = datetime(2025, 11, 5, 10, 0)  # 10:00 UTC
date_to = datetime(2025, 11, 5, 14, 0)    # 14:00 UTC

print("="*80)
print("🔍 ÉVÉNEMENTS EUR/EU 10:00-14:00 UTC")
print("="*80)

# Chercher événements EU
query = f"""
SELECT 
    ts_utc, country, event_title, event_key
FROM events 
WHERE ts_utc >= '{date_from}'
  AND ts_utc <= '{date_to}'
  AND country IN ('EU', 'LU', 'IE', 'DE', 'FR', 'EA')
ORDER BY ts_utc
"""

results = conn.execute(query).fetchall()

print(f"\n📊 {len(results)} événements EU/EUR trouvés:\n")

for row in results[:20]:
    ts, country, title, key = row
    print(f"  {ts} | {country:3} | {title or key}")

if len(results) == 0:
    print("❌ AUCUN événement EU dans cette période !")
    print("\n🔍 Cherchons pays disponibles:")
    
    countries = conn.execute(f"""
        SELECT DISTINCT country 
        FROM events 
        WHERE ts_utc >= '{date_from}'
          AND ts_utc <= '{date_to}'
        ORDER BY country
    """).fetchall()
    
    print("   Pays disponibles:", [c[0] for c in countries])

conn.close()

print("\n" + "="*80)
