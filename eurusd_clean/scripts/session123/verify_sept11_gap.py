"""
Vérification gap 11 septembre - Analyse scientifique

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import duckdb
import json
from pathlib import Path

def verify_sept_11():
    """Vérifier gap 11 septembre scientifiquement"""
    
    print("=" * 80)
    print("ANALYSE SCIENTIFIQUE - GAP 11 SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    # Connexion DB
    db_path = Path(__file__).parent.parent.parent / 'warehouse.duckdb'
    conn = duckdb.connect(str(db_path))
    
    # 1. Vérifier backup tables
    print("1️⃣ VÉRIFICATION BACKUP TABLES")
    print("-" * 70)
    
    tables = conn.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE 'economic_events_backup%'
        ORDER BY table_name DESC
    """).fetchall()
    
    if tables:
        print(f"   Backups trouvés: {len(tables)}")
        for (table_name,) in tables:
            count = conn.execute(f"""
                SELECT COUNT(*) 
                FROM {table_name}
                WHERE DATE(datetime_utc) = '2025-09-11'
            """).fetchone()[0]
            
            print(f"   • {table_name}: {count} événements 11 sept")
            
            if count > 7:
                print(f"     ⚠️  BACKUP AVAIT PLUS D'ÉVÉNEMENTS ({count} vs 7 actuel)")
                print()
                print(f"     Événements dans backup:")
                events = conn.execute(f"""
                    SELECT datetime_utc, event_name, country, source
                    FROM {table_name}
                    WHERE DATE(datetime_utc) = '2025-09-11'
                    AND country = 'usd'
                    ORDER BY datetime_utc
                """).fetchall()
                
                for dt, name, country, source in events:
                    print(f"        {dt} | {country} | {name} | {source}")
    else:
        print("   ⚠️  Aucun backup trouvé")
    
    print()
    
    # 2. Vérifier fichiers sources
    print("2️⃣ VÉRIFICATION FICHIERS SOURCES")
    print("-" * 70)
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    # JBlanked
    jblanked_file = data_dir / 'jblanked_2020_2025' / 'jblanked_all_2020_2025.json'
    if jblanked_file.exists():
        with open(jblanked_file, 'r') as f:
            jblanked_events = json.load(f)
        
        jb_sept11 = [e for e in jblanked_events 
                     if e.get('Date', '').startswith('2025.09.11')]
        
        print(f"   JBlanked fichier: {len(jb_sept11)} événements 11 sept")
        
        jb_sept11_usd = [e for e in jb_sept11 if e.get('Currency') == 'USD']
        print(f"   JBlanked USD: {len(jb_sept11_usd)}")
        
        if len(jb_sept11_usd) > 0:
            print(f"     Détail:")
            for e in jb_sept11_usd:
                print(f"        {e.get('Date')} - {e.get('Name')}")
    
    print()
    
    # EODHD
    eodhd_file = data_dir / 'eodhd_2020_2025_monthly' / 'eodhd_all_2020_2025_monthly.json'
    if eodhd_file.exists():
        with open(eodhd_file, 'r') as f:
            eodhd_events = json.load(f)
        
        eodhd_sept11 = [e for e in eodhd_events 
                        if e.get('date', '').startswith('2025-09-11')]
        
        print(f"   EODHD fichier: {len(eodhd_sept11)} événements 11 sept")
        
        eodhd_sept11_us = [e for e in eodhd_sept11 if e.get('country') == 'US']
        print(f"   EODHD US: {len(eodhd_sept11_us)}")
        
        if len(eodhd_sept11_us) > 0:
            print(f"     Détail:")
            for e in eodhd_sept11_us:
                print(f"        {e.get('date')} - {e.get('type')}")
        else:
            print(f"     ⚠️  EODHD = 0 événements 11 septembre (gap confirmé)")
    
    print()
    
    # 3. Statistiques DB actuelle
    print("3️⃣ DB ACTUELLE")
    print("-" * 70)
    
    current = conn.execute("""
        SELECT datetime_utc, event_name, country, source, actual, forecast
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-09-11'
        AND country = 'usd'
        ORDER BY datetime_utc
    """).fetchall()
    
    print(f"   DB actuelle: {len(current)} événements USD 11 sept")
    print()
    print("   Détail:")
    for dt, name, country, source, actual, forecast in current:
        print(f"      {dt} | {name:30s} | {source:15s} | A:{actual} F:{forecast}")
    
    print()
    
    # Conclusion
    print("=" * 80)
    print("CONCLUSION SCIENTIFIQUE")
    print("=" * 80)
    print()
    
    if tables and any(conn.execute(f"SELECT COUNT(*) FROM {t[0]} WHERE DATE(datetime_utc) = '2025-09-11'").fetchone()[0] > 7 for t in tables):
        print("✅ DIFFÉRENCE CONFIRMÉE")
        print()
        print("Explication:")
        print("   1. Backup table contenait PLUS d'événements 11 septembre")
        print("   2. Import actuel a REMPLACÉ table (DROP + CREATE)")
        print("   3. Sources actuelles (JBlanked + EODHD) ont seulement 7 événements USD")
        print()
        print("Hypothèses:")
        print("   A. DB précédente contenait import d'une autre source")
        print("   B. Import manuel/test précédent")
        print("   C. Données supplémentaires perdues lors DROP TABLE")
    else:
        print("⚠️  AUCUNE DIFFÉRENCE DÉTECTABLE")
        print()
        print("Possibilités:")
        print("   A. Pas de backup disponible pour comparaison")
        print("   B. Confusion avec une autre date/DB")
        print("   C. DB précédente déjà remplacée")
    
    print()
    
    conn.close()

if __name__ == '__main__':
    verify_sept_11()
