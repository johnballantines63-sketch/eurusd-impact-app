#!/usr/bin/env python3
"""
Debug Alternative 1 - Analyse Détaillée
=========================================

Objectif : Comprendre pourquoi Alternative 1 n'est pas plus précise alors qu'elle se base sur événements réels
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

# Dates à tester
TEST_DATES = [
    '2025-09-11',  # Clusters multiples (14:30 + 14:45)
    '2025-11-20',  # Un seul cluster (14:30)
]

print('='*100)
print('DEBUG ALTERNATIVE 1 - ANALYSE DÉTAILLÉE')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

# Charger timings réels
real_timings_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'real_timings_all_dates.csv'
real_timings_df = pd.read_csv(real_timings_file)

for date_str in TEST_DATES:
    print('='*100)
    print(f'📅 DATE : {date_str}')
    print('='*100)
    print()
    
    try:
        result = executor.execute_complete_pipeline(date_str)
        
        if not result.get('success'):
            print(f'❌ Erreur: {result.get("error")}')
            continue
        
        final_pred = result.get('final_prediction', {})
        pattern_info = final_pred.get('pattern_info', {})
        cluster_info = result.get('results', {}).get('etape3_cluster_info', {})
        cluster = cluster_info.get('cluster', {})
        anchor_time = cluster.get('anchor_time')
        
        print(f'📊 INFORMATIONS CLUSTER')
        print('-'*100)
        print(f'Anchor time : {anchor_time}')
        print()
        
        # Charger tous les événements de la date
        all_events = executor.etape1_charger_evenements(date_str)
        clusters = executor.etape2_detecter_clusters(all_events, window_minutes=30)
        
        print(f'📊 CLUSTERS DÉTECTÉS')
        print('-'*100)
        print(f'Nombre de clusters : {len(clusters)}')
        print()
        
        for idx, cluster_info in enumerate(clusters, 1):
            cluster_anchor = cluster_info.get('anchor_time')
            cluster_events = cluster_info.get('events', pd.DataFrame())
            
            print(f'Cluster {idx}:')
            print(f'  Anchor time : {cluster_anchor.strftime("%H:%M")}')
            print(f'  Nombre événements : {len(cluster_events)}')
            
            if not cluster_events.empty:
                # Afficher quelques événements
                print(f'  Événements :')
                for i, (_, event) in enumerate(cluster_events.head(5).iterrows()):
                    event_time = pd.to_datetime(event.get('ts_utc', ''))
                    event_title = event.get('event_title') or event.get('event_key') or event.get('label') or 'Unknown'
                    if pd.isna(event_title) or not isinstance(event_title, str):
                        event_title = str(event_title) if not pd.isna(event_title) else 'Unknown'
                    country = event.get('country', 'Unknown')
                    importance = event.get('importance_n', 'N/A')
                    event_title_str = event_title[:50] if len(str(event_title)) > 50 else str(event_title)
                    print(f'    - {event_time.strftime("%H:%M")} [{country}] {event_title_str} (importance: {importance})')
                if len(cluster_events) > 5:
                    print(f'    ... et {len(cluster_events) - 5} autres')
            print()
        
        # Timings réels
        real_timings_row = real_timings_df[real_timings_df['date'] == date_str]
        wave1_real = None
        pullback_real = None
        wave2_real = None
        
        if not real_timings_row.empty:
            real_timings_row = real_timings_row.iloc[0]
            
            anchor_date = anchor_time.date()
            
            if pd.notna(real_timings_row.get('wave1_real')):
                wave1_time_str = str(real_timings_row['wave1_real'])
                try:
                    wave1_real = pd.to_datetime(f"{anchor_date} {wave1_time_str}")
                    if anchor_time.tzinfo:
                        wave1_real = wave1_real.tz_localize(anchor_time.tzinfo)
                except:
                    pass
            
            if pd.notna(real_timings_row.get('pullback_real')):
                pullback_time_str = str(real_timings_row['pullback_real'])
                try:
                    pullback_real = pd.to_datetime(f"{anchor_date} {pullback_time_str}")
                    if anchor_time.tzinfo:
                        pullback_real = pullback_real.tz_localize(anchor_time.tzinfo)
                except:
                    pass
            
            if pd.notna(real_timings_row.get('wave2_real')):
                wave2_time_str = str(real_timings_row['wave2_real'])
                try:
                    wave2_real = pd.to_datetime(f"{anchor_date} {wave2_time_str}")
                    if anchor_time.tzinfo:
                        wave2_real = wave2_real.tz_localize(anchor_time.tzinfo)
                except:
                    pass
            
            print(f'📊 TIMINGS RÉELS OBSERVÉS')
            print('-'*100)
            if wave1_real is not None:
                delta_w1 = (wave1_real - anchor_time).total_seconds() / 60.0
                print(f'Wave1 : {wave1_real.strftime("%H:%M")} (T+{delta_w1:.0f} min depuis anchor {anchor_time.strftime("%H:%M")})')
            else:
                print(f'Wave1 : N/A')
            if pullback_real is not None:
                delta_pb = (pullback_real - anchor_time).total_seconds() / 60.0
                print(f'Pullback : {pullback_real.strftime("%H:%M")} (T+{delta_pb:.0f} min depuis anchor {anchor_time.strftime("%H:%M")})')
            else:
                print(f'Pullback : N/A')
            if wave2_real is not None:
                delta_w2 = (wave2_real - anchor_time).total_seconds() / 60.0
                print(f'Wave2 : {wave2_real.strftime("%H:%M")} (T+{delta_w2:.0f} min depuis anchor {anchor_time.strftime("%H:%M")})')
            else:
                print(f'Wave2 : N/A')
            print()
        
        # Calculer timings Alternative 1
        if len(clusters) > 1:
            cluster1_time = clusters[0]['anchor_time']
            cluster2_time = clusters[1]['anchor_time']
            ΔT = (cluster2_time - cluster1_time).total_seconds() / 60.0
            
            print(f'📊 CALCUL ALTERNATIVE 1')
            print('-'*100)
            print(f'Cluster 1 : {cluster1_time.strftime("%H:%M")}')
            print(f'Cluster 2 : {cluster2_time.strftime("%H:%M")}')
            print(f'ΔT (délai) : {ΔT:.0f} min')
            print()
            
            if ΔT < 30:  # Pattern Overlapping
                pullback_time_alt1 = cluster2_time + pd.Timedelta(minutes=4)
                wave2_time_alt1 = pullback_time_alt1 + pd.Timedelta(minutes=21)
                wave1_time_alt1 = cluster1_time + pd.Timedelta(minutes=5)
                
                print(f'Timings Alternative 1:')
                print(f'  Wave1 : {wave1_time_alt1.strftime("%H:%M")} (Cluster1 + 5 min)')
                print(f'  Pullback : {pullback_time_alt1.strftime("%H:%M")} (Cluster2 + 4 min = {cluster2_time.strftime("%H:%M")} + 4)')
                print(f'  Wave2 : {wave2_time_alt1.strftime("%H:%M")} (Pullback + 21 min = {pullback_time_alt1.strftime("%H:%M")} + 21)')
                print()
                
                # Comparer avec timings réels
                if wave1_real and pullback_real and wave2_real:
                    print(f'📊 COMPARAISON AVEC RÉELS')
                    print('-'*100)
                    
                    error_w1 = abs((wave1_time_alt1 - wave1_real).total_seconds() / 60.0)
                    error_pb = abs((pullback_time_alt1 - pullback_real).total_seconds() / 60.0)
                    error_w2 = abs((wave2_time_alt1 - wave2_real).total_seconds() / 60.0)
                    
                    print(f'Wave1 :')
                    print(f'  Prédit : {wave1_time_alt1.strftime("%H:%M")}')
                    print(f'  Réel   : {wave1_real.strftime("%H:%M")}')
                    print(f'  Erreur : {error_w1:.1f} min {"✅" if error_w1 < 1 else "⚠️" if error_w1 < 5 else "❌"}')
                    print()
                    
                    print(f'Pullback :')
                    print(f'  Prédit : {pullback_time_alt1.strftime("%H:%M")}')
                    print(f'  Réel   : {pullback_real.strftime("%H:%M")}')
                    print(f'  Erreur : {error_pb:.1f} min {"✅" if error_pb < 1 else "⚠️" if error_pb < 5 else "❌"}')
                    print()
                    
                    print(f'Wave2 :')
                    print(f'  Prédit : {wave2_time_alt1.strftime("%H:%M")}')
                    print(f'  Réel   : {wave2_real.strftime("%H:%M")}')
                    print(f'  Erreur : {error_w2:.1f} min {"✅" if error_w2 < 1 else "⚠️" if error_w2 < 5 else "❌"}')
                    print()
                    
                    # Analyser pourquoi erreur
                    print(f'🔍 ANALYSE ERREURS')
                    print('-'*100)
                    
                    # Pour pullback
                    if error_pb > 1:
                        print(f'Pullback erreur {error_pb:.1f} min:')
                        print(f'  Cluster2 réel : {cluster2_time.strftime("%H:%M")}')
                        print(f'  Pullback réel : {pullback_real.strftime("%H:%M")}')
                        delta_pb_real = (pullback_real - cluster2_time).total_seconds() / 60.0
                        print(f'  → Pullback arrive T+{delta_pb_real:.0f} min APRÈS cluster2 (pas T+4)')
                        print(f'  → Formule devrait être : Pullback = Cluster2 + {delta_pb_real:.0f} min')
                    
                    # Pour wave2
                    if error_w2 > 1:
                        print(f'Wave2 erreur {error_w2:.1f} min:')
                        print(f'  Pullback réel : {pullback_real.strftime("%H:%M")}')
                        print(f'  Wave2 réel : {wave2_real.strftime("%H:%M")}')
                        delta_w2_real = (wave2_real - pullback_real).total_seconds() / 60.0
                        print(f'  → Wave2 arrive T+{delta_w2_real:.0f} min APRÈS pullback (pas T+21)')
                        print(f'  → Formule devrait être : Wave2 = Pullback + {delta_w2_real:.0f} min')
        else:
            print(f'⚠️ Un seul cluster détecté → Alternative 1 utilise timings standard')
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        print()

print('='*100)
print('✅ DEBUG TERMINÉ')
print('='*100)

