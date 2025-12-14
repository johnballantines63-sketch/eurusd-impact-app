#!/usr/bin/env python3
"""
Diagnostic COMPLET - Comprendre où sont les NFP du 1er août 2025

HYPOTHÈSES À TESTER:
1. Événements présents mais importance_n = 1 (LOW) au lieu de 3 (HIGH)
2. Événements présents mais heure différente (décalage timezone)
3. Événements présents mais country != 'US' 
4. Événements vraiment absents de la DB
"""

import duckdb
import pandas as pd
import pytz

db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
tz_bern = pytz.timezone('Europe/Zurich')

conn = duckdb.connect(db_path, read_only=True)

print("="*100)
print("DIAGNOSTIC COMPLET - NFP 1ER AOÛT 2025")
print("="*100 + "\n")

# ============================================================================
# TEST 1 : Chercher TOUS événements 1er août (toutes importances, tous pays)
# ============================================================================
print("TEST 1 : TOUS événements 1er août (aucun filtre)")
print("-"*100)

query1 = """
SELECT 
    ts_utc,
    country,
    event_title,
    importance_n,
    actual
FROM events
WHERE ts_utc >= '2025-08-01 00:00:00'
  AND ts_utc < '2025-08-02 00:00:00'
ORDER BY ts_utc
"""

df1 = conn.execute(query1).df()
print(f"Total événements 1er août : {len(df1)}\n")

if len(df1) > 0:
    print("Résumé par importance_n :")
    for imp in [1, 2, 3]:
        count = len(df1[df1['importance_n'] == imp])
        print(f"  importance_n = {imp} : {count} événements")
    
    print("\nRésumé par pays (top 10) :")
    country_counts = df1['country'].value_counts().head(10)
    for country, count in country_counts.items():
        print(f"  {country} : {count} événements")

# ============================================================================
# TEST 2 : Événements US du 1er août (TOUTES importances)
# ============================================================================
print("\n" + "="*100)
print("TEST 2 : Événements US 1er août (toutes importances)")
print("-"*100)

query2 = """
SELECT 
    ts_utc,
    event_title,
    importance_n,
    actual,
    estimate,
    previous
FROM events
WHERE country = 'US'
  AND ts_utc >= '2025-08-01 00:00:00'
  AND ts_utc < '2025-08-02 00:00:00'
ORDER BY ts_utc, importance_n DESC
"""

df2 = conn.execute(query2).df()
print(f"Événements US 1er août : {len(df2)}\n")

if len(df2) > 0:
    print("Détail par heure (UTC → CEST) :")
    for _, row in df2.iterrows():
        event_utc = pd.to_datetime(row['ts_utc'], utc=True)
        event_cest = event_utc.tz_convert(tz_bern)
        
        imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(row['importance_n'], "?")
        title = row['event_title'] if row['event_title'] else "Unknown Event"
        
        print(f"{event_cest.strftime('%H:%M')} CEST | {event_utc.strftime('%H:%M')} UTC | "
              f"{imp_label:4s} | {title[:40]:40s} | A:{row['actual']}")

# ============================================================================
# TEST 3 : Chercher spécifiquement 12:30 UTC (= 14:30 CEST heure NFP)
# ============================================================================
print("\n" + "="*100)
print("TEST 3 : Événements à 12:30 UTC (= 14:30 CEST, heure typique NFP)")
print("-"*100)

query3 = """
SELECT 
    ts_utc,
    country,
    event_title,
    importance_n,
    actual
FROM events
WHERE ts_utc >= '2025-08-01 12:25:00'
  AND ts_utc <= '2025-08-01 12:35:00'
ORDER BY ts_utc
"""

df3 = conn.execute(query3).df()
print(f"Événements à 12:30 UTC ±5 min : {len(df3)}\n")

if len(df3) > 0:
    for _, row in df3.iterrows():
        event_utc = pd.to_datetime(row['ts_utc'], utc=True)
        event_cest = event_utc.tz_convert(tz_bern)
        imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(row['importance_n'], "?")
        title = row['event_title'] if row['event_title'] else "Unknown Event"
        
        print(f"{event_cest.strftime('%H:%M:%S')} CEST | {event_utc.strftime('%H:%M:%S')} UTC | "
              f"{imp_label:4s} | {row['country']:3s} | {title}")
else:
    print("❌ AUCUN événement à 12:30 UTC (= 14:30 CEST)")
    print("   Les NFP sont absents de la DB à cette heure précise\n")

