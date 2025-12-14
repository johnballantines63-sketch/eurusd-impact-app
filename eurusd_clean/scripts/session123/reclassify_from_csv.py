"""
Reclassifier economic_events depuis CSV

Utilise event_families_eodhd.csv pour reclassifier importance

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Reclassification finale
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
CSV_FILE = Path(__file__).parent / 'validation_results' / 'event_families_eodhd.csv'

def reclassify_from_csv():
    """Reclassifier depuis CSV"""
    
    print("=" * 80)
    print("RECLASSIFICATION DEPUIS CSV")
    print("=" * 80)
    print()
    
    # Charger CSV
    scores_df = pd.read_csv(CSV_FILE)
    
    print(f"CSV chargé : {len(scores_df)} familles")
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # Enregistrer DataFrame dans DuckDB (temporaire)
    conn.register('scores_temp', scores_df)
    
    # Reset
    conn.execute("UPDATE economic_events SET importance = 'MEDIUM'")
    print("✅ Reset → MEDIUM")
    print()
    
    # Reclassifier
    query = """
    UPDATE economic_events
    SET importance = (
        SELECT 
            CASE 
                WHEN s.empirical_score >= 40 THEN 'HIGH'
                WHEN s.empirical_score >= 20 THEN 'MEDIUM'
                ELSE 'LOW'
            END
        FROM scores_temp s
        WHERE economic_events.event_name = s.event_name
          AND economic_events.country = s.country
        LIMIT 1
    )
    WHERE EXISTS (
        SELECT 1 FROM scores_temp s
        WHERE economic_events.event_name = s.event_name
          AND economic_events.country = s.country
    )
    """
    
    conn.execute(query)
    print("✅ Reclassification appliquée")
    print()
    
    # Distribution finale
    query_dist = """
    SELECT 
        importance,
        COUNT(*) as count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM economic_events) as pct
    FROM economic_events
    GROUP BY importance
    ORDER BY 
        CASE importance 
            WHEN 'HIGH' THEN 1 
            WHEN 'MEDIUM' THEN 2 
            WHEN 'LOW' THEN 3 
        END
    """
    
    dist = conn.execute(query_dist).df()
    
    print("DISTRIBUTION FINALE :")
    print(dist.to_string())
    print()
    
    # Vérification 11 septembre
    query_sept11 = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND importance = 'HIGH'
    ORDER BY datetime_utc
    """
    
    sept11 = conn.execute(query_sept11).df()
    
    print(f"ÉVÉNEMENTS HIGH 11 SEPTEMBRE : {len(sept11)}")
    print()
    
    if len(sept11) > 0:
        for idx, row in sept11.iterrows():
            dt = pd.to_datetime(row['datetime_utc'])
            print(f"   {dt.strftime('%H:%M')} - {row['country'].upper()} - {row['event_name']}")
        print()
        print("✅✅✅ SUCCESS !")
    else:
        print("⚠️  Aucun HIGH détecté")
    
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ RECLASSIFICATION TERMINÉE")
    print("=" * 80)
    print()
    print("Prochaines étapes :")
    print("   python validate_cluster_sept11.py")
    print("   python validate_formula_s115_complete.py")
    print()


if __name__ == '__main__':
    reclassify_from_csv()
