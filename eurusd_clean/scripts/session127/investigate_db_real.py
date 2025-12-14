import duckdb
import pandas as pd

# Connexion DB
db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'
conn = duckdb.connect(db_path, read_only=True)

print("=" * 80)
print("INVESTIGATION RÉELLE DB - SCORES HIGH MANQUANTS")
print("=" * 80)
print()

# ============================================================================
# RECHERCHE 1 : u_6_unemployment_rate
# ============================================================================
print("RECHERCHE 1 : u_6_unemployment_rate (score 63.96)")
print("-" * 80)

query_u6 = """
SELECT DISTINCT 
    event_key,
    importance_n,
    COUNT(*) as event_count
FROM events
WHERE country = 'US'
  AND (
    LOWER(event_key) LIKE '%u-6%' 
    OR LOWER(event_key) LIKE '%u6%'
    OR LOWER(event_key) LIKE '%u 6%'
    OR LOWER(event_key) LIKE '%underemployment%'
  )
GROUP BY event_key, importance_n
ORDER BY event_count DESC
"""

result_u6 = conn.execute(query_u6).df()

if len(result_u6) > 0:
    print(f"✅ {len(result_u6)} correspondances trouvées :\n")
    for _, row in result_u6.iterrows():
        imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
        print(f"  → event_key: '{row['event_key']}'")
        print(f"     Importance: {imp} ({row['importance_n']})")
        print(f"     Count: {row['event_count']} événements")
        print()
else:
    print("❌ AUCUNE correspondance trouvée")
    print()
    
    # Recherche plus large : tous unemployment
    print("Recherche élargie : tous 'unemployment' :")
    query_unemployment = """
    SELECT DISTINCT 
        event_key,
        importance_n,
        COUNT(*) as event_count
    FROM events
    WHERE country = 'US'
      AND LOWER(event_key) LIKE '%unemployment%'
    GROUP BY event_key, importance_n
    ORDER BY event_count DESC
    LIMIT 10
    """
    
    result_unemployment = conn.execute(query_unemployment).df()
    print(f"\nTrouvé {len(result_unemployment)} variantes 'unemployment' :\n")
    for _, row in result_unemployment.iterrows():
        imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
        print(f"  → '{row['event_key']}' [{imp}] (n={row['event_count']})")
    print()

print()

# ============================================================================
# RECHERCHE 2 : gross_domestic_product
# ============================================================================
print("RECHERCHE 2 : gross_domestic_product (score 39.70)")
print("-" * 80)

query_gdp = """
SELECT DISTINCT 
    event_key,
    importance_n,
    COUNT(*) as event_count
FROM events
WHERE country = 'US'
  AND (
    LOWER(event_key) LIKE '%gross%domestic%' 
    OR LOWER(event_key) LIKE '%gdp%'
  )
GROUP BY event_key, importance_n
ORDER BY event_count DESC
"""

result_gdp = conn.execute(query_gdp).df()

if len(result_gdp) > 0:
    print(f"✅ {len(result_gdp)} correspondances trouvées :\n")
    for _, row in result_gdp.iterrows():
        imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
        print(f"  → event_key: '{row['event_key']}'")
        print(f"     Importance: {imp} ({row['importance_n']})")
        print(f"     Count: {row['event_count']} événements")
        print()
else:
    print("❌ AUCUNE correspondance trouvée")
    print()

print()

# ============================================================================
# RECHERCHE BONUS : 30_year_mortgage_rate et m2_money_supply
# ============================================================================
print("RECHERCHE BONUS : Autres scores potentiellement trouvables")
print("-" * 80)

# Mortgage rate
query_mortgage = """
SELECT DISTINCT 
    event_key,
    importance_n,
    COUNT(*) as event_count
FROM events
WHERE country = 'US'
  AND LOWER(event_key) LIKE '%mortgage%rate%'
  AND LOWER(event_key) LIKE '%30%'
GROUP BY event_key, importance_n
ORDER BY event_count DESC
"""

result_mortgage = conn.execute(query_mortgage).df()
print("\n30_year_mortgage_rate :")
if len(result_mortgage) > 0:
    for _, row in result_mortgage.iterrows():
        imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
        print(f"  ✅ '{row['event_key']}' [{imp}] (n={row['event_count']})")
else:
    print("  ❌ Aucune correspondance")

# Money supply
query_money = """
SELECT DISTINCT 
    event_key,
    importance_n,
    COUNT(*) as event_count
FROM events
WHERE country = 'US'
  AND (
    LOWER(event_key) LIKE '%money%supply%'
    OR LOWER(event_key) LIKE '%m2%'
  )
GROUP BY event_key, importance_n
ORDER BY event_count DESC
"""

result_money = conn.execute(query_money).df()
print("\nm2_money_supply :")
if len(result_money) > 0:
    for _, row in result_money.iterrows():
        imp = {1: 'LOW', 2: 'MED', 3: 'HIGH'}[row['importance_n']]
        print(f"  ✅ '{row['event_key']}' [{imp}] (n={row['event_count']})")
else:
    print("  ❌ Aucune correspondance")

print()

conn.close()

print("=" * 80)
print("✅ INVESTIGATION DB COMPLÉTÉE")
print("=" * 80)
