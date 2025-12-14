#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Investigation Jobless Claims - Pourquoi exclus du noyau dur ?

Analyse pourquoi les Jobless Claims ont un support faible dans les clusters CPI
et vérifie s'ils apparaissent dans d'autres types de clusters.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import re
from collections import Counter
import duckdb

# Ajouter chemins
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import get_db_path
from core.event_loader import load_high_impact_events

print("=" * 80)
print("🔍 INVESTIGATION JOBLESS CLAIMS - DÉTECTION NOYAU DUR")
print("=" * 80)
print()

db_path = Path(get_db_path())
years_lookback = 5
window_minutes = 30

# Date cible
target_date = datetime(2025, 9, 11)
date_start = target_date - timedelta(days=years_lookback * 365)
date_end = target_date - timedelta(days=1)

print(f"📅 Date cible : {target_date.strftime('%Y-%m-%d')}")
print(f"📊 Période analyse : {date_start.strftime('%Y-%m-%d')} à {date_end.strftime('%Y-%m-%d')}")
print()

# Patterns
CPI_PATTERN = r'(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)'
JOBLESS_PATTERN = r'(?i)(jobless claims|continuing jobless|initial jobless)'

# Connexion DB
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("📊 ANALYSE 1 : Jobless Claims dans clusters CPI historiques")
print("=" * 80)
print()

# Compter occurrences de Jobless Claims dans clusters CPI
jobless_in_cpi_clusters = Counter()
n_cpi_clusters = 0
n_clusters_with_jobless = 0

current_date = date_start
while current_date <= date_end:
    date_str = current_date.strftime('%Y-%m-%d')
    
    try:
        events = load_high_impact_events(
            db_path,
            current_date,
            country='US',
            min_empirical_score=29.0,
            verbose=False
        )
        
        if not events.empty:
            events['ts_utc'] = pd.to_datetime(events['ts_utc'])
            processed_indices = set()
            
            for idx, row in events.iterrows():
                if idx in processed_indices:
                    continue
                
                window_start = row['ts_utc']
                window_end = window_start + timedelta(minutes=window_minutes)
                
                mask = (
                    (events['ts_utc'] >= window_start) &
                    (events['ts_utc'] < window_end)
                )
                cluster_events = events[mask].copy()
                
                # Vérifier si cluster contient CPI
                has_cpi = False
                for _, event in cluster_events.iterrows():
                    event_key = str(event.get('event_key', '')).lower()
                    if re.search(CPI_PATTERN, event_key):
                        has_cpi = True
                        break
                
                if has_cpi and len(cluster_events) > 0:
                    n_cpi_clusters += 1
                    
                    # Vérifier si cluster contient aussi Jobless Claims
                    has_jobless = False
                    jobless_types = []
                    for _, event in cluster_events.iterrows():
                        event_key = str(event.get('event_key', '')).lower()
                        if re.search(JOBLESS_PATTERN, event_key):
                            has_jobless = True
                            jobless_types.append(event_key)
                            jobless_in_cpi_clusters[event_key] += 1
                    
                    if has_jobless:
                        n_clusters_with_jobless += 1
                    
                    processed_indices.update(cluster_events.index.tolist())
    
    except Exception:
        pass
    
    current_date += timedelta(days=1)

print(f"Clusters CPI historiques trouvés : {n_cpi_clusters}")
print(f"Clusters CPI avec Jobless Claims : {n_clusters_with_jobless}")
print(f"Pourcentage : {n_clusters_with_jobless/n_cpi_clusters*100:.1f}%" if n_cpi_clusters > 0 else "N/A")
print()

if jobless_in_cpi_clusters:
    print("Occurrences de Jobless Claims dans clusters CPI :")
    for event_key, count in jobless_in_cpi_clusters.most_common():
        support = count / n_cpi_clusters if n_cpi_clusters > 0 else 0.0
        print(f"  - {event_key:<50} : {count}/{n_cpi_clusters} ({support*100:.1f}%)")
else:
    print("Aucune occurrence de Jobless Claims dans clusters CPI historiques")

print()
print("=" * 80)
print("📊 ANALYSE 2 : Jobless Claims dans TOUS les clusters historiques")
print("=" * 80)
print()

# Compter occurrences de Jobless Claims dans TOUS les clusters (pas seulement CPI)
jobless_in_all_clusters = Counter()
n_all_clusters = 0
n_clusters_with_jobless_all = 0

