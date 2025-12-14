#!/usr/bin/env python3
"""
SESSION 108 - IDENTIFICATION DATES CLUSTER #1
==============================================
Extraire les 11 dates du Cluster #1 (Manufacturing + Consumer + Employment)
depuis le dataset Session 104
"""
import sys
from pathlib import Path
import pandas as pd
import duckdb

print("="*80)
print("SESSION 108 - IDENTIFICATION CLUSTER #1")
print("="*80)
print()

# Setup
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

import importlib.util
spec_config = importlib.util.spec_from_file_location(
    "config", 
    project_root / "eurusd_clean" / "app" / "config.py"
)
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

# Charger dataset Session 104
data_file = Path(__file__).parent.parent / "session104" / "dataset_44_dates_METHOD_SESSION92_5.csv"
df_dates = pd.read_csv(data_file)

print(f"✅ {len(df_dates)} dates chargées depuis Session 104")
print()

# Filtrer Cluster #1 : Manufacturing + Consumer + Employment avec 8 événements
cluster1_pattern = "Manufacturing|Consumer|Employment"

# Filtrer sur families ET num_events = 8
df_cluster1 = df_dates[
    (df_dates['families'] == cluster1_pattern) & 
    (df_dates['num_events'] == 8)
].copy()

print(f"✅ {len(df_cluster1)} dates identifiées pour Cluster #1")
print()

if len(df_cluster1) == 0:
    print("❌ Aucune date trouvée pour ce pattern")
    sys.exit(1)

# Vérifier composition exacte pour première date
conn = duckdb.connect(str(db_path), read_only=True)

first_date = df_cluster1.iloc[0]['date']
print(f"🔍 VÉRIFICATION COMPOSITION : {first_date}")
print("-"*80)

query = f"""
SELECT e.event_key, ef.family, ef.empirical_score
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE DATE(e.ts_utc) = '{first_date}'
    AND e.country = 'US'
    AND ef.empirical_score > 40
ORDER BY ef.family, e.event_key
"""

events = conn.execute(query).fetchdf()

print(f"Nombre événements : {len(events)}")
print()

# Grouper par famille
families = events.groupby('family')['event_key'].count().to_dict()
print("Composition par famille :")
for family, count in sorted(families.items()):
    print(f"  - {family:20s} : {count} événements")

conn.close()

print()
print("="*80)
print("DATES CLUSTER #1 (Manufacturing + Consumer + Employment)")
print("="*80)
print()

# Trier par date
df_cluster1 = df_cluster1.sort_values('date', ascending=False)

print(f"{'#':3s} | {'Date':10s} | {'Impact':7s} | {'Score':6s} | {'Surprise':8s}")
print("-"*80)

for i, (_, row) in enumerate(df_cluster1.iterrows(), 1):
    print(f"{i:3d} | {row['date']:10s} | {row['impact_real_pips']:6.1f}p | "
          f"{row['avg_score']:5.1f} | {row['surprise_max']:7.2%}")

print()
print("="*80)
print(f"TOTAL : {len(df_cluster1)} dates")
print("="*80)
print()

# Sauvegarder
output_file = Path(__file__).parent / "cluster1_dates.csv"
df_cluster1.to_csv(output_file, index=False)

print(f"✅ Dates sauvegardées : {output_file.name}")
print()

# Statistiques
print("📊 STATISTIQUES CLUSTER #1 :")
print("-"*80)
print(f"Impact moyen : {df_cluster1['impact_real_pips'].mean():.1f} pips")
print(f"Impact médian : {df_cluster1['impact_real_pips'].median():.1f} pips")
print(f"Impact min : {df_cluster1['impact_real_pips'].min():.1f} pips")
print(f"Impact max : {df_cluster1['impact_real_pips'].max():.1f} pips")
print(f"Écart-type : {df_cluster1['impact_real_pips'].std():.1f} pips")
print()

print("="*80)
print("PRÊT POUR PHASE 2E (INVERSION) SUR CLUSTER #1 !")
print("="*80)
