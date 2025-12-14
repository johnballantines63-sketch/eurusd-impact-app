ñclcñ--´j"gv,.""
Véhrifier quelle table contient les événements du 20.11.2025
==========================================================================
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'

print("=" * 80)
print("🔍 VÉRIFICATION DES TABLES D'ÉVÉNEMENTS - 20.11.2025")
print("=" * 80)
print()

target_date = datetime(2025, 11, 20)
conn = duckdb.connect(str(DB_PATH), read_only=True)

# Lister toutes les tables
print("1️⃣ TABLES DISPONIBLES DANS LA DB")
print("-" * 80)

tables_query = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'main'
ORDER BY table_name
"""

try:
    tables = conn.execute(tables_query).df()
    event_tables = tables[tables['table_name'].str.contains('event', case=False)]
    
    print(f"   Tables contenant 'event' :")
    for idx, row in event_tables.iterrows():
        print(f"      - {row['table_name']}")
except:
    print("   ⚠️ Impossible de lister les tables via information_schema")
    print("   → Testons directement les tables connues")

print()

# Tester la table 'events'
print("2️⃣ TABLE 'events'")
print("-" * 80)

try:
    query_events = """
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN country = 'US' THEN 1 END) as us_events,
        MIN(ts_utc) as min_date,
        MAX(ts_utc) as max_date
    FROM events
    WHERE DATE(ts_utc) = ?
    """
    
    result = conn.execute(query_events, [target_date.strftime('%Y-%m-%d')]).fetchone()
    
    if result:
        total, us_events, min_date, max_date = result
        print(f"   ✅ Table 'events' existe")
        print(f"      Total événements pour {target_date.strftime('%Y-%m-%d')}: {total}")
        print(f"      Événements US: {us_events}")
        print(f"      Plage: {min_date} → {max_date}")
        
        # Vérifier les événements US à 13:30 UTC
        query_us_1330 = """
        SELECT 
            ts_utc,
            event_key,
            country,
            actual
        FROM events
        WHERE DATE(ts_utc) = ?
          AND country = 'US'
          AND EXTRACT(HOUR FROM ts_utc) = 13
          AND EXTRACT(MINUTE FROM ts_utc) = 30
        ORDER BY ts_utc
        LIMIT 10
        """
        
        df_1330 = conn.execute(query_us_1330, [target_date.strftime('%Y-%m-%d')]).df()
        
        if not df_1330.empty:
            print(f"      ✅ {len(df_1330)} événements US à 13:30 UTC trouvés")
            print("      Premiers événements :")
            for idx, row in df_1330.head(5).iterrows():
                print(f"         {row['ts_utc']} | {row['event_key']} | actual: {row['actual']}")
        else:
            print(f"      ❌ Aucun événement US à 13:30 UTC")
    else:
        print(f"   ❌ Table 'events' vide ou pas de données pour cette date")
except Exception as e:
    print(f"   ❌ Erreur avec table 'events': {e}")

print()

# Tester la table 'economic_events'
print("3️⃣ TABLE 'economic_events'")
print("-" * 80)

try:
    query_economic = """
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN country = 'US' THEN 1 END) as us_events,
        MIN(datetime_utc) as min_date,
        MAX(datetime_utc) as max_date
    FROM economic_events
    WHERE DATE(datetime_utc) = ?
    """
    
    result = conn.execute(query_economic, [target_date.strftime('%Y-%m-%d')]).fetchone()
    
    if result:
        total, us_events, min_date, max_date = result
        print(f"   ✅ Table 'economic_events' existe")
        print(f"      Total événements pour {target_date.strftime('%Y-%m-%d')}: {total}")
        print(f"      Événements US: {us_events}")
        print(f"      Plage: {min_date} → {max_date}")
        
        # Vérifier les événements US à 13:30 UTC
        query_us_1330 = """
        SELECT 
            datetime_utc as ts_utc,
            event_name as event_key,
            country,
            actual
        FROM economic_events
        WHERE DATE(datetime_utc) = ?
          AND country = 'US'
          AND EXTRACT(HOUR FROM datetime_utc) = 13
          AND EXTRACT(MINUTE FROM datetime_utc) = 30
        ORDER BY datetime_utc
        LIMIT 10
        """
        
        df_1330 = conn.execute(query_us_1330, [target_date.strftime('%Y-%m-%d')]).df()
        
        if not df_1330.empty:
            print(f"      ✅ {len(df_1330)} événements US à 13:30 UTC trouvés")
            print("      Premiers événements :")
            for idx, row in df_1330.head(5).iterrows():
                print(f"         {row['ts_utc']} | {row['event_key']} | actual: {row['actual']}")
        else:
            print(f"      ❌ Aucun événement US à 13:30 UTC")
    else:
        print(f"   ❌ Table 'economic_events' vide ou pas de données pour cette date")
except Exception as e:
    print(f"   ❌ Erreur avec table 'economic_events': {e}")

print()

# Comparer les deux tables
print("4️⃣ COMPARAISON DES DEUX TABLES")
print("-" * 80)

try:
    # Compter événements US à 13:30 UTC dans 'events'
    count_events = conn.execute("""
        SELECT COUNT(*) 
        FROM events
        WHERE DATE(ts_utc) = ?
          AND country = 'US'
          AND EXTRACT(HOUR FROM ts_utc) = 13
          AND EXTRACT(MINUTE FROM ts_utc) = 30
    """, [target_date.strftime('%Y-%m-%d')]).fetchone()[0]
    
    # Compter événements US à 13:30 UTC dans 'economic_events'
    count_economic = conn.execute("""
        SELECT COUNT(*) 
        FROM economic_events
        WHERE DATE(datetime_utc) = ?
          AND country = 'US'
          AND EXTRACT(HOUR FROM datetime_utc) = 13
          AND EXTRACT(MINUTE FROM datetime_utc) = 30
    """, [target_date.strftime('%Y-%m-%d')]).fetchone()[0]
    
    print(f"   Événements US à 13:30 UTC (14:30 heure de Berne) :")
    print(f"      Table 'events': {count_events}")
    print(f"      Table 'economic_events': {count_economic}")
    
    if count_economic > count_events:
        print(f"   ⚠️ La table 'economic_events' contient plus d'événements !")
        print(f"   → Il faut peut-être utiliser 'economic_events' au lieu de 'events'")
    elif count_events > count_economic:
        print(f"   ✅ La table 'events' contient plus d'événements")
    else:
        print(f"   ℹ️ Les deux tables ont le même nombre d'événements")
        
except Exception as e:
    print(f"   ⚠️ Erreur lors de la comparaison: {e}")

conn.close()

print()
print("=" * 80)
print("✅ VÉRIFICATION TERMINÉE")
print("=" * 80)


