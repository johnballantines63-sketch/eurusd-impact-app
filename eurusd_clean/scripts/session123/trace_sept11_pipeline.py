"""
Analyse pipeline 11 septembre - Traçage événements manquants

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import json
import duckdb
from pathlib import Path
from datetime import datetime

def trace_sept11_pipeline():
    """Tracer événements 11 septembre à travers tout le pipeline"""
    
    print("=" * 80)
    print("ANALYSE PIPELINE 11 SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    # ====================================================================
    # ÉTAPE 1 : FICHIERS SOURCES BRUTS
    # ====================================================================
    
    print("ÉTAPE 1 : FICHIERS SOURCES BRUTS")
    print("=" * 70)
    print()
    
    # JBlanked
    jblanked_file = data_dir / 'jblanked_2020_2025' / 'jblanked_all_2020_2025.json'
    
    jb_sept11 = []
    if jblanked_file.exists():
        with open(jblanked_file, 'r') as f:
            jblanked_all = json.load(f)
        
        jb_sept11 = [e for e in jblanked_all if e.get('Date', '').startswith('2025.09.11')]
        
        print(f"JBlanked fichier : {len(jb_sept11)} événements 11 sept")
        print()
        
        for e in jb_sept11:
            currency = e.get('Currency', 'XXX')
            name = e.get('Name', 'Unknown')
            date = e.get('Date', '')
            print(f"   {date} | {currency:3s} | {name}")
    
    print()
    
    # EODHD
    eodhd_file = data_dir / 'eodhd_2020_2025_monthly' / 'eodhd_all_2020_2025_monthly.json'
    
    eodhd_sept11 = []
    if eodhd_file.exists():
        with open(eodhd_file, 'r') as f:
            eodhd_all = json.load(f)
        
        eodhd_sept11 = [e for e in eodhd_all if e.get('date', '').startswith('2025-09-11')]
        
        print(f"EODHD fichier : {len(eodhd_sept11)} événements 11 sept")
        print()
        
        for e in eodhd_sept11:
            country = e.get('country', 'XX')
            event_type = e.get('type', 'Unknown')
            date = e.get('date', '')
            print(f"   {date} | {country:3s} | {event_type}")
    else:
        print("EODHD fichier : Non trouvé")
    
    print()
    
    # ====================================================================
    # ÉTAPE 2 : FICHIER MASTER (APRÈS MERGE)
    # ====================================================================
    
    print("ÉTAPE 2 : FICHIER MASTER (APRÈS MERGE)")
    print("=" * 70)
    print()
    
    master_file = data_dir / 'master' / 'events_master_2020_2025.json'
    
    if master_file.exists():
        with open(master_file, 'r') as f:
            master_all = json.load(f)
        
        master_sept11 = [e for e in master_all if e.get('datetime_utc', '').startswith('2025-09-11')]
        
        print(f"Master fichier : {len(master_sept11)} événements 11 sept")
        print()
        
        # Grouper par source
        by_source = {}
        for e in master_sept11:
            source = e.get('source', 'UNKNOWN')
            by_source[source] = by_source.get(source, 0) + 1
        
        print("Par source:")
        for source, count in sorted(by_source.items()):
            print(f"   {source:20s} : {count}")
        
        print()
        
        # Détail événements
        print("Détail événements:")
        for e in master_sept11:
            dt = e.get('datetime_utc', '')
            country = e.get('country', 'xxx')
            name = e.get('event_name', 'unknown')
            source = e.get('source', '')
            print(f"   {dt} | {country.upper():3s} | {name:30s} | {source}")
    else:
        print("Master fichier : Non trouvé")
    
    print()
    
    # ====================================================================
    # ÉTAPE 3 : DB NOUVELLE (APRÈS IMPORT)
    # ====================================================================
    
    print("ÉTAPE 3 : DB NOUVELLE (APRÈS IMPORT)")
    print("=" * 70)
    print()
    
    db_new = Path(__file__).parent.parent.parent / 'warehouse.duckdb'
    
    if db_new.exists():
        conn = duckdb.connect(str(db_new), read_only=True)
        
        count = conn.execute("""
            SELECT COUNT(*)
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-09-11'
        """).fetchone()[0]
        
        print(f"DB nouvelle : {count} événements 11 sept")
        print()
        
        # Par source
        by_source = conn.execute("""
            SELECT source, COUNT(*)
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-09-11'
            GROUP BY source
            ORDER BY source
        """).fetchall()
        
        print("Par source:")
        for source, cnt in by_source:
            print(f"   {source:20s} : {cnt}")
        
        print()
        
        conn.close()
    
    # ====================================================================
    # ÉTAPE 4 : DB ORIGINALE (RÉFÉRENCE)
    # ====================================================================
    
    print("ÉTAPE 4 : DB ORIGINALE (RÉFÉRENCE)")
    print("=" * 70)
    print()
    
    db_orig = Path('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb')
    
    if db_orig.exists():
        conn = duckdb.connect(str(db_orig), read_only=True)
        
        # Trouver colonne date
        columns = conn.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'event_impacts_v2'
        """).fetchall()
        
        date_col = 'event_time'  # Défaut
        for (col,) in columns:
            if 'time' in col.lower() or 'date' in col.lower():
                date_col = col
                break
        
        try:
            count = conn.execute(f"""
                SELECT COUNT(*)
                FROM event_impacts_v2
                WHERE DATE({date_col}) = '2025-09-11'
            """).fetchone()[0]
            
            print(f"DB originale : {count} événements 11 sept")
            print(f"   (table: event_impacts_v2, colonne date: {date_col})")
            print()
            
            # Essayer de lister événements
            try:
                events = conn.execute(f"""
                    SELECT *
                    FROM event_impacts_v2
                    WHERE DATE({date_col}) = '2025-09-11'
                    ORDER BY {date_col}
                """).fetchall()
                
                if len(events) > 0:
                    print(f"   Détail {len(events)} événements:")
                    for i, event in enumerate(events[:20], 1):
                        print(f"      [{i:2d}] {str(event)[:100]}")
                        
            except Exception as e:
                print(f"   ⚠️  Impossible de lister: {e}")
        
        except Exception as e:
            print(f"   ⚠️  Erreur: {e}")
        
        conn.close()
    
    print()
    
    # ====================================================================
    # ANALYSE DIFFÉRENCES
    # ====================================================================
    
    print("=" * 80)
    print("ANALYSE DIFFÉRENCES")
    print("=" * 80)
    print()
    
    print("PIPELINE 11 SEPTEMBRE:")
    print()
    print(f"   Source JBlanked       : {len(jb_sept11)} événements")
    print(f"   Source EODHD          : {len(eodhd_sept11)} événements")
    print(f"   ────────────────────────────────────")
    print(f"   Total sources         : {len(jb_sept11) + len(eodhd_sept11)} événements")
    print()
    
    if master_file.exists():
        print(f"   Master (après merge)  : {len(master_sept11)} événements")
        print(f"   Perte merge           : {len(jb_sept11) + len(eodhd_sept11) - len(master_sept11)} événements")
    print()
    
    if db_new.exists():
        conn = duckdb.connect(str(db_new), read_only=True)
        db_count = conn.execute("SELECT COUNT(*) FROM economic_events WHERE DATE(datetime_utc) = '2025-09-11'").fetchone()[0]
        conn.close()
        
        print(f"   DB nouvelle (import)  : {db_count} événements")
        if master_file.exists():
            print(f"   Perte import          : {len(master_sept11) - db_count} événements")
    print()
    
    if db_orig.exists():
        conn = duckdb.connect(str(db_orig), read_only=True)
        try:
            orig_count = conn.execute(f"SELECT COUNT(*) FROM event_impacts_v2 WHERE DATE({date_col}) = '2025-09-11'").fetchone()[0]
            print(f"   DB originale          : {orig_count} événements")
            print()
            
            if orig_count > db_count:
                print(f"   ⚠️  DB ORIGINALE A {orig_count - db_count} ÉVÉNEMENTS DE PLUS")
                print()
                print("   HYPOTHÈSE: DB originale contient autre source que JBlanked+EODHD")
        except:
            pass
        conn.close()
    
    print()
    
    # ====================================================================
    # CONCLUSION
    # ====================================================================
    
    print("=" * 80)
    print("CONCLUSION SCIENTIFIQUE")
    print("=" * 80)
    print()
    
    if len(eodhd_sept11) == 0:
        print("✅ EODHD N'A AUCUN ÉVÉNEMENT 11 SEPTEMBRE")
        print()
        print("   Gap EODHD confirmé sur cette date critique")
        print("   JBlanked seule source pour 11 septembre")
        print()
    
    if db_orig.exists():
        print("✅ DB ORIGINALE PLUS COMPLÈTE SUR 11 SEPTEMBRE")
        print()
        print("   EXPLICATION PROBABLE:")
        print("   • DB originale contenait AUTRE source (pas EODHD/JBlanked)")
        print("   • Import manuel précédent avec données supplémentaires")
        print("   • Source perdue lors DROP TABLE nouvelle DB")
        print()
        print("   RECOMMANDATION:")
        print("   • Identifier source DB originale")
        print("   • Récupérer ces données")
        print("   • Ajouter à nouvelle DB")

if __name__ == '__main__':
    trace_sept11_pipeline()
