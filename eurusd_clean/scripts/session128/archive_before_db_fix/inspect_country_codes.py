#!/usr/bin/env python3
"""
Investigation codes pays dans economic_events
"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("CODES PAYS DANS economic_events")
print("=" * 80)
print()

# Tous les codes uniques
result = conn.execute("""
    SELECT DISTINCT country, COUNT(*) as count
    FROM economic_events
    GROUP BY country
    ORDER BY count DESC
""").df()

print("Codes pays uniques :")
print(result.to_string())
print()

# Vérifier majuscules/minuscules
print("Détails par code (3 exemples par pays) :")
for country_code in result['country'].head(10):
    sample = conn.execute(f"""
        SELECT country, event_name
        FROM economic_events
        WHERE country = '{country_code}'
        LIMIT 3
    """).df()
    print(f"\n{country_code} (échantillon) :")
    print(sample.to_string(index=False))

conn.close()
