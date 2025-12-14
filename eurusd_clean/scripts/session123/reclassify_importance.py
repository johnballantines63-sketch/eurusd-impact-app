"""
Reclassifier importance events selon event_name

HIGH importance :
- NFP, Payrolls
- CPI, Inflation
- Interest Rate Decision, FOMC
- GDP
- Unemployment Rate
- Retail Sales

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Fix classification importance
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def reclassify_importance():
    """Reclassifier importance selon event_name"""
    
    print("=" * 80)
    print("RECLASSIFICATION IMPORTANCE")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # ========================================================================
    # HIGH IMPORTANCE RULES
    # ========================================================================
    
    high_events = [
        # US Employment
        'non_farm_payrolls',
        'nonfarm_payrolls',
        'payrolls',
        'employment_change',
        'unemployment_rate',
        'jobless_claims',
        
        # US Inflation
        'cpi',
        'inflation_rate',
        'core_inflation',
        'core_cpi',
        'pce_price_index',
        'producer_price_index',
        'ppi',
        
        # Central Banks
        'interest_rate_decision',
        'fomc',
        'fed_interest_rate',
        'ecb_interest_rate',
        'boe_interest_rate',
        'monetary_policy',
        
        # GDP
        'gdp',
        'gross_domestic_product',
        
        # Retail
        'retail_sales',
        
        # Manufacturing
        'ism_manufacturing_pmi',
        'ism_services_pmi',
        'manufacturing_pmi',
        
        # Trade
        'trade_balance',
        'balance_of_trade',
    ]
    
    print("HIGH importance events :")
    for event in high_events[:10]:
        print(f"   - {event}")
    print(f"   ... +{len(high_events)-10} autres")
    print()
    
    # ========================================================================
    # UPDATE IMPORTANCE
    # ========================================================================
    
    print("🔄 Reclassification en cours...")
    print()
    
    # Construire CASE WHEN
    conditions = []
    for event in high_events:
        conditions.append(f"LOWER(event_name) LIKE '%{event}%'")
    
    where_clause = " OR ".join(conditions)
    
    query = f"""
    UPDATE economic_events
    SET importance = 'HIGH'
    WHERE {where_clause}
      AND country IN ('usd', 'eur', 'gbp', 'jpy', 'cad')
    """
    
    result = conn.execute(query)
    rows_updated = result.fetchone()[0] if result else 0
    
    print(f"✅ {rows_updated:,} événements reclassifiés HIGH")
    print()
    
    # ========================================================================
    # VÉRIFICATION
    # ========================================================================
    
    print("📊 NOUVELLE DISTRIBUTION")
    print("=" * 80)
    print()
    
    query_check = """
    SELECT 
        importance,
        COUNT(*) as count
    FROM economic_events
    GROUP BY importance
    ORDER BY count DESC
    """
    
    dist = conn.execute(query_check).df()
    print(dist.to_string())
    print()
    
    # ========================================================================
    # VÉRIFICATION 11 SEPTEMBRE
    # ========================================================================
    
    print("📅 ÉVÉNEMENTS 11 SEPTEMBRE HIGH")
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
    
    if len(sept11_high) > 0:
        print(f"✅ {len(sept11_high)} événements HIGH détectés")
        print()
        print(sept11_high.to_string())
    else:
        print("❌ Aucun événement HIGH trouvé")
    
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ RECLASSIFICATION TERMINÉE")
    print("=" * 80)
    print()
    print("Vous pouvez maintenant relancer :")
    print("   python validate_cluster_sept11.py")
    print()


if __name__ == '__main__':
    reclassify_importance()
