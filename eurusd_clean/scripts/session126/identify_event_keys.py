#!/usr/bin/env python3
"""
Identification Event Keys - Session 126
Trouve event_keys exacts pour Retail Sales + Fed Decisions
"""

import duckdb
from pathlib import Path

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb")

def identify_event_keys():
    """Identifie event_keys pour nouvelles familles à tester"""
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    print("=" * 70)
    print("IDENTIFICATION EVENT_KEYS - Session 126")
    print("=" * 70)
    
    # ========================================
    # RETAIL SALES
    # ========================================
    print("\n[1/2] RETAIL SALES (US)")
    print("-" * 70)
    
    query_retail = """
    SELECT 
        event_key,
        event_title,
        COUNT(*) as count,
        MIN(ts_utc) as first_date,
        MAX(ts_utc) as last_date
    FROM events
    WHERE country = 'US'
      AND importance_n = 3
      AND (event_key LIKE '%retail%' OR event_title LIKE '%Retail%')
    GROUP BY event_key, event_title
    ORDER BY count DESC
    """
    
    retail_results = conn.execute(query_retail).fetchall()
    
    if retail_results:
        print(f"✓ {len(retail_results)} event_key(s) trouvé(s) :\n")
        for row in retail_results:
            event_key, event_title, count, first, last = row
            print(f"  event_key: '{event_key}'")
            print(f"  event_title: '{event_title}'")
            print(f"  count: {count} événements")
            print(f"  période: {first.strftime('%Y-%m-%d')} → {last.strftime('%Y-%m-%d')}")
            print()
    else:
        print("✗ Aucun événement Retail Sales trouvé")
        print("\nTentative recherche plus large...")
        
        query_retail_broad = """
        SELECT DISTINCT event_key, event_title, importance_n, COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND (event_key LIKE '%retail%' OR event_title LIKE '%Retail%')
        GROUP BY event_key, event_title, importance_n
        ORDER BY importance_n DESC, count DESC
        """
        
        retail_broad = conn.execute(query_retail_broad).fetchall()
        print(f"  {len(retail_broad)} résultats (toutes importances) :\n")
        for row in retail_broad:
            event_key, event_title, importance, count = row
            print(f"  [{importance}] '{event_key}' ({count} events)")
    
    # ========================================
    # FED INTEREST RATE DECISION
    # ========================================
    print("\n[2/2] FED INTEREST RATE DECISION (US)")
    print("-" * 70)
    
    query_fed = """
    SELECT 
        event_key,
        event_title,
        COUNT(*) as count,
        MIN(ts_utc) as first_date,
        MAX(ts_utc) as last_date
    FROM events
    WHERE country = 'US'
      AND importance_n = 3
      AND (
          event_key LIKE '%fed%' 
          OR event_key LIKE '%interest%rate%'
          OR event_key LIKE '%fomc%'
          OR event_title LIKE '%Fed%Rate%'
          OR event_title LIKE '%FOMC%'
          OR event_title LIKE '%Interest Rate%'
      )
    GROUP BY event_key, event_title
    ORDER BY count DESC
    """
    
    fed_results = conn.execute(query_fed).fetchall()
    
    if fed_results:
        print(f"✓ {len(fed_results)} event_key(s) trouvé(s) :\n")
        for row in fed_results:
            event_key, event_title, count, first, last = row
            print(f"  event_key: '{event_key}'")
            print(f"  event_title: '{event_title}'")
            print(f"  count: {count} événements")
            print(f"  période: {first.strftime('%Y-%m-%d')} → {last.strftime('%Y-%m-%d')}")
            print()
    else:
        print("✗ Aucun événement Fed trouvé")
        print("\nTentative recherche plus large...")
        
        query_fed_broad = """
        SELECT DISTINCT event_key, event_title, importance_n, COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND (event_key LIKE '%fed%' OR event_key LIKE '%fomc%' OR event_title LIKE '%Fed%')
        GROUP BY event_key, event_title, importance_n
        ORDER BY importance_n DESC, count DESC
        """
        
        fed_broad = conn.execute(query_fed_broad).fetchall()
        print(f"  {len(fed_broad)} résultats (toutes importances) :\n")
        for row in fed_broad:
            event_key, event_title, importance, count = row
            print(f"  [{importance}] '{event_key}' ({count} events)")
    
    # ========================================
    # VÉRIFICATION CPI + NFP (référence)
    # ========================================
    print("\n[RÉFÉRENCE] CPI + NFP (déjà validés Session 125)")
    print("-" * 70)
    
    query_ref = """
    SELECT 
        event_key,
        COUNT(*) as count
    FROM events
    WHERE country = 'US'
      AND importance_n = 3
      AND (event_key LIKE '%cpi%' OR event_key LIKE '%nfp%' OR event_key LIKE '%non farm%')
    GROUP BY event_key
    ORDER BY count DESC
    """
    
    ref_results = conn.execute(query_ref).fetchall()
    
    for row in ref_results:
        event_key, count = row
        print(f"  '{event_key}': {count} événements")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("IDENTIFICATION COMPLÉTÉE")
    print("=" * 70)


if __name__ == "__main__":
    identify_event_keys()
