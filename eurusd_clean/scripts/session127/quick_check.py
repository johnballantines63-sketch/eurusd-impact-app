import duckdb

conn = duckdb.connect('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb', read_only=True)

# Liste tous les event_key US contenant "unemployment" ou "gdp"
query = """
SELECT DISTINCT event_key, importance_n, COUNT(*) as cnt
FROM events 
WHERE country = 'US' 
  AND (LOWER(event_key) LIKE '%unemployment%' OR LOWER(event_key) LIKE '%gdp%')
GROUP BY event_key, importance_n
ORDER BY cnt DESC
"""

result = conn.execute(query).fetchall()

print("EVENT_KEY US contenant 'unemployment' ou 'gdp' :")
print("=" * 80)
for row in result:
    imp_map = {1: 'LOW', 2: 'MED', 3: 'HIGH'}
    print(f"{row[0]:<50} | {imp_map.get(row[1], row[1]):<4} | {row[2]:>5} events")

conn.close()