current_date = date_start
while current_date <= date_end:
    date_str = current_date.strftime('%Y-%m-%d')
    
    try:
        events = load_high_impact_events(
            db_path,
            current_date,
            country='US',
            min_empirical_score=29.0,
            verbose=False
        )
        
        if not events.empty:
            events['ts_utc'] = pd.to_datetime(events['ts_utc'])
            processed_indices = set()
            
            for idx, row in events.iterrows():
                if idx in processed_indices:
                    continue
                
                window_start = row['ts_utc']
                window_end = window_start + timedelta(minutes=window_minutes)
                
                mask = (
                    (events['ts_utc'] >= window_start) &
                    (events['ts_utc'] < window_end)
                )
                cluster_events = events[mask].copy()
                
                if len(cluster_events) > 0:
                    n_all_clusters += 1
                    
                    # Vérifier si cluster contient Jobless Claims
                    has_jobless = False
                    for _, event in cluster_events.iterrows():
                        event_key = str(event.get('event_key', '')).lower()
                        if re.search(JOBLESS_PATTERN, event_key):
                            has_jobless = True
                            jobless_in_all_clusters[event_key] += 1
                    
                    if has_jobless:
                        n_clusters_with_jobless_all += 1
                    
                    processed_indices.update(cluster_events.index.tolist())
    
    except Exception:
        pass
    
    current_date += timedelta(days=1)

print(f"Tous clusters historiques trouvés : {n_all_clusters}")
print(f"Clusters avec Jobless Claims : {n_clusters_with_jobless_all}")
print(f"Pourcentage : {n_clusters_with_jobless_all/n_all_clusters*100:.1f}%" if n_all_clusters > 0 else "N/A")
print()

if jobless_in_all_clusters:
    print("Occurrences de Jobless Claims dans tous clusters :")
    for event_key, count in jobless_in_all_clusters.most_common():
        support = count / n_all_clusters if n_all_clusters > 0 else 0.0
        print(f"  - {event_key:<50} : {count}/{n_all_clusters} ({support*100:.1f}%)")

print()
print("=" * 80)
print("📊 ANALYSE 3 : Jobless Claims avec NFP")
print("=" * 80)
print()

# Compter occurrences de Jobless Claims dans clusters NFP
NFP_PATTERN = r'(?i)(non farm payrolls|nonfarm)'
jobless_in_nfp_clusters = Counter()
n_nfp_clusters = 0
n_clusters_with_jobless_nfp = 0

current_date = date_start
while current_date <= date_end:
    date_str = current_date.strftime('%Y-%m-%d')
    
    try:
        events = load_high_impact_events(
            db_path,
            current_date,
            country='US',
            min_empirical_score=29.0,
            verbose=False
        )
        
        if not events.empty:
            events['ts_utc'] = pd.to_datetime(events['ts_utc'])
            processed_indices = set()
            
            for idx, row in events.iterrows():
                if idx in processed_indices:
                    continue
                
                window_start = row['ts_utc']
                window_end = window_start + timedelta(minutes=window_minutes)
                
                mask = (
                    (events['ts_utc'] >= window_start) &
                    (events['ts_utc'] < window_end)
                )
                cluster_events = events[mask].copy()
                
                # Vérifier si cluster contient NFP
                has_nfp = False
                for _, event in cluster_events.iterrows():
                    event_key = str(event.get('event_key', '')).lower()
                    if re.search(NFP_PATTERN, event_key):
                        has_nfp = True
                        break
                
                if has_nfp and len(cluster_events) > 0:
                    n_nfp_clusters += 1
                    
                    # Vérifier si cluster contient aussi Jobless Claims
                    has_jobless = False
                    for _, event in cluster_events.iterrows():
                        event_key = str(event.get('event_key', '')).lower()
                        if re.search(JOBLESS_PATTERN, event_key):
                            has_jobless = True
                            jobless_in_nfp_clusters[event_key] += 1
                    
                    if has_jobless:
                        n_clusters_with_jobless_nfp += 1
                    
                    processed_indices.update(cluster_events.index.tolist())
    
    except Exception:
        pass
    
    current_date += timedelta(days=1)

print(f"Clusters NFP historiques trouvés : {n_nfp_clusters}")
print(f"Clusters NFP avec Jobless Claims : {n_clusters_with_jobless_nfp}")
print(f"Pourcentage : {n_clusters_with_jobless_nfp/n_nfp_clusters*100:.1f}%" if n_nfp_clusters > 0 else "N/A")
print()

if jobless_in_nfp_clusters:
    print("Occurrences de Jobless Claims dans clusters NFP :")
    for event_key, count in jobless_in_nfp_clusters.most_common():
        support = count / n_nfp_clusters if n_nfp_clusters > 0 else 0.0
        print(f"  - {event_key:<50} : {count}/{n_nfp_clusters} ({support*100:.1f}%)")

print()
print("=" * 80)
print("💡 CONCLUSION")
print("=" * 80)
print()

print("Le problème identifié :")
print("  - Les Jobless Claims apparaissent rarement dans les clusters CPI historiques")
print("  - Mais ils apparaissent probablement souvent dans les clusters NFP ou autres")
print("  - Le système actuel cherche uniquement dans les clusters CPI pour calculer le support")
print()
print("Solution proposée :")
print("  - Inclure les événements importants (importance <= 2) même s'ils ne sont pas")
print("    dans le même type de cluster historique")
print("  - OU : Calculer le support sur TOUS les clusters, pas seulement ceux du même type")
print()

conn.close()

print("=" * 80)
print("✅ Investigation terminée")
print("=" * 80)




