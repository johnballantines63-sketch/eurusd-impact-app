#!/usr/bin/env python3
"""
Vérification Event Keys - Session 126
Identifie event_keys exacts pour Retail Sales + Fed Decisions
"""

import duckdb
from pathlib import Path

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb")

def main():
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    print("=" * 80)
    print("VÉRIFICATION EVENT_KEYS - Session 126")
    print("Objectif : Identifier event_keys exacts pour nouvelles familles à tester")
    print("=" * 80)
    
    # ========================================
    # RÉFÉRENCE : CPI (validé Session 125)
    # ========================================
    print("\n[RÉFÉRENCE] CPI - Validé Session 125")
    print("-" * 80)
    
    query_cpi = """
    SELECT 
        event_key,
        COUNT(*) as count,
        MIN(ts_utc) as first_date,
        MAX(ts_utc) as last_date
    FROM events
    WHERE country = 'US'
      AND importance_n = 3
      AND LOWER(event_key) LIKE '%cpi%'
    GROUP BY event_key
    ORDER BY count DESC
    """
    
    cpi_results = conn.execute(query_cpi).fetchall()
    
    print(f"✓ {len(cpi_results)} event_key(s) CPI trouvé(s) :\n")
    for event_key, count, first, last in cpi_results:
        print(f"  '{event_key}'")
        print(f"    {count:3d} événements | {first.strftime('%Y-%m-%d')} → {last.strftime('%Y-%m-%d')}")
    
    # ========================================
    # RÉFÉRENCE : NFP (validé Session 125)
    # ========================================
    print("\n[RÉFÉRENCE] NFP - Validé Session 125")
    print("-" * 80)
    
    query_nfp = """
    SELECT 
        event_key,
        COUNT(*) as count,
        MIN(ts_utc) as first_date,
        MAX(ts_utc) as last_date
    FROM events
    WHERE country = 'US'
      AND importance_n = 3
      AND (LOWER(event_key) LIKE '%nfp%' 
           OR LOWER(event_key) LIKE '%non%farm%'
           OR LOWER(event_key) LIKE '%payroll%')
    GROUP BY event_key
    ORDER BY count DESC
    """
    
    nfp_results = conn.execute(query_nfp).fetchall()
    
    print(f"✓ {len(nfp_results)} event_key(s) NFP trouvé(s) :\n")
    for event_key, count, first, last in nfp_results:
        print(f"  '{event_key}'")
        print(f"    {count:3d} événements | {first.strftime('%Y-%m-%d')} → {last.strftime('%Y-%m-%d')}")
    
    # ========================================
    # NOUVEAU : RETAIL SALES
    # ========================================
    print("\n[NOUVEAU] RETAIL SALES (US)")
    print("-" * 80)
    
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
      AND (LOWER(event_key) LIKE '%retail%' 
           OR LOWER(event_title) LIKE '%retail%')
    GROUP BY event_key, event_title
    ORDER BY count DESC
    """
    
    retail_results = conn.execute(query_retail).fetchall()
    
    if retail_results:
        print(f"✓ {len(retail_results)} event_key(s) RETAIL SALES trouvé(s) :\n")
        for event_key, event_title, count, first, last in retail_results:
            print(f"  event_key: '{event_key}'")
            print(f"  event_title: '{event_title}'")
            print(f"    {count:3d} événements | {first.strftime('%Y-%m-%d')} → {last.strftime('%Y-%m-%d')}")
            print()
    else:
        print("✗ Aucun événement Retail Sales HIGH importance trouvé")
        print("\n  Recherche élargie (toutes importances)...")
        
        query_retail_all = """
        SELECT 
            event_key,
            event_title,
            importance_n,
            COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND (LOWER(event_key) LIKE '%retail%' 
               OR LOWER(event_title) LIKE '%retail%')
        GROUP BY event_key, event_title, importance_n
        ORDER BY importance_n DESC, count DESC
        LIMIT 10
        """
        
        retail_all = conn.execute(query_retail_all).fetchall()
        print(f"\n  Top 10 résultats (toutes importances) :")
        for event_key, event_title, importance, count in retail_all:
            imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(importance, "?")
            print(f"    [{imp_label}] '{event_key}' | {count} events")
            print(f"         '{event_title}'")
    
    # ========================================
    # NOUVEAU : FED INTEREST RATE DECISION
    # ========================================
    print("\n[NOUVEAU] FED INTEREST RATE DECISION (US)")
    print("-" * 80)
    
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
      AND (LOWER(event_key) LIKE '%fed%' 
           OR LOWER(event_key) LIKE '%fomc%'
           OR LOWER(event_key) LIKE '%interest%rate%'
           OR LOWER(event_key) LIKE '%federal%funds%'
           OR LOWER(event_title) LIKE '%fed%'
           OR LOWER(event_title) LIKE '%fomc%')
    GROUP BY event_key, event_title
    ORDER BY count DESC
    """
    
    fed_results = conn.execute(query_fed).fetchall()
    
    if fed_results:
        print(f"✓ {len(fed_results)} event_key(s) FED trouvé(s) :\n")
        for event_key, event_title, count, first, last in fed_results:
            print(f"  event_key: '{event_key}'")
            print(f"  event_title: '{event_title}'")
            print(f"    {count:3d} événements | {first.strftime('%Y-%m-%d')} → {last.strftime('%Y-%m-%d')}")
            print()
    else:
        print("✗ Aucun événement Fed HIGH importance trouvé")
        print("\n  Recherche élargie (toutes importances)...")
        
        query_fed_all = """
        SELECT 
            event_key,
            event_title,
            importance_n,
            COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND (LOWER(event_key) LIKE '%fed%' 
               OR LOWER(event_key) LIKE '%fomc%'
               OR LOWER(event_title) LIKE '%fed%'
               OR LOWER(event_title) LIKE '%fomc%')
        GROUP BY event_key, event_title, importance_n
        ORDER BY importance_n DESC, count DESC
        LIMIT 10
        """
        
        fed_all = conn.execute(query_fed_all).fetchall()
        print(f"\n  Top 10 résultats (toutes importances) :")
        for event_key, event_title, importance, count in fed_all:
            imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(importance, "?")
            print(f"    [{imp_label}] '{event_key}' | {count} events")
            print(f"         '{event_title}'")
    
    # ========================================
    # STATISTIQUES GLOBALES
    # ========================================
    print("\n[STATISTIQUES] Distribution Événements US HIGH Importance")
    print("-" * 80)
    
    query_stats = """
    SELECT 
        COUNT(DISTINCT event_key) as unique_keys,
        COUNT(*) as total_events,
        MIN(ts_utc) as first_event,
        MAX(ts_utc) as last_event
    FROM events
    WHERE country = 'US' AND importance_n = 3
    """
    
    stats = conn.execute(query_stats).fetchone()
    unique_keys, total_events, first_event, last_event = stats
    
    print(f"  Event Keys Uniques : {unique_keys}")
    print(f"  Total Événements   : {total_events}")
    print(f"  Période Couverte   : {first_event.strftime('%Y-%m-%d')} → {last_event.strftime('%Y-%m-%d')}")
    
    # Top 10 event_keys les plus fréquents
    print("\n  Top 10 Event Keys US HIGH :")
    query_top = """
    SELECT event_key, COUNT(*) as count
    FROM events
    WHERE country = 'US' AND importance_n = 3
    GROUP BY event_key
    ORDER BY count DESC
    LIMIT 10
    """
    
    top_results = conn.execute(query_top).fetchall()
    for event_key, count in top_results:
        print(f"    {count:3d} | '{event_key}'")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("VÉRIFICATION COMPLÉTÉE")
    print("=" * 80)


if __name__ == "__main__":
    main()
