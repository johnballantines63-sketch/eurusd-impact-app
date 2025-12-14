"""
Vérifier si événements HIGH sont bien visibles pour validate_cluster_sept11.py

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Debug final
"""

import duckdb
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import pytz

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def verify_events_detection():
    """Vérifier détection événements par validate_cluster_sept11.py"""
    
    print("=" * 80)
    print("VÉRIFICATION DÉTECTION ÉVÉNEMENTS")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ========================================================================
    # 1. ÉVÉNEMENTS HIGH 11 SEPTEMBRE (GLOBAL)
    # ========================================================================
    
    print("1. ÉVÉNEMENTS HIGH 11 SEPTEMBRE (DANS DB)")
    print("=" * 80)
    print()
    
    query_high = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND importance = 'HIGH'
    ORDER BY datetime_utc
    """
    
    high_events = conn.execute(query_high).df()
    
    print(f"Total HIGH dans DB : {len(high_events)}")
    print()
    
    if len(high_events) > 0:
        for idx, row in high_events.iterrows():
            dt = pd.to_datetime(row['datetime_utc'])
            print(f"   {dt} - {row['country']} - {row['event_name']}")
        print()
    else:
        print("❌ AUCUN événement HIGH dans DB !")
        print("   → Reclassification pas persistée")
        print()
    
    # ========================================================================
    # 2. SIMULATION validate_cluster_sept11.py
    # ========================================================================
    
    print("2. SIMULATION validate_cluster_sept11.py")
    print("=" * 80)
    print()
    
    # Baseline 14:29 Bern
    date_str = '2025-09-11'
    dt = pd.to_datetime(date_str).tz_localize('Europe/Zurich')
    baseline_time = dt.replace(hour=14, minute=29, second=0)
    
    print(f"Baseline Bern : {baseline_time}")
    
    # Convertir en UTC
    baseline_utc = baseline_time.tz_convert('UTC')
    print(f"Baseline UTC  : {baseline_utc}")
    print()
    
    # Fenêtre
    lookback = 30
    lookforward = 10
    start = baseline_utc - timedelta(minutes=lookback)
    end = baseline_utc + timedelta(minutes=lookforward)
    
    print(f"Fenêtre recherche :")
    print(f"   Start : {start} ({lookback} min avant)")
    print(f"   End   : {end} ({lookforward} min après)")
    print()
    
    # Query exacte de validate_cluster_sept11.py
    query_window = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE datetime_utc >= ?
      AND datetime_utc <= ?
      AND country IN ('usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf')
    ORDER BY datetime_utc
    """
    
    events_window = conn.execute(query_window, [start, end]).fetchall()
    
    print(f"Événements détectés dans fenêtre : {len(events_window)}")
    print()
    
    if len(events_window) > 0:
        print("Événements (premiers 20) :")
        for i, row in enumerate(events_window[:20], 1):
            dt_utc = pd.to_datetime(row[0], utc=True)
            print(f"   {i}. {dt_utc} - {row[2].upper()} - {row[1]} - {row[3]}")
        
        if len(events_window) > 20:
            print(f"   ... +{len(events_window)-20} autres")
        print()
        
        # Compter HIGH
        high_count = sum(1 for row in events_window if row[3] == 'HIGH')
        print(f"   HIGH dans fenêtre : {high_count}")
        print()
        
        if high_count == 0:
            print("❌ Aucun HIGH détecté dans fenêtre !")
            print()
            print("Vérification importance des événements :")
            for row in events_window[:10]:
                print(f"   {row[1][:40]:40s} → importance: '{row[3]}'")
            print()
    else:
        print("❌ Aucun événement dans fenêtre !")
        print()
        print("Problème : fenêtre temporelle ou timezone")
        print()
    
    # ========================================================================
    # 3. VÉRIFICATION TIMEZONE
    # ========================================================================
    
    print("3. VÉRIFICATION TIMEZONE")
    print("=" * 80)
    print()
    
    # Événements à 12:30 UTC
    query_1230 = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND HOUR(datetime_utc) = 12
      AND MINUTE(datetime_utc) = 30
      AND country = 'usd'
    """
    
    events_1230 = conn.execute(query_1230).df()
    
    print(f"Événements USD 12:30 UTC : {len(events_1230)}")
    if len(events_1230) > 0:
        print()
        for idx, row in events_1230.iterrows():
            print(f"   {row['event_name']} - {row['importance']}")
        print()
    
    # Convertir 12:30 UTC en Bern
    utc_12_30 = datetime(2025, 9, 11, 12, 30, 0, tzinfo=pytz.UTC)
    bern_time = utc_12_30.astimezone(pytz.timezone('Europe/Zurich'))
    
    print(f"12:30 UTC = {bern_time.strftime('%H:%M')} Bern")
    print(f"Baseline  = 14:29 Bern")
    print(f"Delta     = {(bern_time.hour * 60 + bern_time.minute) - (14 * 60 + 29)} min")
    print()
    
    delta_minutes = (bern_time.hour * 60 + bern_time.minute) - (14 * 60 + 29)
    if -30 <= delta_minutes <= 10:
        print(f"✅ Delta {delta_minutes} min DANS fenêtre [-30, +10]")
    else:
        print(f"❌ Delta {delta_minutes} min HORS fenêtre [-30, +10]")
    
    print()
    
    conn.close()
    
    print("=" * 80)


if __name__ == '__main__':
    verify_events_detection()
