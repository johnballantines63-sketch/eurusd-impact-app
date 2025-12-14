"""
Debug Current Account matching détaillé

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Debug matching
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
CSV_FILE = Path(__file__).parent / 'validation_results' / 'event_families_eodhd_empirical.csv'

def debug_current_account_matching():
    """Debug matching Current Account"""
    
    print("=" * 80)
    print("DEBUG CURRENT ACCOUNT MATCHING")
    print("=" * 80)
    print()
    
    # Charger CSV
    scores_df = pd.read_csv(CSV_FILE)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    conn.register('scores_empirical', scores_df)
    
    # ========================================================================
    # 1. CURRENT ACCOUNT DANS DB
    # ========================================================================
    
    print("1. CURRENT ACCOUNT DANS DB (11 septembre) :")
    print("-" * 80)
    print()
    
    query_db = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND LOWER(event_name) LIKE '%current%account%'
    """
    
    db_ca = conn.execute(query_db).df()
    print(db_ca.to_string())
    print()
    
    # ========================================================================
    # 2. CURRENT ACCOUNT DANS CSV
    # ========================================================================
    
    print("2. CURRENT ACCOUNT DANS CSV SCORES :")
    print("-" * 80)
    print()
    
    csv_ca = scores_df[scores_df['event_name'].str.contains('current.*account', case=False, na=False)]
    print(csv_ca[['event_name', 'country', 'empirical_score', 'sample_size']].to_string())
    print()
    
    # ========================================================================
    # 3. TEST MAPPING MANUEL
    # ========================================================================
    
    print("3. TEST MAPPING 'de' → 'eur' :")
    print("-" * 80)
    print()
    
    # Current Account DE
    ca_de_name = 'current_account'
    ca_de_country = 'de'
    
    # Score EUR correspondant
    ca_eur_score = scores_df[
        (scores_df['event_name'] == ca_de_name) & 
        (scores_df['country'] == 'eur')
    ]
    
    if len(ca_eur_score) > 0:
        score = ca_eur_score.iloc[0]['empirical_score']
        print(f"✅ Score trouvé : current_account 'eur' = {score:.1f} pips")
        print(f"   Seuil contextuel : >= 15 pips")
        print(f"   Match : {score >= 15} ✅" if score >= 15 else f"   Match : {score >= 15} ❌")
    else:
        print("❌ Aucun score 'current_account' 'eur' trouvé")
    
    print()
    
    # ========================================================================
    # 4. VÉRIFIER PRÉSENCE ECB HIGH
    # ========================================================================
    
    print("4. VÉRIFIER ECB HIGH ±60 MIN :")
    print("-" * 80)
    print()
    
    # Current Account timestamp
    ca_timestamp = '2025-09-11 12:45:00'  # UTC
    
    query_ecb = """
    SELECT 
        datetime_utc,
        event_name,
        importance,
        ABS(EXTRACT(EPOCH FROM (datetime_utc - TIMESTAMP '2025-09-11 12:45:00'))) as delta_seconds
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND LOWER(event_name) LIKE '%ecb%'
      AND importance = 'HIGH'
      AND ABS(EXTRACT(EPOCH FROM (datetime_utc - TIMESTAMP '2025-09-11 12:45:00'))) <= 3600
    ORDER BY delta_seconds
    """
    
    ecb_nearby = conn.execute(query_ecb).df()
    
    if len(ecb_nearby) > 0:
        print(f"✅ {len(ecb_nearby)} ECB HIGH events dans ±60 min :")
        print()
        print(ecb_nearby.to_string())
    else:
        print("❌ Aucun ECB HIGH dans ±60 min")
    
    print()
    
    # ========================================================================
    # 5. TEST REQUÊTE COMPLÈTE MANUELLEMENT
    # ========================================================================
    
    print("5. TEST REQUÊTE CONTEXTUELLE MANUELLEMENT :")
    print("-" * 80)
    print()
    
    query_test = """
    SELECT 
        e.datetime_utc,
        e.event_name,
        e.country as e_country,
        s.country as s_country,
        s.empirical_score,
        CASE 
            WHEN e.country = s.country THEN 'Match direct'
            WHEN e.country IN ('de', 'fr', 'it', 'es', 'ea') AND s.country = 'eur' THEN 'Match mapping'
            ELSE 'No match'
        END as match_type
    FROM economic_events e
    CROSS JOIN scores_empirical s
    WHERE DATE(e.datetime_utc) = '2025-09-11'
      AND LOWER(e.event_name) LIKE '%current%account%'
      AND e.event_name = s.event_name
      AND (
          e.country = s.country
          OR (e.country IN ('de', 'fr', 'it', 'es', 'ea') AND s.country = 'eur')
      )
    """
    
    test_result = conn.execute(query_test).df()
    
    if len(test_result) > 0:
        print("✅ MATCHING TROUVÉ :")
        print()
        print(test_result.to_string())
        print()
        
        if any(test_result['empirical_score'] >= 15):
            print("✅ Score >= 15 : Devrait être HIGH")
        else:
            print("❌ Score < 15 : Restera MEDIUM")
    else:
        print("❌ AUCUN MATCHING TROUVÉ")
        print()
        print("Problème probable : Nom event_name ne matche pas exactement")
        print()
        
        # Vérifier variations de nom
        print("Noms exacts dans DB vs CSV :")
        print()
        print("DB :")
        for name in db_ca['event_name'].unique():
            print(f"   '{name}'")
        print()
        print("CSV :")
        for name in csv_ca['event_name'].unique():
            print(f"   '{name}'")
    
    print()
    
    conn.close()
    
    print("=" * 80)


if __name__ == '__main__':
    debug_current_account_matching()
