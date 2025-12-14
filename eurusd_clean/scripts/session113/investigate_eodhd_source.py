"""
INVESTIGATION SOURCE EODHD - 11 septembre 2025
===============================================

Vérifie ce que EODHD fournit réellement pour identifier 
si les doublons viennent de la source ou de l'import.

Session 113 - André Valentin
"""
import sys
from pathlib import Path
import requests
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Clé API EODHD (à récupérer des variables d'environnement ou config)
# Note: André devra fournir sa clé API pour ce test
API_KEY = "demo"  # Remplacer par vraie clé

print("=" * 80)
print("INVESTIGATION SOURCE EODHD - 11 SEPTEMBRE 2025")
print("=" * 80)

print("\n⚠️  IMPORTANT: Ce script nécessite la clé API EODHD")
print("Pour obtenir les vraies données, il faut :")
print("1. Récupérer la clé API d'André")
print("2. L'ajouter à ce script ou aux variables d'environnement")

# URL API EODHD pour calendrier économique
# https://eodhd.com/financial-apis/economic-events-data-api/

url = "https://eodhd.com/api/economic-events"

params = {
    "api_token": API_KEY,
    "from": "2025-09-11",
    "to": "2025-09-11",
    "country": "US"  # Tester d'abord US
}

print(f"\n📡 Requête EODHD:")
print(f"   Date: 2025-09-11")
print(f"   Pays: US")

try:
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✅ Réponse reçue")
        print(f"   Nombre d'événements: {len(data) if isinstance(data, list) else 'N/A'}")
        
        # Filtrer événements 14:30 (12:30 UTC)
        events_1430 = []
        
        for event in data:
            # Afficher structure pour debug
            if not events_1430:
                print(f"\n📋 Structure événement EODHD:")
                print(json.dumps(event, indent=2))
            
            # Extraire heure
            event_time = event.get('date', '')
            if '12:30' in event_time or '14:30' in event_time:
                events_1430.append(event)
        
        print(f"\n🎯 Événements à 14:30 Bern (12:30 UTC):")
        print(f"   Nombre: {len(events_1430)}")
        
        if events_1430:
            print("\n   Liste:")
            for i, evt in enumerate(events_1430, 1):
                name = evt.get('event', 'N/A')
                country = evt.get('country', 'N/A')
                actual = evt.get('actual', 'N/A')
                estimate = evt.get('estimate', 'N/A')
                print(f"   {i}. {name} ({country})")
                print(f"      Actual: {actual}, Estimate: {estimate}")
    
    elif response.status_code == 401:
        print("\n❌ Erreur 401: Clé API invalide ou manquante")
        print("   → Utiliser la vraie clé API d'André")
    
    else:
        print(f"\n❌ Erreur HTTP {response.status_code}")
        print(f"   {response.text}")

except requests.exceptions.Timeout:
    print("\n❌ Timeout: EODHD ne répond pas")

except Exception as e:
    print(f"\n❌ Erreur: {type(e).__name__}: {str(e)}")

# ============================================================================
# ALTERNATIVE: Vérifier les fichiers d'import existants
# ============================================================================

print("\n" + "=" * 80)
print("ALTERNATIVE: FICHIERS D'IMPORT EXISTANTS")
print("=" * 80)

# Chercher fichiers JSON/CSV d'import EODHD
import_dir = Path(__file__).parent.parent.parent / "data" / "raw"

print(f"\nRecherche dans: {import_dir}")

if import_dir.exists():
    # Chercher fichiers septembre 2025
    files = list(import_dir.glob("*2025-09*"))
    
    if files:
        print(f"\n✅ {len(files)} fichier(s) trouvé(s):")
        for f in files:
            print(f"   - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
            
            # Si JSON, afficher contenu
            if f.suffix == '.json' and f.stat().st_size < 1_000_000:  # < 1MB
                try:
                    with open(f, 'r') as file:
                        data = json.load(file)
                        if isinstance(data, list):
                            print(f"     Contient {len(data)} événements")
                            
                            # Filtrer 11 sept
                            events_11sept = [e for e in data if '2025-09-11' in str(e)]
                            if events_11sept:
                                print(f"     → {len(events_11sept)} événements du 11 sept")
                except:
                    pass
    else:
        print("\n⚠️  Aucun fichier septembre 2025 trouvé")
else:
    print(f"\n⚠️  Répertoire {import_dir} n'existe pas")

# ============================================================================
# INSTRUCTIONS POUR ANDRÉ
# ============================================================================

print("\n" + "=" * 80)
print("INSTRUCTIONS")
print("=" * 80)

print("""
POUR COMPLÉTER L'INVESTIGATION:

1. CLÉMENT API EODHD:
   - Récupérer la clé API (probablement dans .env ou config)
   - Remplacer "demo" par la vraie clé dans ce script
   - Relancer

2. OU FOURNIR FICHIER BRUT:
   - Si tu as sauvegardé la réponse EODHD brute du 11 sept
   - Partage le fichier JSON/CSV
   - Je l'analyserai manuellement

3. OU EXAMINER CODE IMPORT:
   - Localiser le script qui importe depuis EODHD
   - Vérifier la logique de dédoublonnage
   - Chercher si on crée des dérivés _mom/_yoy nous-mêmes

OBJECTIF:
Comprendre si EODHD envoie:
- 10 événements distincts (pas de doublons) ✅
- 17 événements (avec doublons) ❌
- Autre structure à interpréter
""")

print("=" * 80)
