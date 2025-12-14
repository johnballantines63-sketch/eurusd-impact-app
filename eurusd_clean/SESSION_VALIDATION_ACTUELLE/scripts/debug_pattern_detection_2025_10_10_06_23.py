#!/usr/bin/env python3
"""
Debug Détection Pattern - 2025-10-10 et 2025-06-23
====================================================

Objectif : Comprendre pourquoi les patterns ne sont pas détectés
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
sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'session120'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor
from scripts.session120.double_wave_detector_rev12 import detect_for_date_duckdb_rev12

TEST_DATES = [
    {'date': '2025-10-10', 'event_time': '14:30', 'notes': 'Pattern non détecté'},
    {'date': '2025-06-23', 'event_time': '14:30', 'notes': 'Pattern non détecté'},
]

print('='*100)
print('DEBUG DÉTECTION PATTERN - 2025-10-10 et 2025-06-23')
print('='*100)
print()

for date_info in TEST_DATES:
    date_str = date_info['date']
    event_time_str = date_info['event_time']
    notes = date_info['notes']
    
    print('='*100)
    print(f'📅 ANALYSE : {date_str} - {notes}')
    print('='*100)
    print()
    
    try:
        # Exécuter pipeline pour obtenir anchor_time
        executor = PipelineExecutor(DB_PATH, verbose=False)
        result = executor.execute_complete_pipeline(date_str)
        
        if not result.get('success'):
            print(f'❌ Erreur pipeline: {result.get("error")}')
            continue
        
        cluster_info = result.get('results', {}).get('etape3_cluster_info', {})
        cluster = cluster_info.get('cluster', {})
        anchor_time = cluster.get('anchor_time')
        
        if anchor_time is None:
            print('❌ Aucun cluster trouvé')
            continue
        
        print(f'📊 INFORMATIONS CLUSTER')
        print(f'   Anchor time : {anchor_time}')
        print()
        
        # Tester détection pattern avec différents paramètres
        print(f'🔍 TEST DÉTECTION PATTERN')
        print('-'*100)
        
        # Test 1 : Paramètres par défaut
        print(f'Test 1 : Paramètres par défaut')
        pattern_result = detect_for_date_duckdb_rev12(
            db_path=str(DB_PATH),
            table='prices_finnhub_m1',
            date=datetime.strptime(date_str, '%Y-%m-%d'),
            tz='Europe/Zurich',
            baseline_mode='prev_close_14_29',
            minutes_after_hint=120,
            trading_window=True,
            debug=False,
            event_time=anchor_time
        )
        
        if pattern_result:
            print(f'   ✅ Pattern détecté : {pattern_result.get("double_wave", False)}')
            print(f'      Wave1 : {pattern_result.get("wave1_amp_pips", 0):.2f} pips')
            print(f'      Wave2 : {pattern_result.get("wave2_amp_pips", 0):.2f} pips')
            print(f'      Confidence : {pattern_result.get("confidence", 0):.1f}%')
        else:
            print(f'   ❌ Aucun pattern détecté')
        
        print()
        
        # Test 2 : baseline_mode = 'local_minmax'
        print(f'Test 2 : baseline_mode = local_minmax')
        pattern_result2 = detect_for_date_duckdb_rev12(
            db_path=str(DB_PATH),
            table='prices_finnhub_m1',
            date=datetime.strptime(date_str, '%Y-%m-%d'),
            tz='Europe/Zurich',
            baseline_mode='local_minmax',
            minutes_after_hint=120,
            trading_window=True,
            debug=False,
            event_time=anchor_time
        )
        
        if pattern_result2:
            print(f'   ✅ Pattern détecté : {pattern_result2.get("double_wave", False)}')
            print(f'      Wave1 : {pattern_result2.get("wave1_amp_pips", 0):.2f} pips')
            print(f'      Wave2 : {pattern_result2.get("wave2_amp_pips", 0):.2f} pips')
            print(f'      Confidence : {pattern_result2.get("confidence", 0):.1f}%')
        else:
            print(f'   ❌ Aucun pattern détecté')
        
        print()
        
        # Test 3 : minutes_after_hint = 180
        print(f'Test 3 : minutes_after_hint = 180')
        pattern_result3 = detect_for_date_duckdb_rev12(
            db_path=str(DB_PATH),
            table='prices_finnhub_m1',
            date=datetime.strptime(date_str, '%Y-%m-%d'),
            tz='Europe/Zurich',
            baseline_mode='prev_close_14_29',
            minutes_after_hint=180,
            trading_window=True,
            debug=True,  # Activer debug pour voir détails
            event_time=anchor_time
        )
        
        if pattern_result3:
            print(f'   ✅ Pattern détecté : {pattern_result3.get("double_wave", False)}')
            print(f'      Wave1 : {pattern_result3.get("wave1_amp_pips", 0):.2f} pips')
            print(f'      Wave2 : {pattern_result3.get("wave2_amp_pips", 0):.2f} pips')
            print(f'      Confidence : {pattern_result3.get("confidence", 0):.1f}%')
        else:
            print(f'   ❌ Aucun pattern détecté')
        
        print()
        
        # Vérifier les prix disponibles
        print(f'📊 VÉRIFICATION PRIX DISPONIBLES')
        print('-'*100)
        
        import duckdb
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Vérifier prix autour de l'événement
        start_dt = anchor_time - pd.Timedelta(hours=2)
        end_dt = anchor_time + pd.Timedelta(hours=3)
        
        query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE datetime >= '{start_dt.isoformat()}' 
          AND datetime <= '{end_dt.isoformat()}'
        ORDER BY datetime ASC
        LIMIT 20
        """
        
        df_prices = conn.execute(query).df()
        conn.close()
        
        if not df_prices.empty:
            print(f'   ✅ {len(df_prices)} bougies trouvées autour de l\'événement')
            print(f'   Première bougie : {df_prices.iloc[0]["datetime"]}')
            print(f'   Dernière bougie : {df_prices.iloc[-1]["datetime"]}')
            print()
            print(f'   Prix autour de l\'événement ({anchor_time}):')
            prices_around = df_prices[
                (pd.to_datetime(df_prices['datetime']) >= anchor_time - pd.Timedelta(minutes=30)) &
                (pd.to_datetime(df_prices['datetime']) <= anchor_time + pd.Timedelta(hours=2))
            ]
            if not prices_around.empty:
                for _, row in prices_around.head(10).iterrows():
                    print(f'      {row["datetime"]} : O={row["open"]:.5f} H={row["high"]:.5f} L={row["low"]:.5f} C={row["close"]:.5f}')
            else:
                print(f'      ⚠️ Aucune bougie trouvée autour de l\'événement')
        else:
            print(f'   ❌ Aucune bougie trouvée')
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        print()

print()




