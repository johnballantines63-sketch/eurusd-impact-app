#!/usr/bin/env python3
"""
Debug Baseline Problem
======================

Objectif : Comprendre pourquoi baseline_price_correct n'est pas calculé
"""

import sys
from pathlib import Path
import pandas as pd
import pytz
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

DATE = '2025-05-29'

print('='*100)
print('DEBUG BASELINE PROBLEM')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

# Exécuter pipeline jusqu'à l'étape 8.6
result = executor.execute_complete_pipeline(DATE)

if result.get('success'):
    # Obtenir anchor_time
    clusters = result.get('etape2_clusters', [])
    if clusters and len(clusters) > 0:
        anchor_time = clusters[0].get('anchor_time')
        print(f'Anchor time: {anchor_time}')
        print(f'Anchor time type: {type(anchor_time)}')
        print(f'Anchor time tzinfo: {anchor_time.tzinfo}')
        print()
        
        # Obtenir pattern_real_result (simuler)
        from scripts.session120.double_wave_detector_rev12 import detect_for_date_duckdb_rev12
        
        anchor_time_naive = anchor_time.replace(tzinfo=None) if anchor_time.tz else anchor_time
        pattern_real = detect_for_date_duckdb_rev12(
            db_path=str(DB_PATH),
            table='prices_finnhub_m1',
            date=anchor_time_naive,
            tz='Europe/Zurich',
            baseline_mode='prev_close_14_29',
            minutes_after_hint=180,
            trading_window=True,
            debug=False,
            event_time=anchor_time_naive
        )
        
        if pattern_real:
            baseline_price_pattern = pattern_real.get('baseline_price', 0.0)
            print(f'Baseline price pattern: {baseline_price_pattern:.5f}')
            print()
        
        # Simuler la recherche du pic absolu étendu
        window_start_event = anchor_time - pd.Timedelta(hours=1)
        window_end_extended = anchor_time + pd.Timedelta(hours=2)
        
        print(f'Fenêtre recherche: {window_start_event} → {window_end_extended}')
        print()
        
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        query_extended = f"""
        SELECT datetime, high, low, close, open
        FROM prices_finnhub_m1
        WHERE datetime >= '{window_start_event.isoformat()}' 
          AND datetime <= '{window_end_extended.isoformat()}'
        ORDER BY datetime ASC
        """
        
        print('Requête SQL:')
        print(query_extended)
        print()
        
        df_extended = conn.execute(query_extended).df()
        conn.close()
        
        print(f'Nombre de lignes retournées: {len(df_extended)}')
        print()
        
        if not df_extended.empty:
            df_extended['datetime'] = pd.to_datetime(df_extended['datetime'])
            df_extended = df_extended.set_index('datetime')
            
            print(f'Index timezone: {df_extended.index.tz}')
            print(f'Anchor time timezone: {anchor_time.tzinfo}')
            print()
            
            # Vérifier filtrage
            print('Vérification filtrage:')
            print(f'  df_extended.index >= anchor_time: {df_extended.index >= anchor_time}')
            print()
            
            prices_at_event = df_extended[df_extended.index >= anchor_time]
            
            print(f'Nombre de bougies après filtrage (>= anchor_time): {len(prices_at_event)}')
            print()
            
            if not prices_at_event.empty:
                print('✅ prices_at_event n\'est PAS vide')
                print(f'Première bougie: {prices_at_event.index[0]}')
                print(f'OPEN: {prices_at_event.iloc[0]["open"]:.5f}')
                baseline_price_correct = prices_at_event.iloc[0]['open']
                print(f'Baseline correct: {baseline_price_correct:.5f}')
                print()
                
                # Calculer wave2_absolute_extended
                peak_absolute_price = df_extended['high'].max()
                peak_absolute_time = df_extended['high'].idxmax()
                wave2_absolute_extended = (peak_absolute_price - baseline_price_correct) * 10000
                
                print(f'Peak absolute price: {peak_absolute_price:.5f}')
                print(f'Peak absolute time: {peak_absolute_time}')
                print(f'wave2_absolute_extended: {wave2_absolute_extended:.2f} pips')
                print()
            else:
                print('❌ prices_at_event est VIDE')
                print()
                print('Premières bougies dans df_extended:')
                print(df_extended.head(10))
                print()
                print('Dernières bougies dans df_extended:')
                print(df_extended.tail(10))
                print()
                print('Vérification directe:')
                print(f'  anchor_time: {anchor_time}')
                print(f'  Première bougie: {df_extended.index[0]}')
                print(f'  Dernière bougie: {df_extended.index[-1]}')
                print(f'  anchor_time >= première bougie: {anchor_time >= df_extended.index[0]}')
                print(f'  anchor_time <= dernière bougie: {anchor_time <= df_extended.index[-1]}')
        else:
            print('❌ df_extended est VIDE')
            print()
            print('Vérification requête SQL:')
            print(f'  window_start_event: {window_start_event}')
            print(f'  window_end_extended: {window_end_extended}')




