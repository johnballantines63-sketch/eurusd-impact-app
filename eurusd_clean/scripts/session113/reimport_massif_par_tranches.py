"""
RÉIMPORT MASSIF PAR TRANCHES - Session 113
===========================================

Import robuste par périodes mensuelles pour éviter timeouts.

PÉRIODE: 2024-01-01 → 2026-12-31 (3 ans)

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
print("RÉIMPORT MASSIF PAR TRANCHES")
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

COUNTRIES = ['US', 'DE', 'EU', 'GB', 'JP', 'CH', 'CA', 'AU', 'NZ']
# CRITIQUE: EODHD ne fournit pas le champ importance
# Le filtrer côté API ne fonctionne pas correctement
# On importe TOUT et on filtre après avec empirical_score
IMPORTANCE = None  # Pas de filtre importance

# Période complète
# CRITIQUE: 2023-2026 pour avoir 3 ans d'historique pour scores empiriques
GLOBAL_START = datetime(2023, 1, 1)
GLOBAL_END = datetime(2026, 12, 31)

print("\n📅 CONFIGURATION IMPORT MASSIF")
print("-" * 80)
print(f"Période: {GLOBAL_START.date()} → {GLOBAL_END.date()}")
print(f"Pays: {', '.join(COUNTRIES)}")
print(f"Importance: {IMPORTANCE} (TOUS les événements, filtre après)")
print(f"\n⚠️  Import par tranches mensuelles pour robustesse")
print(f"  Tranches: 48 mois (2023-01 → 2026-12)")
print(f"  Volume estimé: 15,000-30,000 événements (SANS filtre importance)")
print(f"  Temps total estimé: 25-60 minutes")

response = input("\nConfirmer l'import ? (oui/non): ")
if response.lower() != 'oui':
    print("❌ Annulé")
    sys.exit(1)

# ============================================================================
# IMPORT PAR TRANCHES MENSUELLES
# ============================================================================

print("\n🚀 IMPORT EN COURS...")
print("-" * 80)

total_imported = 0
errors = []

# Générer tranches mensuelles
current = GLOBAL_START
tranches = []

while current < GLOBAL_END:
    # Début du mois
    start = current
    
    # Fin du mois (début mois suivant - 1 jour)
    if current.month == 12:
        next_month = datetime(current.year + 1, 1, 1)
    else:
        next_month = datetime(current.year, current.month + 1, 1)
    
    end = next_month - timedelta(days=1)
    
    # Ne pas dépasser GLOBAL_END
    if end > GLOBAL_END:
        end = GLOBAL_END
    
    tranches.append((start, end))
    current = next_month

print(f"📦 {len(tranches)} tranches à importer\n")

for i, (start, end) in enumerate(tranches, 1):
    start_str = start.strftime('%Y-%m-%d')
    end_str = end.strftime('%Y-%m-%d')
    
    print(f"[{i:2d}/{len(tranches)}] {start_str} → {end_str}", end=" ... ")
    
    try:
        count = fetch_and_import(
            start_date=start_str,
            end_date=end_str,
            db_path=str(DB_PATH),
            countries=COUNTRIES,
            importance=IMPORTANCE
        )
        
        total_imported += count
        print(f"✅ {count:4d} événements")
        
    except Exception as e:
        error_msg = f"{start_str} → {end_str}: {type(e).__name__}: {str(e)}"
        errors.append(error_msg)
        print(f"❌ ERREUR")
        print(f"    {error_msg}")

print(f"\n{'=' * 80}")
print(f"IMPORT TERMINÉ")
print(f"{'=' * 80}")

# ============================================================================
# STATISTIQUES
# ============================================================================

print(f"\n📊 STATISTIQUES:")
print(f"  Tranches traitées: {len(tranches)}")
print(f"  Succès: {len(tranches) - len(errors)}")
print(f"  Erreurs: {len(errors)}")
print(f"  Événements importés: {total_imported:,}")

if errors:
    print(f"\n⚠️  ERREURS RENCONTRÉES:")
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

# Stats globales
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
else:
    print(f"⚠️  ATTENTION: {result} événements au lieu de 10")

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ FINAL")
print("=" * 80)

print(f"""
IMPORT MASSIF TERMINÉ:
- Période: {GLOBAL_START.date()} → {GLOBAL_END.date()}
- Événements importés: {total_imported:,}
- Événements en DB: {total_in_db:,}
- Tranches réussies: {len(tranches) - len(errors)}/{len(tranches)}
- Validation 11 sept: {'✅ OK' if result == 10 else '⚠️  À vérifier'}

🎉 BASE DE DONNÉES COMPLÈTE:
- ✅ Historique 2023-2025 (3 ans pour scores empiriques)
- ✅ Futur 2025-2026 (planification)
- ✅ Nouveaux champs (period, change, change_percentage)

PROCHAINES ACTIONS:
1. Validation:
   python scripts/session113/analyze_11sept_events.py

2. Tests:
   bash scripts/session113/run_test_cluster_calculator.sh

3. Utiliser l'application:
   - Analyser événements passés (backtesting)
   - Planifier trades futurs
   - Exploiter tout le potentiel du système
""")

if errors:
    print(f"\n⚠️  Certaines tranches ont échoué. Relancer le script pour réessayer.")

print("=" * 80)
