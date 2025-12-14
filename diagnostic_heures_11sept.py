"""
DIAGNOSTIC : Afficher heures et détecter les événements simultanés 12:30
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))
from config import get_db_path

print("=" * 80)
print("🔍 DIAGNOSTIC HEURES - Événements 11 septembre")
print("=" * 80)

db_path = get_db_path()
conn = duckdb.connect(str(db_path))

query = """
SELECT 
    e.ts_utc,
    COALESCE(e.label, ef.family) as family,
    e.event_title,
    e.actual,
    e.forecast,
    e.actual - e.forecast as surprise,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND e.actual IS NOT NULL
    AND ef.empirical_score IS NOT NULL
ORDER BY e.ts_utc, e.event_key
"""

df = conn.execute(query).df()
conn.close()

print(f"\n✅ {len(df)} événements totaux")

# Afficher avec heures
print("\nLISTE PAR HEURE :")
print("-" * 80)
df['ts_utc'] = pd.to_datetime(df['ts_utc'])
df['heure'] = df['ts_utc'].dt.strftime('%H:%M:%S')

for heure in df['heure'].unique():
    events_heure = df[df['heure'] == heure]
    print(f"\n🕐 {heure} UTC ({len(events_heure)} événements) :")
    for idx, row in events_heure.iterrows():
        surprise = row['surprise'] if pd.notna(row['surprise']) else 'NaN'
        print(f"   - {row['family']:25s} | Score: {row['empirical_score']:5.1f} | Surprise: {surprise}")

# Focus sur 12:30
print("\n" + "=" * 80)
print("🎯 ÉVÉNEMENTS À 12:30:00 UTC (heure principale CPI)")
print("=" * 80)

events_1230 = df[df['heure'] == '12:30:00']
print(f"\n✅ {len(events_1230)} événements à 12:30:00 UTC")

if not events_1230.empty:
    print("\nDÉTAIL :")
    print("-" * 80)
    for idx, row in events_1230.iterrows():
        surprise = row['surprise'] if pd.notna(row['surprise']) else 'NaN'
        surprise_pct = (row['surprise'] / row['forecast'] * 100) if pd.notna(row['surprise']) and row['forecast'] != 0 else 'NaN'
        print(f"   {row['family']:25s} | Score: {row['empirical_score']:5.1f} | "
              f"Surprise: {surprise:>8} | Surp%: {surprise_pct}")

print("\n" + "=" * 80)
print(f"💡 CONCLUSION : Filtrer sur 12:30:00 UTC pour avoir les vrais événements CPI")
print("=" * 80)
