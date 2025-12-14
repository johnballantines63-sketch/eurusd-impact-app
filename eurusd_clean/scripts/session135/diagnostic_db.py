"""
DIAGNOSTIC DB - Lister tables et vérifier événements
=====================================================
"""

import duckdb
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

import config
DB_PATH = config.DB_PATH

print("="*80)
print("DIAGNOSTIC DATABASE")
print("="*80)
print(f"DB Path: {DB_PATH}")
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Lister toutes les tables
print("📋 TABLES DISPONIBLES:")
tables = conn.execute("SHOW TABLES").df()
print(tables)
print()

# Vérifier structure table events
print("🔍 STRUCTURE TABLE 'events':")
try:
    schema = conn.execute("DESCRIBE events").df()
    print(schema)
    print()
    
    # Compter événements
    count = conn.execute("SELECT COUNT(*) as total FROM events").fetchone()[0]
    print(f"   Total événements : {count:,}")
    
    # Vérifier importance_n
    importance = conn.execute("SELECT importance_n, COUNT(*) as count FROM events GROUP BY importance_n ORDER BY importance_n").df()
    print(f"\n   Distribution importance_n:")
    print(importance)
    
    # Vérifier période
    period = conn.execute("SELECT MIN(ts_utc) as min_date, MAX(ts_utc) as max_date FROM events").df()
    print(f"\n   Période couverte:")
    print(period)
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()

# Vérifier table economic_events (Session 123)
print("🔍 STRUCTURE TABLE 'economic_events' (si existe):")
try:
    schema = conn.execute("DESCRIBE economic_events").df()
    print(schema)
    print()
    
    count = conn.execute("SELECT COUNT(*) as total FROM economic_events").fetchone()[0]
    print(f"   Total événements : {count:,}")
    
    # Vérifier si colonne importance existe
    cols = schema['column_name'].tolist()
    if 'importance_n' in cols or 'importance' in cols:
        try:
            importance = conn.execute("SELECT importance_n, COUNT(*) as count FROM economic_events GROUP BY importance_n ORDER BY importance_n").df()
            print(f"\n   Distribution importance_n:")
            print(importance)
        except:
            try:
                importance = conn.execute("SELECT importance, COUNT(*) as count FROM economic_events GROUP BY importance ORDER BY importance").df()
                print(f"\n   Distribution importance:")
                print(importance)
            except:
                print(f"   ⚠️ Pas de colonne importance")
    
    # Période
    if 'ts_utc' in cols:
        period = conn.execute("SELECT MIN(ts_utc) as min_date, MAX(ts_utc) as max_date FROM economic_events").df()
        print(f"\n   Période couverte:")
        print(period)
    elif 'datetime' in cols:
        period = conn.execute("SELECT MIN(datetime) as min_date, MAX(datetime) as max_date FROM economic_events").df()
        print(f"\n   Période couverte:")
        print(period)
    
except Exception as e:
    print(f"   ❌ Table n'existe pas ou erreur: {e}")

print()

# Test événements 11 septembre 2025
print("🔍 TEST 11 SEPTEMBRE 2025:")
try:
    test_events = conn.execute("""
    SELECT COUNT(*) as count
    FROM events
    WHERE ts_utc >= '2025-09-11' AND ts_utc < '2025-09-12'
    """).fetchone()[0]
    print(f"   events table : {test_events} événements")
except Exception as e:
    print(f"   ❌ Erreur events: {e}")

try:
    test_econ = conn.execute("""
    SELECT COUNT(*) as count
    FROM economic_events
    WHERE ts_utc >= '2025-09-11' AND ts_utc < '2025-09-12'
    """).fetchone()[0]
    print(f"   economic_events table : {test_econ} événements")
except Exception as e:
    print(f"   ⚠️ economic_events: {e}")

conn.close()

print()
print("="*80)
print("✅ DIAGNOSTIC TERMINÉ")
print("="*80)
