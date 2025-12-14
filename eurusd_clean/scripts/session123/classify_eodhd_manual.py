"""
Classification HIGH importance pour EODHD par pattern matching

Basé sur connaissance trading forex :
- HIGH : NFP, CPI, Interest rates, GDP, Retail Sales, etc.
- MEDIUM : PMI, Consumer confidence, etc.
- LOW : Auctions, minor indicators

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Classification manuelle EODHD
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def classify_eodhd_events():
    """Classification basée sur patterns event_name"""
    
    print("=" * 80)
    print("CLASSIFICATION EODHD PAR PATTERNS")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # ========================================================================
    # 1. DÉFINIR PATTERNS HIGH
    # ========================================================================
    
    high_patterns = [
        # Employment (US, CA, AU, etc.)
        'non_farm', 'nonfarm', 'payrolls', 'employment_change',
        'unemployment_rate', 'jobless_claims',
        
        # Inflation (all countries)
        'cpi', 'inflation_rate', 'pce', 'ppi', 'producer_price',
        'consumer_price', 'core_inflation', 'core_cpi',
        
        # Central Banks (all)
        'interest_rate_decision', 'monetary_policy', 'policy_rate',
        'fomc', 'fed_interest', 'ecb_interest', 'boe_interest',
        'rba_interest', 'boc_interest',
        
        # GDP (all countries)
        'gdp', 'gross_domestic_product',
        
        # Retail & Consumer (major economies)
        'retail_sales', 'consumer_spending',
        
        # Manufacturing (major)
        'ism_manufacturing', 'ism_services', 'manufacturing_pmi',
        
        # Trade (major)
        'trade_balance', 'balance_of_trade', 'current_account'
    ]
    
    print("Patterns HIGH définis :")
    for i, pattern in enumerate(high_patterns[:10], 1):
        print(f"   {i}. {pattern}")
    print(f"   ... +{len(high_patterns)-10} autres")
    print()
    
    # ========================================================================
    # 2. RESET + CLASSIFICATION
    # ========================================================================
    
    print("2. CLASSIFICATION")
    print("=" * 80)
    print()
    
    # Reset
    conn.execute("UPDATE economic_events SET importance = 'MEDIUM'")
    print("✅ Reset → MEDIUM")
    print()
    
    # Construire WHERE clause
    conditions_high = []
    for pattern in high_patterns:
        conditions_high.append(f"LOWER(event_name) LIKE '%{pattern}%'")
    
    where_high = " OR ".join(conditions_high)
    
    # Reclassifier HIGH (majors + high impact)
    query_high = f"""
    UPDATE economic_events
    SET importance = 'HIGH'
    WHERE ({where_high})
      AND country IN ('usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf')
    """
    
    conn.execute(query_high)
    print("✅ HIGH classifié (majors)")
    print()
    
    # LOW : événements mineurs
    low_patterns = [
        'auction', 'bill_auction', 'bond_auction',
        'api_', 'eia_', 'treasury',
        'mortgage_rate', 'building_permits'
    ]
    
    conditions_low = []
    for pattern in low_patterns:
        conditions_low.append(f"LOWER(event_name) LIKE '%{pattern}%'")
    
    where_low = " OR ".join(conditions_low)
    
    query_low = f"""
    UPDATE economic_events
    SET importance = 'LOW'
    WHERE ({where_low})
    """
    
    conn.execute(query_low)
    print("✅ LOW classifié (auctions, minors)")
    print()
    
    # ========================================================================
    # 3. VÉRIFICATION DISTRIBUTION
    # ========================================================================
    
    print("3. DISTRIBUTION")
    print("=" * 80)
    print()
    
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
    print(dist.to_string())
    print()
    
    # ========================================================================
    # 4. ÉVÉNEMENTS 11 SEPTEMBRE HIGH
    # ========================================================================
    
    print("4. ÉVÉNEMENTS 11 SEPTEMBRE HIGH")
    print("=" * 80)
    print()
    
    query_sept11_high = """
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
    
    sept11_high = conn.execute(query_sept11_high).df()
    
    print(f"Total HIGH : {len(sept11_high)}")
    print()
    
    if len(sept11_high) > 0:
        print("✅✅✅ SUCCESS !")
        print()
        for idx, row in sept11_high.iterrows():
            dt = pd.to_datetime(row['datetime_utc'])
            print(f"   {dt.strftime('%H:%M')} - {row['country'].upper()} - {row['event_name']}")
            print(f"      Actual: {row['actual']} | Forecast: {row['forecast']} | Previous: {row['previous']}")
            print()
    else:
        print("❌ Aucun HIGH détecté")
        print()
        print("Événements USD/EUR 12h :")
        
        query_debug = """
        SELECT event_name, country, importance
        FROM economic_events
        WHERE DATE(datetime_utc) = '2025-09-11'
          AND country IN ('usd', 'eur')
          AND HOUR(datetime_utc) = 12
        """
        
        debug = conn.execute(query_debug).df()
        print(debug.to_string())
        print()
    
    # ========================================================================
    # 5. ÉCHANTILLON HIGH
    # ========================================================================
    
    print("5. ÉCHANTILLON ÉVÉNEMENTS HIGH")
    print("=" * 80)
    print()
    
    query_sample = """
    SELECT 
        event_name,
        country,
        COUNT(*) as occurrences
    FROM economic_events
    WHERE importance = 'HIGH'
    GROUP BY event_name, country
    ORDER BY occurrences DESC
    LIMIT 15
    """
    
    sample = conn.execute(query_sample).df()
    print(sample.to_string())
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ CLASSIFICATION TERMINÉE")
    print("=" * 80)
    print()
    print("Prochaines étapes :")
    print("   python validate_cluster_sept11.py")
    print("   python validate_formula_s115_complete.py")
    print()


if __name__ == '__main__':
    classify_eodhd_events()
