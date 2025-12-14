"""
Vérification DB Restaurée
=========================

Vérifier que la DB restaurée contient les événements 11 septembre 2025
avec forecast/estimate
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

print("\n" + "="*80)
print("VÉRIFICATION DB RESTAURÉE")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Vérifier tables existantes
print("📊 TABLES DISPONIBLES:")
tables = conn.execute("SHOW TABLES").df()
event_tables = [t for t in tables['name'] if 'event' in t.lower()]

for table in event_tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"   {table:30s} : {count:,} rows")

print()

# 2. Déterminer la table events correcte
if 'events' in tables['name'].values:
    table_name = 'events'
    print("✅ Table 'events' trouvée (ancienne structure)")
elif 'economic_events' in tables['name'].values:
    table_name = 'economic_events'
    print("⚠️  Table 'economic_events' trouvée (structure EODHD)")
else:
    print("❌ Aucune table events trouvée !")
    conn.close()
    exit(1)

print()

# 3. Vérifier structure
print("="*80)
print(f"STRUCTURE TABLE '{table_name}'")
print("="*80)
print()

cols = conn.execute(f"""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = '{table_name}'
    ORDER BY ordinal_position
""").df()

for _, col in cols.iterrows():
    print(f"   {col['column_name']:20s} : {col['data_type']}")

print()

# 4. Chercher événements 11 septembre 2025
print("="*80)
print("ÉVÉNEMENTS 11 SEPTEMBRE 2025")
print("="*80)
print()

if table_name == 'events':
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
      AND importance_n >= 2
      AND LOWER(country) IN ('usd', 'eur', 'de')
    ORDER BY ts_utc, importance_n DESC
    """
else:
    query = """
    SELECT 
        datetime_utc,
        country,
        event_name,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE datetime_utc::DATE = '2025-09-11'
      AND importance IN ('HIGH', 'MEDIUM')
      AND LOWER(country) IN ('usd', 'eur', 'de')
    ORDER BY datetime_utc
    """

events = conn.execute(query).df()

print(f"📊 Événements HIGH/MEDIUM: {len(events)}")
print()

if len(events) == 0:
    print("❌ AUCUN événement 11 septembre 2025 trouvé !")
    print()
    print("⚠️  La DB restaurée est probablement une mauvaise version.")
    print("   Essayer une date Time Machine plus ancienne.")
    
else:
    print("✅ ÉVÉNEMENTS TROUVÉS")
    print()
    
    # Afficher tous
    for idx, event in events.iterrows():
        if table_name == 'events':
            imp = {3: "HIGH", 2: "MEDIUM"}.get(event['importance_n'], "LOW")
            print(f"{idx+1}. {event['ts_utc']} | {event['country'].upper()} | {imp}")
            print(f"   {event['event_title']}")
            print(f"   Actual: {event['actual']}")
            print(f"   Estimate: {event['estimate']}")
            print(f"   Forecast: {event['forecast']}")
            print(f"   Previous: {event['previous']}")
            
            # Calculer surprise si possible
            ref = event['estimate'] if pd.notna(event['estimate']) else event['forecast']
            if pd.notna(event['actual']) and pd.notna(ref) and abs(ref) > 0.001:
                surprise = ((event['actual'] - ref) / abs(ref)) * 100
                print(f"   Surprise: {surprise:+.2f}%")
        else:
            print(f"{idx+1}. {event['datetime_utc']} | {event['country'].upper()} | {event['importance']}")
            print(f"   {event['event_name']}")
            print(f"   Actual: {event['actual']}")
            print(f"   Forecast: {event['forecast']}")
            print(f"   Previous: {event['previous']}")
        
        print()
    
    # 5. Vérifier que forecast/estimate sont remplis
    print("="*80)
    print("ANALYSE QUALITÉ DONNÉES")
    print("="*80)
    print()
    
    if table_name == 'events':
        with_estimate = events['estimate'].notna().sum()
        with_forecast = events['forecast'].notna().sum()
        with_actual = events['actual'].notna().sum()
        
        print(f"Événements avec actual:   {with_actual}/{len(events)} ({100*with_actual/len(events):.1f}%)")
        print(f"Événements avec estimate: {with_estimate}/{len(events)} ({100*with_estimate/len(events):.1f}%)")
        print(f"Événements avec forecast: {with_forecast}/{len(events)} ({100*with_forecast/len(events):.1f}%)")
        print()
        
        if with_estimate > 0 or with_forecast > 0:
            print("✅ FORECAST/ESTIMATE DISPONIBLES - Calcul surprises possible !")
        else:
            print("❌ Aucun forecast/estimate - DB incorrecte")
    else:
        with_forecast = events['forecast'].notna().sum()
        with_actual = events['actual'].notna().sum()
        
        print(f"Événements avec actual:   {with_actual}/{len(events)} ({100*with_actual/len(events):.1f}%)")
        print(f"Événements avec forecast: {with_forecast}/{len(events)} ({100*with_forecast/len(events):.1f}%)")

print()
print("="*80)
print("CONCLUSION")
print("="*80)
print()

if len(events) > 0 and (('estimate' in events.columns and events['estimate'].notna().sum() > 0) or 
                        ('forecast' in events.columns and events['forecast'].notna().sum() > 0)):
    print("✅ DB RESTAURÉE CORRECTEMENT")
    print()
    print("📊 Prochaines étapes:")
    print("   1. Relancer validation formules Session 124")
    print("   2. Les prédictions devraient être précises maintenant")
    print()
    print("Commande:")
    print("   python scripts/session124/run_validation_workflow.py")
else:
    print("❌ DB INCORRECTE")
    print()
    print("💡 Actions:")
    print("   1. Restaurer depuis Time Machine date PLUS ANCIENNE")
    print("   2. Cibler 6 novembre 2025 (fin Session 120)")

conn.close()
