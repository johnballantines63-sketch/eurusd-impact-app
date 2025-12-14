"""
Chercher Événements 11 Septembre - Fenêtre Large
================================================

L'ancienne DB n'a pas d'événements 12:00-14:30 UTC.
Cherchons dans une fenêtre BEAUCOUP plus large pour voir s'ils existent ailleurs.
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_BACKUP = Path(__file__).parent.parent / 'session123' / 'backups' / 'warehouse_backup_20251109_201627.duckdb'

print("\n" + "="*80)
print("RECHERCHE ÉVÉNEMENTS 11 SEPTEMBRE 2025 - FENÊTRE LARGE")
print("="*80)
print()

conn = duckdb.connect(str(DB_BACKUP), read_only=True)

# Fenêtre TOUTE LA JOURNÉE
start_date = '2025-09-11 00:00:00'
end_date = '2025-09-11 23:59:59'

query = """
SELECT 
    ts_utc,
    country,
    event_key,
    event_title,
    importance_n,
    actual,
    estimate,
    forecast,
    previous
FROM events
WHERE ts_utc::DATE = '2025-09-11'
ORDER BY ts_utc, importance_n DESC
"""

events = conn.execute(query).df()

print(f"📊 TOTAL événements 11 septembre 2025: {len(events)}")
print()

if len(events) == 0:
    print("❌ AUCUN événement trouvé pour le 11 septembre 2025")
    print()
    print("Vérifions la plage de dates disponible dans la table events...")
    print()
    
    query_range = """
    SELECT 
        MIN(ts_utc) as min_date,
        MAX(ts_utc) as max_date,
        COUNT(*) as total
    FROM events
    """
    
    result = conn.execute(query_range).fetchone()
    
    print(f"Plage dates table 'events':")
    print(f"  Min: {result[0]}")
    print(f"  Max: {result[1]}")
    print(f"  Total: {result[2]:,} événements")
    print()
    
    # Vérifier si 2025 existe
    query_2025 = """
    SELECT COUNT(*)
    FROM events
    WHERE ts_utc >= '2025-01-01' AND ts_utc < '2026-01-01'
    """
    
    count_2025 = conn.execute(query_2025).fetchone()[0]
    
    print(f"Événements 2025: {count_2025:,}")
    print()
    
    if count_2025 == 0:
        print("⚠️  AUCUN événement 2025 dans l'ancienne DB !")
        print()
        print("Cela signifie que les formules S115 n'ont JAMAIS été validées")
        print("avec des données réelles du 11 septembre 2025.")
        print()
        print("💡 HYPOTHÈSE:")
        print("  Les formules ont été développées avec des données 2023-2024,")
        print("  puis on a SUPPOSÉ qu'elles marcheraient pour 2025.")
        print()
    
else:
    print("✅ Événements trouvés")
    print()
    
    # Grouper par heure
    events['hour'] = pd.to_datetime(events['ts_utc']).dt.hour
    
    print("Distribution par heure (UTC):")
    for hour in sorted(events['hour'].unique()):
        count = len(events[events['hour'] == hour])
        high_count = len(events[(events['hour'] == hour) & (events['importance_n'] == 3)])
        print(f"  {hour:02d}h: {count:2d} événements ({high_count} HIGH)")
    print()
    
    # Montrer tous les HIGH
    high_events = events[events['importance_n'] == 3]
    
    if len(high_events) > 0:
        print(f"📊 Événements HIGH: {len(high_events)}")
        print()
        for idx, event in high_events.iterrows():
            print(f"{idx+1}. {event['ts_utc']} | {event['country'].upper()}")
            print(f"   {event['event_title']}")
            print(f"   Actual: {event['actual']}")
            print(f"   Estimate: {event['estimate']}")
            print(f"   Forecast: {event['forecast']}")
            print(f"   Previous: {event['previous']}")
            print()

conn.close()
