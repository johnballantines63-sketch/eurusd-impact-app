"""
Diagnostic des événements 11 septembre - Heures exactes
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "fx_impact_app"))
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

from config import get_db_path

db_path = get_db_path()
conn = duckdb.connect(str(db_path))

print("="*80)
print("DIAGNOSTIC ÉVÉNEMENTS 11 SEPTEMBRE - HEURES EXACTES")
print("="*80)

# Charger tous les événements US du 11 sept avec actual
query = """
SELECT 
    e.ts_utc,
    e.event_key,
    e.event_title,
    COALESCE(e.label, ef.family) as family,
    e.actual,
    e.estimate,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND e.actual IS NOT NULL
    AND ef.empirical_score IS NOT NULL
ORDER BY e.ts_utc
"""

df = conn.execute(query).df()
conn.close()

print(f"\n✅ {len(df)} événements trouvés\n")
print("LISTE COMPLÈTE DES ÉVÉNEMENTS :")
print("-" * 80)

for idx, row in df.iterrows():
    ts = pd.to_datetime(row['ts_utc'])
    print(f"{idx+1:2d}. {ts.strftime('%H:%M:%S')} | {str(row['family']):25s} | "
          f"Score: {row['empirical_score']:5.1f} | Actual: {row['actual']:8.2f}")

print("\n" + "="*80)
print("GROUPEMENT PAR HEURE :")
print("="*80)

# Grouper par heure
df['ts_utc'] = pd.to_datetime(df['ts_utc'])
df['hour_minute'] = df['ts_utc'].dt.strftime('%H:%M')

grouped = df.groupby('hour_minute').size()
print("\nNombre d'événements par heure-minute :")
for hour, count in grouped.items():
    print(f"   {hour} : {count} événements")

print("\n" + "="*80)
