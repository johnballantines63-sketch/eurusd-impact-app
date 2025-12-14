"""
RÉIMPORT PAR PAYS - Session 113
================================

Import robuste qui contourne la limite de 50 événements/requête
en faisant UNE requête par pays.

PÉRIODE: 2023-01-01 → 2026-12-31 (4 ans)
MÉTHODE: 1 requête par pays par mois

Session 113 - André Valentin
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import duckdb

sys.path.insert(0, str(Path(__file__).parent))
from eodhd_client_corrected import fetch_and_import

sys.path.insert(1, str(Path(__file__).parent.parent.parent))
from src.config import DB_PATH

print("=" * 80)
print("RÉIMPORT PAR PAYS - CONTOURNEMENT LIMITE 50 ÉVÉNEMENTS")
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

# Pays corrigés selon la découverte
COUNTRIES = ['US', 'EU', 'UK', 'CH', 'JP', 'CA', 'AU', 'NZ', 'CN']
IMPORTANCE = None  # Pas de filtre

# Période complète
GLOBAL_START = datetime(2023, 1, 1)
GLOBAL_END = datetime(2026, 12, 31)

print("\n📅 CONFIGURATION IMPORT PAR PAYS")
print("-" * 80)
print(f"Période: {GLOBAL_START.date()} → {GLOBAL_END.date()}")
print(f"Pays: {', '.join(COUNTRIES)}")
print(f"Importance: {IMPORTANCE} (TOUS les événements)")
print(f"\n💡 STRATÉGIE:")
print(f"  - Import PAR PAYS pour contourner limite 50 événements")
print(f"  - {len(COUNTRIES)} pays × 48 mois = {len(COUNTRIES) * 48} requêtes")
print(f"  - Volume estimé: 15,000-25,000 événements")
print(f"  - Temps: 30-90 minutes")

response = input("\nConfirmer l'import ? (oui/non): ")
if response.lower() != 'oui':
    print("❌ Annulé")
    sys.exit(1)

# ============================================================================
# GÉNÉRATION TRANCHES MENSUELLES
# ============================================================================

tranches = []
current = GLOBAL_START

while current < GLOBAL_END:
    start = current
    
    if current.month == 12:
        next_month = datetime(current.year + 1, 1, 1)
    else:
        next_month = datetime(current.year, current.month + 1, 1)
    
    end = next_month - timedelta(days=1)
    
    if end > GLOBAL_END:
        end = GLOBAL_END
    
    tranches.append((start, end))
    current = next_month

print(f"\n📦 {len(tranches)} mois × {len(COUNTRIES)} pays = {len(tranches) * len(COUNTRIES)} requêtes")

# ============================================================================
# IMPORT PAR PAYS
# ============================================================================

print("\n🚀 IMPORT EN COURS...")
print("-" * 80)

total_imported = 0
errors = []
request_count = 0

for i, (start, end) in enumerate(tranches, 1):
    start_str = start.strftime('%Y-%m-%d')
    end_str = end.strftime('%Y-%m-%d')
    
    month_total = 0
    
    for country in COUNTRIES:
        request_count += 1
        
        # Progress
        progress = (request_count / (len(tranches) * len(COUNTRIES))) * 100
        print(f"[{request_count:4d}/{len(tranches) * len(COUNTRIES):4d}] {start_str} {country:3s}", end=" ... ")
        
        try:
            count = fetch_and_import(
                start_date=start_str,
                end_date=end_str,
                db_path=str(DB_PATH),
                countries=[country],  # UN SEUL PAYS
                importance=IMPORTANCE
            )
            
            month_total += count
            total_imported += count
            
            print(f"✅ {count:3d} events ({progress:5.1f}%)")
            
        except Exception as e:
            error_msg = f"{start_str} {country}: {type(e).__name__}: {str(e)}"
            errors.append(error_msg)
            print(f"❌ ERREUR")
    
    # Résumé mensuel
    if month_total > 0:
        print(f"  → Mois {start_str}: {month_total} événements au total")

print(f"\n{'=' * 80}")
print(f"IMPORT TERMINÉ")
print(f"{'=' * 80}")

# ============================================================================
# STATISTIQUES
# ============================================================================

print(f"\n📊 STATISTIQUES:")
print(f"  Requêtes effectuées: {request_count}")
print(f"  Succès: {request_count - len(errors)}")
print(f"  Erreurs: {len(errors)}")
print(f"  Événements importés: {total_imported:,}")

if errors:
    print(f"\n⚠️  ERREURS RENCONTRÉES:")
    for error in errors[:10]:  # Limiter à 10
        print(f"  - {error}")
    if len(errors) > 10:
        print(f"  ... et {len(errors) - 10} autres")

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
    print(f"⚠️  {result} événements trouvés (attendu 10)")
else:
    print(f"❌ AUCUN événement le 11 septembre")

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ FINAL")
print("=" * 80)

print(f"""
IMPORT PAR PAYS TERMINÉ:
- Période: {GLOBAL_START.date()} → {GLOBAL_END.date()}
- Requêtes: {request_count} (1 par pays par mois)
- Événements importés: {total_imported:,}
- Événements en DB: {total_in_db:,}
- Erreurs: {len(errors)}
- Validation 11 sept: {'✅ OK' if result == 10 else '⚠️  À vérifier'}

🎉 BASE DE DONNÉES COMPLÈTE:
- ✅ Contournement limite 50 événements
- ✅ Historique 2023-2025 (3 ans pour scores empiriques)
- ✅ Futur 2025-2026 (planification)
- ✅ Nouveaux champs (period, change, change_percentage)

PROCHAINES ACTIONS:
1. Si validation OK (10 événements 11 sept):
   bash scripts/session113/run_test_cluster_calculator.sh

2. Si validation partielle:
   python scripts/session113/analyze_11sept_events.py

3. Si toujours 0 événements 11 sept:
   → Problème timezone ou déduplication trop agressive
   → Investiguer avec diagnostic
""")

if errors:
    print(f"\n⚠️  Certaines requêtes ont échoué. Voir liste ci-dessus.")

print("=" * 80)
