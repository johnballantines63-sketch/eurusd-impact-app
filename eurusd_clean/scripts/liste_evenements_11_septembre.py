#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liste Événements 11 Septembre 2025

Affiche tous les événements du cluster et identifie ceux du noyau dur.
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter chemins
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from run_pipeline_complete import PipelineExecutor
from config import get_db_path

print("=" * 80)
print("📋 LISTE ÉVÉNEMENTS - 11 SEPTEMBRE 2025")
print("=" * 80)
print()

# Initialiser pipeline
db_path = Path(get_db_path())
executor = PipelineExecutor(db_path=db_path, verbose=False)

date_str = '2025-09-11'

# Charger événements
events = executor.etape1_charger_evenements(date_str)
print(f"📊 Total événements chargés : {len(events)}")
print()

# Détecter clusters
clusters = executor.etape2_detecter_clusters(events, window_minutes=30)
print(f"📊 Clusters détectés : {len(clusters)}")
print()

if not clusters:
    print("❌ Aucun cluster trouvé")
    sys.exit(1)

# Trouver le cluster principal (CPI)
main_cluster = None
for cluster in clusters:
    cluster_events = cluster['events']
    for _, event in cluster_events.iterrows():
        event_key = str(event.get('event_key', '')).lower()
        if 'cpi' in event_key or 'consumer price' in event_key:
            main_cluster = cluster
            break
    if main_cluster:
        break

if main_cluster is None:
    main_cluster = clusters[0]

cluster_events = main_cluster['events']
anchor_time = main_cluster['anchor_time']

print(f"⏰ Cluster principal détecté à : {anchor_time.strftime('%Y-%m-%d %H:%M')}")
print(f"📊 Nombre d'événements dans le cluster : {len(cluster_events)}")
print()

# Définir noyau dur
cluster_info = executor.etape3_definir_noyau_dur(main_cluster, support_threshold=0.60, years_lookback=5)

core_events = cluster_info.get('core_events', [])
support_scores = cluster_info.get('support_scores', {})
core_type = cluster_info.get('core_type', 'N/A')

print("=" * 80)
print(f"📋 TOUS LES ÉVÉNEMENTS DU CLUSTER ({len(cluster_events)} événements)")
print("=" * 80)
print()

# Créer identifiants canoniques pour chaque événement
event_details = []
for idx, (_, event) in enumerate(cluster_events.iterrows(), 1):
    event_key = str(event.get('event_key', '')).lower().strip()
    country = event.get('country', '')
    importance = event.get('importance_n', 3)
    event_id = f"{event_key}_{country}_{importance}"
    
    # Vérifier si dans noyau dur
    is_core = event_id in core_events
    support = support_scores.get(event_id, 0.0)
    
    event_title = event.get('event_title') or event.get('label', 'N/A')
    empirical_score = event.get('empirical_score', 'N/A')
    ts_utc = event.get('ts_utc', 'N/A')
    
    event_details.append({
        'index': idx,
        'event_id': event_id,
        'event_key': event_key,
        'event_title': event_title,
        'country': country,
        'importance': importance,
        'empirical_score': empirical_score,
        'ts_utc': ts_utc,
        'is_core': is_core,
        'support': support
    })

# Trier par core d'abord, puis par index
event_details.sort(key=lambda x: (not x['is_core'], x['index']))

print(f"{'#':<4} {'Core':<6} {'Événement':<50} {'Pays':<6} {'Imp':<4} {'Score':<8} {'Support':<10} {'Heure':<12}")
print("-" * 100)

for detail in event_details:
    core_marker = "✅ CORE" if detail['is_core'] else "❌"
    event_display = detail['event_key'][:48]
    country_display = detail['country']
    importance_display = detail['importance']
    score_display = f"{detail['empirical_score']:.1f}" if isinstance(detail['empirical_score'], (int, float)) else str(detail['empirical_score'])
    support_display = f"{detail['support']*100:.1f}%" if detail['support'] > 0 else "N/A"
    
    # Formater heure
    if isinstance(detail['ts_utc'], datetime):
        time_display = detail['ts_utc'].strftime('%H:%M')
    else:
        time_display = str(detail['ts_utc'])[:12]
    
    print(f"{detail['index']:<4} {core_marker:<6} {event_display:<50} {country_display:<6} {importance_display:<4} {score_display:<8} {support_display:<10} {time_display:<12}")

print()
print("=" * 80)
print(f"📊 RÉSUMÉ NOYAU DUR")
print("=" * 80)
print()

n_core = len(core_events)
n_total = len(cluster_events)

print(f"Type détecté : {core_type}")
print(f"Événements core : {n_core}/{n_total}")
print()

print("Événements CORE (dans le noyau dur) :")
print("-" * 80)

for detail in event_details:
    if detail['is_core']:
        support_display = f"{detail['support']*100:.1f}%" if detail['support'] > 0 else "N/A"
        reason = ""
        if detail['support'] >= 0.60:
            reason = "support >= 60%"
        elif detail['support'] >= 0.40 and detail['importance'] <= 2:
            reason = f"support {detail['support']*100:.1f}% + importance {detail['importance']} (seuil adaptatif)"
        
        print(f"  ✅ {detail['event_key']:<50} | Support: {support_display:<8} | Raison: {reason}")

print()
print("Événements NON-CORE (exclus du noyau dur) :")
print("-" * 80)

for detail in event_details:
    if not detail['is_core']:
        support_display = f"{detail['support']*100:.1f}%" if detail['support'] > 0 else "N/A"
        print(f"  ❌ {detail['event_key']:<50} | Support: {support_display:<8} | Importance: {detail['importance']}")

print()
print("=" * 80)
print("✅ Analyse terminée")
print("=" * 80)




