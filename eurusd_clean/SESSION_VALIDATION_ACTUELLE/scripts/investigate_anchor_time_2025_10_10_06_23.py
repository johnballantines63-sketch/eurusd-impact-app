#!/usr/bin/env python3
"""
Investigation Anchor Time - 2025-10-10 et 2025-06-23
======================================================

Objectif : Comprendre pourquoi anchor_time n'est pas à 14:30
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import pytz

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

TEST_DATES = ['2025-10-10', '2025-06-23']

print('='*100)
print('INVESTIGATION ANCHOR TIME - 2025-10-10 et 2025-06-23')
print('='*100)
print()

for date_str in TEST_DATES:
    print('='*100)
    print(f'📅 ANALYSE : {date_str}')
    print('='*100)
    print()
    
    try:
        executor = PipelineExecutor(DB_PATH, verbose=False)
        result = executor.execute_complete_pipeline(date_str)
        
        if not result.get('success'):
            print(f'❌ Erreur: {result.get("error")}')
            continue
        
        cluster_info = result.get('results', {}).get('etape3_cluster_info', {})
        cluster = cluster_info.get('cluster', {})
        cluster_events = cluster.get('events', pd.DataFrame())
        anchor_time = cluster.get('anchor_time')
        
        print(f'📊 CLUSTER')
        print(f'   Anchor time : {anchor_time}')
        print(f'   Nombre événements : {len(cluster_events)}')
        print()
        
        print(f'📋 ÉVÉNEMENTS DU CLUSTER')
        print('-'*100)
        
        for idx, event in cluster_events.iterrows():
            event_time = event.get('ts_utc')
            country = event.get('country', 'UNKNOWN')
            event_key = event.get('event_key', 'UNKNOWN')
            empirical_score = event.get('empirical_score', 0)
            importance_n = event.get('importance_n', 0)
            
            time_str = event_time.strftime('%H:%M') if hasattr(event_time, 'strftime') else str(event_time)
            
            print(f'   {idx+1}. {time_str} | {country:3s} | Score: {empirical_score:5.1f} | Importance: {importance_n} | {event_key}')
        
        print()
        
        # Vérifier événements US HIGH impact
        us_high_impact = cluster_events[
            (cluster_events['country'] == 'US') & 
            (cluster_events['empirical_score'] > 50)
        ]
        
        print(f'🔍 ÉVÉNEMENTS US HIGH IMPACT (score > 50)')
        print('-'*100)
        
        if not us_high_impact.empty:
            print(f'   ✅ {len(us_high_impact)} événement(s) trouvé(s)')
            for idx, event in us_high_impact.iterrows():
                event_time = event.get('ts_utc')
                time_str = event_time.strftime('%H:%M') if hasattr(event_time, 'strftime') else str(event_time)
                hour = event_time.hour if hasattr(event_time, 'hour') else None
                minute = event_time.minute if hasattr(event_time, 'minute') else None
                
                print(f'      {time_str} | Score: {event.get("empirical_score", 0):.1f} | {event.get("event_key", "UNKNOWN")}')
                
                if hour == 14 and 25 <= minute <= 35:
                    print(f'         ✅ Heure autour de 14:30 → Anchor time devrait être ajusté')
                else:
                    print(f'         ⚠️ Heure non autour de 14:30 (heure: {hour}, minute: {minute})')
        else:
            print(f'   ❌ Aucun événement US HIGH impact trouvé')
            print(f'   → C\'est pourquoi l\'anchor_time n\'est pas ajusté à 14:30')
        
        print()
        
        # Vérifier événements US autour de 14:30
        us_events = cluster_events[cluster_events['country'] == 'US']
        us_around_1430 = []
        
        for idx, event in us_events.iterrows():
            event_time = event.get('ts_utc')
            if hasattr(event_time, 'hour') and hasattr(event_time, 'minute'):
                hour = event_time.hour
                minute = event_time.minute
                if hour == 14 and 25 <= minute <= 35:
                    us_around_1430.append(event)
        
        print(f'🔍 ÉVÉNEMENTS US AUTOUR DE 14:30')
        print('-'*100)
        
        if us_around_1430:
            print(f'   ✅ {len(us_around_1430)} événement(s) trouvé(s)')
            for event in us_around_1430:
                event_time = event.get('ts_utc')
                time_str = event_time.strftime('%H:%M') if hasattr(event_time, 'strftime') else str(event_time)
                empirical_score = event.get('empirical_score', 0)
                print(f'      {time_str} | Score: {empirical_score:.1f} | {event.get("event_key", "UNKNOWN")}')
                if empirical_score <= 50:
                    print(f'         ⚠️ Score ≤ 50 → Ne sera pas utilisé pour ajuster anchor_time')
        else:
            print(f'   ❌ Aucun événement US autour de 14:30')
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        print()

print()




