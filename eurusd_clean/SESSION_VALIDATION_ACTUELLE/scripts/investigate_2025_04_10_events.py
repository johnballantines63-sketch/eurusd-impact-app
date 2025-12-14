#!/usr/bin/env python3
"""
Investigation : 2025-04-10 - Pourquoi les événements 13:30 ne sont pas détectés ?

Objectif :
1. Vérifier les événements à 13:30 (US, impact HAUT)
2. Vérifier pourquoi ils ne sont pas dans le cluster sélectionné
3. Vérifier le mouvement à 14:00

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import pytz
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

def investigate_2025_04_10():
    """Investigation complète pour 2025-04-10"""
    
    date_str = '2025-04-10'
    
    print("="*100)
    print(f"INVESTIGATION : {date_str}")
    print("="*100)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Vérifier tous les événements de la journée
    print("="*100)
    print("1. TOUS LES ÉVÉNEMENTS DE LA JOURNÉE")
    print("="*100)
    print()
    
    query_all_events = f"""
    SELECT 
        e.ts_utc,
        e.event_key,
        e.event_title,
        e.country,
        e.importance_n,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{date_str}'
      AND e.importance_n <= 3
    ORDER BY e.ts_utc
    """
    
    df_all_events = conn.execute(query_all_events).df()
    
    if not df_all_events.empty:
        df_all_events['ts_utc'] = pd.to_datetime(df_all_events['ts_utc'])
        
        print(f"📊 {len(df_all_events)} événements trouvés")
        print()
        print(f"{'Heure':<8} {'Event Key':<60} {'Country':<8} {'Imp':<4} {'Score':<8} {'Actual':<12} {'Estimate':<12}")
        print("-"*120)
        
        for _, event in df_all_events.iterrows():
            event_time = event['ts_utc'].strftime('%H:%M')
            event_key = str(event['event_key'])[:60]
            country = event['country']
            importance = event['importance_n']
            score = event['empirical_score']
            actual = event['actual']
            estimate = event['estimate']
            
            score_str = f"{score:.1f}" if pd.notna(score) else "N/A"
            actual_str = f"{actual:.2f}" if pd.notna(actual) else "N/A"
            estimate_str = f"{estimate:.2f}" if pd.notna(estimate) else "N/A"
            
            # Marquer événements à 13:30
            marker = "🔴" if event_time == "13:30" else "  "
            
            print(f"{marker} {event_time:<8} {event_key:<60} {country:<8} {importance:<4} {score_str:<8} {actual_str:<12} {estimate_str:<12}")
        
        print()
        print("🔴 = Événements à 13:30")
        print()
        
        # Compter événements par heure
        df_all_events['hour'] = df_all_events['ts_utc'].dt.hour
        df_all_events['minute'] = df_all_events['ts_utc'].dt.minute
        
        events_by_hour = df_all_events.groupby(['hour', 'minute']).size().reset_index(name='count')
        events_by_hour = events_by_hour.sort_values(['hour', 'minute'])
        
        print("📊 Événements par heure :")
        print("-"*50)
        for _, row in events_by_hour.iterrows():
            print(f"  {int(row['hour']):02d}:{int(row['minute']):02d} : {int(row['count'])} événements")
        print()
    
    # 2. Vérifier événements à 13:30 spécifiquement
    print("="*100)
    print("2. ÉVÉNEMENTS À 13:30 (US, IMPACT HAUT)")
    print("="*100)
    print()
    
    query_1330 = f"""
    SELECT 
        e.ts_utc,
        e.event_key,
        e.event_title,
        e.country,
        e.importance_n,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{date_str}'
      AND EXTRACT(HOUR FROM e.ts_utc) = 13
      AND EXTRACT(MINUTE FROM e.ts_utc) = 30
      AND e.country = 'US'
      AND e.importance_n = 3
    ORDER BY e.ts_utc
    """
    
    df_1330 = conn.execute(query_1330).df()
    
    if not df_1330.empty:
        print(f"✅ {len(df_1330)} événements US HIGH à 13:30 trouvés")
        print()
        print(f"{'Event Key':<60} {'Score':<8} {'Actual':<12} {'Estimate':<12}")
        print("-"*100)
        
        for _, event in df_1330.iterrows():
            event_key = str(event['event_key'])[:60]
            score = event['empirical_score']
            actual = event['actual']
            estimate = event['estimate']
            
            score_str = f"{score:.1f}" if pd.notna(score) else "N/A"
            actual_str = f"{actual:.2f}" if pd.notna(actual) else "N/A"
            estimate_str = f"{estimate:.2f}" if pd.notna(estimate) else "N/A"
            
            print(f"{event_key:<60} {score_str:<8} {actual_str:<12} {estimate_str:<12}")
        print()
    else:
        print("❌ Aucun événement US HIGH à 13:30 trouvé")
        print()
        print("⚠️  Vérification avec heure UTC...")
        
        # Vérifier en UTC (13:30 US = 19:30 UTC en été, 18:30 UTC en hiver)
        query_1330_utc = f"""
        SELECT 
            ts_utc,
            event_key,
            country,
            importance_n
        FROM events
        WHERE DATE(ts_utc) = '{date_str}'
          AND EXTRACT(HOUR FROM ts_utc) IN (18, 19)
          AND EXTRACT(MINUTE FROM ts_utc) = 30
          AND country = 'US'
          AND importance_n = 3
        ORDER BY ts_utc
        """
        
        df_1330_utc = conn.execute(query_1330_utc).df()
        
        if not df_1330_utc.empty:
            print(f"✅ {len(df_1330_utc)} événements US HIGH trouvés (heure UTC)")
            for _, event in df_1330_utc.iterrows():
                event_time = pd.to_datetime(event['ts_utc']).strftime('%H:%M UTC')
                print(f"  - {event_time} : {event['event_key']}")
        print()
    
    # 3. Exécuter le pipeline pour voir ce qui est sélectionné
    print("="*100)
    print("3. RÉSULTAT DU PIPELINE")
    print("="*100)
    print()
    
    executor = PipelineExecutor(db_path=str(DB_PATH), verbose=True)
    
    result = executor.execute_complete_pipeline(
        date_str,
        window_minutes=30,
        support_threshold=0.8,
        jaccard_threshold=0.6,
        years_lookback=5
    )
    
    if result and result.get('success'):
        results_dict = result.get('results', {})
        
        # Clusters détectés
        clusters = results_dict.get('etape2_clusters', [])
        
        print()
        print("📊 CLUSTERS DÉTECTÉS :")
        print("-"*100)
        
        for i, cluster in enumerate(clusters, 1):
            anchor_time = cluster.get('anchor_time')
            n_events = cluster.get('n_events', 0)
            cluster_events = cluster.get('events', pd.DataFrame())
            
            anchor_str = anchor_time.strftime('%H:%M') if hasattr(anchor_time, 'strftime') else str(anchor_time)
            
            print(f"Cluster {i} : {anchor_str} ({n_events} événements)")
            
            if not cluster_events.empty:
                # Afficher événements US HIGH
                us_high = cluster_events[
                    (cluster_events['country'] == 'US') &
                    (cluster_events['importance_n'] == 3)
                ]
                
                if not us_high.empty:
                    print(f"  Événements US HIGH :")
                    for _, event in us_high.iterrows():
                        event_time = pd.to_datetime(event['ts_utc']).strftime('%H:%M')
                        event_key = str(event['event_key'])[:50]
                        print(f"    - {event_time} : {event_key}")
                else:
                    print(f"  ⚠️  Aucun événement US HIGH")
            print()
        
        # Cluster sélectionné
        cluster_info = results_dict.get('etape3_cluster_info', {})
        main_cluster = cluster_info.get('cluster', {})
        anchor_time_selected = main_cluster.get('anchor_time')
        
        print("="*100)
        print("CLUSTER SÉLECTIONNÉ :")
        print("="*100)
        print()
        
        anchor_str_selected = anchor_time_selected.strftime('%H:%M') if hasattr(anchor_time_selected, 'strftime') else str(anchor_time_selected)
        print(f"Anchor Time : {anchor_str_selected}")
        
        cluster_events_selected = main_cluster.get('events', pd.DataFrame())
        if not cluster_events_selected.empty:
            print(f"Événements ({len(cluster_events_selected)}) :")
            for _, event in cluster_events_selected.iterrows():
                event_time = pd.to_datetime(event['ts_utc']).strftime('%H:%M')
                event_key = str(event['event_key'])[:50]
                country = event['country']
                importance = event['importance_n']
                print(f"  - {event_time} : {event_key} ({country}, imp={importance})")
        print()
        
        # Core type
        etape3 = results_dict.get('etape3_noyau_dur', {})
        core_type = etape3.get('core_type', 'UNKNOWN')
        print(f"Core Type : {core_type}")
        print()
    
    # 4. Vérifier le mouvement à 14:00
    print("="*100)
    print("4. MOUVEMENT À 14:00")
    print("="*100)
    print()
    
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE DATE(datetime) = '{date_str}'
      AND datetime >= '{date_str} 13:00:00'
      AND datetime <= '{date_str} 15:00:00'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_prices).df()
    
    if not df_prices.empty:
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        df_prices = df_prices.set_index('datetime')
        
        # Baseline : 13:30
        baseline_time = TZ_BERN.localize(
            datetime.combine(pd.to_datetime(date_str).date(), datetime.min.time().replace(hour=13, minute=30))
        )
        
        prices_at_1330 = df_prices[df_prices.index >= baseline_time]
        
        if not prices_at_1330.empty:
            baseline_price = prices_at_1330.iloc[0]['open']
            max_high = prices_at_1330['high'].max()
            min_low = prices_at_1330['low'].min()
            
            impact_up = (max_high - baseline_price) * 10000
            impact_down = (baseline_price - min_low) * 10000
            impact = max(impact_up, impact_down)
            
            print(f"Baseline (13:30 OPEN) : {baseline_price:.5f}")
            print(f"Max High : {max_high:.5f}")
            print(f"Min Low : {min_low:.5f}")
            print()
            print(f"Impact UP : {impact_up:.2f} pips")
            print(f"Impact DOWN : {impact_down:.2f} pips")
            print(f"Impact MAX : {impact:.2f} pips")
            print()
            
            # Trouver heure du pic
            if impact_up > impact_down:
                peak_time = prices_at_1330[prices_at_1330['high'] == max_high].index[0]
                print(f"Pic UP à : {peak_time.strftime('%H:%M')}")
            else:
                low_time = prices_at_1330[prices_at_1330['low'] == min_low].index[0]
                print(f"Pic DOWN à : {low_time.strftime('%H:%M')}")
    
    conn.close()
    print()
    print("="*100)
    print("INVESTIGATION TERMINÉE")
    print("="*100)

if __name__ == '__main__':
    investigate_2025_04_10()

