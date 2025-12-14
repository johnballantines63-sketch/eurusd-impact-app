#!/usr/bin/env python3
"""
ÉTAPE 0 : EXTRACTION 30 CLUSTERS IDENTIQUES
============================================

Objectif : Sélectionner 30 dates avec des clusters d'événements
           SIMILAIRES au cas validé du 11 septembre 2025

Critères clusters identiques :
- Événements US HIGH impact (score > 40)
- 5-15 événements simultanés par cluster
- Score moyen 40-50
- Diversité temporelle (30 dates distinctes)
- Données prix disponibles dans prices_1m

Méthodologie rigoureuse pour validation hypothèse :
"Tendance forte → Amplification faible"
"""

import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta
import pandas as pd

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 80)
print("ÉTAPE 0 : EXTRACTION 30 CLUSTERS IDENTIQUES")
print("=" * 80)
print()

# ============================================================================
# PARAMÈTRES SÉLECTION
# ============================================================================

# Référence : Cas validé 11 septembre 2025
REFERENCE_NUM_EVENTS = 11
REFERENCE_AVG_SCORE = 44.31

# Critères clusters similaires
MIN_EVENTS = 5      # Minimum 5 événements simultanés
MAX_EVENTS = 15     # Maximum 15 événements simultanés
MIN_AVG_SCORE = 40  # Score moyen minimum
MAX_AVG_SCORE = 50  # Score moyen maximum
MIN_SCORE_EVENT = 40  # Chaque événement doit avoir score > 40

# Période analyse
START_DATE = '2024-01-01'
END_DATE = '2025-10-31'

# Target
TARGET_CLUSTERS = 30

print(f"📋 CRITÈRES SÉLECTION :")
print(f"   Événements par cluster : {MIN_EVENTS}-{MAX_EVENTS}")
print(f"   Score moyen cluster    : {MIN_AVG_SCORE}-{MAX_AVG_SCORE}")
print(f"   Score min par event    : {MIN_SCORE_EVENT}")
print(f"   Période                : {START_DATE} → {END_DATE}")
print(f"   Target                 : {TARGET_CLUSTERS} clusters")
print()

# ============================================================================
# CONNEXION DB
# ============================================================================

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

print(f"✅ Connecté à : {db_path}")
print()

# ============================================================================
# EXTRACTION CLUSTERS
# ============================================================================

print("=" * 80)
print("RECHERCHE CLUSTERS DANS DB")
print("=" * 80)
print()

# Query pour trouver dates avec clusters d'événements HIGH impact
query_clusters = """
WITH event_clusters AS (
    SELECT 
        DATE(e.ts_utc) as event_date,
        COUNT(*) as num_events,
        AVG(ef.empirical_score) as avg_score,
        MIN(ef.empirical_score) as min_score,
        MAX(ef.empirical_score) as max_score,
        STRING_AGG(DISTINCT ef.family, ', ') as families
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > ?
        AND DATE(e.ts_utc) >= ?
        AND DATE(e.ts_utc) <= ?
    GROUP BY DATE(e.ts_utc)
    HAVING COUNT(*) >= ?
       AND COUNT(*) <= ?
       AND AVG(ef.empirical_score) >= ?
       AND AVG(ef.empirical_score) <= ?
)
SELECT 
    event_date,
    num_events,
    avg_score,
    min_score,
    max_score,
    families
FROM event_clusters
ORDER BY event_date DESC
"""

df_clusters = conn.execute(query_clusters, [
    MIN_SCORE_EVENT,
    START_DATE,
    END_DATE,
    MIN_EVENTS,
    MAX_EVENTS,
    MIN_AVG_SCORE,
    MAX_AVG_SCORE
]).fetchdf()

print(f"✅ Trouvé {len(df_clusters)} clusters potentiels")
print()

if len(df_clusters) == 0:
    print("❌ Aucun cluster trouvé avec ces critères !")
    print("   → Relâcher les critères ou élargir la période")
    conn.close()
    sys.exit(1)

# ============================================================================
# VÉRIFICATION DISPONIBILITÉ PRIX
# ============================================================================

print("=" * 80)
print("VÉRIFICATION DISPONIBILITÉ PRIX")
print("=" * 80)
print()

valid_clusters = []

