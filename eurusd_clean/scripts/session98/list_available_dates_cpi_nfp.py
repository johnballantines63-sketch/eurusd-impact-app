"""
LISTE DATES CPI/NFP DISPONIBLES POUR TESTS
===========================================

Session 98 - Trouver 10-15 dates supplémentaires pour validation formule R²

Critères :
- Country = 'US'
- Score > 40 (HIGH impact)
- Familles : CPI ou NFP
- Année 2024-2025

Date : 29 octobre 2025
"""

import sys
from pathlib import Path

# Ajouter chemins
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

import pandas as pd
import duckdb
from config import get_db_path

print("="*80)
print("📅 RECHERCHE DATES CPI/NFP DISPONIBLES")
print("="*80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# Query pour trouver dates HIGH CPI/NFP
query = """
SELECT 
    DATE(e.ts_utc) as date,
    COUNT(DISTINCT e.event_key) as num_events,
    AVG(ef.empirical_score) as score_moyen,
    MAX(ef.empirical_score) as score_max,
    STRING_AGG(DISTINCT ef.family, ', ') as families
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE e.country = 'US'
    AND ef.empirical_score > 40
    AND (ef.family LIKE '%CPI%' OR ef.family LIKE '%NFP%' OR ef.family LIKE '%Inflation%' OR ef.family LIKE '%Employment%')
    AND YEAR(e.ts_utc) >= 2024
GROUP BY DATE(e.ts_utc)
ORDER BY date DESC
"""

dates = conn.execute(query).df()
conn.close()

print(f"\n✅ Dates trouvées : {len(dates)}")

# Dates déjà testées
dates_testees = ['2025-09-11', '2025-01-15', '2025-05-13', '2025-07-15']

print(f"\n📊 DATES DISPONIBLES (score > 40) :")
print(f"   {'Date':12} {'Events':>7} {'Score Moy':>10} {'Score Max':>10} {'Familles':30}")
print(f"   {'-'*80}")

nouvelles_dates = []

for idx, row in dates.iterrows():
    date_str = str(row['date'])
    status = "✅ TESTÉE" if date_str in dates_testees else "⭐ NOUVELLE"
    
    print(f"   {date_str:12} {row['num_events']:>7} {row['score_moyen']:>10.1f} {row['score_max']:>10.1f} {row['families']:30} {status}")
    
    if date_str not in dates_testees:
        nouvelles_dates.append(date_str)

print(f"\n🎯 RECOMMANDATION TESTS :")
print(f"   Dates déjà testées  : {len(dates_testees)}")
print(f"   Nouvelles dates     : {len(nouvelles_dates)}")
print(f"   Cible (10-15 dates) : {10-15} dates")

if len(nouvelles_dates) >= 10:
    print(f"\n✅ Suffisamment de dates disponibles pour validation étendue")
    print(f"\n📋 Prochaines dates suggérées (10 premières) :")
    for i, date in enumerate(nouvelles_dates[:10], 1):
        print(f"   {i:2}. {date}")
else:
    print(f"\n⚠️ Seulement {len(nouvelles_dates)} nouvelles dates - Peut nécessiter critères élargis")

# Sauvegarder liste complète
output_csv = Path(__file__).parent / "dates_cpi_nfp_disponibles.csv"
dates['status'] = dates['date'].apply(lambda x: 'TESTÉE' if str(x) in dates_testees else 'NOUVELLE')
dates.to_csv(output_csv, index=False)

print(f"\n💾 Liste complète sauvegardée : {output_csv}")

print("\n" + "="*80)
print("✅ RECHERCHE TERMINÉE")
print("="*80)
