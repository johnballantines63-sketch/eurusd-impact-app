"""
RÉIMPORT PAR JOUR - Session 113
================================

Import COMPLET par JOUR pour garantir 100% des événements.

SÉCURITÉ MAXIMALE:
- 1 requête par pays par jour
- Contourne la limite de 50 événements/jour
- Capture TOUS les événements même les jours chargés (CPI, NFP, etc.)

VOLUME:
- 2023-2026 = ~1,461 jours
- 8 pays × 1,461 jours = ~11,688 requêtes
- Temps estimé: 40-90 minutes selon connexion

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
print("RÉIMPORT PAR JOUR - SÉCURITÉ MAXIMALE")
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
GLOBAL_START = datetime(2023, 1, 1)
GLOBAL_END = datetime(2026, 12, 31)

# Calculer nombre de jours
days_count = (GLOBAL_END - GLOBAL_START).days + 1
total_requests = days_count * len(COUNTRIES)

print("\n📅 CONFIGURATION IMPORT PAR JOUR")
print("-" * 80)
print(f"Période: {GLOBAL_START.date()} → {GLOBAL_END.date()}")
print(f"Pays: {', '.join(COUNTRIES)}")
print(f"Importance: {IMPORTANCE} (TOUS les événements)")
print(f"\n💡 STRATÉGIE SÉCURISÉE:")
print(f"  - Import PAR JOUR pour garantir capture complète")
print(f"  - {days_count:,} jours × {len(COUNTRIES)} pays = {total_requests:,} requêtes")
print(f"  - Volume estimé: 15,000-25,000 événements")
print(f"  - Temps: 40-90 minutes selon connexion")

response = input("\nConfirmer l'import ? (oui/non): ")
if response.lower() != 'oui':
    print("❌ Annulé")
    sys.exit(1)

# ============================================================================
# IMPORT PAR JOUR
# ============================================================================

print("\n🚀 IMPORT EN COURS...")
print("-" * 80)

total_imported = 0
errors = []
request_count = 0

# Générer tous les jours
current_date = GLOBAL_START

while current_date <= GLOBAL_END:
    date_str = current_date.strftime('%Y-%m-%d')
    
    # Import pour chaque pays ce jour-là
    for country in COUNTRIES:
        request_count += 1
        
        # Progress tous les 100 requêtes
        if request_count % 100 == 0 or request_count == 1:
            progress = (request_count / total_requests) * 100
            print(f"\n[{request_count:5d}/{total_requests:5d}] Progress: {progress:5.1f}% - {date_str}")
        
        try:
            count = fetch_and_import(
                start_date=date_str,
                end_date=date_str,
                db_path=str(DB_PATH),
                countries=[country],
                importance=IMPORTANCE
            )
            
            total_imported += count
            
            # Afficher seulement si événements trouvés
            if count > 0:
                print(f"  {date_str} {country:3s}: {count:3d} events")
            
        except Exception as e:
            error_msg = f"{date_str} {country}: {type(e).__name__}: {str(e)}"
            errors.append(error_msg)
            if len(errors) <= 10:  # Limiter affichage erreurs
                print(f"  {date_str} {country:3s}: ❌ ERREUR")
    
    current_date += timedelta(days=1)

print(f"\n{'=' * 80}")
print(f"IMPORT TERMINÉ")
print(f"{'=' * 80}")

# ============================================================================
# STATISTIQUES
# ============================================================================

print(f"\n📊 STATISTIQUES:")
print(f"  Requêtes effectuées: {request_count:,}")
print(f"  Succès: {request_count - len(errors):,}")
print(f"  Erreurs: {len(errors)}")
print(f"  Événements importés: {total_imported:,}")

avg_per_day = total_imported / days_count if days_count > 0 else 0
print(f"  Moyenne par jour: {avg_per_day:.1f} événements")

if errors:
    print(f"\n⚠️  ERREURS RENCONTRÉES ({len(errors)}):")
    for error in errors[:10]:
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

# Événements 11 sept 14:30
result = conn.execute("""
    SELECT COUNT(*) FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+02:00'
        AND ts_utc < '2025-09-11 15:00:00+02:00'
""").fetchone()[0]

# Tous événements 11 sept
result_full_day = conn.execute("""
    SELECT COUNT(*) FROM events
    WHERE date(ts_utc) = '2025-09-11'
""").fetchone()[0]

total_in_db = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

# Stats par année
stats_2023 = conn.execute("SELECT COUNT(*) FROM events WHERE date_part('year', ts_utc) = 2023").fetchone()[0]
stats_2024 = conn.execute("SELECT COUNT(*) FROM events WHERE date_part('year', ts_utc) = 2024").fetchone()[0]
stats_2025 = conn.execute("SELECT COUNT(*) FROM events WHERE date_part('year', ts_utc) = 2025").fetchone()[0]
stats_2026 = conn.execute("SELECT COUNT(*) FROM events WHERE date_part('year', ts_utc) = 2026").fetchone()[0]

# Top 10 événements 11 sept
top_events = conn.execute("""
    SELECT 
        ts_utc,
        country,
        event_key,
        actual,
        estimate
    FROM events
    WHERE date(ts_utc) = '2025-09-11'
    ORDER BY ts_utc
    LIMIT 10
""").fetchdf()

conn.close()

print(f"\nÉvénements en DB: {total_in_db:,}")
print(f"  2023: {stats_2023:,}")
print(f"  2024: {stats_2024:,}")
print(f"  2025: {stats_2025:,}")
print(f"  2026: {stats_2026:,}")

print(f"\n11 septembre 2025:")
print(f"  Journée complète: {result_full_day} événements")
print(f"  Plage 14:30 (CPI): {result} événements")
print(f"  Attendu 14:30: 10 événements")

if result == 10:
    print("\n✅ SUCCÈS: Validation parfaite !")
elif result > 0:
    print(f"\n⚠️  {result} événements trouvés (attendu 10)")
else:
    print(f"\n❌ AUCUN événement dans la plage horaire")

if not top_events.empty:
    print(f"\n📋 Premiers événements 11 sept:")
    print(top_events.to_string(index=False))

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ FINAL")
print("=" * 80)

print(f"""
IMPORT PAR JOUR TERMINÉ:
- Période: {GLOBAL_START.date()} → {GLOBAL_END.date()}
- Requêtes: {request_count:,} ({days_count} jours × {len(COUNTRIES)} pays)
- Événements importés: {total_imported:,}
- Événements en DB: {total_in_db:,}
- Erreurs: {len(errors)}
- Validation 11 sept: {'✅ OK' if result == 10 else '⚠️  À vérifier'}

🎉 BASE DE DONNÉES COMPLÈTE:
- ✅ Import par JOUR (sécurité maximale)
- ✅ Contournement limite 50 événements
- ✅ Historique 2023-2025 (3 ans pour scores empiriques)
- ✅ Futur 2025-2026 (planification)
- ✅ Nouveaux champs (period, change, change_percentage)

PROCHAINES ACTIONS:
1. Si validation OK (10 événements):
   bash scripts/session113/run_test_cluster_calculator.sh

2. Si validation partielle:
   python scripts/session113/analyze_11sept_events.py

3. Utiliser l'application:
   streamlit run src/app.py
""")

if errors and len(errors) < 100:
    print(f"\n⚠️  {len(errors)} requêtes ont échoué (acceptable si < 1%)")
elif errors:
    print(f"\n⚠️  {len(errors)} requêtes ont échoué - vérifier connectivité")

print("=" * 80)
