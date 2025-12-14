"""
LISTE CLUSTERS CPI/NFP DISPONIBLES POUR TESTS
==============================================

Session 98 - Trouver 10-15 CLUSTERS supplémentaires pour validation formule R²

CRITÈRE CLUSTER :
- Plusieurs événements SIMULTANÉS (même date, même heure)
- Minimum 5+ événements groupés
- Country = 'US'
- Score > 40 (HIGH impact)
- Familles : CPI, NFP, Inflation, Employment

Note : Événements isolés seront traités séparément plus tard

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
print("📅 RECHERCHE CLUSTERS CPI/NFP DISPONIBLES")
print("="*80)

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# Query pour trouver CLUSTERS (événements simultanés)
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
    AND ef.empirical_score > 40
    AND (ef.family LIKE '%CPI%' 
         OR ef.family LIKE '%NFP%' 
         OR ef.family LIKE '%Inflation%' 
         OR ef.family LIKE '%Employment%'
         OR ef.family LIKE '%Jobless%')
    AND YEAR(e.ts_utc) >= 2024
GROUP BY DATE(e.ts_utc), strftime(e.ts_utc, '%H:%M:%S'), e.ts_utc
HAVING COUNT(DISTINCT e.event_key) >= 5
ORDER BY date DESC, heure
"""

clusters = conn.execute(query).df()
conn.close()

print(f"\n✅ Clusters trouvés (≥5 événements simultanés) : {len(clusters)}")

# Clusters déjà testés
clusters_testes = [
    ('2025-09-11', '14:30:00'),
    ('2025-01-15', '14:30:00'),
    ('2025-05-13', '14:30:00'),
    ('2025-07-15', '14:30:00')
]

print(f"\n📊 CLUSTERS DISPONIBLES (≥5 events simultanés, score > 40) :")
print(f"   {'Date':12} {'Heure':10} {'Events':>7} {'Score Moy':>10} {'Score Max':>10} {'Familles':30} {'Status':12}")
print(f"   {'-'*100}")

nouveaux_clusters = []

for idx, row in clusters.iterrows():
    date_str = str(row['date'])
    heure_str = row['heure']
    cluster_key = (date_str, heure_str)
    
    status = "✅ TESTÉ" if cluster_key in clusters_testes else "⭐ NOUVEAU"
    
    print(f"   {date_str:12} {heure_str:10} {row['num_events']:>7} {row['score_moyen']:>10.1f} {row['score_max']:>10.1f} {row['families'][:30]:30} {status:12}")
    
    if cluster_key not in clusters_testes:
        nouveaux_clusters.append({
            'date': date_str,
            'heure': heure_str,
            'num_events': row['num_events'],
            'score_moyen': row['score_moyen'],
            'families': row['families']
        })

print(f"\n🎯 STATISTIQUES :")
print(f"   Clusters testés      : {len(clusters_testes)}")
print(f"   Nouveaux clusters    : {len(nouveaux_clusters)}")
print(f"   Cible (10-15 total)  : 10-15 clusters")
print(f"   Total disponible     : {len(clusters)}")

if len(nouveaux_clusters) >= 6:
    print(f"\n✅ Suffisamment de nouveaux clusters pour validation étendue")
    print(f"\n📋 Prochains clusters suggérés (10 premiers) :")
    for i, cluster in enumerate(nouveaux_clusters[:10], 1):
        print(f"   {i:2}. {cluster['date']:12} {cluster['heure']:10} ({cluster['num_events']} events) - {cluster['families'][:40]}")
else:
    print(f"\n⚠️ Seulement {len(nouveaux_clusters)} nouveaux clusters disponibles")
    print(f"   Peut nécessiter critères élargis (score > 35 ou ≥4 événements)")

# Sauvegarder liste complète
output_csv = Path(__file__).parent / "clusters_cpi_nfp_disponibles.csv"
clusters['cluster_key'] = clusters['date'].astype(str) + '_' + clusters['heure']
clusters['status'] = clusters.apply(
    lambda x: 'TESTÉ' if (str(x['date']), x['heure']) in clusters_testes else 'NOUVEAU',
    axis=1
)
clusters.to_csv(output_csv, index=False)

print(f"\n💾 Liste complète sauvegardée : {output_csv}")

# Analyse par type
print(f"\n📊 RÉPARTITION PAR TYPE :")
clusters_cpi = clusters[clusters['families'].str.contains('CPI|Inflation', case=False, na=False)]
clusters_nfp = clusters[clusters['families'].str.contains('NFP|Employment|Jobless', case=False, na=False)]

print(f"   Clusters CPI/Inflation  : {len(clusters_cpi)}")
print(f"   Clusters NFP/Employment : {len(clusters_nfp)}")

print("\n" + "="*80)
print("✅ RECHERCHE CLUSTERS TERMINÉE")
print("="*80)
print(f"\n💡 NOTE : Événements isolés (importance HIGH mais seuls) seront traités")
print(f"           dans un volet séparé ultérieurement.")
