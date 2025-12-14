#!/usr/bin/env python3
"""
SESSION 126 - EXPLORATION EVENT_KEYS
Identifier event_keys pour Retail Sales et Fed Interest Rate Decision
"""
import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("SESSION 126 - EXPLORATION EVENT_KEYS (Retail Sales + Fed Interest Rate)")
print("="*80)
print()

# ═══════════════════════════════════════════════════════════════════════════
# 1. RETAIL SALES
# ═══════════════════════════════════════════════════════════════════════════
print("🛒 RETAIL SALES :")
print("-" * 80)

query_retail = """
SELECT 
    event_key,
    event_title,
    COUNT(*) as count,
    MIN(ts_utc) as first_date,
    MAX(ts_utc) as last_date
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND (
    LOWER(event_key) LIKE '%retail%'
    OR LOWER(event_title) LIKE '%retail%'
  )
GROUP BY event_key, event_title
ORDER BY count DESC
"""

df_retail = conn.execute(query_retail).df()

if len(df_retail) > 0:
    for idx, row in df_retail.iterrows():
        title = row['event_title'] if pd.notna(row['event_title']) else "(null)"
        print(f"   {row['count']:3d}× [{row['first_date']:%Y-%m-%d} → {row['last_date']:%Y-%m-%d}]")
        print(f"       event_key   : {row['event_key']}")
        print(f"       event_title : {title}")
        print()
else:
    print("   ❌ Aucun événement Retail Sales trouvé (importance_n=3)")
    print()

# ═══════════════════════════════════════════════════════════════════════════
# 2. FED INTEREST RATE DECISION
# ═══════════════════════════════════════════════════════════════════════════
print("🏦 FED INTEREST RATE DECISION :")
print("-" * 80)

query_fed = """
SELECT 
    event_key,
    event_title,
    COUNT(*) as count,
    MIN(ts_utc) as first_date,
    MAX(ts_utc) as last_date
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND (
    (LOWER(event_key) LIKE '%fed%' AND LOWER(event_key) LIKE '%rate%')
    OR (LOWER(event_title) LIKE '%fed%' AND LOWER(event_title) LIKE '%rate%')
    OR LOWER(event_key) LIKE '%fomc%'
    OR LOWER(event_title) LIKE '%fomc%'
  )
GROUP BY event_key, event_title
ORDER BY count DESC
"""

df_fed = conn.execute(query_fed).df()

if len(df_fed) > 0:
    for idx, row in df_fed.iterrows():
        title = row['event_title'] if pd.notna(row['event_title']) else "(null)"
        print(f"   {row['count']:3d}× [{row['first_date']:%Y-%m-%d} → {row['last_date']:%Y-%m-%d}]")
        print(f"       event_key   : {row['event_key']}")
        print(f"       event_title : {title}")
        print()
else:
    print("   ❌ Aucun événement Fed trouvé (importance_n=3)")
    print()

# ═══════════════════════════════════════════════════════════════════════════
# 3. TOUS LES HIGH US (RÉFÉRENCE)
# ═══════════════════════════════════════════════════════════════════════════
print("📋 TOP 20 EVENT_KEYS HIGH US (2023-2025) :")
print("-" * 80)

query_top = """
SELECT 
    event_key,
    COUNT(*) as count
FROM events
WHERE country = 'US'
  AND importance_n = 3
  AND ts_utc >= '2023-01-01'
GROUP BY event_key
ORDER BY count DESC
LIMIT 20
"""

df_top = conn.execute(query_top).df()

for idx, row in df_top.iterrows():
    print(f"   {row['count']:3d}× {row['event_key']}")

print()
print("="*80)

conn.close()
