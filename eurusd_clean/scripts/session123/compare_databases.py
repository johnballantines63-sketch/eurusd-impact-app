"""
Analyse comparative DB originale (event_impacts_v2) vs DB nouvelle (economic_events)

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import duckdb
from pathlib import Path

def compare_databases():
    """Comparer DB originale vs nouvelle avec noms tables différents"""
    
    print("=" * 80)
    print("ANALYSE COMPARATIVE - DB ORIGINALE VS NOUVELLE")
    print("=" * 80)
    print()
    
    # Chemins
    db_original = Path('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb')
    db_nouvelle = Path('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/warehouse.duckdb')
    
    print(f"DB Originale : {db_original}")
    print(f"   Table     : event_impacts_v2")
    print()
    print(f"DB Nouvelle  : {db_nouvelle}")
    print(f"   Table     : economic_events")
    print()
    
    # Vérifier existence
    if not db_original.exists():
        print(f"❌ DB originale non trouvée: {db_original}")
        return
    
    if not db_nouvelle.exists():
        print(f"❌ DB nouvelle non trouvée: {db_nouvelle}")
        return
    
    print(f"✅ Les deux DB existent")
    print()
    
    # Connexions
    conn_orig = duckdb.connect(str(db_original), read_only=True)
    conn_new = duckdb.connect(str(db_nouvelle), read_only=True)
    
    # Vérifier structure table originale
    print("STRUCTURE TABLE ORIGINALE:")
    print()
    
    columns_orig = conn_orig.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'event_impacts_v2'
        ORDER BY ordinal_position
    """).fetchall()
    
    print("Colonnes event_impacts_v2:")
    for col, dtype in columns_orig:
        print(f"   • {col:30s} : {dtype}")
    
    print()
    
    # ====================================================================
    # STATISTIQUES GLOBALES
    # ====================================================================
    
    print("=" * 80)
    print("STATISTIQUES GLOBALES")
    print("=" * 80)
    print()
    
    total_orig = conn_orig.execute("SELECT COUNT(*) FROM event_impacts_v2").fetchone()[0]
    total_new = conn_new.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    
    print(f"DB Originale : {total_orig:,} événements")
    print(f"DB Nouvelle  : {total_new:,} événements")
    print(f"Différence   : {total_orig - total_new:+,} événements")
    print()
    
    # Chercher colonne date dans table originale
    date_col = 'event_time'  # Nom probable
    
    # Vérifier si colonne existe
    has_event_time = any(col == 'event_time' for col, _ in columns_orig)
    has_datetime = any('date' in col.lower() or 'time' in col.lower() for col, _ in columns_orig)
    
    if has_event_time:
        date_col = 'event_time'
    else:
        # Trouver colonne date
        for col, dtype in columns_orig:
            if 'timestamp' in dtype.lower() or 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
    
    print(f"Colonne date DB originale : {date_col}")
    print()
    
    # ====================================================================
    # PAR ANNÉE
    # ====================================================================
    
    print("PAR ANNÉE:")
    print()
    
    try:
        years_orig = conn_orig.execute(f"""
            SELECT 
                EXTRACT(YEAR FROM {date_col}) as year,
                COUNT(*) as count
            FROM event_impacts_v2
            GROUP BY year
            ORDER BY year
        """).fetchall()
        
        years_new = conn_new.execute("""
            SELECT 
                EXTRACT(YEAR FROM datetime_utc) as year,
                COUNT(*) as count
            FROM economic_events
            GROUP BY year
            ORDER BY year
        """).fetchall()
        
        years_dict_orig = {int(y): c for y, c in years_orig}
        years_dict_new = {int(y): c for y, c in years_new}
        
        all_years = sorted(set(years_dict_orig.keys()) | set(years_dict_new.keys()))
        
        print(f"{'Année':<8} {'Originale':<12} {'Nouvelle':<12} {'Différence':<12}")
        print("-" * 50)
        
        for year in all_years:
            orig = years_dict_orig.get(year, 0)
            new = years_dict_new.get(year, 0)
            diff = orig - new
            print(f"{year:<8} {orig:<12,} {new:<12,} {diff:+12,}")
        
        print()
    
    except Exception as e:
        print(f"⚠️  Impossible d'analyser par année: {e}")
        print()
    
    # ====================================================================
    # 11 SEPTEMBRE 2025 - ANALYSE DÉTAILLÉE
    # ====================================================================
    
    print("=" * 80)
    print("11 SEPTEMBRE 2025 - ANALYSE DÉTAILLÉE")
    print("=" * 80)
    print()
    
    try:
        sept11_orig = conn_orig.execute(f"""
            SELECT COUNT(*) 
            FROM event_impacts_v2
            WHERE DATE({date_col}) = '2025-09-11'
        """).fetchone()[0]
        
        sept11_new = conn_new.execute("""
            SELECT COUNT(*) 
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-09-11'
        """).fetchone()[0]
        
        print(f"DB Originale : {sept11_orig} événements 11 sept")
        print(f"DB Nouvelle  : {sept11_new} événements 11 sept")
        print(f"Différence   : {sept11_orig - sept11_new:+d} événements")
        print()
        
        # Détail événements 11 sept DB originale
        if sept11_orig > 0:
            print("ÉVÉNEMENTS 11 SEPT - DB ORIGINALE:")
            print()
            
            # Sélectionner toutes colonnes
            events_orig = conn_orig.execute(f"""
                SELECT *
                FROM event_impacts_v2
                WHERE DATE({date_col}) = '2025-09-11'
                ORDER BY {date_col}
            """).fetchall()
            
            if len(events_orig) > 0:
                # Afficher premiers événements
                print(f"   {len(events_orig)} événements trouvés")
                print()
                print("   Premiers 10 événements:")
                for i, event in enumerate(events_orig[:10], 1):
                    print(f"      [{i}] {event}")
            
            print()
        
        # Détail événements 11 sept DB nouvelle
        if sept11_new > 0:
            print("ÉVÉNEMENTS 11 SEPT - DB NOUVELLE:")
            print()
            
            events_new = conn_new.execute("""
                SELECT datetime_utc, event_name, country, source, actual, forecast
                FROM economic_events
                WHERE DATE(datetime_utc) = '2025-09-11'
                ORDER BY datetime_utc
            """).fetchall()
            
            for dt, name, country, source, actual, forecast in events_new:
                print(f"   {dt} | {country.upper():3s} | {name:30s} | {source:10s} | A:{actual} F:{forecast}")
            
            print()
    
    except Exception as e:
        print(f"⚠️  Erreur analyse 11 septembre: {e}")
        print()
    
    # ====================================================================
    # 1ER AOÛT 2025
    # ====================================================================
    
    print("=" * 80)
    print("1ER AOÛT 2025 - COMPARAISON")
    print("=" * 80)
    print()
    
    try:
        aug1_orig = conn_orig.execute(f"""
            SELECT COUNT(*) 
            FROM event_impacts_v2
            WHERE DATE({date_col}) = '2025-08-01'
        """).fetchone()[0]
        
        aug1_new = conn_new.execute("""
            SELECT COUNT(*) 
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-08-01'
        """).fetchone()[0]
        
        print(f"DB Originale : {aug1_orig} événements")
        print(f"DB Nouvelle  : {aug1_new} événements")
        print(f"Différence   : {aug1_orig - aug1_new:+d} événements")
        print()
    
    except Exception as e:
        print(f"⚠️  Erreur analyse 1er août: {e}")
        print()
    
    # ====================================================================
    # CONCLUSION
    # ====================================================================
    
    print("=" * 80)
    print("CONCLUSION SCIENTIFIQUE")
    print("=" * 80)
    print()
    
    if total_orig > total_new:
        print(f"✅ DB ORIGINALE PLUS COMPLÈTE")
        print()
        print(f"   • {total_orig - total_new:,} événements supplémentaires dans DB originale")
        print()
        print("RECOMMANDATIONS:")
        print("   1. DB originale = production actuelle (event_impacts_v2)")
        print("   2. DB nouvelle = import test (economic_events)")
        print("   3. DÉCISION NÉCESSAIRE:")
        print("      A. Garder DB originale (abandonner nouvelle)")
        print("      B. Merger nouvelle DANS originale")
        print("      C. Analyser pourquoi originale plus complète")
    
    elif total_new > total_orig:
        print(f"✅ DB NOUVELLE PLUS COMPLÈTE")
        print()
        print(f"   • {total_new - total_orig:,} événements supplémentaires dans DB nouvelle")
        print()
        print("DB nouvelle (75,193) peut remplacer originale")
    
    else:
        print("⚠️  MÊME NOMBRE D'ÉVÉNEMENTS")
        print()
        print("Structures différentes mais totaux identiques")
    
    print()
    
    conn_orig.close()
    conn_new.close()

if __name__ == '__main__':
    compare_databases()
