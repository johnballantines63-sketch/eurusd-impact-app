#!/usr/bin/env python3
"""
IDENTIFIER CLUSTERS D'ÉVÉNEMENTS RÉCURRENTS
============================================
Approche scientifique : Trouver clusters IDENTIQUES (mêmes event_key)
qui se répètent à dates récurrentes (ex: CPI mensuel)
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import importlib.util
from collections import defaultdict

print("="*80)
print("IDENTIFICATION CLUSTERS RÉCURRENTS (MÊME COMPOSITION)")
print("="*80)
print()

# Config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
spec_config = importlib.util.spec_from_file_location("config", project_root / "app" / "config.py")
config_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config_module)
config = config_module.Config()
db_path = Path(config.get_db_path())

# Charger les 35 dates
data_file = Path(__file__).parent / "dataset_44_dates_METHOD_SESSION92_5.csv"
df_dates = pd.read_csv(data_file)

print(f"✅ {len(df_dates)} dates à analyser")
print()

conn = duckdb.connect(str(db_path), read_only=True)

# Pour chaque date, extraire composition cluster (event_key)
clusters = {}

print("🔍 Extraction composition clusters...")
print()

for idx, row in df_dates.iterrows():
    date_str = row['date']
    
    # Charger événements de cette date
    query = f"""
    SELECT e.event_key, ef.family, ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{date_str}'
        AND e.country = 'US'
        AND ef.empirical_score > 40
    ORDER BY e.event_key
    """
    
    events = conn.execute(query).fetchdf()
    
    if len(events) == 0:
        continue
    
    # Créer signature cluster = ensemble trié des event_key
    event_keys = tuple(sorted(events['event_key'].tolist()))
    
    clusters[date_str] = {
        'signature': event_keys,
        'num_events': len(events),
        'families': events['family'].unique().tolist(),
        'impact': row['impact_real_pips']
    }

conn.close()

# Grouper par signature identique
signature_groups = defaultdict(list)

for date, info in clusters.items():
    signature_groups[info['signature']].append(date)

print("="*80)
print("CLUSTERS RÉCURRENTS IDENTIFIÉS")
print("="*80)
print()

# Filtrer seulement clusters qui se répètent ≥2 fois
recurring_clusters = {sig: dates for sig, dates in signature_groups.items() if len(dates) >= 2}

print(f"✅ {len(recurring_clusters)} clusters récurrents trouvés (≥2 occurrences)")
print()

# Afficher chaque cluster récurrent
cluster_num = 0
for signature, dates in sorted(recurring_clusters.items(), key=lambda x: len(x[1]), reverse=True):
    cluster_num += 1
    
    # Info premier cluster
    first_date = dates[0]
    info = clusters[first_date]
    
    print(f"{'='*80}")
    print(f"CLUSTER #{cluster_num} : {len(dates)} occurrences")
    print(f"{'='*80}")
    print()
    print(f"Composition : {info['num_events']} événements")
    print(f"Families    : {', '.join(set(info['families']))}")
    print()
    
    # Afficher event_key (premiers 3)
    print(f"Événements (signature) :")
    for i, key in enumerate(signature[:3]):
        print(f"  - {key}")
    if len(signature) > 3:
        print(f"  ... et {len(signature)-3} autres")
    print()
    
    # Dates et impacts
    print(f"Dates récurrentes :")
    print("-"*80)
    for date in sorted(dates, reverse=True):
        impact = clusters[date]['impact']
        marker = "🎯" if date == "2025-09-11" else "  "
        print(f"  {marker} {date} : {impact:5.1f} pips")
    
    # Stats
    impacts = [clusters[d]['impact'] for d in dates]
    print()
    print(f"Impact moyen : {sum(impacts)/len(impacts):.1f} pips")
    print(f"Écart-type   : {pd.Series(impacts).std():.1f} pips")
    print(f"Min/Max      : {min(impacts):.1f} / {max(impacts):.1f} pips")
    print()

print("="*80)
print("RÉSUMÉ POUR VALIDATION SCIENTIFIQUE")
print("="*80)
print()

print("Clusters recommandés (≥3 occurrences) :")
print()

for signature, dates in sorted(recurring_clusters.items(), key=lambda x: len(x[1]), reverse=True):
    if len(dates) >= 3:
        info = clusters[dates[0]]
        print(f"  ✅ {len(dates):2d}× | {info['num_events']:2d} events | {', '.join(set(info['families']))}")

print()
print("Ces clusters permettent calibration intra-groupe :")
print("  - Même composition événements")
print("  - Variables : surprise, R², amplitude changent")
print("  - Isolation effet sur amp_optimal")
