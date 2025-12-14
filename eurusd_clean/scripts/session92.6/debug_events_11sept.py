#!/usr/bin/env python3
"""
Debug - Vérifier les événements du 11 septembre 2025 SANS filtre importance
"""
from pathlib import Path
import duckdb
import pandas as pd

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("ÉVÉNEMENTS 2025-09-11 - ANALYSE COMPLÈTE")
print("="*80)

# 1. Tous les événements US du 11 septembre
print("\n1️⃣ TOUS LES ÉVÉNEMENTS US (sans filtre importance)")
print("─"*80)

query1 = """
SELECT 
    ts_utc,
    event_title,
    importance_n,
    actual,
    estimate,
    previous
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
AND country = 'US'
ORDER BY ts_utc
"""

df1 = conn.execute(query1).fetchdf()
print(f"\nNombre total: {len(df1)}")
print(f"\nPremiers événements:")
print(df1.head(10).to_string())

# 2. Distribution importance_n
print("\n\n2️⃣ DISTRIBUTION IMPORTANCE_N")
print("─"*80)
importance_counts = df1['importance_n'].value_counts().sort_index()
print(importance_counts)

# 3. Événements avec empirical_score
print("\n\n3️⃣ ÉVÉNEMENTS AVEC EMPIRICAL_SCORE")
print("─"*80)

query3 = """
SELECT 
    e.ts_utc,
    e.event_title,
    e.importance_n,
    e.actual,
    e.estimate,
    ef.family,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
AND e.country = 'US'
AND ef.empirical_score IS NOT NULL
ORDER BY e.ts_utc
"""

df3 = conn.execute(query3).fetchdf()
print(f"\nNombre avec score: {len(df3)}")
if not df3.empty:
    print(f"\nÉvénements avec score:")
    print(df3[['ts_utc', 'event_title', 'importance_n', 'empirical_score', 'actual', 'estimate']].to_string())
    
    # Calcul surprise nette
    print("\n\n4️⃣ CALCUL SURPRISE NETTE")
    print("─"*80)
    
    surprise_net = 0.0
    for _, row in df3.iterrows():
        actual = row['actual']
        estimate = row['estimate']
        
        if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
            surprise_signed = ((actual - estimate) / abs(estimate)) * 100
            surprise_net += surprise_signed
            print(f"{row['event_title'][:40]:40} : {surprise_signed:+7.1f}%")
    
    print(f"\n{'SURPRISE NETTE TOTALE':40} : {surprise_net:+7.1f}%")

# 4. Événements avec empirical_score > 40
print("\n\n5️⃣ ÉVÉNEMENTS AVEC EMPIRICAL_SCORE > 40")
print("─"*80)

query4 = """
SELECT 
    e.ts_utc,
    e.event_title,
    e.importance_n,
    e.actual,
    e.estimate,
    ef.family,
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

df4 = conn.execute(query4).fetchdf()
print(f"\nNombre avec score > 40: {len(df4)}")
if not df4.empty:
    print(f"\nCe sont ces événements qui devraient être utilisés:")
    print(df4[['ts_utc', 'event_title', 'empirical_score', 'actual', 'estimate']].to_string())

conn.close()

print("\n" + "="*80)
print("ANALYSE TERMINÉE")
print("="*80)
