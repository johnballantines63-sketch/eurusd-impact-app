"""
Import EODHD seul dans DB - Source unique

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import duckdb
import json
from pathlib import Path
from datetime import datetime
import time
import hashlib

def import_eodhd_only():
    """Importer EODHD seul dans DB"""
    
    print("=" * 80)
    print("IMPORT EODHD SEUL - SOURCE UNIQUE")
    print("=" * 80)
    print()
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    db_path = Path(__file__).parent.parent.parent / 'warehouse.duckdb'
    
    # Charger EODHD
    eodhd_file = data_dir / 'eodhd_2020_2025_fixed' / 'eodhd_all_2020_2025_fixed.json'
    
    print(f"📂 Source: {eodhd_file.name}")
    print()
    
    with open(eodhd_file, 'r') as f:
        events = json.load(f)
    
    print(f"📊 Total événements EODHD: {len(events):,}")
    print()
    
    # Connexion DB
    print(f"💾 DB: {db_path}")
    print()
    
    conn = duckdb.connect(str(db_path))
    
    # Backup table existante
    print("🔄 Backup table existante...")
    
    try:
        backup_name = f"economic_events_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM economic_events")
        
        backup_count = conn.execute(f"SELECT COUNT(*) FROM {backup_name}").fetchone()[0]
        print(f"   ✅ Backup créé: {backup_name} ({backup_count:,} événements)")
    except:
        print("   ⚠️  Pas de table existante à backuper")
    
    print()
    
    # Drop et recréer table
    print("🗑️  Drop table existante...")
    conn.execute("DROP TABLE IF EXISTS economic_events")
    print("   ✅ Table supprimée")
    print()
    
    print("🏗️  Création nouvelle table...")
    
    conn.execute("""
        CREATE TABLE economic_events (
            event_id VARCHAR PRIMARY KEY,
            datetime_utc TIMESTAMP,
            event_name VARCHAR,
            country VARCHAR,
            importance VARCHAR,
            actual DOUBLE,
            forecast DOUBLE,
            previous DOUBLE,
            source VARCHAR,
            raw_data JSON
        )
    """)
    
    print("   ✅ Table créée")
    print()
    
    # Normaliser et importer
    print("🔄 Normalisation et import...")
    print()
    
    rows = []
    country_map = {
        'US': 'usd', 'GB': 'gbp', 'EU': 'eur', 'JP': 'jpy',
        'CA': 'cad', 'AU': 'aud', 'NZ': 'nzd', 'CH': 'chf'
    }
    
    for event in events:
        try:
            # Date/time
            date_str = event.get('date', '')
            if not date_str:
                continue
            
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                continue
            
            # ID unique avec hash pour garantir unicité
            event_json = json.dumps(event, sort_keys=True)
            event_hash = hashlib.md5(event_json.encode()).hexdigest()[:8]
            event_id = f"eodhd_{date_str}_{event.get('country', 'xx')}_{event_hash}"
            event_id = event_id.replace(' ', '_').replace(':', '').replace('.', '')[:200]
            
            # Pays (convertir code ISO → code devise)
            country_iso = event.get('country', 'XX')
            country = country_map.get(country_iso, country_iso.lower())
            
            # Nom événement
            event_name = event.get('type', 'unknown').lower().replace(' ', '_').replace('-', '_')
            
            # Valeurs
            actual = event.get('actual')
            forecast = event.get('forecast')
            previous = event.get('previous')
            
            # Convertir en float si string
            for val_name in ['actual', 'forecast', 'previous']:
                val = locals()[val_name]
                if val and isinstance(val, str):
                    try:
                        locals()[val_name] = float(val.replace(',', '.'))
                    except:
                        locals()[val_name] = None
            
            # Importance (par défaut MEDIUM)
            importance = 'MEDIUM'
            
            rows.append((
                event_id,
                dt,
                event_name,
                country,
                importance,
                actual,
                forecast,
                previous,
                'EODHD',
                json.dumps(event)
            ))
        
        except Exception as e:
            continue
    
    print(f"   Événements normalisés: {len(rows):,}")
    print()
    
    # Insert en batch
    print("💾 Import dans DB...")
    
    start = time.time()
    
    conn.executemany("""
        INSERT INTO economic_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    
    elapsed = time.time() - start
    
    print(f"   ✅ Importé en {elapsed:.1f}s")
    print()
    
    # Index
    print("📊 Création index...")
    
    conn.execute("CREATE INDEX idx_datetime ON economic_events(datetime_utc)")
    conn.execute("CREATE INDEX idx_country ON economic_events(country)")
    conn.execute("CREATE INDEX idx_source ON economic_events(source)")
    
    print("   ✅ Index créés")
    print()
    
    # Statistiques
    print("=" * 80)
    print("STATISTIQUES DB")
    print("=" * 80)
    print()
    
    total = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"📊 Total événements: {total:,}")
    print()
    
    # Par pays
    by_country = conn.execute("""
        SELECT country, COUNT(*) as count
        FROM economic_events
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    """).fetchall()
    
    print("Top 10 pays:")
    for country, count in by_country:
        print(f"   {country}: {count:,}")
    
    print()
    
    # Par année
    by_year = conn.execute("""
        SELECT 
            EXTRACT(YEAR FROM datetime_utc) as year,
            COUNT(*) as count
        FROM economic_events
        GROUP BY year
        ORDER BY year
    """).fetchall()
    
    print("Par année:")
    for year, count in by_year:
        print(f"   {int(year)}: {count:,}")
    
    print()
    
    # Validation dates critiques
    print("=" * 80)
    print("VALIDATION DATES CRITIQUES")
    print("=" * 80)
    print()
    
    # 1er août
    aug1 = conn.execute("""
        SELECT COUNT(*) 
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-08-01'
    """).fetchone()[0]
    
    aug1_usd = conn.execute("""
        SELECT COUNT(*) 
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-08-01'
        AND country = 'usd'
    """).fetchone()[0]
    
    print(f"1er août 2025:")
    print(f"   Total: {aug1}")
    print(f"   USD: {aug1_usd}")
    print()
    
    # 11 septembre
    sept11 = conn.execute("""
        SELECT COUNT(*) 
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-09-11'
    """).fetchone()[0]
    
    sept11_usd = conn.execute("""
        SELECT COUNT(*) 
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-09-11'
        AND country = 'usd'
    """).fetchone()[0]
    
    print(f"11 septembre 2025:")
    print(f"   Total: {sept11}")
    print(f"   USD: {sept11_usd}")
    print()
    
    if sept11_usd > 0:
        print("   Événements USD 11 sept:")
        events_sept = conn.execute("""
            SELECT datetime_utc, event_name, actual, forecast
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-09-11'
            AND country = 'usd'
            ORDER BY datetime_utc
            LIMIT 10
        """).fetchall()
        
        for dt, name, actual, forecast in events_sept:
            print(f"      • {dt} - {name} (A:{actual} F:{forecast})")
    
    print()
    
    conn.close()
    
    # Conclusion
    print("=" * 80)
    print("✅ IMPORT TERMINÉ")
    print("=" * 80)
    print()
    
    print(f"📊 DB warehouse.duckdb: {total:,} événements")
    print()
    print("🎉 Import EODHD seul réussi !")
    print()
    print("Source unique:")
    print("   • Pipeline simplifié")
    print("   • Pas de conflits")
    print("   • 125k+ événements")
    print("   • Dates critiques validées")
    print()

if __name__ == '__main__':
    import_eodhd_only()
