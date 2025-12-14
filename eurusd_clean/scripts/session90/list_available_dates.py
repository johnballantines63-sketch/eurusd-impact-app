"""
LISTE DATES DISPONIBLES - Session 90
Identifier 10-15 dates pour validation étendue
Critère : événements HIGH IMPACT (score > 40)
"""

import duckdb
from pathlib import Path
import pandas as pd

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

print("="*80)
print("📅 RECHERCHE DATES DISPONIBLES - Événements HIGH IMPACT")
print("="*80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Requête : trouver toutes les dates avec événements HIGH
query = """
SELECT 
    DATE(e.ts_utc) as date,
    COUNT(DISTINCT e.event_key) as num_events,
    AVG(ef.empirical_score) as score_avg,
    MAX(ef.empirical_score) as score_max,
    MIN(ef.empirical_score) as score_min,
    STRING_AGG(DISTINCT ef.family, ', ') as families
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND ef.empirical_score > 40
    AND DATE(e.ts_utc) >= '2025-01-01'
    AND DATE(e.ts_utc) <= '2025-12-31'
GROUP BY DATE(e.ts_utc)
HAVING COUNT(DISTINCT e.event_key) >= 3
ORDER BY date DESC
"""

dates = conn.execute(query).df()

print(f"\n📊 RÉSULTAT RECHERCHE :")
print(f"   Dates trouvées : {len(dates)}")
print(f"   Critères : score > 40, ≥3 événements, US, 2025")

if len(dates) == 0:
    print("\n❌ AUCUNE DATE TROUVÉE !")
    conn.close()
    exit(1)

# Afficher top 20
print("\n" + "="*80)
print("📋 TOP 20 DATES DISPONIBLES :")
print("="*80)

print(f"\n{'Date':<12} {'Events':>7} {'Score Avg':>10} {'Score Max':>10} {'Families':<40}")
print(f"{'-'*12} {'-'*7} {'-'*10} {'-'*10} {'-'*40}")

for idx, row in dates.head(20).iterrows():
    families_short = row['families'][:37] + "..." if len(str(row['families'])) > 40 else row['families']
    print(f"{row['date']:<12} {row['num_events']:>7} {row['score_avg']:>10.1f} {row['score_max']:>10.1f} {families_short:<40}")

# Identifier dates clés par type
print("\n" + "="*80)
print("🎯 DATES CLÉS PAR TYPE D'ÉVÉNEMENT :")
print("="*80)

# NFP (Nonfarm Payrolls)
query_nfp = """
SELECT DISTINCT
    DATE(e.ts_utc) as date,
    COUNT(*) as num_events,
    AVG(ef.empirical_score) as score_avg
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND ef.family LIKE '%nonfarm%'
    AND DATE(e.ts_utc) >= '2025-01-01'
GROUP BY DATE(e.ts_utc)
ORDER BY date DESC
LIMIT 5
"""

nfp_dates = conn.execute(query_nfp).df()
print(f"\n📌 NFP (Nonfarm Payrolls) - {len(nfp_dates)} dates :")
for idx, row in nfp_dates.iterrows():
    print(f"   {row['date']} : {row['num_events']} événements (score avg: {row['score_avg']:.1f})")

# CPI
query_cpi = """
SELECT DISTINCT
    DATE(e.ts_utc) as date,
    COUNT(*) as num_events,
    AVG(ef.empirical_score) as score_avg
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND (ef.family LIKE '%cpi%' OR ef.family LIKE '%inflation%')
    AND ef.empirical_score > 40
    AND DATE(e.ts_utc) >= '2025-01-01'
GROUP BY DATE(e.ts_utc)
ORDER BY date DESC
LIMIT 5
"""

cpi_dates = conn.execute(query_cpi).df()
print(f"\n📌 CPI (Consumer Price Index) - {len(cpi_dates)} dates :")
for idx, row in cpi_dates.iterrows():
    print(f"   {row['date']} : {row['num_events']} événements (score avg: {row['score_avg']:.1f})")

# Jobless Claims
query_jobless = """
SELECT DISTINCT
    DATE(e.ts_utc) as date,
    COUNT(*) as num_events,
    AVG(ef.empirical_score) as score_avg
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND ef.family LIKE '%jobless%'
    AND ef.empirical_score > 40
    AND DATE(e.ts_utc) >= '2025-01-01'
GROUP BY DATE(e.ts_utc)
ORDER BY date DESC
LIMIT 5
"""

jobless_dates = conn.execute(query_jobless).df()
print(f"\n📌 Jobless Claims - {len(jobless_dates)} dates :")
for idx, row in jobless_dates.iterrows():
    print(f"   {row['date']} : {row['num_events']} événements (score avg: {row['score_avg']:.1f})")

# Retail Sales
query_retail = """
SELECT DISTINCT
    DATE(e.ts_utc) as date,
    COUNT(*) as num_events,
    AVG(ef.empirical_score) as score_avg
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND ef.family LIKE '%retail%'
    AND ef.empirical_score > 40
    AND DATE(e.ts_utc) >= '2025-01-01'
GROUP BY DATE(e.ts_utc)
ORDER BY date DESC
LIMIT 5
"""

retail_dates = conn.execute(query_retail).df()
print(f"\n📌 Retail Sales - {len(retail_dates)} dates :")
for idx, row in retail_dates.iterrows():
    print(f"   {row['date']} : {row['num_events']} événements (score avg: {row['score_avg']:.1f})")

# Sauvegarder CSV
output_path = Path(__file__).parent / "dates_disponibles_session90.csv"
dates.to_csv(output_path, index=False)
print(f"\n💾 CSV sauvegardé : {output_path}")

conn.close()

print("\n" + "="*80)
print("✅ Recherche terminée")
print("="*80)
print(f"\n🎯 RECOMMANDATION SÉLECTION :")
print(f"   Pour validation robuste (10-15 dates), sélectionner :")
print(f"   - 3-4 dates NFP (variabilité haute)")
print(f"   - 3-4 dates CPI (variabilité moyenne)")
print(f"   - 2-3 dates Jobless Claims")
print(f"   - 1-2 dates Retail Sales")
print(f"   - 1-2 dates autres types")
