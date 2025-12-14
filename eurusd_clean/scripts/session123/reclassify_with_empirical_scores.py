"""
Reclassification importance basée sur SCORES EMPIRIQUES

Méthodologie :
1. JOIN economic_events avec event_families par event_name normalisé
2. Reclassifier selon empirical_score :
   - HIGH   : score >= 60 (événements majeurs)
   - MEDIUM : score >= 30 (événements importants)
   - LOW    : score < 30  (événements mineurs)
3. Conserver MEDIUM par défaut si pas de match

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Reclassification scientifique
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def reclassify_with_empirical_scores():
    """Reclassifier importance selon scores empiriques"""
    
    print("=" * 80)
    print("RECLASSIFICATION BASÉE SUR SCORES EMPIRIQUES")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # ========================================================================
    # 1. ANALYSER DISTRIBUTION SCORES
    # ========================================================================
    
    print("1. DISTRIBUTION SCORES EMPIRIQUES")
    print("=" * 80)
    print()
    
    query_dist = """
    SELECT 
        CASE 
            WHEN empirical_score >= 80 THEN '80-100 (Extrême)'
            WHEN empirical_score >= 60 THEN '60-80  (Très élevé)'
            WHEN empirical_score >= 40 THEN '40-60  (Élevé)'
            WHEN empirical_score >= 20 THEN '20-40  (Moyen)'
            ELSE '0-20   (Faible)'
        END as score_range,
        COUNT(*) as count,
        AVG(avg_movement_pips) as avg_pips
    FROM event_families
    GROUP BY score_range
    ORDER BY score_range DESC
    """
    
    dist = conn.execute(query_dist).df()
    print(dist.to_string())
    print()
    
    # ========================================================================
    # 2. SEUILS PROPOSÉS
    # ========================================================================
    
    print("2. SEUILS CLASSIFICATION")
    print("=" * 80)
    print()
    
    print("Basé sur distribution empirique :")
    print()
    print("   HIGH   : empirical_score >= 60  (très fort impact)")
    print("   MEDIUM : empirical_score >= 30  (impact significatif)")
    print("   LOW    : empirical_score < 30   (impact faible)")
    print()
    print("   Par défaut (sans match) : MEDIUM")
    print()
    
    # Compter combien d'events dans chaque catégorie
    query_counts = """
    SELECT 
        CASE 
            WHEN empirical_score >= 60 THEN 'HIGH'
            WHEN empirical_score >= 30 THEN 'MEDIUM'
            ELSE 'LOW'
        END as new_importance,
        COUNT(*) as families_count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM event_families) as pct
    FROM event_families
    GROUP BY new_importance
    ORDER BY new_importance
    """
    
    counts = conn.execute(query_counts).df()
    print("Répartition families :")
    print(counts.to_string())
    print()
    
    # ========================================================================
    # 3. BACKUP TABLE
    # ========================================================================
    
    print("3. BACKUP TABLE")
    print("=" * 80)
    print()
    
    # Drop backup si existe
    conn.execute("DROP TABLE IF EXISTS economic_events_backup_importance")
    
    # Créer backup
    conn.execute("""
    CREATE TABLE economic_events_backup_importance AS 
    SELECT * FROM economic_events
    """)
    
    print("✅ Backup créé : economic_events_backup_importance")
    print()
    
    # ========================================================================
    # 4. RECLASSIFICATION
    # ========================================================================
    
    print("4. RECLASSIFICATION EN COURS...")
    print("=" * 80)
    print()
    
    # Stratégie : UPDATE avec CTE pour JOIN
    query_update = """
    UPDATE economic_events
    SET importance = (
        SELECT 
            CASE 
                WHEN f.empirical_score >= 60 THEN 'HIGH'
                WHEN f.empirical_score >= 30 THEN 'MEDIUM'
                ELSE 'LOW'
            END
        FROM event_families f
        WHERE LOWER(REPLACE(economic_events.event_name, ' ', '_')) = LOWER(f.event_key)
          AND LOWER(economic_events.country) = LOWER(f.country)
        LIMIT 1
    )
    WHERE EXISTS (
        SELECT 1 FROM event_families f
        WHERE LOWER(REPLACE(economic_events.event_name, ' ', '_')) = LOWER(f.event_key)
          AND LOWER(economic_events.country) = LOWER(f.country)
    )
    """
    
    result = conn.execute(query_update)
    
    print("✅ Reclassification terminée")
    print()
    
    # ========================================================================
    # 5. VÉRIFICATION NOUVELLE DISTRIBUTION
    # ========================================================================
    
    print("5. NOUVELLE DISTRIBUTION IMPORTANCE")
    print("=" * 80)
    print()
    
    query_new_dist = """
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
            ELSE 4 
        END
    """
    
    new_dist = conn.execute(query_new_dist).df()
    print(new_dist.to_string())
    print()
    
    # ========================================================================
    # 6. ÉVÉNEMENTS 11 SEPTEMBRE HIGH
    # ========================================================================
    
    print("6. ÉVÉNEMENTS 11 SEPTEMBRE - HIGH IMPORTANCE")
    print("=" * 80)
    print()
    
    query_sept11_high = """
    SELECT 
        e.datetime_utc,
        e.event_name,
        e.country,
        e.importance,
        e.actual,
        e.forecast,
        e.previous,
        f.empirical_score,
        f.avg_movement_pips
    FROM economic_events e
    LEFT JOIN event_families f 
        ON LOWER(REPLACE(e.event_name, ' ', '_')) = LOWER(f.event_key)
        AND LOWER(e.country) = LOWER(f.country)
    WHERE DATE(e.datetime_utc) = '2025-09-11'
      AND e.importance = 'HIGH'
      AND e.country IN ('usd', 'eur')
    ORDER BY e.datetime_utc
    """
    
    sept11_high = conn.execute(query_sept11_high).df()
    
    if len(sept11_high) > 0:
        print(f"✅ {len(sept11_high)} événements HIGH détectés")
        print()
        
        # Formater pour affichage
        for idx, row in sept11_high.iterrows():
            dt = pd.to_datetime(row['datetime_utc'])
            print(f"   {dt.strftime('%H:%M')} UTC - {row['country'].upper()}")
            print(f"      {row['event_name']}")
            print(f"      Score: {row['empirical_score']:.1f} | Avg impact: {row['avg_movement_pips']:.1f} pips")
            print(f"      Actual: {row['actual']} | Forecast: {row['forecast']} | Previous: {row['previous']}")
            print()
    else:
        print("⚠️  Aucun événement HIGH USD/EUR le 11 septembre")
        print()
        print("Vérification événements disponibles...")
        
        query_sept11_all = """
        SELECT importance, COUNT(*) as count
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-09-11'
        GROUP BY importance
        """
        
        all_dist = conn.execute(query_sept11_all).df()
        print(all_dist.to_string())
        print()
    
    # ========================================================================
    # 7. TOP EVENTS PAR SCORE (sample validation)
    # ========================================================================
    
    print("7. ÉCHANTILLON ÉVÉNEMENTS RECLASSIFIÉS")
    print("=" * 80)
    print()
    
    query_sample = """
    SELECT 
        e.event_name,
        e.country,
        e.importance,
        f.empirical_score,
        f.avg_movement_pips,
        COUNT(*) as occurrences
    FROM economic_events e
    LEFT JOIN event_families f 
        ON LOWER(REPLACE(e.event_name, ' ', '_')) = LOWER(f.event_key)
        AND LOWER(e.country) = LOWER(f.country)
    WHERE e.importance = 'HIGH'
      AND f.empirical_score IS NOT NULL
    GROUP BY e.event_name, e.country, e.importance, f.empirical_score, f.avg_movement_pips
    ORDER BY f.empirical_score DESC
    LIMIT 10
    """
    
    sample = conn.execute(query_sample).df()
    print("TOP 10 événements HIGH (par score empirique) :")
    print()
    print(sample.to_string())
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ RECLASSIFICATION TERMINÉE")
    print("=" * 80)
    print()
    print("Prochaines étapes :")
    print("   1. python validate_cluster_sept11.py")
    print("   2. python validate_formula_s115_complete.py")
    print()


if __name__ == '__main__':
    reclassify_with_empirical_scores()