# ============================================================================
# TEST 4 : Chercher termes NFP/Employment PARTOUT dans août 2025
# ============================================================================
print("\n" + "="*100)
print("TEST 4 : Chercher NFP/Employment/Payroll dans TOUT août 2025")
print("-"*100)

query4 = """
SELECT 
    ts_utc,
    country,
    event_title,
    importance_n,
    actual
FROM events
WHERE ts_utc >= '2025-08-01 00:00:00'
  AND ts_utc < '2025-09-01 00:00:00'
  AND (
    LOWER(event_title) LIKE '%farm%'
    OR LOWER(event_title) LIKE '%employment%'
    OR LOWER(event_title) LIKE '%payroll%'
    OR LOWER(event_title) LIKE '%jobless%'
    OR LOWER(event_title) LIKE '%nfp%'
  )
ORDER BY ts_utc
"""

df4 = conn.execute(query4).df()
print(f"Événements emploi/NFP dans tout août 2025 : {len(df4)}\n")

if len(df4) > 0:
    for _, row in df4.iterrows():
        event_utc = pd.to_datetime(row['ts_utc'], utc=True)
        event_cest = event_utc.tz_convert(tz_bern)
        imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(row['importance_n'], "?")
        
        print(f"{event_cest.strftime('%Y-%m-%d %H:%M')} CEST | {imp_label:4s} | {row['country']:3s} | {row['event_title']}")
else:
    print("❌ AUCUN événement NFP/Employment trouvé dans août 2025")

# ============================================================================
# TEST 5 : Comparer avec septembre (on sait que 11 sept a des events)
# ============================================================================
print("\n" + "="*100)
print("TEST 5 : Comparaison avec 11 septembre 2025 (référence valide)")
print("-"*100)

query5 = """
SELECT 
    ts_utc,
    country,
    event_title,
    importance_n,
    actual
FROM events
WHERE country = 'US'
  AND ts_utc >= '2025-09-11 12:25:00'
  AND ts_utc <= '2025-09-11 12:35:00'
ORDER BY ts_utc
"""

df5 = conn.execute(query5).df()
print(f"Événements US 11 sept à 12:30 UTC ±5 min : {len(df5)}\n")

if len(df5) > 0:
    print("11 SEPTEMBRE (référence valide) :")
    for _, row in df5.iterrows():
        event_utc = pd.to_datetime(row['ts_utc'], utc=True)
        event_cest = event_utc.tz_convert(tz_bern)
        imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(row['importance_n'], "?")
        title = row['event_title'] if row['event_title'] else "Unknown Event"
        
        print(f"  {event_cest.strftime('%H:%M:%S')} CEST | {imp_label:4s} | {title[:40]:40s} | A:{row['actual']}")

conn.close()

# ============================================================================
# CONCLUSION
# ============================================================================
print("\n" + "="*100)
print("CONCLUSION DIAGNOSTIC")
print("="*100)

print("\n1. DONNÉES 1ER AOÛT :")
print(f"   - Total événements : {len(df1)}")
print(f"   - Événements US : {len(df2)}")
print(f"   - Événements à 12:30 UTC : {len(df3)}")
print(f"   - Événements emploi/NFP août : {len(df4)}")

print("\n2. DONNÉES 11 SEPTEMBRE (référence) :")
print(f"   - Événements US à 12:30 UTC : {len(df5)}")

print("\n3. INTERPRÉTATION :")
if len(df3) == 0 and len(df5) > 0:
    print("   ✅ Les événements du 11 septembre sont présents")
    print("   ❌ Les événements du 1er août à 14:30 CEST sont ABSENTS")
    print("   → Données incomplètes dans warehouse.duckdb pour cette date")
elif len(df2) > 0:
    print("   ⚠️  Événements US présents le 1er août mais PAS à 14:30 CEST")
    print("   → Spike 184.7 pips à 14:30 = mouvement 'unclustered' (sans events)")
else:
    print("   ❌ Très peu d'événements US le 1er août")
    print("   → Import incomplet pour cette journée")

print("\n4. RECOMMANDATION :")
print("   Option A : Scanner avec données existantes (58k événements)")
print("              → Mouvements unclustered = patterns sans événements")
print("   Option B : Enrichir DB avant scan")
print("              → Import données NFP août + autres dates incomplètes")

print("\n" + "="*100)
