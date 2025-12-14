"""
DIAGNOSTIC CHAMPS EODHD - Session 113
======================================

Affiche les champs BRUTS retournés par EODHD pour voir
si l'importance est présente et sous quel nom.

Session 113 - André Valentin
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))
from eodhd_client_corrected import fetch_calendar_json

print("=" * 80)
print("DIAGNOSTIC CHAMPS BRUTS EODHD")
print("=" * 80)

print("\n📡 Fetch événements 11 septembre 2025...")

# Fetch brut
data = fetch_calendar_json(
    d1='2025-09-11',
    d2='2025-09-11',
    countries=['US'],
    importance=None
)

print(f"✅ {len(data)} événements reçus")

if not data:
    print("❌ Aucun événement retourné")
    sys.exit(1)

# Analyser premier événement
first = data[0]

print("\n" + "=" * 80)
print("PREMIER ÉVÉNEMENT - CHAMPS DISPONIBLES")
print("=" * 80)

print(f"\nNombre de champs: {len(first)}")
print("\nListe des champs:")
for key in sorted(first.keys()):
    value = first[key]
    # Tronquer valeurs longues
    if isinstance(value, str) and len(value) > 50:
        value = value[:50] + "..."
    print(f"  {key:25s} = {value}")

print("\n" + "=" * 80)
print("ANALYSE CHAMP IMPORTANCE")
print("=" * 80)

# Chercher tous les champs qui pourraient être l'importance
importance_candidates = []
for key in first.keys():
    key_lower = key.lower()
    if any(word in key_lower for word in ['import', 'impact', 'priority', 'level', 'weight']):
        importance_candidates.append(key)

if importance_candidates:
    print(f"\n✅ Champs candidats trouvés: {len(importance_candidates)}")
    for key in importance_candidates:
        print(f"  {key:25s} = {first[key]}")
else:
    print("\n❌ Aucun champ 'importance' détecté")

print("\n" + "=" * 80)
print("3 PREMIERS ÉVÉNEMENTS COMPLETS")
print("=" * 80)

for i, event in enumerate(data[:3], 1):
    print(f"\n--- ÉVÉNEMENT {i} ---")
    print(json.dumps(event, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("TOUS LES CHAMPS UNIQUES DANS LES 50 ÉVÉNEMENTS")
print("=" * 80)

# Collecter tous les champs de tous les événements
all_fields = set()
for event in data:
    all_fields.update(event.keys())

print(f"\nTotal champs uniques: {len(all_fields)}")
print("\nListe complète:")
for field in sorted(all_fields):
    print(f"  - {field}")

print("\n" + "=" * 80)
print("RECOMMANDATION")
print("=" * 80)

if importance_candidates:
    print(f"""
✅ Champs importance détectés: {', '.join(importance_candidates)}

ACTION:
Vérifier que eodhd_client_corrected.py extrait bien ces champs.

Dans la fonction calendar_to_events_df(), ligne ~170:
    imp_src = _col(raw, "importance", "impact", "priority", "importance_n")

Si le champ EODHD est différent, ajouter le bon nom.
""")
else:
    print("""
❌ Aucun champ importance trouvé

POSSIBILITÉS:
1. EODHD ne fournit pas l'importance pour les requêtes sans filtre
2. Le champ a un nom inattendu
3. L'importance est dans un sous-objet

Examiner les événements complets ci-dessus pour trouver le champ.
""")
