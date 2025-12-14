"""
SESSION 18 - INVESTIGATION CONFUSION MENSUEL/ANNUEL
Objectif : Comprendre pourquoi EODHD importe des données incorrectes
Auteur : Claude
Date : 19 octobre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path
import os
import requests

print("=" * 80)
print("🔍 INVESTIGATION CONFUSION MENSUEL/ANNUEL")
print("=" * 80)

# Connexion DB
db_path = Path('fx_impact_app/data/warehouse.duckdb')
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# PARTIE 1 : CAS 11 SEPTEMBRE - COMPARAISON API vs DB
# ============================================================================

print("\n" + "=" * 80)
print("📅 PARTIE 1 : CAS 11 SEPTEMBRE 2025 - DIAGNOSTIC")
print("=" * 80)

# Vérifier ce qu'on a dans la DB
query_db = """
SELECT 
    e.event_key,
    e.event_title,
    e.country,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.previous,
    e.unit,
    e.type,
    e.label
FROM events e
WHERE strftime(e.ts_utc, '%Y-%m-%d') = '2025-09-11'
    AND e.country = 'US'
    AND (e.event_key LIKE '%inflation%' OR e.event_key = 'cpi')
ORDER BY e.ts_utc, e.event_title
"""

df_db = conn.execute(query_db).df()

print("\n📊 DONNÉES DANS DB (11 septembre) :")
if len(df_db) > 0:
    print(df_db.to_string(index=False))
else:
    print("⚠️ Aucun événement trouvé")

# Appeler API EODHD pour même date
api_key = os.environ.get("EODHD_API_KEY")
if api_key:
    print("\n📡 APPEL API EODHD (11 septembre) :")
    
    params = {
        "from": "2025-09-11",
        "to": "2025-09-11",
        "api_token": api_key,
        "fmt": "json",
        "countries": "US"
    }
    
    try:
        response = requests.get("https://eodhd.com/api/economic-events", params=params, timeout=30)
        data = response.json()
        
        if isinstance(data, dict):
            data = [data]
        
        # Filtrer inflation events
        inflation_events = [e for e in data if 'inflation' in e.get('type', '').lower() or 'cpi' in e.get('type', '').lower()]
        
        print(f"\n✅ {len(inflation_events)} événements inflation/CPI trouvés dans API\n")
        
        for event in inflation_events:
            print(f"📊 Type : {event.get('type')}")
            print(f"   Date/Heure : {event.get('date')}")
            print(f"   Actual : {event.get('actual')}")
            print(f"   Estimate : {event.get('estimate')}")
            print(f"   Previous : {event.get('previous')}")
            
            # Calculer surprise
            if event.get('estimate') is not None and event.get('actual') is not None:
                try:
                    estimate = float(event.get('estimate'))
                    actual = float(event.get('actual'))
                    if estimate != 0:
                        surprise = abs((actual - estimate) / estimate) * 100
                        print(f"   💡 Surprise : {surprise:.2f}%")
                        
                        if surprise > 20:
                            print(f"   🔥 SURPRISE ÉLEVÉE détectée !")
                except:
                    pass
            print()
    
    except Exception as e:
        print(f"\n❌ Erreur API : {e}")

# ============================================================================
# PARTIE 2 : PATTERNS GÉNÉRAUX DE CONFUSION
# ============================================================================

print("\n" + "=" * 80)
print("📊 PARTIE 2 : PATTERNS GÉNÉRAUX (Tous Inflation Rate)")
print("=" * 80)

# Chercher tous les Inflation Rate avec surprise = 0%
query_patterns = """
SELECT 
    e.country,
    strftime(e.ts_utc, '%Y-%m-%d %H:%M') as datetime,
    e.event_title,
    e.actual,
    e.estimate,
    e.previous,
    CASE 
        WHEN e.estimate IS NOT NULL AND e.estimate != 0 
        THEN ROUND(ABS((e.actual - e.estimate) / e.estimate) * 100, 2)
        ELSE NULL 
    END as surprise_pct
FROM events e
WHERE e.event_key = 'inflation rate'
    AND e.estimate IS NOT NULL
    AND e.ts_utc >= '2025-01-01'
ORDER BY e.ts_utc DESC
LIMIT 20
"""

df_patterns = conn.execute(query_patterns).df()

print("\n📋 20 derniers Inflation Rate (2025) :")
print(df_patterns.to_string(index=False))

# Statistiques sur surprises
zero_surprises = df_patterns[df_patterns['surprise_pct'] == 0]
print(f"\n⚠️ Surprises = 0% : {len(zero_surprises)}/{len(df_patterns)} ({len(zero_surprises)/len(df_patterns)*100:.1f}%)")

# ============================================================================
# PARTIE 3 : ANALYSE event_title vs event_key
# ============================================================================

print("\n" + "=" * 80)
print("📊 PARTIE 3 : VARIANTES ÉVÉNEMENTS")
print("=" * 80)

# Chercher toutes les variantes pour US CPI/Inflation le 11 septembre
query_sept11_all = """
SELECT 
    e.event_key,
    e.event_title,
    strftime(e.ts_utc, '%H:%M') as time,
    e.actual,
    e.estimate,
    e.previous,
    CASE 
        WHEN e.estimate IS NOT NULL AND e.estimate != 0 
        THEN ROUND(ABS((e.actual - e.estimate) / e.estimate) * 100, 2)
        ELSE NULL 
    END as surprise_pct
FROM events e
WHERE strftime(e.ts_utc, '%Y-%m-%d') = '2025-09-11'
    AND e.country = 'US'
    AND (e.event_key LIKE '%inflation%' OR e.event_key = 'cpi')
ORDER BY e.ts_utc, e.event_title
"""

df_sept11_all = conn.execute(query_sept11_all).df()

print("\n📋 TOUS les événements CPI/Inflation US du 11 septembre :")
print(df_sept11_all.to_string(index=False))

# ============================================================================
# SYNTHÈSE
# ============================================================================

print("\n" + "=" * 80)
print("📊 SYNTHÈSE")
print("=" * 80)

print("""
🔍 À VÉRIFIER :

1. Comparer valeurs API vs DB ci-dessus
2. Identifier si API fournit PLUSIEURS variantes (Monthly vs Annual)
3. Vérifier si actual/estimate correspondent

🎯 SI DIFFÉRENCE :
→ Problème dans calendar_to_events_df()
→ Nécessite correction du code d'import

🎯 SI IDENTIQUE :
→ EODHD fournit directement mauvaises données
→ Nécessite source alternative (MyFxBook, Trading Economics)
""")

conn.close()

print("\n✅ Investigation terminée !")
print("=" * 80)
