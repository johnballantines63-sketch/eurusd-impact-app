#!/usr/bin/env python3
"""
INVENTAIRE CLUSTERS - IDENTIFICATION COMPLÈTE
==============================================

Script pour identifier TOUS les clusters d'événements disponibles dans la DB
et déterminer lesquels sont testables pour la calibration du seuil de score.

DÉFINITION CLUSTER:
Un cluster = groupe d'événements sortant simultanément (même date + même heure)
Exemple: 11 sept 2025 14:30:00 → 11 événements CPI = 1 cluster

OBJECTIFS:
1. Identifier tous les clusters dans la DB (3 dernières années)
2. Catégoriser par type (CPI, NFP, Retail Sales, etc.)
3. Filtrer les clusters testables (données complètes)
4. Calculer statistiques par type
5. Générer liste complète pour tests de calibration

CRITÈRES CLUSTER TESTABLE:
- Au moins 3 événements dans le cluster
- Données complètes (actual, estimate, score)
- Au moins 1 surprise > 5% (événement significatif)

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import duckdb

# Chemins
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent.parent.parent
db_path = project_root / 'eurusd_clean' / 'app' / 'data' / 'warehouse.duckdb'

print("="*80)
print("🔍 INVENTAIRE COMPLET DES CLUSTERS")
print("="*80)

# Vérifier DB
if not db_path.exists():
    print(f"❌ Base de données introuvable: {db_path}")
    sys.exit(1)

print(f"\n📁 Base de données: {db_path.name}")

# ══════════════════════════════════════════════════════════════════════
# PHASE 1: CHARGEMENT ÉVÉNEMENTS (3 DERNIÈRES ANNÉES)
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 PHASE 1 : CHARGEMENT ÉVÉNEMENTS")
print("="*80)

con = duckdb.connect(str(db_path), read_only=True)

# Période : 3 dernières années
date_end = datetime(2025, 11, 4)  # Aujourd'hui
date_start = datetime(2022, 11, 4)  # -3 ans

print(f"\nPériode analysée:")
print(f"  Début: {date_start.strftime('%Y-%m-%d')}")
print(f"  Fin:   {date_end.strftime('%Y-%m-%d')}")
print(f"  Durée: {(date_end - date_start).days} jours (~{(date_end - date_start).days / 365:.1f} ans)")

# Requête TOUS les événements US avec score
query = """
SELECT 
    e.event_key,
    e.event_title as label,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.previous,
    ef.family,
    ef.empirical_score,
    ef.latency_median,
    DATE(e.ts_utc) as event_date,
    HOUR(e.ts_utc) as event_hour,
    MINUTE(e.ts_utc) as event_minute
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.ts_utc >= ?
    AND e.ts_utc <= ?
    AND e.country = 'US'
    AND ef.empirical_score IS NOT NULL
