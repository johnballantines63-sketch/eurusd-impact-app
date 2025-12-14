import duckdb
from pathlib import Path

DB_PATH = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
conn = duckdb.connect(DB_PATH, read_only=True)

# Retail Sales
print("RETAIL SALES:")
result = conn.execute("""
    SELECT event_key, event_title, COUNT(*) as cnt
    FROM events
    WHERE country = 'US' AND importance_n = 3
    AND (LOWER(event_key) LIKE '%retail%' OR LOWER(event_title) LIKE '%retail%')
    GROUP BY event_key, event_title
    ORDER BY cnt DESC
""").fetchall()
for row in result:
    print(f"  {row[2]:3d}× {row[0]} - {row[1]}")

print("\nFED RATE:")
result = conn.execute("""
    SELECT event_key, event_title, COUNT(*) as cnt
    FROM events
    WHERE country = 'US' AND importance_n = 3
    AND ((LOWER(event_key) LIKE '%fed%' AND LOWER(event_key) LIKE '%rate%')
         OR (LOWER(event_title) LIKE '%fed%' AND LOWER(event_title) LIKE '%rate%')
         OR LOWER(event_key) LIKE '%fomc%')
    GROUP BY event_key, event_title
    ORDER BY cnt DESC
""").fetchall()
for row in result:
    print(f"  {row[2]:3d}× {row[0]} - {row[1]}")

conn.close()
