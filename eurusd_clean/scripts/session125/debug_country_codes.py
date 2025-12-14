#!/usr/bin/env python3
"""
DEBUG - Codes pays dans DB
"""
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("DEBUG CODES PAYS - TABLE economic_events")
print("="*80)
print()

# 1. Tous les codes pays uniques
print("1️⃣ CODES PAYS UNIQUES (top 30) :")
countries = conn.execute("""
    SELECT country, COUNT(*) as count
    FROM economic_events
    GROUP BY country
    ORDER BY count DESC
    LIMIT 30
""").df()

print(countries.to_string())
print()

# 2. Événements 11 septembre TOUS
print("="*80)
print("2️⃣ ÉVÉNEMENTS 11 SEPTEMBRE (TOUS, pas juste HIGH) :")
print("="*80)
print()

sept_11 = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance
    FROM economic_events
    WHERE datetime_utc >= '2025-09-11 12:00:00'
      AND datetime_utc <= '2025-09-11 15:00:00'
    ORDER BY datetime_utc
""").df()

print(f"Total événements 12h-15h UTC : {len(sept_11)}")
print()

if len(sept_11) > 0:
    print("📋 Événements par importance :")
    for imp in ['HIGH', 'MEDIUM', 'LOW']:
        events_imp = sept_11[sept_11['importance'] == imp]
        print(f"\n{imp} : {len(events_imp)} événements")
        
        if len(events_imp) > 0 and imp == 'HIGH':
            print("\nDétail HIGH :")
            for _, e in events_imp.iterrows():
                print(f"   {e['datetime_utc']} - {e['event_name'][:40]:40s} - country={e['country']}")

# 3. Vérifier si CPI existe avec autre code pays
print()
print("="*80)
print("3️⃣ RECHERCHE CPI 11 SEPTEMBRE (tous codes pays) :")
print("="*80)
print()

cpi_search = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance
    FROM economic_events
    WHERE datetime_utc >= '2025-09-11 00:00:00'
      AND datetime_utc <= '2025-09-11 23:59:59'
      AND (event_name LIKE '%cpi%' OR event_name LIKE '%inflation%')
    ORDER BY datetime_utc
""").df()

print(f"CPI/Inflation events trouvés : {len(cpi_search)}")
print()

if len(cpi_search) > 0:
    for _, e in cpi_search.iterrows():
        print(f"   {e['datetime_utc']} - {e['event_name'][:40]:40s} - country={e['country']} - {e['importance']}")

conn.close()

print()
print("="*80)
print("DEBUG TERMINÉ")
print("="*80)
