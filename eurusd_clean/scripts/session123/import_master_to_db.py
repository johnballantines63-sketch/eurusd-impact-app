"""
Import Master → DuckDB warehouse

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Double source
"""

import duckdb
import json
from pathlib import Path
from datetime import datetime

def import_master_to_db():
    """Importer events_master dans warehouse.duckdb"""
    
    print("=" * 80)
    print("IMPORT MASTER → DUCKDB WAREHOUSE")
    print("=" * 80)
    print()
    
    # Chemins
    data_dir = Path(__file__).parent.parent.parent / 'data'
    master_file = data_dir / 'master' / 'events_master_2020_2025.json'
    db_path = Path(__file__).parent.parent.parent / 'warehouse.duckdb'
    
    if not master_file.exists():
        print(f"❌ Fichier master non trouvé: {master_file}")
        return False
    
    print(f"📂 Master: {master_file}")
    print(f"📂 DB: {db_path}")
    print()
    
    # Charger master
    print("🔄 Chargement master...")
    with open(master_file, 'r') as f:
        master_events = json.load(f)
    
    print(f"   ✅ {len(master_events)} événements")
    print()
    
    # Connexion DB
    print("🔄 Connexion DB...")
    conn = duckdb.connect(str(db_path))
    print("   ✅ Connecté")
    print()
    
    # Backup table existante
    print("💾 Backup table existante...")
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'economic_events_backup_{timestamp}'
        
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {backup_name} AS 
            SELECT * FROM economic_events
        """)
        
        count = conn.execute(f"SELECT COUNT(*) FROM {backup_name}").fetchone()[0]
        print(f"   ✅ Backup créé: {backup_name} ({count} événements)")
    except Exception as e:
        print(f"   ⚠️  Pas de table existante à backup: {e}")
    print()
    
    # Drop + recréer table
    print("🔄 Recréation table economic_events...")
    
    conn.execute("DROP TABLE IF EXISTS economic_events")
    
    conn.execute("""
        CREATE TABLE economic_events (
            event_key VARCHAR PRIMARY KEY,
            event_name VARCHAR,
            event_name_original VARCHAR,
            country VARCHAR,
            datetime_utc TIMESTAMP,
            actual DOUBLE,
            forecast DOUBLE,
            previous DOUBLE,
            source VARCHAR,
            validated BOOLEAN DEFAULT FALSE,
            jblanked_actual DOUBLE,
            eodhd_actual DOUBLE,
            raw_data JSON
        )
    """)
    
    print("   ✅ Table créée")
    print()
    
    # Insert événements
    print("🔄 Import événements...")
    
    inserted = 0
    errors = 0
    
    for event in master_events:
        try:
            conn.execute("""
                INSERT INTO economic_events (
                    event_key,
                    event_name,
                    event_name_original,
                    country,
                    datetime_utc,
                    actual,
                    forecast,
                    previous,
                    source,
                    validated,
                    jblanked_actual,
                    eodhd_actual,
                    raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                event['event_key'],
                event['event_name'],
                event['event_name_original'],
                event['country'],
                event['datetime_utc'],
                event.get('actual'),
                event.get('forecast'),
                event.get('previous'),
                event['source'],
                event.get('validated', False),
                event.get('jblanked_actual'),
                event.get('eodhd_actual'),
                json.dumps(event.get('raw_data', {}))
            ])
            
            inserted += 1
            
            if inserted % 1000 == 0:
                print(f"   ... {inserted} événements")
        
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"   ⚠️ Erreur insert: {e}")
    
    print(f"   ✅ {inserted} événements insérés")
    if errors > 0:
        print(f"   ⚠️ {errors} erreurs")
    print()
    
    # Créer index
    print("🔄 Création index...")
    
    conn.execute("CREATE INDEX idx_datetime ON economic_events(datetime_utc)")
    conn.execute("CREATE INDEX idx_country ON economic_events(country)")
    conn.execute("CREATE INDEX idx_source ON economic_events(source)")
    
    print("   ✅ Index créés")
    print()
    
    # Statistiques finales
    print("=" * 80)
    print("STATISTIQUES DB")
    print("=" * 80)
    print()
    
    total = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"📊 Total événements: {total}")
    print()
    
    # Par source
    sources = conn.execute("""
        SELECT source, COUNT(*) as count
        FROM economic_events
        GROUP BY source
        ORDER BY count DESC
    """).fetchall()
    
    print("Par source:")
    for source, count in sources:
        print(f"   {source}: {count}")
    print()
    
    # Par pays (top 10)
    countries = conn.execute("""
        SELECT country, COUNT(*) as count
        FROM economic_events
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    """).fetchall()
    
    print("Top 10 pays:")
    for country, count in countries:
        print(f"   {country.upper()}: {count}")
    print()
    
    # Par année
    years = conn.execute("""
        SELECT 
            EXTRACT(YEAR FROM datetime_utc) as year,
            COUNT(*) as count
        FROM economic_events
        GROUP BY year
        ORDER BY year
    """).fetchall()
    
    print("Par année:")
    for year, count in years:
        print(f"   {int(year)}: {count}")
    print()
    
    # Validation dates critiques
    print("=" * 80)
    print("VALIDATION DATES CRITIQUES")
    print("=" * 80)
    print()
    
    # 1er août 2025
    august_1st = conn.execute("""
        SELECT COUNT(*) 
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-08-01'
    """).fetchone()[0]
    
    august_1st_usd = conn.execute("""
        SELECT COUNT(*) 
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-08-01'
        AND country = 'usd'
    """).fetchone()[0]
    
    print(f"1er août 2025:")
    print(f"   Total: {august_1st}")
    print(f"   USD: {august_1st_usd}")
    print()
    
    # 11 septembre 2025
    sept_11 = conn.execute("""
        SELECT COUNT(*) 
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-09-11'
    """).fetchone()[0]
    
    sept_11_usd = conn.execute("""
        SELECT COUNT(*) 
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-09-11'
        AND country = 'usd'
    """).fetchone()[0]
    
    print(f"11 septembre 2025:")
    print(f"   Total: {sept_11}")
    print(f"   USD: {sept_11_usd}")
    
    if sept_11_usd > 0:
        print()
        print("   Événements USD 11 sept:")
        events = conn.execute("""
            SELECT datetime_utc, event_name, source
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-09-11'
            AND country = 'usd'
            ORDER BY datetime_utc
        """).fetchall()
        
        for dt, name, source in events:
            print(f"      • {dt} - {name} ({source})")
    print()
    
    # Fermer connexion
    conn.close()
    
    print("=" * 80)
    print("✅ IMPORT TERMINÉ")
    print("=" * 80)
    print()
    print(f"📊 DB warehouse.duckdb: {total} événements")
    print()
    
    return True


if __name__ == '__main__':
    success = import_master_to_db()
    
    if success:
        print("🎉 Import réussi !")
    else:
        print("❌ Import échoué")
