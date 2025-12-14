#!/usr/bin/env python3
"""
INSPECTION FAMILIES - Voir les vrais noms
"""
import sys
from pathlib import Path
import duckdb
import importlib.util

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

spec_config = importlib.util.spec_from_file_location("config", project_root / "app" / "config.py")
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)

config = config_module.Config()
db_path = Path(config.get_db_path())

conn = duckdb.connect(str(db_path), read_only=True)

# Voir toutes les families HIGH IMPACT
query = """
SELECT DISTINCT family, COUNT(*) as count, MAX(empirical_score) as max_score
FROM event_families
WHERE empirical_score > 40
    AND country = 'US'
GROUP BY family
ORDER BY max_score DESC, count DESC
"""

result = conn.execute(query).fetchall()

print("=" * 80)
print("FAMILIES HIGH IMPACT (score > 40) US")
print("=" * 80)
print()

for family, count, score in result:
    print(f"{score:6.1f} | {count:4d} events | {family}")

conn.close()
