"""
Debug Extraction Événements
============================

Comparer ce que cherche extract_events_for_timestamp()
vs ce qui existe réellement dans la DB
"""

import duckdb
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import pytz

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

print("\n" + "="*80)
print("DEBUG EXTRACTION ÉVÉNEMENTS - 11 SEPTEMBRE 2025")
print("="*80)
print()

# Test avec un timestamp de pattern Rev12
peak1_time = "2025-09-11 14:35:00+02:00"  # Peak1 du pattern Rev12

print(f"📌 Timestamp test: {peak1_time}")
print()

# 1. Simulation de ce que fait extract_events_for_timestamp()
print("="*80)
print("SIMULATION extract_events_for_timestamp()")
print("="*80)
print()

ts = pd.to_datetime(peak1_time)
print(f"1. Timestamp parsé: {ts}")
print(f"   Timezone: {ts.tz}")
print()

# Convertir UTC
ts_utc = ts.astimezone(pytz.UTC)
print(f"2. Converti UTC (avec TZ): {ts_utc}")
print()

# Enlever timezone
ts_utc_naive = ts_utc.replace(tzinfo=None)
print(f"3. UTC naive (sans TZ): {ts_utc_naive}")
print()

# Fenêtre ±10 minutes
window = 10
start = ts_utc_naive - timedelta(minutes=window)
end = ts_utc_naive + timedelta(minutes=window)

print(f"4. Fenêtre recherche:")
print(f"   Start: {start}")
print(f"   End:   {end}")
print()

# 2. Test requête exacte
print("="*80)
print("TEST REQUÊTE SQL (comme dans code)")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

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
WHERE ts_utc BETWEEN ? AND ?
  AND LOWER(country) IN ('usd', 'eur', 'gbp', 'jpy', 'cad', 'chf', 'de', 'gb', 'jp', 'ca')
  AND importance_n >= 2
ORDER BY ts_utc
"""

print(f"Paramètres:")
print(f"  start: {start} (type: {type(start).__name__})")
print(f"  end:   {end} (type: {type(end).__name__})")
print()

try:
    events = conn.execute(query, [start, end]).df()
    print(f"✅ Requête réussie")
    print(f"📊 Résultat: {len(events)} événements trouvés")
    print()
    
    if len(events) > 0:
        print("Événements trouvés:")
        for _, e in events.iterrows():
            print(f"   {e['ts_utc']} | {e['country'].upper()} | {e['event_title'][:50]}")
    else:
        print("❌ AUCUN événement trouvé avec cette requête")
    
except Exception as e:
    print(f"❌ Erreur requête: {e}")

print()

# 3. Test sans filtre timezone pour voir ce qui existe
print("="*80)
print("TEST SANS FILTRES (voir ce qui existe)")
print("="*80)
print()

# Chercher TOUTE LA JOURNÉE
query_full = """
SELECT 
    ts_utc,
    country,
    event_key,
    event_title,
    importance_n
FROM events
WHERE ts_utc::DATE = '2025-09-11'
  AND LOWER(country) IN ('usd', 'eur', 'de')
  AND importance_n >= 2
ORDER BY ts_utc
"""

try:
    events_full = conn.execute(query_full).df()
    print(f"📊 Événements 11 septembre (toute journée): {len(events_full)}")
    print()
    
    if len(events_full) > 0:
        print("Liste complète:")
        for _, e in events_full.iterrows():
            imp = {3: "HIGH", 2: "MEDIUM"}.get(e['importance_n'], "?")
            print(f"   {e['ts_utc']} | {e['country'].upper()} | {imp:6s} | {e['event_title'][:40]}")
        print()
        
        # Vérifier type de ts_utc
        print("Type de ts_utc:")
        sample = events_full.iloc[0]
        print(f"   Valeur: {sample['ts_utc']}")
        print(f"   Type Python: {type(sample['ts_utc'])}")
        
        # Si timestamp pandas, vérifier timezone
        if isinstance(sample['ts_utc'], pd.Timestamp):
            print(f"   Timezone: {sample['ts_utc'].tz}")
    else:
        print("❌ Aucun événement 11 septembre trouvé !")
        
except Exception as e:
    print(f"❌ Erreur: {e}")

print()

# 4. Test avec timestamps timezone-aware
print("="*80)
print("TEST AVEC TIMESTAMPS TIMEZONE-AWARE")
print("="*80)
print()

# Recréer timestamps avec timezone
start_tz = pytz.UTC.localize(start)
end_tz = pytz.UTC.localize(end)

print(f"Fenêtre avec timezone:")
print(f"  Start: {start_tz}")
print(f"  End:   {end_tz}")
print()

query_tz = """
SELECT 
    ts_utc,
    country,
    event_title,
    importance_n
FROM events
WHERE ts_utc BETWEEN ? AND ?
  AND LOWER(country) IN ('usd', 'eur', 'de')
  AND importance_n >= 2
"""

try:
    events_tz = conn.execute(query_tz, [start_tz, end_tz]).df()
    print(f"✅ Avec TZ: {len(events_tz)} événements trouvés")
    
    if len(events_tz) > 0:
        for _, e in events_tz.iterrows():
            print(f"   {e['ts_utc']} | {e['event_title'][:40]}")
    
except Exception as e:
    print(f"❌ Erreur avec TZ: {e}")

print()

# 5. Test conversion explicite dans SQL
print("="*80)
print("TEST CONVERSION EXPLICITE SQL")
print("="*80)
print()

query_cast = f"""
SELECT 
    ts_utc,
    ts_utc::TIMESTAMP as ts_naive,
    country,
    event_title
FROM events
WHERE ts_utc::TIMESTAMP BETWEEN '{start}' AND '{end}'
  AND LOWER(country) IN ('usd', 'eur', 'de')
  AND importance_n >= 2
LIMIT 5
"""

try:
    events_cast = conn.execute(query_cast).df()
    print(f"✅ Avec CAST: {len(events_cast)} événements")
    
    if len(events_cast) > 0:
        for _, e in events_cast.iterrows():
            print(f"   {e['ts_utc']} → {e['ts_naive']}")
            print(f"   {e['event_title'][:40]}")
    
except Exception as e:
    print(f"❌ Erreur CAST: {e}")

conn.close()

print()
print("="*80)
print("CONCLUSION")
print("="*80)
print()

print("💡 SOLUTIONS POSSIBLES:")
print("   1. Utiliser timestamps timezone-aware dans paramètres")
print("   2. Convertir ts_utc en naive dans SQL: ts_utc::TIMESTAMP")
print("   3. Élargir fenêtre temporelle (±10 min → ±30 min)")
print("   4. Vérifier que conversion Bern→UTC est correcte")
