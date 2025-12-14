"""
RECHERCHE CAS DOUBLE WAVE - SESSION 116
========================================

OBJECTIF:
Identifier 2-3 cas de pattern DOUBLE WAVE (comme 11 septembre) pour valider
la fonction calculate_double_wave_overlapping() sur plusieurs dates.

CRITÈRES DOUBLE WAVE:
1. 2 clusters distincts séparés de 10-25 minutes
2. Surprises significatives (>15%) dans les deux clusters
3. Events HIGH importance (importance_n = 3)
4. Pullback profond entre clusters (>50% du peak 1)
5. Données prix disponibles (vérifier après sélection)

DIFFÉRENCE vs SINGLE WAVE FORT:
- Double Wave: Pullback profond visible + 2ème impulsion distincte
- Single Wave Fort: Pas de pullback profond, momentum continu

Date: 06 novembre 2025 - Session 116
Auteur: André Valentin avec Claude
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import DB_PATH


def find_double_wave_candidates(
    start_date='2024-01-01',
    end_date='2025-11-06',
    min_surprise=15.0,
    min_importance=3,
    cluster_window_min=10,
    cluster_window_max=25
):
    """
    Recherche des dates candidates pour pattern Double Wave.
    
    ALGORITHME:
    1. Chercher dates avec 2+ événements HIGH importance
    2. Grouper événements en clusters (fenêtre 5 min)
    3. Identifier jours avec exactement 2 clusters
    4. Vérifier écart temporel entre clusters (10-25 min)
    5. Calculer surprises pour chaque cluster
    6. Filtrer clusters avec surprise >15%
    
    Args:
        start_date: Date début recherche
        end_date: Date fin recherche
        min_surprise: Surprise minimale absolue (%)
        min_importance: Importance minimale (3=HIGH)
        cluster_window_min: Écart minimum entre clusters (minutes)
        cluster_window_max: Écart maximum entre clusters (minutes)
    
    Returns:
        pd.DataFrame: Candidats avec métadonnées
    """
    print("="*70)
    print("RECHERCHE CANDIDATS DOUBLE WAVE")
    print("="*70)
    print(f"\nPériode: {start_date} → {end_date}")
    print(f"Critères:")
    print(f"  - Surprise min: {min_surprise}%")
    print(f"  - Importance min: {min_importance} (HIGH)")
    print(f"  - Écart clusters: {cluster_window_min}-{cluster_window_max} min")
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ÉTAPE 1: Sélectionner événements HIGH importance avec surprises
    query = f"""
    WITH event_surprises AS (
        SELECT 
            DATE(ts_utc) as event_date,
            ts_utc,
            event_key,
            country,
            actual,
            estimate,
            previous,
            importance_n,
            -- Calculer surprise (même logique que cluster_impact_calculator.py)
            CASE 
                WHEN actual IS NOT NULL AND estimate IS NOT NULL THEN
                    ABS(((actual - estimate) / NULLIF(estimate, 0)) * 100)
                WHEN actual IS NOT NULL AND previous IS NOT NULL THEN
                    ABS(((actual - previous) / NULLIF(previous, 0)) * 100)
                ELSE NULL
            END as surprise_pct
        FROM events
        WHERE ts_utc >= '{start_date}'
            AND ts_utc < '{end_date}'
            AND importance_n >= {min_importance}
            AND country IN ('US', 'DE', 'EU')  -- EUR/USD relevants
            AND (actual IS NOT NULL OR estimate IS NOT NULL)
    ),
    
    -- ÉTAPE 2: Identifier dates avec événements multiples
    dates_with_multiple_events AS (
        SELECT 
            event_date,
            COUNT(*) as num_events,
            COUNT(CASE WHEN surprise_pct > {min_surprise} THEN 1 END) as num_high_surprise
        FROM event_surprises
        WHERE surprise_pct IS NOT NULL
        GROUP BY event_date
        HAVING COUNT(*) >= 2  -- Au moins 2 événements
            AND COUNT(CASE WHEN surprise_pct > {min_surprise} THEN 1 END) >= 1  -- Au moins 1 surprise >15%
    )
    
    SELECT 
        es.event_date,
        es.ts_utc,
        es.event_key,
        es.country,
        es.actual,
        es.estimate,
        es.previous,
        es.surprise_pct,
        es.importance_n,
        dm.num_events as total_events_day,
        dm.num_high_surprise
    FROM event_surprises es
    INNER JOIN dates_with_multiple_events dm 
        ON es.event_date = dm.event_date
    WHERE es.surprise_pct IS NOT NULL
    ORDER BY es.event_date DESC, es.ts_utc
    """
    
    events_df = conn.execute(query).fetchdf()
    conn.close()
    
    print(f"\n✅ {len(events_df)} événements trouvés sur {events_df['event_date'].nunique()} dates")
    
    if events_df.empty:
        print("\n⚠️  Aucun événement trouvé. Élargir les critères.")
        return pd.DataFrame()
    
    # ÉTAPE 3: Analyser chaque date pour détecter pattern Double Wave
    candidates = []
    
    for date in events_df['event_date'].unique():
        date_events = events_df[events_df['event_date'] == date].copy()
        date_events['ts_utc'] = pd.to_datetime(date_events['ts_utc'])
        date_events = date_events.sort_values('ts_utc')
        
        # Grouper en clusters (fenêtre 5 min)
        clusters = []
        current_cluster = {
            'time': date_events.iloc[0]['ts_utc'],
            'events': [date_events.iloc[0]]
        }
        
        for i in range(1, len(date_events)):
            event = date_events.iloc[i]
            time_diff = (event['ts_utc'] - current_cluster['time']).total_seconds() / 60
            
            if time_diff <= 5:  # Même cluster (5 min tolérance)
                current_cluster['events'].append(event)
            else:
                clusters.append(current_cluster)
                current_cluster = {
                    'time': event['ts_utc'],
                    'events': [event]
                }
        
        clusters.append(current_cluster)
        
        # Vérifier si pattern Double Wave possible
        if len(clusters) == 2:  # Exactement 2 clusters
            cluster1 = clusters[0]
            cluster2 = clusters[1]
            
            # Écart temporel entre clusters
            time_gap = (cluster2['time'] - cluster1['time']).total_seconds() / 60
            
            if cluster_window_min <= time_gap <= cluster_window_max:
                # Calculer surprise moyenne par cluster
                surprise1 = sum(e['surprise_pct'] for e in cluster1['events']) / len(cluster1['events'])
                surprise2 = sum(e['surprise_pct'] for e in cluster2['events']) / len(cluster2['events'])
                
                # Vérifier au moins 1 cluster avec surprise significative
                if surprise1 > min_surprise or surprise2 > min_surprise:
                    candidates.append({
                        'date': date,
                        'cluster1_time': cluster1['time'],
                        'cluster1_events': len(cluster1['events']),
                        'cluster1_surprise_avg': surprise1,
                        'cluster1_keys': ', '.join([e['event_key'] for e in cluster1['events'][:3]]),
                        'cluster2_time': cluster2['time'],
                        'cluster2_events': len(cluster2['events']),
                        'cluster2_surprise_avg': surprise2,
                        'cluster2_keys': ', '.join([e['event_key'] for e in cluster2['events'][:3]]),
                        'time_gap_minutes': time_gap,
                        'total_events': len(cluster1['events']) + len(cluster2['events']),
                        'score': (surprise1 + surprise2) / 2 * (1 / (time_gap / 15))  # Score priorité
                    })
    
    if not candidates:
        print("\n⚠️  Aucun candidat Double Wave trouvé avec ces critères.")
        return pd.DataFrame()
    
    candidates_df = pd.DataFrame(candidates).sort_values('score', ascending=False)
    
    print(f"\n🎯 {len(candidates_df)} CANDIDATS DOUBLE WAVE identifiés")
    print("\nTOP 10 candidats (score décroissant):")
    print("="*70)
    
    for idx, row in candidates_df.head(10).iterrows():
        print(f"\n📅 {row['date']} (Score: {row['score']:.1f})")
        print(f"   Cluster 1: {row['cluster1_time'].strftime('%H:%M')} - "
              f"{row['cluster1_events']} events - Surprise: {row['cluster1_surprise_avg']:.1f}%")
        print(f"   → {row['cluster1_keys']}")
        print(f"   Cluster 2: {row['cluster2_time'].strftime('%H:%M')} - "
              f"{row['cluster2_events']} events - Surprise: {row['cluster2_surprise_avg']:.1f}%")
        print(f"   → {row['cluster2_keys']}")
        print(f"   Écart: {row['time_gap_minutes']:.0f} min")
    
    return candidates_df


def verify_price_data_availability(candidates_df, top_n=5):
    """
    Vérifie disponibilité des données prix pour les candidats.
    
    Args:
        candidates_df: DataFrame des candidats
        top_n: Nombre de candidats à vérifier
    
    Returns:
        List[Dict]: Candidats avec disponibilité prix
    """
    print("\n" + "="*70)
    print("VÉRIFICATION DISPONIBILITÉ DONNÉES PRIX")
    print("="*70)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    verified = []
    
    for idx, row in candidates_df.head(top_n).iterrows():
        date = row['date']
        cluster1_time = row['cluster1_time']
        cluster2_time = row['cluster2_time']
        
        # Vérifier plage de prix nécessaire (T-30 min à T+60 min autour cluster 2)
        start_time = cluster1_time - timedelta(minutes=30)
        end_time = cluster2_time + timedelta(minutes=60)
        
        query = f"""
        SELECT COUNT(*) as num_records
        FROM prices_1m
        WHERE datetime >= '{start_time}'
            AND datetime <= '{end_time}'
        """
        
        result = conn.execute(query).fetchone()
        num_records = result[0] if result else 0
        
        expected_records = int((end_time - start_time).total_seconds() / 60) + 1
        coverage = (num_records / expected_records * 100) if expected_records > 0 else 0
        
        verified.append({
            'date': date,
            'cluster1_time': cluster1_time,
            'cluster2_time': cluster2_time,
            'time_gap': row['time_gap_minutes'],
            'num_records': num_records,
            'expected_records': expected_records,
            'coverage_pct': coverage,
            'score': row['score'],
            'available': coverage > 90  # Au moins 90% de couverture
        })
        
        status = "✅" if coverage > 90 else "⚠️"
        print(f"\n{status} {date} - Couverture: {coverage:.0f}% ({num_records}/{expected_records} min)")
    
    conn.close()
    
    verified_df = pd.DataFrame(verified)
    available_count = verified_df['available'].sum()
    
    print(f"\n📊 RÉSUMÉ: {available_count}/{len(verified_df)} candidats avec données prix suffisantes")
    
    return verified_df


def main():
    """
    Point d'entrée principal.
    """
    print("\n" + "="*70)
    print("SESSION 116 - RECHERCHE CAS DOUBLE WAVE")
    print("="*70)
    
    # ÉTAPE 1: Trouver candidats
    candidates = find_double_wave_candidates(
        start_date='2024-01-01',
        end_date='2025-11-06',
        min_surprise=15.0,
        min_importance=3,
        cluster_window_min=10,
        cluster_window_max=25
    )
    
    if candidates.empty:
        print("\n❌ Aucun candidat trouvé. Session terminée.")
        return
    
    # ÉTAPE 2: Vérifier disponibilité prix
    verified = verify_price_data_availability(candidates, top_n=10)
    
    # ÉTAPE 3: Recommandations
    print("\n" + "="*70)
    print("RECOMMANDATIONS POUR TESTS")
    print("="*70)
    
    available = verified[verified['available'] == True].sort_values('score', ascending=False)
    
    if len(available) >= 2:
        print(f"\n✅ {len(available)} candidats validés avec données prix")
        print("\n🎯 TOP 3 RECOMMANDÉS pour Session 116:")
        
        for i, (idx, row) in enumerate(available.head(3).iterrows(), 1):
            print(f"\n{i}. {row['date']}")
            print(f"   Score: {row['score']:.1f}")
            print(f"   Cluster 1: {row['cluster1_time'].strftime('%H:%M')}")
            print(f"   Cluster 2: {row['cluster2_time'].strftime('%H:%M')}")
            print(f"   Écart: {row['time_gap']:.0f} min")
            print(f"   Données: {row['coverage_pct']:.0f}% disponibles")
    else:
        print("\n⚠️  Moins de 2 candidats validés.")
        print("Suggestions:")
        print("  1. Élargir période recherche")
        print("  2. Réduire min_surprise (ex: 10%)")
        print("  3. Augmenter cluster_window_max (ex: 30 min)")
    
    print("\n" + "="*70)
    print("PROCHAINE ÉTAPE:")
    print("Examiner graphiquement les candidats pour confirmer pullback profond")
    print("="*70)


if __name__ == "__main__":
    main()
