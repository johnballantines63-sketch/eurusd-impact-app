"""
RECHERCHE RAPIDE DATES - Session 91
Identifier 10 dates optimales pour validation

⚠️ TIMEZONE : events.ts_utc est déjà en Bern time (+02:00)
   → Pas de conversion nécessaire (SESSION 86)
"""

import duckdb
from pathlib import Path

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("🔍 RECHERCHE DATES OPTIMALES (excluant 01.08, 05.09, 17.09)")
print("="*80)

# 1. NFP (besoin 2-3 supplémentaires)
query_nfp = """
SELECT DISTINCT
    DATE(e.ts_utc) as date,
    MIN(strftime(e.ts_utc, '%H:%M:%S')) as time,
    STRING_AGG(DISTINCT e.event_title, ' | ') as titles
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND ef.family LIKE '%nonfarm%'
    AND DATE(e.ts_utc) >= '2025-01-01'
    AND DATE(e.ts_utc) NOT IN ('2025-08-01', '2025-09-05')
GROUP BY DATE(e.ts_utc)
ORDER BY date DESC
LIMIT 4
"""

nfp = conn.execute(query_nfp).df()
print("\n📌 NFP (Nonfarm Payrolls) - 4 dates :")
for _, row in nfp.iterrows():
    print(f"   {row['date']} {row['time']} - {row['titles'][:60]}")

# 2. CPI (besoin 2-3 supplémentaires)
query_cpi = """
SELECT DISTINCT
    DATE(e.ts_utc) as date,
    MIN(strftime(e.ts_utc, '%H:%M:%S')) as time,
    STRING_AGG(DISTINCT e.event_title, ' | ') as titles
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND (ef.family LIKE '%cpi%' OR e.event_title LIKE '%CPI%')
    AND ef.empirical_score > 40
    AND DATE(e.ts_utc) >= '2025-01-01'
    AND DATE(e.ts_utc) != '2025-09-17'
GROUP BY DATE(e.ts_utc)
ORDER BY date DESC
LIMIT 4
"""

cpi = conn.execute(query_cpi).df()
print("\n📌 CPI (Consumer Price Index) - 4 dates :")
for _, row in cpi.iterrows():
    print(f"   {row['date']} {row['time']} - {row['titles'][:60]}")

# 3. Jobless Claims (besoin 2-3)
query_jobless = """
SELECT DISTINCT
    DATE(e.ts_utc) as date,
    MIN(strftime(e.ts_utc, '%H:%M:%S')) as time,
    STRING_AGG(DISTINCT e.event_title, ' | ') as titles
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND (ef.family LIKE '%jobless%' OR e.event_title LIKE '%Jobless%')
    AND ef.empirical_score > 40
    AND DATE(e.ts_utc) >= '2025-01-01'
GROUP BY DATE(e.ts_utc)
ORDER BY date DESC
LIMIT 3
"""

jobless = conn.execute(query_jobless).df()
print("\n📌 Jobless Claims - 3 dates :")
for _, row in jobless.iterrows():
    print(f"   {row['date']} {row['time']} - {row['titles'][:60]}")

# 4. Retail Sales (besoin 1-2)
query_retail = """
SELECT DISTINCT
    DATE(e.ts_utc) as date,
    MIN(strftime(e.ts_utc, '%H:%M:%S')) as time,
    STRING_AGG(DISTINCT e.event_title, ' | ') as titles
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND (ef.family LIKE '%retail%' OR e.event_title LIKE '%Retail%')
    AND ef.empirical_score > 40
    AND DATE(e.ts_utc) >= '2025-01-01'
GROUP BY DATE(e.ts_utc)
ORDER BY date DESC
LIMIT 2
"""

retail = conn.execute(query_retail).df()
print("\n📌 Retail Sales - 2 dates :")
for _, row in retail.iterrows():
    print(f"   {row['date']} {row['time']} - {row['titles'][:60]}")

conn.close()

print("\n" + "="*80)
print("✅ Recherche terminée")
print("="*80)
print("\n🎯 SÉLECTION RECOMMANDÉE (10 dates) :")
print("   - 3 NFP (05.09 déjà + 2 nouvelles)")
print("   - 3 CPI (17.09 déjà + 2 nouvelles)")
print("   - 2 Jobless")
print("   - 2 Retail")
print("   = 10 dates diversifiées")
print("\n⚠️ TIMEZONE : Dates/times déjà en Bern time (+02:00)")
print("   → Utiliser directement sans conversion")
