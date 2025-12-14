"""
DEBUG - QUELS ÉVÉNEMENTS LE 11 SEPTEMBRE ?
===========================================

Compare événements chargés avec seuil 35 vs 40
"""

import sys
from pathlib import Path
import duckdb

project_root = Path(__file__).resolve().parents[3]
DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"

print("="*80)
print("🔍 ÉVÉNEMENTS 11 SEPTEMBRE 2025")
print("="*80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Test avec seuil 35
print("\n📊 ÉVÉNEMENTS AVEC SEUIL > 35 :")
print("-"*80)
query_35 = """
SELECT 
    e.ts_utc,
    e.event_title,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
    AND ef.empirical_score > 35
ORDER BY e.ts_utc
"""
df_35 = conn.execute(query_35).fetchdf()
print(df_35.to_string(index=False))

# Test avec seuil 40
print("\n\n📊 ÉVÉNEMENTS AVEC SEUIL > 40 :")
print("-"*80)
query_40 = """
SELECT 
    e.ts_utc,
    e.event_title,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
"""
df_40 = conn.execute(query_40).fetchdf()
print(df_40.to_string(index=False))

print("\n\n🔍 ANALYSE :")
print("-"*80)
print(f"Nombre événements (seuil > 35) : {len(df_35)}")
print(f"Nombre événements (seuil > 40) : {len(df_40)}")

if len(df_35) > 0:
    print(f"\n✅ Premier événement (seuil > 35) :")
    print(f"   Time  : {df_35.iloc[0]['ts_utc']}")
    print(f"   Event : {df_35.iloc[0]['event_title']}")
    print(f"   Score : {df_35.iloc[0]['empirical_score']}")

if len(df_40) > 0:
    print(f"\n✅ Premier événement (seuil > 40) :")
    print(f"   Time  : {df_40.iloc[0]['ts_utc']}")
    print(f"   Event : {df_40.iloc[0]['event_title']}")
    print(f"   Score : {df_40.iloc[0]['empirical_score']}")

if len(df_35) != len(df_40):
    print(f"\n🚨 PROBLÈME IDENTIFIÉ !")
    print(f"   Le seuil 35 charge {len(df_35) - len(df_40)} événement(s) supplémentaire(s)")
    print(f"   → Le 'premier événement' est DIFFÉRENT selon le seuil !")
    print(f"   → Cela change complètement la mesure d'impact !")

conn.close()

print("\n" + "="*80)
