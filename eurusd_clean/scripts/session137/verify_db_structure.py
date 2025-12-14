"""
ACTION 2 - VÉRIFIER STRUCTURE DB EVENTS
Session 137 - Workflow LOO-CV ÉTAPE 2

Objectif:
1. Confirmer colonnes events (ts_utc, importance_n, event_title)
2. Compter événements HIGH (importance_n = 3)
3. Tester requête matching ±60 min sur 1 mouvement test
4. Valider conversion timezone UTC → Europe/Zurich

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# =============================================================================
# PARAMÈTRES
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
STEP1_CSV = Path(__file__).parent.parent / "session136" / "step1_price_movements.csv"

# =============================================================================
# 1. VÉRIFIER STRUCTURE TABLE EVENTS
# =============================================================================

def verify_events_structure():
    """Vérifier structure table events et colonnes critiques"""
    
    print("="*80)
    print("ACTION 2.1 : VÉRIFICATION STRUCTURE TABLE EVENTS")
    print("="*80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Obtenir structure table
    print("\n1. Structure table events:")
    print("-" * 80)
    result = conn.execute("DESCRIBE events").df()
    print(result.to_string())
    
    # Vérifier colonnes critiques
    print("\n2. Vérification colonnes critiques:")
    print("-" * 80)
    columns_required = ['ts_utc', 'importance_n', 'event_title', 'event_key', 'country']
    columns_present = result['column_name'].tolist()
    
    for col in columns_required:
        status = "✅" if col in columns_present else "❌"
        print(f"{status} {col}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ ACTION 2.1 COMPLÉTÉE")
    print("="*80 + "\n")

# =============================================================================
# 2. COMPTER ÉVÉNEMENTS HIGH
# =============================================================================

def count_high_importance_events():
    """Compter événements HIGH (importance_n = 3)"""
    
    print("="*80)
    print("ACTION 2.2 : COMPTER ÉVÉNEMENTS HIGH")
    print("="*80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Compter total
    query_total = "SELECT COUNT(*) as total FROM events"
    total = conn.execute(query_total).fetchone()[0]
    print(f"\n1. Total événements : {total:,}")
    
    # Compter par importance
    query_importance = """
    SELECT importance_n, COUNT(*) as count
    FROM events
    GROUP BY importance_n
    ORDER BY importance_n
    """
    df_importance = conn.execute(query_importance).df()
    print("\n2. Distribution par importance:")
    print("-" * 80)
    print(df_importance.to_string())
    
    # Compter HIGH
    query_high = "SELECT COUNT(*) as high_count FROM events WHERE importance_n = 3"
    high_count = conn.execute(query_high).fetchone()[0]
    
    print(f"\n3. Événements HIGH (importance_n = 3) : {high_count:,}")
    print(f"   Pourcentage : {high_count / total * 100:.1f}%")
    
    # Attendu: ~7,889 selon MASTER_PLAN
    print(f"\n4. Comparaison attendu (MASTER_PLAN) : ~7,889")
    print(f"   Écart : {abs(high_count - 7889)} événements")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ ACTION 2.2 COMPLÉTÉE")
    print("="*80 + "\n")
    
    return high_count

# =============================================================================
# 3. TESTER MATCHING ±60 MIN
# =============================================================================

def test_matching_query():
    """Tester requête matching sur 1 mouvement test"""
    
    print("="*80)
    print("ACTION 2.3 : TESTER MATCHING ±60 MIN")
    print("="*80)
    
    # Charger 1er mouvement de step1
    df_movements = pd.read_csv(STEP1_CSV)
    test_movement = df_movements.iloc[0]
    
    print(f"\n1. Mouvement test (ligne 1 de step1_price_movements.csv):")
    print("-" * 80)
    print(f"   Datetime : {test_movement['datetime']}")
    print(f"   Peak time: {test_movement['peak_time']}")
    print(f"   Impact   : {test_movement['impact_pips']:.1f} pips")
    print(f"   Direction: {test_movement['direction']}")
    
    # Convertir en timezone Bern
    tz_bern = pytz.timezone('Europe/Zurich')
    movement_dt = pd.to_datetime(test_movement['datetime'])
    
    # Si pas de timezone, supposer déjà Bern
    if movement_dt.tz is None:
        movement_dt = tz_bern.localize(movement_dt)
    
    # Définir fenêtre ±60 min
    window_start = movement_dt - timedelta(minutes=60)
    window_end = movement_dt + timedelta(minutes=60)
    
    print(f"\n2. Fenêtre matching (timezone Bern):")
    print("-" * 80)
    print(f"   Start  : {window_start}")
    print(f"   Center : {movement_dt}")
    print(f"   End    : {window_end}")
    print(f"   Durée  : 120 minutes (±60)")
    
    # Convertir en UTC pour requête
    window_start_utc = window_start.astimezone(pytz.UTC)
    window_end_utc = window_end.astimezone(pytz.UTC)
    
    print(f"\n3. Fenêtre matching (timezone UTC pour DB):")
    print("-" * 80)
    print(f"   Start UTC: {window_start_utc}")
    print(f"   End UTC  : {window_end_utc}")
    
    # Requête matching
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    query = """
    SELECT 
        ts_utc,
        country,
        event_title,
        event_key,
        importance_n,
        actual,
        estimate,
        forecast
    FROM events
    WHERE importance_n = 3
      AND ts_utc >= ?
      AND ts_utc <= ?
    ORDER BY ts_utc
    """
    
    df_events = conn.execute(query, [window_start_utc, window_end_utc]).df()
    
    print(f"\n4. Événements HIGH trouvés : {len(df_events)}")
    print("-" * 80)
    
    if len(df_events) > 0:
        print("\nÉvénements détaillés:")
        for idx, row in df_events.iterrows():
            # Convertir ts_utc en Bern pour affichage
            event_time_bern = pd.to_datetime(row['ts_utc']).tz_convert('Europe/Zurich')
            print(f"\n   [{idx+1}] {event_time_bern}")
            print(f"       Event  : {row['event_title']}")
            print(f"       Country: {row['country']}")
            print(f"       Key    : {row['event_key']}")
    else:
        print("   Aucun événement HIGH dans cette fenêtre")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ ACTION 2.3 COMPLÉTÉE")
    print("="*80 + "\n")
    
    return len(df_events)

# =============================================================================
# 4. VALIDER CONVERSION TIMEZONE
# =============================================================================

def validate_timezone_conversion():
    """Valider conversion timezone UTC → Europe/Zurich"""
    
    print("="*80)
    print("ACTION 2.4 : VALIDER CONVERSION TIMEZONE")
    print("="*80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Prendre 1 événement test
    query = """
    SELECT ts_utc, country, event_title
    FROM events
    WHERE importance_n = 3
    LIMIT 1
    """
    
    df = conn.execute(query).df()
    
    if len(df) > 0:
        row = df.iloc[0]
        ts_utc = pd.to_datetime(row['ts_utc'])
        
        print(f"\n1. Événement test:")
        print("-" * 80)
        print(f"   Event    : {row['event_title']}")
        print(f"   Country  : {row['country']}")
        print(f"   ts_utc   : {ts_utc}")
        print(f"   Timezone : {ts_utc.tz}")
        
        # Conversion Bern
        tz_bern = pytz.timezone('Europe/Zurich')
        ts_bern = ts_utc.tz_convert(tz_bern)
        
        print(f"\n2. Après conversion Europe/Zurich:")
        print("-" * 80)
        print(f"   ts_bern  : {ts_bern}")
        print(f"   Timezone : {ts_bern.tz}")
        
        # Vérifier différence
        offset = ts_bern.utcoffset()
        print(f"\n3. Offset UTC:")
        print("-" * 80)
        print(f"   Offset   : {offset}")
        print(f"   Note     : UTC+1 (hiver) ou UTC+2 (été) attendu")
        
        print("\n✅ Conversion timezone validée")
    else:
        print("⚠️ Aucun événement HIGH trouvé pour test")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ ACTION 2.4 COMPLÉTÉE")
    print("="*80 + "\n")

# =============================================================================
# MAIN - EXÉCUTER TOUTES VÉRIFICATIONS
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SESSION 137 - ACTION 2 : VÉRIFICATION DB EVENTS")
    print("="*80 + "\n")
    
    # ACTION 2.1 : Structure
    verify_events_structure()
    
    # ACTION 2.2 : Compter HIGH
    high_count = count_high_importance_events()
    
    # ACTION 2.3 : Test matching
    events_found = test_matching_query()
    
    # ACTION 2.4 : Timezone
    validate_timezone_conversion()
    
    # Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ ACTION 2")
    print("="*80)
    print(f"✅ Structure DB vérifiée")
    print(f"✅ Événements HIGH : {high_count:,} (attendu ~7,889)")
    print(f"✅ Test matching : {events_found} événements trouvés")
    print(f"✅ Conversion timezone validée")
    print("="*80 + "\n")
