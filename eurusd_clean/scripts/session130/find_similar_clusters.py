#!/usr/bin/env python3
"""
TROUVER CLUSTERS SIMILAIRES - SESSION 130 ÉTAPE 6
==================================================

Pour chaque cas référence, chercher clusters avec composition similaire.

CRITÈRES SIMILARITÉ :
- Même composition événements (Jaccard > 0.8)
- Fenêtre ±5 min autour cluster_time
- Période 2023-2025

Input : reference_cases_with_amplifications.json
Output : reference_cases_with_similar_clusters.json

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
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
INPUT_FILE = Path(__file__).parent / "reference_cases_with_amplifications.json"
OUTPUT_FILE = Path(__file__).parent / "reference_cases_with_similar_clusters.json"

# Période recherche
START_DATE = "2023-01-01"
END_DATE = "2025-11-07"

# Seuil similarité Jaccard
SIMILARITY_THRESHOLD = 0.8


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


def normalize_event_key(event_key: str) -> str:
    """Normalise event_key pour comparaison"""
    return event_key.lower().strip()


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
        importance_n
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
    
    for i, (ts_utc, event_key, country, importance) in enumerate(results):
        if i in used_indices:
            continue
        
        # Créer cluster autour cet événement
        cluster_time = ts_utc
        cluster_start = cluster_time - timedelta(minutes=5)
        cluster_end = cluster_time + timedelta(minutes=5)
        
        cluster_events = []
        
        for j, (ts2, key2, country2, imp2) in enumerate(results):
            if cluster_start <= ts2 <= cluster_end:
                cluster_events.append({
                    'event_key': key2,
                    'ts_utc': ts2.isoformat() if ts2 else None,
                    'country': country2,
                    'importance': 'HIGH' if imp2 == 3 else 'MEDIUM'
                })
                used_indices.add(j)
        
        if len(cluster_events) > 0:
            clusters.append({
                'cluster_time': cluster_time.isoformat() if cluster_time else None,
                'n_events': len(cluster_events),
                'events': cluster_events
            })
    
    return clusters


def find_similar_clusters_for_reference(ref_case: Dict, conn) -> List[Dict]:
    """
    Trouve clusters similaires à un cas référence.
    
    Returns:
        Liste clusters similaires avec date, similarity, events
    """
    # Composition référence
    ref_events = ref_case['events']
    ref_composition = set(normalize_event_key(e['event_key']) for e in ref_events)
    
    print(f"\n   Composition référence : {len(ref_composition)} événements uniques")
    print(f"   Événements : {sorted(list(ref_composition))[:5]}...")
    
    # Scanner période complète
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d").replace(tzinfo=TZ_BERN)
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d").replace(tzinfo=TZ_BERN)
    
    similar_clusters = []
    current_date = start_dt
    total_days = (end_dt - start_dt).days
    
    print(f"\n   Recherche sur {total_days} jours...")
    
    while current_date <= end_dt:
        # Trouver clusters ce jour
        clusters = find_event_clusters_on_date(conn, current_date)
        
        for cluster in clusters:
            # Composition cluster
            cluster_composition = set(
                normalize_event_key(e['event_key']) 
                for e in cluster['events']
            )
            
            # Calculer similarité
            similarity = jaccard_similarity(ref_composition, cluster_composition)
            
            if similarity >= SIMILARITY_THRESHOLD:
                similar_clusters.append({
                    'date': current_date.strftime("%Y-%m-%d"),
                    'cluster_time': cluster['cluster_time'],
                    'similarity': similarity,
                    'n_events': cluster['n_events'],
                    'events': cluster['events'],
                    'composition': sorted(list(cluster_composition))
                })
        
        current_date += timedelta(days=1)
    
    print(f"   ✅ {len(similar_clusters)} clusters similaires trouvés")
    
    return similar_clusters


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("TROUVER CLUSTERS SIMILAIRES - ÉTAPE 6")
    print("=" * 80)
    
    # Charger cas référence
    print(f"\n📂 Chargement : {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        print(f"❌ Fichier introuvable : {INPUT_FILE}")
        return 1
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    reference_cases = data['reference_cases']
    print(f"✅ {len(reference_cases)} cas référence chargés")
    
    # Connexion DB
    print(f"\n🔗 Connexion DB...")
    conn = duckdb.connect(DB_PATH, read_only=True)
    print(f"✅ Connecté")
    
    # Traiter chaque cas référence
    enriched_cases = {}
    
    for pattern, ref_case in reference_cases.items():
        print(f"\n{'='*80}")
        print(f"Pattern : {pattern}")
        print(f"{'='*80}")
        print(f"Date référence : {ref_case['date']}")
        print(f"Impact : {ref_case.get('impact_real', 0):.2f} pips")
        print(f"Events : {ref_case.get('n_events', 0)}")
        
        try:
            # Chercher clusters similaires
            similar_clusters = find_similar_clusters_for_reference(ref_case, conn)
            
            # Enrichir cas référence
            enriched_cases[pattern] = {
                **ref_case,
                'similar_clusters': similar_clusters,
                'n_similar_clusters': len(similar_clusters)
            }
            
            # Stats
            if similar_clusters:
                similarities = [c['similarity'] for c in similar_clusters]
                avg_sim = sum(similarities) / len(similarities)
                print(f"\n   📊 Statistiques similarité :")
                print(f"      Moyenne : {avg_sim:.3f}")
                print(f"      Min : {min(similarities):.3f}")
                print(f"      Max : {max(similarities):.3f}")
                
                # Top 3
                top3 = sorted(similar_clusters, key=lambda x: -x['similarity'])[:3]
                print(f"\n   Top 3 clusters :")
                for i, cluster in enumerate(top3, 1):
                    print(f"      {i}. {cluster['date']} - Sim: {cluster['similarity']:.3f} ({cluster['n_events']} events)")
            
        except Exception as e:
            print(f"\n❌ ERREUR traitement {pattern} : {e}")
            import traceback
            traceback.print_exc()
            enriched_cases[pattern] = {
                **ref_case,
                'error': str(e),
                'similar_clusters': [],
                'n_similar_clusters': 0
            }
    
    conn.close()
    
    # Résumé
    print(f"\n{'='*80}")
    print("RÉSUMÉ CLUSTERS SIMILAIRES")
    print("=" * 80)
    
    print(f"\n| {'Pattern':<30s} | {'Date Réf':<12s} | {'Similaires':<11s} |")
    print(f"|{'-'*32}|{'-'*14}|{'-'*13}|")
    
    for pattern, case in enriched_cases.items():
        n_similar = case.get('n_similar_clusters', 0)
        date = case.get('date', 'N/A')
        print(f"| {pattern:<30s} | {date:<12s} | {n_similar:>11d} |")
    
    # Sauvegarde
    print(f"\n{'='*80}")
    print("SAUVEGARDE RÉSULTATS")
    print("=" * 80)
    
    output = {
        'metadata': {
            **data['metadata'],
            'similar_clusters_found': datetime.now().isoformat(),
            'search_period': f"{START_DATE} to {END_DATE}",
            'similarity_threshold': SIMILARITY_THRESHOLD
        },
        'reference_cases': enriched_cases,
        'validated_cases': data.get('validated_cases', {})
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Clusters similaires sauvegardés : {OUTPUT_FILE}")
    print(f"   Taille : {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    
    # Validation
    total_similar = sum(case.get('n_similar_clusters', 0) for case in enriched_cases.values())
    print(f"\n📊 TOTAL : {total_similar} clusters similaires trouvés")
    
    print(f"\n{'='*80}")
    print("✅ ÉTAPE 6 TERMINÉE")
    print("=" * 80)
    
    print(f"\n🎯 PROCHAINE ÉTAPE : Calculer R² pour clusters (Étape 7)")
    
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
