"""
Script - Trouver Clusters DoubleWave dans DB
============================================

Analyse la DB pour trouver les vrais clusters d'événements
correspondant aux cas Session 131.

Auteur: Session 132
Date: 13 novembre 2025
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from core.doublewave_prediction import predict_doublewave_overlap

DB_PATH = project_root / 'data' / 'warehouse.duckdb'

print("\n" + "="*70)
print(" RECHERCHE CLUSTERS DOUBLEWAVE DANS DB")
print("="*70)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Dates Session 131
dates_to_analyze = [
    "2023-02-03",  # NFP US + Inflation EU
    "2023-03-22",  # EIA Energy US
    "2025-02-03",  # ISM Manufacturing US
    "2025-09-11",  # 11 septembre ECB+US
]

def find_clusters_for_date(date_str):
    """
    Trouve tous les clusters d'événements pour une date.
    Cluster = 5+ événements dans même fenêtre de 5 minutes.
    """
    print(f"\n{'='*70}")
    print(f"DATE : {date_str}")
    print(f"{'='*70}")
    
    # Charger TOUS les événements de la journée avec scores
    query = """
    WITH event_scores AS (
        SELECT 
            event_key,
            empirical_score as score
        FROM event_families
        WHERE empirical_score > 0
    )
    SELECT 
        e.ts_utc,
        e.country,
        e.event_key,
        e.event_title,
        e.importance_n,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        COALESCE(es.score, 0) as score
    FROM events e
    LEFT JOIN event_scores es ON e.event_key = es.event_key
    WHERE DATE(e.ts_utc) = ?
      AND e.country IN ('US', 'EU', 'UK', 'CA', 'JP', 'CH', 'RS', 'MK', 'UZ', 'CO', 'GR', 'ES', 'DE', 'IT', 'RU', 'CN')
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query, [date_str]).df()
    
    if len(df) == 0:
        print("❌ Aucun événement trouvé")
        return []
    
    print(f"\n📊 {len(df)} événements totaux dans la journée")
    
    # Convertir timestamps
    df['ts_utc'] = pd.to_datetime(df['ts_utc'])
    
    # Grouper par fenêtres de 5 minutes
    df['time_window'] = df['ts_utc'].dt.floor('5min')
    
    # Trouver clusters (≥5 events dans même fenêtre)
    clusters = []
    for time_window, group in df.groupby('time_window'):
        n_events = len(group)
        n_scored = len(group[group['score'] > 0])
        total_score = group['score'].sum()
        
        if n_events >= 5 or n_scored >= 3:  # Cluster potentiel
            clusters.append({
                'timestamp': time_window,
                'n_events': n_events,
                'n_scored': n_scored,
                'total_score': total_score,
                'events': group.to_dict('records')
            })
    
    print(f"\n🔍 {len(clusters)} clusters potentiels trouvés (≥5 events ou ≥3 scorés)\n")
    
    # Analyser chaque cluster
    for i, cluster in enumerate(clusters, 1):
        ts = cluster['timestamp']
        events = cluster['events']
        
        print(f"\n{'─'*70}")
        print(f"CLUSTER #{i} : {ts.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'─'*70}")
        print(f"  Events totaux : {cluster['n_events']}")
        print(f"  Events scorés : {cluster['n_scored']}")
        print(f"  Score total   : {cluster['total_score']:.1f}")
        
        # Afficher événements scorés
        scored = [e for e in events if e['score'] > 0]
        if scored:
            print(f"\n  Événements scorés :")
            for e in scored[:10]:
                print(f"    {e['country']:3s} {e['event_key']:30s} (score: {e['score']:.1f})")
            if len(scored) > 10:
                print(f"    ... +{len(scored)-10} autres")
        
        # Tester avec module prédiction
        print(f"\n  Test module predict_doublewave_overlap :")
        result = predict_doublewave_overlap(events, debug=False)
        
        print(f"    Status        : {result['status']}")
        print(f"    Pattern       : {result['pattern_type']}")
        print(f"    Amplification : {result['amplification']}")
        print(f"    Prediction    : {result['prediction']} pips" if result['prediction'] else f"    Prediction    : None (exclu)")
        print(f"    Raison        : {result['reason']}")
        
        # Marquer si potentiellement intéressant
        if result['status'] == 'predicted':
            print(f"\n  ✅ CLUSTER PRÉDICTIBLE !")
        elif result['status'] == 'special_case':
            print(f"\n  ⚠️ CAS SPÉCIAL DÉTECTÉ !")
    
    return clusters


# Analyser chaque date
for date_str in dates_to_analyze:
    clusters = find_clusters_for_date(date_str)

conn.close()

print("\n" + "="*70)
print(" ANALYSE TERMINÉE")
print("="*70)
print("\n💡 Utilise les timestamps des clusters trouvés pour ajuster les tests")
print()
