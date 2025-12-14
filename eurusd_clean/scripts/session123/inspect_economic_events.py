"""
Inspecter structure table economic_events

Vérifier :
1. Colonnes disponibles
2. Valeurs colonne importance
3. Événements 11 septembre 2025
4. Format données

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Diagnostic DB
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def inspect_economic_events():
    """Inspecter table economic_events"""
    
    print("=" * 80)
    print("INSPECTION TABLE ECONOMIC_EVENTS")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ========================================================================
    # 1. STRUCTURE TABLE
    # ========================================================================
    
    print("1. STRUCTURE TABLE")
    print("=" * 80)
    print()
    
    query_structure = """
    DESCRIBE economic_events
    """
    
    structure = conn.execute(query_structure).df()
    print(structure.to_string())
    print()
    
    # ========================================================================
    # 2. NOMBRE LIGNES
    # ========================================================================
    
    print("2. NOMBRE D'ÉVÉNEMENTS")
    print("=" * 80)
    print()
    
    query_count = """
    SELECT COUNT(*) as total FROM economic_events
    """
    
    total = conn.execute(query_count).fetchone()[0]
    print(f"Total événements : {total:,}")
    print()
    
    # ========================================================================
    # 3. VALEURS COLONNE IMPORTANCE
    # ========================================================================
    
    print("3. VALEURS COLONNE IMPORTANCE")
    print("=" * 80)
    print()
    
    # Vérifier si colonne importance existe
    columns = [row[0] for row in structure.values]
    
    if 'importance' in columns:
        query_importance = """
        SELECT 
            importance,
            COUNT(*) as count
        FROM economic_events
        GROUP BY importance
        ORDER BY count DESC
        """
        
        importance_dist = conn.execute(query_importance).df()
        print(importance_dist.to_string())
    else:
        print("⚠️  Colonne 'importance' n'existe pas !")
        print(f"Colonnes disponibles : {', '.join(columns)}")
    
    print()
    
    # ========================================================================
    # 4. ÉVÉNEMENTS 11 SEPTEMBRE 2025
    # ========================================================================
    
    print("4. ÉVÉNEMENTS 11 SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    query_sept11 = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
    ORDER BY datetime_utc
    """
    
    sept11_events = conn.execute(query_sept11).df()
    
    if len(sept11_events) > 0:
        print(f"✅ {len(sept11_events)} événements trouvés")
        print()
        print(sept11_events.to_string())
    else:
        print("❌ Aucun événement trouvé pour le 11 septembre 2025")
        
        # Vérifier dates disponibles
        query_dates = """
        SELECT 
            MIN(DATE(datetime_utc)) as min_date,
            MAX(DATE(datetime_utc)) as max_date,
            COUNT(DISTINCT DATE(datetime_utc)) as total_dates
        FROM economic_events
        """
        
        dates_range = conn.execute(query_dates).df()
        print()
        print("Plage dates disponibles :")
        print(dates_range.to_string())
    
    print()
    
    # ========================================================================
    # 5. ÉVÉNEMENTS USD AUTOUR 14:30
    # ========================================================================
    
    print("5. ÉVÉNEMENTS USD 11 SEPT AUTOUR 14:30 BERN")
    print("=" * 80)
    print()
    
    query_usd_14h30 = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND country = 'usd'
      AND HOUR(datetime_utc) BETWEEN 11 AND 15
    ORDER BY datetime_utc
    """
    
    usd_events = conn.execute(query_usd_14h30).df()
    
    if len(usd_events) > 0:
        print(f"✅ {len(usd_events)} événements USD trouvés")
        print()
        print(usd_events.to_string())
    else:
        print("❌ Aucun événement USD trouvé")
    
    print()
    
    # ========================================================================
    # 6. SAMPLE ÉVÉNEMENTS
    # ========================================================================
    
    print("6. ÉCHANTILLON 10 ÉVÉNEMENTS")
    print("=" * 80)
    print()
    
    query_sample = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    ORDER BY datetime_utc DESC
    LIMIT 10
    """
    
    sample = conn.execute(query_sample).df()
    print(sample.to_string())
    print()
    
    conn.close()
    
    print("=" * 80)
    print("FIN INSPECTION")
    print("=" * 80)


if __name__ == '__main__':
    inspect_economic_events()
