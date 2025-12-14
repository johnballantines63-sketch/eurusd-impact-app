"""
Investigation : Pourquoi les dates GENERIC n'ont pas de clusters identiques ?

Objectif :
1. Vérifier si des clusters identiques existent pour les dates GENERIC
2. Analyser pourquoi ils ne sont pas trouvés
3. Identifier les problèmes potentiels

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

def investigate_generic_date(date_str: str):
    """Investigation détaillée pour une date GENERIC"""
    
    print("="*100)
    print(f"INVESTIGATION : {date_str}")
    print("="*100)
    print()
    
    executor = PipelineExecutor(db_path=str(DB_PATH), verbose=False)
    
    result = executor.execute_complete_pipeline(
        date_str,
        window_minutes=30,
        support_threshold=0.8,
        jaccard_threshold=0.6,
        years_lookback=5
    )
    
    if not result or not result.get('success'):
        print("❌ Pipeline échoué")
        return
    
    # Extraire informations
    results_dict = result.get('results', {})
    etape3 = results_dict.get('etape3_noyau_dur', {})
    cluster_info = results_dict.get('etape3_cluster_info', {})
    identical_clusters = results_dict.get('etape4_identical_clusters', [])
    
    core_type = etape3.get('core_type', 'UNKNOWN')
    country = etape3.get('country', 'US')
    n_core_events = etape3.get('n_core_events', 0)
    n_total_events = etape3.get('n_total_events', 0)
    
    print("📊 INFORMATIONS NOYAU DUR")
    print("-"*100)
    print(f"Core Type : {core_type}")
    print(f"Country : {country}")
    print(f"Événements core : {n_core_events}/{n_total_events}")
    print()
    
    # Afficher événements core
    main_cluster = cluster_info.get('cluster', {})
    cluster_events = main_cluster.get('events', pd.DataFrame())
    core_events_list = etape3.get('core_events', [])
    
    print("📋 ÉVÉNEMENTS CORE")
    print("-"*100)
    print()
    
    if not cluster_events.empty:
        print(f"{'Heure':<8} {'Event Key':<50} {'Country':<8} {'Imp':<4} {'Score':<8}")
        print("-"*100)
        
        for _, event in cluster_events.iterrows():
            event_time = pd.to_datetime(event['ts_utc']).strftime('%H:%M')
            event_key = str(event.get('event_key', 'Unknown'))[:50]
            country_event = event.get('country', 'N/A')
            importance = event.get('importance_n', 'N/A')
            empirical_score = event.get('empirical_score', 0.0)
            
            is_core = False
            event_id = f"{event_key.lower().strip()}_{country_event}_{importance}"
            if event_id in core_events_list:
                is_core = True
            
            marker = "✅" if is_core else "  "
            score_str = f"{empirical_score:.1f}" if empirical_score > 0 else "N/A"
            
            print(f"{marker} {event_time:<8} {event_key:<50} {country_event:<8} {importance:<4} {score_str:<8}")
        
        print()
        print(f"✅ = Événement core ({len(core_events_list)} événements)")
        print()
    
    # Clusters identiques
    print("="*100)
    print("CLUSTERS IDENTIQUES")
    print("="*100)
    print()
    
    print(f"Clusters identiques trouvés : {len(identical_clusters)}")
    print()
    
    if len(identical_clusters) == 0:
        print("⚠️  Aucun cluster identique trouvé")
        print()
        print("INVESTIGATION : Pourquoi ?")
        print("-"*100)
        print()
        
        # Vérifier si des clusters similaires existent dans l'historique
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Récupérer anchor_time
        anchor_time = main_cluster.get('anchor_time')
        if anchor_time:
            if isinstance(anchor_time, str):
                anchor_time = pd.to_datetime(anchor_time)
            
            # Extraire heure
            if hasattr(anchor_time, 'hour'):
                event_hour = anchor_time.hour
                event_minute = anchor_time.minute
            else:
                event_hour = 14
                event_minute = 30
            
            print(f"Anchor time : {event_hour:02d}:{event_minute:02d}")
            print()
            
            # Rechercher événements historiques à la même heure
            date_dt = pd.to_datetime(date_str)
            years_lookback = 5
            date_start = date_dt - pd.DateOffset(years=years_lookback)
            date_end = date_dt - pd.DateOffset(days=1)
            
            query_historical = f"""
            SELECT 
                DATE(ts_utc) as date_hist,
                COUNT(*) as n_events,
                COUNT(DISTINCT event_key) as n_unique_events
            FROM events
            WHERE DATE(ts_utc) >= '{date_start.strftime('%Y-%m-%d')}'
              AND DATE(ts_utc) <= '{date_end.strftime('%Y-%m-%d')}'
              AND EXTRACT(HOUR FROM ts_utc) = {event_hour}
              AND EXTRACT(MINUTE FROM ts_utc) >= {event_minute - 10}
              AND EXTRACT(MINUTE FROM ts_utc) <= {event_minute + 10}
              AND importance_n <= 3
            GROUP BY DATE(ts_utc)
            ORDER BY date_hist DESC
            LIMIT 20
            """
            
            df_historical = conn.execute(query_historical).df()
            
            print(f"📊 Dates historiques avec événements à {event_hour:02d}:{event_minute:02d} (±10 min) :")
            print(f"   {len(df_historical)} dates trouvées")
            print()
            
            if not df_historical.empty:
                print(f"{'Date':<12} {'N Events':<10} {'N Unique':<10}")
                print("-"*35)
                for _, row in df_historical.head(10).iterrows():
                    print(f"{str(row['date_hist']):<12} {row['n_events']:<10} {row['n_unique_events']:<10}")
                print()
                
                # Vérifier similarité Jaccard pour quelques dates
                print("🔍 Vérification similarité Jaccard (top 5 dates) :")
                print("-"*100)
                print()
                
                # Créer set d'événements core pour date cible
                core_events_set = set()
                for event_id in core_events_list:
                    core_events_set.add(event_id)
                
                print(f"Événements core cible : {len(core_events_set)}")
                for event_id in list(core_events_set)[:5]:
                    print(f"  - {event_id}")
                if len(core_events_set) > 5:
                    print(f"  ... et {len(core_events_set) - 5} autres")
                print()
                
                # Pour chaque date historique, calculer Jaccard
                for idx, row in df_historical.head(5).iterrows():
                    date_hist = str(row['date_hist'])
                    
                    # Charger événements de cette date
                    query_events_hist = f"""
                    SELECT 
                        LOWER(TRIM(event_key)) || '_' || country || '_' || CAST(importance_n AS VARCHAR) as event_id
                    FROM events
                    WHERE DATE(ts_utc) = '{date_hist}'
                      AND EXTRACT(HOUR FROM ts_utc) = {event_hour}
                      AND EXTRACT(MINUTE FROM ts_utc) >= {event_minute - 10}
                      AND EXTRACT(MINUTE FROM ts_utc) <= {event_minute + 10}
                      AND importance_n <= 3
                    """
                    
                    df_events_hist = conn.execute(query_events_hist).df()
                    events_hist_set = set(df_events_hist['event_id'].tolist())
                    
                    # Calculer Jaccard
                    intersection = len(core_events_set & events_hist_set)
                    union = len(core_events_set | events_hist_set)
                    jaccard = intersection / union if union > 0 else 0.0
                    
                    print(f"{date_hist} :")
                    print(f"  Événements historiques : {len(events_hist_set)}")
                    print(f"  Intersection : {intersection}")
                    print(f"  Union : {union}")
                    print(f"  Jaccard : {jaccard:.3f}")
                    print(f"  Seuil (0.60) : {'✅ PASS' if jaccard >= 0.60 else '❌ FAIL'}")
                    print()
            else:
                print("❌ Aucune date historique trouvée à cette heure")
                print()
            
            conn.close()
        else:
            print("❌ Pas d'anchor_time disponible")
    else:
        print(f"✅ {len(identical_clusters)} clusters identiques trouvés")
        print()
        print("Détails (top 5) :")
        print("-"*100)
        for idx, cluster in enumerate(identical_clusters[:5]):
            print(f"Cluster {idx+1} :")
            print(f"  Date : {cluster.get('date')}")
            print(f"  Jaccard : {cluster.get('jaccard_score', 0.0):.3f}")
            print()
    
    print("="*100)
    print()

def test_generic_dates():
    """Tester les dates GENERIC"""
    
    GENERIC_DATES = [
        '2025-06-23',
        '2025-10-10',
    ]
    
    for date_str in GENERIC_DATES:
        investigate_generic_date(date_str)
        print()

if __name__ == '__main__':
    print("="*100)
    print("INVESTIGATION : DATES GENERIC - CLUSTERS IDENTIQUES")
    print("="*100)
    print()
    
    test_generic_dates()
    
    print("="*100)
    print("INVESTIGATION TERMINÉE")
    print("="*100)




