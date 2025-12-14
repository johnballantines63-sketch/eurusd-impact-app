#!/usr/bin/env python3
"""
Vérification Mesure Réel - 2025-10-10
=======================================

Objectif : Vérifier comment le réel a été mesuré et comparer avec pic absolu détecté
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import pytz
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from core.price_loader_finnhub import measure_impact_from_finnhub
from scripts.run_pipeline_complete import PipelineExecutor

date_str = '2025-10-10'
event_time_str = '14:30'  # Heure utilisée pour mesure
timezone_str = 'Europe/Zurich'

print('='*100)
print(f'VÉRIFICATION MESURE RÉEL - {date_str}')
print('='*100)
print()

# 1. Mesurer réel avec méthode actuelle
print('1️⃣ MESURE RÉEL (MÉTHODE ACTUELLE)')
print('-'*100)

date_parts = date_str.split('-')
time_parts = event_time_str.split(':')

tz = pytz.timezone(timezone_str)
event_datetime = datetime(
    int(date_parts[0]),
    int(date_parts[1]),
    int(date_parts[2]),
    int(time_parts[0]),
    int(time_parts[1]),
    0,
    tzinfo=tz
)

result_measure = measure_impact_from_finnhub(
    db_path=DB_PATH,
    event_timestamp=event_datetime,
    lookback_minutes=5,
    lookahead_minutes=120,
    debug=True
)

if result_measure and result_measure.get('success'):
    baseline_measured = result_measure.get('baseline_price')
    peak_measured = result_measure.get('peak_price')
    peak_time_measured = result_measure.get('peak_time')
    impact_measured = result_measure.get('impact_pips', 0.0)
    direction_measured = result_measure.get('direction', 'UNKNOWN')
    
    print(f'Baseline mesurée : {baseline_measured:.5f}')
    print(f'Peak mesuré : {peak_time_measured} @ {peak_measured:.5f}')
    print(f'Direction mesurée : {direction_measured}')
    print(f'Impact mesuré : {impact_measured:.2f} pips')
    print()
else:
    print(f'❌ Erreur mesure: {result_measure.get("error") if result_measure else "None"}')
    impact_measured = None
    direction_measured = None

# 2. Obtenir détection pipeline
print('2️⃣ DÉTECTION PIPELINE')
print('-'*100)

executor = PipelineExecutor(DB_PATH, verbose=False)
result_pipeline = executor.execute_complete_pipeline(date_str)

if result_pipeline.get('success'):
    final_pred = result_pipeline.get('final_prediction', {})
    pattern_info = final_pred.get('pattern_info', {})
    cluster_info = result_pipeline.get('results', {}).get('etape3_cluster_info', {})
    cluster = cluster_info.get('cluster', {})
    anchor_time = cluster.get('anchor_time')
    
    wave2_absolute = pattern_info.get('wave2_peak_pips_absolute', 0.0)
    baseline_price_pattern = pattern_info.get('baseline_price')
    
    print(f'Anchor time pipeline : {anchor_time}')
    print(f'Baseline pattern : {baseline_price_pattern}')
    print(f'Wave2 peak (absolute) : {wave2_absolute:.2f} pips')
    print()

# 3. Analyser prix réels
print('3️⃣ ANALYSE PRIX RÉELS')
print('-'*100)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Charger prix M1 autour de l'événement
start_dt = anchor_time - pd.Timedelta(hours=1)
end_dt = anchor_time + pd.Timedelta(hours=3)

query_m1 = f"""
SELECT datetime, open, high, low, close
FROM prices_finnhub_m1
WHERE datetime >= '{start_dt.isoformat()}' 
  AND datetime <= '{end_dt.isoformat()}'
