"""
RÉIMPORT PROPRE - Session 113
==============================

Utilise eodhd_client_corrected.py pour importer proprement.

IMPORTANTE: Exécuter APRÈS clean_and_prepare_reimport.py

Session 113 - André Valentin
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from eodhd_client_corrected import fetch_and_import

sys.path.insert(1, str(Path(__file__).parent.parent.parent))
from src.config import DB_PATH

print("=" * 80)
print("RÉIMPORT PROPRE EODHD")
print("=" * 80)

print("\n⚠️  PRÉREQUIS:")
print("  1. Table events doit être vide")
print("  2. Variable EODHD_API_KEY doit être définie")
print("  3. Sauvegarde DB faite")

response = input("\nPrérequis OK ? (oui/non): ")
if response.lower() != 'oui':
    print("❌ Annulé")
    sys.exit(1)

# ============================================================================
# CONFIGURATION IMPORT
# ============================================================================

print("\n📥 CONFIGURATION IMPORT")
print("-" * 80)

# Période à importer
# CRITIQUE: Importer 2023-2026 pour avoir 3 ans d'historique pour scores empiriques
START_DATE = "2023-01-01"  # Historique 2023-2025
END_DATE = "2026-12-31"    # Futur jusqu'à fin 2026

# Pays
COUNTRIES = ['US', 'DE', 'EU', 'GB', 'JP', 'CH', 'CA', 'AU', 'NZ']

# Importance - CRITIQUE: EODHD ne fournit pas ce champ
# Le filtrer côté API retourne des résultats incorrects
# On importe TOUT et on filtre après avec empirical_score
IMPORTANCE = None  # Pas de filtre

print(f"Période: {START_DATE} → {END_DATE}")
print(f"Pays: {', '.join(COUNTRIES)}")
print(f"Importance: {IMPORTANCE} (TOUS les événements, filtre après)")
print(f"\n⚠️  IMPORT MASSIF:")
print(f"  Durée: ~4 ans (historique 3 ans + futur)")
print(f"  Volume estimé: 15,000-30,000 événements (SANS filtre importance)")
print(f"  Temps: 20-60 minutes selon connexion")
print(f"  Espace: ~30-50 MB")

response = input("\nConfirmer l'import ? (oui/non): ")
if response.lower() != 'oui':
    print("❌ Annulé")
    sys.exit(1)

# ============================================================================
# IMPORT
# ============================================================================

print("\n🚀 IMPORT EN COURS...")
print("-" * 80)

try:
    count = fetch_and_import(
        start_date=START_DATE,
        end_date=END_DATE,
        db_path=str(DB_PATH),
        countries=COUNTRIES,
        importance=IMPORTANCE
    )
    
    print(f"\n✅ SUCCÈS: {count} événements importés")

except Exception as e:
    print(f"\n❌ ERREUR: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# VALIDATION 11 SEPTEMBRE
# ============================================================================

print("\n📊 VALIDATION 11 SEPTEMBRE")
print("-" * 80)

import duckdb

conn = duckdb.connect(str(DB_PATH), read_only=True)

result = conn.execute("""
    SELECT COUNT(*) FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+02:00'
        AND ts_utc < '2025-09-11 15:00:00+02:00'
""").fetchone()[0]

conn.close()

print(f"Événements 11 sept: {result}")
print(f"Attendu: 10 événements")

if result == 10:
    print("✅ SUCCÈS: Nombre correct !")
else:
    print(f"⚠️  ATTENTION: {result} événements au lieu de 10")
    print("   Vérifier avec: python scripts/session113/analyze_11sept_events.py")

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)

print(f"""
STATUT IMPORT:
- Période importée: {START_DATE} → {END_DATE}
- Événements total: {count:,}
- Événements 11 sept: {result}
- Validation: {'✅ OK' if result == 10 else '⚠️  À vérifier'}

🎉 IMPORT COMPLET:
- Historique 2023-2025: ✅ Importé (3 ans pour scores empiriques)
- Futur 2025-2026: ✅ Importé
- Prêt pour backtesting ET planification

PROCHAINES ACTIONS:
1. Si validation OK:
   bash scripts/session113/run_test_cluster_calculator.sh

2. Si validation échoue:
   python scripts/session113/analyze_11sept_events.py
   (Vérifier les doublons restants)

3. Utiliser l'app:
   - Analyser n'importe quelle date 2024-2026
   - Planifier trades sur événements futurs
   - Backtester stratégies sur historique
""")

print("=" * 80)
