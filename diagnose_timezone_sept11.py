#!/usr/bin/env python3
"""
Diagnostic timezone - Trouver le 11 septembre
"""

import duckdb

con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("=" * 80)
print("DIAGNOSTIC TIMEZONE - 11 SEPTEMBRE 2025")
print("=" * 80)

# 1. Vérifier tous les événements du 11 septembre dans event_impacts_v2
print("\n📊 Événements dans event_impacts_v2 le 11 septembre :")

query1 = """
SELECT 
    ts_utc,
    event_title,
    phase1_pips,
    surprise_pct
FROM event_impacts_v2
WHERE ts_utc::DATE = '2025-09-11'
ORDER BY ts_utc
"""

events_sept11 = con.execute(query1).df()

if len(events_sept11) > 0:
    print(f"\n✅ {len(events_sept11)} événements trouvés\n")
    
    for idx, row in events_sept11.iterrows():
        title = row['event_title'] if row['event_title'] else 'N/A'
        ts_str = str(row['ts_utc'])
        
        # Highlight 14:30 events
        marker = "⭐⭐⭐" if ('14:30' in ts_str or '12:30' in ts_str) else "   "
        
        print(f"{marker} {row['ts_utc']} | {title[:40]:<40} | {row['phase1_pips']:>6.2f} pips | surprise: {row['surprise_pct']:>6.1f}%")
else:
    print("\n❌ AUCUN événement du 11 septembre dans event_impacts_v2")

# 2. Focus sur 14:30 et 12:30
print("\n" + "=" * 80)
print("ÉVÉNEMENTS À 14:30 OU 12:30")
print("=" * 80)

query_1430 = """
SELECT 
    ts_utc,
    event_title,
    phase1_pips,
    ttr_minutes,
    start_price,
    ttr_price,
    surprise_pct
FROM event_impacts_v2
WHERE ts_utc::DATE = '2025-09-11'
  AND (
    EXTRACT(HOUR FROM ts_utc) = 14 AND EXTRACT(MINUTE FROM ts_utc) = 30
    OR EXTRACT(HOUR FROM ts_utc) = 12 AND EXTRACT(MINUTE FROM ts_utc) = 30
  )
ORDER BY phase1_pips DESC
"""

events_target = con.execute(query_1430).df()

if len(events_target) > 0:
    print(f"\n✅ {len(events_target)} événements trouvés à 14:30 ou 12:30\n")
    
    for idx, row in events_target.iterrows():
        title = row['event_title'] if row['event_title'] else 'N/A'
        print(f"\n  📅 {row['ts_utc']}")
        print(f"  📰 {title}")
        print(f"  🎯 Phase 1 : {row['phase1_pips']:.2f} pips")
        print(f"  💰 Prix : {row['start_price']:.5f} → {row['ttr_price']:.5f}")
        print(f"  📊 Surprise : {row['surprise_pct']:.1f}%")
        
        # Validation
        expected = 37.4
        actual = row['phase1_pips']
        error = abs(actual - expected)
        error_pct = (error / expected) * 100
        
        print(f"\n  ✅ VALIDATION:")
        print(f"     Attendu (MT5) : 37.4 pips")
        print(f"     Calculé : {actual:.2f} pips")
        print(f"     Écart : {error:.2f} pips ({error_pct:.1f}%)")
        
        if error <= 5:
            print(f"     Statut : ✅ EXCELLENT")
        elif error <= 10:
            print(f"     Statut : ⚠️  ACCEPTABLE")
        else:
            print(f"     Statut : ❌ PROBLÈME")
else:
    print("\n❌ AUCUN événement à 14:30 ou 12:30")

# 3. Vérifier dans prices_1m le format exact
print("\n" + "=" * 80)
print("FORMAT TIMESTAMPS dans prices_1m (11 septembre)")
print("=" * 80)

query2 = """
SELECT datetime, open
FROM prices_1m
WHERE datetime::DATE = '2025-09-11'
  AND (
    EXTRACT(HOUR FROM datetime) = 14 
    OR EXTRACT(HOUR FROM datetime) = 12
  )
ORDER BY datetime
LIMIT 10
"""

prices_sept11 = con.execute(query2).df()

if len(prices_sept11) > 0:
    print(f"\n✅ Timestamps trouvés dans prices_1m (heures 12 et 14) :")
    for idx, row in prices_sept11.iterrows():
        print(f"  {row['datetime']} | Prix: {row['open']:.5f}")
else:
    print("\n❌ Aucun prix pour les heures 12 ou 14")

# 4. Chercher dans events bruts avec surprise
print("\n" + "=" * 80)
print("ÉVÉNEMENTS BRUTS (table events) le 11 septembre avec surprise")
print("=" * 80)

query4 = """
SELECT 
    ts_utc, 
    event_title, 
    country, 
    actual, 
    forecast,
    CASE 
        WHEN forecast IS NOT NULL AND forecast != 0 
        THEN ABS((actual - forecast) / forecast) * 100
        ELSE NULL
    END as surprise_calc
FROM events
WHERE ts_utc::DATE = '2025-09-11'
  AND actual IS NOT NULL
  AND forecast IS NOT NULL
  AND (
    EXTRACT(HOUR FROM ts_utc) = 14 AND EXTRACT(MINUTE FROM ts_utc) = 30
    OR EXTRACT(HOUR FROM ts_utc) = 12 AND EXTRACT(MINUTE FROM ts_utc) = 30
  )
ORDER BY surprise_calc DESC
"""

events_raw = con.execute(query4).df()

if len(events_raw) > 0:
    print(f"\n✅ {len(events_raw)} événements bruts à 14:30 ou 12:30")
    
    for idx, row in events_raw.iterrows():
        title = row['event_title'] if row['event_title'] else 'N/A'
        surprise = row['surprise_calc'] if row['surprise_calc'] else 0
        
        print(f"\n  {row['ts_utc']}")
        print(f"  {title}")
        print(f"  Actual: {row['actual']}, Forecast: {row['forecast']}")
        print(f"  Surprise: {surprise:.1f}%")
else:
    print("\n❌ Aucun événement brut à 14:30 ou 12:30")

# 5. CONCLUSION
print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if len(events_target) > 0:
    # Prendre le plus gros mouvement
    best = events_target.iloc[0]
    
    print(f"\n📊 Meilleur candidat trouvé :")
    print(f"   Timestamp : {best['ts_utc']}")
    print(f"   Phase 1 : {best['phase1_pips']:.2f} pips")
    print(f"   Attendu : 33-37 pips")
    
    if 30 <= best['phase1_pips'] <= 40:
        print(f"\n✅ VALIDATION OK - Dans la plage attendue")
    else:
        print(f"\n⚠️  VALIDATION PARTIELLE - Hors plage attendue")
        
    print(f"\n💡 FORMAT TIMEZONE UTILISÉ :")
    print(f"   Les timestamps dans la DB incluent l'offset : +02:00")
    print(f"   14:30+02:00 = 12:30 UTC")
    print(f"   Pour le planificateur, utiliser heure locale (14:30 Berne)")
else:
    print("\n❌ PROBLÈME : Aucun événement validé trouvé")

con.close()

print("\n" + "=" * 80)
