#!/usr/bin/env python3
"""Investigation 11 septembre - Pourquoi absent de event_impacts_v2 ?"""

import duckdb

con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("INVESTIGATION 11 SEPTEMBRE 2025")
print("="*60)

# 1. Dans events (table brute) ?
print("\n1. Recherche dans events (table brute)...")

sept11_events = con.execute("""
    SELECT 
        ts_utc,
        event_key,
        event_title,
        country,
        actual,
        forecast,
        previous,
        CASE 
            WHEN forecast IS NOT NULL AND forecast != 0 
            THEN ABS((actual - forecast) / forecast) * 100
            ELSE NULL
        END as surprise_calc
    FROM events
    WHERE ts_utc::DATE = '2025-09-11'
    ORDER BY ts_utc
""").df()

if len(sept11_events) == 0:
    print("❌ Aucun événement 11 septembre dans events !")
    con.close()
    exit(1)

print(f"✅ {len(sept11_events)} événements 11 septembre dans events")

# 2. Afficher tous les événements avec leur surprise
print(f"\nDétail des {len(sept11_events)} événements :")
for i, evt in sept11_events.iterrows():
    surprise = evt['surprise_calc']
    ts = evt['ts_utc']
    print(f"\n{i+1}. {ts} - {evt['event_title']} ({evt['country']})")
    print(f"   actual={evt['actual']}, forecast={evt['forecast']}, previous={evt['previous']}")
    if surprise is not None:
        print(f"   Surprise: {surprise:.1f}%")
        if surprise >= 30:
            print(f"   ✅ Surprise >= 30% (devrait être dans event_impacts_v2)")
        else:
            print(f"   ❌ Surprise < 30% (filtré de event_impacts_v2)")
    else:
        print(f"   ⚠️  Surprise: NULL (forecast manquant)")

# 3. Chercher Inflation Rate MoM spécifiquement
print("\n" + "="*60)
print("3. Recherche Inflation Rate MoM spécifiquement...")

inflation = con.execute("""
    SELECT 
        ts_utc,
        event_key,
        event_title,
        actual,
        forecast,
        previous,
        CASE 
            WHEN forecast IS NOT NULL AND forecast != 0 
            THEN ABS((actual - forecast) / forecast) * 100
            ELSE NULL
        END as surprise_calc
    FROM events
    WHERE ts_utc::DATE = '2025-09-11'
    AND (event_title LIKE '%Inflation%' OR event_key LIKE '%inflation%')
""").df()

if len(inflation) > 0:
    print(f"✅ {len(inflation)} événements inflation trouvés :")
    for _, evt in inflation.iterrows():
        surprise = evt['surprise_calc']
        print(f"\n   {evt['event_title']}")
        print(f"   Heure: {evt['ts_utc']}")
        print(f"   actual={evt['actual']}, forecast={evt['forecast']}")
        if surprise:
            print(f"   Surprise: {surprise:.1f}%")
            if abs(surprise - 33.3) < 5:
                print(f"   ✅ C'est le bon événement (surprise 33.3%)")
        else:
            print(f"   Surprise: NULL")
else:
    print("❌ Aucun événement inflation trouvé")

# 4. Vérifier dans event_impacts_v2
print("\n" + "="*60)
print("4. Dans event_impacts_v2...")

v2_sept11 = con.execute("""
    SELECT 
        ts_utc,
        event_title,
        surprise_pct
    FROM event_impacts_v2
    WHERE ts_utc::DATE = '2025-09-11'
""").df()

if len(v2_sept11) > 0:
    print(f"✅ {len(v2_sept11)} événements 11 sept dans event_impacts_v2")
    for _, evt in v2_sept11.iterrows():
        print(f"   {evt['ts_utc']} - {evt['event_title']} (surprise={evt['surprise_pct']:.1f}%)")
else:
    print("❌ Aucun événement 11 sept dans event_impacts_v2")

# 5. Compter événements avec surprise >= 30%
print("\n" + "="*60)
print("5. Combien d'événements 11 sept ont surprise >= 30% ?")

count_above = con.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE 
            WHEN forecast IS NOT NULL AND forecast != 0 
            AND ABS((actual - forecast) / forecast) * 100 >= 30
            THEN 1 ELSE 0 
        END) as above_30
    FROM events
    WHERE ts_utc::DATE = '2025-09-11'
""").fetchone()

print(f"   Total événements 11 sept: {count_above[0]}")
print(f"   Avec surprise >= 30%: {count_above[1]}")

if count_above[1] > 0:
    print(f"\n   ✅ Il devrait y avoir {count_above[1]} événements dans event_impacts_v2")
else:
    print(f"\n   ❌ Aucun événement 11 sept n'a surprise >= 30%")

print("\n" + "="*60)
print("CONCLUSION:")
print("="*60)

if count_above[1] > 0 and len(v2_sept11) == 0:
    print("❌ PROBLÈME: Événements 11 sept avec surprise >= 30% existent")
    print("   mais ne sont PAS dans event_impacts_v2")
    print("   → event_impacts_v2 a été mal créé ou filtré incorrectement")
elif count_above[1] == 0:
    print("⚠️  Aucun événement 11 sept n'a surprise >= 30%")
    print("   → Vérifier calcul surprise (forecast correct ?)")
else:
    print("✅ OK")

con.close()
