#!/usr/bin/env python3
"""
Investigation Mesure Impact Réel
=================================

Objectif : Comprendre pourquoi les mesures réelles sont incorrectes
et corriger pour capturer le bon pic selon le pattern
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
sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'session120'))

from config import DB_PATH
from core.price_loader_finnhub import get_finnhub_prices_at_event_time
from scripts.run_pipeline_complete import PipelineExecutor
from scripts.session120.double_wave_detector_rev12 import detect_for_date_duckdb_rev12

# Dates à investiguer
TEST_DATES = [
    {
        'date': '2025-09-11',
        'expected_real': 60.0,  # Pic 2 double wave
        'notes': 'DOUBLE_WAVE - Pic 2 attendu ~60 pips'
    },
    {
        'date': '2025-08-01',
        'expected_real': 188.4,  # Single wave
        'notes': 'SINGLE_WAVE_STRONG - Pic unique attendu ~188 pips'
    },
    {
        'date': '2025-11-20',
        'expected_real': 35.5,  # Pic 2 double wave
        'notes': 'DOUBLE_WAVE - Pic 2 attendu ~35 pips'
    },
]

print('='*100)
print('INVESTIGATION MESURE IMPACT RÉEL')
print('='*100)
print()

executor = PipelineExecutor(DB_PATH, verbose=False)

for date_info in TEST_DATES:
    date_str = date_info['date']
    expected_real = date_info['expected_real']
    notes = date_info['notes']
    
    print('='*100)
    print(f'📅 INVESTIGATION : {date_str} - {notes}')
    print('='*100)
    print()
    
    try:
        # 1. Obtenir détection pattern depuis pipeline
        print('1️⃣ DÉTECTION PATTERN')
        print('-'*100)
        
        result_pipeline = executor.execute_complete_pipeline(date_str)
        
        if not result_pipeline.get('success'):
            print(f'❌ Erreur pipeline: {result_pipeline.get("error")}')
            continue
        
        final_pred = result_pipeline.get('final_prediction', {})
        pattern_info = final_pred.get('pattern_info', {})
        cluster_info = result_pipeline.get('results', {}).get('etape3_cluster_info', {})
        cluster = cluster_info.get('cluster', {})
        anchor_time = cluster.get('anchor_time')
        
        pattern_type = pattern_info.get('pattern_type', 'NONE')
        wave1_pips = pattern_info.get('wave1_pips', 0.0)
        wave2_pips = pattern_info.get('wave2_pips', 0.0)
        wave2_peak_pips_absolute = pattern_info.get('wave2_peak_pips_absolute', 0.0)
        
        print(f'Pattern détecté : {pattern_type}')
        print(f'Wave1 pips : {wave1_pips:.2f} pips')
        print(f'Wave2 pips : {wave2_pips:.2f} pips')
        print(f'Wave2 peak (absolute) : {wave2_peak_pips_absolute:.2f} pips')
        print()
        
        # 2. Mesurer impact réel avec méthode actuelle
        print('2️⃣ MESURE ACTUELLE (measure_impact_from_finnhub)')
        print('-'*100)
        
        if anchor_time.tzinfo is None:
            tz_bern = pytz.timezone('Europe/Zurich')
            anchor_time = tz_bern.localize(anchor_time)
        
        # Charger prix
        df_prices = get_finnhub_prices_at_event_time(
            db_path=DB_PATH,
            event_timestamp_bern=anchor_time,
            lookback_minutes=5,
            lookahead_minutes=120
        )
        
        if df_prices.empty:
            print(f'❌ Aucun prix trouvé')
            continue
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        
        # Trouver baseline
        prices_at_anchor = df_prices[df_prices['datetime'] >= anchor_time]
        if not prices_at_anchor.empty:
            baseline = prices_at_anchor.iloc[0]['open']
        else:
            prices_before = df_prices[df_prices['datetime'] < anchor_time]
            baseline = prices_before.iloc[-1]['close']
        
        # Calculer impact bidirectionnel (méthode actuelle)
        prices_after = df_prices[df_prices['datetime'] >= anchor_time].copy()
        prices_after['pips_high'] = (prices_after['high'] - baseline) * 10000
        prices_after['pips_low'] = (baseline - prices_after['low']) * 10000
        
        peak_high = prices_after['pips_high'].max()
        peak_low = prices_after['pips_low'].max()
        
        if peak_high > peak_low:
            impact_current = peak_high
            peak_idx = prices_after['pips_high'].idxmax()
            peak_price = prices_after.loc[peak_idx, 'high']
            peak_time = prices_after.loc[peak_idx, 'datetime']
            direction = 1
        else:
            impact_current = peak_low
            peak_idx = prices_after['pips_low'].idxmax()
            peak_price = prices_after.loc[peak_idx, 'low']
            peak_time = prices_after.loc[peak_idx, 'datetime']
            direction = -1
        
        print(f'Baseline : {baseline:.5f}')
        print(f'Pic mesuré : {peak_time.strftime("%H:%M")} @ {peak_price:.5f}')
        print(f'Impact mesuré (méthode actuelle) : {impact_current:.2f} pips')
        print()
        
        # 3. Comparer avec pattern détecté
        print('3️⃣ COMPARAISON AVEC PATTERN DÉTECTÉ')
        print('-'*100)
        
        if pattern_type == 'DOUBLE_WAVE':
            print(f'Pattern : DOUBLE_WAVE')
            print(f'Wave1 : {wave1_pips:.2f} pips')
            print(f'Wave2 : {wave2_pips:.2f} pips')
            print(f'Wave2 peak (absolute) : {wave2_peak_pips_absolute:.2f} pips')
            print(f'Impact attendu (pic 2) : {wave2_peak_pips_absolute:.2f} pips')
            print()
            
            print(f'🔍 ANALYSE')
            print('-'*100)
            print(f'Impact mesuré actuel : {impact_current:.2f} pips')
            print(f'Wave2 peak (absolute) : {wave2_peak_pips_absolute:.2f} pips')
            print(f'Différence : {abs(impact_current - wave2_peak_pips_absolute):.2f} pips')
            
            if abs(impact_current - wave1_pips) < abs(impact_current - wave2_peak_pips_absolute):
                print(f'⚠️ Impact mesuré correspond à Wave1 ({wave1_pips:.2f} pips) au lieu de Wave2')
                print(f'   → Problème : Mesure capture pic 1 au lieu de pic 2')
            elif abs(impact_current - wave2_peak_pips_absolute) < 5:
                print(f'✅ Impact mesuré correspond à Wave2 peak (absolute)')
            else:
                print(f'⚠️ Impact mesuré ne correspond ni à Wave1 ni à Wave2')
                
        elif pattern_type == 'SINGLE_WAVE_STRONG' or pattern_type == 'SINGLE_WAVE_STANDARD':
            print(f'Pattern : {pattern_type}')
            print(f'Wave1 peak (absolute) : {wave2_peak_pips_absolute:.2f} pips')
            print(f'Impact attendu (pic unique) : {wave2_peak_pips_absolute:.2f} pips')
            print()
            
            print(f'🔍 ANALYSE')
            print('-'*100)
            print(f'Impact mesuré actuel : {impact_current:.2f} pips')
            print(f'Wave1 peak (absolute) : {wave2_peak_pips_absolute:.2f} pips')
            print(f'Différence : {abs(impact_current - wave2_peak_pips_absolute):.2f} pips')
            
            if abs(impact_current - wave2_peak_pips_absolute) < 5:
                print(f'✅ Impact mesuré correspond à Wave1 peak (absolute)')
            else:
                print(f'⚠️ Impact mesuré ne correspond pas au pic unique')
        
        # 4. Analyser prix réels pour comprendre
        print()
        print('4️⃣ ANALYSE PRIX RÉELS DÉTAILLÉE')
        print('-'*100)
        
        # Fenêtre étendue pour voir tous les pics
        window_start = anchor_time - pd.Timedelta(minutes=5)
        window_end = anchor_time + pd.Timedelta(hours=3)
        
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE datetime >= '{window_start.isoformat()}' 
          AND datetime <= '{window_end.isoformat()}'
        ORDER BY datetime ASC
        """
        df_all = conn.execute(query).df()
        conn.close()
        
        if not df_all.empty:
            df_all['datetime'] = pd.to_datetime(df_all['datetime'])
            df_all = df_all.set_index('datetime')
            
            # Trouver tous les pics locaux
            prices_after_all = df_all[df_all.index >= anchor_time].copy()
            prices_after_all['pips_high'] = (prices_after_all['high'] - baseline) * 10000
            
            # Trouver pic absolu
            peak_absolute = prices_after_all['pips_high'].max()
            peak_absolute_time = prices_after_all['pips_high'].idxmax()
            
            print(f'Pic absolu (fenêtre 3h) : {peak_absolute_time.strftime("%H:%M")} @ {peak_absolute:.2f} pips')
            print(f'Pic mesuré actuel : {peak_time.strftime("%H:%M")} @ {impact_current:.2f} pips')
            print()
            
            if pattern_type == 'DOUBLE_WAVE':
                print(f'🔍 COMPARAISON DOUBLE_WAVE')
                print('-'*100)
                print(f'Wave1 pips : {wave1_pips:.2f} pips')
                print(f'Wave2 peak (absolute) : {wave2_peak_pips_absolute:.2f} pips')
                print(f'Pic absolu (3h) : {peak_absolute:.2f} pips')
                print(f'Pic mesuré actuel : {impact_current:.2f} pips')
                print()
                
                if abs(impact_current - wave1_pips) < 5:
                    print(f'❌ PROBLÈME : Mesure capture Wave1 ({wave1_pips:.2f} pips) au lieu de Wave2 ({wave2_peak_pips_absolute:.2f} pips)')
                    print(f'   → Solution : Utiliser wave2_peak_pips_absolute pour DOUBLE_WAVE')
                elif abs(impact_current - wave2_peak_pips_absolute) < 5:
                    print(f'✅ Mesure correcte : Capture Wave2 ({wave2_peak_pips_absolute:.2f} pips)')
                else:
                    print(f'⚠️ Mesure ne correspond ni à Wave1 ni à Wave2')
        
        print()
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        print()

print('='*100)
print('✅ INVESTIGATION TERMINÉE')
print('='*100)