for idx, cluster in df_clusters.iterrows():
    event_date = cluster['event_date']
    
    # Convertir en datetime pour requête
    if isinstance(event_date, str):
        event_date_dt = datetime.strptime(event_date, '%Y-%m-%d')
    else:
        event_date_dt = event_date
    
    # Vérifier si prix disponibles ce jour (UTC)
    # Note : événements à ~12:30 UTC généralement
    query_check_prices = """
    SELECT COUNT(*) as count
    FROM prices_1m
    WHERE DATE(datetime) = ?
    """
    
    result = conn.execute(query_check_prices, [event_date_dt.strftime('%Y-%m-%d')]).fetchdf()
    
    if result['count'][0] > 0:
        valid_clusters.append({
            'event_date': event_date,
            'num_events': cluster['num_events'],
            'avg_score': cluster['avg_score'],
            'min_score': cluster['min_score'],
            'max_score': cluster['max_score'],
            'families': cluster['families']
        })
        
        if len(valid_clusters) <= 5:
            print(f"✅ {event_date} : {cluster['num_events']} events, score={cluster['avg_score']:.1f}")
    
    # Limiter à TARGET_CLUSTERS
    if len(valid_clusters) >= TARGET_CLUSTERS:
        break

print()
print(f"✅ {len(valid_clusters)} clusters avec prix disponibles")
print()

if len(valid_clusters) < TARGET_CLUSTERS:
    print(f"⚠️  Seulement {len(valid_clusters)} clusters trouvés")
    print(f"   Target était {TARGET_CLUSTERS}")
    print(f"   → Continuer avec {len(valid_clusters)} clusters")
    print()

# ============================================================================
# SAUVEGARDER RÉSULTATS
# ============================================================================

print("=" * 80)
print("SAUVEGARDE RÉSULTATS")
print("=" * 80)
print()

df_selected = pd.DataFrame(valid_clusters)

# Trier par date
df_selected = df_selected.sort_values('event_date', ascending=False)

# Sauvegarder CSV
output_path = Path(__file__).parent / "data" / "step0_selected_clusters.csv"
df_selected.to_csv(output_path, index=False)

print(f"✅ Sauvegardé : {output_path}")
print()

# ============================================================================
# STATISTIQUES
# ============================================================================

print("=" * 80)
print("STATISTIQUES CLUSTERS SÉLECTIONNÉS")
print("=" * 80)
print()

print(f"Nombre de clusters       : {len(df_selected)}")
print(f"Période couverte         : {df_selected['event_date'].min()} → {df_selected['event_date'].max()}")
print()

print("Distribution événements par cluster :")
print(df_selected['num_events'].describe())
print()

print("Distribution score moyen :")
print(df_selected['avg_score'].describe())
print()

print("Familles d'événements les plus fréquentes :")
all_families = []
for families_str in df_selected['families']:
    if pd.notna(families_str):
        all_families.extend([f.strip() for f in families_str.split(',')])

from collections import Counter
family_counts = Counter(all_families)
for family, count in family_counts.most_common(10):
    print(f"   {family:30s} : {count:3d}")

print()

# ============================================================================
# APERÇU CLUSTERS
# ============================================================================

print("=" * 80)
print("APERÇU 10 PREMIERS CLUSTERS")
print("=" * 80)
print()

for idx, cluster in df_selected.head(10).iterrows():
    print(f"{cluster['event_date']} : {cluster['num_events']} events, score={cluster['avg_score']:.1f}")

print()

# ============================================================================
# COMPARAISON AVEC RÉFÉRENCE
# ============================================================================

print("=" * 80)
print("COMPARAISON AVEC CAS RÉFÉRENCE (11 SEPTEMBRE 2025)")
print("=" * 80)
print()

print(f"Référence :")
print(f"   Événements : {REFERENCE_NUM_EVENTS}")
print(f"   Score moyen : {REFERENCE_AVG_SCORE:.2f}")
print()

print(f"Clusters sélectionnés :")
print(f"   Événements (moyenne) : {df_selected['num_events'].mean():.1f}")
print(f"   Score moyen (moyenne) : {df_selected['avg_score'].mean():.2f}")
print()

# Vérifier similarité
num_events_diff = abs(df_selected['num_events'].mean() - REFERENCE_NUM_EVENTS)
score_diff = abs(df_selected['avg_score'].mean() - REFERENCE_AVG_SCORE)

if num_events_diff < 3 and score_diff < 5:
    print("✅✅ Clusters très similaires à la référence !")
elif num_events_diff < 5 and score_diff < 10:
    print("✅ Clusters similaires à la référence")
else:
    print("⚠️  Clusters légèrement différents de la référence")

print()

conn.close()

print("=" * 80)
print("✅ ÉTAPE 0 TERMINÉE")
print("=" * 80)
print()
print(f"Prochaine étape : step1_calculate_predicted_impacts.py")
print(f"   → Calculer impact prédit pour chaque cluster")
