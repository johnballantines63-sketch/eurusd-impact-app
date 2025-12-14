"""
Import EODHD vers table EVENTS (structure MASTER_PLAN)
======================================================

OBJECTIF: Remplir table 'events' avec TOUS événements EODHD
STRUCTURE: Celle définie dans MASTER_PLAN.md (ts_utc, event_key, importance_n)

CORRECTIONS appliquées:
1. ✅ Suffixes temporels _mom/_yoy basés sur comparison
2. ✅ Gérer comparison=None (pas de crash)
3. ✅ Colonne 'estimate' (pas 'forecast')
4. ✅ importance_n numérique (1/2/3)
5. ✅ ts_utc avec timezone

Auteur: André Valentin avec Claude
Date: 12 novembre 2025 - Session 128
"""

import duckdb
import json
from pathlib import Path
from datetime import datetime
import hashlib
import pytz

def import_to_events_table():
    """Import EODHD vers table events (structure MASTER_PLAN)"""
    
    print("="*80)
    print("IMPORT EODHD → TABLE EVENTS (STRUCTURE MASTER_PLAN)")
    print("="*80)
    print()
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    db_path = data_dir / 'warehouse.duckdb'
    eodhd_file = data_dir / 'eodhd_2020_2025_fixed' / 'eodhd_all_2020_2025_fixed.json'
    
    print(f"📂 Source: {eodhd_file.name}")
    print(f"💾 DB: {db_path}")
    print()
    
    if not eodhd_file.exists():
        print(f"❌ Fichier source introuvable")
        return False
    
    with open(eodhd_file, 'r') as f:
        events = json.load(f)
    
    print(f"📊 Total événements EODHD: {len(events):,}")
    print()
    
    # Connexion DB
    conn = duckdb.connect(str(db_path))
    
    # ==========================================================================
    # BACKUP TABLE EVENTS
    # ==========================================================================
    
    print("="*80)
    print("BACKUP TABLE EVENTS")
    print("="*80)
    print()
    
    try:
        existing_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        
        if existing_count > 0:
            backup_name = f"events_backup_session128_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"🔄 Création backup: {backup_name}")
            print(f"   Événements: {existing_count:,}")
            
            conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM events")
            
            backup_count = conn.execute(f"SELECT COUNT(*) FROM {backup_name}").fetchone()[0]
            
            if backup_count == existing_count:
                print(f"   ✅ Backup créé: {backup_count:,} événements")
            else:
                print(f"   ❌ Backup incomplet - ABANDON")
                conn.close()
                return False
        else:
            print("   ℹ️  Table vide, pas de backup nécessaire")
            backup_name = None
    
    except Exception as e:
        print(f"   ⚠️  Table n'existe pas encore: {e}")
        backup_name = None
    
    print()
    
    # ==========================================================================
    # DROP ET RECRÉATION TABLE EVENTS (STRUCTURE MASTER_PLAN)
    # ==========================================================================
    
    print("="*80)
    print("RECRÉATION TABLE EVENTS (STRUCTURE MASTER_PLAN)")
    print("="*80)
    print()
    
    print("🗑️  Drop table existante...")
    conn.execute("DROP TABLE IF EXISTS events")
    print("   ✅ Table supprimée")
    print()
    
    print("🏗️  Création table events (structure MASTER_PLAN)...")
    
    # STRUCTURE EXACTE du MASTER_PLAN
    conn.execute("""
        CREATE TABLE events (
            ts_utc               TIMESTAMP WITH TIME ZONE,
            country              VARCHAR,
            event_title          VARCHAR,
            event_key            VARCHAR,
            importance_n         BIGINT,
            actual               DOUBLE,
            previous             DOUBLE,
            estimate             DOUBLE,
            forecast             DOUBLE,
            unit                 VARCHAR,
            type                 VARCHAR,
            label                VARCHAR,
            comparison           VARCHAR,
            period               VARCHAR,
            change               DOUBLE,
            change_percentage    DOUBLE,
            event_type           VARCHAR
        )
    """)
    
    print("   ✅ Table créée")
    print()
    
    # ==========================================================================
    # NORMALISATION ET IMPORT
    # ==========================================================================
    
    print("="*80)
    print("NORMALISATION ET IMPORT")
    print("="*80)
    print()
    
    rows = []
    country_map = {
        'US': 'US', 'GB': 'GB', 'EU': 'EU', 'JP': 'JP',
        'CA': 'CA', 'AU': 'AU', 'NZ': 'NZ', 'CH': 'CH',
        'DE': 'DE', 'FR': 'FR', 'IT': 'IT', 'ES': 'ES'
    }
    
    stats = {'mom': 0, 'yoy': 0, 'qoq': 0, 'base': 0, 'errors': 0}
    
    for event in events:
        try:
            # Date/time avec timezone UTC
            date_str = event.get('date', '')
            if not date_str:
                continue
            
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # Assurer timezone UTC
                if dt.tzinfo is None:
                    dt = pytz.UTC.localize(dt)
            except:
                stats['errors'] += 1
                continue
            
            # event_key avec suffixes _mom/_yoy (CORRECTION)
            event_type_raw = event.get('type', 'unknown')
            # GARDER espaces (comme event_families) au lieu de remplacer par underscores
            event_type = event_type_raw.lower().replace('-', ' ')
            comparison = (event.get('comparison') or '').lower()  # Gérer None
            
            if comparison in ['mom', 'yoy', 'qoq', 'mtd', 'ytd']:
                event_key = f"{event_type}_{comparison}"  # underscore SEULEMENT avant suffixe
                stats[comparison] += 1
            else:
                event_key = event_type
                stats['base'] += 1
            
            # event_title (titre original)
            event_title = event_type_raw
            
            # Pays
            country_iso = event.get('country', 'XX')
            country = country_map.get(country_iso, country_iso)
            
            # Valeurs
            actual = event.get('actual')
            estimate = event.get('estimate')  # ✅ ESTIMATE (pas forecast)
            previous = event.get('previous')
            
            # Convertir strings en float
            for val_name in ['actual', 'estimate', 'previous']:
                val = locals()[val_name]
                if val and isinstance(val, str):
                    try:
                        locals()[val_name] = float(val.replace(',', '.'))
                    except:
                        locals()[val_name] = None
            
            # importance_n numérique (1/2/3) - Par défaut MEDIUM=2
            importance_n = 2
            
            # Colonnes additionnelles (optionnelles)
            unit = event.get('unit')
            type_val = event.get('type')
            label = event.get('label')
            period = event.get('period')
            change = event.get('change')
            change_pct = event.get('change_percentage')
            event_type_val = event.get('event_type')
            
            rows.append((
                dt,                # ts_utc (avec timezone)
                country,           # country
                event_title,       # event_title
                event_key,         # event_key (avec _mom/_yoy si applicable)
                importance_n,      # importance_n (1/2/3)
                actual,            # actual
                previous,          # previous
                estimate,          # estimate
                estimate,          # forecast (même que estimate pour compatibilité)
                unit,              # unit
                type_val,          # type
                label,             # label
                comparison,        # comparison
                period,            # period
                change,            # change
                change_pct,        # change_percentage
                event_type_val     # event_type
            ))
        
        except Exception as e:
            stats['errors'] += 1
            continue
    
    print(f"   Événements normalisés: {len(rows):,}")
    print()
    
    print("📊 Statistiques suffixes:")
    for suffix, count in stats.items():
        if suffix != 'errors' and count > 0:
            pct = (count / len(rows)) * 100
            print(f"   {suffix:>6} : {count:>6,} ({pct:>5.1f}%)")
    
    if stats['errors'] > 0:
        print(f"   errors : {stats['errors']:>6,}")
    
    print()
    
    # ==========================================================================
    # INSERT EN BATCH
    # ==========================================================================
    
    print("💾 Import dans DB...")
    print()
    
    import time
    start = time.time()
    
    conn.executemany("""
        INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    
    elapsed = time.time() - start
    
    print(f"   ✅ Importé en {elapsed:.1f}s")
    print()
    
    # ==========================================================================
    # INDEX
    # ==========================================================================
    
    print("📊 Création index...")
    
    # Drop index s'ils existent (au cas où)
    try:
        conn.execute("DROP INDEX IF EXISTS idx_ts_utc")
        conn.execute("DROP INDEX IF EXISTS idx_country")
        conn.execute("DROP INDEX IF EXISTS idx_event_key")
        conn.execute("DROP INDEX IF EXISTS idx_importance")
    except:
        pass
    
    conn.execute("CREATE INDEX idx_ts_utc ON events(ts_utc)")
    conn.execute("CREATE INDEX idx_country ON events(country)")
    conn.execute("CREATE INDEX idx_event_key ON events(event_key)")
    conn.execute("CREATE INDEX idx_importance ON events(importance_n)")
    
    print("   ✅ Index créés")
    print()
    
    # ==========================================================================
    # VALIDATION
    # ==========================================================================
    
    print("="*80)
    print("VALIDATION")
    print("="*80)
    print()
    
    # Total
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"📊 Total événements: {total:,}")
    print()
    
    # Validation 11 septembre 2025
    print("🎯 VALIDATION 11 SEPTEMBRE 2025")
    print("-"*80)
    
    sept11 = conn.execute("""
        SELECT 
            ts_utc,
            event_key,
            country,
            estimate,
            actual
        FROM events
        WHERE DATE(ts_utc) = '2025-09-11'
          AND country = 'US'
          AND ts_utc >= '2025-09-11 12:30:00+00:00'
          AND ts_utc < '2025-09-11 12:31:00+00:00'
        ORDER BY event_key
    """).fetchall()
    
    print(f"   Événements US 12:30 UTC: {len(sept11)}")
    print()
    
    for ts, key, country, est, act in sept11:
        est_str = f"{est:.2f}" if est else "NULL"
        act_str = f"{act:.2f}" if act else "NULL"
        print(f"   • {key:<40} E={est_str:>8} A={act_str:>8}")
    
    print()
    
    # Vérifier présence événements critiques
    critical_events = [
        'initial_jobless_claims',
        'continuing_jobless_claims',
        'inflation_rate_mom',
        'core_inflation_rate_mom',
        'cpi'
    ]
    
    found = [key for _, key, _, _, _ in sept11]
    
    print("   Vérification événements critiques:")
    for event in critical_events:
        if event in found:
            print(f"   ✅ {event}")
        else:
            print(f"   ❌ {event} MANQUANT")
    
    print()
    
    conn.close()
    
    # ==========================================================================
    # CONCLUSION
    # ==========================================================================
    
    print("="*80)
    print("✅ IMPORT TERMINÉ")
    print("="*80)
    print()
    
    print(f"📊 Table events: {total:,} événements")
    
    if backup_name:
        print(f"💾 Backup: {backup_name}")
    
    print()
    print("🎯 PROCHAINE ÉTAPE:")
    print("   python test_session115_ORIGINAL_adapted.py")
    print()
    print("   Attendu: MAE < 2 pips ✅")
    print()
    
    return True


if __name__ == '__main__':
    success = import_to_events_table()
    
    if not success:
        print("\n❌ Import échoué")
        exit(1)
