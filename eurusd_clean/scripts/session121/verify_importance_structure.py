#!/usr/bin/env python3
"""
Vérifier VRAIE structure importance + scores empiriques
"""

import duckdb
import pandas as pd

db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb'

conn = duckdb.connect(db_path, read_only=True)

print("="*100)
print("VÉRIFICATION STRUCTURE IMPORTANCE + SCORES")
print("="*100 + "\n")

# 1. Distribution importance_n
print("1. DISTRIBUTION importance_n :")
print("-"*100)
query = """
SELECT 
    importance_n,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM events
GROUP BY importance_n
ORDER BY importance_n
"""
df_imp = conn.execute(query).df()
print(df_imp)
print()

# 2. Exemples événements HIGH (importance_n = 1, 2 et 3)
print("2. EXEMPLES PAR importance_n :")
print("-"*100)
for imp in [1, 2, 3]:
    query = f"""
    SELECT event_title, country, ts_utc
    FROM events
    WHERE importance_n = {imp}
    LIMIT 3
    """
    df = conn.execute(query).df()
    print(f"\nimportance_n = {imp} (exemples) :")
    for _, row in df.iterrows():
        title = row['event_title'] if row['event_title'] else "Unknown"
        print(f"  - {title[:50]:50s} | {row['country']}")

# 3. Vérifier table scores
print("\n3. TABLE SCORES :")
print("-"*100)
try:
    query_scores = """
    SELECT * FROM scores LIMIT 5
    """
    df_scores = conn.execute(query_scores).df()
    print("\n✅ Table scores existe :")
    print(df_scores)
    
    # Structure table scores
    query_struct = "DESCRIBE scores"
    df_struct = conn.execute(query_struct).df()
    print("\nStructure table scores :")
    print(df_struct)
    
except Exception as e:
    print(f"❌ Table scores : {e}")

# 4. Chercher événements 1er août avec TOUS les importance_n
print("\n4. ÉVÉNEMENTS 1ER AOÛT - TOUTES IMPORTANCES :")
print("-"*100)
query_aug = """
SELECT 
    ts_utc,
    event_title,
    importance_n,
    country,
    actual
FROM events
WHERE country = 'US'
  AND ts_utc >= '2025-08-01 12:00:00'
  AND ts_utc <= '2025-08-01 13:00:00'
ORDER BY ts_utc, importance_n
"""
df_aug = conn.execute(query_aug).df()
print(f"\nÉvénements US 12:00-13:00 UTC (14:00-15:00 CEST) : {len(df_aug)}")
if len(df_aug) > 0:
    for _, row in df_aug.iterrows():
        title = row['event_title'] if row['event_title'] else "Unknown Event"
        print(f"  {row['ts_utc']} | imp={row['importance_n']} | {title[:40]:40s} | A:{row['actual']}")
else:
    print("  ❌ Aucun événement trouvé")

conn.close()

print("\n" + "="*100)
print("INTERPRÉTATION :")
print("="*100)
print("- Si importance_n=1 a peu d'événements → 1=HIGH (inversé)")
print("- Si importance_n=3 a peu d'événements → 3=HIGH (normal)")
print("- Vérifier exemples pour confirmer")
