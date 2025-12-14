"""
RÉIMPORT SIMPLE PAR PAYS - Session 113
=======================================

Test : 1 requête par pays pour TOUTE la période 2023-2026.

Si limite 50 = globale → on aura 50 events/pays = 450 total
Si limite 50 = par jour → on aura 15,000+ events

Session 113 - André Valentin
"""
import sys
from pathlib import Path
from datetime import datetime
import duckdb

sys.path.insert(0, str(Path(__file__).parent))
from eodhd_client_corrected import fetch_and_import

sys.path.insert(1, str(Path(__file__).parent.parent.parent))
from src.config import DB_PATH

print("=" * 80)
print("RÉIMPORT SIMPLE - 1 REQUÊTE PAR PAYS")
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
# CONFIGURATION
# ============================================================================

# Pays disponibles dans EODHD
COUNTRIES = ['US', 'EU', 'UK', 'CH', 'JP', 'CA', 'AU', 'NZ']
IMPORTANCE = None

# Période complète
START_DATE = "2023-01-01"
END_DATE = "2026-12-31"

print("\n📅 CONFIGURATION")
print("-" * 80)
print(f"Période: {START_DATE} → {END_DATE}")
print(f"Pays: {', '.join(COUNTRIES)}")
print(f"Importance: {IMPORTANCE}")
print(f"\n💡 TEST:")
print(f"  - 1 seule requête par pays pour toute la période")
print(f"  - {len(COUNTRIES)} requêtes au total")
print(f"  - Si limite 50/requête → 50 × {len(COUNTRIES)} = {50 * len(COUNTRIES)} événements")
print(f"  - Si pas de limite → 15,000-25,000 événements")
print(f"  - Temps: 2-5 minutes")

response = input("\nConfirmer l'import ? (oui/non): ")
if response.lower() != 'oui':
    print("❌ Annulé")
    sys.exit(1)

# ============================================================================
# IMPORT PAR PAYS
# ============================================================================

print("\n🚀 IMPORT EN COURS...")
print("-" * 80)

total_imported = 0
errors = []

for i, country in enumerate(COUNTRIES, 1):
    print(f"[{i}/{len(COUNTRIES)}] {country:3s} ({START_DATE} → {END_DATE})", end=" ... ")
    
    try:
        count = fetch_and_import(
            start_date=START_DATE,
            end_date=END_DATE,
            db_path=str(DB_PATH),
            countries=[country],
            importance=IMPORTANCE
        )
        
        total_imported += count
        print(f"✅ {count:5,} événements")
        
        # Analyser si limite atteinte
        if count == 50:
            print(f"    ⚠️  Exactement 50 = LIMITE ATTEINTE")
        
    except Exception as e:
        error_msg = f"{country}: {type(e).__name__}: {str(e)}"
        errors.append(error_msg)
        print(f"❌ ERREUR: {error_msg}")

print(f"\n{'=' * 80}")
print(f"IMPORT TERMINÉ")
print(f"{'=' * 80}")

# ============================================================================
# ANALYSE
# ============================================================================

print(f"\n📊 STATISTIQUES:")
print(f"  Pays traités: {len(COUNTRIES)}")
print(f"  Succès: {len(COUNTRIES) - len(errors)}")
print(f"  Erreurs: {len(errors)}")
print(f"  Événements importés: {total_imported:,}")

# Calculs
avg_per_country = total_imported / len(COUNTRIES) if COUNTRIES else 0
expected_minimum = 15000

print(f"\n🔍 ANALYSE:")
print(f"  Moyenne par pays: {avg_per_country:.0f} événements")

if total_imported < 500:
    print(f"\n❌ LIMITE 50 CONFIRMÉE")
    print(f"  → Chaque pays renvoie ~50 événements max")
    print(f"  → Il faut segmenter par MOIS")
    print(f"  → Utiliser: python scripts/session113/reimport_par_pays.py")
elif total_imported < expected_minimum:
    print(f"\n⚠️  VOLUME FAIBLE ({total_imported:,} < {expected_minimum:,})")
    print(f"  → Possible limite par période")
    print(f"  → Recommandé de segmenter par MOIS")
else:
    print(f"\n✅ VOLUME CORRECT ({total_imported:,} événements)")
    print(f"  → Pas de limite stricte détectée")

if errors:
    print(f"\n⚠️  ERREURS:")
    for error in errors:
        print(f"  - {error}")

# ============================================================================
# VALIDATION 11 SEPTEMBRE
# ============================================================================

print("\n" + "=" * 80)
print("VALIDATION 11 SEPTEMBRE")
print("=" * 80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

result = conn.execute("""
    SELECT COUNT(*) FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+02:00'
        AND ts_utc < '2025-09-11 15:00:00+02:00'
""").fetchone()[0]

total_in_db = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

# Stats par année
stats_2023 = conn.execute("SELECT COUNT(*) FROM events WHERE date_part('year', ts_utc) = 2023").fetchone()[0]
stats_2024 = conn.execute("SELECT COUNT(*) FROM events WHERE date_part('year', ts_utc) = 2024").fetchone()[0]
stats_2025 = conn.execute("SELECT COUNT(*) FROM events WHERE date_part('year', ts_utc) = 2025").fetchone()[0]
stats_2026 = conn.execute("SELECT COUNT(*) FROM events WHERE date_part('year', ts_utc) = 2026").fetchone()[0]

conn.close()

print(f"\nÉvénements en DB: {total_in_db:,}")
print(f"  2023: {stats_2023:,}")
print(f"  2024: {stats_2024:,}")
print(f"  2025: {stats_2025:,}")
print(f"  2026: {stats_2026:,}")

print(f"\nValidation 11 sept: {result} événements")
print(f"Attendu: 10 événements")

if result == 10:
    print("✅ SUCCÈS: Nombre correct !")
elif result > 0:
    print(f"⚠️  {result} événements (attendu 10)")
else:
    print(f"❌ AUCUN événement")

# ============================================================================
# CONCLUSION
# ============================================================================

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if total_imported < 500:
    print(f"""
❌ TEST ÉCHOUÉ - LIMITE 50 CONFIRMÉE

PROBLÈME:
- Seulement {total_imported} événements pour 4 ans × {len(COUNTRIES)} pays
- Chaque requête retourne max 50 événements
- La période longue ne change rien

SOLUTION:
python scripts/session113/reimport_par_pays.py
(Import par MOIS pour contourner la limite)
""")
elif result == 10:
    print(f"""
✅ TEST RÉUSSI !

SUCCÈS:
- {total_in_db:,} événements importés
- 11 septembre validé (10 événements)
- Base de données prête

PROCHAINES ACTIONS:
bash scripts/session113/run_test_cluster_calculator.sh
""")
else:
    print(f"""
⚠️  TEST PARTIEL

RÉSULTAT:
- {total_in_db:,} événements importés
- 11 septembre: {result} événements (attendu 10)

ACTIONS:
1. Analyser: python scripts/session113/analyze_11sept_events.py
2. Si besoin, segmenter par mois
""")

print("=" * 80)