ORDER BY e.ts_utc
"""

print(f"\n🔄 Chargement événements...")
df_events = con.execute(query, [date_start, date_end]).df()

print(f"✅ {len(df_events)} événements chargés")
print(f"   Score moyen: {df_events['empirical_score'].mean():.2f}")
print(f"   Score range: [{df_events['empirical_score'].min():.2f}, {df_events['empirical_score'].max():.2f}]")

# ══════════════════════════════════════════════════════════════════════
# PHASE 2: IDENTIFICATION CLUSTERS
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 PHASE 2 : IDENTIFICATION CLUSTERS")
print("="*80)

# Créer identifiant cluster (date + heure + minute)
df_events['cluster_id'] = (
    df_events['event_date'].astype(str) + '_' + 
    df_events['event_hour'].astype(str).str.zfill(2) + ':' + 
    df_events['event_minute'].astype(str).str.zfill(2)
)

# Grouper par cluster
clusters = df_events.groupby('cluster_id').agg({
    'event_key': 'count',
    'event_date': 'first',
    'event_hour': 'first',
    'event_minute': 'first',
    'empirical_score': ['mean', 'min', 'max'],
    'family': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Mixed',
    'ts_utc': 'first'
}).reset_index()

# Renommer colonnes
clusters.columns = [
    'cluster_id', 'num_events', 'date', 'hour', 'minute',
    'score_mean', 'score_min', 'score_max', 'dominant_family', 'timestamp'
]

print(f"\n✅ {len(clusters)} clusters identifiés")
print(f"   Événements par cluster (médiane): {clusters['num_events'].median():.0f}")
print(f"   Événements par cluster (max): {clusters['num_events'].max():.0f}")

# ══════════════════════════════════════════════════════════════════════
# PHASE 3: ANALYSE DÉTAILS PAR CLUSTER
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 PHASE 3 : ANALYSE DÉTAILS CLUSTERS")
print("="*80)

# Ajouter infos complémentaires
cluster_details = []

for _, cluster in clusters.iterrows():
    cluster_id = cluster['cluster_id']
    
    # Événements du cluster
    events_in_cluster = df_events[df_events['cluster_id'] == cluster_id]
    
    # Calculer surprises
    surprises = []
    for _, event in events_in_cluster.iterrows():
        actual = event['actual']
        estimate = event['estimate']
        
        if pd.notna(actual) and pd.notna(estimate) and abs(estimate) > 0.01:
            surp = abs((actual - estimate) / estimate) * 100
            surprises.append(min(surp, 500.0))
    
    max_surprise = max(surprises) if surprises else 0.0
    avg_surprise = np.mean(surprises) if surprises else 0.0
    num_surprises = len(surprises)
    
    # Vérifier complétude données
    num_complete = events_in_cluster[
        pd.notna(events_in_cluster['actual']) & 
        pd.notna(events_in_cluster['estimate'])
    ].shape[0]
    
    completeness = num_complete / cluster['num_events'] * 100
    
    # Identifier type cluster (CPI, NFP, Retail, etc.)
    event_keys = events_in_cluster['event_key'].str.lower()
    
    if event_keys.str.contains('cpi|inflation').any():
        cluster_type = 'CPI'
    elif event_keys.str.contains('nfp|non farm|payroll').any():
        cluster_type = 'NFP'
    elif event_keys.str.contains('retail').any():
        cluster_type = 'Retail Sales'
    elif event_keys.str.contains('jobless|claims').any():
        cluster_type = 'Jobless Claims'
    elif event_keys.str.contains('gdp').any():
        cluster_type = 'GDP'
    elif event_keys.str.contains('ppi').any():
        cluster_type = 'PPI'
    else:
        cluster_type = 'Other'
    
    # Cluster testable ?
    is_testable = (
        cluster['num_events'] >= 3 and
        completeness >= 50 and
        max_surprise >= 5.0
    )
    
    cluster_details.append({
        'cluster_id': cluster_id,
        'date': cluster['date'],
        'time': f"{cluster['hour']:02d}:{cluster['minute']:02d}",
        'timestamp': cluster['timestamp'],
        'num_events': cluster['num_events'],
        'score_mean': cluster['score_mean'],
        'score_min': cluster['score_min'],
        'score_max': cluster['score_max'],
        'max_surprise': max_surprise,
        'avg_surprise': avg_surprise,
        'num_surprises': num_surprises,
        'completeness_pct': completeness,
        'cluster_type': cluster_type,
        'dominant_family': cluster['dominant_family'],
        'is_testable': is_testable
    })

df_clusters = pd.DataFrame(cluster_details)

print(f"\n📈 Statistiques complétude:")
print(f"   Moyenne: {df_clusters['completeness_pct'].mean():.1f}%")
print(f"   Clusters 100% complets: {(df_clusters['completeness_pct'] == 100).sum()}")
print(f"   Clusters > 50% complets: {(df_clusters['completeness_pct'] > 50).sum()}")

# ══════════════════════════════════════════════════════════════════════
# PHASE 4: FILTRAGE CLUSTERS TESTABLES
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 PHASE 4 : CLUSTERS TESTABLES")
print("="*80)

df_testable = df_clusters[df_clusters['is_testable'] == True].copy()

print(f"\n✅ {len(df_testable)} clusters testables identifiés")
print(f"   ({len(df_testable) / len(df_clusters) * 100:.1f}% du total)")

# Statistiques par type
print(f"\n📋 Répartition par type:")
type_counts = df_testable['cluster_type'].value_counts()
for cluster_type, count in type_counts.items():
    pct = count / len(df_testable) * 100
    print(f"   {cluster_type:<20}: {count:>3} clusters ({pct:>5.1f}%)")

# ══════════════════════════════════════════════════════════════════════
# PHASE 5: FOCUS SUR CPI, NFP, RETAIL SALES
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 PHASE 5 : FOCUS CPI / NFP / RETAIL SALES")
print("="*80)

target_types = ['CPI', 'NFP', 'Retail Sales']
df_target = df_testable[df_testable['cluster_type'].isin(target_types)].copy()

print(f"\n✅ {len(df_target)} clusters CPI/NFP/Retail testables")

for cluster_type in target_types:
    df_type = df_target[df_target['cluster_type'] == cluster_type]
    
    if len(df_type) > 0:
        print(f"\n📊 {cluster_type}:")
        print(f"   Nombre: {len(df_type)}")
        print(f"   Score moyen: {df_type['score_mean'].mean():.2f}")
        print(f"   Surprise max moyenne: {df_type['max_surprise'].mean():.2f}%")
        print(f"   Événements/cluster (médiane): {df_type['num_events'].median():.0f}")
        
        # Top 5 clusters
        top5 = df_type.nlargest(5, 'max_surprise')[['date', 'time', 'num_events', 'max_surprise', 'score_mean']]
        print(f"   Top 5 surprises:")
        for i, row in top5.iterrows():
            print(f"     {row['date']} {row['time']} : {row['max_surprise']:.1f}% surprise, {row['num_events']} events, score {row['score_mean']:.1f}")

# ══════════════════════════════════════════════════════════════════════
# PHASE 6: RECOMMANDATIONS MÉTHODOLOGIQUES
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 PHASE 6 : RECOMMANDATIONS")
print("="*80)

num_cpi = len(df_target[df_target['cluster_type'] == 'CPI'])
num_nfp = len(df_target[df_target['cluster_type'] == 'NFP'])
num_retail = len(df_target[df_target['cluster_type'] == 'Retail Sales'])

print(f"\n📋 Clusters disponibles pour calibration:")
print(f"   CPI:          {num_cpi} clusters")
print(f"   NFP:          {num_nfp} clusters")
print(f"   Retail Sales: {num_retail} clusters")
print(f"   TOTAL:        {len(df_target)} clusters")

print(f"\n💡 Recommandations méthodologiques:")

if len(df_target) >= 30:
    print(f"   ✅ Échantillon suffisant ({len(df_target)} clusters)")
    print(f"   ✅ Test multi-seuils [0, 10, 20, 30, 40, 50] possible")
    print(f"   ✅ Validation croisée recommandée (train/test split)")
else:
    print(f"   ⚠️ Échantillon limité ({len(df_target)} clusters)")
    print(f"   ⚠️ Utiliser tous les clusters pour calibration (pas de split)")
    print(f"   ⚠️ Interpréter résultats avec prudence")

if num_cpi >= 10 and num_nfp >= 10 and num_retail >= 10:
    print(f"   ✅ Analyse séparée par type possible")
else:
    print(f"   ⚠️ Certains types sous-représentés")
    print(f"      → Recommandé: analyse globale + notes sur types")

# ══════════════════════════════════════════════════════════════════════
# PHASE 7: SAUVEGARDE RÉSULTATS
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💾 PHASE 7 : SAUVEGARDE")
print("="*80)

# Sauvegarder tous les clusters
output_all = script_dir / "inventory_all_clusters.csv"
df_clusters.to_csv(output_all, index=False)
print(f"\n✅ Tous les clusters: {output_all}")

# Sauvegarder clusters testables
output_testable = script_dir / "inventory_testable_clusters.csv"
df_testable.to_csv(output_testable, index=False)
print(f"✅ Clusters testables: {output_testable}")

# Sauvegarder CPI/NFP/Retail uniquement
output_target = script_dir / "inventory_cpi_nfp_retail_clusters.csv"
df_target.to_csv(output_target, index=False)
print(f"✅ CPI/NFP/Retail: {output_target}")

# Statistiques finales
print(f"\n📊 RÉSUMÉ FINAL:")
print(f"   Événements analysés:      {len(df_events)}")
print(f"   Clusters identifiés:      {len(df_clusters)}")
print(f"   Clusters testables:       {len(df_testable)}")
print(f"   CPI/NFP/Retail testables: {len(df_target)}")

con.close()

print("\n" + "="*80)
print("✅ INVENTAIRE TERMINÉ")
print("="*80)
