"""
Diagnostic : Pourquoi label = None ?
"""
import sys
from pathlib import Path
import duckdb

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "fx_impact_app"))
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

from config import get_db_path

db_path = get_db_path()
conn = duckdb.connect(str(db_path))

print("="*80)
print("DIAGNOSTIC LABEL = NONE")
print("="*80)

# 1. Vérifier colonnes table events
print("\n1. Colonnes table events :")
schema = conn.execute("DESCRIBE events").fetchall()
for col in schema:
    print(f"   - {col[0]}: {col[1]}")

# 2. Échantillon événements 11 sept AVEC label
print("\n2. Événements 11 sept (avec label) :")
query1 = """
SELECT 
    event_key,
    event_title,
    label,
    actual,
    estimate
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND country = 'US'
    AND actual IS NOT NULL
ORDER BY ts_utc
LIMIT 10
"""

result1 = conn.execute(query1).fetchall()
for row in result1:
    print(f"   Key: {row[0][:30]:30s} | Label: {str(row[2]):20s} | Title: {row[1][:30]}")

# 3. Vérifier jointure avec event_families
print("\n3. Jointure events + event_families :")
query2 = """
SELECT 
    e.event_key,
    e.label as event_label,
    ef.family as ef_family,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND e.actual IS NOT NULL
LIMIT 10
"""

result2 = conn.execute(query2).fetchall()
for row in result2:
    print(f"   Key: {row[0][:30]:30s} | Event.label: {str(row[1]):20s} | EF.family: {str(row[2]):20s} | Score: {row[3]}")

# 4. Compter événements avec/sans label
print("\n4. Statistiques label :")
query3 = """
SELECT 
    COUNT(*) as total,
    COUNT(label) as with_label,
    COUNT(*) - COUNT(label) as without_label
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND country = 'US'
    AND actual IS NOT NULL
"""

result3 = conn.execute(query3).fetchone()
print(f"   Total événements    : {result3[0]}")
print(f"   Avec label          : {result3[1]}")
print(f"   Sans label (NULL)   : {result3[2]}")

conn.close()

print("\n" + "="*80)
