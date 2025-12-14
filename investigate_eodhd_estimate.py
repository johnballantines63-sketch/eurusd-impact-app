#!/usr/bin/env python3
"""
Investigation approfondie de l'API EODHD
pour trouver les forecast/consensus
"""

import os
import requests
import json

api_key = os.environ.get("EODHD_API_KEY")

print("=" * 80)
print("🔍 INVESTIGATION API EODHD - RECHERCHE FORECAST")
print("=" * 80)

# Test 1 : Événement passé avec actual connu (devrait avoir estimate)
print("\n1️⃣ Test sur événement passé avec valeur publiée...\n")

# NFP de septembre 2025 par exemple
params = {
    "from": "2025-09-01",
    "to": "2025-09-15",
    "api_token": api_key,
    "fmt": "json",
    "countries": "US"
}

url = "https://eodhd.com/api/economic-events"
response = requests.get(url, params=params, timeout=30)
data = response.json()

if isinstance(data, dict):
    data = [data]

# Chercher NFP, CPI, ou autres événements majeurs
major_events = [e for e in data if any(term in e.get('type', '').upper() 
                for term in ['PAYROLL', 'CPI', 'EMPLOYMENT', 'JOBLESS', 'INFLATION'])]

print(f"Événements majeurs trouvés: {len(major_events)}\n")

for event in major_events[:10]:
    print(f"📊 {event.get('type')}")
    print(f"   Date: {event.get('date')}")
    print(f"   Actual: {event.get('actual')}")
    print(f"   Estimate: {event.get('estimate')}")  # C'est ça le forecast !
    print(f"   Previous: {event.get('previous')}")
    
    # Vérifier si estimate est rempli
    if event.get('estimate') is not None:
        print(f"   ✅ ESTIMATE PRÉSENT = {event.get('estimate')}")
    print()

# Test 2 : Vérifier notre DB pour voir ce qu'on a stocké
print("\n2️⃣ Vérification de ce qui est stocké dans notre DB...\n")

import duckdb

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=False)

# Vérifier structure table events
schema = conn.execute("DESCRIBE events").fetchdf()
print("Colonnes de la table 'events':")
print(schema[['column_name', 'column_type']].to_string(index=False))

# Vérifier si 'estimate' est stocké
has_estimate = 'estimate' in schema['column_name'].values
has_forecast = 'forecast' in schema['column_name'].values

print(f"\n✅ Colonne 'estimate' existe: {has_estimate}")
print(f"✅ Colonne 'forecast' existe: {has_forecast}")

if has_estimate:
    # Compter combien ont des valeurs
    count_estimate = conn.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(estimate) as has_estimate,
            SUM(CASE WHEN estimate IS NOT NULL AND estimate != 0 THEN 1 ELSE 0 END) as usable_estimate
        FROM events
    """).fetchdf()
    
    print("\nStatistiques 'estimate' dans events:")
    print(count_estimate.to_string(index=False))
    
    # Exemples
    examples = conn.execute("""
        SELECT 
            strftime(ts_utc, '%Y-%m-%d') as date,
            event_title,
            actual,
            estimate,
            previous
        FROM events
        WHERE estimate IS NOT NULL 
            AND estimate != 0
        LIMIT 10
    """).fetchdf()
    
    print("\n📋 Exemples avec estimate:")
    print(examples.to_string(index=False))

if has_forecast:
    count_forecast = conn.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(forecast) as has_forecast,
            SUM(CASE WHEN forecast IS NOT NULL AND forecast != 0 THEN 1 ELSE 0 END) as usable_forecast
        FROM events
    """).fetchdf()
    
    print("\nStatistiques 'forecast' dans events:")
    print(count_forecast.to_string(index=False))

conn.close()

print("\n" + "=" * 80)
print("💡 CONCLUSIONS")
print("=" * 80)
print("""
EODHD utilise 'estimate' au lieu de 'forecast' !

Si 'estimate' contient des valeurs dans l'API mais pas dans notre DB :
→ Le code d'ingestion ne stocke pas 'estimate' correctement

Si 'estimate' est dans la DB mais toujours NULL :
→ EODHD ne fournit pas systématiquement les consensus

Solutions :
1. Vérifier le code d'ingestion (ingest_eodhd_calendar.py)
2. S'assurer qu'on mappe bien 'estimate' → 'forecast' dans la DB
3. Si EODHD insuffisant → Passer à Trading Economics ou Investing.com
""")
