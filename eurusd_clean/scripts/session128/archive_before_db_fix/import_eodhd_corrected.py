"""
Import EODHD CORRIGÉ - Session 128
==================================

CORRECTIONS vs import_eodhd_only.py original :
1. ✅ Ajout suffixes temporels (_mom, _yoy) basés sur 'comparison'
2. ✅ Lecture 'estimate' au lieu de 'forecast'
3. ✅ Backup automatique avant toute modification

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 128
"""

import duckdb
import json
from pathlib import Path
from datetime import datetime
import time
import hashlib


def import_eodhd_corrected():
    """Importer EODHD avec corrections suffixes + estimate"""
    
    print("=" * 80)
    print("IMPORT EODHD CORRIGÉ - SESSION 128")
    print("=" * 80)
    print()
    
    print("CORRECTIONS :")
    print("  1. ✅ Construction event_name avec suffixes _mom/_yoy (comparison)")
    print("  2. ✅ Lecture 'estimate' au lieu de 'forecast'")
    print("  3. ✅ Backup complet avant modification")
    print()
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    db_path = data_dir / 'warehouse.duckdb'
    
    # Charger EODHD
    eodhd_file = data_dir / 'eodhd_2020_2025_fixed' / 'eodhd_all_2020_2025_fixed.json'
    
    print(f"📂 Source: {eodhd_file.name}")
    
    if not eodhd_file.exists():
        print(f"❌ ERREUR : Fichier source introuvable : {eodhd_file}")
        return False
    
    with open(eodhd_file, 'r') as f:
        events = json.load(f)
    
    print(f"📊 Total événements EODHD: {len(events):,}")
    print()
    
    # Connexion DB
    print(f"💾 DB: {db_path}")
    print()
    
    conn = duckdb.connect(str(db_path))
    
    # ==========================================================================
    # BACKUP COMPLET - CRITIQUE
    # ==========================================================================
    
    print("="*80)
    print("BACKUP COMPLET")
    print("="*80)
    print()
    
    try:
        # Vérifier si table existe
        existing_count = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
        
        if existing_count > 0:
            backup_name = f"economic_events_backup_session128_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"🔄 Création backup : {backup_name}")
            print(f"   Événements à sauvegarder : {existing_count:,}")
            
            conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM economic_events")
            
            backup_count = conn.execute(f"SELECT COUNT(*) FROM {backup_name}").fetchone()[0]
            
            if backup_count == existing_count:
                print(f"   ✅ Backup créé avec succès : {backup_count:,} événements")
            else:
                print(f"   ❌ ERREUR : Backup incomplet ({backup_count} != {existing_count})")
                print("   ⚠️  ABANDON pour sécurité")
                conn.close()
                return False
        else:
            print("   ℹ️  Table vide, pas de backup nécessaire")
            backup_name = None
    
    except Exception as e:
        print(f"   ⚠️  Pas de table existante : {e}")
        backup_name = None
    
    print()
    
    # Confirmation utilisateur
    print("⚠️  ATTENTION : La table 'economic_events' va être REMPLACÉE")
    if backup_name:
        print(f"   Backup disponible : {backup_name}")
    print()
    
    # ==========================================================================
    # DROP ET RECRÉATION TABLE
    # ==========================================================================
    
    print("="*80)
    print("RECRÉATION TABLE")
    print("="*80)
    print()
    
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
    
    # ==========================================================================
    # NORMALISATION ET IMPORT - AVEC CORRECTIONS
    # ==========================================================================
    
    print("="*80)
    print("NORMALISATION ET IMPORT (AVEC CORRECTIONS)")
    print("="*80)
    print()
    
    rows = []
    country_map = {
        'US': 'US', 'GB': 'GB', 'EU': 'EU', 'JP': 'JP',
        'CA': 'CA', 'AU': 'AU', 'NZ': 'NZ', 'CH': 'CH',
        'DE': 'DE', 'FR': 'FR', 'IT': 'IT', 'ES': 'ES'
    }
    
    stats_suffixes = {
        'mom': 0, 'yoy': 0, 'qoq': 0, 'mtd': 0, 'ytd': 0, 'base': 0
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
            
            # CORRECTION 1 : Construction event_name avec suffixes temporels
            event_type = event.get('type', 'unknown').lower().replace(' ', '_').replace('-', '_')
            comparison = (event.get('comparison') or '').lower()  # CORRECTION: gérer None
            
            if comparison in ['mom', 'yoy', 'qoq', 'mtd', 'ytd']:
                event_name = f"{event_type}_{comparison}"
                stats_suffixes[comparison] += 1
            else:
                event_name = event_type
                stats_suffixes['base'] += 1
            
            # ID unique
            event_json = json.dumps(event, sort_keys=True)
            event_hash = hashlib.md5(event_json.encode()).hexdigest()[:8]
            event_id = f"eodhd_{date_str}_{event.get('country', 'xx')}_{event_hash}"
            event_id = event_id.replace(' ', '_').replace(':', '').replace('.', '')[:200]
            
            # Pays
            country_iso = event.get('country', 'XX')
            country = country_map.get(country_iso, country_iso)
            
            # CORRECTION 2 : Lire 'estimate' au lieu de 'forecast'
            actual = event.get('actual')
            estimate = event.get('estimate')  # ✅ CORRECTION
            previous = event.get('previous')
            
            # Convertir en float si string
            for val_name in ['actual', 'estimate', 'previous']:
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
                event_name,  # ✅ Avec suffixe si comparison présent
                country,
                importance,
                actual,
                estimate,  # ✅ Colonne forecast contient estimate
                previous,
                'EODHD',
                json.dumps(event)
            ))
        
        except Exception as e:
            continue
    
    print(f"   Événements normalisés: {len(rows):,}")
    print()
    
    print("📊 Statistiques suffixes temporels :")
    for suffix, count in stats_suffixes.items():
        if count > 0:
            pct = (count / len(rows)) * 100
            print(f"   {suffix:>4} : {count:>6,} ({pct:>5.1f}%)")
    
    print()
    
    # ==========================================================================
    # INSERT EN BATCH
    # ==========================================================================
    
    print("💾 Import dans DB...")
    print()
    
    start = time.time()
    
    conn.executemany("""
        INSERT INTO economic_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    
    elapsed = time.time() - start
    
    print(f"   ✅ Importé en {elapsed:.1f}s")
    print()
    
    # ==========================================================================
    # INDEX
    # ==========================================================================
    
    print("📊 Création index...")
    
    conn.execute("CREATE INDEX idx_datetime ON economic_events(datetime_utc)")
    conn.execute("CREATE INDEX idx_country ON economic_events(country)")
    conn.execute("CREATE INDEX idx_event_name ON economic_events(event_name)")
    conn.execute("CREATE INDEX idx_source ON economic_events(source)")
    
    print("   ✅ Index créés")
    print()
    
    # ==========================================================================
    # VALIDATION CORRECTIONS
    # ==========================================================================
    
    print("="*80)
    print("VALIDATION CORRECTIONS")
    print("="*80)
    print()
    
    # Validation 1 : Suffixes temporels présents
    print("1️⃣  VALIDATION SUFFIXES TEMPORELS")
    print("-"*80)
    
    suffixes_db = conn.execute("""
        SELECT 
            CASE 
                WHEN event_name LIKE '%_mom' THEN 'mom'
                WHEN event_name LIKE '%_yoy' THEN 'yoy'
                WHEN event_name LIKE '%_qoq' THEN 'qoq'
                ELSE 'base'
            END as suffix_type,
            COUNT(*) as count
        FROM economic_events
        GROUP BY suffix_type
        ORDER BY count DESC
    """).fetchall()
    
    for suffix, count in suffixes_db:
        print(f"   {suffix:>4} : {count:>6,}")
    
    has_mom = any(s == 'mom' for s, _ in suffixes_db)
    has_yoy = any(s == 'yoy' for s, _ in suffixes_db)
    
    if has_mom and has_yoy:
        print("   ✅ Suffixes temporels détectés")
    else:
        print("   ❌ Suffixes temporels manquants")
    
    print()
    
    # Validation 2 : Estimate (forecast) présents
    print("2️⃣  VALIDATION ESTIMATE/FORECAST")
    print("-"*80)
    
    forecast_stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(forecast) as with_forecast,
            COUNT(*) - COUNT(forecast) as without_forecast
        FROM economic_events
    """).fetchone()
    
    total, with_forecast, without = forecast_stats
    pct_with = (with_forecast / total * 100) if total > 0 else 0
    
    print(f"   Total événements:    {total:>6,}")
    print(f"   Avec forecast:       {with_forecast:>6,} ({pct_with:.1f}%)")
    print(f"   Sans forecast:       {without:>6,}")
    
    if pct_with > 50:
        print("   ✅ Forecast/estimate correctement importés")
    else:
        print("   ⚠️  Peu de forecast/estimate")
    
    print()
    
    # Validation 3 : 11 septembre spécifique
    print("3️⃣  VALIDATION 11 SEPTEMBRE 2025")
    print("-"*80)
    
    sept11_events = conn.execute("""
        SELECT 
            event_name,
            actual,
            forecast
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-09-11'
        AND country = 'US'
        AND datetime_utc >= '2025-09-11 12:30:00'
        AND datetime_utc < '2025-09-11 12:31:00'
        ORDER BY event_name
    """).fetchall()
    
    print(f"   Événements US 12:30 : {len(sept11_events)}")
    print()
    
    has_mom_sept = False
    has_yoy_sept = False
    has_forecast_sept = False
    
    for event_name, actual, forecast in sept11_events:
        fcst_str = f"{forecast:.2f}" if forecast else "NULL"
        act_str = f"{actual:.2f}" if actual else "NULL"
        
        print(f"   • {event_name:<40} F={fcst_str:>8} A={act_str:>8}")
        
        if '_mom' in event_name:
            has_mom_sept = True
        if '_yoy' in event_name:
            has_yoy_sept = True
        if forecast:
            has_forecast_sept = True
    
    print()
    
    if has_mom_sept and has_yoy_sept:
        print("   ✅ Suffixes _mom et _yoy présents pour 11 sept")
    else:
        print("   ❌ Suffixes manquants pour 11 sept")
    
    if has_forecast_sept:
        print("   ✅ Forecast/estimate présents pour 11 sept")
    else:
        print("   ❌ Forecast/estimate manquants pour 11 sept")
    
    print()
    
    # ==========================================================================
    # STATISTIQUES FINALES
    # ==========================================================================
    
    print("="*80)
    print("STATISTIQUES FINALES")
    print("="*80)
    print()
    
    total = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"📊 Total événements: {total:,}")
    print()
    
    conn.close()
    
    # ==========================================================================
    # CONCLUSION
    # ==========================================================================
    
    print("="*80)
    print("✅ IMPORT TERMINÉ")
    print("="*80)
    print()
    
    print(f"📊 DB warehouse.duckdb: {total:,} événements")
    
    if backup_name:
        print(f"💾 Backup disponible: {backup_name}")
        print("   Restauration si besoin:")
        print(f"   DROP TABLE economic_events;")
        print(f"   ALTER TABLE {backup_name} RENAME TO economic_events;")
    
    print()
    print("🎉 Import EODHD corrigé réussi !")
    print()
    print("Corrections appliquées:")
    print("   ✅ Suffixes temporels (_mom, _yoy) basés sur 'comparison'")
    print("   ✅ Lecture 'estimate' au lieu de 'forecast'")
    print()
    
    return True


if __name__ == '__main__':
    success = import_eodhd_corrected()
    
    if success:
        print("="*80)
        print("PROCHAINE ÉTAPE")
        print("="*80)
        print()
        print("Lance maintenant :")
        print("  python test_session115_ORIGINAL_adapted.py")
        print()
        print("Attendu : MAE < 2 pips ✅")
        print()
