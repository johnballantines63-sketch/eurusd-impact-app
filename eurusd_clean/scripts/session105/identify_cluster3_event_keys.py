#!/usr/bin/env python3
"""
SESSION 105 - IDENTIFICATION event_key CLUSTER #3
==================================================
Objectif : Trouver les event_key EXACTS des 11 événements CPI
qui se répètent chaque mois
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import importlib.util

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

spec_config = importlib.util.spec_from_file_location(
    "config",
    project_root / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
Config = config_module.Config

config = Config()
db_path = config.get_db_path()

print("="*80)
print("SESSION 105 - IDENTIFICATION event_key CLUSTER #3")
print("="*80)
print()

conn = duckdb.connect(str(db_path), read_only=True)

# Date référence : 11.09.2025
date_ref = "2025-09-11"

print(f"📅 Analyse événements US du {date_ref} à 14:30 Bern")
print()

# Charger TOUS les événements US du 11.09 avec leurs event_key
query = """
SELECT 
    e.event_key,
    e.event_title,
    ef.family,
    ef.empirical_score,
    e.actual,
    e.estimate,
    e.forecast,
    e.ts_utc
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
    AND e.ts_utc >= '2025-09-11 14:00:00+02:00'::TIMESTAMP
    AND e.ts_utc < '2025-09-11 15:00:00+02:00'::TIMESTAMP
ORDER BY ef.empirical_score DESC NULLS LAST, e.ts_utc
"""

events = conn.execute(query).fetchdf()

print(f"✅ {len(events)} événements trouvés à 14:30")
print()

# Afficher par score décroissant
print("📊 ÉVÉNEMENTS TRIÉS PAR SCORE :")
print("-"*80)
print(f"{'Score':<8} {'Family':<12} {'event_key':<40} {'event_title'}")
print("-"*80)

for _, row in events.iterrows():
    score = row['empirical_score']
    score_str = f"{score:.1f}" if pd.notna(score) else "NULL"
    family = row['family'] if pd.notna(row['family']) else "NULL"
    event_key = row['event_key']
    title = row['event_title'][:50] if pd.notna(row['event_title']) else "NULL"
    
    print(f"{score_str:<8} {family:<12} {event_key:<40} {title}")

print()

# Filtrer score >= 60 (high impact)
high_impact = events[events['empirical_score'] >= 60]
print(f"🎯 {len(high_impact)} événements HIGH IMPACT (score ≥ 60) :")
print("-"*80)

if len(high_impact) > 0:
    for _, row in high_impact.iterrows():
        print(f"   {row['empirical_score']:.1f} - {row['event_key']}")
else:
    print("   ⚠️ Aucun événement score ≥ 60")

print()

# Filtrer score >= 80 (very high)
very_high = events[events['empirical_score'] >= 80]
print(f"⭐ {len(very_high)} événements VERY HIGH IMPACT (score ≥ 80) :")
print("-"*80)

if len(very_high) > 0:
    for _, row in very_high.iterrows():
        print(f"   {row['empirical_score']:.1f} - {row['event_key']}")
else:
    print("   ⚠️ Aucun événement score ≥ 80")

print()

# Test : Compter combien de fois ces event_key apparaissent
dates_test = [
    "2025-09-11",
    "2025-08-12",
    "2025-07-15",
    "2025-06-11",
    "2025-05-13",
    "2025-04-10"
]

if len(high_impact) > 0:
    event_keys = high_impact['event_key'].tolist()
    
    print("🔍 RÉCURRENCE des event_key sur 6 dates Cluster #3 :")
    print("-"*80)
    
    for event_key in event_keys[:10]:  # Top 10
        query_recurrence = f"""
        SELECT COUNT(DISTINCT DATE(e.ts_utc)) as num_dates
        FROM events e
        WHERE e.event_key = '{event_key}'
            AND e.country = 'US'
            AND DATE(e.ts_utc) IN ({','.join([f"'{d}'" for d in dates_test])})
        """
        
        result = conn.execute(query_recurrence).fetchone()
        num_dates = result[0]
        
        pct = (num_dates / len(dates_test)) * 100
        recurrence = "✅ RÉCURRENT" if num_dates >= 5 else "⚠️ PARTIEL" if num_dates >= 3 else "❌ RARE"
        
        print(f"   {event_key:<45} : {num_dates}/6 dates ({pct:>5.1f}%) {recurrence}")

print()

# Chercher pattern CPI mensuel
print("🎯 RECHERCHE PATTERN CPI MENSUEL :")
print("-"*80)

query_cpi = """
SELECT 
    e.event_key,
    COUNT(DISTINCT DATE(e.ts_utc)) as num_occurrences,
    MIN(DATE(e.ts_utc)) as first_date,
    MAX(DATE(e.ts_utc)) as last_date
FROM events e
WHERE e.country = 'US'
    AND e.event_key LIKE '%CPI%'
    AND DATE(e.ts_utc) >= '2025-01-01'
    AND DATE(e.ts_utc) <= '2025-10-31'
GROUP BY e.event_key
HAVING COUNT(DISTINCT DATE(e.ts_utc)) >= 6
ORDER BY num_occurrences DESC
"""

cpi_events = conn.execute(query_cpi).fetchdf()

if len(cpi_events) > 0:
    print(f"✅ {len(cpi_events)} event_key CPI récurrents (≥6 fois en 2025) :")
    print()
    for _, row in cpi_events.iterrows():
        print(f"   {row['event_key']:<45} : {row['num_occurrences']:>2} fois "
              f"({row['first_date']} → {row['last_date']})")
else:
    print("   ⚠️ Aucun event_key CPI récurrent trouvé")

print()

# Sauvegarder liste event_key
if len(high_impact) > 0:
    output_file = Path(__file__).parent / "cluster3_event_keys_identified.txt"
    with open(output_file, 'w') as f:
        f.write("# Cluster #3 - event_key identifiés\n")
        f.write(f"# Date référence : {date_ref}\n")
        f.write(f"# Nombre total : {len(high_impact)}\n")
        f.write("\n")
        for event_key in high_impact['event_key'].tolist():
            f.write(f"{event_key}\n")
    
    print(f"💾 Liste event_key sauvegardée : {output_file.name}")

conn.close()

print()
print("="*80)
print("✅ IDENTIFICATION TERMINÉE")
print("="*80)
