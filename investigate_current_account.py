#!/usr/bin/env python3
"""
INVESTIGATION : Pourquoi Current Account (DE) n'a pas d'empirical_score ?
"""

import duckdb

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=True)

print("\n1️⃣ RECHERCHE DE CURRENT ACCOUNT DANS event_families:\n")

query1 = """
SELECT 
    event_key,
    country,
    family,
    empirical_score,
    impact_level
FROM event_families
WHERE LOWER(event_key) LIKE '%current%account%'
   OR LOWER(family) LIKE '%current%account%'
ORDER BY country, event_key
"""

df1 = conn.execute(query1).fetchdf()
if len(df1) > 0:
    print(df1.to_string(index=False))
else:
    print("❌ Aucun Current Account trouvé dans event_families !")

print("\n2️⃣ RECHERCHE DE CURRENT ACCOUNT DANS events (toutes dates):\n")

query2 = """
SELECT 
    CAST(ts_utc AS DATE) as date,
    strftime(ts_utc, '%H:%M') as time,
    event_key,
    event_title,
    country,
    actual,
    forecast,
    previous
FROM events
WHERE LOWER(event_title) LIKE '%current%account%'
   OR LOWER(event_key) LIKE '%current%account%'
ORDER BY ts_utc DESC
LIMIT 20
"""

df2 = conn.execute(query2).fetchdf()
if len(df2) > 0:
    print(f"Trouvé {len(df2)} occurrences (20 plus récentes) :")
    print(df2.to_string(index=False))
else:
    print("❌ Aucun Current Account trouvé dans events !")

print("\n3️⃣ ÉVÉNEMENTS DE (trade balance) POUR L'ALLEMAGNE:\n")

query3 = """
SELECT 
    event_key,
    country,
    family,
    empirical_score,
    impact_level
FROM event_families
WHERE country = 'DE'
  AND (LOWER(event_key) LIKE '%trade%' 
       OR LOWER(family) LIKE '%trade%'
       OR LOWER(event_key) LIKE '%balance%')
ORDER BY empirical_score DESC NULLS LAST
"""

df3 = conn.execute(query3).fetchdf()
if len(df3) > 0:
    print(df3.to_string(index=False))
else:
    print("❌ Aucun Trade Balance trouvé pour l'Allemagne !")

print("\n4️⃣ TOUS LES ÉVÉNEMENTS DE L'ALLEMAGNE AVEC SCORE > 0:\n")

query4 = """
SELECT 
    event_key,
    family,
    empirical_score,
    impact_level
FROM event_families
WHERE country = 'DE'
  AND empirical_score > 0
ORDER BY empirical_score DESC
LIMIT 15
"""

df4 = conn.execute(query4).fetchdf()
if len(df4) > 0:
    print(f"Top 15 événements DE avec score :")
    print(df4.to_string(index=False))

print("\n5️⃣ VÉRIFICATION : Current Account existe-t-il sous un autre nom ?\n")

query5 = """
SELECT DISTINCT
    event_key,
    event_title,
    country
FROM events
WHERE country = 'DE'
  AND CAST(ts_utc AS DATE) BETWEEN '2024-01-01' AND '2025-12-31'
  AND strftime(ts_utc, '%H:%M') = '14:45'
ORDER BY event_key
"""

df5 = conn.execute(query5).fetchdf()
if len(df5) > 0:
    print(f"Événements DE publiés à 14:45 :")
    print(df5.to_string(index=False))

conn.close()

print("\n" + "="*80)
print("💡 CONCLUSION:")
print("="*80)
print("Si Current Account n'apparaît pas dans event_families,")
print("c'est qu'il n'a jamais été inclus dans le calcul d'empirical_score.")
print("\nPossibilités:")
print("  1. Événement trop récent (ajouté après calcul des scores)")
print("  2. Événement considéré comme non-impactant")
print("  3. Événement mappé sous un autre nom (ex: Trade Balance)")
