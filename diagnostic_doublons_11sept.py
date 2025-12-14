"""
DIAGNOSTIC : Détecter les doublons dans les événements 11 septembre
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))
from config import get_db_path

print("=" * 80)
print("🔍 DIAGNOSTIC DOUBLONS - Événements 11 septembre")
print("=" * 80)

db_path = get_db_path()
conn = duckdb.connect(str(db_path))

# Query complète avec tous les détails
query = """
SELECT 
    e.ts_utc,
    e.event_key,
    e.event_title,
    e.label,
    ef.family,
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

# Afficher tous avec détails
print("\nLISTE COMPLÈTE AVEC event_title :")
print("-" * 100)
df['ts_utc'] = pd.to_datetime(df['ts_utc'])
df['heure'] = df['ts_utc'].dt.strftime('%H:%M:%S')

for idx, row in df.iterrows():
    surprise = row['surprise'] if pd.notna(row['surprise']) else 'NaN'
    title = (row['event_title'][:50] if row['event_title'] else 'N/A').ljust(50)
    print(f"{idx+1:2d}. {row['heure']} | {title} | "
          f"Family: {row['family']:20s} | Score: {row['empirical_score']:5.1f}")

# Détecter doublons par event_key
print("\n" + "=" * 80)
print("🔍 DÉTECTION DOUBLONS PAR event_key")
print("=" * 80)

duplicates = df[df.duplicated(subset=['event_key'], keep=False)]

if not duplicates.empty:
    print(f"\n⚠️  {len(duplicates)} événements avec event_key dupliqués :")
    print("-" * 100)
    
    for event_key in duplicates['event_key'].unique():
        dups = df[df['event_key'] == event_key]
        print(f"\n📌 event_key: {event_key}")
        for idx, row in dups.iterrows():
            title = (row['event_title'][:50] if row['event_title'] else 'N/A').ljust(50)
            print(f"   {row['heure']} | {title} | Score: {row['empirical_score']:5.1f}")
else:
    print("\n✅ Pas de doublons d'event_key")

# Détecter doublons par event_title
print("\n" + "=" * 80)
print("🔍 DÉTECTION DOUBLONS PAR event_title")
print("=" * 80)

duplicates_title = df[df.duplicated(subset=['event_title'], keep=False)]

if not duplicates_title.empty:
    print(f"\n⚠️  {len(duplicates_title)} événements avec event_title dupliqués :")
    print("-" * 100)
    
    for title in duplicates_title['event_title'].unique():
        dups = df[df['event_title'] == title]
        print(f"\n📌 event_title: {title}")
        for idx, row in dups.iterrows():
            print(f"   {row['heure']} | event_key: {row['event_key'][:30]:30s} | Score: {row['empirical_score']:5.1f}")
else:
    print("\n✅ Pas de doublons d'event_title")

# Compter événements à 12:30
print("\n" + "=" * 80)
print("🎯 ÉVÉNEMENTS À 12:30:00 UTC")
print("=" * 80)

events_1230 = df[df['heure'] == '12:30:00']
print(f"\n✅ {len(events_1230)} événements à 12:30:00 UTC")

if not events_1230.empty:
    print("\nDÉTAIL :")
    print("-" * 100)
    for idx, row in events_1230.iterrows():
        surprise = row['surprise'] if pd.notna(row['surprise']) else 'NaN'
        title = (row['event_title'][:50] if row['event_title'] else 'N/A').ljust(50)
        print(f"   {title} | Family: {row['family']:20s} | "
              f"Score: {row['empirical_score']:5.1f} | Surprise: {surprise}")

print("\n" + "=" * 80)
print("💡 RECOMMANDATION")
print("=" * 80)

if len(duplicates) > 0:
    print("\n⚠️  Il y a des doublons d'event_key !")
    print("   → Besoin de dédupliquer avec DISTINCT ou GROUP BY")
elif len(events_1230) < len(df):
    print(f"\n⚠️  Il y a {len(df)} événements mais seulement {len(events_1230)} à 12:30:00 UTC")
    print("   → Filtrer sur ts_utc = '2025-09-11 12:30:00' UTC")
else:
    print("\n✅ Pas de doublons détectés")

print("=" * 80)