ORDER BY datetime ASC
"""

df_m1 = conn.execute(query_m1).df()
conn.close()

if not df_m1.empty:
    df_m1['datetime'] = pd.to_datetime(df_m1['datetime'])
    df_m1 = df_m1.set_index('datetime')
    
    # Trouver baseline réelle (prix à anchor_time)
    prices_at_anchor = df_m1[df_m1.index >= anchor_time]
    if not prices_at_anchor.empty:
        baseline_real = prices_at_anchor.iloc[0]['open']
        baseline_real_time = prices_at_anchor.index[0]
    else:
        baseline_real = df_m1.iloc[0]['close']
        baseline_real_time = df_m1.index[0]
    
    print(f'Baseline réelle (à anchor_time {anchor_time.strftime("%H:%M")}) : {baseline_real_time.strftime("%H:%M")} @ {baseline_real:.5f}')
    
    # Fenêtre événement : ±2 heures
    window_event_start = anchor_time - pd.Timedelta(hours=1)
    window_event_end = anchor_time + pd.Timedelta(hours=2)
    
    df_event_window = df_m1[
        (df_m1.index >= window_event_start) &
        (df_m1.index <= window_event_end)
    ]
    
    if not df_event_window.empty:
        peak_real_event = df_event_window['high'].max()
        peak_real_event_time = df_event_window['high'].idxmax()
        real_amp_event = (peak_real_event - baseline_real) * 10000
        
        print(f'Pic réel (fenêtre événement ±2h) : {peak_real_event_time.strftime("%H:%M")} @ {peak_real_event:.5f}')
        print(f'Amplitude réelle (fenêtre événement) : {real_amp_event:.2f} pips')
        print()
        
        # Fenêtre mesure (14:30 + 120 min = jusqu'à 16:30)
        window_measure_end = event_datetime + pd.Timedelta(minutes=120)
        df_measure_window = df_m1[
            (df_m1.index >= event_datetime - pd.Timedelta(minutes=5)) &
            (df_m1.index <= window_measure_end)
        ]
        
        if not df_measure_window.empty:
            # Baseline pour mesure (close 5 min avant événement)
            baseline_measure_window = df_measure_window[
                df_measure_window.index < event_datetime
            ]
            if not baseline_measure_window.empty:
                baseline_measure = baseline_measure_window.iloc[-1]['close']
            else:
                baseline_measure = df_measure_window.iloc[0]['open']
            
            peak_measure_window = df_measure_window['high'].max()
            peak_measure_window_time = df_measure_window['high'].idxmax()
            impact_measure_window = (peak_measure_window - baseline_measure) * 10000
            
            print(f'📊 FENÊTRE MESURE (14:30 + 120 min)')
            print('-'*100)
            print(f'Baseline mesure : {baseline_measure:.5f} (close 5 min avant événement)')
            print(f'Pic mesure : {peak_measure_window_time.strftime("%H:%M")} @ {peak_measure_window:.5f}')
            print(f'Impact mesure (fenêtre) : {impact_measure_window:.2f} pips')
            print()
            
            # Comparaison
            print(f'🔍 COMPARAISON')
            print('-'*100)
            if impact_measured is not None:
                print(f'Impact mesuré (measure_impact_from_finnhub) : {impact_measured:.2f} pips')
                if direction_measured:
                    print(f'   Direction : {direction_measured}')
            else:
                print(f'Impact mesuré (measure_impact_from_finnhub) : Non disponible')
            print(f'Impact mesure (fenêtre calculée) : {impact_measure_window:.2f} pips')
            print(f'Pic absolu étendu (240 min) : {wave2_absolute:.2f} pips')
            print(f'Amplitude réelle (fenêtre événement ±2h) : {real_amp_event:.2f} pips')
            print()
            
            # Analyser différence
            if impact_measured is not None:
                if abs(impact_measured - impact_measure_window) < 1:
                    print(f'✅ Impact mesuré correspond à fenêtre calculée')
                else:
                    print(f'⚠️ Différence entre impact mesuré et fenêtre calculée : {abs(impact_measured - impact_measure_window):.2f} pips')
                    print(f'   → Possible problème dans measure_impact_from_finnhub')
            else:
                print(f'⚠️ measure_impact_from_finnhub retourne None')
                print(f'   → Utiliser impact mesure fenêtre calculée : {impact_measure_window:.2f} pips')
            
            if abs(wave2_absolute - real_amp_event) < 5:
                print(f'✅ Pic absolu étendu correspond à amplitude réelle événement')
                print(f'   → Pic absolu étendu ({wave2_absolute:.2f} pips) est correct')
            else:
                print(f'⚠️ Différence entre pic absolu et amplitude réelle : {abs(wave2_absolute - real_amp_event):.2f} pips')
                print(f'   → Pic absolu peut capturer mouvement non lié à l\'événement')
            
            # Analyser pourquoi réel mesuré (12.30 pips) est si faible
            print()
            print(f'💡 ANALYSE RÉEL MESURÉ (12.30 pips)')
            print('-'*100)
            print(f'Réel mesuré dans CSV : 12.30 pips')
            print(f'Pic absolu étendu : {wave2_absolute:.2f} pips')
            print(f'Amplitude réelle événement : {real_amp_event:.2f} pips')
            print(f'Impact mesure fenêtre : {impact_measure_window:.2f} pips')
            print()
            
            if abs(real_amp_event - wave2_absolute) < 5:
                print(f'✅ Pic absolu étendu correspond à amplitude réelle')
                print(f'   → Le réel mesuré (12.30 pips) semble incorrect')
                print(f'   → Possible problème :')
                print(f'      1. Baseline incorrecte dans mesure réel')
                print(f'      2. Fenêtre mesure trop courte')
                print(f'      3. Direction incorrecte (bearish au lieu de bullish)')
            else:
                print(f'⚠️ Pic absolu étendu diffère de amplitude réelle')
                print(f'   → Vérifier baseline et fenêtre')
            
            # Vérifier timing pic
            if peak_measure_window_time <= window_measure_end:
                print(f'✅ Pic mesure dans fenêtre mesure (jusqu\'à {window_measure_end.strftime("%H:%M")})')
            else:
                minutes_after = (peak_measure_window_time - window_measure_end).total_seconds() / 60.0
                print(f'⚠️ Pic mesure APRÈS fenêtre mesure ({minutes_after:.0f} min après)')
            
            if peak_real_event_time <= window_measure_end:
                print(f'✅ Pic réel événement dans fenêtre mesure')
            else:
                minutes_after = (peak_real_event_time - window_measure_end).total_seconds() / 60.0
                print(f'⚠️ Pic réel événement APRÈS fenêtre mesure ({minutes_after:.0f} min après)')
                print(f'   → Le réel mesuré ne capture pas le pic réel événement')

print()

