#!/usr/bin/env python3
"""
Scanner Session 75 - Version Inline Exécutable
Combine scanner + exécution + vérification
"""

import sys
from pathlib import Path

fx_impact_app_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app")
sys.path.insert(0, str(fx_impact_app_path))

import duckdb
import pandas as pd

DB_PATH = fx_impact_app_path / "data" / "warehouse.duckdb"
OUTPUT_CSV = fx_impact_app_path / "data" / "movements_strong_session75_stratified.csv"

print("\n" + "="*70)
print("SCANNER SESSION 75 - ÉCHANTILLONNAGE STRATIFIÉ")
print("="*70 + "\n")

# Connexion DB
print("🔌 Connexion database...")
conn = duckdb.connect(str(DB_PATH), read_only=True)

# Scanner TOUS mouvements >80 pips
print("\n🔍 Scanner TOUS mouvements >80 pips (2024-2025)...")

query = """
WITH price_changes AS (
    SELECT 
        DATE(datetime) as date,
        strftime(datetime, '%H:%M') as time,
        datetime,
        close,
        LAG(close, 120) OVER (ORDER BY datetime) as price_start,
        (close - LAG(close, 120) OVER (ORDER BY datetime)) * 10000 as impact_pips,
        CASE 
            WHEN (close - LAG(close, 120) OVER (ORDER BY datetime)) > 0 
            THEN 'UP'
            ELSE 'DOWN'
        END as direction
    FROM prices_1m
    WHERE datetime >= '2024-01-01' AND datetime <= '2025-10-24'
)
SELECT 
    date,
    time,
    datetime,
    close as price_peak,
    price_start,
    impact_pips,
    direction,
    ABS(impact_pips) as abs_impact
FROM price_changes
WHERE ABS(impact_pips) >= 80
ORDER BY datetime ASC
"""

df_all = conn.execute(query).fetchdf()
conn.close()

print(f"✅ Mouvements totaux : {len(df_all)}")

if len(df_all) == 0:
    print("❌ Aucun mouvement détecté")
    sys.exit(1)

# Échantillonnage stratifié
print("\n📅 Échantillonnage stratifié (top 2 par semaine)...")

df_all['datetime_parsed'] = pd.to_datetime(df_all['datetime'])
df_all['year'] = df_all['datetime_parsed'].dt.isocalendar().year
df_all['week'] = df_all['datetime_parsed'].dt.isocalendar().week

df_stratified = []
for (year, week), group in df_all.groupby(['year', 'week']):
    top_week = group.nlargest(2, 'abs_impact')
    df_stratified.append(top_week)

df_result = pd.concat(df_stratified, ignore_index=True)
df_result = df_result.sort_values('datetime').reset_index(drop=True)

print(f"✅ Mouvements échantillonnés : {len(df_result)}")
print(f"✅ Dates uniques : {df_result['date'].nunique()}")
print(f"✅ Semaines : {len(df_result.groupby(['year', 'week']))}")

# Vérification diversité
dates_count = df_result['date'].value_counts()
max_same_day = dates_count.max()

print(f"\n✅ Vérification diversité :")
print(f"   Max mouvements même jour : {max_same_day}")

if max_same_day > 5:
    print(f"   ⚠️  {max_same_day} mouvements sur même date")
    print(f"   Dates concernées :")
    for date, count in dates_count.head(3).items():
        print(f"      {date} : {count} mouvements")
else:
    print(f"   ✅ EXCELLENT diversité (<5 par jour)")

# Statistiques
print(f"\n📊 Statistiques :")
print(f"   Impact moyen : {df_result['abs_impact'].mean():.1f} pips")
print(f"   Impact médiane : {df_result['abs_impact'].median():.1f} pips")
print(f"   Impact max : {df_result['abs_impact'].max():.1f} pips")
print(f"   Direction UP : {(df_result['direction'] == 'UP').sum() / len(df_result) * 100:.1f}%")

# Top 10
print(f"\n📈 Top 10 mouvements :")
for idx, row in df_result.nlargest(10, 'abs_impact').iterrows():
    print(f"   {idx+1:2d}. {row['date']} {row['time']} : "
          f"{row['direction']} {abs(row['impact_pips']):6.1f} pips")

# Export
print(f"\n💾 Export CSV...")
df_export = df_result[[
    'date', 'time', 'datetime', 
    'price_start', 'price_peak', 
    'impact_pips', 'direction', 'abs_impact',
    'year', 'week'
]]
df_export.to_csv(OUTPUT_CSV, index=False)

print(f"✅ Fichier créé : {OUTPUT_CSV.name}")
print(f"   Lignes : {len(df_export)}")

print(f"\n{'='*70}")
print("SCANNER SESSION 75 COMPLÉTÉ")
print("="*70)
