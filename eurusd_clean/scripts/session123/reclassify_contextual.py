"""
Ajuster seuil HIGH pour événements EUR contextuels

Logique : Abaisser seuil à >= 15 pour EUR quand proche ECB (±60 min)

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Seuil contextuel EUR
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
CSV_FILE = Path(__file__).parent / 'validation_results' / 'event_families_eodhd_empirical.csv'

def reclassify_with_contextual_threshold():
    """Reclassification avec seuil contextuel EUR"""
    
    print("=" * 80)
    print("RECLASSIFICATION AVEC SEUIL CONTEXTUEL")
    print("=" * 80)
    print()
    
    # Charger scores
    scores_df = pd.read_csv(CSV_FILE)
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    conn.register('scores_empirical', scores_df)
    
    # Reset
    conn.execute("UPDATE economic_events SET importance = 'MEDIUM'")
    print("✅ Reset → MEDIUM")
    print()
    
    # ========================================================================
    # RECLASSIFICATION STANDARD (seuils normaux)
    # ========================================================================
    
    print("RECLASSIFICATION STANDARD :")
    print("-" * 80)
    print()
    
    query_standard = """
    UPDATE economic_events
    SET importance = (
        SELECT 
            CASE 
                WHEN s.empirical_score >= 40 THEN 'HIGH'
                WHEN s.empirical_score >= 20 THEN 'MEDIUM'
                ELSE 'LOW'
            END
        FROM scores_empirical s
        WHERE economic_events.event_name = s.event_name
          AND economic_events.country = s.country
        LIMIT 1
    )
    WHERE EXISTS (
        SELECT 1 FROM scores_empirical s
        WHERE economic_events.event_name = s.event_name
          AND economic_events.country = s.country
    )
    """
    
    conn.execute(query_standard)
    print("✅ Seuils standard appliqués (HIGH >= 40 pips)")
    print()
    
    # ========================================================================
    # RECLASSIFICATION CONTEXTUELLE EUR (seuil abaissé)
    # ========================================================================
    
    print("RECLASSIFICATION CONTEXTUELLE EUR :")
    print("-" * 80)
    print()
    print("Logique : EUR avec score >= 15 pips → HIGH si ±60 min d'un ECB event")
    print()
    
    query_contextual = """
    UPDATE economic_events e
    SET importance = 'HIGH'
    WHERE e.country IN ('eur', 'de', 'fr', 'it', 'es', 'ea')
      AND EXISTS (
          SELECT 1 FROM scores_empirical s
          WHERE e.event_name = s.event_name
            AND (
                -- Match direct
                e.country = s.country
                -- Ou mapper pays EUR vers 'eur' pour scores
                OR (e.country IN ('de', 'fr', 'it', 'es', 'ea') AND s.country = 'eur')
            )
            AND s.empirical_score >= 15  -- Seuil abaissé pour EUR
      )
      AND EXISTS (
          -- Vérifier présence ECB event ±60 min
          SELECT 1 FROM economic_events ecb
          WHERE ecb.country IN ('eur', 'de', 'fr', 'it', 'es', 'ea')
            AND LOWER(ecb.event_name) LIKE '%ecb%'
            AND ecb.importance = 'HIGH'
            AND DATE(ecb.datetime_utc) = DATE(e.datetime_utc)
            AND ABS(EXTRACT(EPOCH FROM (ecb.datetime_utc - e.datetime_utc))) <= 3600
      )
    """
    
    conn.execute(query_contextual)
    print("✅ Seuil contextuel EUR appliqué (HIGH >= 15 pips si proche ECB)")
    print()
    
    # ========================================================================
    # VÉRIFICATION
    # ========================================================================
    
    print("VÉRIFICATION 11 SEPTEMBRE :")
    print("-" * 80)
    print()
    
    query_verify = """
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
    
    high_events = conn.execute(query_verify).df()
    
    print(f"Total HIGH : {len(high_events)}")
    print()
    
    for idx, row in high_events.iterrows():
        dt_utc = pd.to_datetime(row['datetime_utc']).tz_localize('UTC')
        dt_bern = dt_utc.tz_convert('Europe/Zurich')
        print(f"   {dt_bern.strftime('%H:%M')} Bern - {row['country'].upper():3s} - {row['event_name']}")
    
    print()
    
    # Current Account inclus ?
    current_account_high = any(
        'current_account' in row['event_name'].lower() 
        for _, row in high_events.iterrows()
    )
    
    if current_account_high:
        print("✅✅✅ Current Account inclus comme HIGH !")
    else:
        print("⚠️  Current Account toujours MEDIUM")
        print()
        print("Debug : Vérifier si ECB events sont HIGH...")
        
        query_ecb = """
        SELECT datetime_utc, event_name, importance
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-09-11'
          AND LOWER(event_name) LIKE '%ecb%'
        ORDER BY datetime_utc
        """
        
        ecb_events = conn.execute(query_ecb).df()
        print(ecb_events.to_string())
    
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
    
    conn.close()
    
    print("=" * 80)
    print("✅ RECLASSIFICATION CONTEXTUELLE TERMINÉE")
    print("=" * 80)
    print()
    print("Prochaines étapes :")
    print("   python validate_cluster_sept11.py")
    print("   python validate_formula_s115_complete.py")
    print()


if __name__ == '__main__':
    reclassify_with_contextual_threshold()
