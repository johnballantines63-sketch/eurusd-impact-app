"""
Comparaison DB AVANT/APRÈS EODHD - 11 Septembre 2025
=====================================================

Compare les événements du 11 septembre 2025 entre :
- DB AVANT Session 123 (backup)
- DB APRÈS Session 123 (actuelle avec EODHD)

OBJECTIF : Identifier ce qui a changé et pourquoi prédictions ne marchent plus
"""

import duckdb
from pathlib import Path
import pandas as pd

# Chemins
DB_ACTUELLE = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
DB_BACKUP = Path(__file__).parent.parent / 'session123' / 'backups' / 'warehouse_backup_20251109_201627.duckdb'

print("\n" + "="*80)
print("COMPARAISON DB AVANT/APRÈS EODHD")
print("11 SEPTEMBRE 2025")
print("="*80)
print()

print(f"📂 DB BACKUP (avant): {DB_BACKUP.name}")
print(f"📂 DB ACTUELLE (après): {DB_ACTUELLE.name}")
print()

# ============================================================================
# 1. STRUCTURE TABLES
# ============================================================================

print("="*80)
print("1. STRUCTURE TABLES")
print("="*80)
print()

# BACKUP
conn_backup = duckdb.connect(str(DB_BACKUP), read_only=True)

print("📊 DB BACKUP:")
try:
    cols_backup = conn_backup.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'economic_events'
        ORDER BY ordinal_position
    """).df()
    
    for _, row in cols_backup.iterrows():
        print(f"   {row['column_name']:20s} : {row['data_type']}")
    
    count_backup = conn_backup.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"\n   Total événements: {count_backup:,}")
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()

# ACTUELLE
conn_actuelle = duckdb.connect(str(DB_ACTUELLE), read_only=True)

print("📊 DB ACTUELLE:")
try:
    cols_actuelle = conn_actuelle.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'economic_events'
        ORDER BY ordinal_position
    """).df()
    
    for _, row in cols_actuelle.iterrows():
        print(f"   {row['column_name']:20s} : {row['data_type']}")
    
    count_actuelle = conn_actuelle.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"\n   Total événements: {count_actuelle:,}")
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()

# ============================================================================
# 2. ÉVÉNEMENTS 11 SEPTEMBRE 2025
# ============================================================================

print("="*80)
print("2. ÉVÉNEMENTS 11 SEPTEMBRE 2025 (14:25-16:00 Bern = 12:25-14:00 UTC)")
print("="*80)
print()

# Fenêtre temporelle (UTC)
start_utc = '2025-09-11 12:00:00'
end_utc = '2025-09-11 14:30:00'

# BACKUP
print("📊 DB BACKUP:")
try:
    # Déterminer colonne datetime
    if 'ts_utc' in [c['column_name'] for _, c in cols_backup.iterrows()]:
        datetime_col = 'ts_utc'
    else:
        datetime_col = 'datetime_utc'
    
    query_backup = f"""
    SELECT *
    FROM economic_events
    WHERE {datetime_col} BETWEEN ? AND ?
    ORDER BY {datetime_col}
    """
    
    events_backup = conn_backup.execute(query_backup, [start_utc, end_utc]).df()
    
    print(f"   Nombre événements: {len(events_backup)}")
    
    if len(events_backup) > 0:
        print(f"\n   Colonnes disponibles: {events_backup.columns.tolist()}")
        print(f"\n   Échantillon (5 premiers):")
        print(events_backup.head(5).to_string())
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    events_backup = pd.DataFrame()

print()
print()

# ACTUELLE
print("📊 DB ACTUELLE:")
try:
    query_actuelle = """
    SELECT *
    FROM economic_events
    WHERE datetime_utc BETWEEN ? AND ?
    ORDER BY datetime_utc
    """
    
    events_actuelle = conn_actuelle.execute(query_actuelle, [start_utc, end_utc]).df()
    
    print(f"   Nombre événements: {len(events_actuelle)}")
    
    if len(events_actuelle) > 0:
        print(f"\n   Colonnes disponibles: {events_actuelle.columns.tolist()}")
        print(f"\n   Échantillon (5 premiers):")
        print(events_actuelle.head(5).to_string())
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    events_actuelle = pd.DataFrame()

