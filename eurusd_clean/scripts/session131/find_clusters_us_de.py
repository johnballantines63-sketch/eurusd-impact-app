#!/usr/bin/env python3
"""
CHERCHER CLUSTERS US + CURRENT ACCOUNT DE - SESSION 131
========================================================

Cherche clusters similaires composition 11 septembre SANS événements BCE.

COMPOSITION CIBLE (11 événements) :
- US CPI (6 events) : cpi s.a, cpi, inflation rates mom/yoy, core inflation mom/yoy
- US Jobless Claims (4 events) : initial, continuing, 4-week avg, real earnings
- DE Current Account (1 event)

CRITÈRES :
- Jaccard >= 0.8 (9/11 events en commun)
- Période 2023-2025
- Fenêtre ±5 min autour cluster

Auteur : André Valentin avec Claude
Date : 13 novembre 2025 - Session 131
"""

import json
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set
import sys

# Import utils timezone
sys.path.insert(0, str(Path(__file__).parent / '../session129'))
from utils_timezone import ensure_bern_time, TZ_BERN

# Chemins
DB_PATH = "data/warehouse.duckdb"
OUTPUT_FILE = Path(__file__).parent / "clusters_us_de.json"

# Période recherche
START_DATE = "2023-01-01"
END_DATE = "2025-11-07"

# Seuil similarité Jaccard
SIMILARITY_THRESHOLD = 0.8

# COMPOSITION CIBLE (11 événements US + DE, SANS BCE)
TARGET_COMPOSITION = {
    # US CPI (6 events)
    'cpi s.a',
    'cpi',
    'inflation rate_yoy',
    'inflation rate_mom',
    'core inflation rate_yoy',
    'core inflation rate_mom',
    # US Jobless Claims (4 events)
    'initial jobless claims',
    'continuing jobless claims',
    'jobless claims 4 week average',
    'real earnings_mom',
    # DE (1 event)
    'current account'
}


def normalize_event_key(event_key: str) -> str:
    """Normalise event_key pour comparaison"""
    return event_key.lower().strip()


