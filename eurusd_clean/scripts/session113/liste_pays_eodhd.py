"""
LISTE PAYS EODHD - Session 113
===============================

Récupère la liste complète des pays disponibles dans EODHD.

Session 113 - André Valentin
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from eodhd_client_corrected import fetch_calendar_json

print("=" * 80)
print("LISTE PAYS DISPONIBLES EODHD")
print("=" * 80)

print("\n📡 Fetch événements sur 1 semaine...")

# Fetch sur plusieurs jours pour avoir plus de diversité
data = fetch_calendar_json(
    d1='2025-09-01',
    d2='2025-09-07',
    countries=None,  # TOUS les pays
    importance=None
)

print(f"✅ {len(data)} événements reçus")

# Extraire tous les pays uniques
countries = set()
for event in data:
    country = event.get('country')
    if country:
        countries.add(country)

countries_sorted = sorted(countries)

print(f"\n📍 {len(countries_sorted)} PAYS DISPONIBLES:")
print("=" * 80)

# Afficher en colonnes
for i in range(0, len(countries_sorted), 5):
    row = countries_sorted[i:i+5]
    print("  ".join(f"{c:3s}" for c in row))

print("\n" + "=" * 80)
print("PAYS PRINCIPAUX POUR EUR/USD:")
print("=" * 80)

important_for_eurusd = ['US', 'EU', 'DE', 'FR', 'IT', 'ES', 'GB', 'UK', 'CH', 'JP', 'CA', 'AU', 'NZ', 'CN']

found = []
missing = []

for country in important_for_eurusd:
    if country in countries_sorted:
        found.append(country)
    else:
        missing.append(country)

if found:
    print(f"\n✅ PRÉSENTS ({len(found)}):")
    print("  " + ", ".join(found))

if missing:
    print(f"\n❌ MANQUANTS ({len(missing)}):")
    print("  " + ", ".join(missing))

print("\n" + "=" * 80)
print("NOTE IMPORTANTE")
print("=" * 80)

print(f"""
OBSERVATION CRITIQUE:
- Avec filtre countries: {len(data)} événements
- L'API EODHD semble avoir une LIMITE de 50 événements par requête

PROBLÈME:
- Sur le 11 septembre 2025, il y a probablement 100+ événements
- Mais l'API ne retourne que les 50 premiers
- C'est pourquoi on manque des événements critiques (CPI US, etc.)

SOLUTIONS POSSIBLES:
1. Requêtes par pays individuellement (1 requête par pays)
2. Requêtes par plage horaire (diviser la journée)
3. Contacter EODHD pour augmenter la limite
4. Changer de fournisseur de données

RECOMMANDATION:
Importer pays par pays pour contourner la limite.
""")
