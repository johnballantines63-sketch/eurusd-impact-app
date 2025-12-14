"""
Ajuster seuils classification selon distribution réelle

Analyse distribution scores empiriques pour définir seuils optimaux

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Ajustement seuils
"""

import duckdb
from pathlib import Path
import pandas as pd
import numpy as np

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def adjust_thresholds():
    """Analyser distribution et ajuster seuils"""
    
    print("=" * 80)
    print("ANALYSE DISTRIBUTION SCORES + AJUSTEMENT SEUILS")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # Créer mapping
    conn.execute("""
    CREATE TEMP TABLE temp_currency_country_map AS
    SELECT * FROM (VALUES
        ('usd', 'US'), ('eur', 'EU'), ('gbp', 'GB'), ('jpy', 'JP'),
        ('cad', 'CA'), ('aud', 'AU'), ('chf', 'CH'), ('nzd', 'NZ')
    ) AS t(currency_code, country_code)
    """)
    
    # ========================================================================
    # 1. ANALYSER DISTRIBUTION SCORES
    # ========================================================================
    
    print("1. DISTRIBUTION SCORES EMPIRIQUES")
    print("=" * 80)
    print()
    
    query_stats = """
    SELECT 
        MIN(empirical_score) as min_score,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY empirical_score) as p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY empirical_score) as median,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY empirical_score) as p75,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY empirical_score) as p90,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY empirical_score) as p95,
        MAX(empirical_score) as max_score
    FROM event_families
    WHERE empirical_score IS NOT NULL
    """
    
    stats = conn.execute(query_stats).df()
    
    print("Statistiques scores :")
    print(f"   Min    : {stats['min_score'].iloc[0]:.1f}")
    print(f"   P25    : {stats['p25'].iloc[0]:.1f}")
    print(f"   Médiane: {stats['median'].iloc[0]:.1f}")
    print(f"   P75    : {stats['p75'].iloc[0]:.1f}")
    print(f"   P90    : {stats['p90'].iloc[0]:.1f}")
    print(f"   P95    : {stats['p95'].iloc[0]:.1f}")
    print(f"   Max    : {stats['max_score'].iloc[0]:.1f}")
    print()
    
    # ========================================================================
    # 2. DISTRIBUTION PAR TRANCHES
    # ========================================================================
    
    print("2. DISTRIBUTION PAR TRANCHES")
    print("=" * 80)
    print()
    
    query_dist = """
    SELECT 
        CASE 
            WHEN empirical_score >= 80 THEN '80-100'
            WHEN empirical_score >= 60 THEN '60-80'
            WHEN empirical_score >= 40 THEN '40-60'
            WHEN empirical_score >= 30 THEN '30-40'
            WHEN empirical_score >= 20 THEN '20-30'
            ELSE '0-20'
        END as score_range,
        COUNT(*) as count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM event_families WHERE empirical_score IS NOT NULL) as pct
    FROM event_families
    WHERE empirical_score IS NOT NULL
    GROUP BY score_range
    ORDER BY score_range DESC
    """
    
    dist = conn.execute(query_dist).df()
    print(dist.to_string())
    print()
    
    # ========================================================================
    # 3. TOP ÉVÉNEMENTS MAJEURS
    # ========================================================================
    
    print("3. TOP 20 ÉVÉNEMENTS PAR SCORE")
    print("=" * 80)
    print()
    
    query_top = """
    SELECT 
        event_key,
        country,
        empirical_score,
        avg_movement_pips
    FROM event_families
    WHERE empirical_score IS NOT NULL
    ORDER BY empirical_score DESC
    LIMIT 20
    """
    
    top = conn.execute(query_top).df()
    print(top.to_string())
    print()
    
    # ========================================================================
    # 4. PROPOSITION SEUILS OPTIMAUX
    # ========================================================================
    
    print("4. PROPOSITION SEUILS")
    print("=" * 80)
    print()
    
    p75 = stats['p75'].iloc[0]
    p90 = stats['p90'].iloc[0]
    median = stats['median'].iloc[0]
    
    print("Basé sur distribution :")
    print()
    print(f"   Option A (Conservateur) :")
    print(f"      HIGH   >= {p90:.1f}  (top 10%)")
    print(f"      MEDIUM >= {median:.1f}  (top 50%)")
    print(f"      LOW    < {median:.1f}")
    print()
    
    print(f"   Option B (Équilibré) :")
    print(f"      HIGH   >= {p75:.1f}  (top 25%)")
    print(f"      MEDIUM >= {median:.1f}  (top 50%)")
    print(f"      LOW    < {median:.1f}")
    print()
    
    print(f"   Option C (Trading Focus - RECOMMANDÉ) :")
    print(f"      HIGH   >= 40  (événements majeurs CPI, NFP, Fed)")
    print(f"      MEDIUM >= 20  (événements significatifs)")
    print(f"      LOW    < 20   (événements mineurs)")
    print()
    
    # Compter 11 septembre avec Option C
    query_sept11_optC = """
    SELECT 
        e.event_name,
        f.empirical_score,
        CASE 
            WHEN f.empirical_score >= 40 THEN 'HIGH'
            WHEN f.empirical_score >= 20 THEN 'MEDIUM'
            ELSE 'LOW'
        END as importance_optC
    FROM economic_events e
    LEFT JOIN temp_currency_country_map m
        ON LOWER(e.country) = m.currency_code
    LEFT JOIN event_families f
        ON REPLACE(LOWER(e.event_name), ' ', '_') = REPLACE(LOWER(f.event_key), ' ', '_')
        AND m.country_code = f.country
    WHERE DATE(e.datetime_utc) = '2025-09-11'
      AND e.country IN ('usd', 'eur')
      AND f.empirical_score IS NOT NULL
    ORDER BY f.empirical_score DESC
    """
    
    sept11_optC = conn.execute(query_sept11_optC).df()
    
    high_count = len(sept11_optC[sept11_optC['importance_optC'] == 'HIGH'])
    
    print(f"   Avec Option C → 11 septembre : {high_count} événements HIGH")
    print()
    
    if high_count > 0:
        print("   Événements HIGH (Option C) :")
        high_events = sept11_optC[sept11_optC['importance_optC'] == 'HIGH']
        for idx, row in high_events.iterrows():
            print(f"      - {row['event_name']} (Score: {row['empirical_score']:.1f})")
        print()
    
    # ========================================================================
    # 5. APPLICATION OPTION C
    # ========================================================================
    
    print("5. APPLICATION OPTION C (RECOMMANDÉE)")
    print("=" * 80)
    print()
    
    user_input = input("Appliquer Option C (HIGH>=40, MED>=20) ? [O/n] : ")
    
    if user_input.lower() in ['', 'o', 'oui', 'y', 'yes']:
        print()
        print("Application en cours...")
        
        # Reset
        conn.execute("UPDATE economic_events SET importance = 'MEDIUM'")
        
        # Reclassifier avec seuils 40/20
        query_reclassify = """
        UPDATE economic_events
        SET importance = (
            SELECT 
                CASE 
                    WHEN f.empirical_score >= 40 THEN 'HIGH'
                    WHEN f.empirical_score >= 20 THEN 'MEDIUM'
                    ELSE 'LOW'
                END
            FROM temp_currency_country_map m
            JOIN event_families f
                ON REPLACE(LOWER(economic_events.event_name), ' ', '_') = REPLACE(LOWER(f.event_key), ' ', '_')
                AND m.country_code = f.country
            WHERE LOWER(economic_events.country) = m.currency_code
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1
            FROM temp_currency_country_map m
            JOIN event_families f
                ON REPLACE(LOWER(economic_events.event_name), ' ', '_') = REPLACE(LOWER(f.event_key), ' ', '_')
                AND m.country_code = f.country
            WHERE LOWER(economic_events.country) = m.currency_code
        )
        """
        
        conn.execute(query_reclassify)
        
        print("✅ Reclassification terminée")
        print()
        
        # Vérification
        query_final_dist = """
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
        
        final_dist = conn.execute(query_final_dist).df()
        print("Distribution finale :")
        print(final_dist.to_string())
        print()
        
        # 11 septembre final
        query_sept11_final = """
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
        ORDER BY datetime_utc
        """
        
        sept11_final = conn.execute(query_sept11_final).df()
        
        print(f"Événements HIGH 11 septembre : {len(sept11_final)}")
        print()
        
        if len(sept11_final) > 0:
            for idx, row in sept11_final.iterrows():
                dt = pd.to_datetime(row['datetime_utc'])
                print(f"   {dt.strftime('%H:%M')} - {row['country'].upper()} - {row['event_name']}")
            print()
            print("✅✅✅ SUCCESS FINAL !")
            print()
            print("Prochaines étapes :")
            print("   python validate_cluster_sept11.py")
            print("   python validate_formula_s115_complete.py")
        
    else:
        print()
        print("Annulé. Ajustez manuellement les seuils si nécessaire.")
    
    print()
    
    conn.close()
    
    print("=" * 80)


if __name__ == '__main__':
    adjust_thresholds()
