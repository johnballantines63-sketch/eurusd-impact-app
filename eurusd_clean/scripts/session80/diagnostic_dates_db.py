#!/usr/bin/env python3
"""
Session 80 - Diagnostic Dates DB

Objectif : Identifier quelles dates sont RÉELLEMENT dans la DB
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent.parent / "fx_impact_app" / "data" / "warehouse.duckdb"

print("=" * 70)
print("DIAGNOSTIC DATES DB - SESSION 80")
print("=" * 70)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Plage temporelle events
print("📅 PLAGE TEMPORELLE - Table events")
print("-" * 70)

query_range = """
SELECT 
    MIN(DATE(ts_utc)) as date_min,
    MAX(DATE(ts_utc)) as date_max,
    COUNT(*) as total_events,
    COUNT(DISTINCT DATE(ts_utc)) as dates_distinctes
FROM events
"""

result = conn.execute(query_range).fetchone()
print(f"Date minimale  : {result[0]}")
print(f"Date maximale  : {result[1]}")
print(f"Total événements : {result[2]:,}")
print(f"Dates distinctes : {result[3]:,}")
print()

# 2. Distribution par année
print("📊 DISTRIBUTION PAR ANNÉE")
print("-" * 70)

query_years = """
SELECT 
    YEAR(ts_utc) as annee,
    COUNT(*) as nb_events,
    COUNT(DISTINCT DATE(ts_utc)) as nb_dates
FROM events
GROUP BY YEAR(ts_utc)
ORDER BY annee DESC
LIMIT 10
"""

results = conn.execute(query_years).fetchall()
for row in results:
    print(f"  {row[0]} : {row[1]:>6,} événements sur {row[2]:>4} jours")
print()

# 3. Événements CPI/NFP disponibles
print("📋 ÉVÉNEMENTS CPI/NFP DISPONIBLES (10 plus récents)")
print("-" * 70)

query_cpi = """
SELECT 
    DATE(ts_utc) as date,
    strftime(ts_utc, '%H:%M') as heure,
    event_key,
    country
FROM events
WHERE (event_key LIKE '%CPI%' OR event_key LIKE '%NFP%' OR event_key LIKE '%Payroll%')
  AND country = 'US'
ORDER BY ts_utc DESC
LIMIT 10
"""

results = conn.execute(query_cpi).fetchall()
if results:
    print("Date         Heure  Pays  Événement")
    print("-" * 70)
    for row in results:
        print(f"{row[0]}  {row[1]}  {row[3]:<4}  {row[2][:50]}")
else:
    print("❌ Aucun événement CPI/NFP trouvé")

print()

# 4. Dates dans dataset Session 75
print("🎯 DATES DEMANDÉES PAR DATASET SESSION 75")
print("-" * 70)

# Lire le dataset
import pandas as pd
dataset_path = Path(__file__).parent.parent.parent / "data" / "movements_strong_session75_v3.csv"

if dataset_path.exists():
    df = pd.read_csv(dataset_path)
    if 'datetime' in df.columns:
        df['date'] = pd.to_datetime(df['datetime']).dt.date
        dates_dataset = sorted(df['date'].unique())
        
        print(f"Dataset contient {len(dates_dataset)} dates distinctes :")
        print()
        
        for date in dates_dataset[:20]:  # Afficher 20 premières
            # Vérifier si date existe dans DB
            query_check = f"SELECT COUNT(*) FROM events WHERE DATE(ts_utc) = '{date}'"
            count = conn.execute(query_check).fetchone()[0]
            
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {date} → {count:>3} événements dans DB")
        
        if len(dates_dataset) > 20:
            print(f"  ... ({len(dates_dataset) - 20} autres dates)")
    else:
        print("⚠️ Colonne 'datetime' non trouvée dans dataset")
else:
    print(f"⚠️ Dataset non trouvé : {dataset_path}")

conn.close()

print()
print("=" * 70)
print("🎯 CONCLUSION")
print("=" * 70)
print()
print("Si dataset contient dates 2025 et DB max = 2024 →")
print("  → Événements introuvables (0 événements normaux)")
print()
print("Solution :")
print("  1. Filtrer dataset sur dates EXISTANTES dans DB")
print("  2. Ou mettre à jour DB avec données 2025")
print()
