"""
DIAGNOSTIC JOIN FAILURE - Comprendre mismatch event_key
Session 137 - Pourquoi 0 résultats ?

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"

def diagnose_join_failure():
    """Comprendre pourquoi JOIN events <-> event_families retourne 0 résultats"""
    
    print("="*80)
    print("DIAGNOSTIC JOIN FAILURE")
    print("="*80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Prendre 5 événements HIGH réels
    print("\n1. Exemples event_key dans events (HIGH):")
    print("-" * 80)
    
    query_events = """
    SELECT event_key, country, event_title, importance_n
    FROM events
    WHERE importance_n = 3
    LIMIT 5
    """
    df_events = conn.execute(query_events).df()
    print(df_events.to_string(index=False))
    
    # 2. Prendre 5 event_key dans event_families
    print("\n2. Exemples event_key dans event_families:")
    print("-" * 80)
    
    query_families = """
    SELECT event_key, country, empirical_score
    FROM event_families
    LIMIT 5
    """
    df_families = conn.execute(query_families).df()
    print(df_families.to_string(index=False))
    
    # 3. Compter événements HIGH par pays
    print("\n3. Distribution événements HIGH par pays:")
    print("-" * 80)
    
    query_country = """
    SELECT country, COUNT(*) as count
    FROM events
    WHERE importance_n = 3
    GROUP BY country
    ORDER BY count DESC
    LIMIT 10
    """
    df_country = conn.execute(query_country).df()
    print(df_country.to_string(index=False))
    
    # 4. Tester JOIN avec event_key spécifique
    print("\n4. Test JOIN avec 1er event_key spécifique:")
    print("-" * 80)
    
    if len(df_events) > 0:
        test_key = df_events.iloc[0]['event_key']
        test_country = df_events.iloc[0]['country']
        
        print(f"Test: event_key = '{test_key}', country = '{test_country}'")
        
        query_test = """
        SELECT f.event_key, f.country, f.empirical_score
        FROM event_families f
        WHERE f.event_key = ? AND f.country = ?
        """
        
        df_test = conn.execute(query_test, [test_key, test_country]).df()
        
        if len(df_test) > 0:
            print(f"✅ MATCH TROUVÉ :")
            print(df_test.to_string(index=False))
        else:
            print(f"❌ AUCUN MATCH")
            print(f"\n   Chercher event_key similaires dans event_families:")
            
            # Recherche partielle
            query_partial = """
            SELECT event_key, country, empirical_score
            FROM event_families
            WHERE event_key LIKE ?
            LIMIT 5
            """
            
            df_partial = conn.execute(query_partial, [f"%{test_key[:20]}%"]).df()
            
            if len(df_partial) > 0:
                print(df_partial.to_string(index=False))
            else:
                print(f"   Aucun event_key similaire trouvé")
    
    # 5. Comparer clés primaires
    print("\n5. Vérification clés primaires:")
    print("-" * 80)
    
    # Clé primaire event_families
    print("event_families : (event_key, country)")
    
    # Événements US HIGH
    query_us_high = """
    SELECT COUNT(DISTINCT event_key) as distinct_keys
    FROM events
    WHERE importance_n = 3 AND country = 'US'
    """
    us_high_keys = conn.execute(query_us_high).fetchone()[0]
    
    # event_families US
    query_ef_us = """
    SELECT COUNT(DISTINCT event_key) as distinct_keys
    FROM event_families
    WHERE country = 'US'
    """
    ef_us_keys = conn.execute(query_ef_us).fetchone()[0]
    
    print(f"\nevent_key distincts US HIGH (events)       : {us_high_keys}")
    print(f"event_key distincts US (event_families)    : {ef_us_keys}")
    print(f"Overlap potentiel                          : ? (à vérifier)")
    
    conn.close()
    
    # 6. Recommandation
    print("\n" + "="*80)
    print("RECOMMANDATION")
    print("="*80)
    
    print("\nSi AUCUN MATCH trouvé:")
    print("   → Les event_key sont DIFFÉRENTS entre tables")
    print("   → Utiliser CSV Session 127 (mapping variantes)")
    print("   → OU normaliser event_key avant JOIN")
    
    print("\nSi QUELQUES MATCH trouvés:")
    print("   → JOIN partiel possible")
    print("   → Compléter avec CSV Session 127 pour manquants")

if __name__ == "__main__":
    diagnose_join_failure()
