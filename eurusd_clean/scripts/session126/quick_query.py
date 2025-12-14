#!/usr/bin/env python3
"""Query rapide pour identifier event_keys"""

import duckdb

conn = duckdb.connect("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb", read_only=True)

# Retail Sales
print("=== RETAIL SALES ===")
result = conn.execute("""
    SELECT event_key, event_title, COUNT(*) as cnt
    FROM events
    WHERE country = 'US' AND importance_n = 3
      AND (LOWER(event_key) LIKE '%retail%' OR LOWER(event_title) LIKE '%retail%')
    GROUP BY event_key, event_title
    ORDER BY cnt DESC
""").fetchall()

for row in result:
    print(f"{row[0]} | {row[1]} | {row[2]} events")

# Fed
print("\n=== FED INTEREST RATE ===")
result2 = conn.execute("""
    SELECT event_key, event_title, COUNT(*) as cnt
    FROM events
    WHERE country = 'US' AND importance_n = 3
      AND (LOWER(event_key) LIKE '%fed%' OR LOWER(event_key) LIKE '%fomc%' 
           OR LOWER(event_title) LIKE '%fed%' OR LOWER(event_title) LIKE '%fomc%')
    GROUP BY event_key, event_title
    ORDER BY cnt DESC
""").fetchall()

for row in result2:
    print(f"{row[0]} | {row[1]} | {row[2]} events")

conn.close()
