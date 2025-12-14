"""
CLASSIFICATION ÉVÉNEMENTS - Session 113
========================================

Post-traitement après import EODHD :
1. Classifier les événements selon event_families.py
2. Remplir importance_n selon FAMILY_IMPORTANCE
3. Calculer empirical_score sur historique 3 ans

Session 113 - André Valentin
"""
import sys
from pathlib import Path
import re
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import DB_PATH
from src.core.event_families import (
    FAMILY_PATTERNS, 
    FAMILY_IMPORTANCE,
    FAMILY_SENSITIVITIES
)

print("=" * 80)
print("CLASSIFICATION ÉVÉNEMENTS")
print("=" * 80)

conn = duckdb.connect(str(DB_PATH))

# Compter événements
total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
with_importance = conn.execute("SELECT COUNT(*) FROM events WHERE importance_n IS NOT NULL").fetchone()[0]
without_importance = total - with_importance

print(f"\n📊 ÉTAT ACTUEL:")
print(f"  Total événements: {total:,}")
print(f"  Avec importance_n: {with_importance:,}")
print(f"  Sans importance_n: {without_importance:,}")

if without_importance == 0:
    print("\n✅ Tous les événements ont déjà importance_n")
    response = input("\nReclassifier quand même ? (oui/non): ")
    if response.lower() != 'oui':
        print("❌ Annulé")
        conn.close()
        sys.exit(0)

print(f"\n🔄 CLASSIFICATION EN COURS...")
print("-" * 80)

# Charger tous les événements
events = conn.execute("""
    SELECT 
        rowid,
        event_key,
        type,
        country,
        importance_n
    FROM events
""").fetchdf()

print(f"📦 {len(events):,} événements à classifier")

# Statistiques
stats = {
    'classified': 0,
    'unclassified': 0,
    'by_family': {},
    'by_importance': {1: 0, 2: 0, 3: 0}
}

# Classifier chaque événement
for idx, row in events.iterrows():
    rowid = row['rowid']
    event_key = row['event_key'] or ''
    event_type = row['type'] or ''
    
    # Chercher la famille qui match
    matched_family = None
    matched_importance = None
    
    for family_name, pattern in FAMILY_PATTERNS.items():
        # Tester event_key et type
        if re.search(pattern, event_key, re.IGNORECASE) or \
           re.search(pattern, event_type, re.IGNORECASE):
            matched_family = family_name
            matched_importance = FAMILY_IMPORTANCE.get(family_name, 2)
            break
    
    if matched_family:
        # Mettre à jour importance_n
        conn.execute("""
            UPDATE events
            SET importance_n = ?
            WHERE rowid = ?
        """, [matched_importance, rowid])
        
        stats['classified'] += 1
        stats['by_family'][matched_family] = stats['by_family'].get(matched_family, 0) + 1
        stats['by_importance'][matched_importance] += 1
    else:
        # Assigner importance moyenne par défaut
        conn.execute("""
            UPDATE events
            SET importance_n = 2
            WHERE rowid = ?
        """, [rowid])
        
        stats['unclassified'] += 1
        stats['by_importance'][2] += 1
    
    # Progress tous les 1000
    if (idx + 1) % 1000 == 0:
        progress = ((idx + 1) / len(events)) * 100
        print(f"  Progress: {progress:5.1f}% ({idx + 1:,}/{len(events):,})")

print(f"\n✅ Classification terminée")

# Vérification
final_with_importance = conn.execute("SELECT COUNT(*) FROM events WHERE importance_n IS NOT NULL").fetchone()[0]
final_without_importance = total - final_with_importance

conn.close()

# Afficher statistiques
print("\n" + "=" * 80)
print("RÉSULTATS")
print("=" * 80)

print(f"\n📊 AVANT:")
print(f"  Avec importance_n: {with_importance:,}")
print(f"  Sans importance_n: {without_importance:,}")

print(f"\n📊 APRÈS:")
print(f"  Avec importance_n: {final_with_importance:,}")
print(f"  Sans importance_n: {final_without_importance:,}")

print(f"\n🎯 CLASSIFICATION:")
print(f"  Classifiés (famille trouvée): {stats['classified']:,}")
print(f"  Non classifiés (défaut): {stats['unclassified']:,}")

print(f"\n📈 PAR IMPORTANCE:")
for level in [3, 2, 1]:
    count = stats['by_importance'][level]
    pct = (count / total) * 100 if total > 0 else 0
    level_name = {3: 'HIGH', 2: 'MEDIUM', 1: 'LOW'}[level]
    print(f"  {level} ({level_name:6s}): {count:6,} ({pct:5.1f}%)")

print(f"\n📋 TOP 10 FAMILLES:")
top_families = sorted(stats['by_family'].items(), key=lambda x: x[1], reverse=True)[:10]
for family, count in top_families:
    imp = FAMILY_IMPORTANCE.get(family, 2)
    print(f"  {family:30s}: {count:5,} événements (importance={imp})")

print("\n" + "=" * 80)
print("PROCHAINES ÉTAPES")
print("=" * 80)

print("""
✅ CLASSIFICATION TERMINÉE

RÉSULTAT:
- Tous les événements ont importance_n rempli
- Classification basée sur event_families.py
- Événements non reconnus → importance 2 (MEDIUM)

PROCHAINES ACTIONS:
1. Calculer empirical_score (historique 3 ans):
   python scripts/session113/calculate_empirical_scores.py

2. Valider les données:
   python scripts/session113/analyze_11sept_events.py

3. Lancer les tests:
   bash scripts/session113/run_test_cluster_calculator.sh
""")

print("=" * 80)
