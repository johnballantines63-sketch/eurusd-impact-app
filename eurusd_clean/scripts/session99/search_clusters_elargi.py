"""
RECHERCHE CLUSTERS ÉLARGIS POUR 30+ DATES
==========================================

Session 99 - Extension : Critères élargis pour atteindre 30+ dates

CRITÈRES ÉLARGIS :
- Country = 'US'
- Score > 35 (vs 40)
- Events ≥ 5 simultanés
- Année ≥ 2023 (vs 2024)
- Type = CPI clusters

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
print("🔍 RECHERCHE CLUSTERS ÉLARGIS (Score > 35, Année ≥ 2023)")
print("="*80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# Query clusters avec critères élargis
query = """
SELECT 
    DATE(e.ts_utc) as date,
    strftime(e.ts_utc, '%H:%M:%S') as heure,
    e.ts_utc as timestamp_complet,
    COUNT(DISTINCT e.event_key) as num_events,
    AVG(ef.empirical_score) as score_moyen,
    MAX(ef.empirical_score) as score_max,
    STRING_AGG(DISTINCT ef.family, ', ') as families
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE e.country = 'US'
    AND ef.empirical_score > 35
    AND ef.family LIKE '%CPI%'
    AND YEAR(e.ts_utc) >= 2023
GROUP BY DATE(e.ts_utc), strftime(e.ts_utc, '%H:%M:%S'), e.ts_utc
HAVING COUNT(DISTINCT e.event_key) >= 5
ORDER BY date DESC, heure
"""

clusters = conn.execute(query).df()
conn.close()

print(f"\n✅ Clusters trouvés (≥5 events, score > 35, année ≥ 2023) : {len(clusters)}")

# Charger dates déjà utilisées (20 dates S99)
dates_s99_file = Path(__file__).parent / "dates_validation_20.csv"
if dates_s99_file.exists():
    df_s99 = pd.read_csv(dates_s99_file)
    dates_utilisees = df_s99['date'].tolist()
    print(f"   Dates déjà utilisées (S99) : {len(dates_utilisees)}")
else:
    dates_utilisees = []
    print(f"   ⚠️  Fichier dates_validation_20.csv non trouvé")

# Filtrer nouvelles dates
clusters_nouveaux = clusters[~clusters['date'].astype(str).isin(dates_utilisees)]
print(f"   Nouvelles dates disponibles : {len(clusters_nouveaux)}")

print(f"\n📊 TOTAL POTENTIEL : {len(dates_utilisees)} (déjà utilisées) + {len(clusters_nouveaux)} (nouvelles) = {len(dates_utilisees) + len(clusters_nouveaux)} dates")

if len(dates_utilisees) + len(clusters_nouveaux) >= 30:
    print(f"   ✅ SUFFISANT pour 30+ dates !")
else:
    print(f"   ⚠️  INSUFFISANT - Seulement {len(dates_utilisees) + len(clusters_nouveaux)} dates")
    print(f"   → Besoin élargir encore critères (score > 30 ou inclure NFP)")

# Afficher nouvelles dates
if len(clusters_nouveaux) > 0:
    print(f"\n📋 NOUVELLES DATES DISPONIBLES :")
    print(f"   {'Date':12} {'Heure':10} {'Events':>7} {'Score Moy':>10} {'Score Max':>10}")
    print(f"   {'-'*60}")
    
    for idx, row in clusters_nouveaux.iterrows():
        date_str = str(row['date'])
        heure_str = row['heure']
        print(f"   {date_str:12} {heure_str:10} {row['num_events']:>7} {row['score_moyen']:>10.1f} {row['score_max']:>10.1f}")

# Sauvegarder liste complète
output_csv = Path(__file__).parent / "clusters_elargi_30plus.csv"
clusters['status'] = clusters['date'].astype(str).apply(
    lambda x: 'UTILISÉ' if x in dates_utilisees else 'NOUVEAU'
)
clusters.to_csv(output_csv, index=False)

print(f"\n💾 Liste complète sauvegardée : {output_csv}")

# Créer fichier 30+ dates
if len(dates_utilisees) + len(clusters_nouveaux) >= 30:
    # Sélectionner top 10+ nouvelles dates (plus récentes)
    n_needed = max(30 - len(dates_utilisees), 10)
    nouvelles_selectionnees = clusters_nouveaux.sort_values('date', ascending=False).head(n_needed)
    
    # Combiner avec 20 dates existantes
    if dates_s99_file.exists():
        df_combined = pd.concat([
            df_s99,
            pd.DataFrame({
                'date': nouvelles_selectionnees['date'].astype(str),
                'heure': nouvelles_selectionnees['heure'],
                'timestamp_complet': nouvelles_selectionnees['timestamp_complet'],
                'num_events': nouvelles_selectionnees['num_events'],
                'score_moyen': nouvelles_selectionnees['score_moyen'],
                'tested_s98': 'NON'
            })
        ])
        
        output_30 = Path(__file__).parent / "dates_validation_30plus.csv"
        df_combined.to_csv(output_30, index=False)
        
        print(f"\n✅ Fichier 30+ dates créé : {output_30}")
        print(f"   Total : {len(df_combined)} dates")
        print(f"   - Dates S99 (20) : {len(df_s99)}")
        print(f"   - Nouvelles      : {len(nouvelles_selectionnees)}")

print("\n" + "="*80)
print("✅ RECHERCHE CLUSTERS ÉLARGIS TERMINÉE")
print("="*80)
