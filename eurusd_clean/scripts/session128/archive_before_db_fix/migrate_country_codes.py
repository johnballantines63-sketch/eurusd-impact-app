#!/usr/bin/env python3
"""
MIGRATION DB : Normalisation codes pays economic_events

PROBLÈME :
- Codes minuscules (usd, eur, cad)
- Zone euro fragmentée (eur, de, fr, it, es)
- UK = uk au lieu de GBP

SOLUTION :
- Normaliser en ISO 4217 (codes devises majuscules)
- Regrouper zone euro sous EUR
- Standardiser UK → GBP

BACKUP AUTOMATIQUE AVANT MIGRATION
"""
import duckdb
from pathlib import Path
import shutil
from datetime import datetime

# Chemins
db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
backup_dir = Path(__file__).parents[2] / "data" / "backups"
backup_dir.mkdir(exist_ok=True)

# Mapping normalisation (Option C : Codes PAYS ISO 3166)
COUNTRY_MAPPING = {
    # Devises principales → Codes PAYS
    'usd': 'US',
    'gbp': 'GB',
    'jpy': 'JP',
    'cad': 'CA',
    'aud': 'AU',
    'chf': 'CH',
    'nzd': 'NZ',
    
    # UK
    'uk': 'GB',
    
    # Zone Euro BCE (événements globaux)
    'eur': 'EU',
    
    # Pays zone euro (événements nationaux) - Déjà codes pays corrects, juste MAJUSCULES
    # de → DE, fr → FR, it → IT, etc. (géré par UPPER() automatique)
    
    # Autres codes minuscules → MAJUSCULES via UPPER()
    # cn → CN, in → IN, br → BR, etc.
}

def backup_database():
    """Créer backup avant migration"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"warehouse_before_country_migration_{timestamp}.duckdb"
    
    print("📦 BACKUP DATABASE...")
    print(f"   Source : {db_path}")
    print(f"   Backup : {backup_path}")
    
    shutil.copy2(db_path, backup_path)
    
    print(f"✅ Backup créé : {backup_path.name}")
    print()
    
    return backup_path


def analyze_migration():
    """Analyser impact migration"""
    conn = duckdb.connect(str(db_path), read_only=True)
    
    print("🔍 ANALYSE IMPACT MIGRATION")
    print("=" * 80)
    print()
    
    # Statistiques actuelles
    stats = conn.execute("""
        SELECT 
            country,
            COUNT(*) as count,
            COUNT(DISTINCT event_name) as unique_events
        FROM economic_events
        GROUP BY country
        ORDER BY count DESC
    """).df()
    
    # Calculer nouvelles valeurs
    stats['country_new'] = stats['country'].map(lambda x: COUNTRY_MAPPING.get(x, x.upper()))
    
    # Grouper par nouveau code
    migration_summary = stats.groupby('country_new').agg({
        'count': 'sum',
        'unique_events': 'sum',
        'country': lambda x: ', '.join(sorted(set(x)))
    }).reset_index()
    migration_summary.columns = ['new_code', 'total_events', 'total_unique_events', 'old_codes']
    migration_summary = migration_summary.sort_values('total_events', ascending=False)
    
    print("TOP 15 après migration :")
    print(migration_summary.head(15).to_string(index=False))
    print()
    
    # Codes non mappés
    unmapped = stats[~stats['country'].isin(COUNTRY_MAPPING.keys()) & 
                     (stats['country'] != stats['country'].str.upper())]
    
    if len(unmapped) > 0:
        print(f"⚠️  {len(unmapped)} codes NON MAPPÉS (garderont code actuel en MAJUSCULES) :")
        print(unmapped[['country', 'count']].head(20).to_string(index=False))
        print()
    
    conn.close()
    
    return migration_summary


def migrate_database():
    """Exécuter migration"""
    conn = duckdb.connect(str(db_path))
    
    print("🚀 EXÉCUTION MIGRATION")
    print("=" * 80)
    print()
    
    # Compter événements avant
    count_before = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"Événements avant : {count_before:,}")
    
    # Construire requête UPDATE avec CASE
    case_statements = []
    for old_code, new_code in COUNTRY_MAPPING.items():
        case_statements.append(f"WHEN country = '{old_code}' THEN '{new_code}'")
    
    # Ajouter clause pour codes non mappés (mise en majuscules)
    case_clause = '\n        '.join(case_statements)
    
    update_query = f"""
    UPDATE economic_events
    SET country = CASE
        {case_clause}
        ELSE UPPER(country)
    END
    """
    
    print("Exécution UPDATE...")
    conn.execute(update_query)
    
    # Compter après
    count_after = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"Événements après  : {count_after:,}")
    
    if count_before != count_after:
        print("❌ ERREUR : Nombre événements différent !")
        conn.rollback()
        conn.close()
        return False
    
    # Vérifier nouveaux codes
    new_codes = conn.execute("""
        SELECT DISTINCT country, COUNT(*) as count
        FROM economic_events
        GROUP BY country
        ORDER BY count DESC
        LIMIT 20
    """).df()
    
    print()
    print("✅ Nouveaux codes (TOP 20) :")
    print(new_codes.to_string(index=False))
    
    conn.close()
    return True


def main():
    """Pipeline complet"""
    print("=" * 80)
    print("MIGRATION CODES PAYS - economic_events")
    print("=" * 80)
    print()
    
    # Étape 1 : Backup
    backup_path = backup_database()
    
    # Étape 2 : Analyse
    summary = analyze_migration()
    
    # Étape 3 : Confirmation
    print()
    print("⚠️  CETTE OPÉRATION VA MODIFIER LA BASE DE DONNÉES")
    print(f"   Backup disponible : {backup_path.name}")
    print()
    response = input("Continuer avec la migration ? (oui/non) : ").strip().lower()
    
    if response not in ['oui', 'o', 'yes', 'y']:
        print("❌ Migration annulée")
        return 1
    
    print()
    
    # Étape 4 : Migration
    success = migrate_database()
    
    if success:
        print()
        print("=" * 80)
        print("✅✅✅ MIGRATION RÉUSSIE")
        print("=" * 80)
        print()
        print("Changements principaux :")
        print("  • usd → US (code pays ISO 3166)")
        print("  • eur → EU (zone euro BCE)")
        print("  • uk → GB (code pays ISO 3166)")
        print("  • de, fr, it, es → DE, FR, IT, ES (codes pays maintenus)")
        print("  • Tous codes en MAJUSCULES (ISO 3166)")
        print()
        print(f"📦 Backup : {backup_path}")
        return 0
    else:
        print()
        print("❌ Migration échouée")
        print(f"Restaurer backup : {backup_path}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
