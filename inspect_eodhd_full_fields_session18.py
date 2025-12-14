"""
SESSION 18 - INSPECTION COMPLÈTE RÉPONSE API EODHD
Objectif : Voir TOUS les champs retournés par EODHD pour détecter period
Auteur : Claude
Date : 19 octobre 2025
"""

import os
import requests
import json

api_key = os.environ.get("EODHD_API_KEY")

print("=" * 80)
print("🔍 INSPECTION COMPLÈTE API EODHD - 11 SEPTEMBRE")
print("=" * 80)

params = {
    "from": "2025-09-11",
    "to": "2025-09-11",
    "api_token": api_key,
    "fmt": "json",
    "countries": "US"
}

response = requests.get("https://eodhd.com/api/economic-events", params=params, timeout=30)
data = response.json()

if isinstance(data, dict):
    data = [data]

# Filtrer inflation events
inflation_events = [e for e in data if 'inflation' in e.get('type', '').lower()]

print(f"\n✅ {len(inflation_events)} événements Inflation trouvés\n")

for i, event in enumerate(inflation_events, 1):
    print(f"\n{'='*80}")
    print(f"📊 ÉVÉNEMENT #{i}")
    print(f"{'='*80}")
    
    # Afficher TOUS les champs
    print("\n🔍 TOUS LES CHAMPS (JSON complet) :")
    print(json.dumps(event, indent=2, ensure_ascii=False))
    
    print("\n📋 CHAMPS CLÉS :")
    print(f"   type         : {event.get('type')}")
    print(f"   date         : {event.get('date')}")
    print(f"   actual       : {event.get('actual')}")
    print(f"   estimate     : {event.get('estimate')}")
    print(f"   previous     : {event.get('previous')}")
    
    # Champs qui pourraient indiquer period
    potential_period_fields = [
        'period', 'frequency', 'interval', 'unit', 
        'name', 'title', 'description', 'event',
        'category', 'importance', 'impact'
    ]
    
    print("\n🎯 CHAMPS POTENTIELS POUR IDENTIFIER PERIOD :")
    for field in potential_period_fields:
        if field in event:
            print(f"   {field:15} : {event.get(field)}")
    
    # Calculer surprise
    if event.get('estimate') is not None and event.get('actual') is not None:
        try:
            est = float(event.get('estimate'))
            act = float(event.get('actual'))
            if est != 0:
                surprise = abs((act - est) / est) * 100
                print(f"\n   💡 Surprise calculée : {surprise:.2f}%")
        except:
            pass

print("\n" + "=" * 80)
print("📊 ANALYSE")
print("=" * 80)

print("""
🎯 CHERCHER DANS LES RÉSULTATS CI-DESSUS :

1. Y a-t-il un champ 'period' ou 'frequency' ?
2. Le 'type' ou 'name' contient-il 'Monthly', 'Annual', 'YoY', 'MoM' ?
3. Y a-t-il une différence dans 'category' ou 'description' ?
4. Le 'unit' indique-t-il quelque chose ?

Si AUCUN champ ne distingue Monthly vs Annual :
→ EODHD ne fournit PAS cette info explicitement
→ On doit utiliser une autre approche
""")

print("\n✅ Inspection terminée !")
print("=" * 80)
