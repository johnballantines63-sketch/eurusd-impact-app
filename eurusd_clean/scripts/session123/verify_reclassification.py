"""
Vérifier si reclassification a fonctionné

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Diagnostic reclassification
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def verify_reclassification():
    """Vérifier si événements 11 sept sont bien HIGH"""
    
    print("=" * 80)
    print("VÉRIFICATION RECLASSIFICATION 11 SEPTEMBRE")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ========================================================================
    # 1. DISTRIBUTION GLOBALE
    # ========================================================================
    
    print("1. DISTRIBUTION GLOBALE IMPORTANCE")
    print("=" * 80)
    print()
    
    query_dist = """
    SELECT 
        importance,
        COUNT(*) as count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM economic_events) as pct
    FROM economic_events
    GROUP BY importance
    ORDER BY count DESC
    """
    
    dist = conn.execute(query_dist).df()
    print(dist.to_string())
    print()
    
    # ========================================================================
    # 2. ÉVÉNEMENTS 11 SEPTEMBRE PAR IMPORTANCE
    # ========================================================================
    
    print("2. ÉVÉNEMENTS 11 SEPTEMBRE PAR IMPORTANCE")
    print("=" * 80)
    print()
    
    query_sept11_dist = """
    SELECT 
        importance,
        COUNT(*) as count
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
    GROUP BY importance
    ORDER BY count DESC
    """
    
    sept11_dist = conn.execute(query_sept11_dist).df()
    print(sept11_dist.to_string())
    print()
    
    # ========================================================================
    # 3. ÉVÉNEMENTS HIGH 11 SEPTEMBRE DÉTAIL
    # ========================================================================
    
    print("3. ÉVÉNEMENTS HIGH 11 SEPTEMBRE (USD/EUR)")
    print("=" * 80)
    print()
    
    query_high = """
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
      AND importance = 'HIGH'
      AND country IN ('usd', 'eur')
    ORDER BY datetime_utc
    """
    
    high_events = conn.execute(query_high).df()
    
    if len(high_events) > 0:
        print(f"✅ {len(high_events)} événements HIGH USD/EUR")
        print()
        print(high_events.to_string())
    else:
        print("❌ AUCUN événement HIGH USD/EUR trouvé")
        print()
        print("Vérification événements USD/EUR disponibles :")
        
        query_usd_eur = """
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
          AND country IN ('usd', 'eur')
          AND HOUR(datetime_utc) = 12
        ORDER BY datetime_utc
        """
        
        usd_eur = conn.execute(query_usd_eur).df()
        print(usd_eur.to_string())
    
    print()
    
    # ========================================================================
    # 4. TEST JOIN event_families
    # ========================================================================
    
    print("4. TEST JOIN AVEC event_families")
    print("=" * 80)
    print()
    
    query_join_test = """
    SELECT 
        e.event_name,
        e.country,
        e.importance,
        f.event_key,
        f.empirical_score,
        f.avg_movement_pips
    FROM economic_events e
    LEFT JOIN event_families f 
        ON LOWER(REPLACE(e.event_name, ' ', '_')) = LOWER(f.event_key)
        AND LOWER(e.country) = LOWER(f.country)
    WHERE DATE(e.datetime_utc) = '2025-09-11'
      AND e.country IN ('usd', 'eur')
      AND HOUR(e.datetime_utc) = 12
    ORDER BY f.empirical_score DESC NULLS LAST
    """
    
    join_test = conn.execute(query_join_test).df()
    
    print("Événements 12h UTC avec scores empiriques :")
    print()
    print(join_test.to_string())
    print()
    
    matched = len(join_test[join_test['empirical_score'].notna()])
    total = len(join_test)
    
    print(f"Match rate : {matched}/{total} ({matched/total*100:.1f}%)")
    print()
    
    if matched == 0:
        print("❌ AUCUN MATCH ENTRE economic_events ET event_families")
        print()
        print("Problème : Noms événements ne correspondent pas")
        print()
        print("Échantillon event_families pour comparaison :")
        
        query_families_sample = """
        SELECT event_key, country, empirical_score
        FROM event_families
        WHERE country IN ('US', 'EU')
          AND empirical_score >= 60
        ORDER BY empirical_score DESC
        LIMIT 10
        """
        
        families = conn.execute(query_families_sample).df()
        print(families.to_string())
        print()
    
    conn.close()
    
    print("=" * 80)


if __name__ == '__main__':
    verify_reclassification()
