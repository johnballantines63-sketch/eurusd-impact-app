"""
Reclassification avec MAPPING DEVISE → PAYS

Erreur identifiée :
- economic_events.country = DEVISE ('usd', 'eur')
- event_families.country = PAYS ('US', 'EU')

Solution : Mapper devises → pays avant JOIN

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Fix mapping devise/pays
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def reclassify_with_currency_mapping():
    """Reclassification avec mapping devise→pays correct"""
    
    print("=" * 80)
    print("RECLASSIFICATION AVEC MAPPING DEVISE→PAYS")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # ========================================================================
    # 1. CRÉER TABLE MAPPING DEVISE→PAYS
    # ========================================================================
    
    print("1. CRÉATION MAPPING DEVISE→PAYS")
    print("=" * 80)
    print()
    
    conn.execute("DROP TABLE IF EXISTS temp_currency_country_map")
    
    # Mapping devise → pays
    mapping = """
    CREATE TEMP TABLE temp_currency_country_map AS
    SELECT * FROM (VALUES
        ('usd', 'US'),
        ('eur', 'EU'),
        ('gbp', 'GB'),
        ('jpy', 'JP'),
        ('cad', 'CA'),
        ('aud', 'AU'),
        ('chf', 'CH'),
        ('nzd', 'NZ'),
        ('sek', 'SE'),
        ('nok', 'NO'),
        ('dkk', 'DK'),
        ('pln', 'PL'),
        ('czk', 'CZ'),
        ('huf', 'HU'),
        ('ron', 'RO'),
        ('try', 'TR'),
        ('zar', 'ZA'),
        ('mxn', 'MX'),
        ('brl', 'BR'),
        ('inr', 'IN'),
        ('cny', 'CN'),
        ('krw', 'KR'),
        ('sgd', 'SG'),
        ('hkd', 'HK'),
        ('thb', 'TH'),
        ('myr', 'MY'),
        ('idr', 'ID'),
        ('php', 'PH')
    ) AS t(currency_code, country_code)
    """
    
    conn.execute(mapping)
    
    print("✅ Mapping créé")
    print()
    
    # Vérifier
    query_check = """
    SELECT * FROM temp_currency_country_map
    ORDER BY currency_code
    LIMIT 10
    """
    
    map_sample = conn.execute(query_check).df()
    print("Échantillon mapping :")
    print(map_sample.to_string())
    print()
    
    # ========================================================================
    # 2. TEST JOIN AVEC MAPPING
    # ========================================================================
    
    print("2. TEST JOIN AVEC MAPPING")
    print("=" * 80)
    print()
    
    query_test = """
    SELECT 
        e.event_name,
        e.country as currency,
        m.country_code as country,
        f.event_key,
        f.empirical_score,
        f.avg_movement_pips
    FROM economic_events e
    LEFT JOIN temp_currency_country_map m
        ON LOWER(e.country) = m.currency_code
    LEFT JOIN event_families f
        ON REPLACE(LOWER(e.event_name), ' ', '_') = REPLACE(LOWER(f.event_key), ' ', '_')
        AND m.country_code = f.country
    WHERE DATE(e.datetime_utc) = '2025-09-11'
      AND e.country IN ('usd', 'eur')
      AND HOUR(e.datetime_utc) = 12
    ORDER BY f.empirical_score DESC NULLS LAST
    """
    
    test = conn.execute(query_test).df()
    
    matched = len(test[test['empirical_score'].notna()])
    total_test = len(test)
    
    print(f"Match rate : {matched}/{total_test} ({matched/total_test*100:.1f}%)")
    print()
    
    if matched > 0:
        print("✅✅✅ MAPPING FONCTIONNE !")
        print()
        print("Événements matchés :")
        matched_events = test[test['empirical_score'].notna()]
        for idx, row in matched_events.iterrows():
            print(f"   {row['event_name']} ({row['currency']}) → {row['event_key']} | Score: {row['empirical_score']:.1f}")
        print()
    else:
        print("⚠️  Toujours aucun match")
        print()
        print("Debug - Événements EODHD normalisés :")
        for idx, row in test.head(5).iterrows():
            normalized = row['event_name'].lower().replace(' ', '_')
            print(f"   {row['event_name']} → {normalized}")
        print()
        
        print("Debug - event_families disponibles (US) :")
        query_families = """
        SELECT event_key, empirical_score
        FROM event_families
        WHERE country = 'US'
        ORDER BY empirical_score DESC
        LIMIT 5
        """
        families = conn.execute(query_families).df()
        for idx, row in families.iterrows():
            normalized = row['event_key'].lower().replace(' ', '_')
            print(f"   {row['event_key']} → {normalized}")
        print()
    
    # ========================================================================
    # 3. RECLASSIFICATION SI MATCH OK
    # ========================================================================
    
    if matched > 0:
        print("3. RECLASSIFICATION")
        print("=" * 80)
        print()
        
        # Reset
        conn.execute("UPDATE economic_events SET importance = 'MEDIUM'")
        print("✅ Reset → MEDIUM")
        print()
        
        # Reclassifier avec mapping
        query_reclassify = """
        UPDATE economic_events
        SET importance = (
            SELECT 
                CASE 
                    WHEN f.empirical_score >= 60 THEN 'HIGH'
                    WHEN f.empirical_score >= 30 THEN 'MEDIUM'
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
        print("✅ Reclassification appliquée")
        print()
        
        # Vérification
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
        print("Distribution :")
        print(dist.to_string())
        print()
        
        # 11 septembre HIGH
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
          AND importance = 'HIGH'
        ORDER BY datetime_utc
        """
        
        sept11_high = conn.execute(query_sept11).df()
        
        print(f"Événements HIGH 11 septembre : {len(sept11_high)}")
        print()
        
        if len(sept11_high) > 0:
            for idx, row in sept11_high.iterrows():
                dt = pd.to_datetime(row['datetime_utc'])
                print(f"   {dt.strftime('%H:%M')} - {row['country'].upper()} - {row['event_name']}")
            print()
            print("✅✅✅ SUCCESS COMPLET !")
        
    else:
        print("3. RECLASSIFICATION ANNULÉE")
        print("=" * 80)
        print()
        print("Le mapping ne résout pas le problème.")
        print("Fallback nécessaire : classification manuelle par patterns")
    
    conn.close()
    
    print("=" * 80)


if __name__ == '__main__':
    reclassify_with_currency_mapping()