print()

# ============================================================================
# 3. COMPARAISON DÉTAILLÉE
# ============================================================================

print("="*80)
print("3. COMPARAISON ÉVÉNEMENTS")
print("="*80)
print()

print(f"Nombre événements BACKUP: {len(events_backup)}")
print(f"Nombre événements ACTUELLE: {len(events_actuelle)}")
print(f"Différence: {len(events_actuelle) - len(events_backup)}")
print()

if len(events_backup) > 0 and len(events_actuelle) > 0:
    # Tenter de comparer événements similaires
    print("📊 ÉVÉNEMENTS HAUTE IMPORTANCE:")
    print()
    
    # BACKUP
    if 'importance_n' in events_backup.columns:
        high_backup = events_backup[events_backup['importance_n'] == 3]
    elif 'importance' in events_backup.columns:
        high_backup = events_backup[events_backup['importance'] == 'HIGH']
    else:
        high_backup = pd.DataFrame()
    
    print(f"   BACKUP: {len(high_backup)} événements HIGH")
    if len(high_backup) > 0:
        for _, event in high_backup.iterrows():
            time_col = 'ts_utc' if 'ts_utc' in event.index else 'datetime_utc'
            name_col = 'event_title' if 'event_title' in event.index else 'event_name'
            print(f"      {event[time_col]} - {event[name_col]}")
    print()
    
    # ACTUELLE
    high_actuelle = events_actuelle[events_actuelle['importance'] == 'HIGH']
    
    print(f"   ACTUELLE: {len(high_actuelle)} événements HIGH")
    if len(high_actuelle) > 0:
        for _, event in high_actuelle.iterrows():
            print(f"      {event['datetime_utc']} - {event['event_name']}")
    print()
    
    # ============================================================================
    # 4. COMPARAISON VALEURS (Actual/Forecast/Previous)
    # ============================================================================
    
    print("="*80)
    print("4. COMPARAISON VALEURS")
    print("="*80)
    print()
    
    print("📊 BACKUP - Valeurs disponibles:")
    if len(high_backup) > 0:
        for _, event in high_backup.iterrows():
            name_col = 'event_title' if 'event_title' in event.index else 'event_name'
            print(f"\n   {event[name_col]}:")
            
            if 'actual' in event.index:
                print(f"      Actual: {event['actual']}")
            if 'estimate' in event.index:
                print(f"      Estimate: {event['estimate']}")
            if 'forecast' in event.index:
                print(f"      Forecast: {event['forecast']}")
            if 'previous' in event.index:
                print(f"      Previous: {event['previous']}")
    
    print()
    print()
    
    print("📊 ACTUELLE - Valeurs disponibles:")
    if len(high_actuelle) > 0:
        for _, event in high_actuelle.iterrows():
            print(f"\n   {event['event_name']}:")
            print(f"      Actual: {event['actual']}")
            print(f"      Forecast: {event['forecast']}")
            print(f"      Previous: {event['previous']}")

print()
print("="*80)
print("CONCLUSION")
print("="*80)
print()

if len(events_backup) > len(events_actuelle):
    print("⚠️  MOINS d'événements dans EODHD")
    print(f"   {len(events_backup) - len(events_actuelle)} événements perdus")
elif len(events_actuelle) > len(events_backup):
    print("✅ PLUS d'événements dans EODHD")
    print(f"   {len(events_actuelle) - len(events_backup)} événements ajoutés")
else:
    print("➡️  MÊME nombre d'événements")

print()
print("💡 Vérifier si:")
print("   1. Événements CPI présents dans les deux ?")
print("   2. Valeurs actual/forecast/previous identiques ?")
print("   3. Timestamps identiques ?")
print("   4. Importance identique ?")

conn_backup.close()
conn_actuelle.close()