def jaccard_similarity(set1: Set, set2: Set) -> float:
    """
    Calcule similarité Jaccard entre 2 ensembles.
    
    Jaccard = |intersection| / |union|
    """
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def find_event_clusters_on_date(conn, date: datetime) -> List[Dict]:
    """
    Trouve tous clusters événements sur une date donnée.
    
    Cluster = groupe événements dans fenêtre ±5 min
    
    Returns:
        Liste de dicts avec cluster_time, events
    """
    # Fenêtre complète journée
    start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)
    
    # Charger events MEDIUM+HIGH
    query = """
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        forecast,
        previous
    FROM events
    WHERE ts_utc BETWEEN ? AND ?
      AND importance_n >= 2
    ORDER BY ts_utc
    """
    
    results = conn.execute(query, [start_time, end_time]).fetchall()
    
    if not results:
        return []
    
    # Grouper par fenêtres ±5 min
    clusters = []
    used_indices = set()
    
    for i, row in enumerate(results):
        if i in used_indices:
            continue
        
        ts_utc, event_key, country, importance, actual, forecast, previous = row
        
        # Créer cluster autour cet événement
        cluster_time = ts_utc
        cluster_start = cluster_time - timedelta(minutes=5)
        cluster_end = cluster_time + timedelta(minutes=5)
        
        cluster_events = []
        
        for j, row2 in enumerate(results):
            ts2, key2, country2, imp2, act2, fcst2, prev2 = row2
            
            if cluster_start <= ts2 <= cluster_end:
                cluster_events.append({
                    'event_key': key2,
                    'ts_utc': ts2.isoformat() if ts2 else None,
                    'country': country2,
                    'importance': 'HIGH' if imp2 == 3 else 'MEDIUM',
                    'actual': act2,
                    'forecast': fcst2,
                    'previous': prev2
                })
                used_indices.add(j)
        
        if len(cluster_events) > 0:
            clusters.append({
                'cluster_time': cluster_time.isoformat() if cluster_time else None,
                'n_events': len(cluster_events),
                'events': cluster_events
            })
    
    return clusters


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("CHERCHER CLUSTERS US + CURRENT ACCOUNT DE (SANS BCE)")
    print("=" * 80)
    
    print(f"\n🎯 COMPOSITION CIBLE ({len(TARGET_COMPOSITION)} événements) :")
    for i, event in enumerate(sorted(TARGET_COMPOSITION), 1):
        print(f"   {i:2d}. {event}")
    
    print(f"\n📊 CRITÈRES RECHERCHE :")
    print(f"   Période : {START_DATE} → {END_DATE}")
    print(f"   Jaccard : >= {SIMILARITY_THRESHOLD}")
    print(f"   Fenêtre : ±5 min")
    
    # Connexion DB
    print(f"\n🔗 Connexion DB...")
    conn = duckdb.connect(DB_PATH, read_only=True)
    print(f"✅ Connecté")
    
    # Scanner période complète
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d").replace(tzinfo=TZ_BERN)
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d").replace(tzinfo=TZ_BERN)
    
    similar_clusters = []
    current_date = start_dt
    total_days = (end_dt - start_dt).days
    
    print(f"\n🔍 Scan de {total_days} jours...")
    print(f"   Progression : ", end='', flush=True)
    
    days_processed = 0
    
    while current_date <= end_dt:
        # Progress indicator
        if days_processed % 100 == 0:
            print(f"{days_processed}/{total_days}", end='...', flush=True)
        
        # Trouver clusters ce jour
        clusters = find_event_clusters_on_date(conn, current_date)
        
        for cluster in clusters:
            # Composition cluster (normalisée)
            cluster_composition = set(
                normalize_event_key(e['event_key']) 
                for e in cluster['events']
            )
            
            # Calculer similarité avec composition cible
            similarity = jaccard_similarity(TARGET_COMPOSITION, cluster_composition)
            
            if similarity >= SIMILARITY_THRESHOLD:
                # Calculer détails
                intersection = TARGET_COMPOSITION & cluster_composition
                only_in_target = TARGET_COMPOSITION - cluster_composition
                only_in_cluster = cluster_composition - TARGET_COMPOSITION
                
                similar_clusters.append({
                    'date': current_date.strftime("%Y-%m-%d"),
                    'cluster_time': cluster['cluster_time'],
                    'similarity': similarity,
                    'n_events': cluster['n_events'],
                    'events': cluster['events'],
                    'composition': sorted(list(cluster_composition)),
                    'intersection': sorted(list(intersection)),
                    'missing_from_target': sorted(list(only_in_target)),
                    'extra_in_cluster': sorted(list(only_in_cluster))
                })
        
        current_date += timedelta(days=1)
        days_processed += 1
    
    print(f"{total_days}/{total_days} ✅")
    
    conn.close()
    
    # Résultats
    print(f"\n{'='*80}")
    print("RÉSULTATS")
    print("=" * 80)
    
    print(f"\n✅ {len(similar_clusters)} clusters similaires trouvés")
    
    if similar_clusters:
        # Statistiques similarité
        similarities = [c['similarity'] for c in similar_clusters]
        print(f"\n📊 Statistiques similarité :")
        print(f"   Moyenne : {sum(similarities)/len(similarities):.3f}")
        print(f"   Min : {min(similarities):.3f}")
        print(f"   Max : {max(similarities):.3f}")
        
        # Distribution par année
        years = {}
        for cluster in similar_clusters:
            year = cluster['date'][:4]
            years[year] = years.get(year, 0) + 1
        
        print(f"\n📅 Distribution par année :")
        for year in sorted(years.keys()):
            print(f"   {year} : {years[year]:2d} clusters")
        
        # Top 10
        print(f"\n🏆 Top 10 clusters (par similarité) :")
        print(f"\n| {'#':<3s} | {'Date':<12s} | {'Heure':<8s} | {'Sim':<6s} | {'N':<3s} |")
        print(f"|{'-'*5}|{'-'*14}|{'-'*10}|{'-'*8}|{'-'*5}|")
        
        top10 = sorted(similar_clusters, key=lambda x: -x['similarity'])[:10]
        for i, cluster in enumerate(top10, 1):
            time_str = cluster['cluster_time'][11:16] if cluster['cluster_time'] else 'N/A'
            print(f"| {i:<3d} | {cluster['date']:<12s} | {time_str:<8s} | {cluster['similarity']:.3f} | {cluster['n_events']:<3d} |")
        
        # Détails premier cluster (exemple)
        if len(similar_clusters) > 0:
            first = similar_clusters[0]
            print(f"\n📋 EXEMPLE CLUSTER #{1} ({first['date']}) :")
            print(f"   Similarité : {first['similarity']:.3f}")
            print(f"   Composition ({len(first['composition'])} events) :")
            for event in first['composition'][:5]:
                print(f"      • {event}")
            if len(first['composition']) > 5:
                print(f"      ... et {len(first['composition'])-5} autres")
            
            if first['missing_from_target']:
                print(f"\n   ⚠️  Manquants dans cluster (vs cible) :")
                for event in first['missing_from_target']:
                    print(f"      • {event}")
            
            if first['extra_in_cluster']:
                print(f"\n   ➕ Événements supplémentaires dans cluster :")
                for event in first['extra_in_cluster']:
                    print(f"      • {event}")
    
    # Sauvegarde
    print(f"\n{'='*80}")
    print("SAUVEGARDE")
    print("=" * 80)
    
    output = {
        'metadata': {
            'created': datetime.now().isoformat(),
            'target_composition': sorted(list(TARGET_COMPOSITION)),
            'n_target_events': len(TARGET_COMPOSITION),
            'search_period': f"{START_DATE} to {END_DATE}",
            'similarity_threshold': SIMILARITY_THRESHOLD,
            'total_days_scanned': total_days
        },
        'clusters': similar_clusters,
        'n_clusters': len(similar_clusters),
        'statistics': {
            'mean_similarity': sum(similarities)/len(similarities) if similarities else 0,
            'min_similarity': min(similarities) if similarities else 0,
            'max_similarity': max(similarities) if similarities else 0
        }
    }
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Résultats sauvegardés : {OUTPUT_FILE}")
    print(f"   Taille : {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    
    print(f"\n{'='*80}")
    print("✅ RECHERCHE TERMINÉE")
    print("=" * 80)
    
    if len(similar_clusters) == 0:
        print(f"\n⚠️  AUCUN cluster trouvé avec Jaccard >= {SIMILARITY_THRESHOLD}")
        print(f"\n💡 Suggestions :")
        print(f"   • Abaisser seuil à 0.7 (permettrait 3-4 events différents)")
        print(f"   • Abaisser seuil à 0.6 (permettrait 4-5 events différents)")
        print(f"   • Analyser composition US seule (10 events) sans Current Account")
    else:
        print(f"\n🎯 PROCHAINE ÉTAPE : Calculer R² tendance pour ces {len(similar_clusters)} clusters")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
