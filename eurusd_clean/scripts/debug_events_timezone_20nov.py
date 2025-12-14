"""
Debug : Vérifier le timezone des événements pour le 20.11.2025
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
print("🔍 DEBUG : TIMEZONE DES ÉVÉNEMENTS - 20.11.2025")
print("=" * 80)
print()

# Date cible
target_date = datetime(2025, 11, 20)

# Charger les événements US autour de 14h30
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("1️⃣ ÉVÉNEMENTS US AUTOUR DE 14H30 (SANS CONVERSION)")
print("-" * 80)

query_events = """
SELECT 
    datetime_utc as ts_utc,
    event_name as event_key,
    country
FROM economic_events
WHERE DATE(datetime_utc) = ?
  AND country = 'US'
  AND EXTRACT(HOUR FROM datetime_utc) >= 12
  AND EXTRACT(HOUR FROM datetime_utc) < 16
ORDER BY datetime_utc
"""

df_events = conn.execute(query_events, [target_date.strftime('%Y-%m-%d')]).df()

if not df_events.empty:
    print(f"   ✅ {len(df_events)} événements US trouvés (12h-16h)")
    print()
    print("   Événements (ts_utc brut) :")
    for idx, row in df_events.iterrows():
        print(f"      {row['ts_utc']} | {row['event_key']}")
    
    # Vérifier si les timestamps sont déjà en UTC+2
    print()
    print("   Analyse des timestamps :")
    for idx, row in df_events.head(5).iterrows():
        ts_str = str(row['ts_utc'])
        if '+02:00' in ts_str or '+01:00' in ts_str:
            print(f"      {ts_str} → Déjà en UTC+2/UTC+1 (heure de Berne)")
        else:
            print(f"      {ts_str} → UTC pur (nécessite conversion)")
else:
    print("   ❌ Aucun événement trouvé")

print()

print("2️⃣ ÉVÉNEMENTS US AUTOUR DE 14H30 (AVEC CONVERSION +2H)")
print("-" * 80)

if not df_events.empty:
    df_events['ts_utc'] = pd.to_datetime(df_events['ts_utc'])
    df_events['ts_bern'] = df_events['ts_utc'] + pd.Timedelta(hours=2)
    
    print("   Événements après conversion +2h :")
    for idx, row in df_events.iterrows():
        print(f"      {row['ts_bern']} | {row['event_key']}")
    
    # Filtrer autour de 14h30
    events_1430 = df_events[
        (df_events['ts_bern'].dt.hour == 14) & 
        (df_events['ts_bern'].dt.minute == 30)
    ]
    
    print()
    if not events_1430.empty:
        print(f"   ✅ {len(events_1430)} événement(s) à 14:30 après conversion")
    else:
        print(f"   ❌ Aucun événement à 14:30 après conversion")
        
        # Chercher autour de 14h30
        events_around_1430 = df_events[
            (df_events['ts_bern'].dt.hour == 14) & 
            (df_events['ts_bern'].dt.minute >= 28) &
            (df_events['ts_bern'].dt.minute <= 32)
        ]
        if not events_around_1430.empty:
            print(f"   📍 {len(events_around_1430)} événement(s) autour de 14:30")
            for idx, row in events_around_1430.iterrows():
                print(f"      {row['ts_bern']} | {row['event_key']}")
        
        # Chercher à 15h30 (peut-être que c'est là qu'ils sont après conversion)
        events_1530 = df_events[
            (df_events['ts_bern'].dt.hour == 15) & 
            (df_events['ts_bern'].dt.minute == 30)
        ]
        if not events_1530.empty:
            print(f"   ⚠️ {len(events_1530)} événement(s) à 15:30 après conversion (DOUBLE DÉCALAGE !)")
            for idx, row in events_1530.head(3).iterrows():
                print(f"      {row['ts_bern']} | {row['event_key']}")

conn.close()

print()
print("=" * 80)
print("✅ DEBUG TERMINÉ")
print("=" * 80)
print()
print("💡 CONCLUSION :")
print("   Si les événements sont déjà en UTC+2 dans la DB, alors ajouter 2h crée un")
print("   double décalage (14:30 → 16:30). Il faut corriger load_events_for_date pour")
print("   ne PAS ajouter 2h si les données sont déjà en UTC+2.")
print()


