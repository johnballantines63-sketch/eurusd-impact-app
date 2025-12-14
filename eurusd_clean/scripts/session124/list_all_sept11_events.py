"""
Lister TOUS les Événements 11 Septembre
========================================

Afficher timestamps EXACTS tels que stockés dans la DB
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

print("\n" + "="*80)
print("TOUS LES ÉVÉNEMENTS 11 SEPTEMBRE 2025")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Lister TOUS les événements du 11 septembre (sans filtre)
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
WHERE DATE(ts_utc) = '2025-09-11'
ORDER BY ts_utc
"""

events = conn.execute(query).df()

print(f"📊 TOTAL: {len(events)} événements trouvés")
print()

if len(events) == 0:
    print("❌ AUCUN événement trouvé pour cette date !")
    
    # Vérifier quelles dates existent
    query_dates = """
    SELECT DISTINCT DATE(ts_utc) as date, COUNT(*) as num
    FROM events
    WHERE DATE(ts_utc) >= '2025-09-01'
      AND DATE(ts_utc) <= '2025-09-30'
    GROUP BY DATE(ts_utc)
    ORDER BY date
    """
    
    dates = conn.execute(query_dates).df()
    print("\nDates disponibles en septembre 2025:")
    print(dates.to_string(index=False))
    
else:
    print("="*80)
    print("LISTE COMPLÈTE")
    print("="*80)
    print()
    
    for idx, e in events.iterrows():
        imp = {3: "HIGH", 2: "MEDIUM", 1: "LOW"}.get(e['importance_n'], "?")
        
        print(f"{idx+1:2d}. {e['ts_utc']}")
        print(f"    Country: {e['country'].upper()}")
        print(f"    Importance: {imp}")
        print(f"    Event: {e['event_title']}")
        print(f"    Actual: {e['actual']}, Estimate: {e['estimate']}, Forecast: {e['forecast']}")
        print()
    
    # Focus sur événements autour de 14:30-14:35
    print("="*80)
    print("ÉVÉNEMENTS ENTRE 14:25 ET 14:45 (fenêtre Peak1)")
    print("="*80)
    print()
    
    query_window = """
    SELECT 
        ts_utc,
        country,
        event_title,
        importance_n
    FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+02:00'
      AND ts_utc <= '2025-09-11 14:45:00+02:00'
    ORDER BY ts_utc
    """
    
    events_window = conn.execute(query_window).df()
    print(f"📊 Événements dans fenêtre: {len(events_window)}")
    print()
    
    if len(events_window) > 0:
        for idx, e in events_window.iterrows():
            imp = {3: "HIGH", 2: "MEDIUM", 1: "LOW"}.get(e['importance_n'], "?")
            print(f"  {e['ts_utc']} | {e['country'].upper()} | {imp:6s} | {e['event_title'][:50]}")
    else:
        print("❌ Aucun événement dans cette fenêtre !")
        print()
        print("DIAGNOSTIC:")
        print("  - Peak1 Rev12: 14:35 +02:00")
        print("  - Fenêtre: ±10 min = 14:25 à 14:45")
        print("  - Événements réels probablement stockés différemment")
    
    # Tester différents formats de requête
    print()
    print("="*80)
    print("TEST DIFFÉRENTS FORMATS DE REQUÊTE")
    print("="*80)
    print()
    
    # Test 1: Sans timezone
    print("1. Test sans timezone explicite:")
    query_test1 = """
    SELECT COUNT(*) 
    FROM events
    WHERE ts_utc::TIMESTAMP >= '2025-09-11 14:25:00'
      AND ts_utc::TIMESTAMP <= '2025-09-11 14:45:00'
    """
    count1 = conn.execute(query_test1).fetchone()[0]
    print(f"   Résultat: {count1} événements")
    
    # Test 2: Avec +00:00 (UTC)
    print("2. Test avec +00:00 (UTC):")
    query_test2 = """
    SELECT COUNT(*) 
    FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+00:00'
      AND ts_utc <= '2025-09-11 14:45:00+00:00'
    """
    count2 = conn.execute(query_test2).fetchone()[0]
    print(f"   Résultat: {count2} événements")
    
    # Test 3: Avec +02:00 (Bern)
    print("3. Test avec +02:00 (Bern):")
    query_test3 = """
    SELECT COUNT(*) 
    FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+02:00'
      AND ts_utc <= '2025-09-11 14:45:00+02:00'
    """
    count3 = conn.execute(query_test3).fetchone()[0]
    print(f"   Résultat: {count3} événements")
    
    # Test 4: Chercher événements CPI spécifiquement
    print("4. Test événements CPI (n'importe quelle heure):")
    query_test4 = """
    SELECT COUNT(*), MIN(ts_utc), MAX(ts_utc)
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
      AND LOWER(event_title) LIKE '%cpi%'
    """
    result4 = conn.execute(query_test4).fetchone()
    print(f"   Résultat: {result4[0]} événements CPI")
    if result4[0] > 0:
        print(f"   Premier: {result4[1]}")
        print(f"   Dernier: {result4[2]}")

conn.close()

print()
print("="*80)
print("CONCLUSION")
print("="*80)
print()
print("💡 Si fenêtre 14:25-14:45 ne trouve rien:")
print("   → Événements probablement stockés en UTC (12:25-12:45)")
print("   → Ou dans un format timezone différent")
print("   → Utiliser test sans timezone explicite")
