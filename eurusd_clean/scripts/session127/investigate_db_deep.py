#!/usr/bin/env python3
"""
SESSION 127 - INVESTIGATION APPROFONDIE DB
==========================================
Examiner structure DB events pour comprendre mapping event_key

Objectif : Vérifier si DB contient variantes (_mom, _yoy, _qoq)

Auteur : André Valentin
Date : 11 novembre 2025
"""
import duckdb
import pandas as pd
from pathlib import Path


DB_PATH = Path(__file__).parents[2] / 'data' / 'warehouse.duckdb'
CSV_PATH = Path(__file__).parents[1] / 'session123' / 'validation_results' / 'event_families_eodhd_empirical.csv'


def analyze_db_structure():
    """Analyser structure complète table events"""
    
    print("=" * 80)
    print("INVESTIGATION APPROFONDIE - DB WAREHOUSE.DUCKDB")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ========================================================================
    # 1. STRUCTURE TABLE EVENTS
    # ========================================================================
    
    print("[1] STRUCTURE TABLE EVENTS")
    print("-" * 80)
    
    schema_query = "DESCRIBE events"
    schema = conn.execute(schema_query).df()
    
    print(schema.to_string(index=False))
    print()
    
    # Statistiques globales
    stats_query = """
    SELECT 
        COUNT(*) as total_events,
        COUNT(DISTINCT event_key) as unique_event_keys,
        COUNT(DISTINCT country) as unique_countries,
        MIN(date) as min_date,
        MAX(date) as max_date
    FROM events
    """
    
    stats = conn.execute(stats_query).df()
    print("STATISTIQUES GLOBALES :")
    print(stats.to_string(index=False))
    print()
    print()
    
    # ========================================================================
    # 2. EVENT_KEY AVEC SUFFIXES VARIANTES (US)
    # ========================================================================
    
    print("[2] EVENT_KEY AVEC SUFFIXES VARIANTES (country='US')")
    print("-" * 80)
    
    suffixes = ['_mom', '_yoy', '_qoq', ' mom', ' yoy', ' qoq', '_adv']
    
    for suffix in suffixes:
        query = f"""
        SELECT DISTINCT 
            event_key,
            importance_n,
            COUNT(*) as event_count
        FROM events
        WHERE country = 'US'
          AND LOWER(event_key) LIKE '%{suffix}%'
        GROUP BY event_key, importance_n
        ORDER BY event_count DESC
        LIMIT 10
        """
        
        result = conn.execute(query).df()
        
        if len(result) > 0:
            print(f"\n✅ Suffixe '{suffix}' : {len(result)} event_key trouvés")
            print()
            for _, row in result.iterrows():
                imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
                print(f"  → {row['event_key']:<50} [{imp}] (n={row['event_count']})")
        else:
            print(f"❌ Suffixe '{suffix}' : 0 event_key trouvé")
    
    print()
    print()
    
    # ========================================================================
    # 3. FAMILLE INFLATION (exemple détaillé)
    # ========================================================================
    
    print("[3] EXEMPLE DÉTAILLÉ : FAMILLE INFLATION")
    print("-" * 80)
    
    inflation_query = """
    SELECT DISTINCT 
        event_key,
        importance_n,
        COUNT(*) as event_count
    FROM events
    WHERE country = 'US'
      AND LOWER(event_key) LIKE '%inflation%'
    GROUP BY event_key, importance_n
    ORDER BY event_count DESC
    """
    
    inflation_result = conn.execute(inflation_query).df()
    
    print(f"Total event_key inflation US : {len(inflation_result)}")
    print()
    
    for _, row in inflation_result.iterrows():
        imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
        print(f"  {row['event_key']:<60} [{imp}] (n={row['event_count']})")
    
    print()
    print()
    
    # ========================================================================
    # 4. FAMILLE GDP (exemple détaillé)
    # ========================================================================
    
    print("[4] EXEMPLE DÉTAILLÉ : FAMILLE GDP")
    print("-" * 80)
    
    gdp_query = """
    SELECT DISTINCT 
        event_key,
        importance_n,
        COUNT(*) as event_count
    FROM events
    WHERE country = 'US'
      AND (
        LOWER(event_key) LIKE '%gdp%'
        OR LOWER(event_key) LIKE '%gross%domestic%'
      )
    GROUP BY event_key, importance_n
    ORDER BY event_count DESC
    """
    
    gdp_result = conn.execute(gdp_query).df()
    
    print(f"Total event_key GDP US : {len(gdp_result)}")
    print()
    
    for _, row in gdp_result.iterrows():
        imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
        print(f"  {row['event_key']:<60} [{imp}] (n={row['event_count']})")
    
    print()
    print()
    
    # ========================================================================
    # 5. FAMILLE RETAIL SALES (exemple détaillé)
    # ========================================================================
    
    print("[5] EXEMPLE DÉTAILLÉ : FAMILLE RETAIL SALES")
    print("-" * 80)
    
    retail_query = """
    SELECT DISTINCT 
        event_key,
        importance_n,
        COUNT(*) as event_count
    FROM events
    WHERE country = 'US'
      AND LOWER(event_key) LIKE '%retail%sales%'
    GROUP BY event_key, importance_n
    ORDER BY event_count DESC
    """
    
    retail_result = conn.execute(retail_query).df()
    
    print(f"Total event_key retail sales US : {len(retail_result)}")
    print()
    
    for _, row in retail_result.iterrows():
        imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
        print(f"  {row['event_key']:<60} [{imp}] (n={row['event_count']})")
    
    print()
    print()
    
    # ========================================================================
    # 6. COMPARAISON DB ↔ CSV SCORES
    # ========================================================================
    
    print("[6] COMPARAISON DB ↔ CSV SCORES")
    print("-" * 80)
    
    # Charger CSV scores
    if not CSV_PATH.exists():
        print(f"⚠️  CSV scores introuvable : {CSV_PATH}")
    else:
        df_scores = pd.read_csv(CSV_PATH)
        df_scores_usd = df_scores[df_scores['country'] == 'usd']
        
        print(f"CSV scores USD : {len(df_scores_usd)} lignes")
        print()
        
        # Exemples comparaison
        test_cases = [
            'inflation_rate',
            'inflation_rate_mom',
            'core_inflation_rate',
            'gdp_growth_rate',
            'gdp_growth_rate_qoq',
            'retail_sales',
            'retail_sales_mom'
        ]
        
        print("RECHERCHE EVENT_NAME DANS CSV :")
        print()
        
        for event_name in test_cases:
            match = df_scores_usd[df_scores_usd['event_name'] == event_name]
            if len(match) > 0:
                score = match.iloc[0]['empirical_score']
                print(f"  ✅ CSV : {event_name:<40} score={score:.2f}")
            else:
                print(f"  ❌ CSV : {event_name:<40} INTROUVABLE")
        
        print()
        print()
        
        # Chercher correspondance dans DB
        print("RECHERCHE EVENT_KEY CORRESPONDANTS DANS DB :")
        print()
        
        for event_name in test_cases:
            # Convertir event_name → event_key (underscore → space)
            event_key_search = event_name.replace('_', ' ')
            
            query = f"""
            SELECT DISTINCT event_key, importance_n, COUNT(*) as cnt
            FROM events
            WHERE country = 'US'
              AND event_key = '{event_key_search}'
            GROUP BY event_key, importance_n
            """
            
            result = conn.execute(query).df()
            
            if len(result) > 0:
                imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[result.iloc[0]['importance_n']]
                cnt = result.iloc[0]['cnt']
                print(f"  ✅ DB  : '{event_key_search}'")
                print(f"           importance={imp}, count={cnt}")
            else:
                print(f"  ❌ DB  : '{event_key_search}' INTROUVABLE")
            
            print()
    
    print()
    
    # ========================================================================
    # 7. SYNTHÈSE DÉCOUVERTES
    # ========================================================================
    
    print("=" * 80)
    print("SYNTHÈSE DÉCOUVERTES")
    print("=" * 80)
    print()
    
    # Compter total event_key avec variantes
    total_variants = 0
    for suffix in ['_mom', '_yoy', '_qoq', ' mom', ' yoy', ' qoq']:
        query = f"""
        SELECT COUNT(DISTINCT event_key) as cnt
        FROM events
        WHERE country = 'US'
          AND LOWER(event_key) LIKE '%{suffix}%'
        """
        result = conn.execute(query).fetchone()
        total_variants += result[0] if result else 0
    
    # Total event_key US
    total_query = """
    SELECT COUNT(DISTINCT event_key) as cnt
    FROM events
    WHERE country = 'US'
    """
    total_us = conn.execute(total_query).fetchone()[0]
    
    print(f"Total event_key US               : {total_us}")
    print(f"Event_key avec variantes (_mom..): {total_variants}")
    print(f"% variantes                      : {total_variants/total_us*100:.1f}%")
    print()
    
    if total_variants > 0:
        print("✅ LA DB CONTIENT DES VARIANTES")
        print()
        print("Conclusion :")
        print("  - event_key DB a suffixes : 'inflation rate_mom', 'gdp growth rate_qoq', etc.")
        print("  - event_name CSV est BASE : 'inflation_rate', 'gdp_growth_rate', etc.")
        print()
        print("⚠️  CORRECTION NÉCESSAIRE :")
        print("  - strip_variant_suffix() pour mapper event_key → event_name_base")
    else:
        print("❌ LA DB NE CONTIENT PAS DE VARIANTES")
        print()
        print("Conclusion :")
        print("  - event_key DB sans suffixes")
        print("  - Mapping direct possible")
    
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ INVESTIGATION COMPLÉTÉE")
    print("=" * 80)


if __name__ == "__main__":
    analyze_db_structure()
